"""视频转文档工具 - 配置文件"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """项目配置类，从.env文件读取配置"""

    # LLM配置（用于生成 Markdown）
    llm_base_url: str = Field(default="", alias="base_url")
    llm_api_key: str = Field(default="", alias="api_key")
    llm_model: str = Field(default="", alias="model")

    # Whisper配置（用于语音转文字，与 LLM 分开）
    whisper_base_url: str = Field(default="", alias="whisper_base_url")
    whisper_api_key: str = Field(default="", alias="whisper_api_key")

    # 视频配置
    video_quality: str = "1080"

    # 路径配置
    output_dir: Path = Field(default=Path("./output"))
    temp_dir: Path = Field(default=Path("./temp"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_configured(self) -> bool:
        """检查是否已配置LLM"""
        return bool(self.llm_base_url and self.llm_api_key and self.llm_model)

    @property
    def is_whisper_api_configured(self) -> bool:
        """检查是否已配置 Whisper API"""
        return bool(self.whisper_base_url and self.whisper_api_key)


def get_settings() -> Settings:
    """获取配置实例"""
    return Settings()
