"""
媒体处理任务测试。
"""
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from app.tasks import media_processing


def test_compress_image_updates_primary_media_file(
    tmp_path: Path,
    monkeypatch,
):
    """压缩任务生成的文件应成为数据库记录主文件，而不是无人引用的派生物。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    original_path = media_root / "wide.png"
    Image.new("RGB", (2400, 1200), (220, 80, 60)).save(original_path)

    media = SimpleNamespace(file_type="image", file_path="/media/wide.png")
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

    optimized_path = media_root / "optimized_wide.jpg"
    assert result["status"] == "success"
    assert result["file_path"] == "/media/optimized_wide.jpg"
    assert optimized_path.exists()
    assert not original_path.exists()
    assert updates["file_path"] == "/media/optimized_wide.jpg"
    assert updates["mime_type"] == "image/jpeg"
    assert updates["width"] == 1920
    assert updates["height"] == 960
    assert ThumbnailTaskStub.called_with == "00000000-0000-0000-0000-000000000001"
