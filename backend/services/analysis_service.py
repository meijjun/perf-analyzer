#!/usr/bin/env python3
"""
分析服务 - 协调 SSH/Telnet 采集和大模型分析
集成 linux-performance-analyzer Skill 知识库
支持单次分析和持续监控两种模式
"""

import json
import logging
import os
import re
import time
import csv
from datetime import datetime
from typing import Dict, Any, Optional

from services.knowledge_base import KnowledgeBase, get_knowledge_base
from services.telnet_service import TelnetService

logger = logging.getLogger(__name__)


class AnalysisService:
    """性能分析服务（增强版）"""
    
    def __init__(self, llm_service, ssh_service):
        self.llm_service = llm_service
        self.ssh_service = ssh_service
        self.knowledge_base = get_knowledge_base()
    
    def run_analysis(self, target_id: str, provider: str, model: str, 
                     task_id: str, running_tasks: Dict) -> None:
        """执行完整的分析流程（增强版）"""
        try:
            logger.info(f"[任务 {task_id}] 开始分析 - 提供商：{provider}, 模型：{model}")
            
            # 更新任务状态
            self._update_task(running_tasks, task_id, {
                'status': 'running',
                'progress': 10,
                'current_step': '加载目标设备配置'
            })
            
            # 1. 加载目标配置
            from models.config import ConfigManager
            config_manager = ConfigManager('../config/config.yaml')
            targets = config_manager.get_targets()
            target = next((t for t in targets if t.get('id') == target_id), None)
            
            if not target:
                self._update_task(running_tasks, task_id, {
                    'status': 'failed',
                    'progress': 0,
                    'error': '目标设备不存在'
                })
                return
            
            self._update_task(running_tasks, task_id, {
                'status': 'running',
                'progress': 20,
                'current_step': f"连接 {target.get('host')}..."
            })
            
            # 2. 建立连接（SSH 或 Telnet）
            protocol = target.get('protocol', 'ssh')
            
            # 准备连接配置（添加 task_id 用于日志记录）
            connect_config = target.copy()
            connect_config['task_id'] = task_id
            
            if protocol == 'telnet':
                telnet_service = TelnetService()
                if not telnet_service.connect(connect_config):
                    self._update_task(running_tasks, task_id, {
                        'status': 'failed',
                        'progress': 0,
                        'error': 'Telnet 连接失败'
                    })
                    return
                
                self._update_task(running_tasks, task_id, {
                    'status': 'running',
                    'progress': 30,
                    'current_step': '收集性能数据 (Telnet)...'
                })
                
                # 3. 收集性能数据（带命令日志）
                perf_data = telnet_service.collect_performance_data()
                telnet_service.disconnect()
            else:
                if not self.ssh_service.connect(connect_config):
                    self._update_task(running_tasks, task_id, {
                        'status': 'failed',
                        'progress': 0,
                        'error': 'SSH 连接失败'
                    })
                    return
                
                self._update_task(running_tasks, task_id, {
                    'status': 'running',
                    'progress': 30,
                    'current_step': '收集性能数据...'
                })
                
                # 3. 收集性能数据（带命令日志）
                perf_data = self.ssh_service.collect_performance_data()
                self.ssh_service.disconnect()
                
                # 实时保存采集数据（用于调试）
                self._save_raw_data_realtime(task_id, perf_data, target, protocol)
            
            if not perf_data.get('success'):
                self._update_task(running_tasks, task_id, {
                    'status': 'failed',
                    'progress': 0,
                    'error': '数据采集失败'
                })
                return
            
            self._update_task(running_tasks, task_id, {
                'status': 'running',
                'progress': 40,
                'current_step': '解析性能指标...'
            })
            
            # 4. 解析性能指标
            metrics = self._extract_metrics(perf_data)
            bottlenecks = self.knowledge_base.identify_bottlenecks(metrics)
            
            logger.info(f"[任务 {task_id}] 识别到 {len(bottlenecks)} 个瓶颈")
            
            self._update_task(running_tasks, task_id, {
                'status': 'running',
                'progress': 50,
                'current_step': '调用大模型分析...'
            })
            
            # 5. 准备分析提示词（使用知识库增强）
            raw_data = self._format_raw_data(perf_data)
            prompt = self.knowledge_base.generate_analysis_prompt(metrics, bottlenecks, raw_data)
            
            self._update_task(running_tasks, task_id, {
                'status': 'running',
                'progress': 60,
                'current_step': f'正在分析（使用 {provider}/{model} + Skill 知识库）...'
            })
            
            # 6. 调用大模型分析
            analysis_result = self.llm_service.analyze(provider, model, prompt)
            
            if not analysis_result.get('success'):
                self._update_task(running_tasks, task_id, {
                    'status': 'failed',
                    'progress': 0,
                    'error': f"大模型分析失败：{analysis_result.get('error')}"
                })
                return
            
            self._update_task(running_tasks, task_id, {
                'status': 'running',
                'progress': 80,
                'current_step': '生成报告...'
            })
            
            # 7. 保存报告
            report_content = analysis_result.get('content', '')
            report_path = f"../reports/{task_id}.md"
            
            os.makedirs('../reports', exist_ok=True)
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # 8. 保存原始数据和指标
            data_path = f"../reports/{task_id}_data.json"
            raw_text_path = f"../reports/{task_id}_raw.txt"
            
            # JSON 格式
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'perf_data': perf_data,
                    'metrics': metrics,
                    'bottlenecks': bottlenecks,
                    'target': target,
                    'provider': provider,
                    'model': model
                }, f, indent=2, ensure_ascii=False)
            
            # 纯文本格式（方便调试）
            with open(raw_text_path, 'w', encoding='utf-8') as f:
                f.write(f"=== 性能分析原始数据 ===\n")
                f.write(f"任务 ID: {task_id}\n")
                f.write(f"时间：{datetime.now().isoformat()}\n")
                f.write(f"目标设备：{target.get('host')}:{target.get('port')}\n")
                f.write(f"协议：{target.get('protocol', 'ssh')}\n")
                f.write(f"大模型：{provider}/{model}\n\n")
                
                f.write(f"=== 性能指标 ===\n")
                f.write(json.dumps(metrics, indent=2, ensure_ascii=False))
                f.write(f"\n\n=== 识别的瓶颈 ===\n")
                for b in bottlenecks:
                    f.write(f"- [{b['severity']}] {b['description']}\n")
                
                f.write(f"\n=== 原始采集数据 ===\n")
                f.write(self._format_raw_data(perf_data))
            
            logger.info(f"[任务 {task_id}] 数据已保存到：{data_path}, {raw_text_path}")
            
            # 9. 完成任务
            self._update_task(running_tasks, task_id, {
                'status': 'completed',
                'progress': 100,
                'current_step': '分析完成',
                'report_path': report_path,
                'completed_at': datetime.now().isoformat(),
                'bottleneck_count': len(bottlenecks)
            })
            
            logger.info(f"[任务 {task_id}] 分析完成，报告：{report_path}")
            
        except Exception as e:
            logger.error(f"[任务 {task_id}] 分析失败：{e}")
            self._update_task(running_tasks, task_id, {
                'status': 'failed',
                'progress': 0,
                'error': str(e)
            })
    
    def _extract_metrics(self, perf_data: Dict) -> Dict[str, Any]:
        """从采集数据中提取关键性能指标"""
        metrics = {
            "load_avg_1min": 0,
            "cpu_cores": 1,
            "cpu_user": 0,
            "cpu_system": 0,
            "cpu_iowait": 0,
            "context_switches": 0,
            "mem_available_percent": 100,
            "swap_used_percent": 0,
            "oom_killed": False,
            "disk_util_percent": 0,
            "disk_await_ms": 0,
            "tcp_retrans_percent": 0,
            "time_wait_count": 0
        }
        
        try:
            categories = perf_data.get('categories', {})
            
            # CPU 指标
            cpu_data = categories.get('cpu_info', {})
            loadavg = cpu_data.get('raw_output', {}).get('cat', {}).get('stdout', '')
            if loadavg:
                parts = loadavg.split()
                if parts:
                    metrics['load_avg_1min'] = float(parts[0])
            
            # 解析 CPU 使用率
            top_output = cpu_data.get('raw_output', {}).get('top', {}).get('stdout', '')
            cpu_match = re.search(r'Cpu\(s\):\s+([\d.]+)%?\s*us.*?([\d.]+)%?\s*sy.*?([\d.]+)%?\s*wa', top_output)
            if cpu_match:
                metrics['cpu_user'] = float(cpu_match.group(1))
                metrics['cpu_system'] = float(cpu_match.group(2))
                metrics['cpu_iowait'] = float(cpu_match.group(3))
            
            # 解析 CPU 核心数
            nproc_output = cpu_data.get('raw_output', {}).get('nproc', {}).get('stdout', '1')
            metrics['cpu_cores'] = int(nproc_output.strip()) if nproc_output.strip().isdigit() else 1
            
            # 解析 vmstat（上下文切换）
            vmstat_output = cpu_data.get('raw_output', {}).get('vmstat', {}).get('stdout', '')
            vmstat_lines = vmstat_output.strip().split('\n')
            if len(vmstat_lines) >= 3:
                cs_values = []
                for line in vmstat_lines[2:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            cs_values.append(int(parts[3]))  # cs 列
                        except:
                            pass
                if cs_values:
                    metrics['context_switches'] = sum(cs_values) // len(cs_values)
            
            # 内存指标
            mem_data = categories.get('memory_info', {})
            free_output = mem_data.get('raw_output', {}).get('free', {}).get('stdout', '')
            mem_lines = free_output.strip().split('\n')
            if len(mem_lines) >= 2:
                mem_parts = mem_lines[1].split()
                if len(mem_parts) >= 7:
                    try:
                        total = float(mem_parts[1])
                        available = float(mem_parts[6]) if len(mem_parts) > 6 else float(mem_parts[3])
                        if total > 0:
                            metrics['mem_available_percent'] = (available / total) * 100
                    except:
                        pass
            
            # Swap 指标
            swap_output = mem_data.get('raw_output', {}).get('cat', {}).get('stdout', '')
            swap_match = re.search(r'SwapTotal:\s+(\d+)\s+kB.*?SwapFree:\s+(\d+)\s+kB', swap_output, re.DOTALL)
            if swap_match:
                total_swap = int(swap_match.group(1))
                free_swap = int(swap_match.group(2))
                if total_swap > 0:
                    metrics['swap_used_percent'] = ((total_swap - free_swap) / total_swap) * 100
            
            # OOM 检测
            dmesg_output = mem_data.get('raw_output', {}).get('dmesg', {}).get('stdout', '')
            metrics['oom_killed'] = bool(re.search(r'oom|killed process', dmesg_output, re.IGNORECASE))
            
            # 磁盘指标
            disk_data = categories.get('disk_io_info', {})
            iostat_output = disk_data.get('raw_output', {}).get('iostat', {}).get('stdout', '')
            # 解析 iostat 最后一行的平均值
            iostat_lines = iostat_output.strip().split('\n')
            for line in reversed(iostat_lines):
                if 'avg-cpu' not in line and 'Device' not in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        try:
                            metrics['disk_util_percent'] = float(parts[-1])
                            metrics['disk_await_ms'] = float(parts[-3])
                        except:
                            pass
                    break
            
            # 网络指标
            net_data = categories.get('network_info', {})
            ss_output = net_data.get('raw_output', {}).get('ss', {}).get('stdout', '')
            # 统计 TIME_WAIT
            metrics['time_wait_count'] = ss_output.count('TIME-WAIT')
            
        except Exception as e:
            logger.error(f"提取指标失败：{e}")
        
        return metrics
    
    def _format_raw_data(self, perf_data: Dict) -> str:
        """格式化原始数据为文本"""
        lines = []
        categories = perf_data.get('categories', {})
        
        for category, data in categories.items():
            lines.append(f"\n## {category.replace('_', ' ').title()}\n")
            raw_output = data.get('raw_output', {})
            
            for cmd_name, cmd_result in raw_output.items():
                stdout = cmd_result.get('stdout', '').strip()
                if stdout:
                    lines.append(f"### {cmd_name}\n```{stdout}\n```\n")
        
        return '\n'.join(lines)
    
    def _save_raw_data_realtime(self, task_id: str, perf_data: Dict, target: Dict, protocol: str):
        """实时保存采集数据到本地（用于调试）"""
        try:
            import os
            from datetime import datetime
            
            # 确保目录存在
            os.makedirs('../reports', exist_ok=True)
            
            # 保存原始数据（JSON）
            json_path = f"../reports/{task_id}_collected.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'task_id': task_id,
                    'timestamp': datetime.now().isoformat(),
                    'target': target,
                    'protocol': protocol,
                    'perf_data': perf_data
                }, f, indent=2, ensure_ascii=False)
            
            # 保存原始数据（纯文本）
            txt_path = f"../reports/{task_id}_collected.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"=== 性能数据采集 ===\n")
                f.write(f"任务 ID: {task_id}\n")
                f.write(f"采集时间：{datetime.now().isoformat()}\n")
                f.write(f"目标设备：{target.get('host')}:{target.get('port')}\n")
                f.write(f"协议：{protocol}\n\n")
                
                f.write(f"=== 原始采集数据 ===\n")
                f.write(self._format_raw_data(perf_data))
            
            logger.info(f"[任务 {task_id}] 采集数据已实时保存到：{json_path}, {txt_path}")
            
        except Exception as e:
            logger.error(f"[任务 {task_id}] 实时保存采集数据失败：{e}")
    
    def _update_task(self, running_tasks: Dict, task_id: str, updates: Dict) -> None:
        """更新任务状态"""
        if task_id in running_tasks:
            running_tasks[task_id].update(updates)
            logger.info(f"[任务 {task_id}] 状态更新：{updates.get('status')} - {updates.get('current_step')}")
    
    def get_optimization_suggestions(self, bottleneck_type: str, metrics: Dict) -> Dict:
        """获取优化建议（供 API 调用）"""
        return self.knowledge_base.get_optimization_plan(bottleneck_type, metrics)
    
    def get_quick_commands(self, scenario: str) -> list:
        """获取快速诊断命令（供 API 调用）"""
        return self.knowledge_base.get_quick_commands(scenario)
    
    # ========== 持续监控模式 ==========
    
    def run_continuous_monitoring(self, target_id: str, settings: Dict, 
                                  task_id: str, running_tasks: Dict) -> None:
        """持续监控模式"""
        try:
            logger.info(f"[任务 {task_id}] 开始持续监控")
            
            # 1. 加载目标配置
            from models.config import ConfigManager
            config_manager = ConfigManager('../config/config.yaml')
            targets = config_manager.get_targets()
            target = next((t for t in targets if t.get('id') == target_id), None)
            
            if not target:
                self._update_task(running_tasks, task_id, {
                    'status': 'failed',
                    'error': '目标设备不存在'
                })
                return
            
            # 2. 解析设置
            duration_minutes = settings['duration_minutes']
            max_collections = settings['max_collections']
            interval_seconds = settings['interval_seconds']
            
            # 根据时长计算最大采集次数
            if duration_minutes > 0:
                calculated = (duration_minutes * 60) // interval_seconds
                max_collections = min(max_collections, calculated)
            
            logger.info(f"[任务 {task_id}] 监控参数 - 次数:{max_collections}, "
                       f"间隔:{interval_seconds}s, 预计:{max_collections*interval_seconds/60:.1f}分钟")
            
            # 3. 建立连接
            self._update_task(running_tasks, task_id, {
                'progress': 10,
                'current_step': f"连接 {target.get('host')}..."
            })
            
            protocol = target.get('protocol', 'ssh')
            
            # 准备连接配置（添加 task_id 用于日志记录）
            connect_config = target.copy()
            connect_config['task_id'] = task_id
            
            if protocol == 'telnet':
                telnet_service = TelnetService()
                if not telnet_service.connect(connect_config):
                    self._update_task(running_tasks, task_id, {
                        'status': 'failed',
                        'error': 'Telnet 连接失败'
                    })
                    return
                connection = telnet_service
            else:
                if not self.ssh_service.connect(connect_config):
                    self._update_task(running_tasks, task_id, {
                        'status': 'failed',
                        'error': 'SSH 连接失败'
                    })
                    return
                connection = self.ssh_service
            
            # 4. 循环采集
            all_metrics = []
            start_time = datetime.now()
            
            for i in range(max_collections):
                # 检查是否应该停止
                if self._should_stop(running_tasks, task_id):
                    logger.info(f"[任务 {task_id}] 监控被用户中断")
                    break
                
                # 更新进度
                progress = 10 + int((i / max_collections) * 80)
                self._update_task(running_tasks, task_id, {
                    'progress': progress,
                    'current_step': f'第 {i+1}/{max_collections} 次采集'
                })
                
                # 记录采集开始
                logger.info(f"[任务 {task_id}] 开始第 {i+1}/{max_collections} 次采集")
                
                # 采集数据（会记录所有命令到日志）
                perf_data = connection.collect_performance_data()
                metrics = self._extract_metrics(perf_data)
                metrics['timestamp'] = datetime.now().isoformat()
                metrics['collection_index'] = i + 1
                all_metrics.append(metrics)
                
                # 保存中间数据
                self._save_continuous_data(task_id, i, metrics)
                
                logger.info(f"[任务 {task_id}] 第 {i+1} 次采集完成 - "
                           f"CPU:{metrics.get('cpu_usage')}% "
                           f"内存:{metrics.get('memory_usage')}%")
                
                # 等待（最后一次不等待）
                if i < max_collections - 1:
                    time.sleep(interval_seconds)
            
            # 5. 断开连接
            if protocol == 'telnet':
                telnet_service.disconnect()
            else:
                self.ssh_service.disconnect()
            
            # 6. 生成趋势报告
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self._update_task(running_tasks, task_id, {
                'progress': 90,
                'current_step': '生成趋势报告...'
            })
            
            report_path = self._generate_trend_report(task_id, all_metrics, duration, target)
            
            # 7. 完成任务
            self._update_task(running_tasks, task_id, {
                'status': 'completed',
                'progress': 100,
                'current_step': '完成',
                'result': {
                    'collections': len(all_metrics),
                    'duration_seconds': duration,
                    'report_path': report_path
                }
            })
            
            logger.info(f"[任务 {task_id}] 持续监控完成 - 采集{len(all_metrics)}次，耗时{duration:.1f}秒")
            
        except Exception as e:
            logger.error(f"[任务 {task_id}] 持续监控失败：{e}")
            import traceback
            traceback.print_exc()
            self._update_task(running_tasks, task_id, {
                'status': 'failed',
                'error': str(e)
            })
    
    def _should_stop(self, running_tasks: Dict, task_id: str) -> bool:
        """检查是否应该停止监控"""
        task = running_tasks.get(task_id, {})
        return task.get('status') == 'stopped'
    
    def _save_continuous_data(self, task_id: str, index: int, metrics: Dict):
        """保存持续监控数据"""
        import os
        
        # 创建任务目录
        task_dir = f"../reports/{task_id}"
        os.makedirs(task_dir, exist_ok=True)
        
        # 保存为 JSON Lines 格式
        jsonl_path = f"{task_dir}/metrics.jsonl"
        with open(jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(metrics, ensure_ascii=False) + '\n')
        
        # 同时保存最新数据到单独文件（用于实时查看）
        latest_path = f"{task_dir}/latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    def _generate_trend_report(self, task_id: str, all_metrics: list, 
                               duration_seconds: float, target: Dict) -> str:
        """生成趋势分析报告"""
        import os
        
        report_path = f"../reports/{task_id}/trend_report.md"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        # 计算统计信息
        if not all_metrics:
            return None
        
        cpu_values = [m.get('cpu_usage', 0) for m in all_metrics if m.get('cpu_usage')]
        mem_values = [m.get('memory_usage', 0) for m in all_metrics if m.get('memory_usage')]
        disk_values = [m.get('disk_usage', 0) for m in all_metrics if m.get('disk_usage')]
        load_values = [m.get('load_1min', 0) for m in all_metrics if m.get('load_1min')]
        
        def safe_avg(values):
            return sum(values)/len(values) if values else 0
        
        def safe_max(values):
            return max(values) if values else 0
        
        def safe_min(values):
            return min(values) if values else 0
        
        report = f"""# 性能监控趋势报告

**任务 ID**: {task_id}  
**监控时长**: {duration_seconds:.1f} 秒  
**采集次数**: {len(all_metrics)} 次  
**采集间隔**: {duration_seconds/len(all_metrics):.1f} 秒  
**目标设备**: {target.get('host')}:{target.get('port')}  
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计摘要

### CPU 使用率
- 平均值：{safe_avg(cpu_values):.1f}%
- 最大值：{safe_max(cpu_values):.1f}%
- 最小值：{safe_min(cpu_values):.1f}%

### 内存使用率
- 平均值：{safe_avg(mem_values):.1f}%
- 最大值：{safe_max(mem_values):.1f}%
- 最小值：{safe_min(mem_values):.1f}%

### 磁盘使用率
- 平均值：{safe_avg(disk_values):.1f}%
- 最大值：{safe_max(disk_values):.1f}%
- 最小值：{safe_min(disk_values):.1f}%

### 系统负载
- 平均值：{safe_avg(load_values):.2f}
- 最大值：{safe_max(load_values):.2f}
- 最小值：{safe_min(load_values):.2f}

## 趋势分析

"""
        # 简单趋势分析
        if cpu_values and len(cpu_values) >= 3:
            first_third = cpu_values[:len(cpu_values)//3]
            last_third = cpu_values[-(len(cpu_values)//3):]
            avg_first = safe_avg(first_third)
            avg_last = safe_avg(last_third)
            
            if avg_last > avg_first * 1.2:
                report += "**CPU 使用率**: 呈上升趋势 ⚠️\n\n"
            elif avg_last < avg_first * 0.8:
                report += "**CPU 使用率**: 呈下降趋势 ✅\n\n"
            else:
                report += "**CPU 使用率**: 保持稳定 ➡️\n\n"
        
        # 数据文件说明
        report += f"""
## 原始数据

数据文件：
- `metrics.jsonl` - 所有采集数据（JSON Lines 格式）
- `latest.json` - 最后一次采集数据
- `chart_data.csv` - 图表数据（可导入 Excel）

## 建议

"""
        # 根据平均值给出建议
        if safe_avg(cpu_values) > 80:
            report += "- ⚠️ **CPU 使用率偏高**，建议检查高负载进程\n"
        if safe_avg(mem_values) > 85:
            report += "- ⚠️ **内存使用率偏高**，建议检查内存泄漏或增加内存\n"
        if safe_avg(disk_values) > 80:
            report += "- ⚠️ **磁盘使用率偏高**，建议清理无用文件或扩容\n"
        if safe_avg(cpu_values) <= 80 and safe_avg(mem_values) <= 85 and safe_avg(disk_values) <= 80:
            report += "- ✅ 系统整体运行正常\n"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 同时生成 CSV 格式（方便导入 Excel）
        csv_path = f"../reports/{task_id}/chart_data.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['时间戳', '采集次序', 'CPU 使用率', '内存使用率', '磁盘使用率', '系统负载'])
            
            for m in all_metrics:
                writer.writerow([
                    m.get('timestamp', ''),
                    m.get('collection_index', 0),
                    m.get('cpu_usage', 0),
                    m.get('memory_usage', 0),
                    m.get('disk_usage', 0),
                    m.get('load_1min', 0)
                ])
        
        logger.info(f"[任务 {task_id}] 趋势报告已生成：{report_path}")
        return report_path
