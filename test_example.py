#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试示例脚本 - 演示如何使用reOrganizeObsidian工具
"""

import os
import tempfile
import shutil
from pathlib import Path

def create_test_obsidian_vault():
    """创建一个测试用的Obsidian文件夹结构"""
    # 创建临时目录
    test_dir = Path(tempfile.mkdtemp(prefix="test_obsidian_"))
    print(f"创建测试目录: {test_dir}")
    
    # 创建文件夹结构
    folders = [
        "编程/Python",
        "编程/UML/类图",
        "学习笔记/数学",
        "项目/Web开发"
    ]
    
    for folder in folders:
        (test_dir / folder).mkdir(parents=True, exist_ok=True)
    
    # 创建一些测试图片文件（空文件，仅用于测试）
    test_images = [
        "Pasted image 20250611204755.png",
        "Pasted image 20250611205123.png", 
        "Pasted image 20250612101234.png",
        "screenshot_20250612.jpg"
    ]
    
    for img in test_images:
        (test_dir / img).touch()
    
    # 创建测试markdown文件
    markdown_files = {
        "编程/Python/Python基础.md": """
# Python基础知识

这是一个Python代码示例：

![[Pasted image 20250611204755.png]]

上面的图片展示了Python的基本语法。

## 数据类型

下面是数据类型的对比图：

![数据类型](Pasted image 20250611205123.png)

这个图表很好地说明了不同数据类型的特点。
""",
        
        "编程/UML/类图/面向对象设计.md": """
# 面向对象设计

## 类图设计

下面是我们系统的核心类图：

![[Pasted image 20250612101234.png]]

这个UML类图展示了系统的主要组件和它们之间的关系。

### 设计原则

1. 单一职责原则
2. 开闭原则
3. 里氏替换原则

类图中体现了这些设计原则的应用。
""",
        
        "项目/Web开发/前端架构.md": """
# 前端架构设计

## 系统架构

我们的前端架构如下图所示：

![架构图](screenshot_20250612.jpg)

这个架构图展示了前端各个模块的组织方式。

### 技术栈

- React
- TypeScript  
- Webpack
- ESLint

架构设计考虑了可维护性和扩展性。
"""
    }
    
    # 写入markdown文件
    for file_path, content in markdown_files.items():
        full_path = test_dir / file_path
        full_path.write_text(content, encoding='utf-8')
    
    print(f"测试文件结构创建完成:")
    print(f"  - 文件夹: {len(folders)} 个")
    print(f"  - 图片: {len(test_images)} 个")
    print(f"  - Markdown文件: {len(markdown_files)} 个")
    
    return test_dir

def run_test():
    """运行测试"""
    print("=" * 60)
    print("reOrganizeObsidian 工具测试")
    print("=" * 60)
    
    # 创建测试环境
    test_vault = create_test_obsidian_vault()
    
    try:
        print("\n📁 测试文件夹结构:")
        for root, dirs, files in os.walk(test_vault):
            level = root.replace(str(test_vault), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        print("\n🔍 现在可以运行以下命令来测试工具:")
        print(f"\n预览模式 (推荐):")
        print(f"python main.py \"{test_vault}\" --dry-run")
        
        print(f"\n不使用AI:")
        print(f"python main.py \"{test_vault}\" --no-ai --dry-run")
        
        print(f"\n使用AI (需要API密钥):")
        print(f"python main.py \"{test_vault}\" --ai-key YOUR_API_KEY --dry-run")
        
        print(f"\n实际执行 (谨慎使用):")
        print(f"python main.py \"{test_vault}\" --no-ai")
        
        print(f"\n📂 测试目录位置: {test_vault}")
        print(f"\n⚠️  测试完成后，可以删除测试目录: {test_vault}")
        
        return test_vault
        
    except Exception as e:
        print(f"❌ 测试创建失败: {e}")
        # 清理测试目录
        if test_vault.exists():
            shutil.rmtree(test_vault)
        return None

def cleanup_test(test_vault_path):
    """清理测试环境"""
    if test_vault_path and Path(test_vault_path).exists():
        try:
            shutil.rmtree(test_vault_path)
            print(f"✅ 测试目录已清理: {test_vault_path}")
        except Exception as e:
            print(f"❌ 清理测试目录失败: {e}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        # 清理模式
        if len(sys.argv) > 2:
            cleanup_test(sys.argv[2])
        else:
            print("请提供要清理的测试目录路径")
    else:
        # 创建测试环境
        test_path = run_test()
        
        if test_path:
            print("\n" + "=" * 60)
            print("测试环境创建完成！")
            print("\n使用完毕后，可以运行以下命令清理:")
            print(f"python test_example.py cleanup \"{test_path}\"")
            print("=" * 60)