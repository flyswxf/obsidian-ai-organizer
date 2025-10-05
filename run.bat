@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo reOrganizeObsidian 图片整理工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 🔍 检查依赖包...
python -c "import yaml, tqdm, PIL" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  检测到缺少依赖包，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖包安装失败
        echo 请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo ✅ 依赖包安装完成
)

REM 运行程序
echo.
echo 🚀 启动程序...
echo.
python run.py

echo.
echo 按任意键退出...
pause >nul