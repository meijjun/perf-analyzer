#!/usr/bin/env python3
"""
性能基线服务 - 保存性能基线，对比当前状态与基线
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class BaselineService:
    """性能基线服务"""
    
    def __init__(self, baseline_dir: str = "../baselines"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.current_baseline: Optional[Dict] = None
    
    def save_baseline(self, metrics: Dict, name: str = None, 
                      description: str = "") -> str:
        """
        保存性能基线
        
        Args:
            metrics: 性能指标
            name: 基线名称（可选，默认使用时间戳）
            description: 描述信息
        
        Returns:
            基线文件路径
        """
        if name is None:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        baseline = {
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'metrics': self._extract_key_metrics(metrics),
            'system_info': self._extract_system_info(metrics)
        }
        
        # 保存为 JSON
        baseline_path = self.baseline_dir / f"baseline_{name}.json"
        with open(baseline_path, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2, ensure_ascii=False)
        
        # 设置为当前基线
        self.current_baseline = baseline
        
        # 保存当前基线索引
        self._save_current_index(name)
        
        logger.info(f"✅ 基线已保存：{baseline_path}")
        return str(baseline_path)
    
    def load_baseline(self, name: str) -> Optional[Dict]:
        """加载指定基线"""
        baseline_path = self.baseline_dir / f"baseline_{name}.json"
        
        if not baseline_path.exists():
            logger.error(f"基线不存在：{name}")
            return None
        
        with open(baseline_path, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
        
        logger.info(f"✅ 基线已加载：{name}")
        return baseline
    
    def get_current_baseline(self) -> Optional[Dict]:
        """获取当前基线"""
        index_path = self.baseline_dir / "current.json"
        
        if not index_path.exists():
            return None
        
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        current_name = index_data.get('current_baseline')
        if current_name:
            return self.load_baseline(current_name)
        
        return None
    
    def set_current_baseline(self, name: str) -> bool:
        """设置当前基线"""
        baseline_path = self.baseline_dir / f"baseline_{name}.json"
        
        if not baseline_path.exists():
            logger.error(f"基线不存在：{name}")
            return False
        
        self._save_current_index(name)
        self.current_baseline = self.load_baseline(name)
        return True
    
    def compare_with_baseline(self, current_metrics: Dict, 
                               baseline_name: str = None) -> Dict[str, Any]:
        """
        对比当前状态与基线
        
        Args:
            current_metrics: 当前性能指标
            baseline_name: 基线名称（可选，默认使用当前基线）
        
        Returns:
            对比结果
        """
        # 加载基线
        if baseline_name:
            baseline = self.load_baseline(baseline_name)
        else:
            baseline = self.get_current_baseline()
        
        if not baseline:
            return {
                'success': False,
                'error': '基线不存在',
                'baseline_name': baseline_name
            }
        
        baseline_metrics = baseline.get('metrics', {})
        current = self._extract_key_metrics(current_metrics)
        
        # 对比各项指标
        comparisons = []
        issues = []
        
        # CPU 对比
        cpu_issue = self._compare_metric(
            'CPU 使用率',
            current.get('cpu_usage', 0),
            baseline_metrics.get('cpu_usage', 0),
            higher_is_worse=True
        )
        if cpu_issue:
            issues.append(cpu_issue)
        comparisons.append(cpu_issue or {'name': 'CPU 使用率', 'status': 'normal'})
        
        # 内存对比
        mem_issue = self._compare_metric(
            '内存使用率',
            current.get('memory_usage', 0),
            baseline_metrics.get('memory_usage', 0),
            higher_is_worse=True
        )
        if mem_issue:
            issues.append(mem_issue)
        comparisons.append(mem_issue or {'name': '内存使用率', 'status': 'normal'})
        
        # 负载对比
        load_issue = self._compare_metric(
            '系统负载 (1m)',
            current.get('load_avg_1m', 0),
            baseline_metrics.get('load_avg_1m', 0),
            higher_is_worse=True,
            threshold_percent=50  # 增长 50% 算异常
        )
        if load_issue:
            issues.append(load_issue)
        comparisons.append(load_issue or {'name': '系统负载', 'status': 'normal'})
        
        # Swap 对比
        swap_issue = self._compare_metric(
            'Swap 使用率',
            current.get('swap_usage', 0),
            baseline_metrics.get('swap_usage', 0),
            higher_is_worse=True,
            threshold_percent=100
        )
        if swap_issue:
            issues.append(swap_issue)
        comparisons.append(swap_issue or {'name': 'Swap 使用率', 'status': 'normal'})
        
        # 磁盘对比
        disk_issues = []
        current_disks = current.get('disk_partitions', [])
        baseline_disks = baseline_metrics.get('disk_partitions', [])
        
        for i, current_disk in enumerate(current_disks):
            if i < len(baseline_disks):
                baseline_disk = baseline_disks[i]
                if current_disk['mountpoint'] == baseline_disk['mountpoint']:
                    disk_issue = self._compare_metric(
                        f"磁盘使用率 ({current_disk['mountpoint']})",
                        current_disk['usage_percent'],
                        baseline_disk['usage_percent'],
                        higher_is_worse=True
                    )
                    if disk_issue:
                        disk_issues.append(disk_issue)
                        issues.append(disk_issue)
        
        # 生成总结
        if len(issues) == 0:
            summary = "✅ 当前状态与基线基本一致，系统运行正常"
            status = "normal"
        elif len(issues) <= 2:
            summary = f"⚠️ 发现 {len(issues)} 项指标异常，建议关注"
            status = "warning"
        else:
            summary = f"🔴 发现 {len(issues)} 项指标异常，系统性能可能存在问题"
            status = "critical"
        
        return {
            'success': True,
            'baseline_name': baseline.get('name', 'unknown'),
            'baseline_time': baseline.get('created_at', 'unknown'),
            'current_time': datetime.now().isoformat(),
            'status': status,
            'summary': summary,
            'issues': issues,
            'comparisons': comparisons,
            'total_issues': len(issues)
        }
    
    def list_baselines(self) -> List[Dict[str, Any]]:
        """列出所有基线"""
        baselines = []
        
        for file in self.baseline_dir.glob("baseline_*.json"):
            if file.name == "current.json":
                continue
            
            with open(file, 'r', encoding='utf-8') as f:
                baseline = json.load(f)
            
            baselines.append({
                'name': baseline.get('name', file.stem),
                'created_at': baseline.get('created_at', ''),
                'description': baseline.get('description', ''),
                'filename': file.name
            })
        
        # 按时间倒序排列
        baselines.sort(key=lambda x: x['created_at'], reverse=True)
        
        return baselines
    
    def delete_baseline(self, name: str) -> bool:
        """删除基线"""
        baseline_path = self.baseline_dir / f"baseline_{name}.json"
        
        if not baseline_path.exists():
            logger.error(f"基线不存在：{name}")
            return False
        
        baseline_path.unlink()
        logger.info(f"✅ 基线已删除：{name}")
        return True
    
    def _extract_key_metrics(self, metrics: Dict) -> Dict:
        """提取关键指标"""
        return {
            'cpu_usage': metrics.get('cpu', {}).get('usage_percent', 0),
            'memory_usage': metrics.get('memory', {}).get('usage_percent', 0),
            'swap_usage': metrics.get('memory', {}).get('swap_usage_percent', 0),
            'load_avg_1m': metrics.get('cpu', {}).get('load_avg_1m', 0),
            'load_avg_5m': metrics.get('cpu', {}).get('load_avg_5m', 0),
            'disk_partitions': [
                {
                    'mountpoint': p.get('mountpoint', ''),
                    'usage_percent': p.get('usage_percent', 0)
                }
                for p in metrics.get('disk', {}).get('partitions', [])
            ],
            'process_count': metrics.get('process', {}).get('total', 0)
        }
    
    def _extract_system_info(self, metrics: Dict) -> Dict:
        """提取系统信息"""
        return {
            'cpu_cores': metrics.get('cpu', {}).get('cores', 1),
            'memory_total_mb': metrics.get('memory', {}).get('total_mb', 0),
            'timestamp': metrics.get('timestamp', '')
        }
    
    def _compare_metric(self, name: str, current: float, baseline: float,
                        higher_is_worse: bool = True,
                        threshold_percent: float = 20) -> Optional[Dict]:
        """
        对比单个指标
        
        Args:
            name: 指标名称
            current: 当前值
            baseline: 基线值
            higher_is_worse: 值越高越糟糕
            threshold_percent: 变化超过多少百分比算异常
        
        Returns:
            如果有问题返回问题字典，否则返回 None
        """
        if baseline == 0:
            if current > 0:
                return {
                    'name': name,
                    'status': 'warning',
                    'current': current,
                    'baseline': baseline,
                    'change': '+∞',
                    'message': f"{name} 从 0 增长到 {current}"
                }
            return None
        
        change_percent = ((current - baseline) / baseline) * 100
        
        if higher_is_worse and change_percent > threshold_percent:
            return {
                'name': name,
                'status': 'warning' if change_percent < 50 else 'critical',
                'current': round(current, 1),
                'baseline': round(baseline, 1),
                'change': f"+{round(change_percent, 1)}%",
                'message': f"{name} 较基线增长 {round(change_percent, 1)}% ({baseline} → {current})"
            }
        elif not higher_is_worse and change_percent < -threshold_percent:
            return {
                'name': name,
                'status': 'warning',
                'current': round(current, 1),
                'baseline': round(baseline, 1),
                'change': f"{round(change_percent, 1)}%",
                'message': f"{name} 较基线下降 {abs(round(change_percent, 1))}%"
            }
        
        return None
    
    def _save_current_index(self, name: str):
        """保存当前基线索引"""
        index_path = self.baseline_dir / "current.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'current_baseline': name,
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)


def get_baseline_service() -> BaselineService:
    """获取基线服务单例"""
    return BaselineService()
