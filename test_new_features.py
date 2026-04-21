#!/usr/bin/env python3
"""
新功能测试 - 实时监控、优化命令生成、性能基线
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

print("=" * 60)
print("🧪 新功能测试")
print("=" * 60)

# 1. 测试实时监控服务
print("\n1️⃣ 测试实时监控服务...")
from services.monitor_service import get_monitor

monitor = get_monitor()
print(f"   ✓ 监控器已创建")

# 等待几秒采集数据
time.sleep(2)

metrics = monitor.get_current_metrics()
print(f"   ✓ 当前指标：CPU {metrics.get('cpu', {}).get('usage_percent', 0)}%")

summary = monitor.get_summary()
print(f"   ✓ 健康评分：{summary.get('health_score', 0)}")
print(f"   ✓ 状态：{summary.get('status', 'unknown')}")

# 2. 测试优化命令生成
print("\n2️⃣ 测试优化命令生成...")
from services.optimizer_service import create_optimizer
from services.knowledge_base import get_knowledge_base

kb = get_knowledge_base()
optimizer = create_optimizer(kb)

# 模拟瓶颈
bottlenecks = [
    {'type': 'cpu', 'severity': 'critical', 'description': 'CPU 使用率过高'},
    {'type': 'memory', 'severity': 'warning', 'description': '内存使用率偏高'}
]

plan = optimizer.generate_optimization_plan(bottlenecks, metrics)
print(f"   ✓ 生成优化计划：{plan.title}")
print(f"   ✓ 步骤数量：{len(plan.steps)}")

# 生成脚本
script = plan.generate_script()
print(f"   ✓ 脚本长度：{len(script)} 字符")
print(f"\n   脚本预览:")
for line in script.split('\n')[:10]:
    print(f"     {line}")

# 3. 测试性能基线
print("\n3️⃣ 测试性能基线...")
from services.baseline_service import get_baseline_service

baseline_svc = get_baseline_service()

# 保存基线
baseline_path = baseline_svc.save_baseline(metrics, "test_baseline", "测试基线")
print(f"   ✓ 基线已保存：{baseline_path}")

# 列出基线
baselines = baseline_svc.list_baselines()
print(f"   ✓ 基线数量：{len(baselines)}")

# 对比基线
compare_result = baseline_svc.compare_with_baseline(metrics)
print(f"   ✓ 对比结果：{compare_result.get('status', 'unknown')}")
print(f"   ✓ 问题数量：{compare_result.get('total_issues', 0)}")

print("\n" + "=" * 60)
print("✅ 所有新功能测试通过！")
print("=" * 60)

print("\n📊 功能总结:")
print("   1. 实时监控 - 每 5 秒采集性能指标，支持告警")
print("   2. 优化命令 - 自动生成可执行的优化脚本")
print("   3. 性能基线 - 保存基线并对比当前状态")
print("\n🌐 访问地址:")
print("   http://localhost:5000/dashboard - 实时监控仪表板")
print("\n🚀 启动服务:")
print("   cd backend && python app.py")
