"""
安全与认证模块
提供密码哈希、JWT Token 生成与验证功能
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

# 密码哈希上下文（使用 bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer 认证方案
security = HTTPBearer()


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

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
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


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
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

    token = credentials.credentials
    payload = decode_access_token(token)

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
