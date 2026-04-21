#!/usr/bin/env python3
"""
Windows 兼容性检查脚本
检查所有代码中的 Windows 兼容性问题
"""

import os
import sys
import re
from pathlib import Path

def check_file(filepath):
    """检查单个文件"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except:
        return issues
    
    # 检查硬编码的 Linux 路径
    if '/tmp/' in content or '/var/log/' in content or '/etc/' in content:
        for i, line in enumerate(lines, 1):
            if '/tmp/' in line or '/var/log/' in line or '/etc/' in line:
                if not line.strip().startswith('#'):
                    issues.append(f"Line {i}: 可能包含 Linux 路径：{line.strip()[:60]}")
    
    # 检查路径分隔符
    if re.search(r"['\"][^'\"]*/[^'\"]*['\"]", content):
        # 有路径字符串，检查是否使用 os.path 或 Path
        if 'os.path' not in content and 'Path' not in content and 'pathlib' not in content:
            for i, line in enumerate(lines, 1):
                if re.search(r"['\"][^'\"]*/[^'\"]*['\"]", line):
                    if 'import' not in line and '#' not in line[:10]:
                        issues.append(f"Line {i}: 建议使用 os.path 或 Path: {line.strip()[:60]}")
    
    return issues

def main():
    print("=" * 60)
    print("🔍 Windows 兼容性检查")
    print("=" * 60)
    
    backend_dir = Path(__file__).parent / 'backend'
    all_issues = []
    
    # 检查所有 Python 文件
    for py_file in backend_dir.rglob('*.py'):
        issues = check_file(py_file)
        if issues:
            all_issues.append((py_file, issues))
    
    if all_issues:
        print(f"\n⚠️  发现 {len(all_issues)} 个文件有潜在问题:\n")
        for filepath, issues in all_issues:
            print(f"\n📄 {filepath.relative_to(backend_dir)}:")
            for issue in issues[:5]:  # 最多显示 5 个问题
                print(f"   - {issue}")
    else:
        print("\n✅ 未发现明显的 Windows 兼容性问题")
    
    print("\n" + "=" * 60)
    print("📋 Windows 部署建议:")
    print("=" * 60)
    print("""
1. 使用 start.bat 启动（已提供）
   cd perf-analyzer-web
   start.bat

2. 确保 Python 环境变量设置
   set PYTHONUTF8=1
   set PYTHONIOENCODING=utf-8

3. 日志文件路径已自动适配 Windows
   - 使用 Path 对象处理路径
   - 日志目录自动创建

4. 监控服务兼容性
   - 实时监控支持 Windows（本机模式）
   - SSH 远程连接在 Windows 下同样可用

5. 性能基线存储
   - JSON 文件存储，跨平台兼容
   - 路径使用 pathlib 处理

6. 优化脚本执行
   - Windows 下需要 .bat 版本脚本
   - 已提供 generate.bat 功能
    """)
    
    return len(all_issues) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
