"""
家庭设置 API 测试。
"""

import pytest
from io import BytesIO
from pathlib import Path
from httpx import AsyncClient

from app.core import media_utils
from app.core.security import create_access_token
from app.models.user import User


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(data={"user_id": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_family_settings_signs_local_background_image_url(
    client: AsyncClient,
    test_admin: User,
    test_user: User,
):
    """本地媒体背景图响应时带签名，持久化时不保存旧 token。"""
    raw_background_url = "/media/backgrounds/family.jpg"

    update_response = await client.put(
        "/api/v1/admin/family-settings",
        headers=auth_headers(test_admin),
        json={
            "family_name": "测试家庭",
            "tagline": "私有空间",
            "theme_color": "#f8d9b7",
            "accent_color": "#d94d30",
            "background_image_url": f"{raw_background_url}?token=expired",
        },
    )

    assert update_response.status_code == 200
    update_payload = update_response.json()
    assert update_payload["background_image_url"].startswith(
        f"{raw_background_url}?token="
    )
    assert "expired" not in update_payload["background_image_url"]

    get_response = await client.get(
        "/api/v1/admin/family-settings",
        headers=auth_headers(test_user),
    )

    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["background_image_url"].startswith(
        f"{raw_background_url}?token="
    )
    assert "expired" not in get_payload["background_image_url"]


@pytest.mark.asyncio
async def test_family_settings_signs_nested_theme_assets_and_logo(
    client: AsyncClient,
    test_admin: User,
    test_user: User,
):
    """主题资产响应时递归签名，持久化请求中的旧 token 不会回显。"""
    raw_logo_url = "/media/theme/logo.png"
    raw_cursor_url = "/media/theme/cursor.gif"
    raw_ornament_url = "/media/theme/knot.webp"

    response = await client.put(
        "/api/v1/admin/family-settings",
        headers=auth_headers(test_admin),
        json={
            "family_name": "主题家庭",
            "tagline": "私有空间",
            "theme_color": "#f6f1e8",
            "accent_color": "#c9432f",
            "background_image_url": "/media/theme/background.jpg?token=expired",
            "logo_url": f"{raw_logo_url}?token=expired",
            "theme_assets": {
                "backgrounds": [
                    {
                        "id": "bg-1",
                        "url": "/media/theme/background.jpg?token=expired",
                        "label": "客厅",
                        "enabled": True,
                    }
                ],
                "cursor": {
                    "url": f"{raw_cursor_url}?token=expired",
                    "enabled": True,
                    "size": 88,
                },
                "ornaments": [
                    {
                        "id": "orn-1",
                        "url": f"{raw_ornament_url}?token=expired",
                        "position": "top-right",
                        "enabled": True,
                        "size": 96,
                        "opacity": 0.7,
                    }
                ],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["logo_url"].startswith(f"{raw_logo_url}?token=")
    assert payload["theme_assets"]["cursor"]["url"].startswith(
        f"{raw_cursor_url}?token="
    )
    assert payload["theme_assets"]["ornaments"][0]["url"].startswith(
        f"{raw_ornament_url}?token="
    )
    assert "expired" not in str(payload["theme_assets"])

    get_response = await client.get(
        "/api/v1/admin/family-settings",
        headers=auth_headers(test_user),
    )

    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["theme_assets"]["backgrounds"][0]["url"].startswith(
        "/media/theme/background.jpg?token="
    )
    assert "expired" not in str(get_payload)


@pytest.mark.asyncio
async def test_family_settings_rejects_non_local_theme_asset_urls(
    client: AsyncClient,
    test_admin: User,
):
    """主题资产不能引用外链、data URL 或脚本 URL。"""
    response = await client.put(
        "/api/v1/admin/family-settings",
        headers=auth_headers(test_admin),
        json={
            "family_name": "测试家庭",
            "logo_url": "https://example.com/logo.png",
            "theme_assets": {
                "cursor": {
                    "url": "data:image/gif;base64,AAAA",
                    "enabled": True,
                    "size": 64,
                }
            },
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_theme_asset_upload_is_admin_only_and_preserves_gif(
    client: AsyncClient,
    test_admin: User,
    test_user: User,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """主题资产上传仅管理员可用，GIF 原文件不进入压缩队列。"""
    media_root = tmp_path / "media"
    media_root.mkdir()
    monkeypatch.setattr(media_utils, "MEDIA_ROOT", media_root)

    gif_bytes = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"

    member_response = await client.post(
        "/api/v1/admin/theme-assets/upload?kind=cursor",
        headers=auth_headers(test_user),
        files={"files": ("cursor.gif", BytesIO(gif_bytes), "image/gif")},
    )
    assert member_response.status_code == 403

    admin_response = await client.post(
        "/api/v1/admin/theme-assets/upload?kind=cursor",
        headers=auth_headers(test_admin),
        files={"files": ("cursor.gif", BytesIO(gif_bytes), "image/gif")},
    )
    assert admin_response.status_code == 200
    uploaded = admin_response.json()["files"][0]
    assert uploaded["type"] == "image"
    assert uploaded["raw_url"].endswith(".gif")
    assert (
        media_root / uploaded["raw_url"].removeprefix("/media/")
    ).read_bytes() == gif_bytes
