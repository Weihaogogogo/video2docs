#!/bin/bash

# Video2Docs 快速安装脚本
# 会在当前目录创建 .venv 虚拟环境并安装依赖

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 调试：打印当前目录，确保在项目根目录
echo "[DEBUG] 当前工作目录: $(pwd)"
echo "[DEBUG] venv 存在检查: $([ -d "venv" ] && echo '是' || echo '否')"

echo "========================================"
echo "       Video2Docs 安装脚本"
echo "========================================"

# 检测 venv 是否已创建
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    echo "[INFO] 检测到已存在的 venv 虚拟环境，跳过创建步骤"
else
    echo "[1/3] 创建虚拟环境 venv ..."
    python3 -m venv venv
    echo "[OK] 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "[2/3] 激活虚拟环境并安装依赖..."
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

echo "[OK] 依赖安装完成"

# 验证安装
echo "[3/3] 验证安装..."
python -c "import typer, rich, ytdlp, ffmpeg, openai, jinja2, dotenv, pydantic_settings, faster_whisper, weasyprint, markdown; print('[OK] 所有依赖验证通过')" 2>/dev/null || echo "[WARNING] 部分依赖验证失败，请手动检查"

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
