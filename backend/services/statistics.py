"""
统计分析服务
负责处理各种统��数据的计算和聚合
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from backend.models.database import Database


class StatisticsService:
    """统计分析服务类"""

    def __init__(self, db: Database = None):
        """
        初始化统计服务

        Args:
            db: 数据库实例,为 None 则创建新实例
        """
        self.db = db if db else Database()

    def get_statistics(self,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      repo_path: Optional[str] = None) -> Dict:
        """
        获取综合统计数据

        Args:
            start_date: 开始日期(格式: YYYY-MM-DD)
            end_date: 结束日期(格式: YYYY-MM-DD)
            repo_path: 仓库路径筛选

        Returns:
            统计数据字典
        """
        stats = self.db.get_statistics(start_date, end_date, repo_path)

        # 补充额外的统计信息
        stats['total_activities'] = stats['total_commits'] + stats['total_pushes']

        # 计算平均值
        if stats['commits_by_date']:
            stats['avg_commits_per_day'] = stats['total_commits'] / len(stats['commits_by_date'])
        else:
            stats['avg_commits_per_day'] = 0

        return stats

    def get_trends(self,
                   period: str = 'day',
                   repo_path: Optional[str] = None,
                   days: int = 30) -> Dict:
        """
        获取趋势数据,用于图表展示

        Args:
            period: 时间周期(day/week/month)
            repo_path: 仓库路径筛选
            days: 返回最近几天的数据

        Returns:
            趋势数据字典,包含格式化后的日期和数量
        """
        # 计算开始日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 获取原始数据
        raw_trends = self.db.get_trends(
            period=period,
            repo_path=repo_path,
            limit=days * 2  # 获取更多数据以确保覆盖
        )

        # 格式化数据
        formatted_data = self._format_trend_data(raw_trends, period)

        return {
            'period': period,
            'data': formatted_data,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }

    def _format_trend_data(self, raw_trends: List[Dict], period: str) -> List[Dict]:
        """
        格式化趋势数据,将 commit 和 push 合并到同一条记录

        Args:
            raw_trends: 原始趋势数据
            period: 时间周期

        Returns:
            格式化后的趋势数据列表
        """
        # 按日期分组
        date_data = defaultdict(lambda: {'commits': 0, 'pushes': 0})

        for item in raw_trends:
            date = item['date']
            activity_type = item['activity_type']
            count = item['count']

            if activity_type == 'commit':
                date_data[date]['commits'] = count
            elif activity_type == 'push':
                date_data[date]['pushes'] = count

        # 转换为列表并排序
        formatted = [
            {
                'date': date,
                'commits': data['commits'],
                'pushes': data['pushes'],
                'total': data['commits'] + data['pushes']
            }
            for date, data in sorted(date_data.items(), reverse=True)
        ]

        return formatted

    def get_repo_summary(self, repo_path: str, days: int = 30) -> Dict:
        """
        获取指定仓库的汇总信息

        Args:
            repo_path: 仓库路径
            days: 统计最近几天的数据

        Returns:
            仓库汇总数据
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        activities, total = self.db.get_activities(
            page=1,
            page_size=1000,  # 获取足够多的数据
            repo_path=repo_path,
            start_date=start_date,
            end_date=end_date
        )

        # 计算统计数据
        commits = sum(1 for a in activities if a['activity_type'] == 'commit')
        pushes = sum(1 for a in activities if a['activity_type'] == 'push')

        # 按分支统计
        branch_stats = defaultdict(lambda: {'commits': 0, 'pushes': 0})
        for activity in activities:
            branch = activity['branch_name']
            if activity['activity_type'] == 'commit':
                branch_stats[branch]['commits'] += 1
            else:
                branch_stats[branch]['pushes'] += 1

        # 最近的活动
        recent_activities = activities[:10]

        return {
            'repo_path': repo_path,
            'period_days': days,
            'total_commits': commits,
            'total_pushes': pushes,
            'total_activities': commits + pushes,
            'branches': dict(branch_stats),
            'recent_activities': recent_activities
        }

    def get_daily_activity_heatmap(self, days: int = 90) -> List[Dict]:
        """
        获取每日活动热力图数据(类似 GitHub contribution graph)

        Args:
            days: 统计最近几天的数据

        Returns:
            热力图数据列表,每项包含日期和活动数量
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 获取数据
        activities, _ = self.db.get_activities(
            page=1,
            page_size=10000,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )

        # 按日期统计
        daily_counts = defaultdict(int)
        for activity in activities:
            date = activity['timestamp'][:10]  # 提取日期部分 YYYY-MM-DD
            daily_counts[date] += 1

        # 填充缺失的日期
        heatmap_data = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            heatmap_data.append({
                'date': date_str,
                'count': daily_counts.get(date_str, 0),
                'level': self._get_activity_level(daily_counts.get(date_str, 0))
            })
            current_date += timedelta(days=1)

        return heatmap_data

    def _get_activity_level(self, count: int) -> int:
        """
        根据活动数量返回热力图级别(0-4)

        Args:
            count: 活动数量

        Returns:
            级别(0-4)
        """
        if count == 0:
            return 0
        elif count <= 3:
            return 1
        elif count <= 6:
            return 2
        elif count <= 9:
            return 3
        else:
            return 4

    def get_top_repos(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """
        获取最活跃的仓库列表

        Args:
            limit: 返回数量
            days: 统计最近几天的数据

        Returns:
            仓库列表,按活跃度降序排列
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # 获取统计数据
        stats = self.db.get_statistics(start_date, end_date)

        # 格式化仓库数据
        repos = []
        for item in stats['commits_by_repo'][:limit]:
            repo_path = item['repo_path']
            count = item['count']

            # 提取仓库名称
            repo_name = repo_path.split('/')[-1] if '/' in repo_path else repo_path

            repos.append({
                'repo_path': repo_path,
                'repo_name': repo_name,
                'activity_count': count
            })

        return repos

    def get_author_stats(self, repo_path: Optional[str] = None) -> List[Dict]:
        """
        获取作者统计信息

        Args:
            repo_path: 仓库路径筛选

        Returns:
            作者统计列表
        """
        self.db.connect()
        cursor = self.db.conn.cursor()

        # 构建查询条件
        conditions = []
        params = []

        if repo_path:
            conditions.append('repo_path = ?')
            params.append(repo_path)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        # 查询作者统计
        cursor.execute(f'''
            SELECT
                author_name,
                author_email,
                COUNT(*) as total_commits,
                COUNT(DISTINCT repo_path) as repo_count,
                SUM(insertions) as total_insertions,
                SUM(deletions) as total_deletions
            FROM git_activities
            WHERE activity_type = 'commit' AND {where_clause}
            GROUP BY author_name, author_email
            ORDER BY total_commits DESC
        ''', params)

        authors = []
        for row in cursor.fetchall():
            authors.append({
                'author_name': row[0],
                'author_email': row[1],
                'total_commits': row[2],
                'repo_count': row[3],
                'total_insertions': row[4],
                'total_deletions': row[5]
            })

        return authors

    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()


if __name__ == '__main__':
    # 测试代码
    service = StatisticsService()

    # 测试获取统计数据
    print('测试获取统计数据...')
    stats = service.get_statistics()
    print(f'总提交数: {stats["total_commits"]}')
    print(f'总推送数: {stats["total_pushes"]}')

    # 测试获取趋势数据
    print('\n测试获取趋势数据...')
    trends = service.get_trends(period='day', days=7)
    print(f'趋势数据点数: {len(trends["data"])}')

    service.close()
