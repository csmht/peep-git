"""
Flask 应用主入口
"""

import os
import sys
from flask import Flask

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.routes.api import api_bp
from backend.routes.web import web_bp
from backend.routes.repo_management import repo_management_bp
from backend.models.storage_manager import BackgroundSyncThread, StorageManager
import threading


def create_app():
    """
    创建 Flask 应用实例

    Returns:
        Flask 应用对象
    """
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    # 创建 Flask 应用
    app = Flask(__name__,
                template_folder=os.path.join(project_root, 'frontend', 'templates'),
                static_folder=os.path.join(project_root, 'frontend', 'static'))

    # 注册蓝图
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(web_bp)
    app.register_blueprint(repo_management_bp)

    # 启动后台同步线程
    start_background_sync()

    return app


def start_background_sync():
    """启动后台同步线程"""
    try:
        storage_manager = StorageManager()
        sync_thread = BackgroundSyncThread(storage_manager, interval_seconds=300)  # 5 分钟
        sync_thread.start()
        print('后台同步线程已启动')
    except Exception as e:
        print(f'启动后台同步线程失败: {e}')


if __name__ == '__main__':
    # 创建应用
    app = create_app()

    # 获取配置
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f'GitSee 服务启动中...')
    print(f'访问地址: http://localhost:{port}')
    print(f'按 Ctrl+C 停止服务')

    # 运行应用
    app.run(host=host, port=port, debug=debug)
