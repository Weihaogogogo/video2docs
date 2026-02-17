# Video2Docs

**一款命令行工具（CLI），可将视频自动转换为结构化的 Markdown 或 PDF 文档，并智能嵌入关键帧截图。适用于多个场景**：
- 学习与知识管理：将 Bilibili 等平台的教学视频、讲座或讲解类内容一键转为图文并茂的预习/复习资料，便于检索、标注与长期沉淀；
- 新媒体运营：快速将视频核心内容提取为图文推文素材，高效实现跨平台内容分发与二次创作；
- 创作者竞品分析：对同行视频进行结构化解构，通过时间戳、关键画面与文本对照，深入分析其叙事逻辑、节奏设计与信息密度。

## 功能特性

### 核心功能

- **多平台视频下载**: 支持 B站、YouTube 等 1000+ 视频网站
- **语音转文字**: 支持 Whisper API 和本地 Whisper 模型两种方式
- **LLM 内容润色**: 将口语化转录转化为书面语教程文档
- **智能关键帧定位**: LLM 自动识别需要插入图片的位置
- **关键帧截取**: 使用 FFmpeg 按时间戳截取视频画面
- **多格式输出**: 同时生成 Markdown 和 PDF 文档

### 转换流程

整个转换过程包含 6 个阶段：

1. **视频下载** - 使用 yt-dlp 下载视频
2. **语音转文字** - 使用 Faster Whisper 将音频转为带时间戳的文字
3. **LLM 内容润色** - 将口语化转录转为书面语教程
4. **LLM 关键帧定位** - 确定需要插入图片的位置
5. **截取关键帧** - 使用 FFmpeg 按时间戳截取视频画面
6. **生成文档** - 生成 Markdown + PDF 文档

## 环境要求

- Python 3.10+
- FFmpeg (系统安装)
- 网络访问 (用于下载视频和调用 LLM API)

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd video2docs
```

### 2. 创建虚拟环境

```bash
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装 FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
下载 FFmpeg 并添加到系统 PATH。

### 5. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# LLM 配置（用于生成 Markdown 文档）
base_url=your_base_url
api_key=your_api_key
model=your_model_name

# Whisper 配置（用于语音转文字，独立于 LLM,可选填入）
whisper_base_url=your_base_url #(but insure to use model "whisper-1")
whisper_api_key=your_api_key
```

#### 配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `base_url` | LLM API 地址 | `https://api.openai.com/v1` 或其他兼容 API |
| `api_key` | LLM API 密钥 | 你的 API 密钥 |
| `model` | 使用的模型名称 | `gpt-4o`, `gemini-3-flash-preview` 等 |
| `whisper_base_url` | Whisper API 地址 | `https://api.openai.com/v1` |
| `whisper_api_key` | Whisper API 密钥 | 可以与 `api_key` 相同 |

## 使用方法

### 基本用法

```bash
python -m video2docs "https://www.bilibili.com/video/BVxxx"
```

或使用快速启动脚本，可启动后再输入视频链接（推荐）
```bash
./v2d.sh
```

### 命令行参数

```bash
python -m video2docs [URL] [OPTIONS]
```

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `URL` | 视频链接 | 无 (交互式输入) |
| `--base-dir` | 基础目录 | 当前目录 |
| `--model` | 使用的 LLM 模型 | .env 中的配置 |
| `--whisper` | 语音模式: `api` 或 `local` | 交互式选择 |

### 使用示例

```bash
# 基本用法
python -m video2docs "https://www.bilibili.com/video/BV1xx411c7mD"

# 最快速用法(推荐)
./v2d.sh

# 指定模型
python -m video2docs "https://www.bilibili.com/video/BVxxx" --model gpt-4o

# 使用本地 Whisper
python -m video2docs "https://www.bilibili.com/video/BVxxx" --whisper local

# 指定输出目录
python -m video2docs "https://www.bilibili.com/video/BVxxx" --base-dir /path/to/dir
```

## 交互式使用

运行不带参数的命令进入交互式模式：

```bash
./v2d.sh
```
或：
```bash
python -m video2docs
```

程序会提示：
1. 输入视频链接
2. 选择语音转文字方式 (Whisper API 或本地模型)
3. 自动执行完整转换流程

## 输出结果

转换完成后，在任务目录中生成以下文件：

```
task_X/
├── temp/
│   ├── video.mp4          # 下载的视频
│   └── transcript.json    # 转录结果
└── output/
    ├── *.md               # Markdown 文档
    ├── *.pdf              # PDF 文档
    └── images/            # 关键帧截图
        ├── 00_30.jpg
        ├── 01_45.jpg
        └── ...
```

## 语音转文字模式

### Whisper API 模式

- 使用 OpenAI Whisper API 进行转录
- 需要配置 `whisper_base_url` 和 `whisper_api_key`
- 转写质量高，识别精准
- 需要支付 API 费用

### 本地模型模式

- 使用本地 Faster Whisper 模型
- 首次使用需要下载约 150MB 的模型文件
- 无需 API 密钥，免费使用
- 质量略低于 API 模式

## 常见问题

### 1. 视频下载失败

- 检查网络连接
- 确保视频链接有效
- 某些视频可能需要登录才能下载

### 2. 语音转录失败

- 检查 FFmpeg 是否正确安装
- 确保视频包含音频轨道
- 尝试更换语音转文字模式

### 3. PDF 生成失败

- 确保 WeasyPrint 已正确安装: `pip install weasyprint`
- 检查图片路径是否正确

### 4. API 请求失败

- 检查 `.env` 配置是否正确
- 确认 API 密钥有效
- 检查网络连接

## 项目结构

```
video2docs/
├── video2docs/
│   ├── __init__.py          # 包初始化
│   ├── __main__.py          # 主入口
│   ├── cli.py               # CLI 命令行界面
│   ├── config.py            # 配置管理
│   ├── downloader.py        # 视频下载器
│   ├── transcriber.py       # 语音转文字
│   ├── frame_extractor.py   # 视频截帧
│   ├── llm_processor.py     # LLM 处理器
│   ├── prompts.py           # Prompt 模板
│   ├── markdown_generator.py# Markdown 生成器
│   └── pdf_generator.py     # PDF 生成器
├── .env                    # 环境配置
├── requirements.txt        # Python 依赖
└── README.md               # 项目说明
```

## 技术栈

- **CLI 框架**: Typer + Rich
- **视频下载**: yt-dlp
- **视频处理**: FFmpeg
- **语音转文字**: Faster Whisper / Whisper API
- **LLM 调用**: OpenAI SDK
- **PDF 生成**: WeasyPrint

## 许可证

MIT License
