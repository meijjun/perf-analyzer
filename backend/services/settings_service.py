#!/usr/bin/env python3
"""
设置服务 - 管理全局配置（采集时长、次数等）
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SettingsService:
    """设置服务"""
    
    DEFAULT_SETTINGS = {
        'collection': {
            'duration_minutes': 10,  # 默认采集时长（分钟）
            'max_collections': 10,   # 默认最大采集次数
            'interval_seconds': 60   # 默认采集间隔（秒）
        },
        'analysis': {
            'timeout_seconds': 300,  # 分析超时时间
            'max_retries': 3         # 最大重试次数
        }
    }
    
    def __init__(self, settings_path: str = "../data/settings.json"):
        self.settings_path = Path(settings_path)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict:
        """加载设置"""
        if not self.settings_path.exists():
            self._save_settings(self.DEFAULT_SETTINGS)
            return self.DEFAULT_SETTINGS.copy()
        
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 合并默认设置
            merged = self._merge_settings(self.DEFAULT_SETTINGS, settings)
            return merged
        except Exception as e:
            logger.error(f"加载设置失败：{e}，使用默认设置")
            return self.DEFAULT_SETTINGS.copy()
    
    def _merge_settings(self, default: Dict, custom: Dict) -> Dict:
        """合并设置"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_settings(self, settings: Dict) -> None:
        """保存设置"""
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 设置已保存：{self.settings_path}")
    
    def get_settings(self) -> Dict:
        """获取所有设置"""
        return self.settings
    
    def update_settings(self, new_settings: Dict) -> bool:
        """更新设置"""
        def update_dict(target: Dict, source: Dict):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    update_dict(target[key], value)
                else:
                    target[key] = value
        
        update_dict(self.settings, new_settings)
        self._save_settings(self.settings)
        logger.info("✅ 设置已更新")
        return True
    
    def get_collection_settings(self) -> Dict:
        """获取采集设置"""
        return self.settings.get('collection', self.DEFAULT_SETTINGS['collection'])
    
    def get_analysis_settings(self) -> Dict:
        """获取分析设置"""
        return self.settings.get('analysis', self.DEFAULT_SETTINGS['analysis'])


# 全局单例
_settings_service = None

def get_settings_service() -> SettingsService:
    """获取设置服务单例"""
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
