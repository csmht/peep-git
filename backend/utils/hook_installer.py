"""
Git Hook 安装工具
为指定的 Git 仓库安装监控 hook
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List


class HookInstaller:
    """Git Hook 安装器"""

    def __init__(self):
        # 获取 GitSee 项目根目录
        self.gitsee_root = Path(__file__).parent.parent.parent.absolute()
        self.hooks_script_dir = self.gitsee_root / 'hooks_global' / 'scripts'

    def install_hook(self, repo_path: str) -> Dict:
        """
        为指定仓库安装 GitSee hook

        Args:
            repo_path: 仓库路径

        Returns:
            安装结果字典
        """
        repo = Path(repo_path)

        # 检查是否是 Git 仓库
        git_dir = repo / '.git'
        if not git_dir.exists():
            return {
                'success': False,
                'error': '不是 Git 仓库',
                'repo_path': repo_path
            }

        # 创建 hooks 目录
        hooks_dir = git_dir / 'hooks'
        hooks_dir.mkdir(exist_ok=True)

        # 检查是否已安装
        post_commit_hook = hooks_dir / 'post-commit'
        if self.is_gitsee_hook_installed(post_commit_hook):
            return {
                'success': True,
                'message': 'Hook 已安装',
                'repo_path': repo_path,
                'already_installed': True
            }

        # 生成 hook 脚本内容
        hook_content = self.generate_hook_script(repo)

        # 写入 hook 脚本
        try:
            with open(post_commit_hook, 'w', encoding='utf-8') as f:
                f.write(hook_content)

            # 设置可执行权限(Linux/Mac)
            try:
                os.chmod(post_commit_hook, 0o755)
            except:
                pass  # Windows 忽略

            return {
                'success': True,
                'message': 'Hook 安装成功',
                'repo_path': repo_path,
                'hook_file': str(post_commit_hook)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'repo_path': repo_path
            }

    def generate_hook_script(self, repo_path: Path) -> str:
        """
        生成 hook 脚本内容

        Args:
            repo_path: 仓库路径

        Returns:
            hook 脚本内容
        """
        gitsee_root_str = str(self.gitsee_root).replace('\\', '/')

        hook_script = f'''#!/bin/bash
# GitSee post-commit hook
# 自动生成,请勿手动修改

REPO_PATH="$(git rev-parse --show-toplevel)"
BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
COMMIT_HASH="$(git rev-parse HEAD)"
COMMIT_MESSAGE="$(git log -1 --pretty=%B)"
AUTHOR_INFO="$(git log -1 --pretty='%an|%ae')"

# 调用 GitSee 捕获脚本
python "{gitsee_root_str}/hooks_global/scripts/capture_commit.py" \\
  --repo "$REPO_PATH" \\
  --branch "$BRANCH_NAME" \\
  --hash "$COMMIT_HASH" \\
  --message "$COMMIT_MESSAGE" \\
  --author "$AUTHOR_INFO"

exit 0
'''

        return hook_script

    def is_gitsee_hook_installed(self, hook_file: Path) -> bool:
        """
        检查是否已安装 GitSee hook

        Args:
            hook_file: hook 文件路径

        Returns:
            是否已安装
        """
        if not hook_file.exists():
            return False

        try:
            with open(hook_file, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'GitSee' in content or 'capture_commit.py' in content
        except Exception:
            return False

    def uninstall_hook(self, repo_path: str) -> Dict:
        """
        卸载 GitSee hook

        Args:
            repo_path: 仓库路径

        Returns:
            卸载结果字典
        """
        repo = Path(repo_path)
        hook_file = repo / '.git' / 'hooks' / 'post-commit'

        if not hook_file.exists():
            return {
                'success': False,
                'error': 'Hook 文件不存在',
                'repo_path': repo_path
            }

        try:
            # 备份原文件
            backup_file = hook_file.with_suffix('.gitsee.bak')
            shutil.copy2(hook_file, backup_file)

            # 删除 hook
            hook_file.unlink()

            return {
                'success': True,
                'message': 'Hook 卸载成功',
                'repo_path': repo_path,
                'backup_file': str(backup_file)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'repo_path': repo_path
            }

    def batch_install(self, repo_paths: List[str]) -> List[Dict]:
        """
        批量安装 hook

        Args:
            repo_paths: 仓库路径列表

        Returns:
            安装结果列表
        """
        results = []

        for repo_path in repo_paths:
            result = self.install_hook(repo_path)
            results.append(result)

        return results

    def check_hook_status(self, repo_path: str) -> Dict:
        """
        检查仓库的 hook 状态

        Args:
            repo_path: 仓库路径

        Returns:
            hook 状态信息
        """
        repo = Path(repo_path)
        hook_file = repo / '.git' / 'hooks' / 'post-commit'

        return {
            'repo_path': repo_path,
            'hook_exists': hook_file.exists(),
            'is_gitsee_hook': self.is_gitsee_hook_installed(hook_file) if hook_file.exists() else False,
            'hook_file': str(hook_file) if hook_file.exists() else None
        }


if __name__ == '__main__':
    # 测试代码
    import sys

    if len(sys.argv) < 2:
        print('用法: python hook_installer.py <仓库路径>')
        sys.exit(1)

    repo_path = sys.argv[1]
    installer = HookInstaller()

    print(f'为仓库安装 hook: {repo_path}')
    result = installer.install_hook(repo_path)

    if result['success']:
        print(f'✓ {result["message"]}')
    else:
        print(f'✗ {result.get("error", "安装失败")}')
