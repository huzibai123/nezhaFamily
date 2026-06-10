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
    provider = AIProviderConfig(
        name="测试模型",
        base_url="https://api.example.com/v1",
        api_key_encrypted="secret",
        text_model="gpt-test",
        enabled=True,
        status="active",
    )
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
    test_admin: User,
):
    response = await client.post(
        "/api/v1/admin/ai/jobs",
        json={"job_type": "history_learning"},
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 400
    assert "AI 管家尚未启用" in response.json()["detail"]


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
    job = result.scalar_one()
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
