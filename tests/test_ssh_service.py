#!/usr/bin/env python3
"""
SSH 服务测试
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.ssh_service import SSHService


class TestSSHService(unittest.TestCase):
    """SSH 服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.ssh_service = SSHService()
        self.test_config = {
            'host': '192.168.1.100',
            'port': 22,
            'username': 'test_user',
            'auth': 'key',
            'key_path': '~/.ssh/id_rsa'
        }
    
    def test_ssh_service_init(self):
        """测试 SSH 服务初始化"""
        self.assertFalse(self.ssh_service.connected)
        self.assertIsNone(self.ssh_service.client)
        self.assertIsNone(self.ssh_service.host)
    
    @patch('services.ssh_service.paramiko.SSHClient')
    def test_connect_with_key(self, mock_ssh_client):
        """测试使用密钥连接"""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        
        result = self.ssh_service.connect(self.test_config)
        
        self.assertTrue(result)
        self.assertTrue(self.ssh_service.connected)
        mock_client.connect.assert_called_once()
    
    @patch('services.ssh_service.paramiko.SSHClient')
    def test_connect_with_password(self, mock_ssh_client):
        """测试使用密码连接"""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        
        config = self.test_config.copy()
        config['auth'] = 'password'
        config['password'] = 'test_password'
        
        result = self.ssh_service.connect(config)
        
        self.assertTrue(result)
        mock_client.connect.assert_called_once()
        # 验证使用了密码认证
        call_args = mock_client.connect.call_args
        self.assertIn('password', call_args.kwargs)
    
    @patch('services.ssh_service.paramiko.SSHClient')
    def test_connect_failure(self, mock_ssh_client):
        """测试连接失败"""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception('连接超时')
        mock_ssh_client.return_value = mock_client
        
        result = self.ssh_service.connect(self.test_config)
        
        self.assertFalse(result)
        self.assertFalse(self.ssh_service.connected)
    
    @patch('services.ssh_service.paramiko.SSHClient')
    def test_execute_command(self, mock_ssh_client):
        """测试执行命令"""
        # 先连接
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        self.ssh_service.connect(self.test_config)
        
        # Mock 命令执行
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b'command output'
        mock_stderr.read.return_value = b''
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        
        result = self.ssh_service.execute('ls -l')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['stdout'], 'command output')
        self.assertEqual(result['return_code'], 0)
    
    def test_execute_without_connection(self):
        """测试未连接时执行命令"""
        result = self.ssh_service.execute('ls -l')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], '未连接')
    
    @patch('services.ssh_service.paramiko.SSHClient')
    def test_collect_performance_data(self, mock_ssh_client):
        """测试收集性能数据"""
        # Mock 连接
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        self.ssh_service.connect(self.test_config)
        
        # Mock 所有命令执行
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b'测试数据'
        mock_stderr.read.return_value = b''
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        
        result = self.ssh_service.collect_performance_data()
        
        self.assertTrue(result['success'])
        self.assertIn('categories', result)
        self.assertIn('cpu_info', result['categories'])
        self.assertIn('memory_info', result['categories'])
        self.assertIn('disk_io_info', result['categories'])
    
    @patch('services.ssh_service.paramiko.SSHClient')
    def test_disconnect(self, mock_ssh_client):
        """测试断开连接"""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        
        self.ssh_service.connect(self.test_config)
        self.ssh_service.disconnect()
        
        self.assertFalse(self.ssh_service.connected)
        mock_client.close.assert_called_once()
    
    @patch('services.ssh_service.paramiko.SSHClient')
    def test_test_connection(self, mock_ssh_client):
        """测试连接测试功能"""
        mock_client = Mock()
        mock_ssh_client.return_value = mock_client
        
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stdout.read.return_value = b'Connection successful'
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, Mock())
        
        result = self.ssh_service.test_connection(self.test_config)
        
        self.assertTrue(result['success'])


if __name__ == '__main__':
    unittest.main()
