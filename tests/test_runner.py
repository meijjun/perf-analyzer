#!/usr/bin/env python3
"""
测试运行器 - 统一测试入口
"""

import unittest
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 导入所有测试模块（直接导入，不使用 import 语句）
import sys
import os

# 添加 backend 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 动态加载测试模块
import importlib.util

def load_test_module(name):
    """加载测试模块"""
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), f'{name}.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 加载模块
test_config = load_test_module('test_config')
test_ssh_service = load_test_module('test_ssh_service')
test_llm_service = load_test_module('test_llm_service')
test_api = load_test_module('test_api')
test_integration = load_test_module('test_integration')

# 导入测试类
TestConfigManager = test_config.TestConfigManager
TestSSHService = test_ssh_service.TestSSHService
TestLLMProviders = test_llm_service.TestLLMProviders
TestLLMService = test_llm_service.TestLLMService
TestAPI = test_api.TestAPI
TestWebPages = test_api.TestWebPages
TestIntegration = test_integration.TestIntegration
TestPerformance = test_integration.TestPerformance


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSSHService))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMProviders))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMService))
    suite.addTests(loader.loadTestsFromTestCase(TestAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestWebPages))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 生成报告
    generate_report(result)
    
    return result


def generate_report(result):
    """生成测试报告"""
    report_dir = Path('tests/reports')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON 报告
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': result.testsRun,
        'passed': result.testsRun - len(result.failures) - len(result.errors),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful(),
        'details': {
            'failures': [
                {
                    'test': str(test),
                    'error': str(traceback)
                }
                for test, traceback in result.failures
            ],
            'errors': [
                {
                    'test': str(test),
                    'error': str(traceback)
                }
                for test, traceback in result.errors
            ]
        }
    }
    
    json_report_path = report_dir / f'test_report_{timestamp}.json'
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    # 文本报告
    text_report_path = report_dir / f'test_report_{timestamp}.txt'
    with open(text_report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("🧪 Web 版性能分析器 - 测试报告\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"总测试数：{result.testsRun}\n")
        f.write(f"✅ 通过：{result.testsRun - len(result.failures) - len(result.errors)}\n")
        f.write(f"❌ 失败：{len(result.failures)}\n")
        f.write(f"⚠️  错误：{len(result.errors)}\n\n")
        
        if result.failures:
            f.write("-" * 60 + "\n")
            f.write("失败详情:\n")
            f.write("-" * 60 + "\n")
            for test, traceback in result.failures:
                f.write(f"\n测试：{test}\n")
                f.write(f"错误：{traceback}\n")
        
        if result.errors:
            f.write("-" * 60 + "\n")
            f.write("错误详情:\n")
            f.write("-" * 60 + "\n")
            for test, traceback in result.errors:
                f.write(f"\n测试：{test}\n")
                f.write(f"错误：{traceback}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        if result.wasSuccessful():
            f.write("🎉 所有测试通过！\n")
        else:
            f.write("⚠️  有测试失败或错误\n")
        f.write("=" * 60 + "\n")
    
    print(f"\n📄 测试报告已保存:")
    print(f"   JSON: {json_report_path}")
    print(f"   文本：{text_report_path}")


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 Web 版性能分析器 - 自动化测试")
    print("=" * 60)
    print()
    
    result = run_all_tests()
    
    # 退出码
    sys.exit(0 if result.wasSuccessful() else 1)
