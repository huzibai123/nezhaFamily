"""
相册 API 测试
测试相册 CRUD 和权限校验
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.album import Album
from app.models.media import MediaFile
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_create_album_success(client: AsyncClient, test_user: User):
    """测试创建相册成功"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    album_data = {
        "name": "家庭旅行",
        "description": "2024年春节旅行照片",
        "cover_image_url": "/media/cover.jpg"
    }

    response = await client.post(
        "/api/v1/albums",
        json=album_data,
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == album_data["name"]
    assert data["description"] == album_data["description"]
    assert data["created_by"] == str(test_user.id)
    assert data["media_count"] == 0


@pytest.mark.asyncio
async def test_create_album_unauthorized(client: AsyncClient):
    """测试未登录创建相册返回 403（FastAPI HTTPBearer 默认行为）"""
    album_data = {
        "name": "测试相册",
        "description": "测试描述"
    }

    response = await client.post(
        "/api/v1/albums",
        json=album_data
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_albums_list(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试获取相册列表（返回 media_count）"""
    # 创建测试相册
    album1 = Album(name="相册1", created_by=test_user.id)
    album2 = Album(name="相册2", created_by=test_user.id)
    db.add_all([album1, album2])
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/albums", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "albums" in data
    assert len(data["albums"]) == 2
    # 验证每个相册都有 media_count 字段
    for album in data["albums"]:
        assert "media_count" in album
        assert album["media_count"] == 0


@pytest.mark.asyncio
async def test_delete_album_by_creator(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试创建者可以删除自己的相册"""
    # 创建测试相册
    album = Album(name="待删除相册", created_by=test_user.id)
    db.add(album)
    await db.commit()
    await db.refresh(album)

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(
        f"/api/v1/albums/{album.id}",
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["message"] == "删除成功"


@pytest.mark.asyncio
async def test_delete_album_forbidden_non_creator(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession
):
    """测试非创建者无法删除别人的相册（403）"""
    # test_admin 创建相册
    album = Album(name="管理员相册", created_by=test_admin.id)
    db.add(album)
    await db.commit()
    await db.refresh(album)

    # test_user 尝试删除（应该失败）
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.delete(
        f"/api/v1/albums/{album.id}",
        headers=headers
    )

    assert response.status_code == 403
    assert "无权限删除" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_album_success(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试更新相册成功"""
    album = Album(name="原始名称", description="原始描述", created_by=test_user.id)
    db.add(album)
    await db.commit()
    await db.refresh(album)

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    update_data = {
        "name": "新名称",
        "description": "新描述"
    }

    response = await client.put(
        f"/api/v1/albums/{album.id}",
        json=update_data,
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新名称"
    assert data["description"] == "新描述"


@pytest.mark.asyncio
async def test_get_album_detail(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试获取相册详情（含媒体列表）"""
    album = Album(name="详情测试相册", created_by=test_user.id)
    db.add(album)
    await db.commit()
    await db.refresh(album)

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"/api/v1/albums/{album.id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(album.id)
    assert data["name"] == album.name
    assert "media" in data
    assert isinstance(data["media"], list)


@pytest.mark.asyncio
async def test_add_and_remove_media_from_album(
    client: AsyncClient,
    test_user: User,
    db: AsyncSession,
):
    """测试相册媒体添加、详情返回与移除闭环。"""
    album = Album(name="可整理相册", created_by=test_user.id)
    media = MediaFile(
        uploader_id=test_user.id,
        file_type="image",
        file_path="/media/family-photo.jpg",
        file_size=128,
    )
    db.add_all([album, media])
    await db.commit()
    await db.refresh(album)
    await db.refresh(media)

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    add_response = await client.post(
        f"/api/v1/albums/{album.id}/media/{media.id}",
        headers=headers,
    )
    assert add_response.status_code == 200

    detail_response = await client.get(
        f"/api/v1/albums/{album.id}",
        headers=headers,
    )
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert len(detail_payload["media"]) == 1
    assert detail_payload["media"][0]["id"] == str(media.id)
    assert detail_payload["media"][0]["url"].startswith(f"{media.file_path}?token=")
    assert detail_payload["media"][0]["type"] == media.file_type

    remove_response = await client.delete(
        f"/api/v1/albums/{album.id}/media/{media.id}",
        headers=headers,
    )
    assert remove_response.status_code == 200

    empty_detail_response = await client.get(
        f"/api/v1/albums/{album.id}",
        headers=headers,
    )
    assert empty_detail_response.status_code == 200
    assert empty_detail_response.json()["media"] == []
