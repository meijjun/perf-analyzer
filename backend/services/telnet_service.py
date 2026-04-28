#!/usr/bin/env python3
"""
Telnet 服务 - 远程连接和数据采集
"""

import telnetlib
import time
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TelnetService:
    """Telnet 连接服务"""
    
    # 性能采集命令（与 SSH 相同）
    COLLECTION_COMMANDS = {
        "system_info": ["hostname", "uname -r", "uptime -p", "date"],
        "cpu_info": ["cat /proc/loadavg", "top -bn1 | grep 'Cpu(s)' | head -1", "ps aux --sort=-%cpu | head -11"],
        "memory_info": ["free -h", "cat /proc/meminfo | head -20"],
        "disk_io_info": ["df -h", "mount | grep -E '^/dev'"],
        "network_info": ["ip addr show 2>/dev/null || ifconfig", "ss -s", "ss -antp | head -20"],
        "process_info": ["ps aux | wc -l", "ps aux --sort=-%cpu | head -6"]
    }
    
    def __init__(self):
        self.client = None
        self.connected = False
        self.host = None
        self.command_logger = None
        self.target_info = {}
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立 Telnet 连接（带日志）"""
        try:
            self.target_info = config
            host = config.get("host")
            self.host = host
            port = config.get("port", 23)
            username = config.get("username")
            password = config.get("password", "")
            timeout = config.get("timeout", 30)
            
            # 初始化命令日志
            task_id = config.get('task_id')
            if task_id:
                from services.command_logger import get_command_logger
                self.command_logger = get_command_logger(task_id)
                self.command_logger.log_connection('connect', host, port, 'telnet')
            
            self.client = telnetlib.Telnet(host, port, timeout)
            
            # 等待登录提示
            self.client.write(b"\r\n")
            time.sleep(0.5)
            self.client.read_very_eager()
            
            # 发送用户名
            self.client.write(username.encode('ascii') + b"\r\n")
            time.sleep(0.5)
            
            # 发送密码（如果有）
            if password:
                try:
                    self.client.read_until(b"assword:", timeout=10)
                    self.client.write(password.encode('ascii') + b"\r\n")
                    time.sleep(1)
                except:
                    pass  # 某些设备不需要密码
            
            # 等待命令提示符
            time.sleep(1)
            self.client.read_very_eager()
            
            self.host = host
            self.connected = True
            logger.info(f"[Telnet] 已连接到 {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"[Telnet] 连接失败：{e}")
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
            # 执行命令
            self.client.write(command.encode('ascii') + b"\r\n")
            time.sleep(1)  # 等待命令执行
            
            # 读取输出
            output = self.client.read_very_eager().decode('utf-8', errors='ignore')
            
            # 清理输出（去除命令本身和提示符）
            lines = output.strip().split('\r\n')
            clean_output = '\n'.join([l for l in lines if l.strip() and command not in l])
            
            return {
                "success": True,
                "stdout": clean_output,
                "stderr": "",
                "return_code": 0
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
        """收集性能数据（带命令日志）"""
        if not self.connected:
            return {"success": False, "error": "未连接"}
        
        logger.info("[Telnet 采集] 开始收集性能数据...")
        
        # 记录采集开始
        if self.command_logger:
            self.command_logger.log_collection_start(1)
        
        collected_data = {"success": True, "hostname": None, "categories": {}}
        
        for category, commands in self.COLLECTION_COMMANDS.items():
            logger.info(f"  - 收集 {category}...")
            category_data = {"commands": [], "raw_output": {}}
            
            for cmd in commands:
                # 记录命令执行（带时间戳）
                if self.command_logger:
                    self.command_logger.log_command(
                        command=cmd,
                        target_host=self.host,
                        target_port=self.target_info.get('port', 23),
                        category=category
                    )
                
                # 执行命令并计时
                start_time = datetime.now()
                result = self.execute(cmd)
                end_time = datetime.now()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                cmd_name = cmd.split()[0] if cmd.split() else "unknown"
                category_data["commands"].append({"command": cmd, "success": result["success"]})
                category_data["raw_output"][cmd_name] = result
                
                # 记录命令执行结果
                if self.command_logger:
                    self.command_logger.log_command_result(
                        command=cmd,
                        stdout=result.get('stdout', ''),
                        stderr=result.get('stderr', ''),
                        exit_code=result.get('exit_code'),
                        duration_ms=duration_ms
                    )
                
                if category == "system_info" and "hostname" in cmd:
                    collected_data["hostname"] = result["stdout"].strip()
            
            collected_data["categories"][category] = category_data
        
        # 记录采集完成
        if self.command_logger:
            metrics_summary = {
                'hostname': collected_data['hostname'],
                'categories': len(collected_data['categories'])
            }
            self.command_logger.log_collection_complete(1, metrics_summary)
        
        logger.info(f"[Telnet 采集] 数据收集完成，主机名：{collected_data['hostname']}")
        return collected_data
    
    def disconnect(self):
        """断开连接（带日志）"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info(f"[Telnet] 已断开连接 {self.host}")
            
            # 记录断开连接
            if self.command_logger:
                self.command_logger.log_connection(
                    'disconnect',
                    self.host,
                    self.target_info.get('port', 23),
                    'telnet',
                    success=True
                )
