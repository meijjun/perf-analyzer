#!/usr/bin/env python3
"""
实时监控服务 - 每 5 秒采集性能指标，提供实时数据流
跨平台支持：Windows/Linux/macOS
"""

import os
import time
import threading
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from collections import deque

logger = logging.getLogger(__name__)


class RealTimeMonitor:
    """实时监控器"""
    
    DEFAULT_THRESHOLDS = {
        'cpu_critical': 90,
        'cpu_warning': 70,
        'memory_critical': 85,
        'memory_warning': 60,
        'disk_critical': 95,
        'disk_warning': 80,
        'load_critical': 2.0,
        'load_warning': 1.5,
    }
    
    def __init__(self, ssh_service=None, interval: int = 5):
        self.ssh_service = ssh_service
        self.interval = interval
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        self.is_running = False
        self.monitor_thread = None
        
        self.current_metrics: Dict[str, Any] = {}
        self.metrics_history: deque = deque(maxlen=100)
        self.alerts: deque = deque(maxlen=50)
        self.callbacks: List[Callable] = []
        self.local_mode = True
    
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"✅ 实时监控已启动（间隔：{self.interval}秒）")
    
    def stop(self):
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        logger.info("⏹️ 实时监控已停止")
    
    def _monitor_loop(self):
        while self.is_running:
            try:
                metrics = self._collect_metrics()
                self.current_metrics = metrics
                self.metrics_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics
                })
                
                alerts = self._check_alerts(metrics)
                for alert in alerts:
                    self.alerts.append(alert)
                    if alert['level'] == 'critical':
                        logger.warning(f"🚨 告警：{alert['message']}")
                
                for callback in self.callbacks:
                    try:
                        callback(metrics, alerts)
                    except Exception as e:
                        logger.error(f"回调执行失败：{e}")
                
            except Exception as e:
                logger.error(f"监控采集失败：{e}")
            
            time.sleep(self.interval)
    
    def _collect_metrics(self) -> Dict[str, Any]:
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {'usage_percent': 0, 'user_percent': 0, 'system_percent': 0, 'iowait_percent': 0, 'cores': 1, 'load_avg_1m': 0, 'load_avg_5m': 0, 'load_avg_15m': 0},
            'memory': {'total_mb': 0, 'used_mb': 0, 'available_mb': 0, 'usage_percent': 0, 'swap_total_mb': 0, 'swap_used_mb': 0, 'swap_usage_percent': 0},
            'disk': {'partitions': [], 'io_stats': {}},
            'network': {'interfaces': [], 'connections': {'established': 0, 'time_wait': 0, 'close_wait': 0}},
            'process': {'total': 0, 'top_cpu': [], 'top_memory': []}
        }
        
        if self.local_mode:
            return self._collect_local_psutil(metrics)
        else:
            return self._collect_remote_ssh(metrics)
    
    def _collect_local_psutil(self, metrics: Dict) -> Dict:
        """使用 psutil 采集本机指标（跨平台）"""
        try:
            import psutil
            
            # CPU
            metrics['cpu']['cores'] = psutil.cpu_count(logical=True) or 1
            metrics['cpu']['usage_percent'] = psutil.cpu_percent(interval=0.1)
            cpu_times = psutil.cpu_times_percent(interval=0.1)
            metrics['cpu']['user_percent'] = round(cpu_times.user, 1)
            metrics['cpu']['system_percent'] = round(cpu_times.system, 1)
            metrics['cpu']['iowait_percent'] = round(getattr(cpu_times, 'iowait', 0), 1)
            
            # 负载（Windows 用 CPU 使用率模拟）
            try:
                load_avg = os.getloadavg()
                metrics['cpu']['load_avg_1m'] = round(load_avg[0], 2)
                metrics['cpu']['load_avg_5m'] = round(load_avg[1], 2)
                metrics['cpu']['load_avg_15m'] = round(load_avg[2], 2)
            except (AttributeError, OSError):
                cpu_load = metrics['cpu']['usage_percent'] / 100 * metrics['cpu']['cores']
                metrics['cpu']['load_avg_1m'] = round(cpu_load, 2)
                metrics['cpu']['load_avg_5m'] = round(cpu_load, 2)
                metrics['cpu']['load_avg_15m'] = round(cpu_load, 2)
            
            # 内存
            mem = psutil.virtual_memory()
            metrics['memory']['total_mb'] = round(mem.total / (1024 * 1024), 1)
            metrics['memory']['available_mb'] = round(mem.available / (1024 * 1024), 1)
            metrics['memory']['used_mb'] = round(mem.used / (1024 * 1024), 1)
            metrics['memory']['usage_percent'] = round(mem.percent, 1)
            
            # Swap
            swap = psutil.swap_memory()
            metrics['memory']['swap_total_mb'] = round(swap.total / (1024 * 1024), 1)
            metrics['memory']['swap_used_mb'] = round(swap.used / (1024 * 1024), 1)
            metrics['memory']['swap_usage_percent'] = round(swap.percent, 1)
            
            # 磁盘
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    metrics['disk']['partitions'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total_gb': round(usage.total / (1024**3), 1),
                        'used_gb': round(usage.used / (1024**3), 1),
                        'free_gb': round(usage.free / (1024**3), 1),
                        'usage_percent': round(usage.percent, 1)
                    })
                except (PermissionError, OSError):
                    pass
            
            # 网络
            net_io = psutil.net_io_counters(pernic=True)
            for iface, stats in net_io.items():
                metrics['network']['interfaces'].append({
                    'name': iface,
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv
                })
            
            # 进程
            metrics['process']['total'] = len(psutil.pids())
            
        except ImportError:
            logger.error("psutil 未安装，请运行：pip install psutil")
        except Exception as e:
            logger.error(f"psutil 采集失败：{e}")
        
        return metrics
    
    def _collect_remote_ssh(self, metrics: Dict) -> Dict:
        """通过 SSH 采集远程 Linux 设备指标（使用原生命令）"""
        try:
            if not self.ssh_service or not self.ssh_service.connected:
                logger.error("SSH 未连接")
                return metrics
            
            # CPU 信息
            stdout, stderr, code = self.ssh_service.execute("cat /proc/loadavg")
            if code == 0:
                parts = stdout.strip().split()
                metrics['cpu']['load_avg_1m'] = round(float(parts[0]), 2)
                metrics['cpu']['load_avg_5m'] = round(float(parts[1]), 2)
                metrics['cpu']['load_avg_15m'] = round(float(parts[2]), 2)
            
            stdout, stderr, code = self.ssh_service.execute("nproc")
            if code == 0:
                metrics['cpu']['cores'] = int(stdout.strip())
            
            stdout, stderr, code = self.ssh_service.execute("top -bn1 | grep 'Cpu(s)' | head -1")
            if code == 0:
                match = re.search(r'(\d+\.?\d*)\s*id', stdout)
                if match:
                    idle = float(match.group(1))
                    metrics['cpu']['usage_percent'] = round(100 - idle, 1)
            
            # 内存信息
            stdout, stderr, code = self.ssh_service.execute("free -m | grep Mem")
            if code == 0:
                parts = stdout.split()
                if len(parts) >= 7:
                    metrics['memory']['total_mb'] = int(parts[1])
                    metrics['memory']['used_mb'] = int(parts[2])
                    metrics['memory']['available_mb'] = int(parts[6])
                    metrics['memory']['usage_percent'] = round(int(parts[2]) / int(parts[1]) * 100, 1)
            
            # 磁盘信息
            stdout, stderr, code = self.ssh_service.execute("df -h | grep '^/dev'")
            if code == 0:
                for line in stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 6:
                        metrics['disk']['partitions'].append({
                            'device': parts[0],
                            'mountpoint': parts[5],
                            'total': parts[1],
                            'used': parts[2],
                            'free': parts[3],
                            'usage_percent': float(parts[4].replace('%', ''))
                        })
            
        except Exception as e:
            logger.error(f"远程 SSH 采集失败：{e}")
        
        return metrics
    
    def _check_alerts(self, metrics: Dict) -> List[Dict[str, Any]]:
        alerts = []
        
        cpu_usage = metrics['cpu']['usage_percent']
        if cpu_usage >= self.thresholds['cpu_critical']:
            alerts.append({'level': 'critical', 'type': 'cpu', 'message': f'CPU 使用率过高：{cpu_usage}%', 'timestamp': datetime.now().isoformat(), 'value': cpu_usage, 'threshold': self.thresholds['cpu_critical']})
        elif cpu_usage >= self.thresholds['cpu_warning']:
            alerts.append({'level': 'warning', 'type': 'cpu', 'message': f'CPU 使用率偏高：{cpu_usage}%', 'timestamp': datetime.now().isoformat(), 'value': cpu_usage, 'threshold': self.thresholds['cpu_warning']})
        
        mem_usage = metrics['memory']['usage_percent']
        if mem_usage >= self.thresholds['memory_critical']:
            alerts.append({'level': 'critical', 'type': 'memory', 'message': f'内存使用率过高：{mem_usage}%', 'timestamp': datetime.now().isoformat(), 'value': mem_usage, 'threshold': self.thresholds['memory_critical']})
        elif mem_usage >= self.thresholds['memory_warning']:
            alerts.append({'level': 'warning', 'type': 'memory', 'message': f'内存使用率偏高：{mem_usage}%', 'timestamp': datetime.now().isoformat(), 'value': mem_usage, 'threshold': self.thresholds['memory_warning']})
        
        for partition in metrics['disk']['partitions']:
            disk_usage = partition.get('usage_percent', 0)
            if disk_usage >= self.thresholds['disk_critical']:
                alerts.append({'level': 'critical', 'type': 'disk', 'message': f"磁盘空间严重不足 ({partition['mountpoint']}): {disk_usage}%", 'timestamp': datetime.now().isoformat(), 'value': disk_usage, 'threshold': self.thresholds['disk_critical']})
            elif disk_usage >= self.thresholds['disk_warning']:
                alerts.append({'level': 'warning', 'type': 'disk', 'message': f"磁盘空间偏少 ({partition['mountpoint']}): {disk_usage}%", 'timestamp': datetime.now().isoformat(), 'value': disk_usage, 'threshold': self.thresholds['disk_warning']})
        
        return alerts
    
    def get_current_metrics(self) -> Dict[str, Any]:
        return self.current_metrics
    
    def get_history(self, minutes: int = 10) -> List[Dict]:
        cutoff = datetime.now().timestamp() - (minutes * 60)
        return [item for item in self.metrics_history if datetime.fromisoformat(item['timestamp']).timestamp() > cutoff]
    
    def get_alerts(self, limit: int = 20) -> List[Dict]:
        return list(self.alerts)[-limit:]
    
    def get_summary(self) -> Dict[str, Any]:
        if not self.current_metrics:
            return {'status': 'no_data'}
        
        health_score = 100
        cpu_usage = self.current_metrics['cpu']['usage_percent']
        if cpu_usage > 90:
            health_score -= 30
        elif cpu_usage > 70:
            health_score -= 15
        
        mem_usage = self.current_metrics['memory']['usage_percent']
        if mem_usage > 85:
            health_score -= 30
        elif mem_usage > 60:
            health_score -= 15
        
        for partition in self.current_metrics['disk']['partitions']:
            disk_usage = partition.get('usage_percent', 0)
            if disk_usage > 95:
                health_score -= 20
            elif disk_usage > 80:
                health_score -= 10
        
        status = 'healthy' if health_score >= 80 else ('warning' if health_score >= 60 else 'critical')
        
        return {
            'status': status,
            'health_score': max(0, health_score),
            'timestamp': self.current_metrics['timestamp'],
            'cpu_usage': cpu_usage,
            'memory_usage': mem_usage,
            'active_alerts': len([a for a in self.alerts if a['level'] == 'critical']),
            'warning_alerts': len([a for a in self.alerts if a['level'] == 'warning'])
        }
    
    def register_callback(self, callback: Callable):
        self.callbacks.append(callback)


_monitor_instance: Optional[RealTimeMonitor] = None


def get_monitor() -> RealTimeMonitor:
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = RealTimeMonitor()
    return _monitor_instance
