#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务模块 - 处理图片内容分析和智能命名
"""

import base64
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image
import io

from config import get_ai_api_key, get_ai_model, get_ai_base_url, config

class AIService:
    """AI服务类"""
    
    def __init__(self):
        self.api_key = get_ai_api_key()
        self.model = get_ai_model()
        self.base_url = get_ai_base_url() or "https://api.openai.com/v1"
        self.ai_config = config.get_ai_config()
        
        # 支持ECNU API
        if self.ai_config.get('provider') == 'ecnu':
            self.base_url = "https://chat.ecnu.edu.cn/open/api/v1"
            if not self.model or self.model.startswith('gpt-'):
                self.model = 'ecnu-max'  # 默认使用ecnu-max模型
        
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        return bool(self.api_key)
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """将图片编码为base64"""
        try:
            with open(image_path, "rb") as image_file:
                # 检查图片大小，如果太大则压缩
                image = Image.open(image_file)
                
                # 如果图片太大，压缩到合适大小
                max_size = (1024, 1024)
                if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # 保存压缩后的图片到内存
                    buffer = io.BytesIO()
                    format = image.format or 'PNG'
                    image.save(buffer, format=format)
                    image_data = buffer.getvalue()
                else:
                    image_file.seek(0)
                    image_data = image_file.read()
                    
                return base64.b64encode(image_data).decode('utf-8')
        except Exception as e:
            print(f"编码图片失败 {image_path}: {e}")
            return None
    
    def analyze_image_content(self, image_path: str, context: str = "") -> Optional[str]:
        """分析图片内容并生成描述"""
        if not self.is_available():
            return None
        
        # 检查是否为ECNU提供商且不支持图像分析
        if self.ai_config.get('provider') == 'ecnu':
            if self.model not in ['ecnu-vl']:
                # ECNU的其他模型不支持图像分析，返回基于上下文的描述
                print(f"ECNU模型 {self.model} 不支持图像分析，使用上下文生成名称")
                return self.generate_text_based_description(context)
            
        base64_image = self.encode_image(image_path)
        if not base64_image:
            return None
            
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建提示词
            prompt = self.build_analysis_prompt(context)
            
            # 构建消息内容
            if self.ai_config.get('provider') == 'ecnu' and self.model == 'ecnu-vl':
                # ECNU的多模态模型使用标准格式
                payload = {
                    "model": "ecnu-vl",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": self.ai_config.get('max_tokens', 150),
                    "temperature": self.ai_config.get('temperature', 0.3)
                }
            else:
                # 标准OpenAI格式
                payload = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": self.ai_config.get('max_tokens', 150),
                    "temperature": self.ai_config.get('temperature', 0.3)
                }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return content.strip()
            else:
                print(f"AI API请求失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"调用AI API失败: {e}")
            return None
    
    def build_analysis_prompt(self, context: str = "") -> str:
        """构建图片分析提示词"""
        base_prompt = """
请分析这张图片的内容，并根据图片内容和上下文信息，为这张图片生成一个简洁、描述性的文件名。

要求：
1. 文件名应该简洁明了，能够反映图片的主要内容
2. 使用中文或英文，长度不超过30个字符
3. 避免使用特殊字符，可以使用下划线或连字符
4. 如果是代码截图，请包含相关技术关键词
5. 如果是图表或流程图，请描述图表类型和主题
6. 如果是界面截图，请描述界面功能

只返回建议的文件名，不要包含其他解释。
"""
        
        if context:
            base_prompt += f"\n\n上下文信息：\n{context}"
            
        return base_prompt
    
    def generate_image_name(self, image_path: str, context: str = "") -> Optional[str]:
        """生成图片名称"""
        description = self.analyze_image_content(image_path, context)
        if not description:
            return None
            
        # 清理和格式化名称
        name = self.clean_filename(description)
        return name
    
    def clean_filename(self, filename: str) -> str:
        """清理文件名，移除特殊字符"""
        import re
        
        naming_config = config.get_naming_config()
        
        # 移除特殊字符
        if naming_config.get('remove_special_chars', True):
            filename = re.sub(r'[<>:"/\\|?*]', '', filename)
            filename = re.sub(r'[\r\n\t]', ' ', filename)
        
        # 替换空格
        if naming_config.get('replace_spaces', '_'):
            replacement = naming_config.get('replace_spaces', '_')
            filename = filename.replace(' ', replacement)
        
        # 限制长度
        max_length = naming_config.get('max_length', 50)
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        # 移除首尾空白和特殊字符
        filename = filename.strip(' ._-')
        
        return filename or "unnamed_image"
    
    def generate_text_based_description(self, context: str) -> Optional[str]:
        """基于文本上下文生成描述（当AI不支持图像分析时）"""
        if not context.strip():
            return None
            
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            prompt = f"""
根据以下上下文内容，为其中提到的图片生成一个简洁、描述性的文件名。

上下文：
{context}

要求：
1. 文件名应该简洁明了，能够反映图片可能的内容
2. 使用中文，长度不超过20个字符
3. 避免使用特殊字符，可以使用下划线
4. 只返回建议的文件名，不要包含其他解释
"""
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": self.ai_config.get('max_tokens', 50),
                "temperature": self.ai_config.get('temperature', 0.3)
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return content.strip()
            else:
                print(f"AI API请求失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"调用AI API失败: {e}")
            return None

class LocalAIService(AIService):
    """本地AI服务（可以集成本地模型）"""
    
    def __init__(self, model_path: str = None):
        super().__init__()
        self.model_path = model_path
        
    def is_available(self) -> bool:
        """检查本地AI服务是否可用"""
        # TODO: 实现本地模型检查
        return False
    
    def analyze_image_content(self, image_path: str, context: str = "") -> Optional[str]:
        """使用本地模型分析图片内容"""
        # TODO: 实现本地模型调用
        return None

def create_ai_service(provider: str = None) -> AIService:
    """创建AI服务实例"""
    provider = provider or config.get('ai.provider', 'openai')
    
    if provider == 'local':
        return LocalAIService()
    else:
        return AIService()

# 全局AI服务实例
ai_service = create_ai_service()