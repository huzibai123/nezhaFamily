"""
媒体 API 测试
测试媒体上传和获取
"""

import pytest
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import media as media_api
from app.core import media_utils
from app.models.user import User
from app.models.album import Album, album_media
from app.models.media import MediaFavorite, MediaFile
from app.core.security import create_access_token


PNG_IMAGE_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def isolated_media_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use a per-test writable media root for upload tests."""
    media_root = tmp_path / "media"
    media_root.mkdir(exist_ok=True)
    monkeypatch.setattr(media_utils, "MEDIA_ROOT", media_root)
    return media_root


@pytest.mark.asyncio
async def test_upload_image_success(
    client: AsyncClient,
    test_user: User,
    db: AsyncSession,
    isolated_media_root: Path,
):
    """测试上传图片成功"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 创建一个简单的测试图片（1x1 像素 PNG）
    image_data = BytesIO(PNG_IMAGE_BYTES)

    files = {"files": ("test_image.png", image_data, "application/octet-stream")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 1
    uploaded_file = data["files"][0]
    assert "id" in uploaded_file
    assert "url" in uploaded_file
    assert uploaded_file["type"] == "image"
    assert uploaded_file["url"].startswith("/media/")
    assert "?token=" in uploaded_file["url"]
    assert uploaded_file["raw_url"].startswith("/media/")
    assert "?" not in uploaded_file["raw_url"]

    stored_media = await db.scalar(
        select(MediaFile).where(MediaFile.original_name == "test_image.png")
    )
    assert stored_media is not None
    assert stored_media.mime_type == "image/png"


@pytest.mark.asyncio
async def test_upload_response_url_can_access_signed_media(
    client: AsyncClient,
    test_user: User,
    isolated_media_root: Path,
):
    """上传响应中的 url 是可直接访问的签名媒体链接。"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    files = {"files": ("test_image.png", BytesIO(PNG_IMAGE_BYTES), "image/png")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 200
    uploaded_file = response.json()["files"][0]
    assert uploaded_file["url"].startswith(f"{uploaded_file['raw_url']}?token=")

    media_response = await client.get(uploaded_file["url"])
    assert media_response.status_code == 200
    assert media_response.content == PNG_IMAGE_BYTES


@pytest.mark.asyncio
async def test_upload_multi_file_failure_removes_saved_files_and_db_rows(
    client: AsyncClient,
    test_user: User,
    db: AsyncSession,
    isolated_media_root: Path,
):
    """同批上传后续文件失败时，已保存文件和 DB 记录都要回滚。"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    files = [
        ("files", ("ok.png", BytesIO(PNG_IMAGE_BYTES), "image/png")),
        ("files", ("bad.mp4", BytesIO(b"\x00\x00\x00not-a-real-mp4"), "video/mp4")),
    ]

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert list(isolated_media_root.iterdir()) == []
    media_count = await db.scalar(select(func.count()).select_from(MediaFile))
    assert media_count == 0


@pytest.mark.asyncio
async def test_upload_unauthorized(client: AsyncClient):
    """测试未登录上传返回 403（FastAPI HTTPBearer 默认行为）"""
    image_data = BytesIO(b"fake image data")
    files = {"files": ("test.png", image_data, "image/png")}

    response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, test_user: User):
    """测试上传不支持的文件类型返回 400"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 尝试上传 .txt 文件
    file_data = BytesIO(b"text content")
    files = {"files": ("test.txt", file_data, "text/plain")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert "不支持的文件类型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_unknown_magic_bytes(
    client: AsyncClient,
    test_user: User,
    isolated_media_root: Path,
):
    """测试伪造扩展名但无法识别真实文件头时拒绝上传。"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    fake_video = BytesIO(b"\x00\x00\x00not-a-real-mp4")
    files = {"files": ("fake.mp4", fake_video, "video/mp4")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert "无法识别文件类型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_allowed_extension_without_mime_mapping(
    client: AsyncClient,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试配置允许但没有 MIME 映射的扩展名会被强制拒绝。"""
    monkeypatch.setattr(
        media_api,
        "ALLOWED_EXTENSIONS",
        media_api.ALLOWED_EXTENSIONS | {".bmp"},
    )
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    files = {"files": ("bitmap.bmp", BytesIO(b"BMfake-bitmap"), "image/bmp")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert "不支持的文件类型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_mime_mismatch(
    client: AsyncClient,
    test_user: User,
    isolated_media_root: Path,
):
    """测试文件内容 MIME 与扩展名不匹配时拒绝上传。"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    files = {"files": ("pretend.jpg", BytesIO(PNG_IMAGE_BYTES), "image/jpeg")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert "文件内容与扩展名不匹配" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_accepts_mp4_ftyp_box(
    client: AsyncClient,
    test_user: User,
    isolated_media_root: Path,
):
    """测试 MP4/MOV 检测使用 ftyp box，而不是宽泛前缀。"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    mp4_data = BytesIO(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2")
    files = {"files": ("clip.mp4", mp4_data, "video/mp4")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 200
    assert response.json()["files"][0]["type"] == "video"


@pytest.mark.asyncio
async def test_get_media_detail(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试获取单个媒体详情"""
    # 创建测试媒体记录
    media = MediaFile(
        file_path="/media/test_image.jpg",
        file_type="image",
        original_name="test_image.jpg",
        mime_type="image/jpeg",
        file_size=1024,
        uploader_id=test_user.id,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(f"/api/v1/media/{media.id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(media.id)
    assert data["url"].startswith(f"{media.file_path}?token=")
    assert data["type"] == media.file_type
    assert data["original_name"] == media.original_name
    assert data["file_size"] == media.file_size


@pytest.mark.asyncio
async def test_signed_media_route_requires_valid_token(
    client: AsyncClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试 /media 文件访问必须带有效签名。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    media_file = media_root / "private.jpg"
    media_file.write_bytes(b"private-image")
    monkeypatch.setattr(media_utils, "MEDIA_ROOT", media_root)

    anonymous_response = await client.get("/media/private.jpg")
    assert anonymous_response.status_code == 403

    signed_url = media_utils.signed_media_url("/media/private.jpg")
    signed_response = await client.get(signed_url)
    assert signed_response.status_code == 200
    assert signed_response.content == b"private-image"

    tampered_response = await client.get("/media/private.jpg?token=bad-token")
    assert tampered_response.status_code == 403


@pytest.mark.asyncio
async def test_search_media_filters_and_signs_urls(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession,
):
    """测试家庭媒体搜索支持关键词、上传者、类型和日期过滤。"""
    target_media = MediaFile(
        file_path="/media/summer-birthday.jpg",
        thumbnail_path="/media/thumbs/summer-birthday.jpg",
        file_type="image",
        original_name="summer-birthday.jpg",
        file_size=2048,
        mime_type="image/jpeg",
        width=1200,
        height=800,
        uploader_id=test_user.id,
        created_at=datetime(2026, 6, 8, 10, 30, tzinfo=timezone.utc),
    )
    other_user_media = MediaFile(
        file_path="/media/summer-video.mp4",
        file_type="video",
        original_name="summer-video.mp4",
        file_size=4096,
        mime_type="video/mp4",
        uploader_id=test_admin.id,
        created_at=datetime(2026, 6, 9, 11, 0, tzinfo=timezone.utc),
    )
    old_media = MediaFile(
        file_path="/media/old-photo.jpg",
        file_type="image",
        original_name="old-photo.jpg",
        uploader_id=test_user.id,
        created_at=datetime(2026, 5, 1, 9, 0, tzinfo=timezone.utc),
    )
    db.add_all([target_media, other_user_media, old_media])
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        "/api/v1/media/search",
        params={
            "q": "summer",
            "uploader_id": str(test_user.id),
            "type": "image",
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["has_more"] is False
    item = data["media"][0]
    assert item["id"] == str(target_media.id)
    assert item["url"].startswith("/media/summer-birthday.jpg?token=")
    assert item["thumbnail_url"].startswith("/media/thumbs/summer-birthday.jpg?token=")
    assert item["type"] == "image"
    assert item["original_name"] == "summer-birthday.jpg"
    assert item["uploader"]["id"] == str(test_user.id)
    assert item["uploader"]["username"] == test_user.username
    assert [uploader["id"] for uploader in data["uploaders"]] == [str(test_user.id)]


@pytest.mark.asyncio
async def test_search_media_pagination_and_family_scope(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession,
):
    """测试媒体搜索分页，并允许家庭成员检索其他成员上传的媒体。"""
    media_files = [
        MediaFile(
            file_path=f"/media/family-{index}.jpg",
            file_type="image",
            original_name=f"family-{index}.jpg",
            uploader_id=test_admin.id if index == 1 else test_user.id,
            created_at=datetime(2026, 6, 9, 12 - index, 0, tzinfo=timezone.utc),
        )
        for index in range(3)
    ]
    db.add_all(media_files)
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        "/api/v1/media/search",
        params={"page": 2, "page_size": 1},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["page_size"] == 1
    assert data["has_more"] is True
    assert len(data["media"]) == 1
    assert data["media"][0]["uploader"]["id"] == str(test_admin.id)


@pytest.mark.asyncio
async def test_search_media_uploaders_are_faceted_outside_pagination_and_uploader_filter(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession,
):
    """测试上传者 facet 不受分页和当前 uploader_id 过滤限制。"""
    media_files = [
        MediaFile(
            file_path=f"/media/facet-user-{index}.jpg",
            file_type="image",
            original_name=f"facet-user-{index}.jpg",
            uploader_id=test_user.id,
            created_at=datetime(2026, 6, 9, 12, index, tzinfo=timezone.utc),
        )
        for index in range(3)
    ]
    media_files.append(
        MediaFile(
            file_path="/media/facet-admin.jpg",
            file_type="image",
            original_name="facet-admin.jpg",
            uploader_id=test_admin.id,
            created_at=datetime(2026, 6, 9, 13, 0, tzinfo=timezone.utc),
        )
    )
    db.add_all(media_files)
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        "/api/v1/media/search",
        params={
            "q": "facet",
            "uploader_id": str(test_user.id),
            "page": 1,
            "page_size": 1,
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["media"]) == 1
    uploader_ids = {item["id"] for item in data["uploaders"]}
    assert uploader_ids == {str(test_user.id), str(test_admin.id)}


@pytest.mark.asyncio
async def test_search_media_hides_deleted_files(
    client: AsyncClient,
    test_user: User,
    db: AsyncSession,
):
    """测试普通媒体搜索不会返回回收站文件。"""
    active_media = MediaFile(
        file_path="/media/active-search.jpg",
        file_type="image",
        original_name="active-search.jpg",
        uploader_id=test_user.id,
    )
    deleted_media = MediaFile(
        file_path="/media/deleted-search.jpg",
        file_type="image",
        original_name="deleted-search.jpg",
        uploader_id=test_user.id,
        deleted_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc),
        deleted_by=test_user.id,
    )
    db.add_all([active_media, deleted_media])
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/media/search", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["media"][0]["id"] == str(active_media.id)


@pytest.mark.asyncio
async def test_media_library_filters_facets_and_user_favorites(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession,
):
    """测试媒体库筛选、月份/上传者 facet、收藏隔离和回收站统计。"""
    favorite_media = MediaFile(
        file_path="/media/library-favorite.jpg",
        thumbnail_path="/media/thumbs/library-favorite.jpg",
        file_type="image",
        original_name="library-favorite.jpg",
        caption="儿童节照片",
        uploader_id=test_user.id,
        captured_at=datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc),
        created_at=datetime(2026, 6, 1, 9, 5, tzinfo=timezone.utc),
    )
    admin_media = MediaFile(
        file_path="/media/library-video.mp4",
        file_type="video",
        original_name="library-video.mp4",
        uploader_id=test_admin.id,
        captured_at=datetime(2026, 5, 20, 20, 0, tzinfo=timezone.utc),
        created_at=datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
    )
    deleted_media = MediaFile(
        file_path="/media/library-trash.jpg",
        file_type="image",
        original_name="library-trash.jpg",
        uploader_id=test_user.id,
        captured_at=datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc),
        deleted_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc),
        deleted_by=test_user.id,
    )
    db.add_all([favorite_media, admin_media, deleted_media])
    await db.flush()
    db.add(MediaFavorite(media_id=favorite_media.id, user_id=test_user.id))
    db.add(MediaFavorite(media_id=admin_media.id, user_id=test_admin.id))
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        "/api/v1/media/library",
        params={
            "q": "library",
            "date_from": "2026-05-01",
            "date_to": "2026-06-30",
            "page_size": 10,
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["trash_count"] == 1
    assert data["favorite_count"] == 1
    assert {item["id"] for item in data["media"]} == {
        str(favorite_media.id),
        str(admin_media.id),
    }
    favorite_item = next(item for item in data["media"] if item["id"] == str(favorite_media.id))
    admin_item = next(item for item in data["media"] if item["id"] == str(admin_media.id))
    assert favorite_item["is_favorite"] is True
    assert favorite_item["caption"] == "儿童节照片"
    assert favorite_item["thumbnail_url"].startswith("/media/thumbs/library-favorite.jpg?token=")
    assert admin_item["is_favorite"] is False
    assert {month["month"] for month in data["months"]} == {"2026-06", "2026-05"}
    assert {uploader["id"] for uploader in data["uploaders"]} == {
        str(test_user.id),
        str(test_admin.id),
    }

    favorite_response = await client.get(
        "/api/v1/media/library",
        params={"favorite_only": "true"},
        headers=headers,
    )
    assert favorite_response.status_code == 200
    favorite_data = favorite_response.json()
    assert favorite_data["total"] == 1
    assert favorite_data["media"][0]["id"] == str(favorite_media.id)

    trash_response = await client.get(
        "/api/v1/media/library",
        params={"trash_only": "true"},
        headers=headers,
    )
    assert trash_response.status_code == 200
    trash_data = trash_response.json()
    assert trash_data["total"] == 1
    assert trash_data["media"][0]["id"] == str(deleted_media.id)
    assert trash_data["media"][0]["deleted_at"] is not None


@pytest.mark.asyncio
async def test_media_favorite_is_user_scoped_and_rejects_deleted(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession,
):
    """测试收藏按用户隔离，且不能收藏回收站文件。"""
    media = MediaFile(
        file_path="/media/scope-favorite.jpg",
        file_type="image",
        original_name="scope-favorite.jpg",
        uploader_id=test_admin.id,
    )
    deleted_media = MediaFile(
        file_path="/media/scope-deleted.jpg",
        file_type="image",
        original_name="scope-deleted.jpg",
        uploader_id=test_admin.id,
        deleted_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc),
        deleted_by=test_admin.id,
    )
    db.add_all([media, deleted_media])
    await db.commit()

    user_token = create_access_token(data={"user_id": str(test_user.id)})
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_token = create_access_token(data={"user_id": str(test_admin.id)})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    response = await client.post(
        f"/api/v1/media/{media.id}/favorite",
        headers=user_headers,
    )
    assert response.status_code == 200
    assert response.json()["is_favorite"] is True

    admin_library = await client.get(
        "/api/v1/media/library",
        params={"favorite_only": "true"},
        headers=admin_headers,
    )
    assert admin_library.status_code == 200
    assert admin_library.json()["total"] == 0

    deleted_response = await client.post(
        f"/api/v1/media/{deleted_media.id}/favorite",
        headers=user_headers,
    )
    assert deleted_response.status_code == 404

    toggle_response = await client.post(
        f"/api/v1/media/{media.id}/favorite",
        headers=user_headers,
    )
    assert toggle_response.status_code == 200
    assert toggle_response.json()["is_favorite"] is False


@pytest.mark.asyncio
async def test_media_trash_restore_permissions_and_user_list_visibility(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession,
):
    """测试回收站权限、恢复和个人媒体列表隐藏软删除文件。"""
    own_media = MediaFile(
        file_path="/media/own-trash.jpg",
        file_type="image",
        original_name="own-trash.jpg",
        uploader_id=test_user.id,
    )
    admin_media = MediaFile(
        file_path="/media/admin-trash.jpg",
        file_type="image",
        original_name="admin-trash.jpg",
        uploader_id=test_admin.id,
    )
    db.add_all([own_media, admin_media])
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    denied_response = await client.delete(f"/api/v1/media/{admin_media.id}", headers=headers)
    assert denied_response.status_code == 200
    assert denied_response.json()["affected"] == 0
    assert denied_response.json()["skipped"] == 1

    trash_response = await client.delete(f"/api/v1/media/{own_media.id}", headers=headers)
    assert trash_response.status_code == 200
    assert trash_response.json()["affected"] == 1

    user_media_response = await client.get("/api/v1/media", headers=headers)
    assert user_media_response.status_code == 200
    assert user_media_response.json()["media"] == []

    trash_library = await client.get(
        "/api/v1/media/library",
        params={"trash_only": "true"},
        headers=headers,
    )
    assert trash_library.status_code == 200
    assert trash_library.json()["total"] == 1

    restore_response = await client.post(
        f"/api/v1/media/{own_media.id}/restore",
        headers=headers,
    )
    assert restore_response.status_code == 200
    assert restore_response.json()["affected"] == 1

    restored_library = await client.get("/api/v1/media/library", headers=headers)
    assert restored_library.status_code == 200
    assert restored_library.json()["total"] == 2


@pytest.mark.asyncio
async def test_media_bulk_add_to_album_skips_deleted_and_duplicates(
    client: AsyncClient,
    test_user: User,
    db: AsyncSession,
):
    """测试批量加入相册会跳过已存在和回收站媒体，相册详情也隐藏回收站媒体。"""
    album = Album(name="六月", description="夏天", created_by=test_user.id)
    active_media = MediaFile(
        file_path="/media/album-active.jpg",
        file_type="image",
        original_name="album-active.jpg",
        uploader_id=test_user.id,
    )
    duplicate_media = MediaFile(
        file_path="/media/album-duplicate.jpg",
        file_type="image",
        original_name="album-duplicate.jpg",
        uploader_id=test_user.id,
    )
    deleted_media = MediaFile(
        file_path="/media/album-deleted.jpg",
        file_type="image",
        original_name="album-deleted.jpg",
        uploader_id=test_user.id,
        deleted_at=datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc),
        deleted_by=test_user.id,
    )
    db.add_all([album, active_media, duplicate_media, deleted_media])
    await db.flush()
    await db.execute(
        album_media.insert().values(album_id=album.id, media_id=duplicate_media.id)
    )
    await db.execute(
        album_media.insert().values(album_id=album.id, media_id=deleted_media.id)
    )
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/media/bulk",
        json={
            "action": "add_to_album",
            "album_id": str(album.id),
            "media_ids": [
                str(active_media.id),
                str(duplicate_media.id),
                str(deleted_media.id),
            ],
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["affected"] == 1
    assert data["skipped"] == 2

    album_response = await client.get(f"/api/v1/albums/{album.id}", headers=headers)
    assert album_response.status_code == 200
    album_data = album_response.json()
    assert [item["id"] for item in album_data["media"]] == [
        str(active_media.id),
        str(duplicate_media.id),
    ]
    assert all(item["added_at"] for item in album_data["media"])


@pytest.mark.asyncio
async def test_media_update_requires_owner_or_admin_and_normalizes_caption(
    client: AsyncClient,
    test_user: User,
    test_admin: User,
    db: AsyncSession,
):
    """测试媒体元数据修改权限和说明清理。"""
    media = MediaFile(
        file_path="/media/edit-me.jpg",
        file_type="image",
        original_name="edit-me.jpg",
        uploader_id=test_admin.id,
    )
    db.add(media)
    await db.commit()

    user_token = create_access_token(data={"user_id": str(test_user.id)})
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_token = create_access_token(data={"user_id": str(test_admin.id)})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    denied_response = await client.patch(
        f"/api/v1/media/{media.id}",
        json={"caption": "  偷偷改  "},
        headers=user_headers,
    )
    assert denied_response.status_code == 403

    captured_at = "2026-06-08T10:00:00Z"
    response = await client.patch(
        f"/api/v1/media/{media.id}",
        json={"caption": "  一张旧照片  ", "captured_at": captured_at},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["caption"] == "一张旧照片"
    assert data["captured_at"].startswith("2026-06-08T10:00:00")


@pytest.mark.asyncio
async def test_search_media_requires_auth(client: AsyncClient):
    """测试媒体搜索必须登录。"""
    response = await client.get("/api/v1/media/search")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_media_not_found(client: AsyncClient, test_user: User):
    """测试获取不存在的媒体返回 404"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 使用一个不存在的 UUID
    fake_uuid = "00000000-0000-0000-0000-000000000000"

    response = await client.get(f"/api/v1/media/{fake_uuid}", headers=headers)

    assert response.status_code == 404
    assert "媒体文件不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_media_list(
    client: AsyncClient, test_user: User, db: AsyncSession
):
    """测试获取当前用户的媒体列表"""
    # 创建多个测试媒体记录
    media1 = MediaFile(
        file_path="/media/image1.jpg", file_type="image", uploader_id=test_user.id
    )
    media2 = MediaFile(
        file_path="/media/video1.mp4", file_type="video", uploader_id=test_user.id
    )
    db.add_all([media1, media2])
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/media", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "media" in data
    assert len(data["media"]) == 2
    assert "skip" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_get_user_media_pagination(
    client: AsyncClient, test_user: User, db: AsyncSession
):
    """测试媒体列表分页"""
    # 创建多个测试媒体记录
    for i in range(5):
        media = MediaFile(
            file_path=f"/media/image{i}.jpg",
            file_type="image",
            uploader_id=test_user.id,
        )
        db.add(media)
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 测试分页参数
    response = await client.get("/api/v1/media?skip=2&limit=2", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data["media"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2
