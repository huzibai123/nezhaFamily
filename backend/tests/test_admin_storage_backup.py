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

    async def fake_redis_available() -> bool:
        return False

    monkeypatch.setattr(admin_api, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(admin_api, "BACKUP_ROOT", backup_root)
    monkeypatch.setattr(admin_api, "is_redis_available", fake_redis_available)

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
    assert payload["runtime"]["database_available"] is True
    assert payload["runtime"]["redis_available"] is False
    assert payload["runtime"]["celery_broker_configured"] is True
    assert payload["runtime"]["celery_result_backend_configured"] is True
    assert "task_time_limit_seconds" in payload["runtime"]["task_timeouts"]
    assert payload["runtime"]["media_trash_retention_days"] >= 1
    assert payload["backups"]["recent"] == []
    assert payload["recent_comments"][0]["content"] == "一条最近评论"
    assert payload["recent_media"][0]["uploader_username"] == test_admin.username
    assert payload["upload_warnings"][0]["warning"]


@pytest.mark.asyncio
async def test_admin_overview_rejects_member_user(
    client: AsyncClient,
    test_user: User,
):
    """管理员概览只允许管理员访问。"""
    response = await client.get(
        "/api/v1/admin/overview",
        headers=auth_headers(test_user),
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_member_surfaces_hide_system_users(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
    test_user: User,
):
    """管理员成员列表和概览最近成员不展示 AI 系统用户。"""
    system_user = User(
        username="ai_hidden",
        email="ai_hidden@ai.nezha.local",
        password_hash="!",
        role="member",
        is_system=True,
        system_type="ai_persona",
    )
    db.add(system_user)
    await db.flush()
    system_post = Post(author_id=system_user.id, content="系统用户动态", media_urls=[])
    db.add(system_post)
    await db.commit()

    users_response = await client.get(
        "/api/v1/admin/users",
        headers=auth_headers(test_admin),
    )
    assert users_response.status_code == 200
    usernames = {item["username"] for item in users_response.json()}
    assert test_user.username in usernames
    assert system_user.username not in usernames

    overview_response = await client.get(
        "/api/v1/admin/overview",
        headers=auth_headers(test_admin),
    )
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert overview_payload["user_count"] == 2
    recent_member_names = {
        item["username"] for item in overview_payload["recent_members"]
    }
    recent_posting_names = {
        item["username"] for item in overview_payload["recent_posting_members"]
    }
    assert system_user.username not in recent_member_names
    assert system_user.username not in recent_posting_names


@pytest.mark.asyncio
async def test_admin_cannot_edit_or_regenerate_invite_for_system_user(
    client: AsyncClient,
    db: AsyncSession,
    test_admin: User,
):
    """系统用户不应被成员管理接口当作真实家庭成员操作。"""
    system_user = User(
        username="ai_locked",
        email="ai_locked@ai.nezha.local",
        password_hash="!",
        role="member",
        is_system=True,
        system_type="ai_persona",
    )
    db.add(system_user)
    await db.commit()
    await db.refresh(system_user)

    edit_response = await client.patch(
        f"/api/v1/admin/users/{system_user.id}",
        headers=auth_headers(test_admin),
        json={"role_in_family": "不应修改"},
    )
    invite_response = await client.post(
        f"/api/v1/admin/users/{system_user.id}/invite-code",
        headers=auth_headers(test_admin),
    )

    assert edit_response.status_code == 404
    assert invite_response.status_code == 404


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
