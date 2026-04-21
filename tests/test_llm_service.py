#!/usr/bin/env python3
"""
大模型服务测试
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.llm_service import (
    LLMService, AliyunProvider, DeepSeekProvider, 
    ZhipuProvider, LLMProvider
)


class TestLLMProviders(unittest.TestCase):
    """大模型提供商测试"""
    
    def test_aliyun_provider_init(self):
        """测试阿里云提供商初始化"""
        provider = AliyunProvider('test_api_key')
        self.assertEqual(provider.get_name(), 'aliyun')
        self.assertIsInstance(provider.get_models(), list)
        self.assertGreater(len(provider.get_models()), 0)
    
    def test_deepseek_provider_init(self):
        """测试 DeepSeek 提供商初始化"""
        provider = DeepSeekProvider('test_api_key')
        self.assertEqual(provider.get_name(), 'deepseek')
        self.assertIn('deepseek-chat', provider.get_models())
    
    def test_zhipu_provider_init(self):
        """测试智谱 AI 提供商初始化"""
        provider = ZhipuProvider('test_api_key')
        self.assertEqual(provider.get_name(), 'zhipu')
        self.assertIn('glm-4', provider.get_models())
    
    @patch('services.llm_service.requests.post')
    def test_aliyun_analyze_success(self, mock_post):
        """测试阿里云分析成功"""
        # Mock API 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status_code': 200,
            'output': {
                'choices': [{
                    'message': {
                        'content': '测试分析结果'
                    }
                }]
            }
        }
        mock_post.return_value = mock_response
        
        provider = AliyunProvider('test_key')
        result = provider.analyze('测试提示词', 'qwen-max')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['content'], '测试分析结果')
        self.assertEqual(result['provider'], 'aliyun')
    
    @patch('services.llm_service.requests.post')
    def test_aliyun_analyze_failure(self, mock_post):
        """测试阿里云分析失败"""
        mock_post.side_effect = Exception('网络错误')
        
        provider = AliyunProvider('test_key')
        result = provider.analyze('测试提示词', 'qwen-max')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    @patch('services.llm_service.requests.post')
    def test_deepseek_analyze(self, mock_post):
        """测试 DeepSeek 分析"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': 'DeepSeek 分析结果'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        provider = DeepSeekProvider('test_key')
        result = provider.analyze('测试', 'deepseek-chat')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['provider'], 'deepseek')


class TestLLMService(unittest.TestCase):
    """大模型服务管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_config = Mock()
        self.mock_config.get_llm_config.return_value = {
            'aliyun': {'api_key': 'test_key'},
            'deepseek': {'api_key': 'test_key'},
            'zhipu': {'api_key': 'test_key'}
        }
        self.llm_service = LLMService(self.mock_config)
    
    def test_get_available_providers(self):
        """测试获取可用提供商列表"""
        providers = self.llm_service.get_available_providers()
        self.assertIsInstance(providers, list)
        self.assertGreater(len(providers), 0)
        
        # 验证提供商结构
        for provider in providers:
            self.assertIn('name', provider)
            self.assertIn('models', provider)
    
    def test_get_models_for_provider(self):
        """测试获取指定提供商的模型列表"""
        models = self.llm_service.get_models_for_provider('aliyun')
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
    
    def test_get_models_for_invalid_provider(self):
        """测试获取无效提供商的模型列表"""
        models = self.llm_service.get_models_for_provider('invalid')
        self.assertEqual(models, [])
    
    def test_analyze_with_valid_provider(self):
        """测试使用有效提供商分析"""
        with patch.object(AliyunProvider, 'analyze') as mock_analyze:
            mock_analyze.return_value = {
                'success': True,
                'content': '测试结果',
                'provider': 'aliyun'
            }
            
            result = self.llm_service.analyze('aliyun', 'qwen-max', '测试提示词')
            self.assertTrue(result['success'])
            mock_analyze.assert_called_once()
    
    def test_analyze_with_invalid_provider(self):
        """测试使用无效提供商分析"""
        result = self.llm_service.analyze('invalid_provider', 'model', '提示词')
        self.assertFalse(result['success'])
        self.assertIn('不支持的提供商', result['error'])


if __name__ == '__main__':
    unittest.main()
