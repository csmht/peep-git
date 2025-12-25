"""
GitSee 安装脚本
自动配置项目环境、初始化数据库、设置 Git 全局 hook
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path


class SetupWizard:
    """安装向导类"""

    def __init__(self):
        # 获取项目根目录
        self.current_dir = Path(__file__).parent.absolute()
        self.data_dir = self.current_dir / 'data'
        self.logs_dir = self.current_dir / 'logs'
        self.hooks_dir = self.current_dir / 'hooks_global' / 'templates' / 'hooks'
        self.db_path = self.data_dir / 'gitsee.db'

    def print_step(self, step_num, total_steps, message):
        """打印安装步骤"""
        print(f'\n[{step_num}/{total_steps}] {message}...')

    def print_success(self, message):
        """打印成功信息"""
        print(f'✓ {message}')

    def print_error(self, message):
        """打印错误信息"""
        print(f'✗ {message}')

    def check_python_version(self):
        """检查 Python 版本"""
        print('\n检查 Python 版本...')

        version = sys.version_info
        version_str = f'{version.major}.{version.minor}.{version.micro}'

        print(f'当前 Python 版本: {version_str}')

        # 检查最低版本要求 (Python 3.7+)
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.print_error(f'Python 版本过低: {version_str}')
            self.print_error('GitSee 需要 Python 3.7 或更高版本')
            print(f'\n当前版本: Python {version_str}')
            print('要求版本: Python 3.7+')
            print('\n建议操作:')
            print('1. 访问 https://www.python.org/downloads/ 下载最新版本')
            print('2. 或使用包管理器升级:')
            print('   Windows: 从官网下载安装程序')
            print('   Linux/Mac: 使用 pyenv 或系统包管理器')

            return False

        self.print_success(f'Python 版本符合要求: {version_str}')

        # 额外检查:推荐 Python 3.8+
        if version.major == 3 and version.minor >= 8:
            print('  提示: 您使用的是 Python 3.8+,这是推荐的版本')
        elif version.major == 3 and version.minor == 7:
            print('  提示: Python 3.7 可用,但建议升级到 3.8+ 以获得更好的性能')

        return True

    def create_directories(self):
        """创建必要的目录结构"""
        self.print_step(1, 6, '创建目录结构')

        directories = [
            self.data_dir,
            self.logs_dir,
            self.hooks_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.print_success(f'创建目录: {directory}')

    def init_database(self):
        """初始化 SQLite 数据库"""
        self.print_step(2, 6, '初始化数据库')

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 创建 git_activities 表
            cursor.execute('''
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

            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON git_activities(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_repo_path
                ON git_activities(repo_path)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_activity_type
                ON git_activities(activity_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_branch_name
                ON git_activities(branch_name)
            ''')

            conn.commit()
            conn.close()

            self.print_success(f'数据库初始化成功: {self.db_path}')

        except Exception as e:
            self.print_error(f'数据库初始化失败: {e}')
            sys.exit(1)

    def setup_git_hooks(self):
        """配置 Git 全局模板目录"""
        self.print_step(3, 6, '配置 Git 全局 hook')

        try:
            # 设置全局模板目录
            template_dir = self.current_dir / 'hooks_global' / 'templates'

            # 执行 git config 命令
            result = subprocess.run(
                ['git', 'config', '--global', 'init.templatedir', str(template_dir)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.print_success(f'Git 全局模板目录已设置: {template_dir}')
            else:
                self.print_error(f'Git 配置失败: {result.stderr}')
                print('  提示: 请确保已安装 Git')

        except Exception as e:
            self.print_error(f'配置 Git hook 失败: {e}')

    def copy_hook_scripts(self):
        """复制 hook 脚本到模板目录"""
        self.print_step(4, 6, '复制 hook 脚本')

        hook_templates = {
            'post-commit': '''#!/bin/bash
# Git post-commit hook - GitSee

REPO_PATH="$(git rev-parse --show-toplevel)"
BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
COMMIT_HASH="$(git rev-parse HEAD)"
COMMIT_MESSAGE="$(git log -1 --pretty=%B)"
AUTHOR_INFO="$(git log -1 --pretty='%an|%ae')"

# 调用 Python 捕获脚本
python "''' + str(self.current_dir) + '''/hooks_global/scripts/capture_commit.py" \\
  --repo "$REPO_PATH" \\
  --branch "$BRANCH_NAME" \\
  --hash "$COMMIT_HASH" \\
  --message "$COMMIT_MESSAGE" \\
  --author "$AUTHOR_INFO"

exit 0
''',
            'post-push': '''#!/bin/bash
# Git post-push hook - GitSee

REPO_PATH="$(git rev-parse --show-toplevel)"
BRANCH_NAME="$(git rev-parse --abbrev-ref HEAD)"
REMOTE="${1:-origin}"

python "''' + str(self.current_dir) + '''/hooks_global/scripts/capture_push.py" \\
  --repo "$REPO_PATH" \\
  --branch "$BRANCH_NAME" \\
  --remote "$REMOTE"

exit 0
'''
        }

        for hook_name, content in hook_templates.items():
            hook_file = self.hooks_dir / hook_name
            with open(hook_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # 设置可执行权限(Unix/Linux/Mac)
            try:
                os.chmod(hook_file, 0o755)
            except:
                pass  # Windows 系统忽略

            self.print_success(f'创建 hook 脚本: {hook_file}')

    def install_dependencies(self):
        """安装 Python 依赖"""
        self.print_step(5, 6, '安装 Python 依赖')

        requirements_file = self.current_dir / 'requirements.txt'

        if not requirements_file.exists():
            self.print_error('requirements.txt 文件不存在')
            return

        try:
            # 检查 pip 是否可用
            subprocess.run(['pip', '--version'], check=True, capture_output=True)

            # 安装依赖
            result = subprocess.run(
                ['pip', 'install', '-r', str(requirements_file)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.print_success('Python 依赖安装完成')
            else:
                self.print_error(f'依赖安装失败: {result.stderr}')
                print('  提示: 请手动运行: pip install -r requirements.txt')

        except FileNotFoundError:
            self.print_error('pip 未找到,请确保已安装 Python 和 pip')
        except subprocess.CalledProcessError:
            self.print_error('pip 命令执行失败')

    def create_config_file(self):
        """创建配置文件"""
        self.print_step(6, 6, '创建配置文件')

        config_file = self.current_dir / 'config.json'

        default_config = {
            "app": {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": False
            },
            "database": {
                "path": str(self.db_path),
                "backup_enabled": True,
                "backup_interval": 86400
            },
            "json_storage": {
                "path": str(self.data_dir / 'records.json'),
                "auto_sync": True,
                "sync_interval": 300
            },
            "logging": {
                "level": "INFO",
                "file": str(self.logs_dir / 'app.log'),
                "max_size": "10MB"
            },
            "features": {
                "auto_refresh": True,
                "refresh_interval": 30,
                "enable_trends": True,
                "enable_export": True
            }
        }

        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

        self.print_success(f'配置文件已创建: {config_file}')

    def run(self):
        """运行安装向导"""
        print('=' * 60)
        print('GitSee 安装向导')
        print('=' * 60)
        print('\n欢迎使用 GitSee!')
        print('本向导将帮助您完成项目配置\n')

        # 首先检查 Python 版本
        if not self.check_python_version():
            print('\n安装已中止')
            sys.exit(1)

        try:
            self.create_directories()
            self.init_database()
            self.setup_git_hooks()
            self.copy_hook_scripts()
            self.install_dependencies()
            self.create_config_file()

            print('\n' + '=' * 60)
            print('安装完成!')
            print('=' * 60)
            print('\n下一步操作:')
            print('1. 为已有仓库启用 hook:')
            print('   cd your-repo')
            print('   git init  # 重新初始化,应用全局模板')
            print('')
            print('2. 启动 Web 服务:')
            print('   python backend/app.py')
            print('   或运行启动脚本: start_server.bat (Windows) / start_server.sh (Linux/Mac)')
            print('')
            print('3. 访问 Web 界面:')
            print('   打开浏览器访问: http://localhost:5000')
            print('')

        except KeyboardInterrupt:
            print('\n\n安装已取消')
            sys.exit(1)
        except Exception as e:
            print(f'\n\n安装过程出现错误: {e}')
            sys.exit(1)


if __name__ == '__main__':
    wizard = SetupWizard()
    wizard.run()
