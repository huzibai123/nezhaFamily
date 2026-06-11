"""
AI 家庭管家 API 与服务测试
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import ai as ai_api
from app.core.security import create_access_token
from app.models.ai import AIAlbumSuggestion, AIJob, AIProviderConfig, AIReportDraft, AIPersona
from app.models.album import Album
from app.models.comment import Comment
from app.models.media import MediaFile
from app.models.notification import Notification
from app.models.post import Post
from app.models.user import User
from app.services import ai_housekeeper
from app.services.ai_client import AIChatResult, AIProviderError


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token({'user_id': str(user.id)})}"}


def active_provider() -> AIProviderConfig:
    return AIProviderConfig(
        name="测试模型",
        base_url="https://api.example.com/v1",
        api_key_encrypted="secret",
        text_model="gpt-test",
        enabled=True,
        status="active",
    )


async def ai_comment_count(db: AsyncSession, post_id) -> int:
    result = await db.execute(
        select(Comment.id).where(
            Comment.post_id == post_id,
            Comment.is_ai_generated.is_(True),
        )
    )
    return len(result.scalars().all())


class CaptionFakeClient:
    def __init__(self, content: str = "整理好的家庭配文") -> None:
        self.content = content
        self.calls = []

    async def chat(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})
        return AIChatResult(content=self.content, raw={})


def install_caption_client(monkeypatch, fake_client) -> None:
    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider, **kwargs: fake_client)
    monkeypatch.setattr(ai_api, "build_client", lambda provider, **kwargs: fake_client, raising=False)


def caption_from_response(response) -> str | None:
    data = response.json()
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        return data["data"].get("content") or data["data"].get("caption")
    if isinstance(data, dict):
        return data.get("content") or data.get("caption")
    return None


def flattened_message_text(messages) -> str:
    parts: list[str] = []

    def collect(value) -> None:
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    collect(messages)
    return "\n".join(parts)


def content_parts(messages) -> list[dict]:
    parts: list[dict] = []
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            parts.extend([part for part in content if isinstance(part, dict)])
    return parts


async def test_ai_status_creates_default_provider_and_personas(
    client: AsyncClient,
    test_admin: User,
):
    response = await client.get("/api/v1/admin/ai/status", headers=auth_headers(test_admin))

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["status"] == "disabled"
    assert data["personas_enabled"] >= 1
    assert data["provider"]["has_api_key"] is False


async def test_ai_status_reuses_orphaned_system_persona_users(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    username = ai_housekeeper._slugify_persona_name("哪吒总管")
    db.add(
        User(
            username=username,
            email=f"{username}@ai.nezha.local",
            password_hash="!",
            role="member",
            is_system=True,
            system_type="ai_persona",
        )
    )
    await db.commit()

    response = await client.get("/api/v1/admin/ai/status", headers=auth_headers(test_admin))

    assert response.status_code == 200
    data = response.json()
    assert data["personas_enabled"] >= 1


async def test_duplicate_persona_names_get_distinct_system_users(
    client: AsyncClient,
    test_admin: User,
):
    payload = {
        "name": "小猫",
        "persona_type": "pet_cat",
        "tone": "活泼、短句",
        "enabled": True,
    }

    first = await client.post(
        "/api/v1/admin/ai/personas",
        json=payload,
        headers=auth_headers(test_admin),
    )
    second = await client.post(
        "/api/v1/admin/ai/personas",
        json=payload,
        headers=auth_headers(test_admin),
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["user_id"] != second.json()["user_id"]


async def test_ai_search_requires_enabled_provider(
    client: AsyncClient,
    test_user: User,
):
    response = await client.get(
        "/api/v1/ai/search",
        params={"q": "生日"},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 400
    assert "AI 管家尚未启用" in response.json()["detail"]


async def test_post_caption_rejects_empty_content_and_files(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
):
    db.add(active_provider())
    await db.commit()

    response = await client.post(
        "/api/v1/ai/post-caption",
        data={"mode": "generate", "content": "   "},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 400
    assert "内容" in response.json()["detail"]


async def test_post_caption_member_can_polish_text(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    provider = active_provider()
    db.add(provider)
    await db.commit()
    fake_client = CaptionFakeClient("宝宝自己穿好鞋啦，今天又多了一点小独立。")
    install_caption_client(monkeypatch, fake_client)

    response = await client.post(
        "/api/v1/ai/post-caption",
        data={"mode": "polish", "content": "  宝宝今天第一次自己穿鞋  "},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 200
    assert caption_from_response(response) == "宝宝自己穿好鞋啦，今天又多了一点小独立。"
    assert len(fake_client.calls) == 1
    assert "宝宝今天第一次自己穿鞋" in flattened_message_text(fake_client.calls[0]["messages"])
    assert not any(
        part.get("type") in {"image_url", "input_image"}
        for part in content_parts(fake_client.calls[0]["messages"])
    )


async def test_post_caption_image_prompt_uses_multimodal_content(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    provider = active_provider()
    db.add(provider)
    await db.commit()
    fake_client = CaptionFakeClient("阳光下的小笑脸，像把今天都点亮了。")
    install_caption_client(monkeypatch, fake_client)

    response = await client.post(
        "/api/v1/ai/post-caption",
        data={"mode": "generate", "content": ""},
        files={"files[]": ("photo.jpg", b"fake-image-bytes", "image/jpeg")},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 200
    assert caption_from_response(response) == "阳光下的小笑脸，像把今天都点亮了。"
    parts = content_parts(fake_client.calls[0]["messages"])
    assert any(part.get("type") in {"image_url", "input_image"} for part in parts)
    assert "data:image/jpeg;base64" in flattened_message_text(parts)


async def test_post_caption_image_generation_falls_back_to_text_metadata(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    provider = active_provider()
    provider.vision_model = "vision-test"
    db.add(provider)
    await db.commit()
    calls = []

    class FallbackClient:
        async def chat(self, messages, **kwargs):
            calls.append({"messages": messages, "kwargs": kwargs})
            if len(calls) == 1:
                raise AIProviderError("vision unavailable", status_code=502)
            return AIChatResult(content="一张值得收藏的家庭小照片。", raw={})

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider, **kwargs: FallbackClient())

    response = await client.post(
        "/api/v1/ai/post-caption",
        data={"mode": "generate", "content": ""},
        files={"files[]": ("photo.jpg", b"fake-image-bytes", "image/jpeg")},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 200
    assert caption_from_response(response) == "一张值得收藏的家庭小照片。"
    assert len(calls) == 2
    assert any(part.get("type") in {"image_url", "input_image"} for part in content_parts(calls[0]["messages"]))
    assert not any(
        part.get("type") in {"image_url", "input_image"}
        for part in content_parts(calls[1]["messages"])
    )
    assert "photo.jpg" in flattened_message_text(calls[1]["messages"])


async def test_post_caption_video_prompt_uses_metadata_without_image_parts(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    provider = active_provider()
    db.add(provider)
    await db.commit()
    fake_client = CaptionFakeClient("一小段会反复回看的家庭视频。")
    install_caption_client(monkeypatch, fake_client)

    response = await client.post(
        "/api/v1/ai/post-caption",
        data={"mode": "polish", "content": "晚饭后的客厅"},
        files={"files[]": ("clip.mp4", b"fake-video-bytes", "video/mp4")},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 200
    assert caption_from_response(response) == "一小段会反复回看的家庭视频。"
    text = flattened_message_text(fake_client.calls[0]["messages"])
    parts = content_parts(fake_client.calls[0]["messages"])
    assert "video" in text or "视频" in text
    assert "clip.mp4" in text
    assert not any(part.get("type") in {"image_url", "input_image"} for part in parts)


@pytest.mark.parametrize(
    ("status_code", "expected_status"),
    [
        (401, "paused_billing_or_auth"),
        (402, "paused_billing_or_auth"),
        (403, "paused_billing_or_auth"),
        (429, "paused_rate_limit"),
    ],
)
async def test_post_caption_provider_auth_billing_or_rate_errors_pause_and_notify(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    test_user: User,
    status_code: int,
    expected_status: str,
    monkeypatch,
):
    provider = active_provider()
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    class FailingClient:
        async def chat(self, *args, **kwargs):
            raise AIProviderError("模型不可用", status_code=status_code)

    install_caption_client(monkeypatch, FailingClient())

    response = await client.post(
        "/api/v1/ai/post-caption",
        data={"mode": "polish", "content": "帮这条家庭动态润色一下"},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 503
    assert "模型不可用" in response.json()["detail"]
    await db.refresh(provider)
    assert provider.enabled is False
    assert provider.status == expected_status
    result = await db.execute(
        select(Notification).where(
            Notification.recipient_id == test_admin.id,
            Notification.type == "ai_paused",
            Notification.target_id == provider.id,
        )
    )
    assert result.scalar_one_or_none() is not None


async def test_post_caption_unavailable_provider_does_not_block_post_publish(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    class UnexpectedClient:
        async def chat(self, *args, **kwargs):
            raise AssertionError("post publish should not call the caption client")

    install_caption_client(monkeypatch, UnexpectedClient())

    response = await client.post(
        "/api/v1/posts",
        json={"content": "普通发布接口继续可用", "media": []},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 201
    assert response.json()["content"] == "普通发布接口继续可用"
    result = await db.execute(select(Post).where(Post.content == "普通发布接口继续可用"))
    assert result.scalar_one_or_none() is not None


async def test_provider_connection_failure_pauses_and_notifies_admin(
    db: AsyncSession,
    test_admin: User,
    monkeypatch,
):
    provider = AIProviderConfig(
        name="测试模型",
        base_url="https://api.example.com/v1",
        api_key_encrypted="secret",
        text_model="deepseek-chat",
        enabled=True,
        status="active",
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    class FailingClient:
        async def chat(self, *args, **kwargs):
            raise AIProviderError("余额不足", status_code=402)

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: FailingClient())

    ok, message = await ai_housekeeper.test_provider_connection(db, provider)
    await db.commit()

    assert ok is False
    assert "余额不足" in message
    assert provider.enabled is False
    assert provider.status == "paused_billing_or_auth"

    result = await db.execute(select(Notification).where(Notification.recipient_id == test_admin.id))
    notification = result.scalar_one_or_none()
    assert notification is not None
    assert notification.type == "ai_paused"


async def test_disabled_provider_connection_failure_only_records_error(
    db: AsyncSession,
    test_admin: User,
    monkeypatch,
):
    provider = AIProviderConfig(
        name="测试模型",
        base_url="https://api.example.com/v1",
        api_key_encrypted="secret",
        text_model="deepseek-chat",
        enabled=False,
        status="disabled",
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)

    class FailingClient:
        async def chat(self, *args, **kwargs):
            raise AIProviderError("鉴权失败", status_code=401)

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: FailingClient())

    ok, message = await ai_housekeeper.test_provider_connection(db, provider)
    await db.commit()

    assert ok is False
    assert "鉴权失败" in message
    assert provider.enabled is False
    assert provider.status == "disabled"
    assert provider.last_error == "鉴权失败"
    assert provider.last_checked_at is not None

    result = await db.execute(select(Notification).where(Notification.recipient_id == test_admin.id))
    assert result.scalar_one_or_none() is None


async def test_provider_update_hides_and_encrypts_api_key(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    response = await client.put(
        "/api/v1/admin/ai/providers/default",
        json={
            "name": "中转站",
            "base_url": "https://api.example.com/v1",
            "api_key": "secret-key",
            "text_model": "gpt-compatible",
            "vision_model": None,
            "timeout_seconds": 30,
            "enabled": True,
        },
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_api_key"] is True
    assert "api_key" not in data

    result = await db.execute(select(AIProviderConfig))
    provider = result.scalar_one()
    assert provider.api_key_encrypted != "secret-key"
    assert provider.api_key_encrypted.startswith("fernet:")
    assert ai_housekeeper.resolve_provider_api_key(provider) == "secret-key"


async def test_provider_update_preserves_existing_key_when_api_key_missing_or_blank(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    provider = AIProviderConfig(
        name="旧配置",
        base_url="https://api.example.com/v1",
        api_key_encrypted=ai_housekeeper.encrypt_ai_api_key("old-key"),
        text_model="gpt-old",
        enabled=True,
        status="active",
    )
    db.add(provider)
    await db.commit()

    base_payload = {
        "name": "新配置",
        "base_url": "https://api.example.com/v1",
        "text_model": "gpt-new",
        "vision_model": None,
        "timeout_seconds": 30,
        "enabled": True,
    }

    response = await client.put(
        "/api/v1/admin/ai/providers/default",
        json=base_payload,
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 200
    await db.refresh(provider)
    assert ai_housekeeper.resolve_provider_api_key(provider) == "old-key"

    response = await client.put(
        "/api/v1/admin/ai/providers/default",
        json={**base_payload, "api_key": "   "},
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 200
    await db.refresh(provider)
    assert ai_housekeeper.resolve_provider_api_key(provider) == "old-key"


async def test_provider_update_clear_api_key_and_new_key_precedence(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    provider = AIProviderConfig(
        name="旧配置",
        base_url="https://api.example.com/v1",
        api_key_encrypted=ai_housekeeper.encrypt_ai_api_key("old-key"),
        text_model="gpt-old",
        enabled=True,
        status="active",
    )
    db.add(provider)
    await db.commit()

    payload = {
        "name": "新配置",
        "base_url": "https://api.example.com/v1",
        "text_model": "gpt-new",
        "vision_model": None,
        "timeout_seconds": 30,
        "enabled": True,
    }

    response = await client.put(
        "/api/v1/admin/ai/providers/default",
        json={**payload, "clear_api_key": True},
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 200
    await db.refresh(provider)
    assert provider.api_key_encrypted is None
    assert provider.status == "disabled"

    response = await client.put(
        "/api/v1/admin/ai/providers/default",
        json={**payload, "clear_api_key": True, "api_key": "new-key"},
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 200
    await db.refresh(provider)
    assert ai_housekeeper.resolve_provider_api_key(provider) == "new-key"
    assert provider.status == "active"


async def test_provider_response_reports_api_key_source(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    monkeypatch,
):
    monkeypatch.setattr(ai_housekeeper.settings, "AI_API_KEY", "")
    response = await client.get(
        "/api/v1/admin/ai/status",
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 200
    assert response.json()["provider"]["api_key_source"] == "none"

    monkeypatch.setattr(ai_housekeeper.settings, "AI_API_KEY", "env-key")
    response = await client.get(
        "/api/v1/admin/ai/status",
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 200
    provider_data = response.json()["provider"]
    assert provider_data["has_api_key"] is True
    assert provider_data["api_key_source"] == "environment"

    provider = await ai_housekeeper.get_or_create_provider(db)
    provider.api_key_encrypted = ai_housekeeper.encrypt_ai_api_key("db-key")
    await db.commit()

    response = await client.get(
        "/api/v1/admin/ai/status",
        headers=auth_headers(test_admin),
    )
    assert response.status_code == 200
    assert response.json()["provider"]["api_key_source"] == "database"


async def test_provider_update_persists_wire_api_settings(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    provider = AIProviderConfig(
        name="旧配置",
        base_url="https://api.example.com/v1",
        api_key_encrypted=ai_housekeeper.encrypt_ai_api_key("old-key"),
        text_model="gpt-old",
        enabled=True,
        status="active",
    )
    db.add(provider)
    await db.commit()

    response = await client.put(
        "/api/v1/admin/ai/providers/default",
        json={
            "name": "Responses 配置",
            "base_url": "https://api.example.com/v1/responses",
            "text_model": "gpt-new",
            "vision_model": None,
            "timeout_seconds": 60,
            "enabled": True,
            "wire_api": "responses",
            "model_reasoning_effort": "low",
            "disable_response_storage": True,
        },
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["base_url"] == "https://api.example.com/v1"
    assert data["wire_api"] == "responses"
    assert data["model_reasoning_effort"] == "low"
    assert data["disable_response_storage"] is True

    await db.refresh(provider)
    assert provider.settings == {
        "wire_api": "responses",
        "model_reasoning_effort": "low",
        "disable_response_storage": True,
    }

    built_client = ai_housekeeper.build_client(provider)
    assert built_client.wire_api == "responses"
    assert built_client.reasoning_effort == "low"
    assert built_client.disable_response_storage is True


async def test_disabled_provider_connection_success_does_not_enable(
    db: AsyncSession,
    monkeypatch,
):
    provider = AIProviderConfig(
        name="测试模型",
        base_url="https://api.example.com/v1",
        api_key_encrypted="secret",
        text_model="gpt-test",
        enabled=False,
        status="disabled",
    )
    db.add(provider)
    await db.commit()

    class FakeClient:
        async def chat(self, *args, **kwargs):
            return AIChatResult(content="OK", raw={})

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: FakeClient())

    ok, message = await ai_housekeeper.test_provider_connection(db, provider)
    await db.commit()

    assert ok is True
    assert message == "连接可用，当前未启用"
    assert provider.enabled is False
    assert provider.status == "disabled"
    assert provider.last_error is None


async def test_provider_save_then_mock_test_success_and_resets_paused_error(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    monkeypatch,
):
    provider = AIProviderConfig(
        name="旧配置",
        base_url="https://api.example.com/v1",
        api_key_encrypted=ai_housekeeper.encrypt_ai_api_key("old-key"),
        text_model="gpt-old",
        enabled=False,
        status="paused_error",
        failure_count=3,
        last_error="旧错误",
        paused_reason="旧暂停",
        notified_pause_at=ai_housekeeper.now_utc(),
    )
    db.add(provider)
    await db.commit()

    update_response = await client.put(
        "/api/v1/admin/ai/providers/default",
        json={
            "name": "恢复配置",
            "base_url": "https://api.example.com/v1/chat/completions",
            "api_key": "fresh-key",
            "text_model": "gpt-fresh",
            "vision_model": None,
            "timeout_seconds": 30,
            "enabled": True,
        },
        headers=auth_headers(test_admin),
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["status"] == "active"
    assert data["base_url"] == "https://api.example.com/v1"
    assert data["last_error"] is None
    assert data["paused_reason"] is None

    class FakeClient:
        async def chat(self, *args, **kwargs):
            return AIChatResult(content="OK", raw={})

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: FakeClient())

    test_response = await client.post(
        "/api/v1/admin/ai/providers/default/test",
        headers=auth_headers(test_admin),
    )

    assert test_response.status_code == 200
    assert test_response.json() == {
        "ok": True,
        "status": "active",
        "message": "连接测试成功",
    }
    await db.refresh(provider)
    assert ai_housekeeper.resolve_provider_api_key(provider) == "fresh-key"


async def test_provider_test_handles_invalid_encrypted_key(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    provider = AIProviderConfig(
        name="旧配置",
        base_url="https://api.example.com/v1",
        api_key_encrypted="fernet:not-a-valid-token",
        text_model="gpt-test",
        enabled=True,
        status="active",
    )
    db.add(provider)
    await db.commit()

    response = await client.post(
        "/api/v1/admin/ai/providers/default/test",
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert "重新保存配置" in data["message"]


async def test_generate_ai_comment_creates_positive_comment(
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    provider = active_provider()
    post = Post(author_id=test_user.id, content="宝宝今天第一次自己走了两步", media_urls=[])
    db.add_all([provider, post])
    await db.commit()
    await db.refresh(post)
    await ai_housekeeper.ensure_default_personas(db)
    await db.commit()

    class FakeClient:
        async def chat(self, *args, **kwargs):
            return AIChatResult(content="太珍贵啦，这一步真是温暖又开心！", raw={})

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: FakeClient())

    comment = await ai_housekeeper.generate_ai_comment_for_post(db, post.id)
    await db.commit()

    assert comment is not None
    assert comment.is_ai_generated is True
    assert comment.ai_persona_id is not None
    assert "温暖" in comment.content or "开心" in comment.content


@pytest.mark.parametrize(
    ("enabled", "status"),
    [
        (False, "disabled"),
        (False, "paused_billing_or_auth"),
        (True, "paused_rate_limit"),
    ],
)
async def test_generate_ai_comment_skips_when_ai_off_or_paused(
    db: AsyncSession,
    test_user: User,
    enabled: bool,
    status: str,
    monkeypatch,
):
    provider = active_provider()
    provider.enabled = enabled
    provider.status = status
    post = Post(author_id=test_user.id, content="今天去公园玩了", media_urls=[])
    db.add_all([provider, post])
    await db.commit()
    await db.refresh(post)

    class UnexpectedClient:
        async def chat(self, *args, **kwargs):
            raise AssertionError("AI client should not be called")

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: UnexpectedClient())

    comment = await ai_housekeeper.generate_ai_comment_for_post(db, post.id)
    await db.commit()

    assert comment is None
    assert await ai_comment_count(db, post.id) == 0


async def test_generate_ai_comment_skips_when_all_auto_comment_personas_disabled(
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    provider = active_provider()
    post = Post(author_id=test_user.id, content="今天吃了甜甜的蛋糕", media_urls=[])
    db.add_all([provider, post])
    await db.commit()
    await db.refresh(post)
    personas = await ai_housekeeper.ensure_default_personas(db)
    for persona in personas:
        persona.auto_comment_enabled = False
    await db.commit()

    class UnexpectedClient:
        async def chat(self, *args, **kwargs):
            raise AssertionError("AI client should not be called")

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: UnexpectedClient())

    comment = await ai_housekeeper.generate_ai_comment_for_post(db, post.id)
    await db.commit()

    assert comment is None
    assert await ai_comment_count(db, post.id) == 0


async def test_generate_ai_comment_is_idempotent_per_post(
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    provider = active_provider()
    post = Post(author_id=test_user.id, content="宝宝今天第一次自己搭积木", media_urls=[])
    db.add_all([provider, post])
    await db.commit()
    await db.refresh(post)
    await ai_housekeeper.ensure_default_personas(db)
    await db.commit()

    class FakeClient:
        calls = 0

        async def chat(self, *args, **kwargs):
            self.calls += 1
            return AIChatResult(content=f"第{self.calls}次也很温暖！", raw={})

    fake_client = FakeClient()
    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: fake_client)

    first = await ai_housekeeper.generate_ai_comment_for_post(db, post.id)
    await db.commit()
    second = await ai_housekeeper.generate_ai_comment_for_post(db, post.id)
    await db.commit()

    assert first is not None
    assert second is None
    assert fake_client.calls == 1
    assert await ai_comment_count(db, post.id) == 1


@pytest.mark.parametrize(
    ("status_code", "expected_status"),
    [
        (401, "paused_billing_or_auth"),
        (402, "paused_billing_or_auth"),
        (403, "paused_billing_or_auth"),
        (429, "paused_rate_limit"),
    ],
)
async def test_generate_ai_comment_provider_auth_billing_or_rate_errors_pause_and_notify(
    db: AsyncSession,
    test_admin: User,
    test_user: User,
    status_code: int,
    expected_status: str,
    monkeypatch,
):
    provider = active_provider()
    post = Post(author_id=test_user.id, content="今天拍了一张很可爱的照片", media_urls=[])
    db.add_all([provider, post])
    await db.commit()
    await db.refresh(provider)
    await db.refresh(post)
    await ai_housekeeper.ensure_default_personas(db)
    await db.commit()

    class FailingClient:
        async def chat(self, *args, **kwargs):
            raise AIProviderError("模型不可用", status_code=status_code)

    monkeypatch.setattr(ai_housekeeper, "build_client", lambda provider: FailingClient())

    comment = await ai_housekeeper.generate_ai_comment_for_post(db, post.id)
    await db.commit()

    assert comment is None
    assert await ai_comment_count(db, post.id) == 0
    await db.refresh(provider)
    assert provider.enabled is False
    assert provider.status == expected_status
    result = await db.execute(
        select(Notification).where(
            Notification.recipient_id == test_admin.id,
            Notification.type == "ai_paused",
            Notification.target_id == provider.id,
        )
    )
    notification = result.scalar_one_or_none()
    assert notification is not None


async def test_admin_can_edit_ai_comment_but_member_cannot(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    test_user: User,
):
    persona_user = User(
        username="ai_test",
        email="ai_test@ai.nezha.local",
        password_hash="!",
        role="member",
        is_system=True,
        system_type="ai_persona",
    )
    db.add(persona_user)
    await db.flush()
    persona = AIPersona(
        user_id=persona_user.id,
        name="小猫",
        persona_type="pet_cat",
        enabled=True,
    )
    post = Post(author_id=test_user.id, content="今天吃了蛋糕", media_urls=[])
    db.add_all([persona, post])
    await db.flush()
    comment = Comment(
        post_id=post.id,
        author_id=persona_user.id,
        content="好开心！",
        is_ai_generated=True,
        ai_persona_id=persona.id,
    )
    db.add(comment)
    await db.commit()

    member_response = await client.patch(
        f"/api/v1/comments/{comment.id}",
        json={"content": "普通成员尝试修改"},
        headers=auth_headers(test_user),
    )
    assert member_response.status_code == 403

    admin_response = await client.patch(
        f"/api/v1/comments/{comment.id}",
        json={"content": "这条回忆真温暖，值得好好收藏。"},
        headers=auth_headers(test_admin),
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["content"] == "这条回忆真温暖，值得好好收藏。"
    assert admin_response.json()["edited_by"] == str(test_admin.id)


async def test_history_learning_job_requires_enabled_ai(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    response = await client.post(
        "/api/v1/admin/ai/jobs",
        json={"job_type": "history_learning"},
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 400
    assert "AI 管家尚未启用" in response.json()["detail"]
    result = await db.execute(select(AIJob))
    assert result.scalars().all() == []


async def test_ai_job_enqueue_failure_marks_job_failed(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    monkeypatch,
):
    provider = AIProviderConfig(
        name="测试模型",
        base_url="https://api.example.com/v1",
        api_key_encrypted="secret",
        text_model="gpt-test",
        enabled=True,
        status="active",
    )
    db.add(provider)
    await db.commit()

    def failing_delay(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(ai_api.run_ai_history_learning, "delay", failing_delay)

    response = await client.post(
        "/api/v1/admin/ai/jobs",
        json={"job_type": "history_learning"},
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 503
    result = await db.execute(select(AIJob))
    jobs = list(result.scalars().all())
    assert len(jobs) == 1
    job = jobs[0]
    assert job.status == "failed"
    assert "任务队列不可用" in (job.error_message or "")


async def test_album_suggestion_job_creates_reviewable_suggestion(
    db: AsyncSession,
    test_admin: User,
):
    provider = AIProviderConfig(
        name="测试模型",
        base_url="https://api.example.com/v1",
        api_key_encrypted="secret",
        text_model="gpt-test",
        enabled=True,
        status="active",
    )
    media = MediaFile(
        uploader_id=test_admin.id,
        file_type="image",
        original_name="birthday-cake.jpg",
        file_path="/2026/06/test.jpg",
        caption="宝宝生日吃蛋糕",
    )
    db.add_all([provider, media])
    await db.commit()

    job = await ai_housekeeper.create_album_suggestion_job(db, test_admin.id)
    await db.commit()

    await ai_housekeeper.run_album_suggestions(db, job.id)
    await db.commit()

    result = await db.execute(select(AIAlbumSuggestion))
    suggestion = result.scalar_one()
    assert suggestion.status == "pending"
    assert suggestion.target_id == media.id
    assert suggestion.suggested_album_name == "生日时光"


async def test_album_suggestion_approve_missing_media_keeps_review_fields_pending(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    suggestion = AIAlbumSuggestion(
        target_type="media",
        target_id=uuid4(),
        suggested_album_name="不存在的媒体",
        status="pending",
    )
    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    response = await client.post(
        f"/api/v1/admin/ai/album-suggestions/{suggestion.id}/review",
        json={"action": "approve", "album_id": str(uuid4())},
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 404
    await db.refresh(suggestion)
    assert suggestion.status == "pending"
    assert suggestion.reviewed_by is None
    assert suggestion.reviewed_at is None


async def test_album_suggestion_explicit_missing_album_returns_404(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    media = MediaFile(
        uploader_id=test_admin.id,
        file_type="image",
        original_name="park.jpg",
        file_path="/2026/06/park.jpg",
        caption="公园",
    )
    db.add(media)
    await db.flush()
    suggestion = AIAlbumSuggestion(
        target_type="media",
        target_id=media.id,
        suggested_album_name="一起出门的日子",
        status="pending",
    )
    db.add(suggestion)
    await db.commit()

    response = await client.post(
        f"/api/v1/admin/ai/album-suggestions/{suggestion.id}/review",
        json={"action": "approve", "album_id": str(uuid4())},
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 404
    result = await db.execute(select(Album))
    assert result.scalar_one_or_none() is None


async def test_admin_can_edit_published_ai_report_post(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    persona_user = User(
        username="ai_reporter",
        email="ai_reporter@ai.nezha.local",
        password_hash="!",
        role="member",
        is_system=True,
        system_type="ai_persona",
    )
    db.add(persona_user)
    await db.flush()
    persona = AIPersona(
        user_id=persona_user.id,
        name="哪吒总管",
        persona_type="steward",
        enabled=True,
    )
    db.add(persona)
    await db.flush()
    draft = AIReportDraft(
        persona_id=persona.id,
        period_type="week",
        period_start=ai_housekeeper.now_utc(),
        period_end=ai_housekeeper.now_utc(),
        title="本周回忆",
        content="一些温暖瞬间",
        status="draft",
        created_by=test_admin.id,
    )
    db.add(draft)
    await db.commit()

    publish_response = await client.post(
        f"/api/v1/admin/ai/reports/{draft.id}/publish",
        headers=auth_headers(test_admin),
    )
    assert publish_response.status_code == 200
    post_id = publish_response.json()["published_post_id"]

    update_response = await client.put(
        f"/api/v1/posts/{post_id}",
        json={"content": "管理员修正后的回忆报告"},
        headers=auth_headers(test_admin),
    )

    assert update_response.status_code == 200
    assert update_response.json()["content"] == "管理员修正后的回忆报告"


async def test_new_post_notifications_skip_ai_system_users(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    test_user: User,
):
    ai_user = User(
        username="ai_notice",
        email="ai_notice@ai.nezha.local",
        password_hash="!",
        role="member",
        is_system=True,
        system_type="ai_persona",
    )
    db.add(ai_user)
    await db.commit()

    response = await client.post(
        "/api/v1/posts",
        json={"content": "今天的家庭动态"},
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 201
    result = await db.execute(select(Notification.recipient_id))
    recipient_ids = set(result.scalars().all())
    assert test_user.id in recipient_ids
    assert ai_user.id not in recipient_ids
