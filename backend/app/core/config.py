"""
配置管理模块
从环境变量加载配置，使用 Pydantic Settings 进行类型验证
"""
from pathlib import Path
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent / "media"


class Settings(BaseSettings):
    """应用配置类"""

    # 基础配置
    PROJECT_NAME: str = "哪吒家庭"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # CORS 配置
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            # 尝试解析 JSON 数组格式（如 .env 中的 ["http://...","http://..."]）
            import json

            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass
            # 回退到逗号分隔格式
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # 数据库配置
    DATABASE_URL: str = (
        "postgresql+asyncpg://nezha_user:nezha_dev_password@localhost:5432/nezha_family"
    )

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT 配置
    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION"  # 生产环境必须修改
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 天

    # 代理配置
    TRUSTED_PROXY_COUNT: int = 0

    # 文件存储配置
    MEDIA_ROOT: str = str(_DEFAULT_MEDIA_ROOT)
    MEDIA_SIGNED_URL_EXPIRE_SECONDS: int = 60 * 60
    MEDIA_TRASH_RETENTION_DAYS: int = 30
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_IMAGE_EXTENSIONS: Union[List[str], str] = ["jpg", "jpeg", "png", "gif", "webp"]
    ALLOWED_VIDEO_EXTENSIONS: Union[List[str], str] = ["mp4", "mov", "avi"]

    @field_validator('ALLOWED_IMAGE_EXTENSIONS', 'ALLOWED_VIDEO_EXTENSIONS', mode='before')
    @classmethod
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v

    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_TIME_LIMIT: int = 600
    CELERY_TASK_SOFT_TIME_LIMIT: int = 540

    # AI 管家配置（默认关闭；API Key 可由数据库配置或环境变量提供）
    AI_ENABLED: bool = False
    AI_API_KEY: str = ""
    AI_DEFAULT_BASE_URL: str = "https://api.openai.com/v1"
    AI_DEFAULT_TEXT_MODEL: str = "gpt-4o-mini"
    AI_DEFAULT_VISION_MODEL: str = "gpt-4o-mini"
    AI_REQUEST_TIMEOUT_SECONDS: int = 30
    AI_FAILURE_THRESHOLD: int = 3
    AI_KEY_ENCRYPTION_SECRET: str = ""

    # 邀请码配置
    INVITE_CODE_LENGTH: int = 8
    INVITE_CODE_EXPIRES_DAYS: int = 30

    @field_validator("ENVIRONMENT")
    @classmethod
    def normalize_environment(cls, v: str) -> str:
        environment = v.strip().lower()
        if environment == "prod":
            return "production"
        if environment not in {"development", "test", "production"}:
            raise ValueError("ENVIRONMENT must be development, test, or production")
        return environment

    @field_validator("TRUSTED_PROXY_COUNT")
    @classmethod
    def validate_trusted_proxy_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("TRUSTED_PROXY_COUNT 不能为负数")
        return v

    @field_validator("MEDIA_TRASH_RETENTION_DAYS")
    @classmethod
    def validate_media_trash_retention_days(cls, v: int) -> int:
        if v < 1:
            raise ValueError("MEDIA_TRASH_RETENTION_DAYS 必须大于 0")
        return v

    @model_validator(mode="after")
    def validate_production_secret_key(self):
        if self.ENVIRONMENT == "production" and (
            not self.SECRET_KEY or self.SECRET_KEY == "CHANGE_THIS_IN_PRODUCTION"
        ):
            raise ValueError("生产环境必须设置非默认 SECRET_KEY")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# 全局配置实例
settings = Settings()
