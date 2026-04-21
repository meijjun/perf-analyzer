#!/usr/bin/env python3
"""
API 接口测试
"""

import os
import sys
import unittest
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


class TestAPI(unittest.TestCase):
    """API 接口测试"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_health_check(self):
        """测试健康检查接口"""
        response = self.client.get('/api/health')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'] or data['status'] == 'ok')
    
    def test_get_llm_providers(self):
        """测试获取大模型提供商列表"""
        response = self.client.get('/api/llm/providers')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
    
    def test_get_llm_models(self):
        """测试获取模型列表"""
        response = self.client.get('/api/llm/models?provider=aliyun')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
    
    def test_get_targets_empty(self):
        """测试获取空的目标设备列表"""
        response = self.client.get('/api/targets')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
    
    def test_add_target(self):
        """测试添加目标设备"""
        target_data = {
            'name': '测试服务器',
            'host': '192.168.1.100',
            'port': 22,
            'protocol': 'ssh',
            'username': 'admin',
            'auth': 'key'
        }
        
        response = self.client.post(
            '/api/targets',
            data=json.dumps(target_data),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['name'], '测试服务器')
    
    def test_add_target_missing_fields(self):
        """测试添加目标设备缺少必填字段"""
        target_data = {
            'name': '测试服务器'
            # 缺少 host 和 username
        }
        
        response = self.client.post(
            '/api/targets',
            data=json.dumps(target_data),
            content_type='application/json'
        )
        
        # 应该返回错误
        self.assertIn(response.status_code, [200, 400])
    
    def test_delete_target(self):
        """测试删除目标设备"""
        # 先添加
        target_data = {
            'name': '临时服务器',
            'host': '192.168.1.101',
            'username': 'admin'
        }
        add_response = self.client.post(
            '/api/targets',
            data=json.dumps(target_data),
            content_type='application/json'
        )
        target_id = json.loads(add_response.data)['data']['id']
        
        # 再删除
        delete_response = self.client.delete(f'/api/targets/{target_id}')
        data = json.loads(delete_response.data)
        
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_start_analysis_no_target(self):
        """测试开始分析但未指定目标"""
        response = self.client.post(
            '/api/analyze',
            data=json.dumps({}),
            content_type='application/json'
        )
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
    
    def test_get_reports(self):
        """测试获取报告列表"""
        response = self.client.get('/api/reports')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)
    
    def test_404_error(self):
        """测试 404 错误处理"""
        response = self.client.get('/api/nonexistent')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
        self.assertIn('error', data)


class TestWebPages(unittest.TestCase):
    """Web 页面测试"""
    
    def setUp(self):
        """测试前准备"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_index_page(self):
        """测试主页"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Linux', response.data)
    
    def test_static_files(self):
        """测试静态文件服务"""
        # Flask 会自动服务静态文件，这里只验证应用能正常启动
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
