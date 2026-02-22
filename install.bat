@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo        Video2Docs 安装脚本 (Windows)
echo ========================================

echo.
echo [0/4] 检查 ffmpeg 安装状态...

where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] ffmpeg 已安装
) else (
    echo [INFO] ffmpeg 未安装，正在尝试自动安装...
    where winget >nul 2>&1
    if %errorlevel% equ 0 (
        winget install ffmpeg
    ) else (
        echo [ERROR] 未检测到 winget，请手动安装 ffmpeg:
        echo   方法1: 运行 'winget install ffmpeg'
        echo   方法2: 从 https://ffmpeg.org/download.html 下载
        exit /b 1
    )
)

echo.
echo [1/4] 检查虚拟环境 venv ...

if exist "venv\Scripts\activate.bat" (
    echo [INFO] 检测到已存在的 venv 虚拟环境，跳过创建步骤
) else (
    echo [1/4] 创建虚拟环境 venv ...
    python -m venv venv
    echo [OK] 虚拟环境创建完成
)

echo.
echo [2/4] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat

echo.
echo 升级 pip...
python -m pip install --upgrade pip

echo.
echo 安装依赖...
pip install -r requirements.txt

echo.
echo [OK] 依赖安装完成

echo.
echo [3/4] 验证 Python 依赖...
python -c "import typer, rich, ytdlp, ffmpeg, openai, jinja2, dotenv, pydantic_settings, faster_whisper, weasyprint, markdown" 2>nul
if %errorlevel% equ 0 (
    echo [OK] Python 依赖验证通过
) else (
    echo [WARNING] 部分依赖验证失败，请手动检查
)

echo.
echo [4/4] 验证 ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] ffmpeg 验证通过
) else (
    echo [WARNING] ffmpeg 验证失败
)

echo.
echo ========================================
echo        安装完成!
echo ========================================
echo.
echo 使用方法:
echo 确保目录中 .env 文件正确配置了 base_url 与 api_key，之后可以使用以下命令启动程序：
echo.
echo   venv\Scripts\activate.bat     # 激活虚拟环境
echo   python -m video2docs            # 运行程序
echo.
