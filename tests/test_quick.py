#!/usr/bin/env python3
"""
快速测试 - 核心功能验证
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models.config import ConfigManager
from services.ssh_service import SSHService
from services.llm_service import LLMService, AliyunProvider, DeepSeekProvider, ZhipuProvider


class TestCoreFunctionality(unittest.TestCase):
    """核心功能测试"""
    
    def test_01_config_manager(self):
        """测试配置管理器"""
        print("\n✅ 测试配置管理器...")
        
        config_path = Path('/tmp/test_config_quick.yaml')
        if config_path.exists():
            config_path.unlink()
        
        config = ConfigManager(str(config_path))
        
        # 验证默认配置
        self.assertIn('llm', config.config)
        self.assertIn('server', config.config)
        
        # 验证大模型配置
        llm_config = config.get_llm_config()
        self.assertIn('aliyun', llm_config)
        self.assertIn('deepseek', llm_config)
        
        # 验证服务器配置
        server_config = config.get_server_config()
        self.assertEqual(server_config['port'], 5000)
        
        config_path.unlink()
        print("   ✓ 配置管理器正常")
    
    def test_02_ssh_service(self):
        """测试 SSH 服务"""
        print("\n✅ 测试 SSH 服务...")
        
        ssh = SSHService()
        
        # 验证初始化
        self.assertFalse(ssh.connected)
        self.assertIsNone(ssh.client)
        
        # 验证方法存在
        self.assertTrue(hasattr(ssh, 'connect'))
        self.assertTrue(hasattr(ssh, 'execute'))
        self.assertTrue(hasattr(ssh, 'collect_performance_data'))
        self.assertTrue(hasattr(ssh, 'disconnect'))
        
        # 验证采集命令定义
        self.assertIn('cpu_info', ssh.COLLECTION_COMMANDS)
        self.assertIn('memory_info', ssh.COLLECTION_COMMANDS)
        
        print("   ✓ SSH 服务正常")
    
    def test_03_llm_providers(self):
        """测试大模型提供商"""
        print("\n✅ 测试大模型提供商...")
        
        # 阿里云
        aliyun = AliyunProvider('test_key')
        self.assertEqual(aliyun.get_name(), 'aliyun')
        self.assertGreater(len(aliyun.get_models()), 0)
        
        # DeepSeek
        deepseek = DeepSeekProvider('test_key')
        self.assertEqual(deepseek.get_name(), 'deepseek')
        self.assertIn('deepseek-chat', deepseek.get_models())
        
        # 智谱 AI
        zhipu = ZhipuProvider('test_key')
        self.assertEqual(zhipu.get_name(), 'zhipu')
        self.assertIn('glm-4', zhipu.get_models())
        
        print("   ✓ 大模型提供商正常")
    
    @patch('services.llm_service.requests.post')
    def test_04_llm_api_mock(self, mock_post):
        """测试大模型 API 调用（Mock）"""
        print("\n✅ 测试大模型 API 调用...")
        
        # Mock 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status_code': 200,
            'output': {
                'choices': [{
                    'message': {'content': '测试分析结果'}
                }]
            }
        }
        mock_post.return_value = mock_response
        
        aliyun = AliyunProvider('test_key')
        result = aliyun.analyze('测试', 'qwen-max')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['content'], '测试分析结果')
        self.assertEqual(result['provider'], 'aliyun')
        
        print("   ✓ 大模型 API 调用正常")
    
    def test_05_llm_service_manager(self):
        """测试大模型服务管理"""
        print("\n✅ 测试大模型服务管理...")
        
        mock_config = Mock()
        mock_config.get_llm_config.return_value = {
            'aliyun': {'api_key': 'test'},
            'deepseek': {'api_key': 'test'}
        }
        
        service = LLMService(mock_config)
        
        # 验证提供商注册
        providers = service.get_available_providers()
        self.assertGreater(len(providers), 0)
        
        # 验证模型列表
        models = service.get_models_for_provider('aliyun')
        self.assertGreater(len(models), 0)
        
        # 验证无效提供商处理
        result = service.analyze('invalid', 'model', 'prompt')
        self.assertFalse(result['success'])
        
        print("   ✓ 大模型服务管理正常")
    
    def test_06_error_handling(self):
        """测试错误处理"""
        print("\n✅ 测试错误处理...")
        
        ssh = SSHService()
        
        # 未连接时执行命令
        result = ssh.execute('test')
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], '未连接')
        
        print("   ✓ 错误处理正常")


class TestProjectStructure(unittest.TestCase):
    """项目结构测试"""
    
    def test_project_files_exist(self):
        """测试项目文件存在"""
        print("\n✅ 测试项目文件...")
        
        base = Path(__file__).parent.parent
        
        # 后端文件
        self.assertTrue((base / 'backend' / 'app.py').exists())
        self.assertTrue((base / 'backend' / 'services' / 'llm_service.py').exists())
        self.assertTrue((base / 'backend' / 'services' / 'ssh_service.py').exists())
        self.assertTrue((base / 'backend' / 'services' / 'analysis_service.py').exists())
        self.assertTrue((base / 'backend' / 'models' / 'config.py').exists())
        
        # 前端文件
        self.assertTrue((base / 'frontend' / 'templates' / 'index.html').exists())
        
        # 配置文件
        self.assertTrue((base / 'config' / 'config.yaml').exists())
        
        # 文档
        self.assertTrue((base / 'README.md').exists())
        self.assertTrue((base / 'requirements.txt').exists())
        
        print("   ✓ 项目文件完整")


def run_quick_tests():
    """运行快速测试"""
    print("=" * 60)
    print("🧪 Web 版性能分析器 - 核心功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreFunctionality)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestProjectStructure))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print(f"测试完成：{result.testsRun} 个测试")
    print(f"✅ 通过：{result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败：{len(result.failures)}")
    print(f"⚠️  错误：{len(result.errors)}")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("\n🎉 所有核心功能测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查上方输出")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_quick_tests()
    sys.exit(0 if success else 1)
