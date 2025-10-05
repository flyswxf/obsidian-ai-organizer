# reOrganizeObsidian

一个强大的Obsidian图片整理工具，能够自动整理和重命名Obsidian笔记中的图片文件。

## 功能特性

### 🎯 核心功能
- **自动图片整理**: 将分散的图片文件移动到使用它们的笔记文件夹中
- **智能重命名**: 使用AI分析图片内容和上下文，生成有意义的文件名
- **多种命名策略**: 支持AI命名、上下文关键词、文件名等多种策略
- **安全备份**: 自动创建备份，确保数据安全
- **预览模式**: 支持dry-run模式，预览操作结果

### 🤖 AI功能
- 支持OpenAI GPT-4 Vision等AI模型
- 分析图片内容和周围文本上下文
- 生成简洁、描述性的文件名
- 支持中英文命名

### 📁 文件处理
- 支持多种图片格式：PNG, JPG, JPEG, GIF, BMP, SVG, WebP
- 自动处理Obsidian的两种图片引用格式：`![[image]]` 和 `![alt](image)`
- 智能避免文件名冲突
- 自动更新markdown文件中的图片链接

## 安装和使用

### 环境要求
- Python 3.7+
- Windows/macOS/Linux

### 安装依赖
```bash
pip install -r requirements.txt
```

### 基本使用

#### 1. 预览模式（推荐首次使用）
```bash
python main.py /path/to/your/obsidian/vault --dry-run
```

#### 2. 使用AI功能
```bash
# 通过命令行参数提供API密钥
python main.py /path/to/your/obsidian/vault --ai-key your_openai_api_key

# 或者设置环境变量
export OPENAI_API_KEY=your_openai_api_key
python main.py /path/to/your/obsidian/vault
```

#### 3. 不使用AI功能
```bash
python main.py /path/to/your/obsidian/vault --no-ai
```

#### 4. 自定义配置
```bash
python main.py /path/to/your/obsidian/vault --config custom_config.yaml
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `obsidian_path` | Obsidian文件夹路径（必需） |
| `--dry-run` | 预览模式，不实际移动文件 |
| `--ai-key` | AI API密钥 |
| `--no-ai` | 禁用AI功能 |
| `--no-backup` | 跳过备份创建 |
| `--config` | 自定义配置文件路径 |
| `--log-level` | 日志级别（DEBUG/INFO/WARNING/ERROR） |

## 配置文件

工具使用YAML格式的配置文件，支持以下配置项：

### AI配置

支持多种AI服务提供商：

- **OpenAI**: 使用 GPT-4 Vision 进行图像分析
- **Claude**: Anthropic 的 Claude 模型
- **ECNU**: 华东师范大学开发者平台的AI模型
- **Local**: 本地AI服务（需要自行搭建）

#### OpenAI 配置示例：
```yaml
ai:
  provider: openai
  api_key: 'your-api-key'
  model: gpt-4-vision-preview
  max_tokens: 150
  temperature: 0.3
```

#### ECNU 配置示例：
```yaml
ai:
  provider: ecnu
  api_key: ''  # 可留空，会自动从文件读取
  model: ecnu-vl  # 或 ecnu-max, ecnu-plus, ecnu-turbo
  ecnu_key_file: 'D:\path\to\your\ecnu.key'
  max_tokens: 150
  temperature: 0.3
```

**ECNU 特殊说明：**
- `ecnu-vl`: 支持多模态理解的对话模型，可进行图像分析
- `ecnu-max`、`ecnu-plus`、`ecnu-turbo`: 仅支持文本分析，会根据上下文生成图片名称
- API密钥可以通过环境变量 `ECNU_API_KEY` 设置，或在配置文件中指定密钥文件路径

### 命名策略
```yaml
naming:
  max_length: 50  # 文件名最大长度
  use_ai: true  # 是否使用AI命名
  fallback_strategy: context_keywords  # 备用策略
  remove_special_chars: true  # 移除特殊字符
  replace_spaces: '_'  # 空格替换字符
```

### 文件整理
```yaml
organization:
  create_backup: true  # 是否创建备份
  backup_suffix: '_backup'  # 备份文件夹后缀
  skip_existing: true  # 跳过已存在的文件
  update_links: true  # 更新markdown中的链接
```

完整的配置示例请参考 `config.yaml` 文件。

## 使用场景

### 问题场景
在使用Obsidian记笔记时，经常遇到以下问题：

1. **图片路径混乱**: 截图粘贴的图片都保存在根目录，路径如 `D:\Obsidian\Pasted image 20250611204755.png`，但使用该图片的笔记可能在 `D:\Obsidian\编程\UML\类图\` 文件夹中

2. **文件名无意义**: 所有图片都是 "Pasted image + 数字" 的格式，无法反映图片的实际内容

3. **分享困难**: 由于图片分散在各处，很难将笔记完整地分享给他人

### 解决方案

使用 reOrganizeObsidian 工具后：

1. **图片就近存放**: 图片会被移动到使用它们的笔记文件夹中
2. **智能命名**: 根据图片内容和上下文生成有意义的文件名
3. **链接自动更新**: markdown文件中的图片链接会自动更新
4. **便于分享**: 每个文件夹都是自包含的，可以独立分享

### 示例

**整理前**:
```
D:\Obsidian\
├── Pasted image 20250611204755.png  # UML类图
├── Pasted image 20250611205123.png  # 代码截图
└── 编程\
    └── UML\
        └── 类图\
            └── 面向对象设计.md  # 引用了上面的图片
```

**整理后**:
```
D:\Obsidian\
└── 编程\
    └── UML\
        └── 类图\
            ├── 面向对象设计.md
            ├── UML类图_继承关系.png
            └── Java代码_类定义.png
```

## 安全性

- **自动备份**: 默认在操作前创建完整备份
- **预览模式**: 支持dry-run模式，可以先预览操作结果
- **错误处理**: 完善的错误处理和日志记录
- **可逆操作**: 保留原始备份，操作可逆

## 注意事项

1. **首次使用建议**: 第一次使用时建议先用 `--dry-run` 参数预览结果
2. **备份重要性**: 虽然工具会自动备份，但建议手动备份重要数据
3. **AI API费用**: 使用AI功能需要消耗API调用费用
4. **网络要求**: AI功能需要网络连接

## 故障排除

### 常见问题

**Q: AI功能不工作**
A: 检查API密钥是否正确设置，网络连接是否正常

**Q: 图片没有被找到**
A: 确保图片文件确实存在于Obsidian文件夹中，检查文件扩展名

**Q: 文件名包含特殊字符**
A: 工具会自动清理特殊字符，可以在配置文件中调整清理规则

**Q: 备份占用空间太大**
A: 可以使用 `--no-backup` 参数跳过备份，但不推荐

### 日志查看

工具会生成详细的日志文件 `reorganize.log`，包含：
- 处理过程详情
- 错误信息
- 性能统计

## 开发和贡献

### 项目结构
```
reOrganizeObsidian/
├── main.py          # 主程序
├── config.py        # 配置管理
├── ai_service.py    # AI服务
├── config.yaml      # 配置文件
├── requirements.txt # 依赖列表
└── README.md        # 说明文档
```

### 扩展功能

工具设计为模块化架构，可以轻松扩展：
- 添加新的AI服务提供商
- 支持更多图片格式
- 添加新的命名策略
- 集成其他笔记软件

## 许可证

本项目采用 MIT 许可证。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的图片整理功能
- 集成OpenAI GPT-4 Vision
- 支持多种命名策略
- 完善的配置系统