#!/usr/bin/env python3
"""
Web 版性能分析器 - Flask 后端主程序
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm_service import LLMService
from services.ssh_service import SSHService
from services.telnet_service import TelnetService
from services.analysis_service import AnalysisService
from services.optimizer_service import create_optimizer
from services.baseline_service import get_baseline_service
from services.settings_service import get_settings_service
from services.collection_command_service import get_collection_command_service
from services.package_service import get_package_service
from models.config import ConfigManager

# 配置日志
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 初始化 Flask 应用
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

# 关键修复：修改 Jinja2 分隔符，避免与 Vue 的 {{ }} 冲突
# Flask 使用 {% %} 作为控制语句，{{ }} 留给 Vue
app.jinja_env.block_start_string = '{%'
app.jinja_env.block_end_string = '%}'
app.jinja_env.variable_start_string = '[[['
app.jinja_env.variable_end_string = ']]]'
app.jinja_env.comment_start_string = '{#'
app.jinja_env.comment_end_string = '#}'

CORS(app)

# 存储运行中的任务
running_tasks = {}

# 初始化服务
config_manager = ConfigManager('../config/config.yaml')
settings_service = get_settings_service()
command_service = get_collection_command_service()
package_service = get_package_service()
llm_service = LLMService(config_manager)
ssh_service = SSHService()
analysis_service = AnalysisService(llm_service, ssh_service)
optimizer_service = create_optimizer()
baseline_service = get_baseline_service()

# 启动实时监控


# ==================== 页面路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/llm/providers', methods=['GET'])
def get_llm_providers():
    """获取可用的大模型提供商列表"""
    providers = llm_service.get_available_providers()
    return jsonify({
        'success': True,
        'data': providers
    })


@app.route('/api/llm/models', methods=['GET'])
def get_llm_models():
    """获取指定提供商的模型列表"""
    provider = request.args.get('provider', 'aliyun')
    models = llm_service.get_models_for_provider(provider)
    return jsonify({
        'success': True,
        'data': models
    })


@app.route('/api/config/llm', methods=['GET'])
def get_llm_config():
    """获取大模型配置"""
    config = config_manager.get_llm_config()
    return jsonify({
        'success': True,
        'data': config
    })


@app.route('/api/config/llm', methods=['POST'])
def update_llm_config():
    """更新大模型配置"""
    try:
        data = request.json
        config_manager.update_llm_config(data)
        return jsonify({
            'success': True,
            'message': '配置已保存'
        })
    except Exception as e:
        logger.error(f"更新配置失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/targets', methods=['GET'])
def get_targets():
    """获取目标设备列表"""
    targets = config_manager.get_targets()
    return jsonify({
        'success': True,
        'data': targets
    })


@app.route('/api/targets', methods=['POST'])
def add_target():
    """添加目标设备"""
    try:
        data = request.json
        logger.info(f"收到添加设备请求：{data}")
        
        # 验证必填字段
        if not data.get('name') or not data.get('host') or not data.get('username'):
            return jsonify({
                'success': False,
                'error': '缺少必填字段：name, host, username'
            }), 400
        
        target = {
            'id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'name': data.get('name'),
            'host': data.get('host'),
            'port': int(data.get('port', 22)),
            'protocol': data.get('protocol', 'ssh'),
            'username': data.get('username'),
            'auth': data.get('auth', 'key'),
            'created_at': datetime.now().isoformat()
        }
        
        if data.get('auth') == 'key':
            target['key_path'] = data.get('key_path', '~/.ssh/id_rsa')
        else:
            target['password'] = data.get('password', '')
        
        config_manager.add_target(target)
        logger.info(f"设备添加成功：{target['name']}")
        
        return jsonify({
            'success': True,
            'data': target,
            'message': '目标设备已添加'
        })
    except Exception as e:
        logger.error(f"添加目标设备失败：{e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/targets/<target_id>', methods=['DELETE'])
def delete_target(target_id):
    """删除目标设备"""
    try:
        config_manager.delete_target(target_id)
        return jsonify({
            'success': True,
            'message': '目标设备已删除'
        })
    except Exception as e:
        logger.error(f"删除目标设备失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """开始性能分析（支持单次分析和持续监控两种模式）"""
    try:
        data = request.json
        target_id = data.get('target_id')
        provider = data.get('provider', 'aliyun')
        model = data.get('model', 'qwen-max')
        mode = data.get('mode', 'single')  # 'single' or 'continuous'
        
        if not target_id:
            return jsonify({
                'success': False,
                'error': '请指定目标设备'
            }), 400
        
        # 创建分析任务
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        running_tasks[task_id] = {
            'status': 'pending',
            'progress': 0,
            'current_step': '准备中',
            'created_at': datetime.now().isoformat(),
            'mode': mode
        }
        
        # 异步执行分析
        import threading
        
        if mode == 'continuous':
            # 持续监控模式
            settings = settings_service.get_collection_settings()
            thread = threading.Thread(
                target=analysis_service.run_continuous_monitoring,
                args=(target_id, settings, task_id, running_tasks)
            )
            message = '持续监控任务已启动'
        else:
            # 单次分析模式
            thread = threading.Thread(
                target=analysis_service.run_analysis,
                args=(target_id, provider, model, task_id, running_tasks)
            )
            message = '分析任务已启动'
        
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'mode': mode,
            'message': message
        })
    except Exception as e:
        logger.error(f"启动分析失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态（支持持续监控）"""
    if task_id not in running_tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    task = running_tasks[task_id]
    
    # 如果是持续监控模式，附加最新指标
    if task.get('mode') == 'continuous' and task.get('status') == 'running':
        import os
        task_dir = f"../reports/{task_id}"
        latest_path = f"{task_dir}/latest.json"
        
        if os.path.exists(latest_path):
            with open(latest_path, 'r', encoding='utf-8') as f:
                latest_metrics = json.load(f)
            task['latest_metrics'] = latest_metrics
    
    return jsonify({
        'success': True,
        'data': task
    })


@app.route('/api/tasks/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止任务（用于中断持续监控）"""
    if task_id not in running_tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    running_tasks[task_id]['status'] = 'stopped'
    logger.info(f"[任务 {task_id}] 用户请求停止")
    
    return jsonify({
        'success': True,
        'message': '任务已停止'
    })


@app.route('/api/tasks/<task_id>/report', methods=['GET'])
def get_task_report(task_id):
    """获取任务报告"""
    report_path = f"../reports/{task_id}.md"
    if not os.path.exists(report_path):
        return jsonify({
            'success': False,
            'error': '报告不存在'
        }), 404
    
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return jsonify({
        'success': True,
        'data': {
            'content': content,
            'format': 'markdown'
        }
    })


@app.route('/api/reports', methods=['GET'])
def get_reports():
    """获取历史报告列表"""
    reports_dir = '../reports'
    if not os.path.exists(reports_dir):
        return jsonify({
            'success': True,
            'data': []
        })
    
    reports = []
    for filename in os.listdir(reports_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(reports_dir, filename)
            stat = os.stat(filepath)
            reports.append({
                'filename': filename,
                'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'size': stat.st_size
            })
    
    reports.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify({
        'success': True,
        'data': reports
    })


@app.route('/api/reports/<filename>', methods=['GET'])
def get_report(filename):
    """获取指定报告"""
    try:
        filename = secure_filename(filename)
        report_path = f"../reports/{filename}"
        
        if not os.path.exists(report_path):
            return jsonify({
                'success': False,
                'error': '报告不存在'
            }), 404
        
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'data': {
                'content': content,
                'filename': filename
            }
        })
    except Exception as e:
        logger.error(f"获取报告失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/docs/<filename>', methods=['GET'])
def get_doc(filename):
    """获取参考文档"""
    try:
        filename = secure_filename(filename)
        doc_path = f"../docs/{filename}"
        
        if not os.path.exists(doc_path):
            return jsonify({
                'success': False,
                'error': '文档不存在'
            }), 404
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'data': content
        })
    except Exception as e:
        logger.error(f"获取文档失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/analysis/quick-commands', methods=['GET'])
def get_quick_commands():
    """获取快速诊断命令"""
    try:
        scenario = request.args.get('scenario', 'cpu')
        commands = analysis_service.get_quick_commands(scenario)
        
        return jsonify({
            'success': True,
            'data': commands
        })
    except Exception as e:
        logger.error(f"获取快速命令失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== 实时监控 API ====================

def get_monitor_summary():
    """获取监控摘要"""
    try:
        summary = monitor_service.get_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        logger.error(f"获取监控摘要失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


def get_monitor_alerts():
    """获取告警列表"""
    try:
        limit = request.args.get('limit', 20, type=int)
        alerts = monitor_service.get_alerts(limit)
        return jsonify({
            'success': True,
            'data': alerts
        })
    except Exception as e:
        logger.error(f"获取告警失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== 优化命令生成 API ====================

@app.route('/api/optimize/generate', methods=['POST'])
def generate_optimization():
    """生成优化命令"""
    try:
        data = request.json
        bottlenecks = data.get('bottlenecks', [])
        metrics = data.get('metrics', {})
        
        if not bottlenecks:
            return jsonify({
                'success': False,
                'error': '请提供瓶颈列表'
            }), 400
        
        plan = optimizer_service.generate_optimization_plan(bottlenecks, metrics)
        plan_path = optimizer_service.save_plan(plan)
        
        return jsonify({
            'success': True,
            'data': {
                'plan': plan.to_dict(),
                'script_path': plan_path
            }
        })
    except Exception as e:
        logger.error(f"生成优化命令失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== 性能基线 API ====================

@app.route('/api/baseline/save', methods=['POST'])
def save_baseline():
    """保存性能基线"""
    try:
        data = request.json
        metrics = data.get('metrics', {})
        name = data.get('name')
        description = data.get('description', '')
        
        if not metrics:
            return jsonify({
                'success': False,
                'error': '请提供性能指标'
            }), 400
        
        baseline_path = baseline_service.save_baseline(metrics, name, description)
        
        return jsonify({
            'success': True,
            'data': {
                'path': baseline_path,
                'name': name or 'auto'
            }
        })
    except Exception as e:
        logger.error(f"保存基线失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/baseline/list', methods=['GET'])
def list_baselines():
    """列出所有基线"""
    try:
        baselines = baseline_service.list_baselines()
        return jsonify({
            'success': True,
            'data': baselines
        })
    except Exception as e:
        logger.error(f"列出基线失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/baseline/compare', methods=['POST'])
def compare_baseline():
    """对比当前状态与基线"""
    try:
        data = request.json
        current_metrics = data.get('metrics', {})
        baseline_name = data.get('baseline_name')
        
        if not current_metrics:
            return jsonify({
                'success': False,
                'error': '请提供当前性能指标'
            }), 400
        
        result = baseline_service.compare_with_baseline(current_metrics, baseline_name)
        
        return jsonify({
            'success': result['success'],
            'data': result
        })
    except Exception as e:
        logger.error(f"基线对比失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/baseline/current', methods=['GET'])
def get_current_baseline():
    """获取当前基线"""
    try:
        baseline = baseline_service.get_current_baseline()
        return jsonify({
            'success': True,
            'data': baseline
        })
    except Exception as e:
        logger.error(f"获取当前基线失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/tasks/<task_id>/raw', methods=['GET'])
def get_task_raw_data(task_id):
    """获取任务的原始采集数据（用于调试）"""
    try:
        raw_text_path = f"../reports/{task_id}_raw.txt"
        collected_txt_path = f"../reports/{task_id}_collected.txt"
        collected_json_path = f"../reports/{task_id}_collected.json"
        data_path = f"../reports/{task_id}_data.json"
        
        # 优先返回采集数据
        if os.path.exists(collected_txt_path):
            with open(collected_txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'data': {
                    'text': content,
                    'json_path': collected_json_path,
                    'text_path': collected_txt_path,
                    'type': 'collected'
                }
            })
        
        # 其次返回分析报告的原始数据
        if os.path.exists(raw_text_path):
            with open(raw_text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({
                'success': True,
                'data': {
                    'text': content,
                    'json_path': data_path,
                    'text_path': raw_text_path,
                    'type': 'analyzed'
                }
            })
        
        return jsonify({
            'success': False,
            'error': '原始数据不存在，可能任务还未开始采集'
        }), 404
        
    except Exception as e:
        logger.error(f"获取原始数据失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


# ==================== 采集命令管理 API ====================

@app.route('/api/collection-commands', methods=['GET'])
def get_collection_commands():
    """获取所有采集命令"""
    try:
        commands = command_service.get_all_commands()
        return jsonify({
            'success': True,
            'data': commands
        })
    except Exception as e:
        logger.error(f"获取采集命令失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/collection-commands/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        categories = command_service.get_categories()
        return jsonify({
            'success': True,
            'data': categories
        })
    except Exception as e:
        logger.error(f"获取分类失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/collection-commands', methods=['POST'])
def add_command():
    """添加采集命令"""
    try:
        data = request.json
        category = data.get('category')
        command = data.get('command')
        description = data.get('description', '')
        is_custom = data.get('is_custom', True)
        
        if not all([category, command]):
            return jsonify({
                'success': False,
                'error': '缺少必填字段：category, command'
            }), 400
        
        success = command_service.add_command(category, command, description, is_custom)
        
        if success:
            return jsonify({
                'success': True,
                'message': '命令已添加'
            })
        else:
            return jsonify({
                'success': False,
                'error': '命令已存在'
            }), 400
    except Exception as e:
        logger.error(f"添加命令失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/collection-commands/update', methods=['POST'])
def update_command():
    """更新采集命令"""
    try:
        data = request.json
        category = data.get('category')
        old_command = data.get('old_command')
        new_command = data.get('new_command')
        new_description = data.get('new_description', '')
        
        if not all([category, old_command, new_command]):
            return jsonify({
                'success': False,
                'error': '缺少必填字段'
            }), 400
        
        success = command_service.update_command(category, old_command, new_command, new_description)
        
        if success:
            return jsonify({
                'success': True,
                'message': '命令已更新'
            })
        else:
            return jsonify({
                'success': False,
                'error': '更新失败（系统命令不可修改）'
            }), 400
    except Exception as e:
        logger.error(f"更新命令失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/collection-commands/delete', methods=['POST'])
def delete_command():
    """删除采集命令"""
    try:
        data = request.json
        category = data.get('category')
        command = data.get('command')
        
        if not all([category, command]):
            return jsonify({
                'success': False,
                'error': '缺少必填字段'
            }), 400
        
        success = command_service.delete_command(category, command)
        
        if success:
            return jsonify({
                'success': True,
                'message': '命令已删除'
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除失败（系统命令不可删除）'
            }), 400
    except Exception as e:
        logger.error(f"删除命令失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/collection-commands/categories', methods=['POST'])
def add_category():
    """添加分类"""
    try:
        data = request.json
        category = data.get('category')
        
        if not category:
            return jsonify({
                'success': False,
                'error': '缺少必填字段：category'
            }), 400
        
        success = command_service.add_category(category)
        
        if success:
            return jsonify({
                'success': True,
                'message': '分类已添加'
            })
        else:
            return jsonify({
                'success': False,
                'error': '分类已存在'
            }), 400
    except Exception as e:
        logger.error(f"添加分类失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== 设置 API ====================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """获取系统设置"""
    try:
        settings = settings_service.get_settings()
        return jsonify({
            'success': True,
            'data': settings
        })
    except Exception as e:
        logger.error(f"获取设置失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """更新系统设置"""
    try:
        data = request.json
        success = settings_service.update_settings(data)
        return jsonify({
            'success': success,
            'message': '设置已保存' if success else '保存失败'
        })
    except Exception as e:
        logger.error(f"更新设置失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/commands-manage')
def commands_manage():
    """采集命令管理页面"""
    return render_template('commands-manage.html')


@app.route('/download')
def download_page():
    """项目打包下载页面"""
    return render_template('download.html')


# ==================== 打包下载 API ====================

@app.route('/api/package/create', methods=['POST'])
def create_package():
    """创建项目包"""
    try:
        data = request.json or {}
        format = data.get('format', 'zip')
        include_data = data.get('include_data', False)
        include_logs = data.get('include_logs', False)
        
        success, result = package_service.create_package(
            format=format,
            include_data=include_data,
            include_logs=include_logs
        )
        
        if success:
            package_info = package_service.get_package_info(result)
            return jsonify({
                'success': True,
                'message': '项目包已创建',
                'data': {
                    'path': result,
                    'filename': package_info['filename'],
                    'size_mb': package_info['size_mb']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': result
            }), 400
    except Exception as e:
        logger.error(f"创建项目包失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/package/download')
def download_package():
    """下载项目包"""
    try:
        filename = request.args.get('filename')
        
        if not filename:
            # 如果没有指定文件名，创建最新的包
            success, result = package_service.create_package()
            if not success:
                return jsonify({
                    'success': False,
                    'error': result
                }), 400
            filename = Path(result).name
        
        # 查找文件
        build_dir = Path('../build')
        package_path = build_dir / filename
        
        if not package_path.exists():
            # 尝试查找最新的包
            packages = list(build_dir.glob('perf-analyzer-v*.zip'))
            if packages:
                package_path = sorted(packages)[-1]
                filename = package_path.name
            else:
                return jsonify({
                    'success': False,
                    'error': '项目包不存在'
                }), 404
        
        from flask import send_file
        return send_file(
            package_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"下载项目包失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/package/latest')
def get_latest_package():
    """获取最新项目包信息"""
    try:
        build_dir = Path('../build')
        packages = list(build_dir.glob('perf-analyzer-v*.zip'))
        
        if not packages:
            return jsonify({
                'success': True,
                'data': None
            })
        
        # 获取最新的包
        latest = sorted(packages)[-1]
        info = package_service.get_package_info(str(latest))
        
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        logger.error(f"获取项目包信息失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/version')
def get_version():
    """获取版本信息"""
    try:
        version = package_service.get_version()
        
        version_file = Path('../VERSION.json')
        if version_file.exists():
            import json
            with open(version_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
        else:
            version_data = {'version': version}
        
        return jsonify({
            'success': True,
            'data': version_data
        })
    except Exception as e:
        logger.error(f"获取版本信息失败：{e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ==================== 主程序 ====================

if __name__ == '__main__':
    # 确保目录存在
    os.makedirs('../logs', exist_ok=True)
    os.makedirs('../reports', exist_ok=True)
    os.makedirs('../config', exist_ok=True)
    os.makedirs('../baselines', exist_ok=True)
    
    logger.info("Web Performance Analyzer starting...")
    logger.info(f"Working directory: {os.path.abspath('..')}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
