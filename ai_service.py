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
    
    def encode_image(self, image_path: str) -> Optional[Dict[str, str]]:
        """将图片编码为base64（不再压缩），并返回MIME类型"""
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
            b64 = base64.b64encode(image_data).decode('utf-8')
            mime = self.detect_mime_type(image_path)
            return {"base64": b64, "mime": mime}
        except Exception as e:
            print(f"编码图片失败 {image_path}: {e}")
            return None
    
    def detect_mime_type(self, image_path: str) -> str:
        """根据文件扩展名推断MIME类型"""
        ext = Path(image_path).suffix.lower()
        mapping = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.svg': 'image/svg+xml'
        }
        return mapping.get(ext, 'image/png')
    
    def analyze_image_content(self, image_path: str, context: str = "", extra_hint: str = None) -> Optional[str]:
        """分析图片内容并生成描述"""
        if not self.is_available():
            return None
        
        # 检查是否为ECNU提供商且不支持图像分析
        if self.ai_config.get('provider') == 'ecnu':
            if self.model not in ['ecnu-vl']:
                # ECNU的其他模型不支持图像分析，返回基于上下文的描述
                print(f"ECNU模型 {self.model} 不支持图像分析，使用上下文生成名称")
                return self.generate_text_based_description(context)
        
        img_data = self.encode_image(image_path)
        if not img_data:
            return None
        base64_image = img_data["base64"]
        mime_type = img_data["mime"]
            
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # 构建提示词（包含全文上下文与额外约束）
            prompt = self.build_analysis_prompt(context, extra_hint)
            
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
                                        "url": f"data:{mime_type};base64,{base64_image}"
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
                                        "url": f"data:{mime_type};base64,{base64_image}"
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
    
    def build_analysis_prompt(self, context: str = "", extra_hint: str = None) -> str:
        """构建图片分析提示词（强调中文名词短语与示例约束）"""
        base_prompt = """
请你为以下图片生成一个中文文件名（仅一个名词短语），用于描述整张图片的主要内容。

严格要求：
1. 只输出中文名词短语，避免动词和完整句子
2. 绝对不使用英文/数字/下划线/空格/破折号/符号
3. 不包含文件扩展名或格式词（如 png、jpg 等）
4. 长度不超过8个汉字，尽量简洁但完整
5. 只返回文件名，不要包含任何解释或额外内容
6. 如果文件名本身就是中文名词短语，直接返回该短语

示例（正例，仿照此风格输出）：
- 构件的样式
- 酒店预约系统流程图
- 图书预约系统状态机
- 服务器连接案例
- 没有事件发生的迁移
- 隔离级别与异常的关系

反例（不要这样命名）：
- Pasted_image_png.png（英文+扩展名，信息不足）
- TravelBookingSystemSequenceDiagram_png_png.png（英文冗长且包含格式词）
- 对象图在某个特定_时刻_给出了一个类的多个具体.png（过长且有截断痕迹）
- 将两个图片命名在一起（如 Terminal#180-185）（会导致覆盖或混淆）

请仿照正例的简洁中文名词短语风格生成文件名，并避免反例中的问题。
"""
        
        if context:
            base_prompt += f"\n以下为该图片所在笔记全文与位置信息：\n{context}"
        if extra_hint:
            base_prompt += f"\n命名约束：\n{extra_hint}"
        
        return base_prompt
    
    def generate_image_name(self, image_path: str, context: str = "", extra_hint: str = None) -> Optional[str]:
        """生成图片名称"""
        description = self.analyze_image_content(image_path, context, extra_hint)
        if not description:
            return None
            
        # 清理和格式化名称
        name = self.clean_filename(description)
        return name
    
    def clean_filename(self, filename: str) -> str:
        """清理文件名，移除特殊字符并强制中文名词短语风格"""
        import re
        
        naming_config = config.get_naming_config()
        
        # 移除常见扩展名或格式词
        filename = re.sub(r'(?i)\b(png|jpg|jpeg|gif|bmp|svg|webp)\b', '', filename)
        # 移除无意义前缀
        filename = re.sub(r'(?i)pasted[_\- ]?image', '', filename)
        
        # 移除英文和数字
        filename = re.sub(r'[A-Za-z0-9]+', '', filename)
        
        # 移除特殊字符
        filename = re.sub(r'[<>:\"/\\|?*]', '', filename)
        # 移除分隔符
        filename = re.sub(r'[_\-#]+', '', filename)
        
        # 替换空格（默认不使用下划线）
        replacement = naming_config.get('replace_spaces', '')
        filename = filename.replace(' ', replacement)
        
        # 限制长度（强制不超过14个汉字）
        max_length = min(naming_config.get('max_length', 50), 14)
        if len(filename) > max_length:
            filename = filename[:max_length]
        
        # 移除首尾空白和分隔符
        filename = filename.strip(' ._-')
        
        return filename or "未命名图片"
    
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
请依据以下上下文，为其中提到的图片生成一个中文文件名（仅名词短语）。

上下文：
{context}

严格要求：
1. 只输出中文名词短语；不含英文、数字或符号
2. 不包含扩展名或格式词（如 png、jpg）
3. 长度不超过8个汉字，尽量简洁且能涵盖图片主要内容
4. 只返回文件名，不要包含任何解释
5. 如果文件名本身就是中文名词短语，直接返回该短语



示例（正例，仿照此风格输出）：
- 构件的样式
- 酒店预约系统流程图
- 图书预约系统状态机
- 服务器连接案例
- 没有事件发生的迁移
- 隔离级别与异常的关系

反例（不要这样命名）：
- Pasted_image_png.png（英文+扩展名，信息不足）
- TravelBookingSystemSequenceDiagram_png_png.png（英文冗长且包含格式词）
- 对象图在某个特定_时刻_给出了一个类的多个具体.png（过长且有截断痕迹）
- 将两个图片命名在一起（如 Terminal#180-185）（会导致覆盖或混淆）

请仿照正例的简洁中文名词短语风格生成文件名，并避免反例中的问题。
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