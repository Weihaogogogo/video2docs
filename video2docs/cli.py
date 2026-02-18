"""CLI入口模块 - 命令行界面"""
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
import json

app = typer.Typer(
    name="video2docs",
    help="视频转Markdown/PDF文档工具",
    add_completion=False
)
console = Console()


def get_next_task_id(base_dir: Path = Path(".")) -> int:
    """获取下一个任务ID"""
    task_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith("task_")]
    if not task_dirs:
        return 1
    ids = [int(d.name.split("_")[1]) for d in task_dirs if d.name.split("_")[1].isdigit()]
    return max(ids) + 1 if ids else 1


def create_task_folder(base_dir: Path = Path(".")) -> Path:
    """创建任务文件夹"""
    task_id = get_next_task_id(base_dir)
    task_dir = base_dir / f"task_{task_id}"
    task_dir.mkdir(parents=True, exist_ok=True)

    # 创建 temp 和 output 子目录
    (task_dir / "temp").mkdir(exist_ok=True)
    (task_dir / "output").mkdir(exist_ok=True)

    return task_dir


def show_welcome():
    """显示欢迎界面"""
    console.clear()
    console.print(Panel.fit(
        """
[bold cyan]Video2Docs[/bold cyan] - 视频转文档工具

[yellow]功能：[/yellow]
  - 支持多平台视频下载（B站、YouTube等）
  - 语音转文字（Whisper API / 本地模型）
  - LLM内容润色
  - 智能关键帧定位
  - 生成 Markdown + PDF 文档

[yellow]使用方式：[/yellow]
  1. 选择语音转文字方式
  2. 输入视频链接
  3. 等待自动转换完成
  4. 在任务目录查看结果
        """,
        title="欢迎使用 Video2Docs",
        border_style="cyan"
    ))
    console.print()


def select_whisper_mode() -> str:
    """让用户选择 Whisper 模式"""
    console.print("\n[bold]请选择语音转文字方式：[/bold]\n")

    # 显示选项
    console.print("  [1] Whisper API (推荐)")
    console.print("      [+] 转写质量高，识别精准")
    console.print("      [!] 需要 API 密钥 (OpenAI 或兼容中转站)\n")

    console.print("  [2] 本地 Whisper 模型")
    console.print("      [+] 无需 API 密钥，已预置在项目中")
    console.print("      [!] 质量略低于 API\n")

    choice = Prompt.ask(
        "请选择 [1/2]",
        default="1"
    )

    # 返回模式
    if choice == "2":
        return "local"
    return "api"


def run_conversion(
    url: str,
    base_path: Path,
    model: str,
    whisper_mode: str,
    transcriber=None
):
    """
    执行转换流程

    Args:
        url: 视频链接
        base_path: 基础路径
        model: LLM 模型
        whisper_mode: Whisper 模式
        transcriber: 可选的转录器实例（用于复用）

    Returns:
        (success: bool, transcriber: Transcriber or None)
    """
    from .config import get_settings
    from .downloader import VideoDownloader
    from .transcriber import Transcriber
    from .frame_extractor import FrameExtractor
    from .llm_processor import LLMProcessor
    from .markdown_generator import MarkdownGenerator
    from .pdf_generator import PDFGenerator
    from openai import OpenAI

    # 加载配置
    settings = get_settings()

    # 检查 LLM 配置
    if not settings.is_configured:
        console.print("[red]错误: 请先配置 .env 文件[/red]")
        console.print("""
请创建 .env 文件，内容如下：
base_url=your_api_base_url
api_key=your_api_key
model=your_model_name
        """)
        return False, transcriber

    # 如果选择 API 模式但未配置，返回错误
    if whisper_mode == "api" and not settings.is_whisper_api_configured:
        console.print("[red]Whisper API 模式需要配置 whisper_base_url 和 whisper_api_key[/red]")
        console.print("请在 .env 中添加：")
        console.print("whisper_base_url=https://api.openai.com/v1")
        console.print("whisper_api_key=your_api_key")
        console.print("或选择本地模式 [2]")
        return False, transcriber

    # 使用命令行参数覆盖配置
    if model:
        settings.llm_model = model

    # 创建任务文件夹
    task_dir = create_task_folder(base_path)
    temp_path = task_dir / "temp"
    output_path = task_dir / "output"

    try:
        # 显示任务信息
        console.print(f"\n[bold]任务信息[/bold]")
        console.print(f"   模型: {settings.llm_model}")
        console.print(f"   语音: {'Whisper API' if whisper_mode == 'api' else '本地模型'}")
        console.print(f"   链接: {url[:50]}...")
        console.print(f"   目录: {task_dir}\n")

        # 阶段1: 下载视频
        console.print("[bold cyan]阶段 1/6: 下载视频[/bold cyan]")
        downloader = VideoDownloader(temp_path)
        video_info = downloader.get_video_info(url)
        if not video_info:
            console.print("[red]获取视频信息失败[/red]")
            return False, transcriber

        video_path = downloader.download(url)
        if not video_path:
            console.print("[red]视频下载失败[/red]")
            return False, transcriber

        console.print(f"   [OK] 下载完成: {video_path.name}\n")

        # 阶段2: 语音转文字
        mode_display = "Whisper API" if whisper_mode == "api" else "本地模型"
        console.print(f"[bold cyan]阶段 2/6: 语音转文字 ({mode_display})[/bold cyan]")

        # 如果没有传入 transcriber，则创建新的
        if transcriber is None:
            if whisper_mode == "api":
                # 创建 OpenAI 客户端
                llm_client = OpenAI(
                    base_url=settings.whisper_base_url,
                    api_key=settings.whisper_api_key
                )
                transcriber = Transcriber(
                    mode="api",
                    llm_client=llm_client
                )
            else:
                # 本地模式
                transcriber = Transcriber(mode="local")

        segments = transcriber.transcribe(video_path)
        if not segments:
            console.print("[red]转录失败[/red]")
            return False, transcriber

        # 合并零散片段
        merged_segments = transcriber.merge_segments_by_rule(
            segments,
            min_duration=8.0,
            max_duration=20.0,
            merge_gap=0.5
        )
        console.print(f"   [OK] 转录完成 ({len(segments)} -> {len(merged_segments)} 片段)\n")

        # 使用合并后的片段
        process_segments = merged_segments

        # 保存转录结果
        transcript_file = temp_path / "transcript.json"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            json.dump([s.to_dict() for s in process_segments], f, ensure_ascii=False, indent=2)

        # 阶段3: LLM内容润色
        console.print("[bold cyan]阶段 3/6: LLM 内容润色[/bold cyan]")
        llm_processor = LLMProcessor(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model
        )

        video_intro = llm_processor.get_video_intro(video_info)
        polished_content = llm_processor.polish_content(process_segments)
        console.print("   [OK] 视频介绍 + 内容润色完成\n")

        # 阶段4: LLM关键帧定位
        console.print("[bold cyan]阶段 4/6: 关键帧定位[/bold cyan]")
        marked_content, image_plans = llm_processor.add_image_markers(
            process_segments, polished_content
        )
        console.print(f"   [OK] 定位完成 ({len(image_plans)} 张图片)\n")

        # 阶段5: 截取关键帧
        console.print("[bold cyan]阶段 5/6: 截取关键帧[/bold cyan]")
        frame_extractor = FrameExtractor(output_path / "images")

        timestamps = [plan.timestamp for plan in image_plans]
        frame_mapping = frame_extractor.extract_frames(video_path, timestamps)

        if not frame_mapping:
            console.print("   [!] 没有成功截取图片\n")
        else:
            console.print(f"   [OK] 截取完成 ({len(frame_mapping)}/{len(image_plans)})\n")

        # 阶段6: 生成文档
        console.print("[bold cyan]阶段 6/6: 生成文档[/bold cyan]")
        md_generator = MarkdownGenerator(output_path)

        output_file = md_generator.generate(
            title=video_info.get('title', '视频文档'),
            video_intro=video_intro,
            content=marked_content,
            video_info=video_info,
            frame_mapping=frame_mapping
        )

        # 生成 PDF
        pdf_generator = PDFGenerator(output_path)
        pdf_file = pdf_generator.generate(output_file)

        console.print("   [OK] Markdown + PDF 生成完成\n")

        # 显示结果
        console.print("[bold green]转换完成![/bold green]\n")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("项目")
        table.add_column("值")
        table.add_row("任务目录", str(task_dir))
        table.add_row("Markdown", str(output_file))
        table.add_row("PDF", str(pdf_file) if pdf_file else "生成失败")
        table.add_row("图片", f"{len(frame_mapping)}/{len(image_plans)} 张")

        console.print(table)

        return True, transcriber

    except KeyboardInterrupt:
        console.print("\n[yellow]用户中断操作[/yellow]")
        return False, transcriber
    except Exception as e:
        console.print(f"\n[red]错误: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return False, transcriber


@app.command()
def main(
    url: str = typer.Argument(None, help="视频链接"),
    base_dir: str = typer.Option(".", help="基础目录"),
    model: Optional[str] = typer.Option(None, help="使用的模型"),
    whisper: Optional[str] = typer.Option(None, help="语音模式: api 或 local"),
):
    """
    将视频转换为 Markdown/PDF 文档
    """
    from .transcriber import clear_model_cache

    base_path = Path(base_dir)

    # 如果没有提供URL，显示交互式界面
    if url is None:
        show_welcome()
        # 进入连续处理模式
        run_interactive_mode(base_path, model)
    else:
        # 单次执行模式
        # 先选择 whisper 模式
        whisper_mode = whisper if whisper else select_whisper_mode()

        success, _ = run_conversion(url, base_path, model, whisper_mode)

        if success:
            console.print("\n[bold green]按回车键退出...[/bold green]")
            input()
        else:
            console.print("\n[bold red]转换失败，请检查错误信息[/bold red]")
            raise typer.Exit(1)

    # 退出时清理模型缓存
    clear_model_cache()


def run_interactive_mode(base_path: Path, model: Optional[str] = None):
    """
    交互式连续处理模式

    支持：
    - 连续处理多个视频
    - 失败时询问是否重试
    - Whisper 模式沿用上次选择
    """
    # 第一次需要选择 whisper 模式
    whisper_mode = select_whisper_mode()
    transcriber = None  # 用于复用

    while True:
        console.print()
        url = Prompt.ask(
            "[bold cyan]请输入视频链接 (输入 n 退出)[/bold cyan]",
            default="",
            show_default=False
        )

        # 检查退出
        if not url or url.lower() in ['q', 'quit', 'exit', '退出', 'n']:
            console.print("\n[yellow]感谢使用，再见！[/yellow]")
            break

        # 执行转换（支持重试）
        success, transcriber = run_conversion_with_retry(
            url, base_path, model, whisper_mode, transcriber
        )

        if success:
            # 询问是否继续
            console.print()
            continue_prompt = Prompt.ask(
                "[bold]是否继续处理下一个视频? (y\/n)[/bold]",
                default="y"
            )

            if continue_prompt.lower() == 'n':
                console.print("\n[yellow]感谢使用，再见！[/yellow]")
                break
        else:
            # 失败后询问是否重试或退出
            console.print()
            retry_prompt = Prompt.ask(
                "[bold yellow]是否重新输入链接重试? (y\/n)[/bold yellow]",
                default="y"
            )

            if retry_prompt.lower() not in ['y', 'yes', '是', '']:
                console.print("\n[yellow]感谢使用，再见！[/yellow]")
                break
            # 否则继续循环，让用户输入新的链接


def run_conversion_with_retry(
    url: str,
    base_path: Path,
    model: str,
    whisper_mode: str,
    transcriber=None,
    max_retries: int = 3
):
    """
    带重试机制的转换执行

    Args:
        url: 视频链接
        base_path: 基础路径
        model: LLM 模型
        whisper_mode: Whisper 模式
        transcriber: 转录器实例
        max_retries: 最大重试次数

    Returns:
        (success: bool, transcriber: Transcriber or None)
    """
    attempt = 1

    while attempt <= max_retries:
        success, transcriber = run_conversion(
            url, base_path, model, whisper_mode, transcriber
        )

        if success:
            return True, transcriber

        # 失败，询问是否重试
        if attempt < max_retries:
            console.print(f"\n[yellow]第 {attempt} 次尝试失败[/yellow]")
            retry = Prompt.ask(
                f"是否重试? (剩余 {max_retries - attempt} 次) [y/n]",
                default="y"
            )

            if retry.lower() not in ['y', 'yes', '是', '']:
                return False, transcriber

            attempt += 1
        else:
            console.print("\n[red]已达到最大重试次数，转换失败[/red]")
            return False, transcriber

    return False, transcriber


if __name__ == "__main__":
    app()
