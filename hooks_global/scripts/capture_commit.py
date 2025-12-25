"""
Git commit 事件捕获脚本
由 post-commit hook 调用,用于��录提交信息到数据库
"""

import argparse
import sys
import os
import subprocess
from datetime import datetime
import json

# 添加项目路径到 sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.models.database import Database


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='捕获 Git commit 事件')
    parser.add_argument('--repo', required=True, help='仓库路径')
    parser.add_argument('--branch', required=True, help='分支名称')
    parser.add_argument('--hash', required=True, help='提交哈希')
    parser.add_argument('--message', required=True, help='提交消息')
    parser.add_argument('--author', required=True, help='作者信息(格式: 名称|邮箱)')
    return parser.parse_args()


def get_file_stats(repo_path, commit_hash):
    """
    获取文件变更统计

    Args:
        repo_path: 仓库路径
        commit_hash: 提交哈希

    Returns:
        (变更文件数, 新增行数, 删除行数)
    """
    try:
        # 获取与上一次提交的差异统计
        cmd = [
            'git', 'diff', '--shortstat',
            f'{commit_hash}~1', commit_hash
        ]
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout.strip()
        if not output:
            return 0, 0, 0

        # 解析输出格式: "3 files changed, 15 insertions(+), 5 deletions(-)"
        files_changed = 0
        insertions = 0
        deletions = 0

        # 提取文件数
        if 'file' in output:
            parts = output.split()[0]
            files_changed = int(parts)

        # 提取新增行数
        if 'insertion' in output:
            for part in output.split(','):
                if 'insertion' in part:
                    insertions = int(part.strip().split()[0])

        # 提取删除行数
        if 'deletion' in output:
            for part in output.split(','):
                if 'deletion' in part:
                    deletions = int(part.strip().split()[0])

        return files_changed, insertions, deletions

    except Exception as e:
        print(f'获取文件统计失败: {e}', file=sys.stderr)
        return 0, 0, 0


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

    # 解析作者信息
    author_parts = args.author.split('|')
    author_name = author_parts[0] if len(author_parts) > 0 else 'Unknown'
    author_email = author_parts[1] if len(author_parts) > 1 else ''

    # 规范化仓库路径(统一使用正斜杠)
    repo_path = args.repo.replace('\\', '/')

    # 获取文件变更统计
    files_changed, insertions, deletions = get_file_stats(args.repo, args.hash)

    # 构建活动数据
    activity_data = {
        'activity_type': 'commit',
        'timestamp': datetime.now().isoformat(),
        'repo_path': repo_path,
        'branch_name': args.branch,
        'commit_hash': args.hash,
        'commit_message': args.message,
        'author_name': author_name,
        'author_email': author_email,
        'files_changed': files_changed,
        'insertions': insertions,
        'deletions': deletions
    }

    # 保存到数据库
    activity_id = save_activity(activity_data)

    if activity_id:
        print(f'成功记录 commit 事件, ID: {activity_id}')
        return 0
    else:
        print('记录 commit 事件失败', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
