"""
FastAPI 依赖注入函数
提供常用的依赖项，如当前用户、数据库会话等
"""
from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.core.security import get_current_user  # 复用 security.py 的实现


async def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    依赖注入函数：获取当前管理员用户
    仅管理员可以访问的路由使用此依赖

    使用方式:
        @app.post("/admin/invite-codes")
        async def create_invite_code(admin: User = Depends(get_current_active_admin)):
            return {"message": "仅管理员可访问"}

    Raises:
        HTTPException: 当前用户不是管理员
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    return current_user
