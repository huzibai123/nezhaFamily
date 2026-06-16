"""
认证相关 API 路由
包含注册、登录、获取用户信息等功能
"""
import logging
import time
from typing import Any, Optional
from uuid import UUID
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserProfile,
    TokenResponse,
    InviteLookupResponse,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_token,
    get_current_user_id,
    revoke_token,
)
from app.core.config import settings
from app.api.users import user_profile_response, user_response

router = APIRouter()
logger = logging.getLogger(__name__)

# 登录/邀请码限速：Redis 共享计数器（IP -> 失败次数）
redis_client: Any | None = None
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 分钟锁定
MAX_INVITE_LOOKUP_ATTEMPTS = 5
INVITE_LOOKUP_WINDOW_SECONDS = 60
MAX_REGISTER_ATTEMPTS = 10  # 单 IP 注册窗口内上限（成功也计入）
REGISTER_WINDOW_SECONDS = 3600  # 注册限流窗口（1 小时）

# Redis 不可用时的进程内兜底：IP -> 失败/尝试时间戳列表（单 worker 内有效）
_login_attempts_memory: dict[str, list[float]] = {}
_register_attempts_memory: dict[str, list[float]] = {}


def _prune_memory_attempts(timestamps: list[float], window_seconds: int) -> list[float]:
    """按时间窗口裁剪过期的尝试时间戳，返回仍在窗口内的列表。"""
    cutoff = time.monotonic() - window_seconds
    return [ts for ts in timestamps if ts >= cutoff]


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
    返回邀请者的 User 对象；无效时返回 None

    有效条件（全部满足）：
      1. 邀请者存在；
      2. 邀请码未过期（invite_code_expires_at 为 NULL 表示永久，或大于当前 UTC 时间）；
      3. 邀请码使用次数未达上限（invite_code_uses < INVITE_CODE_MAX_USES）。
    """
    stmt = select(User).where(User.invite_code == code)
    result = await db.execute(stmt)
    inviter = result.scalar_one_or_none()

    if not inviter:
        return None

    # 过期校验：NULL 视为永久有效，向后兼容历史数据
    expires_at = inviter.invite_code_expires_at
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        return None

    # 使用次数校验
    if (inviter.invite_code_uses or 0) >= settings.INVITE_CODE_MAX_USES:
        return None

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


def register_attempt_key(client_ip: str) -> str:
    return f"register_attempts:{client_ip}"


def invite_lookup_key(client_ip: str) -> str:
    return f"invite_lookup:{client_ip}"


def get_redis_client(request: Request):
    """从应用生命周期管理的 Redis client 获取登录限流计数器。"""
    if redis_client is not None:
        return redis_client

    return getattr(request.app.state, "redis_client", None)


async def ensure_login_not_locked(request: Request, client_ip: str) -> None:
    client = get_redis_client(request)
    if client is not None:
        try:
            attempts = await client.get(login_attempt_key(client_ip))
        except RedisError as exc:
            logger.warning("登录限流 Redis 不可用，回退进程内内存计数: %s", exc)
        else:
            if int(attempts or 0) >= MAX_LOGIN_ATTEMPTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"登录尝试过多，请 {LOCKOUT_SECONDS} 秒后再试",
                )
            return

    # 进程内内存兜底（单 worker 内有效）
    recent = _prune_memory_attempts(
        _login_attempts_memory.get(client_ip, []), LOCKOUT_SECONDS
    )
    _login_attempts_memory[client_ip] = recent
    if len(recent) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过多，请 {LOCKOUT_SECONDS} 秒后再试",
        )


async def record_failed_login(request: Request, client_ip: str) -> None:
    client = get_redis_client(request)
    if client is not None:
        key = login_attempt_key(client_ip)
        try:
            attempts = await client.incr(key)
            if attempts == 1:
                await client.expire(key, LOCKOUT_SECONDS)
            return
        except RedisError as exc:
            logger.warning("登录限流 Redis 不可用，回退进程内内存计数: %s", exc)

    # 进程内内存兜底（单 worker 内有效）
    recent = _prune_memory_attempts(
        _login_attempts_memory.get(client_ip, []), LOCKOUT_SECONDS
    )
    recent.append(time.monotonic())
    _login_attempts_memory[client_ip] = recent


async def clear_failed_logins(request: Request, client_ip: str) -> None:
    client = get_redis_client(request)
    if client is not None:
        try:
            await client.delete(login_attempt_key(client_ip))
            return
        except RedisError as exc:
            logger.warning("登录限流 Redis 不可用，回退进程内内存清理: %s", exc)

    # 进程内内存兜底（单 worker 内有效）
    _login_attempts_memory.pop(client_ip, None)


async def ensure_register_not_limited(request: Request, client_ip: str) -> None:
    """注册限流：单 IP 窗口内（成功也计入）超过上限抛 429。Redis 不可用时进程内兜底。"""
    client = get_redis_client(request)
    if client is not None:
        key = register_attempt_key(client_ip)
        try:
            attempts = await client.incr(key)
            if attempts == 1:
                await client.expire(key, REGISTER_WINDOW_SECONDS)
        except RedisError as exc:
            logger.warning("注册限流 Redis 不可用，回退进程内内存计数: %s", exc)
        else:
            if attempts > MAX_REGISTER_ATTEMPTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"注册过于频繁，请 {REGISTER_WINDOW_SECONDS} 秒后再试",
                )
            return

    # 进程内内存兜底（单 worker 内有效）
    recent = _prune_memory_attempts(
        _register_attempts_memory.get(client_ip, []), REGISTER_WINDOW_SECONDS
    )
    recent.append(time.monotonic())
    _register_attempts_memory[client_ip] = recent
    if len(recent) > MAX_REGISTER_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"注册过于频繁，请 {REGISTER_WINDOW_SECONDS} 秒后再试",
        )


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
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册

    - 需要有效的邀请码（限次数 + 过期校验）
    - 同一 IP 注册次数超过上限会被限流（成功也计入）
    - 用户名和邮箱不能重复
    - 密码会自动加密存储
    - 注册成功后自动登录，返回 JWT Token
    """
    # 0. IP 限流（成功也计入，防止刷注册）
    await ensure_register_not_limited(request, get_client_ip(request))

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

    # 4. 创建新用户，并为其自己的邀请码设置过期时间
    new_invite_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.INVITE_CODE_EXPIRES_DAYS
    )
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        invited_by=inviter.id,
        invite_code=generate_invite_code(),  # 生成该用户自己的邀请码
        invite_code_expires_at=new_invite_expires_at,
        role="member",  # 默认角色
    )

    db.add(new_user)
    try:
        # 邀请者邀请码使用次数原子 +1（与新用户在同一事务提交）。
        # 注意：此处 execute 会触发 new_user 的 autoflush，唯一约束冲突也在此抛出，
        # 故 UPDATE 与 commit 必须同在 try 内，确保 IntegrityError 统一捕获为 400。
        await db.execute(
            update(User)
            .where(User.id == inviter.id)
            .values(invite_code_uses=User.invite_code_uses + 1)
        )
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
        user=user_response(new_user),
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
        user=user_response(user),
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

    return user_profile_response(user)


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(get_current_token),
    user_id: UUID = Depends(get_current_user_id),
):
    """
    用户登出

    当前 access token 会写入 Redis 黑名单，直到原始过期时间。
    """
    del user_id
    await revoke_token(request, token)
    return {"message": "登出成功"}


# 注意：GET /users/{user_id} 已在 app.api.users 实现（返回更详细的 UserProfile）
# 此处删除重复路由以避免冲突
