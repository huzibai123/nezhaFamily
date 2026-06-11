"""
认证相关 API 路由
包含注册、登录、获取用户信息等功能
"""
import logging
from typing import Any, Optional
from uuid import UUID
import secrets

from fastapi import APIRouter, Depends, HTTPException, status, Request
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserProfile,
    TokenResponse,
    InviteLookupResponse,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user_id,
)
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# 登录/邀请码限速：Redis 共享计数器（IP -> 失败次数）
redis_client: Any | None = None
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 分钟锁定
MAX_INVITE_LOOKUP_ATTEMPTS = 5
INVITE_LOOKUP_WINDOW_SECONDS = 60


# ==================== 辅助函数 ====================

async def get_user_by_username_or_email(
    db: AsyncSession, username: str
) -> Optional[User]:
    """根据用户名或邮箱查找用户"""
    stmt = select(User).where(
        or_(User.username == username, User.email == username)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """根据 ID 查找用户"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def verify_invite_code(db: AsyncSession, code: str) -> Optional[User]:
    """
    验证邀请码是否有效
    返回邀请者的 User 对象
    """
    stmt = select(User).where(User.invite_code == code)
    result = await db.execute(stmt)
    inviter = result.scalar_one_or_none()

    if not inviter:
        return None

    # TODO: 如果需要邀请码过期功能，可以在这里添加逻辑
    # 当前版本邀请码永久有效
    return inviter


def generate_invite_code() -> str:
    """生成随机邀请码"""
    return secrets.token_urlsafe(settings.INVITE_CODE_LENGTH)


def get_client_ip(request: Request) -> str:
    """获取客户端 IP，仅在显式配置可信代理数量后信任 X-Forwarded-For。"""
    direct_client_ip = request.client.host if request.client else "unknown"
    if settings.TRUSTED_PROXY_COUNT <= 0:
        return direct_client_ip

    forwarded_for = request.headers.get("x-forwarded-for")
    if not forwarded_for:
        return direct_client_ip

    forwarded_chain = [
        forwarded_ip.strip()
        for forwarded_ip in forwarded_for.split(",")
        if forwarded_ip.strip()
    ]
    if not forwarded_chain:
        return direct_client_ip

    if len(forwarded_chain) > settings.TRUSTED_PROXY_COUNT:
        return forwarded_chain[-(settings.TRUSTED_PROXY_COUNT + 1)]
    return forwarded_chain[0]


def login_attempt_key(client_ip: str) -> str:
    return f"login_attempts:{client_ip}"


def invite_lookup_key(client_ip: str) -> str:
    return f"invite_lookup:{client_ip}"


def get_redis_client(request: Request):
    """从应用生命周期管理的 Redis client 获取登录限流计数器。"""
    if redis_client is not None:
        return redis_client

    return getattr(request.app.state, "redis_client", None)


async def ensure_login_not_locked(request: Request, client_ip: str) -> None:
    client = get_redis_client(request)
    if client is None:
        logger.warning("登录限流 Redis 尚未初始化，跳过锁定检查")
        return

    try:
        attempts = await client.get(login_attempt_key(client_ip))
    except RedisError as exc:
        logger.warning("登录限流 Redis 不可用，跳过锁定检查: %s", exc)
        return

    if int(attempts or 0) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过多，请 {LOCKOUT_SECONDS} 秒后再试",
        )


async def record_failed_login(request: Request, client_ip: str) -> None:
    client = get_redis_client(request)
    if client is None:
        logger.warning("登录限流 Redis 尚未初始化，跳过失败计数")
        return

    key = login_attempt_key(client_ip)
    try:
        attempts = await client.incr(key)
        if attempts == 1:
            await client.expire(key, LOCKOUT_SECONDS)
    except RedisError as exc:
        logger.warning("登录限流 Redis 不可用，跳过失败计数: %s", exc)


async def clear_failed_logins(request: Request, client_ip: str) -> None:
    client = get_redis_client(request)
    if client is None:
        logger.warning("登录限流 Redis 尚未初始化，跳过清理计数")
        return

    try:
        await client.delete(login_attempt_key(client_ip))
    except RedisError as exc:
        logger.warning("登录限流 Redis 不可用，跳过清理计数: %s", exc)


async def ensure_invite_lookup_not_limited(request: Request, client_ip: str) -> None:
    client = get_redis_client(request)
    if client is None:
        logger.warning("邀请码查询限流 Redis 尚未初始化，跳过计数")
        return

    key = invite_lookup_key(client_ip)
    try:
        attempts = await client.incr(key)
        if attempts == 1:
            await client.expire(key, INVITE_LOOKUP_WINDOW_SECONDS)
    except RedisError as exc:
        logger.warning("邀请码查询限流 Redis 不可用，跳过计数: %s", exc)
        return

    if attempts > MAX_INVITE_LOOKUP_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"查询过于频繁，请 {INVITE_LOOKUP_WINDOW_SECONDS} 秒后再试",
        )


# ==================== API 路由 ====================

@router.get("/invites/{invite_code}", response_model=InviteLookupResponse)
async def lookup_invite(
    invite_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    查询邀请码是否可用

    无效邀请码也返回 200，方便注册页展示友好提示。
    """
    await ensure_invite_lookup_not_limited(request, get_client_ip(request))

    inviter = await verify_invite_code(db, invite_code)
    if not inviter:
        return InviteLookupResponse(
            valid=False,
            message="邀请码无效或已过期",
        )

    return InviteLookupResponse(
        valid=True,
        message="邀请码可用",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册

    - 需要有效的邀请码
    - 用户名和邮箱不能重复
    - 密码会自动加密存储
    - 注册成功后自动登录，返回 JWT Token
    """
    # 1. 验证邀请码
    inviter = await verify_invite_code(db, user_data.invite_code)
    if not inviter:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀请码无效或已过期",
        )

    # 2. 检查用户名是否已存在
    existing_user = await get_user_by_username_or_email(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该信息已被使用",
        )

    # 3. 检查邮箱是否已存在
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该信息已被使用",
        )

    # 4. 创建新用户
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        invited_by=inviter.id,
        invite_code=generate_invite_code(),  # 生成该用户自己的邀请码
        role="member",  # 默认角色
    )

    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该信息已被使用",
        )
    await db.refresh(new_user)

    # 5. 生成 JWT Token
    access_token = create_access_token(data={"user_id": str(new_user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录

    - 支持用户名或邮箱登录
    - 同一 IP 密码错误超过 5 次会被锁定 5 分钟
    """
    client_ip = get_client_ip(request)
    await ensure_login_not_locked(request, client_ip)

    # 1. 查找用户
    user = await get_user_by_username_or_email(db, login_data.username)
    if not user:
        await record_failed_login(request, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 2. 验证密码
    if not verify_password(login_data.password, user.password_hash):
        await record_failed_login(request, client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 登录成功，清除该 IP 的失败记录
    await clear_failed_logins(request, client_ip)

    # 3. 生成 JWT Token
    access_token = create_access_token(data={"user_id": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前登录用户的详细信息

    需要在请求头中携带 JWT Token:
    Authorization: Bearer <token>
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    return UserProfile.model_validate(user)


@router.post("/logout")
async def logout(user_id: UUID = Depends(get_current_user_id)):
    """
    用户登出

    由于使用 JWT，服务端无状态，实际登出由客户端删除 Token 实现
    此接口主要用于记录登出日志（可选）
    """
    # TODO: 可以在这里添加登出日志记录
    return {"message": "登出成功"}


# 注意：GET /users/{user_id} 已在 app.api.users 实现（返回更详细的 UserProfile）
# 此处删除重复路由以避免冲突
