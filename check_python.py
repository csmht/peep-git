"""
快速检查 Python 版本和环境
用户可以在安装前运行此脚本检查环境是否符合要求
"""

import sys
import subprocess


def check_python_version():
    """检查 Python 版本"""
    print('=' * 60)
    print('GitSee 环境检查工具')
    print('=' * 60)
    print()

    # 显示当前 Python 版本
    version = sys.version_info
    version_str = f'{version.major}.{version.minor}.{version.micro}'
    full_version = sys.version

    print(f'Python 版本: {version_str}')
    print(f'完整信息: {full_version}')
    print()

    # 检查版本是否符合要求
    min_version = (3, 7)
    recommended_version = (3, 8)

    current_version = (version.major, version.minor)

    if current_version < min_version:
        print('[失败] 检查结果: Python 版本过低')
        print(f'   当前版本: {version_str}')
        print(f'   最低要求: 3.7')
        print(f'   推荐版本: 3.8+')
        print()
        print('您的 Python 版本不支持运行 GitSee,请先升级 Python。')
        print()
        print('升级方法:')
        print('  Windows: 访问 https://www.python.org/downloads/')
        print('  macOS:   brew install python3 或 brew upgrade python3')
        print('  Linux:   使用系统包管理器安装 python3.8+')
        return False
    elif current_version < recommended_version:
        print('[警告] 检查结果: Python 版本可用,但建议升级')
        print(f'   当前版本: {version_str}')
        print(f'   推荐版本: 3.8+')
        print()
        print('您的 Python 版本可以运行 GitSee,但建议升级到 3.8+')
        print('以获得更好的性能和新特性支持。')
        return True
    else:
        print('[成功] 检查结果: Python 版本符合要求')
        print(f'   当前版本: {version_str}')
        print()
        print('您的 Python 版本完全支持 GitSee!')
        return True


def check_pip():
    """检查 pip 是否可用"""
    print()
    print('-' * 60)
    print('检查 pip...')
    print()

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', '--version'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f'[成功] pip 可用')
            print(f'   {result.stdout.strip()}')
            return True
        else:
            print('[失败] pip 不可用')
            print('   请安装 pip: python -m ensurepip --upgrade')
            return False

    except Exception as e:
        print(f'[错误] 检查 pip 时出错: {e}')
        return False


def check_git():
    """检查 Git 是否安装"""
    print()
    print('-' * 60)
    print('检查 Git...')
    print()

    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f'[成功] Git 已安装')
            print(f'   {result.stdout.strip()}')
            return True
        else:
            print('[警告] Git 未找到')
            print('   Git 用于 hook 功能,虽然不是必需的,但建议安装')
            print('   下载地址: https://git-scm.com/downloads')
            return False

    except FileNotFoundError:
        print('[警告] Git 未找到')
        print('   Git 用于 hook 功能,虽然不是必需的,但建议安装')
        print('   下载地址: https://git-scm.com/downloads')
        return False
    except Exception as e:
        print(f'[错误] 检查 Git 时出错: {e}')
        return False


def main():
    """主函数"""
    results = {}

    # 检查 Python 版本
    results['python'] = check_python_version()

    # 检查 pip
    results['pip'] = check_pip()

    # 检查 Git
    results['git'] = check_git()

    # 总结
    print()
    print('=' * 60)
    print('检查总结')
    print('=' * 60)
    print()

    if results['python'] and results['pip']:
        print('[成功] 您的环境符合要求,可以安装 GitSee!')
        print()
        print('下一步: 运行安装脚本')
        print('  Windows: python setup.py')
        print('  Linux/Mac: python3 setup.py')
    else:
        print('[失败] 您的环境需要调整后才能安装 GitSee')
        print()
        print('请根据上面的提示解决环境问题')

    print()
    print('=' * 60)


if __name__ == '__main__':
    main()
