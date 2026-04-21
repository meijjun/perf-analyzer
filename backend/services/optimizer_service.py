#!/usr/bin/env python3
"""
自动优化服务 - 根据识别的问题生成可执行的优化命令
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class OptimizationPlan:
    """优化计划"""
    
    def __init__(self, title: str, description: str = ""):
        self.title = title
        self.description = description
        self.steps: List[Dict[str, Any]] = []
        self.risks: List[str] = []
        self.verify_commands: List[str] = []
        self.rollback_commands: List[str] = []
        self.created_at = datetime.now().isoformat()
    
    def add_step(self, name: str, command: str, description: str = "", 
                 auto_execute: bool = False, order: int = 0):
        """添加优化步骤"""
        self.steps.append({
            'order': order or len(self.steps) + 1,
            'name': name,
            'command': command,
            'description': description,
            'auto_execute': auto_execute,
            'status': 'pending',  # pending, running, success, failed, skipped
            'output': '',
            'error': ''
        })
        # 按 order 排序
        self.steps.sort(key=lambda x: x['order'])
    
    def add_risk(self, risk: str):
        """添加风险提示"""
        self.risks.append(risk)
    
    def add_verify(self, command: str):
        """添加验证命令"""
        self.verify_commands.append(command)
    
    def add_rollback(self, command: str):
        """添加回滚命令"""
        self.rollback_commands.append(command)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'title': self.title,
            'description': self.description,
            'steps': self.steps,
            'risks': self.risks,
            'verify_commands': self.verify_commands,
            'rollback_commands': self.rollback_commands,
            'created_at': self.created_at,
            'total_steps': len(self.steps),
            'completed_steps': len([s for s in self.steps if s['status'] == 'success'])
        }
    
    def generate_script(self) -> str:
        """生成可执行脚本"""
        lines = [
            "#!/bin/bash",
            f"# {self.title}",
            f"# 生成时间：{self.created_at}",
            f"# 描述：{self.description}",
            "",
            "set -e  # 遇到错误立即退出",
            "",
            "# 备份当前配置",
            "echo '正在备份当前配置...'",
            f"cp /etc/sysctl.conf /etc/sysctl.conf.backup.{datetime.now().strftime('%Y%m%d%H%M%S')} 2>/dev/null || true",
            ""
        ]
        
        for step in self.steps:
            lines.append(f"# 步骤 {step['order']}: {step['name']}")
            lines.append(f"echo '执行：{step['name']}'")
            lines.append(step['command'])
            lines.append("")
        
        lines.append("# 验证优化效果")
        lines.append("echo '验证优化效果...'")
        for cmd in self.verify_commands:
            lines.append(cmd)
        
        lines.append("")
        lines.append("echo '优化完成！'")
        
        return '\n'.join(lines)
    
    def generate_rollback_script(self) -> str:
        """生成回滚脚本"""
        lines = [
            "#!/bin/bash",
            f"# 回滚：{self.title}",
            f"# 生成时间：{datetime.now().isoformat()}",
            "",
            "set -e",
            ""
        ]
        
        for cmd in self.rollback_commands:
            lines.append(cmd)
        
        lines.append("")
        lines.append("echo '回滚完成！'")
        
        return '\n'.join(lines)


class OptimizerService:
    """优化服务"""
    
    def __init__(self, knowledge_base=None):
        self.knowledge_base = knowledge_base
    
    def generate_optimization_plan(self, bottlenecks: List[Dict], 
                                    metrics: Dict) -> OptimizationPlan:
        """
        生成优化计划
        
        Args:
            bottlenecks: 瓶颈列表
            metrics: 当前性能指标
        
        Returns:
            OptimizationPlan 对象
        """
        plan = OptimizationPlan(
            title="系统性能优化方案",
            description=f"基于 {len(bottlenecks)} 个性能瓶颈的自动优化建议"
        )
        
        # 按严重程度排序
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        sorted_bottlenecks = sorted(bottlenecks, 
                                    key=lambda x: severity_order.get(x.get('severity', 'info'), 3))
        
        order = 1
        
        for bottleneck in sorted_bottlenecks:
            b_type = bottleneck.get('type', '')
            severity = bottleneck.get('severity', 'warning')
            description = bottleneck.get('description', '')
            
            if b_type == 'cpu':
                self._add_cpu_optimizations(plan, metrics, order)
                order += 1
            elif b_type == 'memory':
                self._add_memory_optimizations(plan, metrics, order)
                order += 1
            elif b_type == 'disk_io':
                self._add_disk_optimizations(plan, metrics, order)
                order += 1
            elif b_type == 'network':
                self._add_network_optimizations(plan, metrics, order)
                order += 1
            elif b_type == 'load':
                self._add_load_optimizations(plan, metrics, order)
                order += 1
        
        # 添加通用验证命令
        plan.add_verify("echo '=== 优化后系统状态 ==='")
        plan.add_verify("uptime")
        plan.add_verify("free -h")
        plan.add_verify("df -h")
        
        # 添加通用回滚命令
        plan.add_rollback("# 回滚所有 sysctl 修改")
        plan.add_rollback("cp /etc/sysctl.conf.backup.* /etc/sysctl.conf 2>/dev/null && sysctl -p || echo '无备份可回滚'")
        
        return plan
    
    def _add_cpu_optimizations(self, plan: OptimizationPlan, 
                                metrics: Dict, order: int):
        """添加 CPU 优化步骤"""
        plan.add_step(
            name="减少上下文切换",
            command="sysctl -w kernel.sched_min_granularity_ns=10000000",
            description="增大调度粒度，减少 CPU 抢占频率（适用于 CPU 密集型场景）",
            order=order
        )
        plan.add_risk("可能轻微增加交互响应延迟")
        plan.add_rollback("sysctl -w kernel.sched_min_granularity_ns=3000000")
        
        plan.add_verify("vmstat 1 3 | tail -5")
        
        # 如果是高负载场景
        cpu_usage = metrics.get('cpu', {}).get('usage_percent', 0)
        if cpu_usage > 90:
            plan.add_step(
                name="设置 CPU 性能模式",
                command="for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > $cpu 2>/dev/null; done",
                description="关闭 CPU 节能模式，提升性能",
                order=order + 1
            )
            plan.add_risk("会增加功耗和发热")
            plan.add_rollback("for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo ondemand > $cpu 2>/dev/null; done")
            plan.add_verify("cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor | sort -u")
    
    def _add_memory_optimizations(self, plan: OptimizationPlan, 
                                   metrics: Dict, order: int):
        """添加内存优化步骤"""
        mem_usage = metrics.get('memory', {}).get('usage_percent', 0)
        swap_usage = metrics.get('memory', {}).get('swap_usage_percent', 0)
        
        # 降低 swappiness
        plan.add_step(
            name="降低 Swap 使用倾向",
            command="sysctl -w vm.swappiness=10",
            description="减少系统使用 Swap 的倾向，适用于数据库等内存敏感应用",
            order=order
        )
        plan.add_risk("可能导致内存压力增大时直接触发 OOM")
        plan.add_rollback("sysctl -w vm.swappiness=60")
        plan.add_verify("sysctl vm.swappiness")
        
        # 如果 Swap 使用率高
        if swap_usage > 30:
            plan.add_step(
                name="清理页缓存",
                command="sync && echo 1 > /proc/sys/vm/drop_caches",
                description="清理页缓存释放内存（安全操作）",
                order=order + 1
            )
            plan.add_risk("可能短暂影响 I/O 性能")
            plan.add_verify("free -h")
        
        # 如果是数据库场景（内存使用率高）
        if mem_usage > 80:
            plan.add_step(
                name="关闭透明大页",
                command="echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true",
                description="数据库场景建议关闭透明大页（THP）",
                order=order + 2
            )
            plan.add_risk("需要持久化配置，重启后还原")
            plan.add_verify("cat /sys/kernel/mm/transparent_hugepage/enabled")
    
    def _add_disk_optimizations(self, plan: OptimizationPlan, 
                                 metrics: Dict, order: int):
        """添加磁盘 I/O 优化步骤"""
        # 获取磁盘设备名（如果有）
        partitions = metrics.get('disk', {}).get('partitions', [])
        device = 'sda'  # 默认
        if partitions:
            for p in partitions:
                if p.get('device', '').startswith('/dev/sd'):
                    device = p['device'].replace('/dev/', '')
                    break
        
        plan.add_step(
            name="调整 I/O 调度器（SSD 推荐）",
            command=f"echo mq-deadline > /sys/block/{device}/queue/scheduler 2>/dev/null || echo '设备不存在或无权限'",
            description="SSD 使用 mq-deadline 调度器，HDD 使用 bfq",
            order=order
        )
        plan.add_risk("调度器修改重启后还原")
        plan.add_verify(f"cat /sys/block/{device}/queue/scheduler")
        
        # 增大读预读
        plan.add_step(
            name="增大读预读",
            command=f"blockdev --setra 4096 /dev/{device} 2>/dev/null || echo '无法设置'",
            description="顺序读场景增大预读到 2MB（默认通常较小）",
            order=order + 1
        )
        plan.add_risk("会占用更多内存用于预读")
        plan.add_rollback(f"blockdev --setra 128 /dev/{device}")
        plan.add_verify(f"cat /sys/block/{device}/queue/read_ahead_kb")
        
        # 优化脏页回写
        plan.add_step(
            name="优化脏页回写",
            command="sysctl -w vm.dirty_ratio=10 && sysctl -w vm.dirty_background_ratio=5",
            description="减少脏页积压，避免 I/O 突发",
            order=order + 2
        )
        plan.add_risk("可能增加写操作频率")
        plan.add_rollback("sysctl -w vm.dirty_ratio=20 && sysctl -w vm.dirty_background_ratio=10")
        plan.add_verify("sysctl vm.dirty_ratio vm.dirty_background_ratio")
    
    def _add_network_optimizations(self, plan: OptimizationPlan, 
                                    metrics: Dict, order: int):
        """添加网络优化步骤"""
        plan.add_step(
            name="启用 TIME_WAIT 回收",
            command="sysctl -w net.ipv4.tcp_tw_reuse=1",
            description="允许重用 TIME_WAIT socket，适用于高并发短连接场景",
            order=order
        )
        plan.add_risk("可能导致旧连接数据被误接收（极少见）")
        plan.add_rollback("sysctl -w net.ipv4.tcp_tw_reuse=0")
        plan.add_verify("sysctl net.ipv4.tcp_tw_reuse")
        
        plan.add_step(
            name="缩短 FIN_WAIT 超时",
            command="sysctl -w net.ipv4.tcp_fin_timeout=30",
            description="减少连接关闭等待时间",
            order=order + 1
        )
        plan.add_rollback("sysctl -w net.ipv4.tcp_fin_timeout=60")
        
        # 增大连接队列
        plan.add_step(
            name="增大连接队列",
            command="sysctl -w net.core.somaxconn=65535 && sysctl -w net.ipv4.tcp_max_syn_backlog=16384",
            description="高并发服务必备，增大监听队列",
            order=order + 2
        )
        plan.add_risk("会增加少量内存占用")
        plan.add_rollback("sysctl -w net.core.somaxconn=128 && sysctl -w net.ipv4.tcp_max_syn_backlog=1024")
        plan.add_verify("ss -s")
        
        # 优化 TCP 缓冲区
        plan.add_step(
            name="优化 TCP 缓冲区",
            command="sysctl -w net.core.rmem_max=16777216 && sysctl -w net.core.wmem_max=16777216",
            description="高带宽场景增大 TCP 缓冲区",
            order=order + 3
        )
        plan.add_risk("每个连接占用更多内存")
        plan.add_rollback("sysctl -w net.core.rmem_max=212992 && sysctl -w net.core.wmem_max=212992")
    
    def _add_load_optimizations(self, plan: OptimizationPlan, 
                                 metrics: Dict, order: int):
        """添加负载优化步骤"""
        plan.add_step(
            name="识别高负载进程",
            command="ps aux --sort=-%cpu | head -10",
            description="查看占用 CPU 最多的进程",
            order=order
        )
        
        plan.add_verify("uptime")
        plan.add_verify("cat /proc/loadavg")
    
    def save_plan(self, plan: OptimizationPlan, output_dir: str = "../reports") -> str:
        """保存优化计划"""
        import os
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存为 JSON
        json_path = output_path / f"optimization_plan_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)
        
        # 保存为可执行脚本
        script_path = output_path / f"optimization_{timestamp}.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(plan.generate_script())
        os.chmod(script_path, 0o755)
        
        # 保存回滚脚本
        rollback_path = output_path / f"rollback_{timestamp}.sh"
        with open(rollback_path, 'w', encoding='utf-8') as f:
            f.write(plan.generate_rollback_script())
        os.chmod(rollback_path, 0o755)
        
        logger.info(f"优化计划已保存：{json_path}, {script_path}")
        return str(json_path)


def create_optimizer(knowledge_base=None) -> OptimizerService:
    """创建优化器实例"""
    return OptimizerService(knowledge_base)
