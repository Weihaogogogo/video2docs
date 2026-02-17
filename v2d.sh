#!/bin/bash

# Video2Docs 启动脚本

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行: python3 -m venv venv"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖是否安装
if ! python -c "import typer" 2>/dev/null; then
    echo "📦 安装依赖中..."
    pip install typer rich yt-dlp ffmpeg-python openai jinja2 python-dotenv pydantic-settings
fi

# 启动程序
echo "🚀 启动 Video2Docs..."
python -m video2docs
