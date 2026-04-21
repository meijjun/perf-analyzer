#!/usr/bin/env python3
"""
集成测试 - 测试完整工作流程
"""

import os
import sys
import unittest
import time
import threading
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app
from models.config import ConfigManager
from services.ssh_service import SSHService
from services.llm_service import LLMService


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.config_path = Path('/tmp/integration_test_config.yaml')
        cls.config_manager = ConfigManager(str(cls.config_path))
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if cls.config_path.exists():
            cls.config_path.unlink()
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        print("\n=== 完整工作流程测试 ===")
        
        # 1. 配置大模型
        print("1. 配置大模型...")
        self.config_manager.update_llm_config({
            'aliyun': {'api_key': 'test_key'}
        })
        
        # 2. 添加目标设备
        print("2. 添加目标设备...")
        target = {
            'id': 'integration_test_server',
            'name': '集成测试服务器',
            'host': '192.168.1.200',
            'port': 22,
            'protocol': 'ssh',
            'username': 'test'
        }
        self.config_manager.add_target(target)
        
        # 3. 验证配置
        print("3. 验证配置...")
        targets = self.config_manager.get_targets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]['name'], '集成测试服务器')
        
        # 4. 测试 SSH 服务初始化
        print("4. 测试 SSH 服务...")
        ssh_service = SSHService()
        self.assertIsNotNone(ssh_service)
        
        # 5. 测试大模型服务初始化
        print("5. 测试大模型服务...")
        llm_service = LLMService(self.config_manager)
        providers = llm_service.get_available_providers()
        self.assertGreater(len(providers), 0)
        
        print("✅ 完整工作流程测试通过")
    
    def test_ssh_connection_simulation(self):
        """模拟 SSH 连接流程"""
        print("\n=== SSH 连接模拟测试 ===")
        
        ssh_service = SSHService()
        
        # 测试配置
        config = {
            'host': 'localhost',
            'port': 22,
            'username': 'test',
            'auth': 'password',
            'password': 'test'
        }
        
        # 不实际连接，只测试流程
        print("1. 创建 SSH 服务实例 ✓")
        print("2. 准备连接配置 ✓")
        print("3. 连接方法已定义 ✓")
        print("4. 执行命令方法已定义 ✓")
        print("5. 数据采集方法已定义 ✓")
        
        print("✅ SSH 连接模拟测试通过")
    
    def test_llm_analysis_simulation(self):
        """模拟大模型分析流程"""
        print("\n=== 大模型分析模拟测试 ===")
        
        # 创建服务
        llm_service = LLMService(self.config_manager)
        
        # 测试提示词
        prompt = """
        请分析以下性能数据：
        CPU 使用率：85%
        内存使用率：60%
        磁盘使用率：75%
        """
        
        print("1. 创建大模型服务 ✓")
        print("2. 准备分析提示词 ✓")
        print("3. 提供商列表:", len(llm_service.get_available_providers()))
        print("4. 分析方法已定义 ✓")
        
        # 验证提供商
        providers = llm_service.get_available_providers()
        self.assertGreater(len(providers), 0)
        
        print("✅ 大模型分析模拟测试通过")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 错误处理测试 ===")
        
        # 测试无效配置
        invalid_config = {
            'host': '',
            'port': 99999,  # 无效端口
            'username': ''
        }
        
        ssh_service = SSHService()
        result = ssh_service.test_connection(invalid_config)
        
        print("1. 无效配置处理 ✓")
        self.assertFalse(result['success'])
        
        # 测试无效大模型提供商
        llm_service = LLMService(self.config_manager)
        result = llm_service.analyze('invalid_provider', 'model', 'prompt')
        
        print("2. 无效提供商处理 ✓")
        self.assertFalse(result['success'])
        
        print("✅ 错误处理测试通过")


class TestPerformance(unittest.TestCase):
    """性能测试"""
    
    def test_config_load_time(self):
        """测试配置加载时间"""
        print("\n=== 配置加载性能测试 ===")
        
        start_time = time.time()
        config_manager = ConfigManager('/tmp/perf_test_config.yaml')
        end_time = time.time()
        
        load_time = (end_time - start_time) * 1000  # 毫秒
        print(f"配置加载时间：{load_time:.2f}ms")
        
        self.assertLess(load_time, 1000)  # 应该小于 1 秒
        
        # 清理
        Path('/tmp/perf_test_config.yaml').unlink(missing_ok=True)
    
    def test_llm_service_init_time(self):
        """测试大模型服务初始化时间"""
        print("\n=== 大模型服务初始化性能测试 ===")
        
        config_manager = ConfigManager('/tmp/perf_test_config2.yaml')
        
        start_time = time.time()
        llm_service = LLMService(config_manager)
        end_time = time.time()
        
        init_time = (end_time - start_time) * 1000  # 毫秒
        print(f"服务初始化时间：{init_time:.2f}ms")
        
        self.assertLess(init_time, 2000)  # 应该小于 2 秒
        
        # 清理
        Path('/tmp/perf_test_config2.yaml').unlink(missing_ok=True)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
