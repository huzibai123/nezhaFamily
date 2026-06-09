"""
配置加载与启动契约测试。
"""
from pathlib import Path

import pytest

from app.core.config import Settings


def test_settings_ignores_compose_only_env_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """根目录 compose .env 的额外字段不应导致后端配置导入失败。"""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "POSTGRES_USER=nezha_user",
                "POSTGRES_PASSWORD=secret",
                "REDIS_PASSWORD=secret",
                "ADMIN_EMAIL=admin@example.com",
                "ENVIRONMENT=development",
                "DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app",
                "SECRET_KEY=test-secret",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@db:5432/app"
    assert settings.SECRET_KEY == "test-secret"
