#!/bin/bash

# Video2Docs 快速安装脚本
# 会在当前目录创建 venv 虚拟环境并安装依赖

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "       Video2Docs 安装脚本"
echo "========================================"

# ========== ffmpeg 安装 ==========
echo "[0/4] 检查 ffmpeg 安装状态..."

if command -v ffmpeg &> /dev/null; then
    echo "[OK] ffmpeg 已安装: $(ffmpeg -version | head -n1)"
else
    echo "[INFO] ffmpeg 未安装，正在尝试自动安装..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo "[ERROR] Homebrew 未安装，请先安装 Homebrew: https://brew.sh"
            echo "或者手动安装 ffmpeg: brew install ffmpeg"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install ffmpeg
        elif command -v yum &> /dev/null; then
            sudo yum install ffmpeg
        else
            echo "[ERROR] 无法自动安装 ffmpeg，请手动安装"
            exit 1
        fi
    else
        echo "[ERROR] Windows 系统请手动安装 ffmpeg:"
        echo "  方法1: 运行 'winget install ffmpeg'"
        echo "  方法2: 从 https://ffmpeg.org/download.html 下载"
        exit 1
    fi
fi

# 检测 venv 是否已创建
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "[INFO] 检测到已存在的 venv 虚拟环境，跳过创建步骤"
else
    echo "[1/4] 创建虚拟环境 venv ..."
    python3 -m venv venv
    echo "[OK] 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "[2/4] 激活虚拟环境并安装依赖..."
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

echo "[OK] 依赖安装完成"

# 验证安装
echo "[3/4] 验证 Python 依赖..."
python -c "import typer, rich, ytdlp, ffmpeg, openai, jinja2, dotenv, pydantic_settings, faster_whisper, weasyprint, markdown; print('[OK] Python 依赖验证通过')" 2>/dev/null || echo "[WARNING] 部分依赖验证失败，请手动检查"

echo "[4/4] 验证 ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "[OK] ffmpeg 验证通过"
else
    echo "[WARNING] ffmpeg 验证失败"
fi

echo ""
echo "========================================"
echo "       安装完成!"
echo "========================================"
echo ""
echo "使用方法:"
echo "确保目录中.env文件正确配置了base_url与api_key，之后可以使用以下命令启动程序："
echo ""
echo "  ./v2d.sh                    # 使用快捷脚本（推荐）"
echo "  python -m video2docs        # 或运行python程序"
