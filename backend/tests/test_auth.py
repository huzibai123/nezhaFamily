"""
认证 API 测试
"""
import pytest
from httpx import AsyncClient
from redis.exceptions import ConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


class FakeRedis:
    def __init__(self):
        self.values: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    async def get(self, key: str):
        value = self.values.get(key)
        return str(value) if value is not None else None

    async def incr(self, key: str):
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    async def expire(self, key: str, seconds: int):
        self.expirations[key] = seconds
        return True

    async def delete(self, key: str):
        self.values.pop(key, None)
        return 1


class FailingRedis:
    async def get(self, key: str):
        raise ConnectionError("redis unavailable")

    async def incr(self, key: str):
        raise ConnectionError("redis unavailable")

    async def expire(self, key: str, seconds: int):
        raise ConnectionError("redis unavailable")

    async def delete(self, key: str):
        raise ConnectionError("redis unavailable")


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, test_admin: User):
    """测试用户注册成功"""
    response = await client.post(
        "/api/v1/register",
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
            "invite_code": "TEST_ADMIN_INVITE",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "newuser"
    assert data["user"]["email"] == "newuser@test.com"
    assert data["user"]["role"] == "member"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_admin: User):
    """测试用户登录成功"""
    response = await client.post(
        "/api/v1/login",
        json={
            "username": "testadmin",
            "password": "admin123456",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testadmin"


@pytest.mark.asyncio
async def test_register_invalid_invite_code(client: AsyncClient):
    """测试无效邀请码注册失败"""
    response = await client.post(
        "/api/v1/register",
        json={
            "username": "baduser",
            "email": "bad@test.com",
            "password": "password123",
            "invite_code": "INVALID_CODE",
        },
    )

    assert response.status_code == 400
    assert "邀请码" in response.json()["detail"]


@pytest.mark.asyncio
async def test_lookup_invite_code_success(
    client: AsyncClient,
    test_admin: User,
    db: AsyncSession,
):
    """测试公开查询有效邀请码。"""
    test_admin.role_in_family = "爸爸"
    await db.commit()

    response = await client.get("/api/v1/invites/TEST_ADMIN_INVITE")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["inviter_username"] == "testadmin"
    assert data["inviter_role_in_family"] == "爸爸"
    assert "可用" in data["message"]


@pytest.mark.asyncio
async def test_lookup_invite_code_invalid(client: AsyncClient):
    """测试公开查询无效邀请码不会抛 4xx。"""
    response = await client.get("/api/v1/invites/INVALID_CODE")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["inviter_username"] is None
    assert "邀请码" in data["message"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_admin: User):
    """测试错误密码登录失败"""
    response = await client.post(
        "/api/v1/login",
        json={
            "username": "testadmin",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_rate_limit_uses_shared_redis_counter(
    client: AsyncClient,
    test_admin: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试登录限速写入 Redis 共享计数器。"""
    from app.api import auth as auth_api

    fake_redis = FakeRedis()
    monkeypatch.setattr(auth_api, "redis_client", fake_redis)
    headers = {"X-Forwarded-For": "203.0.113.10"}

    for _ in range(auth_api.MAX_LOGIN_ATTEMPTS):
        response = await client.post(
            "/api/v1/login",
            headers=headers,
            json={
                "username": "testadmin",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    locked_response = await client.post(
        "/api/v1/login",
        headers=headers,
        json={
            "username": "testadmin",
            "password": "admin123456",
        },
    )
    assert locked_response.status_code == 429
    assert fake_redis.expirations["login_attempts:203.0.113.10"] == auth_api.LOCKOUT_SECONDS


@pytest.mark.asyncio
async def test_login_does_not_500_when_redis_is_unavailable(
    client: AsyncClient,
    test_admin: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """Redis 临时不可用时登录限流 fail-open，不应把登录接口打成 500。"""
    from app.api import auth as auth_api

    monkeypatch.setattr(auth_api, "redis_client", FailingRedis())

    response = await client.post(
        "/api/v1/login",
        json={
            "username": "testadmin",
            "password": "admin123456",
        },
    )

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "testadmin"


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user: User):
    """测试获取当前用户信息"""
    # 先登录获取 token
    login_response = await client.post(
        "/api/v1/login",
        json={
            "username": "testuser",
            "password": "user123456",
        },
    )
    token = login_response.json()["access_token"]

    # 使用 token 获取用户信息
    response = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "user@test.com"
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_get_other_user_profile_does_not_expose_invite_code(
    client: AsyncClient,
    test_admin: User,
    test_user: User,
):
    """测试查看他人档案不会泄露邀请码字段。"""
    token = create_access_token({"user_id": str(test_user.id)})

    response = await client.get(
        f"/api/v1/users/{test_admin.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testadmin"
    assert data["email"] == "admin@test.com"
    assert "invite_code" not in data
    assert "invited_by" not in data
