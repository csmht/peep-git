"""
Flask API 路由模块
提供 RESTful API 端点供前端调用
"""

from flask import Blueprint, jsonify, request, send_file, current_app
from backend.services.statistics import StatisticsService
from backend.services.ai_evaluator import AIEvaluator
from backend.models.database import Database
from backend.models.storage_manager import StorageManager
import csv
from io import StringIO
from datetime import datetime, date
import os
import json
import logging

# 创建 logger
logger = logging.getLogger(__name__)

# 创建 API 蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    获取活动统计

    Query Parameters:
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        repo_path: 仓库路径筛选

    Returns:
        JSON 格式的统计数据
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        repo_path = request.args.get('repo_path')

        service = StatisticsService()
        stats = service.get_statistics(start_date, end_date, repo_path)
        service.close()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/activities', methods=['GET'])
def get_activities():
    """
    获取活动列表

    Query Parameters:
        page: 页码(从 1 开始)
        page_size: 每页记录数
        activity_type: 活动类型(commit/push)
        repo_path: 仓库路径筛选
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        分页的活动记录列表
    """
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        activity_type = request.args.get('activity_type')
        repo_path = request.args.get('repo_path')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        db = Database()
        activities, total = db.get_activities(
            page=page,
            page_size=page_size,
            activity_type=activity_type,
            repo_path=repo_path,
            start_date=start_date,
            end_date=end_date
        )
        db.close()

        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'page': page,
                'page_size': page_size,
                'activities': activities
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/activities/<int:activity_id>', methods=['GET'])
def get_activity_detail(activity_id):
    """
    获取单个活动详情

    Args:
        activity_id: 活动 ID

    Returns:
        活动详情数据
    """
    try:
        db = Database()
        activity = db.get_activity_by_id(activity_id)
        db.close()

        if activity:
            return jsonify({
                'success': True,
                'data': activity
            })
        else:
            return jsonify({
                'success': False,
                'error': '活动记录不存在'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/trends', methods=['GET'])
def get_trends():
    """
    获取趋势数据

    Query Parameters:
        period: 时间周期(day/week/month)
        repo_path: 仓库路径筛选
        days: 返回最近几天的数据

    Returns:
        趋势数据列表
    """
    try:
        period = request.args.get('period', 'day')
        repo_path = request.args.get('repo_path')
        days = int(request.args.get('days', 30))

        service = StatisticsService()
        trends = service.get_trends(period=period, repo_path=repo_path, days=days)
        service.close()

        return jsonify({
            'success': True,
            'data': trends
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/repos/top', methods=['GET'])
def get_top_repos():
    """
    获取最活跃的仓库列表

    Query Parameters:
        limit: 返回数量
        days: 统计最近几天的数据

    Returns:
        仓库列表
    """
    try:
        limit = int(request.args.get('limit', 10))
        days = int(request.args.get('days', 30))

        service = StatisticsService()
        repos = service.get_top_repos(limit=limit, days=days)
        service.close()

        return jsonify({
            'success': True,
            'data': repos
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/repos/<path:repo_path>/summary', methods=['GET'])
def get_repo_summary(repo_path):
    """
    获取指定仓库的汇总信息

    Args:
        repo_path: 仓库路径

    Query Parameters:
        days: 统计最近几天的数据

    Returns:
        仓库汇总数据
    """
    try:
        days = int(request.args.get('days', 30))

        service = StatisticsService()
        summary = service.get_repo_summary(repo_path, days)
        service.close()

        return jsonify({
            'success': True,
            'data': summary
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/heatmap', methods=['GET'])
def get_heatmap():
    """
    获取活动热力图数据

    Query Parameters:
        days: 统计最近几天的数据

    Returns:
        热力图数据列表
    """
    try:
        days = int(request.args.get('days', 90))

        service = StatisticsService()
        heatmap = service.get_daily_activity_heatmap(days=days)
        service.close()

        return jsonify({
            'success': True,
            'data': heatmap
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/authors', methods=['GET'])
def get_authors():
    """
    获取作者统计信息

    Query Parameters:
        repo_path: 仓库路径筛选

    Returns:
        作者统计列表
    """
    try:
        repo_path = request.args.get('repo_path')

        service = StatisticsService()
        authors = service.get_author_stats(repo_path)
        service.close()

        return jsonify({
            'success': True,
            'data': authors
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/export', methods=['GET'])
def export_data():
    """
    导出数据

    Query Parameters:
        format: 导出格式(json/csv)
        start_date: 开始日期
        end_date: 结束日期
        repo_path: 仓库路径筛选

    Returns:
        文件下载
    """
    try:
        export_format = request.args.get('format', 'json')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        repo_path = request.args.get('repo_path')

        db = Database()
        activities, total = db.get_activities(
            page=1,
            page_size=100000,  # 获取大量数据
            start_date=start_date,
            end_date=end_date,
            repo_path=repo_path
        )
        db.close()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if export_format == 'csv':
            # 导出为 CSV
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'id', 'activity_type', 'timestamp', 'repo_path', 'branch_name',
                'commit_hash', 'commit_message', 'author_name', 'files_changed',
                'insertions', 'deletions'
            ])
            writer.writeheader()
            for activity in activities:
                writer.writerow(activity)

            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'gitsee_export_{timestamp}.csv'
            )

        else:
            # 默认导出为 JSON
            return jsonify({
                'success': True,
                'data': {
                    'export_time': datetime.now().isoformat(),
                    'total_records': total,
                    'activities': activities
                }
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/sync', methods=['POST'])
def sync_data():
    """
    手动触发数据同步(SQLite -> JSON)

    Returns:
        同步结果
    """
    try:
        storage_manager = StorageManager()
        success = storage_manager.sync_from_db_to_json()

        if success:
            return jsonify({
                'success': True,
                'message': '数据同步成功',
                'synced_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '数据同步失败'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点

    Returns:
        服务状态信息
    """
    try:
        db = Database()
        # 执行简单查询测试数据库连接
        activities, total = db.get_activities(page=1, page_size=1)
        db.close()

        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'total_records': total,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@api_bp.errorhandler(404)
def not_found(error):
    """处理 404 错误"""
    return jsonify({
        'success': False,
        'error': 'API 端点不存在'
    }), 404


@api_bp.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


@api_bp.route('/today-summary', methods=['GET'])
def get_today_summary():
    """
    获取今日活动总结

    Returns:
        今日统计信息和 AI 评价
    """
    try:
        # 获取今日日期
        today = date.today().strftime('%Y-%m-%d')
        print(f"[DEBUG API] Today is: {today}")

        # 获取今日统计
        db = Database()
        activities, total = db.get_activities(
            page=1,
            page_size=1000,
            start_date=today,
            end_date=today
        )
        logger.info(f"Today summary query: date={today}, found {total} activities")
        db.close()

        # 计算统计信息
        commit_count = sum(1 for a in activities if a['activity_type'] == 'commit')
        push_count = sum(1 for a in activities if a['activity_type'] == 'push')
        logger.info(f"Today stats: commits={commit_count}, pushes={push_count}")

        today_stats = {
            'date': today,
            'commit_count': commit_count,
            'push_count': push_count,
            'total_count': len(activities)
        }

        # 获取评价
        evaluation = None
        ai_enabled = False

        try:
            # 读取配置
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            ai_config = config.get('ai', {})
            ai_enabled = ai_config.get('enabled', False)
            feature_enabled = config.get('features', {}).get('enable_ai_evaluation', False)

            # 如果 AI 功能启用且 AI 已配置
            if feature_enabled and ai_enabled:
                evaluator = AIEvaluator(ai_config)
                evaluation = evaluator.evaluate_today(today_stats, activities)

                # 如果 AI 评价失败,使用默认评价
                if not evaluation:
                    evaluation = evaluator.get_fallback_evaluation(today_stats)
            elif feature_enabled:
                # 功能启用但 AI 未配置,使用默认评价
                evaluator = AIEvaluator({})
                evaluation = evaluator.get_fallback_evaluation(today_stats)

        except Exception as e:
            # 出错时使用默认评价
            logger.error(f"评价生成失败: {str(e)}")
            evaluator = AIEvaluator({})
            evaluation = evaluator.get_fallback_evaluation(today_stats)

        return jsonify({
            'success': True,
            'data': {
                'stats': today_stats,
                'evaluation': evaluation,
                'ai_enabled': ai_enabled
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

