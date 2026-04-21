#!/usr/bin/env python3
"""
配置管理模块
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "llm": {
            "aliyun": {
                "api_key": "",
                "enabled": True
            },
            "deepseek": {
                "api_key": "",
                "enabled": True
            },
            "zhipu": {
                "api_key": "",
                "enabled": True
            },
            "baidu": {
                "api_key": "",
                "secret_key": "",
                "enabled": False
            },
            "custom": {
                "api_url": "",
                "api_key": "",
                "model_name": "",
                "enabled": False
            }
        },
        "targets": [],
        "analysis": {
            "default_provider": "aliyun",
            "default_model": "qwen-max",
            "timeout": 120
        },
        "server": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": True
        }
    }
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if not self.config_path.exists():
            logger.info(f"配置文件不存在，创建默认配置：{self.config_path}")
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 合并默认配置
            merged = self._merge_config(self.DEFAULT_CONFIG, config)
            logger.info(f"✅ 配置已加载：{self.config_path}")
            return merged
            
        except Exception as e:
            logger.error(f"加载配置失败：{e}，使用默认配置")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_config(self, default: Dict, custom: Dict) -> Dict:
        """合并配置"""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: Dict) -> None:
        """保存配置文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"✅ 配置已保存：{self.config_path}")
    
    def get_llm_config(self) -> Dict:
        """获取大模型配置"""
        return self.config.get("llm", {})
    
    def update_llm_config(self, new_config: Dict) -> None:
        """更新大模型配置"""
        if "llm" not in self.config:
            self.config["llm"] = {}
        
        for provider, provider_config in new_config.items():
            if provider in self.config["llm"]:
                self.config["llm"][provider].update(provider_config)
            else:
                self.config["llm"][provider] = provider_config
        
        self._save_config(self.config)
        logger.info("✅ 大模型配置已更新")
    
    def get_targets(self) -> List[Dict]:
        """获取目标设备列表"""
        targets = self.config.get("targets")
        return targets if targets is not None else []
    
    def add_target(self, target: Dict) -> None:
        """添加目标设备"""
        if self.config.get("targets") is None:
            self.config["targets"] = []
        
        self.config["targets"].append(target)
        self._save_config(self.config)
        logger.info(f"✅ 目标设备已添加：{target.get('name')}")
    
    def delete_target(self, target_id: str) -> None:
        """删除目标设备"""
        if "targets" in self.config:
            self.config["targets"] = [
                t for t in self.config["targets"] 
                if t.get("id") != target_id
            ]
            self._save_config(self.config)
            logger.info(f"✅ 目标设备已删除：{target_id}")
    
    def get_server_config(self) -> Dict:
        """获取服务器配置"""
        return self.config.get("server", {})
    
    def get_analysis_config(self) -> Dict:
        """获取分析配置"""
        return self.config.get("analysis", {})
