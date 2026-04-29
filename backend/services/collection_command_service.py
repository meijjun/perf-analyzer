#!/usr/bin/env python3
"""
采集命令管理服务 - 管理性能采集命令
支持增删改查自定义命令
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class CollectionCommandService:
    """采集命令管理服务"""
    
    # 默认系统命令（不可删除）
    DEFAULT_COMMANDS = {
        "system_info": [
            {"command": "hostname", "description": "获取主机名"},
            {"command": "uname -r", "description": "查看内核版本"},
            {"command": "cat /etc/os-release | grep PRETTY_NAME", "description": "查看操作系统版本"},
            {"command": "uptime -p", "description": "查看运行时间"},
            {"command": "date", "description": "查看当前时间"}
        ],
        "cpu_info": [
            {"command": "cat /proc/cpuinfo | grep 'model name' | head -1", "description": "查看 CPU 型号"},
            {"command": "nproc", "description": "查看 CPU 核心数"},
            {"command": "top -bn1 | grep 'Cpu(s)' | head -1", "description": "查看 CPU 使用率"},
            {"command": "cat /proc/loadavg", "description": "查看系统负载"},
            {"command": "ps aux --sort=-%cpu | head -11", "description": "查看 CPU 占用最高的进程"}
        ],
        "memory_info": [
            {"command": "free -h", "description": "查看内存使用情况"},
            {"command": "cat /proc/meminfo | head -20", "description": "查看详细内存信息"},
            {"command": "cat /proc/swaps", "description": "查看交换分区"},
            {"command": "ps aux --sort=-%mem | head -11", "description": "查看内存占用最高的进程"}
        ],
        "disk_io_info": [
            {"command": "df -h", "description": "查看磁盘使用情况"},
            {"command": "iostat -x 1 1 2>/dev/null || echo 'iostat not available'", "description": "查看磁盘 IO 统计"},
            {"command": "mount | grep -E '^/dev'", "description": "查看挂载点"}
        ],
        "network_info": [
            {"command": "ip addr show 2>/dev/null || ifconfig", "description": "查看网络接口"},
            {"command": "ss -s", "description": "查看网络统计"},
            {"command": "ss -antp | head -20", "description": "查看网络连接"},
            {"command": "cat /proc/net/dev | grep -v 'Inter\\|face'", "description": "查看网络流量"}
        ],
        "process_info": [
            {"command": "ps aux | wc -l", "description": "查看进程总数"},
            {"command": "ps aux | grep -w defunct || echo 'No zombie processes'", "description": "查看僵尸进程"},
            {"command": "ps aux --sort=-%cpu | head -6", "description": "查看进程 CPU 占用"}
        ]
    }
    
    def __init__(self, commands_file: str = "../data/collection_commands.json"):
        self.commands_file = Path(commands_file)
        self.commands_file.parent.mkdir(parents=True, exist_ok=True)
        self.commands = self._load_commands()
    
    def _load_commands(self) -> Dict:
        """加载命令配置"""
        if not self.commands_file.exists():
            # 首次加载，使用默认命令
            self._save_commands(self.DEFAULT_COMMANDS.copy())
            return self.DEFAULT_COMMANDS.copy()
        
        try:
            with open(self.commands_file, 'r', encoding='utf-8') as f:
                commands = json.load(f)
            
            # 合并默认命令（防止新版本增加命令）
            merged = self.DEFAULT_COMMANDS.copy()
            for category, cmds in commands.items():
                if category in merged:
                    # 合并现有分类的命令
                    existing = {cmd['command']: cmd for cmd in merged[category]}
                    for cmd in cmds:
                        existing[cmd['command']] = cmd
                    merged[category] = list(existing.values())
                else:
                    merged[category] = cmds
            
            return merged
        except Exception as e:
            logger.error(f"加载命令配置失败：{e}，使用默认配置")
            return self.DEFAULT_COMMANDS.copy()
    
    def _save_commands(self, commands: Dict) -> None:
        """保存命令配置"""
        with open(self.commands_file, 'w', encoding='utf-8') as f:
            json.dump(commands, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 命令配置已保存：{self.commands_file}")
    
    def get_all_commands(self) -> Dict:
        """获取所有命令"""
        return self.commands
    
    def get_commands_by_category(self, category: str) -> List:
        """获取指定分类的命令"""
        return self.commands.get(category, [])
    
    def add_command(self, category: str, command: str, description: str = "", 
                   is_custom: bool = True) -> bool:
        """添加命令"""
        if category not in self.commands:
            self.commands[category] = []
        
        # 检查命令是否已存在
        for cmd in self.commands[category]:
            if cmd['command'] == command:
                return False
        
        self.commands[category].append({
            'command': command,
            'description': description,
            'is_custom': is_custom
        })
        
        self._save_commands(self.commands)
        logger.info(f"✅ 命令已添加：{category} - {command}")
        return True
    
    def update_command(self, category: str, old_command: str, 
                      new_command: str, new_description: str = "") -> bool:
        """更新命令"""
        if category not in self.commands:
            return False
        
        for cmd in self.commands[category]:
            if cmd['command'] == old_command:
                # 系统命令不能修改
                if not cmd.get('is_custom', False):
                    return False
                
                cmd['command'] = new_command
                cmd['description'] = new_description
                self._save_commands(self.commands)
                logger.info(f"✅ 命令已更新：{old_command} -> {new_command}")
                return True
        
        return False
    
    def delete_command(self, category: str, command: str) -> bool:
        """删除命令"""
        if category not in self.commands:
            return False
        
        original_count = len(self.commands[category])
        self.commands[category] = [
            cmd for cmd in self.commands[category]
            if cmd['command'] != command or not cmd.get('is_custom', False)
        ]
        
        deleted = len(self.commands[category]) < original_count
        
        if deleted:
            self._save_commands(self.commands)
            logger.info(f"✅ 命令已删除：{category} - {command}")
        
        return deleted
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(self.commands.keys())
    
    def add_category(self, category: str) -> bool:
        """添加新分类"""
        if category in self.commands:
            return False
        
        self.commands[category] = []
        self._save_commands(self.commands)
        logger.info(f"✅ 分类已添加：{category}")
        return True
    
    def delete_category(self, category: str) -> bool:
        """删除分类（只能删除自定义分类）"""
        if category not in self.commands:
            return False
        
        # 系统分类不能删除
        if category in self.DEFAULT_COMMANDS:
            return False
        
        del self.commands[category]
        self._save_commands(self.commands)
        logger.info(f"✅ 分类已删除：{category}")
        return True


# 全局单例
_command_service = None

def get_collection_command_service() -> CollectionCommandService:
    """获取采集命令服务单例"""
    global _command_service
    if _command_service is None:
        _command_service = CollectionCommandService()
    return _command_service
