"""
帖子 API 测试
覆盖发帖内容与媒体的契约。
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import posts as posts_api
from app.core.security import create_access_token
from app.models.post import Post
from app.models.user import User


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(data={"user_id": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def media_item(url: str = "/media/family-photo.jpg") -> dict[str, object]:
    return {
        "type": "image",
        "url": url,
        "width": 1200,
        "height": 800,
    }


@pytest.mark.asyncio
async def test_create_pure_media_post_success(
    client: AsyncClient,
    test_user: User,
):
    """测试允许只包含媒体的帖子。"""
    response = await client.post(
        "/api/v1/posts",
        json={"media": [media_item()]},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["content"] == ""
    assert len(payload["media_urls"]) == 1
    assert payload["media_urls"][0]["url"].startswith("/media/family-photo.jpg?token=")


@pytest.mark.asyncio
async def test_create_post_succeeds_when_ai_comment_enqueue_fails(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
    monkeypatch,
):
    """测试 AI 自动评论入队失败不影响发帖主链路。"""

    def failing_delay(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(posts_api.generate_ai_comment, "delay", failing_delay)

    response = await client.post(
        "/api/v1/posts",
        json={"content": "今天也要好好记录一下"},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 201
    post_id = response.json()["id"]
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    assert post is not None
    assert post.content == "今天也要好好记录一下"


@pytest.mark.asyncio
async def test_create_empty_content_without_media_fails(
    client: AsyncClient,
    test_user: User,
):
    """测试不允许空文字且无媒体的帖子。"""
    response = await client.post(
        "/api/v1/posts",
        json={"content": "", "media": []},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 422
    assert "帖子内容和媒体不能同时为空" in response.text


@pytest.mark.asyncio
async def test_update_media_post_to_pure_media_success(
    client: AsyncClient,
    test_user: User,
):
    """测试有媒体的帖子可以更新为空文字，成为纯媒体帖子。"""
    create_response = await client.post(
        "/api/v1/posts",
        json={"content": "今天的照片", "media": [media_item()]},
        headers=auth_headers(test_user),
    )
    assert create_response.status_code == 201
    post_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/posts/{post_id}",
        json={"content": ""},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content"] == ""
    assert len(payload["media_urls"]) == 1


@pytest.mark.asyncio
async def test_update_post_to_empty_content_without_media_fails(
    client: AsyncClient,
    test_user: User,
):
    """测试更新后也不能变成空文字且无媒体。"""
    create_response = await client.post(
        "/api/v1/posts",
        json={"content": "准备清空的帖子", "media": [media_item()]},
        headers=auth_headers(test_user),
    )
    assert create_response.status_code == 201
    post_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/posts/{post_id}",
        json={"content": "", "media": []},
        headers=auth_headers(test_user),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "帖子内容和媒体不能同时为空"
