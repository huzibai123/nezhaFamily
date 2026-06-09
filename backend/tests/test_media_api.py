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

from app.core import media_utils
from app.api import media as media_api
from app.models.user import User
from app.models.media import MediaFile
from app.core.security import create_access_token


PNG_IMAGE_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


@pytest.mark.asyncio
async def test_upload_image_success(client: AsyncClient, test_user: User):
    """测试上传图片成功"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 创建一个简单的测试图片（1x1 像素 PNG）
    image_data = BytesIO(PNG_IMAGE_BYTES)

    files = {
        "files": ("test_image.png", image_data, "image/png")
    }

    response = await client.post(
        "/api/v1/upload",
        files=files,
        headers=headers
    )

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


@pytest.mark.asyncio
async def test_upload_response_url_can_access_signed_media(
    client: AsyncClient,
    test_user: User,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """上传响应中的 url 是可直接访问的签名媒体链接。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    monkeypatch.setattr(media_utils, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(media_api, "MEDIA_ROOT", media_root)

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
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """同批上传后续文件失败时，已保存文件和 DB 记录都要回滚。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    monkeypatch.setattr(media_utils, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(media_api, "MEDIA_ROOT", media_root)

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    files = [
        ("files", ("ok.png", BytesIO(PNG_IMAGE_BYTES), "image/png")),
        ("files", ("bad.mp4", BytesIO(b"\x00\x00\x00not-a-real-mp4"), "video/mp4")),
    ]

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert list(media_root.iterdir()) == []
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

    response = await client.post(
        "/api/v1/upload",
        files=files,
        headers=headers
    )

    assert response.status_code == 400
    assert "不支持的文件类型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_unknown_magic_bytes(client: AsyncClient, test_user: User):
    """测试伪造扩展名但无法识别真实文件头时拒绝上传。"""
    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    fake_video = BytesIO(b"\x00\x00\x00not-a-real-mp4")
    files = {"files": ("fake.mp4", fake_video, "video/mp4")}

    response = await client.post("/api/v1/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert "无法识别文件类型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_accepts_mp4_ftyp_box(client: AsyncClient, test_user: User):
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
        uploader_id=test_user.id
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get(
        f"/api/v1/media/{media.id}",
        headers=headers
    )

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

    response = await client.get(
        f"/api/v1/media/{fake_uuid}",
        headers=headers
    )

    assert response.status_code == 404
    assert "媒体文件不存在" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_user_media_list(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试获取当前用户的媒体列表"""
    # 创建多个测试媒体记录
    media1 = MediaFile(
        file_path="/media/image1.jpg",
        file_type="image",
        uploader_id=test_user.id
    )
    media2 = MediaFile(
        file_path="/media/video1.mp4",
        file_type="video",
        uploader_id=test_user.id
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
async def test_get_user_media_pagination(client: AsyncClient, test_user: User, db: AsyncSession):
    """测试媒体列表分页"""
    # 创建多个测试媒体记录
    for i in range(5):
        media = MediaFile(
            file_path=f"/media/image{i}.jpg",
            file_type="image",
            uploader_id=test_user.id
        )
        db.add(media)
    await db.commit()

    token = create_access_token(data={"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 测试分页参数
    response = await client.get(
        "/api/v1/media?skip=2&limit=2",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["media"]) == 2
    assert data["skip"] == 2
    assert data["limit"] == 2
