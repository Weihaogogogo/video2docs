"""视频截帧模块 - 按时间戳截取视频帧"""
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console

console = Console()


class FrameExtractor:
    """视频截帧器"""

    def __init__(self, output_dir: Path):
        """
        初始化截帧器

        Args:
            output_dir: 图片输出目录
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_frame(self, video_path: Path, timestamp: str, output_name: str) -> Optional[Path]:
        """
        截取单帧

        Args:
            video_path: 视频文件路径
            timestamp: 时间戳 (MM:SS 或 HH:MM:SS)
            output_name: 输出文件名（不含扩展名）

        Returns:
            生成的图片路径，失败返回None
        """
        output_path = self.output_dir / f"{output_name}.jpg"

        # 使用FFmpeg截帧
        # -ss 指定时间戳
        # -vframes 1 只截取1帧
        # -q:v 2 输出质量（2是高质量）
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖已存在的文件
            "-ss", timestamp,
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            "-vf", "scale=1280:-1",  # 限制宽度，保持比例
            str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and output_path.exists():
                return output_path
            else:
                console.print(f"[yellow]截帧失败 ({timestamp}): {result.stderr}[/yellow]")
                return None

        except subprocess.TimeoutExpired:
            console.print(f"[red]截帧超时: {timestamp}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]截帧异常: {str(e)}[/red]")
            return None

    def extract_frames(self, video_path: Path, timestamps: List[str]) -> Dict[str, Path]:
        """
        批量截取多帧

        Args:
            video_path: 视频文件路径
            timestamps: 时间戳列表

        Returns:
            时间戳到图片路径的字典
        """
        results: Dict[str, Path] = {}
        total = len(timestamps)

        console.print(f"[cyan]开始截取 {total} 张图片...[/cyan]")

        for i, timestamp in enumerate(timestamps, 1):
            # 使用时间戳作为文件名 (如 01_30.jpg)，保持与LLM输出的一致性
            # 替换冒号为下划线，使其成为有效的文件名
            output_name = timestamp.replace(":", "_")
            frame_path = self.extract_frame(video_path, timestamp, output_name)

            if frame_path:
                results[timestamp] = frame_path
                console.print(f"  [{i}/{total}] {timestamp} -> {frame_path.name}")
            else:
                console.print(f"  [{i}/{total}] [red]截取失败: {timestamp}[/red]")

        console.print(f"[green]截帧完成，成功 {len(results)}/{total} 张[/green]")
        return results

    def get_video_duration(self, video_path: Path) -> Optional[float]:
        """
        获取视频时长

        Args:
            video_path: 视频文件路径

        Returns:
            视频时长（秒），失败返回None
        """
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return float(result.stdout.strip())
            return None

        except Exception:
            return None
