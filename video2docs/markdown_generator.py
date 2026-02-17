"""Markdown生成器模块 - 生成最终的Markdown文档"""
import re
from pathlib import Path
from typing import Dict, List
from rich.console import Console

console = Console()


class MarkdownGenerator:
    """Markdown文档生成器"""

    def __init__(self, output_dir: Path):
        """
        初始化生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        title: str,
        video_intro: str,
        content: str,
        video_info: Dict,
        frame_mapping: Dict[str, Path]
    ) -> Path:
        """
        生成Markdown文档

        Args:
            title: 文档标题
            video_intro: 视频介绍
            content: 文档内容（已包含IMAGE标记）
            video_info: 视频信息
            frame_mapping: 时间戳到图片路径的映射

        Returns:
            生成的文档路径
        """
        # 构建完整的文档
        doc = self._build_document(
            title=title,
            video_intro=video_intro,
            content=content,
            video_info=video_info
        )

        # 提取所有IMAGE标记并替换为真实图片
        doc = self._replace_image_marks(doc, frame_mapping)

        # 保存文档
        safe_title = self._sanitize_filename(title)
        output_path = self.output_dir / f"{safe_title}.md"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(doc)

        console.print(f"[green]文档已生成: {output_path}[/green]")
        return output_path

    def _build_document(
        self,
        title: str,
        video_intro: str,
        content: str,
        video_info: Dict
    ) -> str:
        """构建完整的Markdown文档"""
        # 格式化时长
        duration = video_info.get('duration', 0)
        if duration is None:
            duration = 0
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        duration_str = f"{minutes:02d}:{seconds:02d}"

        # 构建头部
        header = f"""# {title}

> 来源: [{video_info.get('url', 'B站视频')}]({video_info.get('url', '')})
> 时长: {duration_str}
> 创作者: {video_info.get('uploader', '未知')}

---

{video_intro}

---

"""

        # 组合完整文档
        return header + content

    def _replace_image_marks(
        self,
        content: str,
        frame_mapping: Dict[str, Path]
    ) -> str:
        """
        替换IMAGE标记为真实的Markdown图片语法

        Args:
            content: 文档内容
            frame_mapping: 时间戳到图片路径的映射

        Returns:
            替换后的内容
        """
        # 优先处理已有的 Markdown 图片格式
        # LLM 输出格式: ![说明](images/MM:SS.jpg)
        # 实际文件格式: MM_SS.jpg (冒号被替换为下划线)
        # 兼容旧的 frame_XXX 格式
        content = re.sub(
            r'!\[([^\]]*)\]\(images/frame_(\d+)\.jpg\)',
            r'![\1](images/frame_\2.jpg)',
            content
        )

        # 处理 MM:SS 格式 - 替换冒号为下划线以匹配实际文件名
        def replace_timestamp_image(match):
            desc = match.group(1)
            timestamp = match.group(2)  # MM:SS 格式
            # 替换冒号为下划线以查找对应的图片文件
            timestamp_key = timestamp.replace(":", "_")

            if timestamp in frame_mapping:
                frame_path = frame_mapping[timestamp]
                relative_path = f"images/{frame_path.name}"
                return f"![{desc}]({relative_path})"
            else:
                console.print(f"[yellow]警告: 找不到时间戳 {timestamp} 对应的图片[/yellow]")
                return f"<!-- [IMAGE: {timestamp}] -->"

        # 替换 images/MM:SS.jpg 格式
        content = re.sub(
            r'!\[([^\]]*)\]\(images/(\d{2}:\d{2})\.jpg\)',
            replace_timestamp_image,
            content
        )

        # 查找所有 [IMAGE: MM:SS] 标记（兼容旧格式）
        pattern = r'\[IMAGE:\s*(\d{2}:\d{2})\]'

        def replace(match):
            timestamp = match.group(1)
            if timestamp in frame_mapping:
                frame_path = frame_mapping[timestamp]
                # 使用 images/ 相对路径
                relative_path = f"images/{frame_path.name}"
                return f"![{timestamp}]({relative_path})\n*{timestamp}*"
            else:
                console.print(f"[yellow]警告: 找不到时间戳 {timestamp} 对应的图片[/yellow]")
                return f"<!-- [IMAGE: {timestamp}] -->"

        return re.sub(pattern, replace, content)

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename

    def extract_image_timestamps(self, content: str) -> List[str]:
        """
        从内容中提取所有图片时间戳

        Args:
            content: Markdown内容

        Returns:
            时间戳列表
        """
        pattern = r'\[IMAGE:\s*(\d{2}:\d{2})\]'
        matches = re.findall(pattern, content)
        return matches
