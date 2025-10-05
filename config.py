#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件 - 管理AI接口和其他设置
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or 'config.yaml'
        self.config_data = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = Path(self.config_file)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        else:
            # 创建默认配置文件
            default_config = self.get_default_config()
            self.save_config(default_config)
            return default_config
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'ai': {
                'provider': 'openai',  # openai, claude, ecnu, local
                'api_key': '',
                'model': 'gpt-4-vision-preview',
                'base_url': '',  # 自定义API地址
                'ecnu_key_file': '',  # ECNU密钥文件路径
                'max_tokens': 150,
                'temperature': 0.3
            },
            'image': {
                'supported_formats': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'],
                'max_size_mb': 10,
                'context_window': 2  # 图片上下文行数
            },
            'naming': {
                'max_length': 50,
                'use_ai': True,
                'fallback_strategy': 'context_keywords',  # context_keywords, file_name, timestamp
                'remove_special_chars': True,
                'replace_spaces': '_'
            },
            'organization': {
                'create_backup': True,
                'backup_suffix': '_backup',
                'skip_existing': True,
                'update_links': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'reorganize.log',
                'console': True
            }
        }
    
    def save_config(self, config_data: Dict[str, Any] = None):
        """保存配置文件"""
        data = config_data or self.config_data
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key_path: str, default=None):
        """获取配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        value = self.config_data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value):
        """设置配置值"""
        keys = key_path.split('.')
        config = self.config_data
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_ai_config(self) -> Dict[str, Any]:
        """获取AI配置"""
        return self.get('ai', {})
    
    def get_image_config(self) -> Dict[str, Any]:
        """获取图片配置"""
        return self.get('image', {})
    
    def get_naming_config(self) -> Dict[str, Any]:
        """获取命名配置"""
        return self.get('naming', {})
    
    def get_organization_config(self) -> Dict[str, Any]:
        """获取整理配置"""
        return self.get('organization', {})

# 全局配置实例
config = Config()

# 环境变量支持
def get_env_or_config(env_key: str, config_key: str, default=None):
    """优先从环境变量获取，然后从配置文件获取"""
    env_value = os.getenv(env_key)
    if env_value:
        return env_value
    return config.get(config_key, default)

# 常用配置获取函数
def get_ai_api_key() -> Optional[str]:
    """获取AI API密钥"""
    # 优先从环境变量获取OpenAI密钥
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        return api_key
    
    # 尝试从环境变量获取ECNU密钥
    ecnu_key = os.getenv('ECNU_API_KEY')
    if ecnu_key:
        return ecnu_key
    
    # 尝试从配置文件获取API密钥
    config_api_key = config.get('ai.api_key')
    if config_api_key:
        return config_api_key
    
    # 尝试读取ECNU密钥文件
    ecnu_key_file = config.get('ai.ecnu_key_file')
    if ecnu_key_file:
        try:
            key_path = Path(ecnu_key_file)
            if key_path.exists():
                with open(key_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"读取ECNU密钥文件失败: {e}")
    
    return None

def get_ai_model() -> str:
    """获取AI模型"""
    provider = config.get('ai.provider', 'openai')
    if provider == 'ecnu':
        return get_env_or_config('AI_MODEL', 'ai.model') or 'ecnu-vl'
    else:
        return get_env_or_config('AI_MODEL', 'ai.model') or 'gpt-4-vision-preview'

def get_ai_base_url() -> Optional[str]:
    """获取AI API基础URL"""
    return get_env_or_config('AI_BASE_URL', 'ai.base_url')