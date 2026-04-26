from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


# ============================================================
# 配置层
# 作用：集中管理项目配置，从 .env 文件读取
# 特点：Pydantic Settings 自动做环境变量映射
# ============================================================

class Settings(BaseSettings):
    """项目配置

    通过 pydantic_settings 从环境变量/.env 文件读取配置
    """

    # GitHub 配置
    github_webhook_secret: str = "your-webhook-secret"
    github_token: Optional[str] = None

    # Redis 配置（后续用于消息队列）
    redis_url: str = "redis://localhost:6379"

    # LLM 配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # pydantic v2 写法
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
