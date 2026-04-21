#!/usr/bin/env python3
"""
知识库服务 - 基于 linux-performance-analyzer Skill 的专业知识库
提供性能诊断规则、优化建议、参考文档检索能力
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """性能分析知识库"""
    
    # 瓶颈识别规则
    BOTTLENECK_RULES = {
        "cpu": {
            "name": "CPU 瓶颈",
            "rules": [
                {
                    "condition": lambda data: data.get("load_avg_1min", 0) > data.get("cpu_cores", 1) * 2,
                    "severity": "critical",
                    "description": "系统负载过高（load > CPU 核数×2）"
                },
                {
                    "condition": lambda data: data.get("cpu_user", 0) + data.get("cpu_system", 0) > 90,
                    "severity": "critical",
                    "description": "CPU 使用率超过 90%"
                },
                {
                    "condition": lambda data: data.get("context_switches", 0) > 500000,
                    "severity": "warning",
                    "description": "上下文切换过于频繁（> 50 万/秒）"
                },
                {
                    "condition": lambda data: data.get("cpu_iowait", 0) > 20,
                    "severity": "warning",
                    "description": "CPU 等待 I/O 时间过长（iowait > 20%）"
                }
            ],
            "doc": "references/cpu.md"
        },
        "memory": {
            "name": "内存瓶颈",
            "rules": [
                {
                    "condition": lambda data: data.get("mem_available_percent", 100) < 10,
                    "severity": "critical",
                    "description": "可用内存严重不足（< 10%）"
                },
                {
                    "condition": lambda data: data.get("swap_used_percent", 0) > 30,
                    "severity": "critical",
                    "description": "Swap 使用率过高（> 30%）"
                },
                {
                    "condition": lambda data: data.get("oom_killed", False),
                    "severity": "critical",
                    "description": "检测到 OOM Killer 事件"
                },
                {
                    "condition": lambda data: data.get("mem_available_percent", 100) < 20,
                    "severity": "warning",
                    "description": "可用内存不足（< 20%）"
                }
            ],
            "doc": "references/memory.md"
        },
        "disk_io": {
            "name": "磁盘 I/O 瓶颈",
            "rules": [
                {
                    "condition": lambda data: data.get("disk_util_percent", 0) > 95,
                    "severity": "critical",
                    "description": "磁盘利用率饱和（> 95%）"
                },
                {
                    "condition": lambda data: data.get("disk_await_ms", 0) > 50,
                    "severity": "critical",
                    "description": "磁盘 I/O 延迟过高（await > 50ms）"
                },
                {
                    "condition": lambda data: data.get("disk_util_percent", 0) > 80,
                    "severity": "warning",
                    "description": "磁盘利用率偏高（> 80%）"
                },
                {
                    "condition": lambda data: data.get("disk_await_ms", 0) > 20,
                    "severity": "warning",
                    "description": "磁盘 I/O 延迟偏高（await > 20ms）"
                }
            ],
            "doc": "references/disk_io.md"
        },
        "network": {
            "name": "网络瓶颈",
            "rules": [
                {
                    "condition": lambda data: data.get("tcp_retrans_percent", 0) > 5,
                    "severity": "critical",
                    "description": "TCP 重传率过高（> 5%）"
                },
                {
                    "condition": lambda data: data.get("time_wait_count", 0) > 10000,
                    "severity": "warning",
                    "description": "TIME_WAIT 连接过多（> 1 万）"
                },
                {
                    "condition": lambda data: data.get("tcp_retrans_percent", 0) > 1,
                    "severity": "warning",
                    "description": "TCP 重传率偏高（> 1%）"
                }
            ],
            "doc": "references/network.md"
        }
    }
    
    # 优化建议模板
    OPTIMIZATION_TEMPLATES = {
        "cpu_high": {
            "title": "CPU 使用率过高优化",
            "steps": [
                {
                    "name": "识别高 CPU 进程",
                    "command": "ps aux --sort=-%cpu | head -10",
                    "description": "查找占用 CPU 最多的进程"
                },
                {
                    "name": "减少上下文切换",
                    "command": "sysctl -w kernel.sched_min_granularity_ns=10000000",
                    "description": "增大调度粒度，减少抢占频率"
                },
                {
                    "name": "设置 CPU 性能模式",
                    "command": "echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor",
                    "description": "关闭 CPU 节能模式"
                },
                {
                    "name": "进程绑核（可选）",
                    "command": "taskset -pc 0-3 <PID>",
                    "description": "将关键进程绑定到特定 CPU 核心"
                }
            ],
            "risk": "性能模式会增加功耗；绑核可能降低其他进程性能",
            "verify": "mpstat -P ALL 1 5",
            "rollback": "sysctl -w kernel.sched_min_granularity_ns=3000000"
        },
        "memory_high": {
            "title": "内存使用率过高优化",
            "steps": [
                {
                    "name": "识别高内存进程",
                    "command": "ps aux --sort=-%mem | head -10",
                    "description": "查找占用内存最多的进程"
                },
                {
                    "name": "降低 swappiness",
                    "command": "sysctl -w vm.swappiness=10",
                    "description": "减少 Swap 使用倾向（数据库推荐 1-10）"
                },
                {
                    "name": "清理页缓存",
                    "command": "sync && echo 1 > /proc/sys/vm/drop_caches",
                    "description": "清理页缓存释放内存"
                },
                {
                    "name": "关闭透明大页",
                    "command": "echo never > /sys/kernel/mm/transparent_hugepage/enabled",
                    "description": "数据库场景建议关闭 THP"
                }
            ],
            "risk": "清理缓存可能短暂影响 I/O 性能；关闭 THP 需持久化",
            "verify": "free -h && cat /proc/meminfo",
            "rollback": "sysctl -w vm.swappiness=60"
        },
        "disk_io_slow": {
            "title": "磁盘 I/O 性能优化",
            "steps": [
                {
                    "name": "识别高 I/O 进程",
                    "command": "iotop -o -b -n 5 | head -20",
                    "description": "查找 I/O 密集进程"
                },
                {
                    "name": "调整 I/O 调度器",
                    "command": "echo mq-deadline > /sys/block/sda/queue/scheduler",
                    "description": "SSD 推荐 mq-deadline 或 none"
                },
                {
                    "name": "增大读预读",
                    "command": "blockdev --setra 4096 /dev/sda",
                    "description": "顺序读场景增大预读（2MB）"
                },
                {
                    "name": "优化脏页回写",
                    "command": "sysctl -w vm.dirty_ratio=10\nsysctl -w vm.dirty_background_ratio=5",
                    "description": "减少脏页积压"
                }
            ],
            "risk": "调度器修改重启后还原；预读过大会占用内存",
            "verify": "iostat -xz 1 5",
            "rollback": "echo bfq > /sys/block/sda/queue/scheduler"
        },
        "network_slow": {
            "title": "网络性能优化",
            "steps": [
                {
                    "name": "检查连接状态",
                    "command": "ss -s && ss -ant | awk '{print $1}' | sort | uniq -c",
                    "description": "查看 TCP 连接状态分布"
                },
                {
                    "name": "启用 TIME_WAIT 回收",
                    "command": "sysctl -w net.ipv4.tcp_tw_reuse=1",
                    "description": "允许重用 TIME_WAIT socket"
                },
                {
                    "name": "增大连接队列",
                    "command": "sysctl -w net.core.somaxconn=65535\nsysctl -w net.ipv4.tcp_max_syn_backlog=16384",
                    "description": "高并发服务必备"
                },
                {
                    "name": "优化 TCP 缓冲区",
                    "command": "sysctl -w net.core.rmem_max=16777216\nsysctl -w net.core.wmem_max=16777216",
                    "description": "高带宽场景增大缓冲区"
                }
            ],
            "risk": "增大缓冲区会增加内存占用",
            "verify": "ss -s && netstat -s | grep -i retrans",
            "rollback": "sysctl -w net.ipv4.tcp_tw_reuse=0"
        },
        "oom_killer": {
            "title": "OOM Killer 处理",
            "steps": [
                {
                    "name": "查看 OOM 日志",
                    "command": "dmesg | grep -iE 'oom|killed process' | tail -20",
                    "description": "确认被杀死的进程"
                },
                {
                    "name": "保护关键进程",
                    "command": "echo -1000 > /proc/<PID>/oom_score_adj",
                    "description": "降低关键进程被 Kill 概率"
                },
                {
                    "name": "增加 Swap（临时）",
                    "command": "swapon --show",
                    "description": "检查 Swap 配置"
                },
                {
                    "name": "优化应用内存",
                    "command": "# 根据具体应用调整内存配置",
                    "description": "如 MySQL innodb_buffer_pool_size"
                }
            ],
            "risk": "保护进程可能导致其他进程被 Kill",
            "verify": "dmesg -w",
            "rollback": "echo 0 > /proc/<PID>/oom_score_adj"
        }
    }
    
    def __init__(self, docs_dir: str = None):
        """初始化知识库"""
        if docs_dir is None:
            docs_dir = Path(__file__).parent.parent.parent / "docs"
        self.docs_dir = Path(docs_dir)
        self.doc_cache: Dict[str, str] = {}
        self._load_docs()
    
    def _load_docs(self):
        """加载参考文档到缓存"""
        doc_files = [
            "cpu.md", "memory.md", "disk_io.md", "network.md",
            "kernel_params.md", "compile_optimization.md", "case_studies.md"
        ]
        
        for doc_file in doc_files:
            doc_path = self.docs_dir / doc_file
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    self.doc_cache[doc_file] = f.read()
                    # Windows 兼容性：使用纯文本日志
                    logger.info(f"Loaded doc: {doc_file}")
            else:
                logger.warning(f"Doc not found: {doc_file}")
    
    def identify_bottlenecks(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        识别性能瓶颈
        
        Args:
            metrics: 性能指标字典，包含：
                - load_avg_1min: 1 分钟负载
                - cpu_cores: CPU 核心数
                - cpu_user: 用户态 CPU%
                - cpu_system: 内核态 CPU%
                - cpu_iowait: I/O 等待%
                - context_switches: 上下文切换/秒
                - mem_available_percent: 可用内存%
                - swap_used_percent: Swap 使用率%
                - oom_killed: 是否有 OOM 事件
                - disk_util_percent: 磁盘利用率%
                - disk_await_ms: 磁盘 I/O 延迟 ms
                - tcp_retrans_percent: TCP 重传率%
                - time_wait_count: TIME_WAIT 连接数
        
        Returns:
            瓶颈列表，每个包含：type, severity, description, doc
        """
        bottlenecks = []
        
        for category, config in self.BOTTLENECK_RULES.items():
            for rule in config["rules"]:
                try:
                    if rule["condition"](metrics):
                        bottlenecks.append({
                            "type": category,
                            "category_name": config["name"],
                            "severity": rule["severity"],
                            "description": rule["description"],
                            "doc": config["doc"]
                        })
                except Exception as e:
                    logger.error(f"评估规则失败：{e}")
        
        # 按严重程度排序
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        bottlenecks.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return bottlenecks
    
    def get_optimization_plan(self, bottleneck_type: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取优化方案
        
        Args:
            bottleneck_type: 瓶颈类型（cpu/memory/disk_io/network/oom_killer）
            metrics: 性能指标
        
        Returns:
            优化方案字典
        """
        template_key = bottleneck_type.replace("_io", "_io").replace("cpu", "cpu_high")
        if bottleneck_type == "cpu":
            template_key = "cpu_high"
        elif bottleneck_type == "memory":
            template_key = "memory_high"
        elif bottleneck_type == "disk_io":
            template_key = "disk_io_slow"
        elif bottleneck_type == "network":
            template_key = "network_slow"
        elif bottleneck_type == "oom":
            template_key = "oom_killer"
        
        template = self.OPTIMIZATION_TEMPLATES.get(template_key)
        
        if not template:
            return {
                "title": f"{bottleneck_type} 优化方案",
                "steps": [],
                "risk": "未知",
                "verify": "监控相关指标",
                "rollback": "恢复原始配置"
            }
        
        return template
    
    def get_doc_content(self, doc_name: str, section: str = None) -> str:
        """
        获取参考文档内容
        
        Args:
            doc_name: 文档名称（如 cpu.md）
            section: 章节标题（可选）
        
        Returns:
            文档内容
        """
        if doc_name not in self.doc_cache:
            return f"文档 {doc_name} 未找到"
        
        content = self.doc_cache[doc_name]
        
        if section:
            # 提取指定章节
            pattern = f"## {section}.*?(?=## |\Z)"
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(0)
        
        return content
    
    def generate_analysis_prompt(self, metrics: Dict[str, Any], 
                                  bottlenecks: List[Dict], 
                                  raw_data: str) -> str:
        """
        生成大模型分析提示词
        
        Args:
            metrics: 性能指标
            bottlenecks: 识别的瓶颈列表
            raw_data: 原始采集数据
        
        Returns:
            优化的分析提示词
        """
        bottleneck_summary = "\n".join([
            f"- [{b['severity'].upper()}] {b['description']}"
            for b in bottlenecks
        ])
        
        optimization_tips = []
        for b in bottlenecks[:3]:  # 最多 3 个优化建议
            plan = self.get_optimization_plan(b["type"], metrics)
            if plan["steps"]:
                optimization_tips.append(f"**{b['category_name']}**:\n{plan['title']}")
        
        prompt = f"""你是一位专业的 Linux 系统性能分析专家。请根据以下数据进行分析：

## 性能指标摘要

{json.dumps(metrics, indent=2, ensure_ascii=False)}

## 已识别的瓶颈

{bottleneck_summary if bottleneck_summary else "未发现明显瓶颈"}

## 原始采集数据

```
{raw_data[:5000]}  # 限制长度
```

## 参考优化方向

{chr(10).join(optimization_tips) if optimization_tips else "暂无特定建议"}

## 报告要求

请按照以下结构输出分析报告：

# 📊 Linux 性能分析报告

## 一、系统概览
- 主机名：
- 采集时间：
- 系统运行时间：
- 整体健康状态评分（0-100 分）：

## 二、性能瓶颈识别
（按严重程度列出所有问题）

### 问题 1: [问题名称]
- **严重程度**: 🔴 严重 / 🟡 警告 / 🔵 提示
- **问题描述**: 
- **证据数据**: 
- **根本原因**: 

## 三、详细分析

### 1. CPU 性能分析
### 2. 内存性能分析
### 3. 磁盘 I/O 分析
### 4. 网络性能分析

## 四、优化建议

### 优先级 P0 - 立即处理
1. [优化项]
   - 操作步骤：
   - 预期效果：
   - 风险评估：
   - 回滚方案：

### 优先级 P1 - 近期处理
### 优先级 P2 - 长期优化

## 五、验证方案

### 验证命令
### 监控指标

## 六、总结

---
*报告由 AI 性能分析专家生成 | 基于 linux-performance-analyzer Skill 知识库*
"""
        return prompt
    
    def get_quick_commands(self, scenario: str) -> List[Dict[str, str]]:
        """
        获取场景化快速诊断命令
        
        Args:
            scenario: 场景（cpu/memory/disk/network/oom）
        
        Returns:
            命令列表
        """
        commands = {
            "cpu": [
                {"desc": "负载概览", "cmd": "uptime && cat /proc/loadavg"},
                {"desc": "CPU 使用率", "cmd": "mpstat -P ALL 1 3"},
                {"desc": "上下文切换", "cmd": "vmstat 1 5"},
                {"desc": "高 CPU 进程", "cmd": "ps aux --sort=-%cpu | head -10"},
                {"desc": "中断分布", "cmd": "cat /proc/interrupts | sort -k2 -rn | head -10"}
            ],
            "memory": [
                {"desc": "内存状态", "cmd": "free -h"},
                {"desc": "内存详情", "cmd": "cat /proc/meminfo | head -20"},
                {"desc": "高内存进程", "cmd": "ps aux --sort=-%mem | head -10"},
                {"desc": "OOM 历史", "cmd": "dmesg | grep -iE 'oom|killed' | tail -10"},
                {"desc": "Slab 缓存", "cmd": "slabtop -o | head -10"}
            ],
            "disk": [
                {"desc": "磁盘空间", "cmd": "df -h"},
                {"desc": "I/O 统计", "cmd": "iostat -xz 1 3"},
                {"desc": "高 I/O 进程", "cmd": "iotop -o -b -n 3 | head -10"},
                {"desc": "调度器", "cmd": "cat /sys/block/*/queue/scheduler"},
                {"desc": "挂载选项", "cmd": "mount | grep -v tmpfs"}
            ],
            "network": [
                {"desc": "连接统计", "cmd": "ss -s"},
                {"desc": "连接状态", "cmd": "ss -ant | awk '{print $1}' | sort | uniq -c"},
                {"desc": "网络错误", "cmd": "netstat -s | grep -iE 'fail|error|drop' | grep -v ' 0 '"},
                {"desc": "接口统计", "cmd": "ip -s link"},
                {"desc": "conntrack", "cmd": "cat /proc/sys/net/netfilter/nf_conntrack_count"}
            ]
        }
        
        return commands.get(scenario, [])


# 单例
_knowledge_base_instance: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """获取知识库单例"""
    global _knowledge_base_instance
    if _knowledge_base_instance is None:
        _knowledge_base_instance = KnowledgeBase()
    return _knowledge_base_instance
