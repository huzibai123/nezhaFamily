#!/usr/bin/env python3
"""
兼容旧文档的管理员创建脚本。

首次部署推荐使用交互式脚本：
    python init_admin.py

非交互环境可设置：
    INITIAL_ADMIN_USERNAME
    INITIAL_ADMIN_EMAIL
    INITIAL_ADMIN_PASSWORD
"""
import asyncio
import os
import secrets
import sys
from getpass import getpass

from sqlalchemy import or_, select

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User


def _read_value(
    env_name: str,
    prompt: str,
    *,
    default: str | None = None,
    required: bool = True,
    secret: bool = False,
) -> str:
    env_value = os.getenv(env_name)
    if env_value:
        return env_value.strip()

    if not sys.stdin.isatty():
        if default is not None:
            return default
        if required:
            raise RuntimeError(f"请设置 {env_name}，或改用交互式脚本 python init_admin.py")
        return ""

    if secret:
        value = getpass(prompt)
    else:
        value = input(prompt)

    value = value.strip()
    if value:
        return value
    if default is not None:
        return default
    if required:
        raise RuntimeError(f"{prompt.strip()} 不能为空")
    return ""


async def create_admin() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.role == "admin").limit(1))
        existing_admin = result.scalar_one_or_none()
        if existing_admin:
            print(f"管理员账号已存在: {existing_admin.username} ({existing_admin.email})")
            print("未创建新管理员，也不会覆盖已有管理员。")
            return

        username = _read_value(
            "INITIAL_ADMIN_USERNAME",
            "请输入管理员用户名 (默认: admin): ",
            default="admin",
        )
        email = _read_value("INITIAL_ADMIN_EMAIL", "请输入管理员邮箱: ")

        password = os.getenv("INITIAL_ADMIN_PASSWORD")
        if password is None:
            password = _read_value(
                "INITIAL_ADMIN_PASSWORD",
                "请输入管理员密码（至少6位）: ",
                secret=True,
            )
            if sys.stdin.isatty():
                password_confirm = getpass("请再次输入密码: ")
                if password != password_confirm:
                    raise RuntimeError("两次输入的密码不一致")

        if len(password) < 6:
            raise RuntimeError("管理员密码长度至少为 6 位")

        result = await session.execute(
            select(User.id).where(or_(User.username == username, User.email == email)).limit(1)
        )
        if result.scalar_one_or_none():
            raise RuntimeError("用户名或邮箱已被使用")

        invite_code = secrets.token_urlsafe(8)
        admin = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role="admin",
            invite_code=invite_code,
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("=" * 60)
        print("初始管理员创建成功")
        print("=" * 60)
        print(f"用户名: {admin.username}")
        print(f"邮箱: {admin.email}")
        print(f"邀请码: {admin.invite_code}")
        print("请妥善保管管理员密码和邀请码。")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(create_admin())
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
    except Exception as exc:
        print(f"创建失败: {exc}")
        sys.exit(1)
