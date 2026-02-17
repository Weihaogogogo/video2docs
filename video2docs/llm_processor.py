"""LLM处理器模块 - 调用大模型进行内容处理"""
import json
import re
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from rich.console import Console
from .prompts import FIRST_STAGE_PROMPT, SECOND_STAGE_PROMPT, VIDEO_INFO_PROMPT
from .transcriber import TranscriptSegment

console = Console()


class ImagePlan:
    """图片插入计划"""

    def __init__(self, timestamp: str, description: str):
        self.timestamp = timestamp
        self.description = description

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "description": self.description
        }


class LLMProcessor:
    """LLM处理器"""

    def __init__(self, base_url: str, api_key: str, model: str):
        """
        初始化LLM处理器

        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model

    def _call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """
        调用LLM

        Args:
            prompt: 用户提示
            system_prompt: 系统提示

        Returns:
            LLM响应文本
        """
        if system_prompt is None:
            system_prompt = "你是一个专业的AI助手。"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=8192,
            )
            return response.choices[0].message.content

        except Exception as e:
            console.print(f"[red]LLM调用失败: {str(e)}[/red]")
            raise

    def polish_content(self, transcript: List[TranscriptSegment]) -> str:
        """
        第一阶段：内容润色

        Args:
            transcript: 转录片段列表

        Returns:
            润色后的Markdown文档
        """
        console.print("[cyan]阶段1/2: 正在润色内容...[/cyan]")

        # 转换为带时间戳的文本格式
        transcript_text = ""
        for seg in transcript:
            timestamp = seg.format_timestamp(seg.start)
            transcript_text += f"[{timestamp}] {seg.text}\n"

        prompt = FIRST_STAGE_PROMPT.format(transcript=transcript_text)

        result = self._call_llm(prompt)

        console.print("[green]内容润色完成[/green]")
        return result

    def add_image_markers(
        self,
        transcript: List[TranscriptSegment],
        polished_content: str
    ) -> Tuple[str, List[ImagePlan]]:
        """
        第二阶段：添加图片标记

        Args:
            transcript: 转录片段列表
            polished_content: 润色后的内容

        Returns:
            (带图片标记的文档, 图片计划列表)
        """
        console.print("[cyan]阶段2/2: 正在分析关键帧位置...[/cyan]")

        # 转换为带时间戳的文本格式
        transcript_text = ""
        for seg in transcript:
            timestamp = seg.format_timestamp(seg.start)
            transcript_text += f"[{timestamp}] {seg.text}\n"

        prompt = SECOND_STAGE_PROMPT.format(
            transcript=transcript_text,
            polished_content=polished_content
        )

        # 直接使用LLM返回的内容（已经包含图片标记）
        marked_content = self._call_llm(prompt)

        # 提取图片计划
        image_plans = self._extract_image_plans_from_content(marked_content)

        console.print(f"[green]关键帧分析完成，共 {len(image_plans)} 张图片[/green]")
        return marked_content, image_plans

    def _extract_image_plans_from_content(self, content: str) -> List[ImagePlan]:
        """从内容中提取图片计划"""
        plans = []

        # 优先匹配新的时间戳格式：![说明](images/MM:SS.jpg)
        pattern_new = r'!\[([^\]]*)\]\(images/(\d{2}:\d{2})\.jpg\)'
        matches = re.findall(pattern_new, content)
        for desc, timestamp in matches:
            plans.append(ImagePlan(
                timestamp=timestamp,
                description=desc
            ))

        # 兼容旧的frame_XXX格式
        if not plans:
            pattern_old = r'!\[([^\]]*)\]\(images/frame_(\d+)\.jpg\)'
            matches = re.findall(pattern_old, content)
            for desc, num in matches:
                plans.append(ImagePlan(
                    timestamp=f"frame_{int(num):03d}",
                    description=desc
                ))

        return plans

    def _parse_image_plans(self, response: str) -> List[ImagePlan]:
        """解析LLM返回的图片计划"""
        plans = []

        # 尝试提取JSON部分
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                data = json.loads(json_str)
                for item in data:
                    if isinstance(item, dict) and 'timestamp' in item:
                        plans.append(ImagePlan(
                            timestamp=item['timestamp'],
                            description= item.get('description', '')
                        ))
            except json.JSONDecodeError:
                console.print("[yellow]JSON解析失败，尝试其他方式[/yellow]")

        # 如果没有解析到任何计划，尝试从文本中提取
        if not plans:
            # 简单提取 [IMAGE: MM:SS] 格式的时间戳
            timestamps = re.findall(r'\[IMAGE:\s*(\d{2}:\d{2})\]', response)
            for ts in timestamps:
                plans.append(ImagePlan(timestamp=ts, description=""))

        return plans

    def _insert_image_marks(self, content: str, plans: List[ImagePlan]) -> str:
        """将图片标记插入到文档中"""
        # 简单处理：在每个图片计划对应位置插入标记
        # 注意：这里是一个简化实现，实际上LLM返回的应该已经包含了标记

        # 检查内容是否已经包含IMAGE标记
        if '[IMAGE:' in content:
            return content

        # 如果没有，但有计划，则在合适位置插入
        # 这里简单地在开头插入所有计划（实际应由LLM决定位置）
        marks = "\n\n".join([f"[IMAGE: {p.timestamp}] {p.description}" for p in plans])
        return f"{content}\n\n---\n\n### 关键帧\n\n{marks}"

    def get_video_intro(self, video_info: Dict) -> str:
        """
        生成视频介绍

        Args:
            video_info: 视频信息字典

        Returns:
            视频介绍文本
        """
        console.print("[cyan]生成视频介绍...[/cyan]")

        duration = video_info.get('duration', 0)
        if duration is None:
            duration = 0
        duration_min = int(duration) // 60
        duration_sec = int(duration) % 60

        prompt = VIDEO_INFO_PROMPT.format(
            title=video_info.get('title', '未知'),
            duration=f"{duration_min:02d}:{duration_sec:02d}",
            uploader=video_info.get('uploader', '未知'),
            url=video_info.get('url', '')
        )

        result = self._call_llm(prompt)
        console.print("[green]视频介绍生成完成[/green]")
        return result
