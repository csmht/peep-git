"""
Git push 事件捕获脚本
由 post-push hook 调用,用于记录推送信息到数据库
"""

import argparse
import sys
import os
from datetime import datetime

# 添加项目路径到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.models.database import Database


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='捕获 Git push 事件')
    parser.add_argument('--repo', required=True, help='仓库路径')
    parser.add_argument('--branch', required=True, help='分支名称')
    parser.add_argument('--remote', default='origin', help='远程仓库名称')
    parser.add_argument('--commit-hash', help='最新的提交哈希(可选)')
    return parser.parse_args()


def get_latest_commit_hash(repo_path, branch):
    """
    获取分支最新的提交哈希

    Args:
        repo_path: 仓库路径
        branch: 分支名称

    Returns:
        提交哈希字符串,失败返回空字符串
    """
    try:
        import subprocess
        cmd = ['git', 'rev-parse', branch]
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception:
        return ''


def save_activity(data):
    """
    保存活动记录到数据库

    Args:
        data: 活动数据字典

    Returns:
        新插入记录的 ID,失败返回 None
    """
    try:
        db = Database()
        activity_id = db.insert_activity(data)
        db.close()
        return activity_id
    except Exception as e:
        print(f'保存到数据库失败: {e}', file=sys.stderr)
        return None


def main():
    """主函数"""
    args = parse_args()

    # 规范化仓库路径(统一使用正斜杠)
    repo_path = args.repo.replace('\\', '/')

    # 如果没有提供提交哈希,尝试获取最新的
    commit_hash = args.commit_hash
    if not commit_hash:
        commit_hash = get_latest_commit_hash(args.repo, args.branch)

    if not commit_hash:
        commit_hash = 'unknown'

    # 构建活动数据
    activity_data = {
        'activity_type': 'push',
        'timestamp': datetime.now().isoformat(),
        'repo_path': repo_path,
        'branch_name': args.branch,
        'commit_hash': commit_hash,
        'commit_message': '',  # push 不记录具体消息
        'author_name': '',     # push 可以从 commit 获取,但这里简化为空
        'author_email': '',
        'files_changed': 0,
        'insertions': 0,
        'deletions': 0
    }

    # 保存到数据库
    activity_id = save_activity(activity_data)

    if activity_id:
        print(f'成功记录 push 事件, ID: {activity_id}')
        return 0
    else:
        print('记录 push 事件失败', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
