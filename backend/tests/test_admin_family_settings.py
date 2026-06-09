"""
家庭设置 API 测试。
"""
import pytest
from httpx import AsyncClient

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
    assert update_payload["background_image_url"].startswith(f"{raw_background_url}?token=")
    assert "expired" not in update_payload["background_image_url"]

    get_response = await client.get(
        "/api/v1/admin/family-settings",
        headers=auth_headers(test_user),
    )

    assert get_response.status_code == 200
    get_payload = get_response.json()
    assert get_payload["background_image_url"].startswith(f"{raw_background_url}?token=")
    assert "expired" not in get_payload["background_image_url"]
