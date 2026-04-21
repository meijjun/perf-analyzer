#!/usr/bin/env python3
"""
SSH 服务 - 远程连接和数据采集
"""

import paramiko
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class SSHService:
    """SSH 连接服务"""
    
    # 性能采集命令
    COLLECTION_COMMANDS = {
        "system_info": [
            "hostname",
            "uname -r",
            "cat /etc/os-release | grep PRETTY_NAME",
            "uptime -p",
            "date"
        ],
        "cpu_info": [
            "cat /proc/cpuinfo | grep 'model name' | head -1",
            "nproc",
            "top -bn1 | grep 'Cpu(s)' | head -1",
            "cat /proc/loadavg",
            "ps aux --sort=-%cpu | head -11"
        ],
        "memory_info": [
            "free -h",
            "cat /proc/meminfo | head -20",
            "cat /proc/swaps",
            "ps aux --sort=-%mem | head -11"
        ],
        "disk_io_info": [
            "df -h",
            "iostat -x 1 1 2>/dev/null || echo 'iostat not available'",
            "mount | grep -E '^/dev'"
        ],
        "network_info": [
            "ip addr show 2>/dev/null || ifconfig",
            "ss -s",
            "ss -antp | head -20",
            "cat /proc/net/dev | grep -v 'Inter\\|face'"
        ],
        "process_info": [
            "ps aux | wc -l",
            "ps aux | grep -w defunct || echo 'No zombie processes'",
            "ps aux --sort=-%cpu | head -6"
        ]
    }
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.host = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立 SSH 连接（增强兼容性）"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            host = config.get("host")
            port = config.get("port", 22)
            username = config.get("username")
            auth_method = config.get("auth", "key")
            
            # 连接参数
            connect_kwargs = {
                'hostname': host,
                'port': port,
                'username': username,
                'timeout': 30,
                'banner_timeout': 60,
                'auth_timeout': 60,
                'allow_agent': False,
                'look_for_keys': False
            }
            
            if auth_method == "key":
                key_path = Path(config.get("key_path", "~/.ssh/id_rsa")).expanduser()
                connect_kwargs['key_filename'] = str(key_path)
            else:
                connect_kwargs['password'] = password
            
            # 尝试连接，失败后重试
            for attempt in range(3):
                try:
                    self.client.connect(**connect_kwargs)
                    break
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"[SSH] 连接尝试 {attempt + 1} 失败，重试中...")
                        time.sleep(2)
                    else:
                        raise
            
            self.host = host
            self.connected = True
            logger.info(f"[SSH] 已连接到 {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"[SSH] 连接失败：{e}")
            return False
    
    def execute(self, command: str) -> Dict[str, Any]:
        """执行命令"""
        if not self.connected:
            return {
                "success": False,
                "error": "未连接",
                "stdout": "",
                "stderr": "",
                "return_code": -1
            }
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            return {
                "success": True,
                "stdout": stdout.read().decode('utf-8', errors='ignore'),
                "stderr": stderr.read().decode('utf-8', errors='ignore'),
                "return_code": stdout.channel.recv_exit_status()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
                "return_code": -1
            }
    
    def collect_performance_data(self) -> Dict[str, Any]:
        """收集性能数据"""
        if not self.connected:
            return {
                "success": False,
                "error": "未连接"
            }
        
        logger.info("[采集] 开始收集性能数据...")
        
        collected_data = {
            "success": True,
            "hostname": None,
            "categories": {}
        }
        
        # 收集各个类别的数据
        for category, commands in self.COLLECTION_COMMANDS.items():
            logger.info(f"  - 收集 {category}...")
            
            category_data = {
                "commands": [],
                "raw_output": {}
            }
            
            for cmd in commands:
                result = self.execute(cmd)
                cmd_name = cmd.split()[0] if cmd.split() else "unknown"
                
                category_data["commands"].append({
                    "command": cmd,
                    "success": result["success"]
                })
                category_data["raw_output"][cmd_name] = result
                
                # 提取主机名
                if category == "system_info" and "hostname" in cmd:
                    collected_data["hostname"] = result["stdout"].strip()
            
            collected_data["categories"][category] = category_data
        
        logger.info(f"[采集] 数据收集完成，主机名：{collected_data['hostname']}")
        return collected_data
    
    def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info(f"[SSH] 已断开连接 {self.host}")
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试连接"""
        if self.connect(config):
            # 执行一个简单的测试命令
            result = self.execute("echo 'Connection successful'")
            self.disconnect()
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "连接测试成功"
                }
            else:
                return {
                    "success": False,
                    "error": "命令执行失败"
                }
        else:
            return {
                "success": False,
                "error": "无法建立连接"
            }


