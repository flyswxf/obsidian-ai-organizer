#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的启动脚本 - 提供交互式界面
"""

import os
import sys
from pathlib import Path

def get_user_input():
    """获取用户输入"""
    print("🚀 reOrganizeObsidian 图片整理工具")
    print("=" * 50)
    
    # 获取Obsidian路径
    while True:
        obsidian_path = input("\n📁 请输入Obsidian文件夹路径: ").strip().strip('"')
        if not obsidian_path:
            print("❌ 路径不能为空")
            continue
        
        if not os.path.exists(obsidian_path):
            print(f"❌ 路径不存在: {obsidian_path}")
            continue
            
        if not os.path.isdir(obsidian_path):
            print(f"❌ 不是有效的文件夹: {obsidian_path}")
            continue
            
        break
    
    # 选择模式
    print("\n🔧 请选择运行模式:")
    print("1. 预览模式 (推荐首次使用)")
    print("2. 实际执行 - 不使用AI")
    print("3. 实际执行 - 使用AI")
    
    while True:
        choice = input("\n请选择 (1-3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("❌ 请输入有效选项 (1-3)")
    
    # 构建命令
    cmd_parts = ['python', 'main.py', f'"{obsidian_path}"']
    
    if choice == '1':
        cmd_parts.append('--dry-run')
        print("\n🔍 将以预览模式运行")
    elif choice == '2':
        cmd_parts.extend(['--no-ai', '--no-backup'])
        print("\n⚠️  将实际移动文件，不使用AI功能")
        confirm = input("确认继续? (y/N): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return None
    elif choice == '3':
        # 获取API密钥
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            api_key = input("\n🤖 请输入OpenAI API密钥: ").strip()
            if api_key:
                cmd_parts.extend(['--ai-key', api_key])
            else:
                print("❌ 使用AI功能需要API密钥")
                return None
        
        print("\n🤖 将使用AI功能实际移动文件")
        confirm = input("确认继续? (y/N): ").strip().lower()
        if confirm != 'y':
            print("操作已取消")
            return None
    
    return ' '.join(cmd_parts)

def main():
    """主函数"""
    try:
        # 检查依赖
        try:
            import yaml
            import tqdm
            from PIL import Image
        except ImportError as e:
            print(f"❌ 缺少依赖包: {e}")
            print("请运行: pip install -r requirements.txt")
            return 1
        
        # 检查主程序文件
        if not Path('main.py').exists():
            print("❌ 找不到 main.py 文件")
            print("请确保在正确的目录中运行此脚本")
            return 1
        
        # 获取用户输入
        command = get_user_input()
        if not command:
            return 0
        
        print(f"\n🚀 执行命令: {command}")
        print("=" * 50)
        
        # 执行命令
        exit_code = os.system(command)
        
        if exit_code == 0:
            print("\n✅ 操作完成!")
        else:
            print(f"\n❌ 操作失败，退出码: {exit_code}")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
        return 1
    except Exception as e:
        print(f"\n❌ 程序执行失败: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())