from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """项目配置"""

    # GitHub 配置
    github_webhook_secret: str = "your-webhook-secret"
    github_token: Optional[str] = None

    # Redis 配置
    redis_url: str = "redis://localhost:6379"

    # LLM 配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
