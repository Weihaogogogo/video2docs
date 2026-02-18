"""语音转文字模块 - 支持本地 Whisper 和 Whisper API"""
import subprocess
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
import tempfile

console = Console()


# ============ Whisper 模型缓存（支持复用）============
_model_cache: Dict[str, "WhisperModel"] = {}


def get_cached_whisper_model(
    model_name: str = "base",
    device: str = "cpu",
    compute_type: str = "int8"
) -> "WhisperModel":
    """
    获取或创建缓存的 Whisper 模型

    Args:
        model_name: 模型名称 (base, small, medium, large)
        device: 设备 (cpu, cuda)
        compute_type: 计算类型 (int8, float16, etc)

    Returns:
        WhisperModel 实例
    """
    from faster_whisper import WhisperModel

    cache_key = f"{model_name}_{device}_{compute_type}"

    if cache_key not in _model_cache:
        console.print(f"[cyan]首次加载 Whisper 模型: {model_name}...[/cyan]")
        _model_cache[cache_key] = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
    else:
        console.print(f"[cyan]复用已加载的 Whisper 模型: {model_name}[/cyan]")

    return _model_cache[cache_key]


def clear_model_cache():
    """清空模型缓存（通常在程序结束时调用）"""
    global _model_cache
    _model_cache.clear()
    console.print("[cyan]模型缓存已清空[/cyan]")


def is_model_downloaded(model_name: str = "base") -> bool:
    """
    检测 Whisper 模型是否已下载

    Args:
        model_name: 模型名称 (base, small, medium, large)

    Returns:
        True 如果模型已下载，False 如果需要下载
    """
    import os
    import platform

    # 确定缓存目录 - 先检查默认位置
    if platform.system() == "Windows":
        cache_dir = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "huggingface" / "hub"
    elif platform.system() == "Darwin":  # macOS
        # macOS 可能有两个位置，先检查 ~/.cache
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    else:  # Linux
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"

    # 如果默认目录不存在，尝试另一个位置
    if not cache_dir.exists() and platform.system() == "Darwin":
        alt_cache_dir = Path.home() / "Library" / "Caches" / "huggingface" / "hub"
        if alt_cache_dir.exists():
            cache_dir = alt_cache_dir

    if not cache_dir.exists():
        return False

    # 检查是否存在模型目录 - faster-whisper 使用 Systran 组织
    target_name = f"models--Systran--faster-whisper-{model_name}"

    for item in cache_dir.iterdir():
        # 检查目录名是否以目标名称开头
        if item.is_dir() and item.name.startswith(target_name.replace(".lock", "")):
            # 确保目录非空（有模型文件）
            if any(item.iterdir()):
                return True

    return False


class TranscriptSegment:
    """转录片段"""

    def __init__(self, start: float, end: float, text: str):
        self.start = start  # 秒
        self.end = end  # 秒
        self.text = text

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text
        }

    def format_timestamp(self, seconds: float) -> str:
        """格式化时间戳为 MM:SS 格式"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    @property
    def timestamp_str(self) -> str:
        """返回时间戳字符串"""
        return f"{self.format_timestamp(self.start)}"


class Transcriber:
    """语音转文字处理器 - 支持本地 Whisper 和 Whisper API"""

    def __init__(
        self,
        mode: str = "api",
        llm_client=None,
        api_base_url: str = "https://api.openai.com/v1",
        api_key: str = ""
    ):
        """
        初始化转录器

        Args:
            mode: 转录模式，"api" 或 "local"
            llm_client: OpenAI客户端实例（API模式用）
            api_base_url: Whisper API 基础URL
            api_key: Whisper API 密钥
        """
        self.mode = mode
        self.llm_client = llm_client
        self.api_base_url = api_base_url
        self.api_key = api_key

    def extract_audio(self, video_path: Path, output_path: Path) -> Optional[Path]:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径

        Returns:
            音频文件路径，失败返回None
        """
        # 使用ffmpeg提取音频
        cmd = [
            "ffmpeg",
            "-y",  # 覆盖已存在的文件
            "-i", str(video_path),
            "-vn",  # 不处理视频
            "-acodec", "libmp3lame",
            "-q:a", "2",  # 高质量
            "-ar", "16000",  # 采样率
            "-ac", "1",  # 单声道
            str(output_path)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0 and output_path.exists():
                return output_path
            else:
                console.print(f"[red]音频提取失败: {result.stderr}[/red]")
                return None

        except subprocess.TimeoutExpired:
            console.print("[red]音频提取超时[/red]")
            return None
        except Exception as e:
            console.print(f"[red]音频提取异常: {str(e)}[/red]")
            return None

    def transcribe(self, video_path: Path) -> List[TranscriptSegment]:
        """
        转录音频

        Args:
            video_path: 视频文件路径

        Returns:
            转录片段列表
        """
        # 提取音频
        temp_dir = video_path.parent
        audio_path = temp_dir / "temp_audio.mp3"

        audio_file = self.extract_audio(video_path, audio_path)
        if audio_file is None:
            console.print("[red]音频提取失败，无法继续转录[/red]")
            return []

        # 根据模式选择转录方式
        if self.mode == "api":
            return self._transcribe_api(audio_file)
        else:
            return self._transcribe_local(audio_file)

    def _transcribe_api(self, audio_path: Path) -> List[TranscriptSegment]:
        """使用 Whisper API 转录"""
        console.print(f"[cyan]正在使用 Whisper API 转录...[/cyan]")

        try:
            # 调用 Whisper API
            with open(audio_path, "rb") as f:
                response = self.llm_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )

            # 解析结果
            segments = []
            for seg in response.segments:
                segments.append(TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip()
                ))

            console.print(f"[green]Whisper API 转录完成，共 {len(segments)} 个片段[/green]")

            # 删除临时音频文件
            try:
                audio_path.unlink()
            except:
                pass

            return segments

        except Exception as e:
            console.print(f"[red]Whisper API 调用失败: {str(e)}[/red]")
            return []

    def _transcribe_local(self, audio_path: Path) -> List[TranscriptSegment]:
        """使用本地 Whisper 模型转录"""
        try:
            # 使用缓存的模型（首次加载，后续复用）
            model = get_cached_whisper_model("base", "cpu", "int8")

            # 执行转录
            segments, info = model.transcribe(
                str(audio_path),
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            console.print(f"[cyan]检测到语言: {info.language} (概率: {info.language_probability:.2f})[/cyan]")

            # 解析结果
            result_segments = []
            for seg in segments:
                result_segments.append(TranscriptSegment(
                    start=seg.start,
                    end=seg.end,
                    text=seg.text.strip()
                ))

            console.print(f"[green]本地 Whisper 转录完成，共 {len(result_segments)} 个片段[/green]")

            # 删除临时音频文件
            try:
                audio_path.unlink()
            except:
                pass

            return result_segments

        except Exception as e:
            console.print(f"[red]本地 Whisper 转录失败: {str(e)}[/red]")
            return []

    def segments_to_text(self, segments: List[TranscriptSegment], include_timestamp: bool = False) -> str:
        """
        将片段列表转换为文本

        Args:
            segments: 转录片段列表
            include_timestamp: 是否包含时间戳

        Returns:
            格式化后的文本
        """
        if include_timestamp:
            lines = []
            for seg in segments:
                timestamp = seg.format_timestamp(seg.start)
                lines.append(f"[{timestamp}] {seg.text}")
            return "\n".join(lines)
        else:
            return " ".join(seg.text for seg in segments)

    def get_available_timestamps(self, segments: List[TranscriptSegment]) -> List[str]:
        """
        获取所有可用的时间戳列表

        Args:
            segments: 转录片段列表

        Returns:
            时间戳字符串列表
        """
        return [seg.format_timestamp(seg.start) for seg in segments]

    def merge_segments_by_rule(
        self,
        segments: List[TranscriptSegment],
        min_duration: float = 8.0,
        max_duration: float = 20.0,
        merge_gap: float = 0.5
    ) -> List[TranscriptSegment]:
        """
        基于规则合并片段

        合并策略：
        1. 如果当前片段 < min_duration，尝试与下一片段合并
        2. 如果当前片段 + 下一片段 < max_duration 且间隔 < merge_gap，合并
        3. 如果当前片段以标点结尾（。！？），不合并

        Args:
            segments: 原始片段列表
            min_duration: 最小片段时长（秒）
            max_duration: 最大片段时长（秒）
            merge_gap: 可合并的最大间隔（秒）

        Returns:
            合并后的片段列表
        """
        if not segments:
            return []

        # 标点符号列表（句末标点）
        end_punctuation = {'。', '！', '？', '.', '!', '?'}

        merged = []
        current = segments[0]

        for i in range(1, len(segments)):
            next_seg = segments[i]
            gap = next_seg.start - current.end
            combined_duration = next_seg.end - current.start

            # 检查是否应该合并
            should_merge = (
                # 情况1：当前片段太短
                (current.end - current.start < min_duration) or
                # 情况2：间隔很短且合并后不超过最大时长
                (gap <= merge_gap and combined_duration < max_duration)
            )

            # 检查当前片段是否以句末标点结尾（不合并）
            if current.text.strip() and current.text.strip()[-1] in end_punctuation:
                should_merge = False

            if should_merge:
                # 合并
                current = TranscriptSegment(
                    start=current.start,
                    end=next_seg.end,
                    text=current.text + " " + next_seg.text
                )
            else:
                # 不合并，保存当前，开始新的
                merged.append(current)
                current = next_seg

        # 添加最后一个
        merged.append(current)

        console.print(f"[cyan]片段合并: {len(segments)} -> {len(merged)} 个[/cyan]")
        return merged
