"""
安全与认证模块
提供密码哈希、JWT Token 生成与验证功能
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.exceptions import RedisError

from app.core.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

# 密码哈希上下文（使用 bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证方案
security = HTTPBearer()
redis_client = None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配哈希密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Access Token

    Args:
        data: 要编码到 token 中的数据（通常包含 user_id）
        expires_delta: 过期时间增量，默认使用配置中的值

    Returns:
        编码后的 JWT token 字符串
    """
    to_encode = data.copy()

    now = _utc_now()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": now, "jti": uuid4().hex})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码 JWT Access Token

    Args:
        token: JWT token 字符串

    Returns:
        解码后的数据字典

    Raises:
        HTTPException: token 无效或已过期
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _revoked_token_key(jti: str) -> str:
    return f"revoked_token:{jti}"


def _token_expiry_timestamp(payload: dict) -> int:
    exp = payload.get("exp")
    if isinstance(exp, int):
        return exp
    if isinstance(exp, float):
        return int(exp)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token 中缺少过期时间",
    )


def _token_jti(payload: dict) -> str:
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少会话标识",
        )
    return jti


def get_redis_client(request: Request):
    if redis_client is not None:
        return redis_client
    return getattr(request.app.state, "redis_client", None)


async def is_token_revoked(request: Request, payload: dict) -> bool:
    """检查 token 是否已被登出撤销；Redis 不可用时普通鉴权 fail-open。"""
    client = get_redis_client(request)
    if client is None:
        logger.warning("Token 撤销检查 Redis 尚未初始化，跳过黑名单检查")
        return False

    try:
        return bool(await client.exists(_revoked_token_key(_token_jti(payload))))
    except RedisError as exc:
        # Redis 不可用时普通鉴权有意 fail-open（可用性优先），
        # 登出黑名单可能短暂失效，但避免因 Redis 故障导致全站无法访问。
        logger.warning("Token 撤销检查 Redis 不可用，跳过黑名单检查: %s", exc)
        return False


async def revoke_token(request: Request, token: str) -> None:
    """把当前 token 加入 Redis 黑名单；失败时让调用方返回 503。"""
    payload = decode_access_token(token)
    jti = _token_jti(payload)
    expires_at = _token_expiry_timestamp(payload)
    ttl = max(1, expires_at - int(_utc_now().timestamp()))

    client = get_redis_client(request)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="登出服务暂时不可用",
        )

    try:
        await client.setex(_revoked_token_key(jti), ttl, "1")
    except RedisError as exc:
        logger.warning("写入 token 撤销黑名单失败: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="登出服务暂时不可用",
        ) from exc


async def get_current_token_payload(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    token = credentials.credentials
    payload = decode_access_token(token)
    if await is_token_revoked(request, payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    return credentials.credentials


async def get_current_user_id(
    payload: dict = Depends(get_current_token_payload),
):
    """
    依赖注入函数：从请求头中提取并验证 JWT token，返回当前用户 ID

    使用方式:
        @app.get("/protected")
        async def protected_route(user_id = Depends(get_current_user_id)):
            return {"user_id": user_id}

    Raises:
        HTTPException: token 无效、过期或缺少 user_id
    """
    from uuid import UUID

    user_id_str: Optional[str] = payload.get("user_id")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户信息",
        )

    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中用户 ID 格式无效",
        )

    return user_id



async def get_current_user(
    user_id = Depends(get_current_user_id),
    db = Depends(get_db),
):
    """
    获取当前用户的完整对象（需要数据库查询）

    使用方式:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"username": user.username}
    """
    from sqlalchemy import select
    from app.models.user import User

    # 查询用户
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return user
