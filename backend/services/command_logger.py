#!/usr/bin/env python3
"""
命令执行日志服务 - 记录发送到远程设备的所有命令
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CommandLogger:
    """命令执行日志记录器"""
    
    def __init__(self, task_id: Optional[str] = None):
        self.task_id = task_id
        self.log_file = self._get_log_file_path()
        self._ensure_log_dir()
    
    def _get_log_file_path(self) -> str:
        """获取日志文件路径"""
        if self.task_id:
            log_dir = f"../reports/{self.task_id}"
        else:
            log_dir = "../logs"
        
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{log_dir}/commands_{timestamp}.log"
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        log_dir = os.path.dirname(self.log_file)
        os.makedirs(log_dir, exist_ok=True)
    
    def log_command(self, command: str, target_host: str = None, 
                    target_port: int = None, category: str = None):
        """记录命令执行
        
        Args:
            command: 执行的命令
            target_host: 目标主机
            target_port: 目标端口
            category: 命令分类（CPU、内存等）
        """
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'command': command,
            'target_host': target_host,
            'target_port': target_port,
            'category': category
        }
        
        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}]")
            
            if target_host:
                f.write(f" [目标：{target_host}:{target_port}]")
            
            if category:
                f.write(f" [{category}]")
            
            f.write(f"\n  命令：{command}\n")
            f.write("-" * 80 + "\n")
        
        # 同时输出到标准日志
        logger.info(f"[命令] {timestamp} - 目标:{target_host}:{target_port} - {category}: {command}")
    
    def log_command_result(self, command: str, stdout: str = None, 
                          stderr: str = None, exit_code: int = None,
                          duration_ms: int = None):
        """记录命令执行结果
        
        Args:
            command: 执行的命令
            stdout: 标准输出
            stderr: 错误输出
            exit_code: 退出码
            duration_ms: 执行耗时（毫秒）
        """
        timestamp = datetime.now().isoformat()
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [结果]\n")
            
            if exit_code is not None:
                f.write(f"  退出码：{exit_code}\n")
            
            if duration_ms is not None:
                f.write(f"  耗时：{duration_ms}ms\n")
            
            if stdout:
                # 只记录前 1000 个字符
                preview = stdout[:1000]
                if len(stdout) > 1000:
                    preview += f"\n... (共 {len(stdout)} 字符)"
                f.write(f"  输出:\n{preview}\n")
            
            if stderr:
                f.write(f"  错误:\n{stderr}\n")
            
            f.write("=" * 80 + "\n\n")
        
        # 标准日志只记录摘要
        status = "成功" if exit_code == 0 else f"失败 (exit={exit_code})"
        duration_str = f" ({duration_ms}ms)" if duration_ms else ""
        logger.info(f"[结果] {command[:50]}... - {status}{duration_str}")
    
    def log_connection(self, action: str, host: str, port: int, 
                      protocol: str = 'ssh', success: bool = True,
                      error: str = None):
        """记录连接事件
        
        Args:
            action: 动作（connect/disconnect）
            host: 主机
            port: 端口
            protocol: 协议
            success: 是否成功
            error: 错误信息
        """
        timestamp = datetime.now().isoformat()
        
        status = "✅" if success else "❌"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{status}] {action.upper()}\n")
            f.write(f"  协议：{protocol}\n")
            f.write(f"  目标：{host}:{port}\n")
            
            if error:
                f.write(f"  错误：{error}\n")
            
            f.write("=" * 80 + "\n\n")
        
        if success:
            logger.info(f"[连接] {action} {host}:{port} ({protocol}) - 成功")
        else:
            logger.error(f"[连接] {action} {host}:{port} ({protocol}) - 失败：{error}")
    
    def log_collection_start(self, collection_index: int, total: int = None):
        """记录采集开始"""
        timestamp = datetime.now().isoformat()
        
        total_str = f"/{total}" if total else ""
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{timestamp}] 📊 第 {collection_index}{total_str} 次采集开始\n")
            f.write(f"{'='*80}\n\n")
        
        logger.info(f"[采集] 第 {collection_index}{total_str} 次采集开始")
    
    def log_collection_complete(self, collection_index: int, 
                                metrics_summary: dict = None):
        """记录采集完成"""
        timestamp = datetime.now().isoformat()
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{timestamp}] ✅ 第 {collection_index} 次采集完成\n")
            
            if metrics_summary:
                f.write("  指标摘要:\n")
                for key, value in metrics_summary.items():
                    f.write(f"    - {key}: {value}\n")
            
            f.write("\n")
        
        logger.info(f"[采集] 第 {collection_index} 次采集完成 - {metrics_summary}")


# 全局日志实例
_command_loggers = {}

def get_command_logger(task_id: str = None) -> CommandLogger:
    """获取命令日志记录器"""
    global _command_loggers
    
    if task_id:
        if task_id not in _command_loggers:
            _command_loggers[task_id] = CommandLogger(task_id)
        return _command_loggers[task_id]
    else:
        return CommandLogger()


def cleanup_logger(task_id: str):
    """清理任务日志器"""
    global _command_loggers
    if task_id in _command_loggers:
        del _command_loggers[task_id]
