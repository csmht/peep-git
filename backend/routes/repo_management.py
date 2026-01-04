"""
仓库管理 API 路由
提供仓库扫描、添加、删除等功能�� API 端点
"""

from flask import Blueprint, jsonify, request
from backend.utils.repo_scanner import RepoScanner
from backend.utils.hook_installer import HookInstaller
from backend.models.database import Database
import os

# 创建仓库管理蓝图
repo_management_bp = Blueprint('repo_management', __name__, url_prefix='/api/v1/repos')


@repo_management_bp.route('/scan', methods=['POST'])
def scan_repos():
    """
    扫描 Git 仓库

    Request Body:
        {
            "directories": ["路径1", "路径2"],  // 可选,不指定则扫描常见目录
            "max_depth": 5  // 可选,扫描深度
        }

    Returns:
        扫描到的仓库列表
    """
    try:
        data = request.get_json() or {}
        directories = data.get('directories', [])
        max_depth = data.get('max_depth', 5)

        scanner = RepoScanner()

        if directories:
            # 扫描指定目录
            repos = scanner.scan_custom_directories(directories, max_depth=max_depth)
        else:
            # 扫描常见目录
            repos = scanner.scan_common_directories()

        return jsonify({
            'success': True,
            'data': {
                'count': len(repos),
                'repos': repos
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@repo_management_bp.route('/add', methods=['POST'])
def add_repo():
    """
    添加监控仓库

    Request Body:
        {
            "repo_path": "仓库路径",
            "install_hook": true  // 是否安装 hook
        }

    Returns:
        添加结果
    """
    try:
        data = request.get_json()
        repo_path = data.get('repo_path')
        install_hook = data.get('install_hook', True)

        if not repo_path:
            return jsonify({
                'success': False,
                'error': '仓库路径不能为空'
            }), 400

        # 检查仓库是否存在
        if not os.path.exists(repo_path):
            return jsonify({
                'success': False,
                'error': '仓库路径不存在'
            }), 404

        from pathlib import Path
        scanner = RepoScanner()
        installer = HookInstaller()

        # 转换为 Path 对象
        repo_path_obj = Path(repo_path)

        # 检查是否是 Git 仓库
        if not scanner.is_git_repo(repo_path_obj):
            return jsonify({
                'success': False,
                'error': '不是 Git 仓库'
            }), 400

        # 获取仓库信息
        repo_info = scanner.get_repo_info(repo_path_obj)

        if not repo_info:
            return jsonify({
                'success': False,
                'error': '无法获取仓库信息'
            }), 500

        # 安装 hook
        hook_result = None
        if install_hook:
            hook_result = installer.install_hook(repo_path)
            repo_info['is_monitored'] = hook_result['success']

        # 添加到数据库
        db = Database()
        repo_id = db.add_monitored_repo({
            'repo_path': repo_info['path'],
            'repo_name': repo_info['name'],
            'remote_url': repo_info.get('remote_url', ''),
            'current_branch': repo_info.get('current_branch', ''),
            'is_monitored': repo_info['is_monitored']
        })
        db.close()

        return jsonify({
            'success': True,
            'data': {
                'repo_id': repo_id,
                'repo_info': repo_info,
                'hook_result': hook_result
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@repo_management_bp.route('/list', methods=['GET'])
def list_repos():
    """
    获取监控仓库列表

    Query Parameters:
        monitored_only: 是否只返回正在监控的仓库

    Returns:
        仓库列表,按总活动数(提交数+推送数)降序排列
    """
    try:
        monitored_only = request.args.get('monitored_only', 'false').lower() == 'true'

        db = Database()
        repos = db.get_monitored_repos(monitored_only=monitored_only)

        # 更新每个仓库的统计数据
        for repo in repos:
            db.update_repo_stats(repo['repo_path'])

        # 重新获取更新后的数据
        repos = db.get_monitored_repos(monitored_only=monitored_only)

        # 按总活动数(提交数+推送数)降序排序
        for repo in repos:
            repo['total_activities'] = (repo.get('total_commits', 0) +
                                       repo.get('total_pushes', 0))

        repos.sort(key=lambda x: x['total_activities'], reverse=True)

        db.close()

        return jsonify({
            'success': True,
            'data': {
                'count': len(repos),
                'repos': repos
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@repo_management_bp.route('/<path:repo_path>/info', methods=['GET'])
def get_repo_info(repo_path):
    """
    获取仓库详细信息

    Args:
        repo_path: 仓库路径

    Returns:
        仓库详细信息
    """
    try:
        db = Database()
        repo = db.get_monitored_repo(repo_path)

        if not repo:
            return jsonify({
                'success': False,
                'error': '仓库不存在'
            }), 404

        # 获取 hook 状态
        installer = HookInstaller()
        hook_status = installer.check_hook_status(repo_path)

        repo['hook_status'] = hook_status

        db.close()

        return jsonify({
            'success': True,
            'data': repo
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@repo_management_bp.route('/<path:repo_path>/install-hook', methods=['POST'])
def install_hook(repo_path):
    """
    为仓库安装 GitSee hook

    Args:
        repo_path: 仓库路径

    Returns:
        安装结果
    """
    try:
        installer = HookInstaller()
        result = installer.install_hook(repo_path)

        if result['success']:
            # 更新数据库中的监控状态
            db = Database()
            db.update_monitored_repo(repo_path, {'is_monitored': True})
            db.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@repo_management_bp.route('/<path:repo_path>/uninstall-hook', methods=['POST'])
def uninstall_hook(repo_path):
    """
    卸载仓库的 GitSee hook

    Args:
        repo_path: 仓库路径

    Returns:
        卸载结果
    """
    try:
        installer = HookInstaller()
        result = installer.uninstall_hook(repo_path)

        if result['success']:
            # 更新数据库中的监控状态
            db = Database()
            db.update_monitored_repo(repo_path, {'is_monitored': False})
            db.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@repo_management_bp.route('/<path:repo_path>', methods=['DELETE'])
def delete_repo(repo_path):
    """
    删除监控仓库

    Args:
        repo_path: 仓库路径

    Returns:
        删除结果
    """
    try:
        db = Database()
        success = db.delete_monitored_repo(repo_path)
        db.close()

        if success:
            return jsonify({
                'success': True,
                'message': '仓库已删除'
            })
        else:
            return jsonify({
                'success': False,
                'error': '仓库不存在'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@repo_management_bp.route('/batch-add', methods=['POST'])
def batch_add_repos():
    """
    批量添加仓库

    Request Body:
        {
            "repo_paths": ["路径1", "路径2"],
            "install_hooks": true
        }

    Returns:
        批量添加结果
    """
    try:
        data = request.get_json()
        repo_paths = data.get('repo_paths', [])
        install_hooks = data.get('install_hooks', True)

        results = []
        installer = HookInstaller()
        db = Database()

        for repo_path in repo_paths:
            # 检查是否是 Git 仓库
            from pathlib import Path
            repo_path_obj = Path(repo_path)
            scanner = RepoScanner()

            if not scanner.is_git_repo(repo_path_obj):
                results.append({
                    'repo_path': repo_path,
                    'success': False,
                    'error': '不是 Git 仓库'
                })
                continue

            # 获取仓库信息
            repo_info = scanner.get_repo_info(repo_path_obj)

            if not repo_info:
                results.append({
                    'repo_path': repo_path,
                    'success': False,
                    'error': '无法获取仓库信息'
                })
                continue

            # 安装 hook
            hook_result = None
            if install_hooks:
                hook_result = installer.install_hook(repo_path)
                repo_info['is_monitored'] = hook_result['success']

            # 添加到数据库
            repo_id = db.add_monitored_repo({
                'repo_path': repo_info['path'],
                'repo_name': repo_info['name'],
                'remote_url': repo_info.get('remote_url', ''),
                'current_branch': repo_info.get('current_branch', ''),
                'is_monitored': repo_info['is_monitored']
            })

            results.append({
                'repo_path': repo_path,
                'success': True,
                'repo_id': repo_id,
                'repo_info': repo_info,
                'hook_result': hook_result
            })

        db.close()

        return jsonify({
            'success': True,
            'data': {
                'total': len(repo_paths),
                'successful': sum(1 for r in results if r['success']),
                'failed': sum(1 for r in results if not r['success']),
                'results': results
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
