"""
双存储管理器
负责在 SQLite 和 JSON 之间保持数据同步
"""

import os
import json
import threading
from datetime import datetime
from typing import Dict, List
from filelock import FileLock

from backend.models.database import Database


class StorageManager:
    """双存储管理器类"""

    def __init__(self, db_path: str = None, json_path: str = None):
        """
        初始化存储管理器

        Args:
            db_path: SQLite 数据库路径
            json_path: JSON 文件路径
        """
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        data_dir = os.path.join(current_dir, 'data')

        if db_path is None:
            db_path = os.path.join(data_dir, 'gitsee.db')
        if json_path is None:
            json_path = os.path.join(data_dir, 'records.json')

        self.db_path = db_path
        self.json_path = json_path
        self.lock_path = json_path + '.lock'

        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)

        # 初始化 JSON 文件
        self._init_json_file()

    def _init_json_file(self):
        """初始化 JSON 文件(如果不存在)"""
        if not os.path.exists(self.json_path):
            initial_data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'activities': [],
                'statistics': {
                    'total_commits': 0,
                    'total_pushes': 0,
                    'most_active_repo': '',
                    'most_active_branch': ''
                }
            }
            self._write_json(initial_data)

    def _read_json(self) -> Dict:
        """
        读取 JSON 文件

        Returns:
            JSON 数据字典
        """
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 文件不存在或损坏,返回初始数据
            return {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'activities': [],
                'statistics': {
                    'total_commits': 0,
                    'total_pushes': 0,
                    'most_active_repo': '',
                    'most_active_branch': ''
                }
            }

    def _write_json(self, data: Dict):
        """
        写入 JSON 文件(使用文件锁)

        Args:
            data: 要写入的数据字典
        """
        with FileLock(self.lock_path, timeout=10):
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def save_activity(self, activity_data: Dict) -> int:
        """
        双写策略: 保存活动记录到 SQLite 和 JSON

        Args:
            activity_data: 活动数据字典

        Returns:
            新插入记录的 ID,失败返回 -1
        """
        try:
            # 1. 先写入 SQLite(使用事务保证原子性)
            db = Database(self.db_path)
            activity_id = db.insert_activity(activity_data)
            db.close()

            if activity_id <= 0:
                raise Exception('数据库插入失败')

            # 2. 更新 JSON 缓存
            activity_data['id'] = activity_id
            self._update_json_cache(activity_data)

            return activity_id

        except Exception as e:
            print(f'保存活动记录失败: {e}')
            return -1

    def _update_json_cache(self, activity_data: Dict):
        """
        增量更新 JSON 缓存

        Args:
            activity_data: 新的活动数据
        """
        try:
            # 读取现有数据
            data = self._read_json()

            # 添加新活动
            data['activities'].insert(0, activity_data)  # 插入到开头

            # 限制活动记录数量(保留最近 1000 条)
            if len(data['activities']) > 1000:
                data['activities'] = data['activities'][:1000]

            # 更新时间戳
            data['last_updated'] = datetime.now().isoformat()

            # 重新计算统计
            data['statistics'] = self._calculate_statistics(data['activities'])

            # 写入文件
            self._write_json(data)

        except Exception as e:
            print(f'更新 JSON 缓存失败: {e}')

    def _calculate_statistics(self, activities: List[Dict]) -> Dict:
        """
        计算统计数据

        Args:
            activities: 活动记录列表

        Returns:
            统计数据字典
        """
        total_commits = sum(1 for a in activities if a['activity_type'] == 'commit')
        total_pushes = sum(1 for a in activities if a['activity_type'] == 'push')

        # 找出最活跃的仓库
        repo_counts = {}
        for activity in activities:
            repo = activity['repo_path']
            repo_counts[repo] = repo_counts.get(repo, 0) + 1

        most_active_repo = max(repo_counts.keys(), key=lambda k: repo_counts[k]) if repo_counts else ''

        # 找出最活跃的分支
        branch_counts = {}
        for activity in activities:
            branch = activity['branch_name']
            branch_counts[branch] = branch_counts.get(branch, 0) + 1

        most_active_branch = max(branch_counts.keys(), key=lambda k: branch_counts[k]) if branch_counts else ''

        return {
            'total_commits': total_commits,
            'total_pushes': total_pushes,
            'most_active_repo': most_active_repo,
            'most_active_branch': most_active_branch
        }

    def sync_from_db_to_json(self) -> bool:
        """
        全量同步: 从数据库重建 JSON

        Returns:
            同步是否成功
        """
        try:
            # 从数据库读取所有数据
            db = Database(self.db_path)
            activities = db.get_all_activities()
            db.close()

            # 构建 JSON 数据
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'activities': activities,
                'statistics': self._calculate_statistics(activities)
            }

            # 写入 JSON 文件
            self._write_json(data)

            return True

        except Exception as e:
            print(f'数据库到 JSON 同步失败: {e}')
            return False

    def get_activities_from_json(self, limit: int = None) -> List[Dict]:
        """
        从 JSON 读取活动记录

        Args:
            limit: 限制返回数量

        Returns:
            活动记录列表
        """
        data = self._read_json()
        activities = data.get('activities', [])

        if limit and len(activities) > limit:
            activities = activities[:limit]

        return activities

    def get_statistics_from_json(self) -> Dict:
        """
        从 JSON 读取统计数据

        Returns:
            统计数据字典
        """
        data = self._read_json()
        return data.get('statistics', {})

    def backup_json(self, backup_count: int = 7):
        """
        备份 JSON 文件

        Args:
            backup_count: 保留的备份数量
        """
        try:
            if not os.path.exists(self.json_path):
                return

            # 创建备份目录
            backup_dir = os.path.join(os.path.dirname(self.json_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)

            # 生成备份文件名(带时间戳)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'records_{timestamp}.json')

            # 复制文件
            import shutil
            shutil.copy2(self.json_path, backup_path)

            # 清理旧备份(保留最近的 N 个)
            backups = sorted(
                [f for f in os.listdir(backup_dir) if f.startswith('records_')],
                reverse=True
            )

            for old_backup in backups[backup_count:]:
                os.remove(os.path.join(backup_dir, old_backup))

        except Exception as e:
            print(f'备份 JSON 失败: {e}')

    def restore_from_backup(self, backup_file: str = None) -> bool:
        """
        从备份恢复 JSON 文件

        Args:
            backup_file: 备份文件路径,不指定则使用最新的备份

        Returns:
            恢复是否成功
        """
        try:
            backup_dir = os.path.join(os.path.dirname(self.json_path), 'backups')

            if backup_file is None:
                # 找到最新的备份
                backups = sorted(
                    [f for f in os.listdir(backup_dir) if f.startswith('records_')],
                    reverse=True
                )
                if not backups:
                    return False
                backup_file = os.path.join(backup_dir, backups[0])
            else:
                backup_file = os.path.join(backup_dir, backup_file)

            if not os.path.exists(backup_file):
                return False

            # 恢复文件
            import shutil
            shutil.copy2(backup_file, self.json_path)

            return True

        except Exception as e:
            print(f'从备份恢复失败: {e}')
            return False


# 后台同步线程
class BackgroundSyncThread(threading.Thread):
    """后台同步线程,定期执行数据库到 JSON 的全量同步"""

    def __init__(self, storage_manager: StorageManager, interval_seconds: int = 300):
        """
        初始化后台同步线程

        Args:
            storage_manager: 存储管理器实例
            interval_seconds: 同步间隔(秒),默认 5 分钟
        """
        super().__init__(daemon=True)
        self.storage_manager = storage_manager
        self.interval_seconds = interval_seconds
        self.running = False

    def run(self):
        """线程主循环"""
        self.running = True
        while self.running:
            try:
                # 执行同步
                self.storage_manager.sync_from_db_to_json()
                # 创建备份
                self.storage_manager.backup_json()
            except Exception as e:
                print(f'后台同步失败: {e}')

            # 等待下一次同步
            import time
            time.sleep(self.interval_seconds)

    def stop(self):
        """停止线程"""
        self.running = False


if __name__ == '__main__':
    # 测试代码
    manager = StorageManager()

    # 测试同步
    print('测试数据库到 JSON 同步...')
    success = manager.sync_from_db_to_json()
    print(f'同步结果: {"成功" if success else "失败"}')

    # 测试读取
    activities = manager.get_activities_from_json(limit=5)
    print(f'读取到 {len(activities)} 条活动记录')

    stats = manager.get_statistics_from_json()
    print(f'统计数据: {stats}')
