#!/usr/bin/env python3
"""
配置管理测试
"""

import os
import sys
import unittest
import yaml
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from models.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_config_path = Path('/tmp/test_config.yaml')
        if self.test_config_path.exists():
            self.test_config_path.unlink()
        self.config_manager = ConfigManager(str(self.test_config_path))
    
    def tearDown(self):
        """测试后清理"""
        if self.test_config_path.exists():
            self.test_config_path.unlink()
    
    def test_default_config_created(self):
        """测试默认配置创建"""
        self.assertTrue(self.test_config_path.exists())
        self.assertIn('llm', self.config_manager.config)
        self.assertIn('server', self.config_manager.config)
    
    def test_get_llm_config(self):
        """测试获取大模型配置"""
        config = self.config_manager.get_llm_config()
        self.assertIsInstance(config, dict)
        self.assertIn('aliyun', config)
        self.assertIn('deepseek', config)
    
    def test_update_llm_config(self):
        """测试更新大模型配置"""
        new_config = {
            'aliyun': {'api_key': 'test_key_123'}
        }
        self.config_manager.update_llm_config(new_config)
        
        # 重新加载配置验证
        new_manager = ConfigManager(str(self.test_config_path))
        config = new_manager.get_llm_config()
        self.assertEqual(config['aliyun']['api_key'], 'test_key_123')
    
    def test_add_target(self):
        """测试添加目标设备"""
        target = {
            'id': 'test_server_1',
            'name': '测试服务器',
            'host': '192.168.1.100',
            'port': 22,
            'protocol': 'ssh',
            'username': 'admin'
        }
        self.config_manager.add_target(target)
        
        targets = self.config_manager.get_targets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]['name'], '测试服务器')
    
    def test_delete_target(self):
        """测试删除目标设备"""
        # 先添加
        target = {
            'id': 'test_server_2',
            'name': '临时服务器',
            'host': '192.168.1.101'
        }
        self.config_manager.add_target(target)
        
        # 验证已添加
        targets = self.config_manager.get_targets()
        self.assertEqual(len(targets), 1)
        
        # 再删除
        self.config_manager.delete_target('test_server_2')
        
        # 重新加载配置
        new_manager = ConfigManager(str(self.test_config_path))
        targets = new_manager.get_targets()
        self.assertEqual(len(targets), 0)
    
    def test_get_server_config(self):
        """测试获取服务器配置"""
        config = self.config_manager.get_server_config()
        self.assertIn('host', config)
        self.assertIn('port', config)
        self.assertEqual(config['port'], 5000)


if __name__ == '__main__':
    unittest.main()
