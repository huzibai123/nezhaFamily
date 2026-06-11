"""
媒体处理任务测试。
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.media import MediaFile
from app.models.user import User
from app.tasks import media_processing


def test_compress_image_keeps_primary_media_url_stable(
    tmp_path: Path,
    monkeypatch,
):
    """压缩任务不应替换主文件 URL，避免上传响应 raw_url 断链。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    original_path = media_root / "wide.jpg"
    Image.new("RGB", (2400, 1200), (220, 80, 60)).save(original_path)

    media = SimpleNamespace(
        file_type="image", file_path="/media/wide.jpg", mime_type="image/jpeg"
    )
    updates: dict[str, object] = {}

    async def fake_get_media_by_id(media_id: str):
        return media

    async def fake_update_media_after_compression(media_id: str, **kwargs):
        updates.update(kwargs)

    class ThumbnailTaskStub:
        called_with: str | None = None

        @classmethod
        def delay(cls, media_id: str):
            cls.called_with = media_id

    monkeypatch.setattr(media_processing, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(media_processing, "get_media_by_id", fake_get_media_by_id)
    monkeypatch.setattr(
        media_processing,
        "update_media_after_compression",
        fake_update_media_after_compression,
    )
    monkeypatch.setattr(media_processing, "generate_thumbnail", ThumbnailTaskStub)

    result = media_processing.compress_image.run("00000000-0000-0000-0000-000000000001")

    assert result["status"] == "success"
    assert result["file_path"] == "/media/wide.jpg"
    assert original_path.exists()
    assert updates["file_path"] == "/media/wide.jpg"
    assert updates["mime_type"] == "image/jpeg"
    assert updates["width"] == 1920
    assert updates["height"] == 960
    assert ThumbnailTaskStub.called_with == "00000000-0000-0000-0000-000000000001"


def test_compress_image_preserves_transparent_png(
    tmp_path: Path,
    monkeypatch,
):
    """透明 PNG 保留原始文件，不转成 JPEG。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    original_path = media_root / "badge.png"
    Image.new("RGBA", (128, 96), (220, 80, 60, 120)).save(original_path)
    original_bytes = original_path.read_bytes()

    media = SimpleNamespace(
        file_type="image", file_path="/media/badge.png", mime_type="image/png"
    )
    updates: dict[str, object] = {}

    async def fake_get_media_by_id(media_id: str):
        return media

    async def fake_update_media_after_compression(media_id: str, **kwargs):
        updates.update(kwargs)

    class ThumbnailTaskStub:
        called_with: str | None = None

        @classmethod
        def delay(cls, media_id: str):
            cls.called_with = media_id

    monkeypatch.setattr(media_processing, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(media_processing, "get_media_by_id", fake_get_media_by_id)
    monkeypatch.setattr(
        media_processing,
        "update_media_after_compression",
        fake_update_media_after_compression,
    )
    monkeypatch.setattr(media_processing, "generate_thumbnail", ThumbnailTaskStub)

    result = media_processing.compress_image.run("00000000-0000-0000-0000-000000000001")

    assert result["status"] == "success"
    assert result["file_path"] == "/media/badge.png"
    assert result["preserved"] is True
    assert original_path.read_bytes() == original_bytes
    assert updates["mime_type"] == "image/png"
    assert ThumbnailTaskStub.called_with == "00000000-0000-0000-0000-000000000001"


def test_compress_image_rejects_path_traversal(
    tmp_path: Path,
    monkeypatch,
):
    """媒体任务中的路径穿越必须被拒绝，不能触碰 MEDIA_ROOT 外文件。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    outside_path = tmp_path / "outside.jpg"
    outside_path.write_bytes(b"outside")

    media = SimpleNamespace(
        file_type="image",
        file_path="/media/../outside.jpg",
        mime_type="image/jpeg",
    )

    async def fake_get_media_by_id(media_id: str):
        return media

    monkeypatch.setattr(media_processing, "MEDIA_ROOT", media_root)
    monkeypatch.setattr(media_processing, "get_media_by_id", fake_get_media_by_id)

    result = media_processing.compress_image.run("00000000-0000-0000-0000-000000000001")

    assert result == {"status": "error", "reason": "unsafe_media_path"}
    assert outside_path.read_bytes() == b"outside"


@pytest.mark.asyncio
async def test_cleanup_expired_media_trash_only_deletes_expired_soft_deleted_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    test_engine,
    db: AsyncSession,
    test_user: User,
):
    """回收站清理只删除超过保留期的软删除媒体文件和 DB 记录。"""
    media_root = tmp_path / "media"
    thumbnails_dir = media_root / "thumbnails"
    thumbnails_dir.mkdir(parents=True)
    monkeypatch.setattr(media_processing, "MEDIA_ROOT", media_root)

    TaskTestSession = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    monkeypatch.setattr(media_processing, "TaskAsyncSession", TaskTestSession)

    expired_path = media_root / "expired.jpg"
    expired_thumbnail_path = thumbnails_dir / "expired.jpg"
    recent_path = media_root / "recent.jpg"
    active_path = media_root / "active.jpg"
    for path in [expired_path, expired_thumbnail_path, recent_path, active_path]:
        path.write_bytes(path.name.encode())

    now = datetime.now(timezone.utc)
    expired_media = MediaFile(
        id=uuid4(),
        uploader_id=test_user.id,
        file_type="image",
        file_path="/media/expired.jpg",
        thumbnail_path="/media/thumbnails/expired.jpg",
        deleted_at=now - timedelta(days=31),
    )
    recent_media = MediaFile(
        id=uuid4(),
        uploader_id=test_user.id,
        file_type="image",
        file_path="/media/recent.jpg",
        deleted_at=now - timedelta(days=5),
    )
    active_media = MediaFile(
        id=uuid4(),
        uploader_id=test_user.id,
        file_type="image",
        file_path="/media/active.jpg",
    )
    db.add_all([expired_media, recent_media, active_media])
    await db.commit()

    cutoff = now - timedelta(days=30)
    expired_records = await media_processing.fetch_expired_trashed_media(cutoff)
    record_ids, file_stats = media_processing.delete_expired_trashed_media_files(
        expired_records
    )
    deleted_db_records = await media_processing.delete_expired_trashed_media_records(
        record_ids
    )

    assert [record.id for record in expired_records] == [expired_media.id]
    assert file_stats["deleted_files"] == 2
    assert file_stats["skipped_records"] == 0
    assert deleted_db_records == 1

    assert not expired_path.exists()
    assert not expired_thumbnail_path.exists()
    assert recent_path.exists()
    assert active_path.exists()

    remaining_ids = set(await db.scalars(select(MediaFile.id)))
    assert expired_media.id not in remaining_ids
    assert recent_media.id in remaining_ids
    assert active_media.id in remaining_ids


def test_cleanup_expired_media_trash_task_uses_default_retention(monkeypatch):
    """清理任务可手动调用，默认保留 30 天。"""
    cutoff_seen: datetime | None = None
    deleted_record_id = uuid4()

    async def fake_fetch_expired_trashed_media(cutoff: datetime):
        nonlocal cutoff_seen
        cutoff_seen = cutoff
        return [
            media_processing.TrashMediaRecord(
                id=deleted_record_id,
                file_path="/media/expired.jpg",
            )
        ]

    def fake_delete_expired_trashed_media_files(records):
        assert records[0].id == deleted_record_id
        return [deleted_record_id], {
            "candidate_records": 1,
            "deleted_files": 1,
            "missing_files": 0,
            "skipped_records": 0,
            "unsafe_record_ids": [],
        }

    async def fake_delete_expired_trashed_media_records(media_ids):
        assert media_ids == [deleted_record_id]
        return 1

    monkeypatch.delenv("MEDIA_TRASH_RETENTION_DAYS", raising=False)
    monkeypatch.setattr(
        media_processing,
        "fetch_expired_trashed_media",
        fake_fetch_expired_trashed_media,
    )
    monkeypatch.setattr(
        media_processing,
        "delete_expired_trashed_media_files",
        fake_delete_expired_trashed_media_files,
    )
    monkeypatch.setattr(
        media_processing,
        "delete_expired_trashed_media_records",
        fake_delete_expired_trashed_media_records,
    )

    result = media_processing.cleanup_expired_media_trash.run()

    assert result["status"] == "success"
    assert result["retention_days"] == 30
    assert result["deleted_db_records"] == 1
    assert result["deleted_files"] == 1
    assert cutoff_seen is not None


def test_media_trash_retention_rejects_manual_zero_days():
    """手动传入 0 天保留期会立即失败，避免误删刚进入回收站的文件。"""
    with pytest.raises(ValueError, match="retention_days must be at least 1"):
        media_processing.get_media_trash_retention_days(0)


def test_media_trash_retention_env_zero_falls_back_to_default(monkeypatch):
    """环境变量配置为 0 时回退默认值，避免启动后执行危险清理窗口。"""
    monkeypatch.setenv("MEDIA_TRASH_RETENTION_DAYS", "0")

    assert (
        media_processing.get_media_trash_retention_days()
        == media_processing.DEFAULT_MEDIA_TRASH_RETENTION_DAYS
    )


def test_cleanup_expired_media_trash_has_task_timeout():
    """媒体回收站清理任务必须有局部超时，避免长时间占用 worker。"""
    assert media_processing.cleanup_expired_media_trash.time_limit == 3600
    assert media_processing.cleanup_expired_media_trash.soft_time_limit == 3300


def test_cleanup_expired_media_trash_skips_unsafe_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """回收站记录包含路径穿越时整条跳过，不删除文件也不允许删 DB。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    safe_path = media_root / "safe.jpg"
    safe_path.write_bytes(b"safe")
    unsafe_record_id = uuid4()

    monkeypatch.setattr(media_processing, "MEDIA_ROOT", media_root)

    record_ids, stats = media_processing.delete_expired_trashed_media_files(
        [
            media_processing.TrashMediaRecord(
                id=unsafe_record_id,
                file_path="/media/safe.jpg",
                thumbnail_path="/media/../outside.jpg",
            )
        ]
    )

    assert record_ids == []
    assert stats["skipped_records"] == 1
    assert stats["unsafe_record_ids"] == [str(unsafe_record_id)]
    assert safe_path.read_bytes() == b"safe"
