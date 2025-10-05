#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API密钥获取测试脚本
用于诊断ECNU API密钥配置问题
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_ai_api_key, config

def test_api_key_sources():
    """测试各种API密钥来源"""
    print("🔍 API密钥获取测试")
    print("=" * 50)
    
    # 1. 测试环境变量
    print("\n1. 环境变量测试:")
    openai_key = os.getenv('OPENAI_API_KEY')
    ecnu_key = os.getenv('ECNU_API_KEY')
    
    print(f"   OPENAI_API_KEY: {'✅ 已设置' if openai_key else '❌ 未设置'}")
    if openai_key:
        print(f"   值: {openai_key[:10]}...{openai_key[-4:] if len(openai_key) > 14 else openai_key}")
    
    print(f"   ECNU_API_KEY: {'✅ 已设置' if ecnu_key else '❌ 未设置'}")
    if ecnu_key:
        print(f"   值: {ecnu_key[:10]}...{ecnu_key[-4:] if len(ecnu_key) > 14 else ecnu_key}")
    
    # 2. 测试配置文件
    print("\n2. 配置文件测试:")
    config_api_key = config.get('ai.api_key')
    print(f"   ai.api_key: {'✅ 已设置' if config_api_key else '❌ 未设置'}")
    if config_api_key:
        print(f"   值: {config_api_key[:10]}...{config_api_key[-4:] if len(config_api_key) > 14 else config_api_key}")
    
    # 3. 测试ECNU密钥文件
    print("\n3. ECNU密钥文件测试:")
    ecnu_key_file = config.get('ai.ecnu_key_file')
    print(f"   配置的文件路径: {ecnu_key_file}")
    
    if ecnu_key_file:
        key_path = Path(ecnu_key_file)
        print(f"   文件是否存在: {'✅ 存在' if key_path.exists() else '❌ 不存在'}")
        
        if key_path.exists():
            try:
                with open(key_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                print(f"   文件内容: {'✅ 有内容' if file_content else '❌ 空文件'}")
                if file_content:
                    print(f"   值: {file_content[:10]}...{file_content[-4:] if len(file_content) > 14 else file_content}")
            except Exception as e:
                print(f"   读取错误: ❌ {e}")
    
    # 4. 测试最终获取结果
    print("\n4. 最终API密钥获取结果:")
    final_key = get_ai_api_key()
    print(f"   get_ai_api_key(): {'✅ 成功获取' if final_key else '❌ 获取失败'}")
    if final_key:
        print(f"   值: {final_key[:10]}...{final_key[-4:] if len(final_key) > 14 else final_key}")
    
    # 5. 测试AI配置
    print("\n5. AI配置信息:")
    ai_config = config.get_ai_config()
    print(f"   provider: {ai_config.get('provider', 'N/A')}")
    print(f"   model: {ai_config.get('model', 'N/A')}")
    print(f"   base_url: {ai_config.get('base_url', 'N/A')}")
    
    return final_key is not None

def test_api_connection():
    """测试API连接"""
    print("\n🌐 API连接测试")
    print("=" * 50)
    
    api_key = get_ai_api_key()
    if not api_key:
        print("❌ 无法获取API密钥，跳过连接测试")
        return False
    
    try:
        import requests
        
        # 测试ECNU API连接
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 简单的模型列表请求
        response = requests.get(
            "https://chat.ecnu.edu.cn/open/api/v1/models",
            headers=headers,
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ API连接成功")
            try:
                models = response.json()
                if 'data' in models:
                    print(f"   可用模型数量: {len(models['data'])}")
                    for model in models['data'][:3]:  # 显示前3个模型
                        print(f"     - {model.get('id', 'Unknown')}")
            except:
                print("   响应解析成功但格式未知")
            return True
        else:
            print(f"   ❌ API连接失败: {response.text}")
            return False
            
    except ImportError:
        print("   ❌ requests库未安装，无法测试连接")
        return False
    except Exception as e:
        print(f"   ❌ 连接测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 reOrganizeObsidian API密钥诊断工具")
    print("=" * 60)
    
    # 测试API密钥获取
    key_success = test_api_key_sources()
    
    # 测试API连接
    if key_success:
        connection_success = test_api_connection()
    else:
        connection_success = False
    
    # 总结
    print("\n📋 测试总结")
    print("=" * 50)
    print(f"API密钥获取: {'✅ 成功' if key_success else '❌ 失败'}")
    print(f"API连接测试: {'✅ 成功' if connection_success else '❌ 失败'}")
    
    if not key_success:
        print("\n💡 解决建议:")
        print("1. 设置环境变量: set ECNU_API_KEY=your_api_key")
        print("2. 或在config.yaml中设置: ai.api_key: 'your_api_key'")
        print("3. 或创建密钥文件并在config.yaml中配置路径")
    
    return key_success and connection_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)