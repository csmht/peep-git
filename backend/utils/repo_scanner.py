"""
Git 仓库扫描工具
自动扫描用户系统中的所有 Git 仓库
"""

import os
from pathlib import Path
from typing import List, Dict, Set
import subprocess


class RepoScanner:
    """Git 仓库扫描器"""

    def __init__(self):
        self.scanned_repos = []
        self.excluded_dirs = {
            # Windows 系统目录
            'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
            'C:\\ProgramData', '$RECYCLE.BIN',
            # Linux/Mac 系统目录
            '/bin', '/sbin', '/usr', '/lib', '/etc', '/var',
            '/sys', '/proc', '/dev', '/tmp',
            # 常见排除目录
            'node_modules', '.venv', 'venv', 'env', '.env',
            '__pycache__', '.git', '.vscode', '.idea',
            'target', 'build', 'dist', '.next', '.nuxt'
        }

    def is_git_repo(self, path: Path) -> bool:
        """
        检查目录是���是 Git 仓库

        Args:
            path: 目录路径

        Returns:
            是否是 Git 仓库
        """
        git_dir = path / '.git'
        return git_dir.exists() and git_dir.is_dir()

    def is_excluded(self, path: Path) -> bool:
        """
        检查路径是否应该被排除

        Args:
            path: 目录路径

        Returns:
            是否应该排除
        """
        path_str = str(path)

        # 检查是否在排除列表中
        for excluded in self.excluded_dirs:
            if excluded in path_str:
                return True

        # 检查是否是隐藏目录
        if path.name.startswith('.') and path.name not in ['.git']:
            return True

        return False

    def scan_directory(self, root_path: str, max_depth: int = 5) -> List[Dict]:
        """
        扫描指定目录下的所有 Git 仓库

        Args:
            root_path: 根目录路径
            max_depth: 最大扫描深度

        Returns:
            Git 仓库列表
        """
        root = Path(root_path)

        if not root.exists():
            return []

        repos = []
        self._scan_recursive(root, 0, max_depth, repos)

        return repos

    def _scan_recursive(self, current_path: Path, current_depth: int, max_depth: int, repos: List[Dict]):
        """
        递归扫描目录

        Args:
            current_path: 当前路径
            current_depth: 当前深度
            max_depth: 最大深度
            repos: 仓库列表(引用传递)
        """
        # 超过最大深度
        if current_depth > max_depth:
            return

        # 排除特定目录
        if self.is_excluded(current_path):
            return

        # 检查是否是 Git 仓库
        if self.is_git_repo(current_path):
            repo_info = self.get_repo_info(current_path)
            if repo_info:
                repos.append(repo_info)
            return  # 不继续扫描仓库内部

        # 递归扫描子目录
        try:
            for item in current_path.iterdir():
                if item.is_dir():
                    self._scan_recursive(item, current_depth + 1, max_depth, repos)
        except PermissionError:
            pass  # 无权限访问,跳过

    def get_repo_info(self, repo_path: Path) -> Dict:
        """
        获取仓库信息

        Args:
            repo_path: 仓库路径

        Returns:
            仓库信息字典
        """
        try:
            # 获取仓库基本信息
            repo_path_str = str(repo_path.absolute())

            # 尝试获取仓库名称
            name = repo_path.name

            # 尝试获取远程仓库 URL
            remote_url = self.get_remote_url(repo_path)

            # 获取当前分支
            branch = self.get_current_branch(repo_path)

            return {
                'path': repo_path_str,
                'name': name,
                'remote_url': remote_url,
                'current_branch': branch,
                'is_monitored': self.has_hook_installed(repo_path)
            }

        except Exception:
            return None

    def get_remote_url(self, repo_path: Path) -> str:
        """
        获取远程仓库 URL

        Args:
            repo_path: 仓库路径

        Returns:
            远程仓库 URL
        """
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception:
            pass

        return ''

    def get_current_branch(self, repo_path: Path) -> str:
        """
        获取当前分支名称

        Args:
            repo_path: 仓库路径

        Returns:
            分支名称
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception:
            pass

        return ''

    def has_hook_installed(self, repo_path: Path) -> bool:
        """
        检查仓库是否已安装 GitSee hook

        Args:
            repo_path: 仓库路径

        Returns:
            是否已安装 hook
        """
        hook_file = repo_path / '.git' / 'hooks' / 'post-commit'

        if not hook_file.exists():
            return False

        try:
            with open(hook_file, 'r', encoding='utf-8') as f:
                content = f.read()
                return 'GitSee' in content or 'capture_commit.py' in content

        except Exception:
            return False

    def scan_common_directories(self) -> List[Dict]:
        """
        扫描常见目录(用户主目录、桌面、文档等)

        Returns:
            Git 仓库列表
        """
        repos = []
        home = Path.home()

        # 常见扫描目录
        common_dirs = [
            home,  # 用户主目录
            home / 'Desktop',
            home / 'Documents',
            home / 'projects',
            home / 'Projects',
            home / 'workspace',
            home / 'Workspace',
            home / 'code',
            home / 'Code',
            home / 'Work',  # 工作目录
        ]

        for directory in common_dirs:
            if directory.exists():
                print(f'扫描目录: {directory}')
                found_repos = self.scan_directory(str(directory), max_depth=4)
                repos.extend(found_repos)

        # 去重
        unique_repos = []
        seen_paths = set()

        for repo in repos:
            if repo['path'] not in seen_paths:
                unique_repos.append(repo)
                seen_paths.add(repo['path'])

        return unique_repos

    def scan_custom_directories(self, directories: List[str], max_depth: int = 5) -> List[Dict]:
        """
        扫描自定义目录列表

        Args:
            directories: 目录路径列表
            max_depth: 最大扫描深度

        Returns:
            Git 仓库列表
        """
        repos = []

        for directory in directories:
            # 确保目录是字符串
            directory_str = str(directory)

            if os.path.exists(directory_str):
                print(f'扫描目录: {directory_str}')
                found_repos = self.scan_directory(directory_str, max_depth=max_depth)
                repos.extend(found_repos)

        # 去重
        unique_repos = []
        seen_paths = set()

        for repo in repos:
            if repo['path'] not in seen_paths:
                unique_repos.append(repo)
                seen_paths.add(repo['path'])

        return unique_repos


if __name__ == '__main__':
    # 测试代码
    scanner = RepoScanner()

    print('开始扫描 Git 仓库...')
    repos = scanner.scan_common_directories()

    print(f'\n找到 {len(repos)} 个 Git 仓库:')
    for repo in repos:
        print(f"  - {repo['name']}")
        print(f"    路径: {repo['path']}")
        print(f"    分支: {repo['current_branch']}")
        print(f"    远程: {repo['remote_url'] or '无'}")
        print(f"    已监控: {'是' if repo['is_monitored'] else '否'}")
        print()
