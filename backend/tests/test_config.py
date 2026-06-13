"""
配置加载与启动契约测试。
"""
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.main import lifespan


def project_root_or_skip() -> Path:
    current_file = Path(__file__).resolve()
    for parent in current_file.parents:
        if (parent / ".env.example").exists() and (parent / "docker-compose.yml").exists():
            return parent

    pytest.skip("repository root config files are not mounted in this test environment")


def clear_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "DATABASE_URL",
        "DEBUG",
        "ENVIRONMENT",
        "SECRET_KEY",
        "TRUSTED_PROXY_COUNT",
        "ALLOWED_ORIGINS",
    ):
        monkeypatch.delenv(key, raising=False)


def test_settings_ignores_compose_only_env_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """根目录 compose .env 的额外字段不应导致后端配置导入失败。"""
    clear_settings_env(monkeypatch)

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


def test_settings_debug_defaults_to_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试 DEBUG 默认关闭，避免生产误暴露调试端点。"""
    clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")

    settings = Settings(_env_file=env_file)

    assert settings.DEBUG is False
    assert settings.ENVIRONMENT == "development"
    assert settings.TRUSTED_PROXY_COUNT == 0


def test_settings_rejects_default_secret_key_in_production(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试生产环境禁止使用默认 SECRET_KEY。"""
    clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("ENVIRONMENT=production\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="生产环境必须设置非默认 SECRET_KEY"):
        Settings(_env_file=env_file)


def test_settings_accepts_custom_secret_key_in_production(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试生产环境设置自定义 SECRET_KEY 后配置可加载。"""
    clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "ENVIRONMENT=production",
                "SECRET_KEY=prod-secret-that-is-not-default-123456",
                "ALLOWED_ORIGINS=https://family.example.com",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.ENVIRONMENT == "production"
    assert settings.SECRET_KEY == "prod-secret-that-is-not-default-123456"


def test_settings_rejects_short_secret_key_in_production(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    clear_settings_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ENVIRONMENT=production\nSECRET_KEY=too-short\nALLOWED_ORIGINS=https://family.example.com",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="长度至少 32 字符"):
        Settings(_env_file=env_file)


def test_settings_rejects_wildcard_cors_in_production(
    monkeypatch: pytest.MonkeyPatch,
):
    """生产环境禁止 ALLOWED_ORIGINS 包含通配符 *"""
    clear_settings_env(monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "prod-secret-that-is-not-default-123456")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")

    with pytest.raises(ValidationError, match="ALLOWED_ORIGINS 不能包含通配符"):
        Settings()


def test_env_example_documents_runtime_and_proxy_settings():
    env_example = project_root_or_skip() / ".env.example"
    content = env_example.read_text(encoding="utf-8")

    assert "DEBUG=false" in content
    assert "ENVIRONMENT=production" in content
    assert "TRUSTED_PROXY_COUNT=1" in content
    assert "CELERY_TASK_TIME_LIMIT=600" in content
    assert "CELERY_TASK_SOFT_TIME_LIMIT=540" in content
    assert "CELERY_WORKER_PREFETCH_MULTIPLIER=1" in content
    assert "CELERY_AI_TASK_TIME_LIMIT=180" in content
    assert "CELERY_AI_TASK_SOFT_TIME_LIMIT=150" in content
    assert "CELERY_MEDIA_CLEANUP_TASK_TIME_LIMIT=3600" in content
    assert "CELERY_MEDIA_CLEANUP_TASK_SOFT_TIME_LIMIT=3300" in content
    assert "ACCESS_TOKEN_EXPIRE_MINUTES=60" in content
    assert "DATABASE_POOL_SIZE=5" in content
    assert "DATABASE_MAX_OVERFLOW=10" in content
    assert "DATABASE_POOL_TIMEOUT=30" in content


def test_compose_files_make_runtime_settings_explicit():
    project_root = project_root_or_skip()
    compose_files = [
        project_root / "docker-compose.yml",
        project_root / "docker-compose.prod.yml",
    ]

    for compose_file in compose_files:
        content = compose_file.read_text(encoding="utf-8")
        assert "DEBUG:" in content
        assert "ENVIRONMENT:" in content
        assert "TRUSTED_PROXY_COUNT" in content
        assert "CELERY_TASK_TIME_LIMIT" in content
        assert "CELERY_TASK_SOFT_TIME_LIMIT" in content
        assert "CELERY_WORKER_PREFETCH_MULTIPLIER" in content
        assert "CELERY_MEDIA_CLEANUP_TASK_TIME_LIMIT" in content
        assert "CELERY_MEDIA_CLEANUP_TASK_SOFT_TIME_LIMIT" in content
        assert "DATABASE_POOL_SIZE" in content
        assert "DATABASE_MAX_OVERFLOW" in content
        assert "DATABASE_POOL_TIMEOUT" in content

    prod_content = (project_root / "docker-compose.prod.yml").read_text(encoding="utf-8")
    assert "ENVIRONMENT: production" in prod_content
    assert "TRUSTED_PROXY_COUNT: ${TRUSTED_PROXY_COUNT:-1}" in prod_content
    assert "ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-60}" in prod_content


def test_caddy_security_headers_are_configured():
    project_root = project_root_or_skip()
    prod_caddy = (project_root / "docker" / "Caddyfile").read_text(encoding="utf-8")
    dev_caddy = (project_root / "docker" / "Caddyfile.dev").read_text(encoding="utf-8")

    assert "Strict-Transport-Security" in prod_caddy
    assert "X-Frame-Options" in prod_caddy
    assert "X-Content-Type-Options" in prod_caddy
    assert "Referrer-Policy" in prod_caddy
    assert "Content-Security-Policy" in prod_caddy
    assert "frame-ancestors 'none'" in prod_caddy

    assert "X-Content-Type-Options" in dev_caddy
    assert "Strict-Transport-Security" not in dev_caddy
    assert "Content-Security-Policy" not in dev_caddy


@pytest.mark.asyncio
async def test_lifespan_disconnects_redis_pool(monkeypatch: pytest.MonkeyPatch):
    events: list[str] = []
    redis_url = "redis://localhost:6379/0"

    class FakePool:
        @classmethod
        def from_url(cls, url: str, decode_responses: bool):
            assert decode_responses is True
            events.append(f"pool:{url}")
            return cls()

        async def disconnect(self):
            events.append("disconnect")

    class FakeRedis:
        def __init__(self, connection_pool):
            events.append("redis")
            self.connection_pool = connection_pool

        async def aclose(self, close_connection_pool: bool = True):
            assert close_connection_pool is False
            events.append("close")

    monkeypatch.setattr("app.main.ConnectionPool", FakePool)
    monkeypatch.setattr("app.main.Redis", FakeRedis)
    monkeypatch.setattr("app.main.settings.REDIS_URL", redis_url)

    app = SimpleNamespace(state=SimpleNamespace())
    async with lifespan(app):
        assert isinstance(app.state.redis_pool, FakePool)
        assert isinstance(app.state.redis_client, FakeRedis)

    assert events == [f"pool:{redis_url}", "redis", "close", "disconnect"]
    assert app.state.redis_client is None
    assert app.state.redis_pool is None
