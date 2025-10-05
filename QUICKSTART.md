# 快速开始指南

## 🚀 5分钟上手 reOrganizeObsidian

### 第一步：安装依赖

**方法1：使用批处理文件（Windows推荐）**
```bash
# 双击运行 run.bat 文件
# 它会自动检查并安装依赖
```

**方法2：手动安装**
```bash
pip install -r requirements.txt
```

### 第二步：创建测试环境（可选）

如果你想先测试工具功能，可以创建一个测试环境：

```bash
python test_example.py
```

这会创建一个包含示例文件的测试文件夹。

### 第三步：运行工具

**方法1：交互式运行（推荐新手）**
```bash
python run.py
```

**方法2：命令行运行**
```bash
# 预览模式（安全，推荐首次使用）
python main.py "C:\path\to\your\obsidian" --dry-run

# 不使用AI，直接整理
python main.py "C:\path\to\your\obsidian" --no-ai

# 使用AI功能
python main.py "C:\path\to\your\obsidian" --ai-key YOUR_API_KEY
```

### 第四步：查看结果

工具会显示处理结果，包括：
- 移动的文件数量
- 重命名的文件
- 任何错误信息

## ⚡ 常用场景

### 场景1：首次使用，想看看效果
```bash
python main.py "D:\MyObsidian" --dry-run
```

### 场景2：不想用AI，快速整理
```bash
python main.py "D:\MyObsidian" --no-ai
```

### 场景3：使用AI智能命名

**使用OpenAI：**
```bash
# 设置环境变量
set OPENAI_API_KEY=your_api_key
python main.py "D:\MyObsidian"

# 或者直接指定
python main.py "D:\MyObsidian" --ai-key your_api_key
```

**使用ECNU：**
```bash
# 设置环境变量
set ECNU_API_KEY=your_ecnu_api_key
python main.py "D:\MyObsidian" --ai-provider ecnu

# 或者使用密钥文件
python main.py "D:\MyObsidian" --ai-provider ecnu --ecnu-key-file "D:\path\to\ecnu.key"
```

**注意：**
- `ecnu-vl` 支持多模态理解，可进行图像分析
- `ecnu-max`、`ecnu-plus`、`ecnu-turbo` 仅支持文本分析

### 场景4：自定义配置
```bash
python main.py "D:\MyObsidian" --config my_config.yaml
```

## 🛡️ 安全提示

1. **首次使用必须加 `--dry-run`** - 这样可以预览结果而不实际移动文件
2. **工具会自动备份** - 但建议手动备份重要数据
3. **从小范围开始** - 可以先在一个小文件夹中测试

## 📋 检查清单

使用前请确认：
- [ ] Python 3.7+ 已安装
- [ ] 依赖包已安装 (`pip install -r requirements.txt`)
- [ ] Obsidian文件夹路径正确
- [ ] 已备份重要数据
- [ ] 首次使用加了 `--dry-run` 参数

## 🆘 遇到问题？

### 常见错误

**错误：找不到Python**
```
解决：安装Python 3.7+
下载：https://www.python.org/downloads/
```

**错误：缺少依赖包**
```bash
pip install -r requirements.txt
```

**错误：AI功能不工作**
```
检查：
1. API密钥是否正确
2. 网络连接是否正常
3. API余额是否充足
```

**错误：找不到图片文件**
```
检查：
1. 图片文件是否真的存在
2. 文件扩展名是否正确
3. 文件是否被其他程序占用
```

### 获取帮助

```bash
# 查看所有命令行选项
python main.py --help

# 查看详细文档
# 阅读 README.md
```

## 🎯 下一步

熟悉基本用法后，你可以：

1. **自定义配置** - 编辑 `config.yaml` 文件
2. **设置环境变量** - 避免每次输入API密钥
3. **批量处理** - 编写脚本处理多个文件夹
4. **集成工作流** - 将工具集成到你的笔记工作流中

---

**🎉 恭喜！你已经掌握了 reOrganizeObsidian 的基本用法！**

更多高级功能请参考 [README.md](README.md) 文档。