# Video2Docs 项目

将B站视频转换为带截图的Markdown教程文档。

## 项目概述

Video2Docs 是一个命令行工具，可以将B站视频自动转换为图文并茂的Markdown教程文档。整个转换过程包含6个阶段：

1. **视频下载** - 使用yt-dlp下载B站视频
2. **语音转文字** - 使用Faster Whisper将音频转为带时间戳的文字
3. **LLM内容润色** - 第一次LLM调用，将口语化转录转为书面语教程
4. **LLM关键帧定位** - 第二次LLM调用，确定需要插入图片的位置
5. **截取关键帧** - 使用FFmpeg按时间戳截取视频画面
6. **生成Markdown** - 生成最终的Markdown文档

## 项目结构

```
video2docs/
├── video2docs/
│   ├── __init__.py          # 包初始化
│   ├── __main__.py          # 主入口
│   ├── main.py              # 主程序
│   ├── cli.py               # CLI命令行界面
│   ├── config.py            # 配置管理
│   ├── downloader.py        # 视频下载器
│   ├── transcriber.py      # 语音转文字
│   ├── frame_extractor.py  # 视频截帧
│   ├── llm_processor.py   # LLM处理器
│   ├── prompts.py           # Prompt模板
│   └── markdown_generator.py# Markdown生成器
├── .env                    # 环境配置（需用户创建）
├── requirements.txt        # Python依赖
└── README.md               # 项目说明
```

## 环境配置

在项目根目录创建 `.env` 文件：

```bash
base_url=your_api_base_url    # API地址，如 https://api.openai.com/v1
api_key=your_api_key          # API密钥
model=your_model_name         # 模型名称，如 gpt-4o, gemini-3-flash-preview
```

## 使用方法

### 激活虚拟环境

```bash
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 运行转换

```bash
python -m video2docs "https://www.bilibili.com/video/BVxxx"
```

### 参数说明

- `url` (必需): B站视频链接
- `--temp-dir`: 临时文件目录（默认: ./temp）
- `--output-dir`: 输出目录（默认: ./output）

## 技术栈

- **CLI框架**: Typer + Rich
- **视频下载**: yt-dlp
- **视频处理**: FFmpeg + ffmpeg-python
- **语音转文字**: Faster Whisper
- **LLM调用**: OpenAI SDK
- **模板引擎**: Jinja2

## 依赖安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install typer rich yt-dlp ffmpeg-python faster-whisper openai jinja2 python-dotenv pydantic-settings
```

## 系统要求

- Python 3.10+
- FFmpeg
- 网络访问（用于下载视频和调用LLM API）

## 注意事项

1. 确保 `.env` 文件配置正确
2. 首次运行需要下载Whisper模型（约140MB）
3. 整个转换过程取决于视频长度和网络状况
4. 生成的Markdown文档和图片保存在 `./output` 目录
