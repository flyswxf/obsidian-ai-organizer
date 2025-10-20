#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reOrganizeObsidian - Obsidian图片整理工具

功能：
1. 扫描Obsidian文件夹中的所有markdown文件
2. 找到文件中引用的图片
3. 将图片移动到对应笔记的文件夹中
4. 根据图片内容和上下文重命名图片（使用AI接口）
5. 更新markdown文件中的图片链接
"""

import os
import re
import shutil
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import argparse
from dataclasses import dataclass
from tqdm import tqdm

from config import config
from ai_service import ai_service

@dataclass
class ImageReference:
    """图片引用信息"""
    markdown_file: str  # markdown文件路径
    image_path: str     # 图片当前路径
    image_name: str     # 图片当前名称
    context: str        # 图片周围的上下文
    line_number: int    # 图片在文件中的行号

class ObsidianReorganizer:
    """Obsidian图片整理器"""
    
    def __init__(self, obsidian_root: str, ai_api_key: str = None):
        self.obsidian_root = Path(obsidian_root)
        self.ai_api_key = ai_api_key
        self.image_references: List[ImageReference] = []
        
        # 从配置获取支持的图片格式
        image_config = config.get_image_config()
        self.image_extensions = set(image_config.get('supported_formats', 
            ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp']))
        
        # 图片引用的正则表达式
        self.image_pattern = re.compile(r'!\[\[([^\]]+)\]\]|!\[([^\]]*)\]\(([^\)]+)\)')
        
        # 设置日志
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        log_config = config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO').upper())
        
        # 配置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 清除现有的处理器
        logging.getLogger().handlers.clear()
        
        # 设置根日志级别
        logging.getLogger().setLevel(level)
        
        # 控制台输出
        if log_config.get('console', True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)
        
        # 文件输出
        log_file = log_config.get('file')
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
    
    def create_backup(self):
        """创建备份"""
        try:
            org_config = config.get_organization_config()
            backup_suffix = org_config.get('backup_suffix', '_backup')
            
            backup_dir = self.obsidian_root.parent / f"{self.obsidian_root.name}{backup_suffix}"
            
            if backup_dir.exists():
                logging.warning(f"备份目录已存在: {backup_dir}")
                return
            
            logging.info(f"创建备份到: {backup_dir}")
            shutil.copytree(self.obsidian_root, backup_dir)
            logging.info("备份创建完成")
            
        except Exception as e:
            logging.error(f"创建备份失败: {e}")
        
    def scan_markdown_files(self) -> List[Path]:
        """扫描所有markdown文件"""
        markdown_files = []
        for file_path in self.obsidian_root.rglob('*.md'):
            markdown_files.append(file_path)
        return markdown_files
    
    def extract_image_references(self, markdown_file: Path) -> List[ImageReference]:
        """从markdown文件中提取图片引用"""
        references = []
        
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            lines = content.splitlines()
            
            for line_num, line in enumerate(lines, 1):
                matches = self.image_pattern.findall(line)
                for match in matches:
                    # 处理 ![[image]] 格式
                    if match[0]:
                        image_name = match[0]
                    # 处理 ![alt](path) 格式
                    elif match[2]:
                        image_name = match[2]
                    else:
                        continue
                    
                    # 使用全文上下文并标注图片在文件中的位置
                    position_info = f"图片位于第{line_num}行：{line.strip()}"
                    context = f"{content}\n\n[位置信息]\n{position_info}"
                    
                    # 查找图片文件
                    image_path = self.find_image_file(image_name)
                    if image_path:
                        ref = ImageReference(
                            markdown_file=str(markdown_file),
                            image_path=str(image_path),
                            image_name=image_name,
                            context=context,
                            line_number=line_num
                        )
                        references.append(ref)
        except Exception as e:
            logging.error(f"处理文件 {markdown_file} 时出错: {e}")
            
        return references
    
    def find_image_file(self, image_name: str) -> Optional[Path]:
        """在Obsidian文件夹中查找图片文件"""
        # 移除可能的扩展名
        base_name = Path(image_name).stem
        
        # 在根目录和所有子目录中搜索
        for ext in self.image_extensions:
            # 尝试完整名称
            for pattern in [image_name, f"{image_name}{ext}", f"{base_name}{ext}"]:
                for image_path in self.obsidian_root.rglob(pattern):
                    if image_path.is_file():
                        return image_path
        return None
    
    def get_context_around_image(self, content: str, image_line: str, window_size: int = 2) -> str:
        """获取图片周围的上下文"""
        lines = content.split('\n')
        image_line_idx = -1
        
        for i, line in enumerate(lines):
            if image_line.strip() in line:
                image_line_idx = i
                break
                
        if image_line_idx == -1:
            return ""
            
        start = max(0, image_line_idx - window_size)
        end = min(len(lines), image_line_idx + window_size + 1)
        
        return '\n'.join(lines[start:end])

    def extract_image_links(self, markdown_file: Path) -> List[Tuple[str, int]]:
        """提取markdown文件中的所有图片引用（不检查文件是否存在）"""
        links: List[Tuple[str, int]] = []
        try:
            with open(markdown_file, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
            for line_num, line in enumerate(lines, 1):
                matches = self.image_pattern.findall(line)
                for match in matches:
                    if match[0]:
                        links.append((match[0], line_num))
                    elif match[2]:
                        links.append((match[2], line_num))
        except Exception as e:
            logging.error(f"提取文件 {markdown_file} 的图片链接时出错: {e}")
        return links

    def audit_missing_images(self) -> List[Dict[str, Any]]:
        """审计所有markdown中的图片链接，记录缺失情况并写入日志"""
        missing: List[Dict[str, Any]] = []
        markdown_files = self.scan_markdown_files()
        log_path = Path('missing_images.log')

        for md_file in markdown_files:
            links = self.extract_image_links(md_file)
            for image_name, line_num in links:
                found = self.find_image_file(image_name)
                if not found:
                    missing.append({
                        'markdown_file': str(md_file),
                        'image_name': image_name,
                        'line_number': line_num
                    })
        try:
            from datetime import datetime
            with open(log_path, 'a', encoding='utf-8') as logf:
                logf.write(f"\n==== 缺失图片链接审计 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====\n")
                logf.write(f"Obsidian根目录: {self.obsidian_root}\n")
                logf.write(f"缺失数量: {len(missing)}\n")
                for item in missing:
                    logf.write(
                        f"- 缺失引用: '{item['image_name']}' | 来源: {item['markdown_file']} | 行: {item['line_number']}\n"
                    )
        except Exception as e:
            logging.error(f"写入审计日志失败: {e}")
        return missing
    
    def organize_images(self, dry_run: bool = False) -> Dict[str, str]:
        """整理图片到对应的文件夹"""
        results = {}
        
        # 扫描所有markdown文件
        markdown_files = self.scan_markdown_files()
        logging.info(f"找到 {len(markdown_files)} 个markdown文件")
        
        # 提取所有图片引用
        all_references = []
        for md_file in tqdm(markdown_files, desc="扫描markdown文件"):
            refs = self.extract_image_references(md_file)
            all_references.extend(refs)
            
        logging.info(f"找到 {len(all_references)} 个图片引用")
        
        # 创建备份（如果启用）
        org_config = config.get_organization_config()
        if org_config.get('create_backup', True) and not dry_run:
            self.create_backup()
        
        # 处理每个图片引用
        for ref in tqdm(all_references, desc="处理图片"):
            try:
                # 确定目标文件夹（markdown文件所在的文件夹）
                target_dir = Path(ref.markdown_file).parent
                
                # 生成新的图片名称（如果有AI接口）
                new_image_name = self.generate_new_image_name(ref)
                
                # 先获取扩展名
                image_ext = Path(ref.image_path).suffix

                # 若AI返回与原文件名一致，视为已符合标准，跳过重命名
                original_stem = Path(ref.image_path).stem
                # 仅当AI返回与当前文件名完全一致时，认为已符合标准并跳过重命名
                if new_image_name == original_stem:
                    same_name_target = target_dir / f"{original_stem}{image_ext}"
                    # 如果目标路径与当前路径相同，则无需移动
                    if Path(ref.image_path).absolute() == same_name_target.absolute():
                        logging.info(f"文件名已符合标准且位置正确，无需处理: {same_name_target}")
                        results[ref.image_path] = str(same_name_target)
                        # 不更新markdown引用（名称未变）
                        continue
                    # 若目标文件夹中已存在同名但不同文件，则走冲突重命名逻辑
                    if same_name_target.exists():
                        existing_names = [p.stem for p in target_dir.glob(f"*{image_ext}")]
                        hint = f"当前文件名已符合规范，但目标文件夹中已有同名文件。\n新名称必须与『{original_stem}』不同；同时避免与已有文件名：{', '.join(existing_names[:10])} 重复。请生成一个不同的中文名词短语。"
                        new_image_name = self.generate_new_image_name(ref, hint=hint)
                        new_image_path = target_dir / f"{new_image_name}{image_ext}"
                        # 后续冲突重试由下面逻辑处理（不立即continue）
                    else:
                        # 目标文件夹中无同名文件，直接按原名移动
                        if not dry_run:
                            shutil.move(ref.image_path, same_name_target)
                        logging.info(f"文件名已符合标准，按原名处理: {same_name_target.name}")
                        results[ref.image_path] = str(same_name_target)
                        # 不更新markdown引用（名称未变）
                        continue

                # 确定新的图片路径
                new_image_path = target_dir / f"{new_image_name}{image_ext}"
                
                # 若发生同名，优先让AI重新生成不同名称（最多重试3次）
                attempts = 0
                while new_image_path.exists() and attempts < 3:
                    existing_names = [p.stem for p in target_dir.glob(f"*{image_ext}")]
                    hint = f"新名称必须与『{new_image_name}』不同；同时避免与已有文件名：{', '.join(existing_names[:10])} 重复。请生成一个不同的中文名词短语。"
                    new_image_name = self.generate_new_image_name(ref, hint=hint)
                    new_image_path = target_dir / f"{new_image_name}{image_ext}"
                    attempts += 1
                
                # 如果仍然冲突，则添加数字后缀避免覆盖
                counter = 1
                while new_image_path.exists():
                    new_image_path = target_dir / f"{new_image_name}_{counter}{image_ext}"
                    counter += 1
                
                if not dry_run:
                    # 移动图片文件
                    shutil.move(ref.image_path, new_image_path)
                    
                    # 更新markdown文件中的引用
                    self.update_markdown_reference(ref, new_image_path.name)
                    
                results[ref.image_path] = str(new_image_path)
                logging.info(f"移动: {ref.image_path} -> {new_image_path}")
                
            except Exception as e:
                logging.error(f"处理图片 {ref.image_path} 时出错: {e}")
                results[ref.image_path] = f"ERROR: {e}"
                
        return results
    
    def generate_new_image_name(self, ref: ImageReference, hint: Optional[str] = None) -> str:
        """生成新的图片名称"""
        naming_config = config.get_naming_config()
        
        # 如果启用AI且AI服务可用
        if naming_config.get('use_ai', True) and ai_service.is_available():
            try:
                ai_name = ai_service.generate_image_name(ref.image_path, ref.context, extra_hint=hint)
                if ai_name:
                    logging.info(f"AI生成名称: {ai_name}")
                    return ai_name
            except Exception as e:
                logging.warning(f"AI命名失败，使用备用策略: {e}")
        
        # 使用备用命名策略
        fallback = naming_config.get('fallback_strategy', 'context_keywords')
        if fallback == 'context_keywords':
            return self.generate_simple_name(ref)
        elif fallback == 'file_name':
            return Path(ref.markdown_file).stem + '_image'
        else:  # timestamp
            import time
            return f"image_{int(time.time())}"
    
    def generate_simple_name(self, ref: ImageReference) -> str:
        """生成简单的图片名称（基于上下文关键词）"""
        # 从上下文中提取关键词
        context_words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', ref.context)
        
        # 过滤常见词汇
        stop_words = {'的', '是', '在', '有', '和', '与', '或', 'the', 'a', 'an', 'and', 'or', 'but'}
        keywords = [word for word in context_words if word.lower() not in stop_words and len(word) > 1]
        
        if keywords:
            # 取前3个关键词
            name_parts = keywords[:3]
            return '_'.join(name_parts)
        else:
            # 如果没有找到关键词，使用markdown文件名
            md_name = Path(ref.markdown_file).stem
            return f"{md_name}_image"
    
    def update_markdown_reference(self, ref: ImageReference, new_image_name: str):
        """更新markdown文件中的图片引用"""
        try:
            with open(ref.markdown_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换图片引用
            old_name = ref.image_name
            
            # 处理不同的引用格式
            patterns = [
                (f'![[{old_name}]]', f'![[{new_image_name}]]'),
                (f'![{old_name}]({old_name})', f'![{new_image_name}]({new_image_name})'),
                (f'![]({old_name})', f'![]({new_image_name})')
            ]
            
            for old_pattern, new_pattern in patterns:
                content = content.replace(old_pattern, new_pattern)
            
            with open(ref.markdown_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except Exception as e:
            logging.error(f"更新文件 {ref.markdown_file} 时出错: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Obsidian图片整理工具 - 自动整理和重命名Obsidian笔记中的图片',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py /path/to/obsidian --dry-run
  python main.py /path/to/obsidian --ai-key your_api_key
  python main.py /path/to/obsidian --config custom_config.yaml
        """
    )
    
    parser.add_argument('obsidian_path', help='Obsidian文件夹路径')
    parser.add_argument('--ai-key', help='AI API密钥（可选，也可通过环境变量OPENAI_API_KEY设置）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际移动文件')
    parser.add_argument('--config', help='自定义配置文件路径')
    parser.add_argument('--no-ai', action='store_true', help='禁用AI功能，仅使用基于上下文的命名')
    parser.add_argument('--no-backup', action='store_true', help='跳过备份创建')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='日志级别')
    parser.add_argument('--ai-provider', type=str, choices=['openai', 'claude', 'ecnu', 'local'],
                        help='指定AI服务提供商')
    parser.add_argument('--ecnu-key-file', type=str, help='ECNU API密钥文件路径')
    parser.add_argument('--audit-only', action='store_true', help='仅执行图片链接缺失检测，不移动文件')
    
    args = parser.parse_args()
    
    # 验证路径
    if not os.path.exists(args.obsidian_path):
        print(f"❌ 错误: 路径 {args.obsidian_path} 不存在")
        return 1
    
    if not os.path.isdir(args.obsidian_path):
        print(f"❌ 错误: {args.obsidian_path} 不是一个目录")
        return 1
    
    # 加载自定义配置
    if args.config:
        if os.path.exists(args.config):
            config.config_file = args.config
            config.config_data = config.load_config()
        else:
            print(f"⚠️  警告: 配置文件 {args.config} 不存在，使用默认配置")
    
    # 设置配置选项
    if args.ai_key:
        config.set('ai.api_key', args.ai_key)
    
    if args.no_ai:
        config.set('naming.use_ai', False)
    
    if args.no_backup:
        config.set('organization.create_backup', False)
    
    config.set('logging.level', args.log_level)
    
    if args.ai_provider:
        config.set('ai.provider', args.ai_provider)
    
    if args.ecnu_key_file:
        config.set('ai.ecnu_key_file', args.ecnu_key_file)
    
    # 创建整理器
    reorganizer = ObsidianReorganizer(args.obsidian_path, args.ai_key)
    
    # 显示配置信息
    print(f"🚀 开始整理Obsidian文件夹: {args.obsidian_path}")
    if args.dry_run:
        print("🔍 预览模式 - 不会实际移动文件")
    
    if config.get('naming.use_ai', True) and ai_service.is_available():
        print(f"🤖 AI服务已启用 - 模型: {config.get('ai.model')}")
    else:
        print("📝 使用基于上下文的命名策略")
    
    if config.get('organization.create_backup', True) and not args.dry_run:
        print("💾 将创建备份")
    
    print("\n" + "="*50)
    
    # 审计模式：仅检测缺失图片链接
    if args.audit_only:
        missing = reorganizer.audit_missing_images()
        print(f"\n🔎 图片链接缺失数量: {len(missing)}")
        print("📝 详情已写入: missing_images.log")
        return 0
    
    try:
        # 执行整理
        results = reorganizer.organize_images(dry_run=args.dry_run)
        
        # 统计结果
        success_count = sum(1 for v in results.values() if not v.startswith('ERROR:'))
        error_count = len(results) - success_count
        
        print("\n" + "="*50)
        print(f"✅ 整理完成!")
        print(f"📊 处理统计:")
        print(f"   - 成功处理: {success_count} 个图片")
        if error_count > 0:
            print(f"   - 处理失败: {error_count} 个图片")
        
        if args.dry_run and results:
            print("\n🔍 预览结果:")
            for old_path, new_path in results.items():
                if new_path.startswith('ERROR:'):
                    print(f"   ❌ {old_path} -> {new_path}")
                else:
                    print(f"   ✅ {old_path} -> {new_path}")
        
        # 显示错误详情
        if error_count > 0 and not args.dry_run:
            print("\n❌ 处理失败的文件:")
            for old_path, result in results.items():
                if result.startswith('ERROR:'):
                    print(f"   {old_path}: {result}")
        
        # 运行完成后自动执行链接缺失审计
        missing = reorganizer.audit_missing_images()
        print(f"\n🔎 图片链接缺失数量: {len(missing)}")
        print("📝 详情已写入: missing_images.log")
        
        return 0 if error_count == 0 else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
        return 1
    except Exception as e:
        logging.error(f"程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())