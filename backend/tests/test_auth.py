"""
认证 API 测试
"""
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from redis.exceptions import ConnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_access_token
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

    async def exists(self, key: str):
        return 1 if key in self.values else 0

    async def setex(self, key: str, seconds: int, value: str):
        self.values[key] = int(value)
        self.expirations[key] = seconds
        return True


class FailingRedis:
    async def get(self, key: str):
        raise ConnectionError("redis unavailable")

    async def incr(self, key: str):
        raise ConnectionError("redis unavailable")

    async def expire(self, key: str, seconds: int):
        raise ConnectionError("redis unavailable")

    async def delete(self, key: str):
        raise ConnectionError("redis unavailable")

    async def exists(self, key: str):
        raise ConnectionError("redis unavailable")

    async def setex(self, key: str, seconds: int, value: str):
        raise ConnectionError("redis unavailable")


@pytest.fixture(autouse=True)
def fail_open_auth_redis(monkeypatch: pytest.MonkeyPatch):
    """认证接口默认不依赖真实 Redis，限流专项测试会单独替换为 FakeRedis。"""
    from app.api import auth as auth_api
    from app.core import security as security_api

    monkeypatch.setattr(auth_api, "redis_client", FailingRedis())
    monkeypatch.setattr(security_api, "redis_client", FailingRedis())


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, test_admin: User):
    """测试用户注册成功"""
    response = await client.post(
        "/api/v1/register",
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "FamilyPass123",
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
            "password": "AdminPass123",
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
            "password": "FamilyPass123",
            "invite_code": "INVALID_CODE",
        },
    )

    assert response.status_code == 400
    assert "邀请码" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_rejects_weak_password(
    client: AsyncClient,
    test_admin: User,
):
    """注册密码必须满足统一强度策略。"""
    response = await client.post(
        "/api/v1/register",
        json={
            "username": "weakpassuser",
            "email": "weakpass@test.com",
            "password": "password",
            "invite_code": test_admin.invite_code,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "password"


@pytest.mark.asyncio
async def test_register_integrity_error_returns_400(
    client: AsyncClient,
    test_admin: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试注册提交时遇到唯一约束冲突会统一返回 400。"""
    from app.api import auth as auth_api

    monkeypatch.setattr(auth_api, "generate_invite_code", lambda: "TEST_ADMIN_INVITE")

    response = await client.post(
        "/api/v1/register",
        json={
            "username": "invitecollision",
            "email": "invitecollision@test.com",
            "password": "FamilyPass123",
            "invite_code": test_admin.invite_code,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "该信息已被使用"


@pytest.mark.asyncio
async def test_register_duplicate_username_and_email_use_same_message(
    client: AsyncClient,
    test_admin: User,
):
    """用户名或邮箱冲突返回同一文案，避免精确枚举邮箱注册状态。"""
    username_response = await client.post(
        "/api/v1/register",
        json={
            "username": test_admin.username,
            "email": "other-username-conflict@test.com",
            "password": "FamilyPass123",
            "invite_code": test_admin.invite_code,
        },
    )
    email_response = await client.post(
        "/api/v1/register",
        json={
            "username": "other_email_conflict",
            "email": test_admin.email,
            "password": "FamilyPass123",
            "invite_code": test_admin.invite_code,
        },
    )

    assert username_response.status_code == 400
    assert email_response.status_code == 400
    assert username_response.json()["detail"] == "该信息已被使用"
    assert email_response.json()["detail"] == "该信息已被使用"


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
    assert "inviter_username" not in data
    assert "inviter_role_in_family" not in data
    assert "可用" in data["message"]


@pytest.mark.asyncio
async def test_lookup_invite_code_invalid(client: AsyncClient):
    """测试公开查询无效邀请码不会抛 4xx。"""
    response = await client.get("/api/v1/invites/INVALID_CODE")

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "inviter_username" not in data
    assert "inviter_role_in_family" not in data
    assert "邀请码" in data["message"]


@pytest.mark.asyncio
async def test_lookup_invite_rate_limit_uses_redis_counter(
    client: AsyncClient,
    test_admin: User,
    monkeypatch: pytest.MonkeyPatch,
):
    """测试公开邀请码查询按客户端 IP 走 Redis 简单限流。"""
    from app.api import auth as auth_api

    fake_redis = FakeRedis()
    monkeypatch.setattr(auth_api, "redis_client", fake_redis)
    monkeypatch.setattr(auth_api, "MAX_INVITE_LOOKUP_ATTEMPTS", 2)
    monkeypatch.setattr(auth_api.settings, "TRUSTED_PROXY_COUNT", 1)
    headers = {"X-Forwarded-For": "203.0.113.30"}

    for _ in range(2):
        response = await client.get(
            f"/api/v1/invites/{test_admin.invite_code}",
            headers=headers,
        )
        assert response.status_code == 200

    limited_response = await client.get(
        f"/api/v1/invites/{test_admin.invite_code}",
        headers=headers,
    )

    assert limited_response.status_code == 429
    assert (
        fake_redis.expirations["invite_lookup:203.0.113.30"]
        == auth_api.INVITE_LOOKUP_WINDOW_SECONDS
    )


def test_invite_lookup_default_rate_limit_is_strict():
    """公开邀请码查询默认限流保持保守，降低枚举邀请码空间的吞吐。"""
    from app.api import auth as auth_api

    assert auth_api.MAX_INVITE_LOOKUP_ATTEMPTS == 5


def test_get_client_ip_only_trusts_x_forwarded_for_when_configured(
    monkeypatch: pytest.MonkeyPatch,
):
    """测试未配置可信代理时忽略 X-Forwarded-For。"""
    from app.api import auth as auth_api

    request = SimpleNamespace(
        headers={"x-forwarded-for": "203.0.113.10, 198.51.100.2"},
        client=SimpleNamespace(host="192.0.2.50"),
    )

    monkeypatch.setattr(auth_api.settings, "TRUSTED_PROXY_COUNT", 0)
    assert auth_api.get_client_ip(request) == "192.0.2.50"

    monkeypatch.setattr(auth_api.settings, "TRUSTED_PROXY_COUNT", 1)
    assert auth_api.get_client_ip(request) == "203.0.113.10"


def test_access_token_contains_session_claims(test_user: User):
    token = create_access_token({"user_id": str(test_user.id)})
    payload = decode_access_token(token)

    assert payload["user_id"] == str(test_user.id)
    assert payload["jti"]
    assert payload["iat"]
    assert payload["exp"]


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
    assert "用户名或密码错误" in response.json()["detail"]


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
    monkeypatch.setattr(auth_api.settings, "TRUSTED_PROXY_COUNT", 1)
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
            "password": "AdminPass123",
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
            "password": "AdminPass123",
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
            "password": "UserPass123",
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
async def test_logout_revokes_current_token(
    client: AsyncClient,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.core import security as security_api

    fake_redis = FakeRedis()
    monkeypatch.setattr(security_api, "redis_client", fake_redis)
    token = create_access_token({"user_id": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = await client.post("/api/v1/logout", headers=headers)
    me_response = await client.get("/api/v1/me", headers=headers)

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "登出成功"
    assert me_response.status_code == 401
    assert any(key.startswith("revoked_token:") for key in fake_redis.values)


@pytest.mark.asyncio
async def test_logout_returns_503_when_revocation_store_unavailable(
    client: AsyncClient,
    test_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    from app.core import security as security_api

    token = create_access_token({"user_id": str(test_user.id)})
    monkeypatch.setattr(security_api, "redis_client", FailingRedis())

    response = await client.post(
        "/api/v1/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 503


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
    # 邮箱最小披露：他人公开档案（UserPublicResponse）不再返回 email
    assert "email" not in data
    assert "invite_code" not in data
    assert "invited_by" not in data


@pytest.mark.asyncio
async def test_update_profile_avatar_stores_raw_and_returns_signed_url(
    client: AsyncClient,
    db: AsyncSession,
    test_user: User,
):
    """成员更新头像时数据库保存原始媒体路径，响应返回可访问签名地址。"""
    token = create_access_token({"user_id": str(test_user.id)})

    response = await client.put(
        f"/api/v1/users/{test_user.id}",
        json={"avatar_url": "/media/avatars/me.png?token=temporary"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["avatar_url"].startswith("/media/avatars/me.png?token=")

    await db.refresh(test_user)
    assert test_user.avatar_url == "/media/avatars/me.png"

    me_response = await client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["avatar_url"].startswith("/media/avatars/me.png?token=")
