"""
媒体处理任务测试。
"""

from pathlib import Path
from types import SimpleNamespace

from PIL import Image

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
