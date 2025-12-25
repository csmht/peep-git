"""
数据库模型和操作模块
负责 SQLite 数据库的初始化、连接管理和 CRUD 操作
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json


class Database:
    """数据库管理类"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径,默认为 data/gitsee.db
        """
        if db_path is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(current_dir, 'data', 'gitsee.db')

        self.db_path = db_path
        self.conn = None

        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # 初始化数据库
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        self.connect()

        # 创建 git_activities 表
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS git_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                repo_path TEXT NOT NULL,
                branch_name TEXT NOT NULL,
                commit_hash TEXT NOT NULL,
                commit_message TEXT,
                author_name TEXT,
                author_email TEXT,
                files_changed INTEGER DEFAULT 0,
                insertions INTEGER DEFAULT 0,
                deletions INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建 monitored_repos 表
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS monitored_repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_path TEXT NOT NULL UNIQUE,
                repo_name TEXT NOT NULL,
                remote_url TEXT,
                current_branch TEXT,
                is_monitored BOOLEAN DEFAULT 1,
                last_activity_time DATETIME,
                total_commits INTEGER DEFAULT 0,
                total_pushes INTEGER DEFAULT 0,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引优化查询性能
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON git_activities(timestamp)
        ''')

        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_repo_path
            ON git_activities(repo_path)
        ''')

        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_activity_type
            ON git_activities(activity_type)
        ''')

        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_branch_name
            ON git_activities(branch_name)
        ''')

        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_monitored_repos_path
            ON monitored_repos(repo_path)
        ''')

        self.conn.commit()

    def connect(self):
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # 允许通过列名访问

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def insert_activity(self, activity_data: Dict) -> int:
        """
        插入一条活动记录

        Args:
            activity_data: 活动数据字典

        Returns:
            新插入记录的 ID
        """
        self.connect()

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO git_activities
            (activity_type, timestamp, repo_path, branch_name, commit_hash,
             commit_message, author_name, author_email, files_changed,
             insertions, deletions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            activity_data.get('activity_type'),
            activity_data.get('timestamp'),
            activity_data.get('repo_path'),
            activity_data.get('branch_name'),
            activity_data.get('commit_hash'),
            activity_data.get('commit_message'),
            activity_data.get('author_name'),
            activity_data.get('author_email'),
            activity_data.get('files_changed', 0),
            activity_data.get('insertions', 0),
            activity_data.get('deletions', 0)
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_activities(self,
                      page: int = 1,
                      page_size: int = 20,
                      activity_type: Optional[str] = None,
                      repo_path: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> Tuple[List[Dict], int]:
        """
        获取活动记录列表(支持分页和筛选)

        Args:
            page: 页码(从 1 开始)
            page_size: 每页记录数
            activity_type: 活动类型筛选(commit/push)
            repo_path: 仓库路径筛选
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            (活动记录列表, 总记录数)
        """
        self.connect()

        # 构建查询条件
        conditions = []
        params = []

        if activity_type:
            conditions.append('activity_type = ?')
            params.append(activity_type)

        if repo_path:
            conditions.append('repo_path = ?')
            params.append(repo_path)

        if start_date:
            conditions.append('timestamp >= ?')
            params.append(start_date)

        if end_date:
            conditions.append('timestamp <= ?')
            params.append(end_date)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        # 查询总记录数
        cursor = self.conn.cursor()
        count_query = f'SELECT COUNT(*) FROM git_activities WHERE {where_clause}'
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # 查询分页数据
        offset = (page - 1) * page_size
        query = f'''
            SELECT * FROM git_activities
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        '''
        params.extend([page_size, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # 转换为字典列表
        activities = [dict(row) for row in rows]

        return activities, total

    def get_activity_by_id(self, activity_id: int) -> Optional[Dict]:
        """
        根据 ID 获取单条活动记录

        Args:
            activity_id: 活动 ID

        Returns:
            活动记录字典,如果不存在则返回 None
        """
        self.connect()

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM git_activities WHERE id = ?', (activity_id,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def get_statistics(self,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      repo_path: Optional[str] = None) -> Dict:
        """
        获取统计数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            repo_path: 仓库路径筛选

        Returns:
            统计数据字典
        """
        self.connect()

        # 构建查询条件
        conditions = []
        params = []

        if start_date:
            conditions.append('timestamp >= ?')
            params.append(start_date)

        if end_date:
            conditions.append('timestamp <= ?')
            params.append(end_date)

        if repo_path:
            conditions.append('repo_path = ?')
            params.append(repo_path)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        cursor = self.conn.cursor()

        # 总提交数
        cursor.execute(f'''
            SELECT COUNT(*) FROM git_activities
            WHERE activity_type = 'commit' AND {where_clause}
        ''', params)
        total_commits = cursor.fetchone()[0]

        # 总推送数
        cursor.execute(f'''
            SELECT COUNT(*) FROM git_activities
            WHERE activity_type = 'push' AND {where_clause}
        ''', params)
        total_pushes = cursor.fetchone()[0]

        # 按日期统计
        cursor.execute(f'''
            SELECT
                DATE(timestamp) as date,
                activity_type,
                COUNT(*) as count
            FROM git_activities
            WHERE {where_clause}
            GROUP BY DATE(timestamp), activity_type
            ORDER BY date DESC
            LIMIT 30
        ''', params)
        commits_by_date = [dict(row) for row in cursor.fetchall()]

        # 按仓库统计
        cursor.execute(f'''
            SELECT
                repo_path,
                COUNT(*) as count
            FROM git_activities
            WHERE {where_clause}
            GROUP BY repo_path
            ORDER BY count DESC
        ''', params)
        commits_by_repo = [dict(row) for row in cursor.fetchall()]

        # 按分支统计
        cursor.execute(f'''
            SELECT
                branch_name,
                COUNT(*) as count
            FROM git_activities
            WHERE {where_clause}
            GROUP BY branch_name
            ORDER BY count DESC
            LIMIT 10
        ''', params)
        commits_by_branch = [dict(row) for row in cursor.fetchall()]

        return {
            'total_commits': total_commits,
            'total_pushes': total_pushes,
            'commits_by_date': commits_by_date,
            'commits_by_repo': commits_by_repo,
            'commits_by_branch': commits_by_branch
        }

    def get_trends(self,
                   period: str = 'day',
                   repo_path: Optional[str] = None,
                   limit: int = 30) -> List[Dict]:
        """
        获取趋势数据

        Args:
            period: 时间周期(day/week/month)
            repo_path: 仓库路径筛选
            limit: 返回记录数

        Returns:
            趋势数据列表
        """
        self.connect()

        # SQLite 日期格式化
        date_format = {
            'day': '%Y-%m-%d',
            'week': '%Y-%W',
            'month': '%Y-%m'
        }.get(period, '%Y-%m-%d')

        conditions = []
        params = []

        if repo_path:
            conditions.append('repo_path = ?')
            params.append(repo_path)

        where_clause = ' AND '.join(conditions) if conditions else '1=1'

        cursor = self.conn.cursor()
        cursor.execute(f'''
            SELECT
                strftime('{date_format}', timestamp) as date,
                activity_type,
                COUNT(*) as count
            FROM git_activities
            WHERE {where_clause}
            GROUP BY strftime('{date_format}', timestamp), activity_type
            ORDER BY date DESC
            LIMIT ?
        ''', params + [limit])

        return [dict(row) for row in cursor.fetchall()]

    def get_all_activities(self) -> List[Dict]:
        """
        获取所有活动记录(用于 JSON 同步)

        Returns:
            所有活动记录列表
        """
        self.connect()

        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM git_activities ORDER BY timestamp DESC')
        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def delete_old_activities(self, days: int = 90) -> int:
        """
        删除指定天数之前的旧记录

        Args:
            days: 保留天数

        Returns:
            删除的记录数
        """
        self.connect()

        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM git_activities
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))

        self.conn.commit()
        return cursor.rowcount

    # ========== 仓库管理方法 ==========

    def add_monitored_repo(self, repo_data: Dict) -> int:
        """
        添加监控仓库

        Args:
            repo_data: 仓库数据字典
                - repo_path: 仓库路径(必需)
                - repo_name: 仓库名称(必需)
                - remote_url: 远程仓库 URL
                - current_branch: 当前分支
                - is_monitored: 是否监控

        Returns:
            新插入记录的 ID,如果已存在则返回现有 ID
        """
        self.connect()
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO monitored_repos
                (repo_path, repo_name, remote_url, current_branch, is_monitored)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                repo_data['repo_path'],
                repo_data['repo_name'],
                repo_data.get('remote_url', ''),
                repo_data.get('current_branch', ''),
                repo_data.get('is_monitored', True)
            ))

            self.conn.commit()
            return cursor.lastrowid

        except sqlite3.IntegrityError:
            # 仓库已存在,返回现有 ID
            cursor.execute('SELECT id FROM monitored_repos WHERE repo_path = ?', (repo_data['repo_path'],))
            result = cursor.fetchone()
            return result[0] if result else -1

    def get_monitored_repos(self, monitored_only: bool = False) -> List[Dict]:
        """
        获取所有监控仓库

        Args:
            monitored_only: 是否只返回正在监控的仓库

        Returns:
            仓库列表
        """
        self.connect()
        cursor = self.conn.cursor()

        if monitored_only:
            cursor.execute('SELECT * FROM monitored_repos WHERE is_monitored = 1 ORDER BY added_at DESC')
        else:
            cursor.execute('SELECT * FROM monitored_repos ORDER BY added_at DESC')

        return [dict(row) for row in cursor.fetchall()]

    def get_monitored_repo(self, repo_path: str) -> Optional[Dict]:
        """
        根据路径获取监控仓库

        Args:
            repo_path: 仓库路径

        Returns:
            仓库信息字典,不存在则返回 None
        """
        self.connect()
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM monitored_repos WHERE repo_path = ?', (repo_path,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def update_monitored_repo(self, repo_path: str, update_data: Dict) -> bool:
        """
        更新监控仓库信息

        Args:
            repo_path: 仓库路径
            update_data: 要更新的字段字典

        Returns:
            是否更新成功
        """
        self.connect()
        cursor = self.conn.cursor()

        # 构建更新语句
        update_fields = []
        params = []

        for key, value in update_data.items():
            if key in ['repo_name', 'remote_url', 'current_branch', 'is_monitored',
                      'last_activity_time', 'total_commits', 'total_pushes']:
                update_fields.append(f'{key} = ?')
                params.append(value)

        if not update_fields:
            return False

        # 添加更新时间戳
        update_fields.append('updated_at = ?')
        params.append(datetime.now().isoformat())

        # 添加 repo_path 参数(WHERE 条件)
        params.append(repo_path)

        sql = f'UPDATE monitored_repos SET {", ".join(update_fields)} WHERE repo_path = ?'

        cursor.execute(sql, params)
        self.conn.commit()

        return cursor.rowcount > 0

    def delete_monitored_repo(self, repo_path: str) -> bool:
        """
        删除监控仓库

        Args:
            repo_path: 仓库路径

        Returns:
            是否删除成功
        """
        self.connect()
        cursor = self.conn.cursor()

        cursor.execute('DELETE FROM monitored_repos WHERE repo_path = ?', (repo_path,))
        self.conn.commit()

        return cursor.rowcount > 0

    def update_repo_stats(self, repo_path: str, last_activity_time: str = None):
        """
        更新仓库统计信息

        Args:
            repo_path: 仓库路径
            last_activity_time: 最后活动时间(可选,自动获取最新)
        """
        self.connect()
        cursor = self.conn.cursor()

        # 统计该仓库的提交和推送次数
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN activity_type = 'commit' THEN 1 END) as commits,
                COUNT(CASE WHEN activity_type = 'push' THEN 1 END) as pushes,
                MAX(timestamp) as last_activity
            FROM git_activities
            WHERE repo_path = ?
        ''', (repo_path,))

        result = cursor.fetchone()

        if result and result[0] > 0:  # 有活动记录
            update_data = {
                'total_commits': result[0],
                'total_pushes': result[1],
                'last_activity_time': last_activity_time or result[2]
            }
            self.update_monitored_repo(repo_path, update_data)


if __name__ == '__main__':
    # 测试代码
    with Database() as db:
        # 插入测试数据
        test_data = {
            'activity_type': 'commit',
            'timestamp': datetime.now().isoformat(),
            'repo_path': 'C:/Users/Liang/test/repo',
            'branch_name': 'main',
            'commit_hash': 'abc123',
            'commit_message': 'Test commit',
            'author_name': 'Liang',
            'author_email': 'liang@example.com',
            'files_changed': 3,
            'insertions': 10,
            'deletions': 2
        }
        activity_id = db.insert_activity(test_data)
        print(f'插入记录 ID: {activity_id}')

        # 查询测试
        activities, total = db.get_activities(page=1, page_size=10)
        print(f'总记录数: {total}')
        print(f'查询结果: {activities}')
