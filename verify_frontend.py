#!/usr/bin/env python3
"""
前端代码验证脚本
检查 HTML 中的 Vue 组件是否所有在模板中使用的变量都在 setup 中定义并返回
"""

import re
import sys
from pathlib import Path

def verify_vue_component(html_file):
    """验证 Vue 组件"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 setup 函数
    setup_match = re.search(r'setup\(\)\s*{([^]+?)(?=^\s*}\);?\s*$)}', content, re.MULTILINE)
    if not setup_match:
        print(f"❌ {html_file}: 未找到 setup 函数")
        return False
    
    setup_content = setup_match.group(0)
    
    # 提取 return 语句中的变量
    return_match = re.search(r'return\s*{([^]+?)}', setup_content)
    if not return_match:
        print(f"❌ {html_file}: 未找到 return 语句")
        return False
    
    returned_vars = set()
    for var in re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', return_match.group(1)):
        returned_vars.add(var)
    
    # 提取模板中使用的变量（{{ }} 和 v-xxx 中的变量）
    template_vars = set()
    for match in re.findall(r'{{\s*([^}]+)\s*}}', content):
        # 提取变量名（排除函数调用和运算符）
        for var in re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', match):
            if var not in ['ref', 'computed', 'onMounted']:
                template_vars.add(var)
    
    # 检查 v-if, v-for, v-bind 等
    for match in re.findall(r':([a-zA-Z-]+)="([^"]+)"', content):
        for var in re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', match[1]):
            template_vars.add(var)
    
    # 找出未定义的变量
    undefined_vars = []
    for var in template_vars:
        if var not in returned_vars:
            # 检查是否在 setup 中定义
            if not re.search(rf'\b(const|let|var)\s+{var}\s*=', setup_content):
                undefined_vars.append(var)
    
    if undefined_vars:
        print(f"❌ {html_file}: 未定义的变量:")
        for var in sorted(undefined_vars)[:10]:
            print(f"   - {var}")
        return False
    
    print(f"✅ {html_file}: 验证通过")
    return True

if __name__ == '__main__':
    templates_dir = Path(__file__).parent / 'frontend' / 'templates'
    all_ok = True
    
    for html_file in templates_dir.glob('*.html'):
        if not verify_vue_component(html_file):
            all_ok = False
    
    sys.exit(0 if all_ok else 1)
