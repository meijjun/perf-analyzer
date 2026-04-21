#!/usr/bin/env python3
"""
启动前验证脚本
确保所有组件正常后再启动服务
"""

import sys
import subprocess
from pathlib import Path

def check_python():
    """检查 Python 版本"""
    import sys
    if sys.version_info < (3, 8):
        print(f"❌ Python 版本过低：{sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_dependencies():
    """检查依赖"""
    required = ['flask', 'flask_cors', 'paramiko', 'pyyaml', 'requests', 'psutil']
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"❌ 缺少依赖：{', '.join(missing)}")
        print(f"   运行：pip install -r requirements.txt")
        return False
    
    print(f"✅ 所有依赖已安装")
    return True

def check_backend():
    """检查后端"""
    try:
        from app import app
        print(f"✅ 后端模块加载成功")
        return True
    except Exception as e:
        print(f"❌ 后端加载失败：{e}")
        return False

def check_frontend():
    """检查前端文件"""
    templates = Path('frontend/templates')
    required_files = ['index.html', 'dashboard.html']
    
    for file in required_files:
        if not (templates / file).exists():
            print(f"❌ 缺少前端文件：{file}")
            return False
    
    # 检查常见的 Vue 错误
    index_html = (templates / 'index.html').read_text(encoding='utf-8')
    
    # 检查 return 语句中的变量是否都定义了
    if 'return {' in index_html:
        # 简单检查：是否有明显的未定义变量
        if 'viewDoc' in index_html and 'const viewDoc' not in index_html:
            print(f"⚠️  viewDoc 可能未定义")
    
    print(f"✅ 前端文件存在")
    return True

def check_config():
    """检查配置文件"""
    config_file = Path('backend/config/config.yaml')
    if not config_file.exists():
        print(f"⚠️  配置文件不存在，将创建默认配置")
    else:
        print(f"✅ 配置文件存在")
    return True

def check_directories():
    """检查目录"""
    dirs = ['backend/logs', 'reports', 'baselines']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    print(f"✅ 目录结构就绪")
    return True

def main():
    print("=" * 60)
    print("启动前验证")
    print("=" * 60)
    
    checks = [
        ("Python 版本", check_python),
        ("依赖检查", check_dependencies),
        ("后端检查", check_backend),
        ("前端检查", check_frontend),
        ("配置检查", check_config),
        ("目录检查", check_directories),
    ]
    
    all_ok = True
    for name, check_func in checks:
        if not check_func():
            all_ok = False
    
    print("=" * 60)
    if all_ok:
        print("✅ 所有检查通过，可以启动")
        print("\n运行：python backend/app.py")
        return 0
    else:
        print("❌ 部分检查失败，请先修复")
        return 1

if __name__ == '__main__':
    sys.exit(main())
