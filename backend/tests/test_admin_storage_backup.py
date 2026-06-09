"""
管理员存储与备份 API 测试
"""
import json
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.comment import Comment
from app.models.media import MediaFile
from app.models.post import Post
from app.models.user import User


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(data={"user_id": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_overview_includes_storage_status(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """管理员概览返回真实存储与备份状态字段。"""
    from app.api import admin as admin_api

    media_root = tmp_path / "media"
    backup_root = tmp_path / "backups"
    media_root.mkdir()
    backup_root.mkdir()
    (media_root / "example.jpg").write_bytes(b"example-media")

    monkeypatch.setattr(admin_api, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(admin_api, "BACKUP_ROOT", backup_root)

    post = Post(author_id=test_admin.id, content="管理概览测试", media_urls=[])
    db.add(post)
    await db.flush()
    comment = Comment(
        post_id=post.id,
        author_id=test_admin.id,
        content="一条最近评论",
    )
    media = MediaFile(
        file_path="/media/example.jpg",
        file_type="image",
        file_size=2048,
        uploader_id=test_admin.id,
    )
    db.add_all([comment, media])
    await db.commit()

    response = await client.get(
        "/api/v1/admin/overview",
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["storage"]["media_root"]
    assert payload["storage"]["database_media_bytes"] >= 2048
    assert payload["storage"]["disk_total_bytes"] > 0
    assert payload["backups"]["recent"] == []
    assert payload["recent_comments"][0]["content"] == "一条最近评论"
    assert payload["recent_media"][0]["uploader_username"] == test_admin.username
    assert payload["upload_warnings"][0]["warning"]


@pytest.mark.asyncio
async def test_create_admin_backup_writes_snapshot_files(
    client: AsyncClient,
    test_admin: User,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """创建备份会写入 JSON 快照、媒体归档和 manifest。"""
    from app.api import admin as admin_api

    media_root = tmp_path / "media"
    backup_root = tmp_path / "backups"
    media_root.mkdir()
    backup_root.mkdir()
    (media_root / "family.jpg").write_bytes(b"family-photo")

    monkeypatch.setattr(admin_api, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(admin_api, "BACKUP_ROOT", backup_root)

    response = await client.post(
        "/api/v1/admin/backups",
        headers=auth_headers(test_admin),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["media_file_count"] == 1
    assert payload["snapshot_file"].endswith("-database.json")
    assert payload["media_archive_file"].endswith("-media.tar.gz")

    backup_dir = backup_root / payload["backup_id"]
    manifest_path = backup_dir / "manifest.json"
    snapshot_path = backup_dir / f"{payload['backup_id']}-database.json"
    archive_path = backup_dir / f"{payload['backup_id']}-media.tar.gz"

    assert manifest_path.exists()
    assert snapshot_path.exists()
    assert archive_path.exists()

    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot["format"] == "nezha-family-json-snapshot-v1"
    assert "users" in snapshot["tables"]


@pytest.mark.asyncio
async def test_verify_and_download_admin_backup_files(
    client: AsyncClient,
    test_admin: User,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """管理员可以校验备份并下载数据库快照。"""
    from app.api import admin as admin_api

    media_root = tmp_path / "media"
    backup_root = tmp_path / "backups"
    media_root.mkdir()
    backup_root.mkdir()

    monkeypatch.setattr(admin_api, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(admin_api, "BACKUP_ROOT", backup_root)

    create_response = await client.post(
        "/api/v1/admin/backups",
        headers=auth_headers(test_admin),
    )
    assert create_response.status_code == 200
    backup_id = create_response.json()["backup_id"]

    verify_response = await client.post(
        f"/api/v1/admin/backups/{backup_id}/verify",
        headers=auth_headers(test_admin),
    )
    assert verify_response.status_code == 200
    verify_payload = verify_response.json()
    assert verify_payload["status"] == "valid"
    assert {item["label"] for item in verify_payload["checks"]} == {
        "manifest",
        "database",
        "media",
    }

    download_response = await client.get(
        f"/api/v1/admin/backups/{backup_id}/download/database",
        headers=auth_headers(test_admin),
    )
    assert download_response.status_code == 200
    assert download_response.headers["content-disposition"].endswith(
        f'{backup_id}-database.json"'
    )
    assert download_response.json()["format"] == "nezha-family-json-snapshot-v1"
