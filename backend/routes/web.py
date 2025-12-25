"""
Web 页面路由模块
负责处理前端页面请求
"""

from flask import Blueprint, render_template

# 创建 Web 蓝图
web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """首页 - 仪表盘"""
    return render_template('dashboard.html')


@web_bp.route('/dashboard')
def dashboard():
    """仪表盘页面"""
    return render_template('dashboard.html')


@web_bp.route('/details')
def details():
    """详细记录页面"""
    return render_template('details.html')


@web_bp.route('/repositories')
def repositories():
    """仓库管理页面"""
    return render_template('repositories.html')
