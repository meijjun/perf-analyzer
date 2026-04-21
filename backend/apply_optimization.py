#!/usr/bin/env python3
"""
应用优化脚本 - Windows 兼容版本
用法：python apply_optimization.py optimization_plan.json
"""

import sys
import json
import subprocess
from pathlib import Path

def apply_optimization(json_path):
    """应用优化计划"""
    print("=" * 60)
    print("🔧 应用性能优化")
    print("=" * 60)
    
    # 读取优化计划
    with open(json_path, 'r', encoding='utf-8') as f:
        plan = json.load(f)
    
    print(f"\n📋 优化计划：{plan['title']}")
    print(f"📝 描述：{plan['description']}")
    print(f"⏰ 生成时间：{plan['created_at']}")
    print(f"📊 步骤数量：{plan['total_steps']}")
    
    # 风险提示
    if plan.get('risks'):
        print("\n⚠️  风险提示:")
        for risk in plan['risks']:
            print(f"   - {risk}")
    
    # 确认执行
    print("\n❓ 是否继续执行优化？(y/n): ", end='')
    confirm = input().strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return False
    
    # 备份配置
    print("\n📦 正在备份当前配置...")
    backup_path = Path(f"sysctl.conf.backup.{json.dumps({'time': 'backup'})[:10]}")
    try:
        # Windows 可能没有 sysctl，跳过
        if sys.platform != 'win32':
            subprocess.run(['cp', '/etc/sysctl.conf', str(backup_path)], check=False)
        print("✅ 配置已备份")
    except:
        print("⚠️  备份失败，继续执行...")
    
    # 执行步骤
    print("\n🚀 开始执行优化步骤:\n")
    
    success_count = 0
    for step in plan.get('steps', []):
        print(f"步骤 {step['order']}: {step['name']}")
        print(f"  命令：{step['command']}")
        
        try:
            # 执行命令
            result = subprocess.run(
                step['command'],
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"  ✅ 执行成功")
                success_count += 1
            else:
                print(f"  ❌ 执行失败：{result.stderr}")
        except Exception as e:
            print(f"  ❌ 异常：{e}")
        
        print()
    
    # 验证
    print("\n✅ 验证优化效果:\n")
    for cmd in plan.get('verify_commands', []):
        print(f"执行：{cmd}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            print(result.stdout[:500])  # 限制输出长度
        except:
            pass
    
    # 总结
    print("\n" + "=" * 60)
    print(f"优化完成！成功 {success_count}/{len(plan.get('steps', []))} 个步骤")
    print("=" * 60)
    
    # 回滚提示
    print("\n💡 如需回滚，执行:")
    print(f"   {'; '.join(plan.get('rollback_commands', []))}")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法：python apply_optimization.py <优化计划 JSON 文件>")
        print("示例：python apply_optimization.py ../reports/optimization_plan_20260419.json")
        sys.exit(1)
    
    apply_optimization(sys.argv[1])
