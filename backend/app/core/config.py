"""
配置管理模块
从环境变量加载配置，使用 Pydantic Settings 进行类型验证
"""
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_MEDIA_ROOT = Path(__file__).resolve().parent.parent.parent / "media"


class Settings(BaseSettings):
    """应用配置类"""

    # 基础配置
    PROJECT_NAME: str = "哪吒家庭"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True  # 开发默认 True，生产设为 False

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

    # 文件存储配置
    MEDIA_ROOT: str = str(_DEFAULT_MEDIA_ROOT)
    MEDIA_SIGNED_URL_EXPIRE_SECONDS: int = 60 * 60
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

    # 邀请码配置
    INVITE_CODE_LENGTH: int = 8
    INVITE_CODE_EXPIRES_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# 全局配置实例
settings = Settings()
