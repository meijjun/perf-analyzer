#!/usr/bin/env python3
"""
大模型服务 - 支持多个大模型提供商
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """大模型提供商基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        pass
    
    @abstractmethod
    def get_models(self) -> List[str]:
        pass
    
    @abstractmethod
    def analyze(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        pass


class AliyunProvider(LLMProvider):
    """阿里云通义千问"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.models = ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-max-longcontext"]
    
    def get_name(self) -> str:
        return "aliyun"
    
    def get_models(self) -> List[str]:
        return self.models
    
    def analyze(self, prompt: str, model: str = "qwen-max", **kwargs) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {"role": "system", "content": "你是一位专业的 Linux 系统性能分析专家。请根据提供的性能数据，分析问题、识别瓶颈，并提供详细的优化建议。"},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "result_format": "message"
            }
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status_code") == 200:
                content = result["output"]["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "content": content,
                    "provider": "aliyun",
                    "model": model
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "请求失败"),
                    "provider": "aliyun"
                }
        except Exception as e:
            logger.error(f"阿里云 API 调用失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "aliyun"
            }


class DeepSeekProvider(LLMProvider):
    """深度求索 DeepSeek"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.models = ["deepseek-chat", "deepseek-coder"]
    
    def get_name(self) -> str:
        return "deepseek"
    
    def get_models(self) -> List[str]:
        return self.models
    
    def analyze(self, prompt: str, model: str = "deepseek-chat", **kwargs) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一位专业的 Linux 系统性能分析专家。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            return {
                "success": True,
                "content": content,
                "provider": "deepseek",
                "model": model
            }
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "deepseek"
            }


class ZhipuProvider(LLMProvider):
    """智谱 AI ChatGLM"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.models = ["glm-4", "glm-3-turbo", "glm-4-flash"]
    
    def get_name(self) -> str:
        return "zhipu"
    
    def get_models(self) -> List[str]:
        return self.models
    
    def analyze(self, prompt: str, model: str = "glm-4", **kwargs) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一位专业的 Linux 系统性能分析专家。"},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            return {
                "success": True,
                "content": content,
                "provider": "zhipu",
                "model": model
            }
        except Exception as e:
            logger.error(f"智谱 AI API 调用失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "zhipu"
            }


class CustomProvider(LLMProvider):
    """自定义 OpenAI 兼容模型"""
    
    def __init__(self, api_url: str, api_key: str, model_name: str):
        # 自动补全 API 端点
        if not api_url.endswith('/chat/completions'):
            if api_url.endswith('/v1/'):
                api_url = api_url + 'chat/completions'
            elif api_url.endswith('/v1'):
                api_url = api_url + '/chat/completions'
            else:
                api_url = api_url.rstrip('/') + '/v1/chat/completions'
        
        self.api_url = api_url
        self.api_key = api_key
        self.model_name = model_name
        logger.info(f"[Custom] API 端点：{self.api_url}, 模型：{self.model_name}")
    
    def get_name(self) -> str:
        return "custom"
    
    def get_models(self) -> List[str]:
        return [self.model_name] if self.model_name else ["custom-model"]
    
    def analyze(self, prompt: str, model: str = None, **kwargs) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.model_name,
            "messages": [
                {"role": "system", "content": "你是一位专业的 Linux 系统性能分析专家。请根据提供的性能数据，分析问题、识别瓶颈，并提供详细的优化建议。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "stream": False
        }
        
        logger.info(f"[Custom] 发送请求到：{self.api_url}")
        logger.info(f"[Custom] 使用模型：{model or self.model_name}")
        logger.info(f"[Custom] 请求体大小：{len(json.dumps(payload))} bytes")
        logger.info(f"[Custom] 请求体预览：{json.dumps(payload)[:500]}...")
        
        try:
            logger.info(f"[Custom] 正在发送 HTTP POST 请求...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            logger.info(f"[Custom] HTTP 状态码：{response.status_code}")
            logger.info(f"[Custom] 响应头：{dict(response.headers)}")
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[Custom] API 响应：{result.keys() if isinstance(result, dict) else 'N/A'}")
            
            # 兼容不同 API 格式
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
            elif "result" in result:
                content = result["result"]
            elif "response" in result:
                content = result["response"]
            else:
                content = str(result)
            
            return {
                "success": True,
                "content": content,
                "provider": "custom",
                "model": model or self.model_name
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"[Custom] HTTP 错误：{e}")
            logger.error(f"[Custom] 响应内容：{e.response.text[:500] if hasattr(e, 'response') else 'N/A'}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:200] if hasattr(e, 'response') else str(e)}",
                "provider": "custom"
            }
        except Exception as e:
            logger.error(f"[Custom] API 调用失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "custom"
            }


class BaiduProvider(LLMProvider):
    """百度文心一言"""
    
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.api_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions"
        self.models = ["ernie-bot-4", "ernie-bot", "ernie-bot-turbo"]
        self.access_token = None
        self.token_expiry = None
    
    def get_name(self) -> str:
        return "baidu"
    
    def get_models(self) -> List[str]:
        return self.models
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token and self.token_expiry and self.token_expiry > datetime.now():
            return self.access_token
        
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        response = requests.post(token_url, params=params)
        result = response.json()
        
        self.access_token = result["access_token"]
        from datetime import datetime, timedelta
        self.token_expiry = datetime.now() + timedelta(seconds=result["expires_in"])
        
        return self.access_token
    
    def analyze(self, prompt: str, model: str = "ernie-bot", **kwargs) -> Dict[str, Any]:
        try:
            access_token = self._get_access_token()
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {"role": "system", "content": "你是一位专业的 Linux 系统性能分析专家。"},
                    {"role": "user", "content": prompt}
                ]
            }
            
            url = f"{self.api_url}/{model}?access_token={access_token}"
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result["result"]
            return {
                "success": True,
                "content": content,
                "provider": "baidu",
                "model": model
            }
        except Exception as e:
            logger.error(f"百度 API 调用失败：{e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "baidu"
            }


class LLMService:
    """大模型服务管理器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.providers: Dict[str, LLMProvider] = {}
        self._init_providers()
    
    def _init_providers(self):
        """初始化所有提供商"""
        config = self.config_manager.get_llm_config()
        
        # 阿里云
        if config.get("aliyun", {}).get("api_key"):
            self.providers["aliyun"] = AliyunProvider(config["aliyun"]["api_key"])
            logger.info("✅ 阿里云通义千问已初始化")
        
        # DeepSeek
        if config.get("deepseek", {}).get("api_key"):
            self.providers["deepseek"] = DeepSeekProvider(config["deepseek"]["api_key"])
            logger.info("✅ DeepSeek 已初始化")
        
        # 智谱 AI
        if config.get("zhipu", {}).get("api_key"):
            self.providers["zhipu"] = ZhipuProvider(config["zhipu"]["api_key"])
            logger.info("✅ 智谱 AI 已初始化")
        
        # 百度
        if config.get("baidu", {}).get("api_key") and config.get("baidu", {}).get("secret_key"):
            self.providers["baidu"] = BaiduProvider(
                config["baidu"]["api_key"],
                config["baidu"]["secret_key"]
            )
            logger.info("✅ 百度文心一言已初始化")
        
        # 自定义模型
        custom_config = config.get("custom", {})
        if custom_config.get("api_url") and custom_config.get("api_key") and custom_config.get("model_name"):
            self.providers["custom"] = CustomProvider(
                custom_config["api_url"],
                custom_config["api_key"],
                custom_config["model_name"]
            )
            logger.info(f"✅ 自定义模型已初始化：{custom_config['model_name']}")
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """获取可用的提供商列表"""
        return [
            {
                "name": provider.get_name(),
                "models": provider.get_models()
            }
            for provider in self.providers.values()
        ]
    
    def get_models_for_provider(self, provider_name: str) -> List[str]:
        """获取指定提供商的模型列表"""
        if provider_name in self.providers:
            return self.providers[provider_name].get_models()
        return []
    
    def analyze(self, provider: str, model: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """使用指定模型进行分析"""
        if provider not in self.providers:
            return {
                "success": False,
                "error": f"不支持的提供商：{provider}"
            }
        
        return self.providers[provider].analyze(prompt, model, **kwargs)
    
    def reload_providers(self):
        """重新加载提供商配置"""
        self.providers.clear()
        self._init_providers()
