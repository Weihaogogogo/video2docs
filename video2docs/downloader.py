"""视频下载器模块 - 支持多平台视频网站"""
import warnings
# 必须在导入 yt_dlp 之前抑制警告
warnings.filterwarnings('ignore')
warnings.filterwarnings('ignore', category=DeprecationWarning)

import yt_dlp
from pathlib import Path
from typing import Optional
from rich.console import Console
import sys

console = Console()


class VideoDownloader:
    """视频下载器，使用yt-dlp支持多平台视频"""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir

    def download(self, url: str) -> Optional[Path]:
        """
        下载视频

        Args:
            url: 视频URL（支持B站、YouTube等1000+网站）

        Returns:
            视频文件路径，如果失败返回None
        """
        # 视频保存路径
        output_template = str(self.temp_dir / "%(title)s.%(ext)s")

        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            # B站需要特定的 headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 获取视频信息并下载
                info = ydl.extract_info(url, download=True)
                video_title = info.get('title', 'video')

                # 找到下载的文件 - 使用更宽松的匹配
                video_files = list(self.temp_dir.glob("*.mp4"))
                if not video_files:
                    video_files = list(self.temp_dir.glob("*.mkv"))
                if not video_files:
                    video_files = list(self.temp_dir.glob("*.webm"))
                if not video_files:
                    # 最后尝试：列出所有文件
                    video_files = [f for f in self.temp_dir.iterdir() if f.is_file()]

                if video_files:
                    # 返回最大的文件（通常是完整的视频）
                    return max(video_files, key=lambda f: f.stat().st_size)

                console.print(f"[yellow]未找到视频文件，目录内容: {list(self.temp_dir.iterdir())}[/yellow]")
                return None

        except Exception as e:
            console.print(f"[red]视频下载失败: {str(e)}[/red]")
            return None

    def get_video_info(self, url: str) -> Optional[dict]:
        """
        获取视频信息

        Args:
            url: 视频URL

        Returns:
            视频信息字典
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', ''),
                    'url': url,
                }
        except Exception as e:
            console.print(f"[red]获取视频信息失败: {str(e)}[/red]")
            return None
