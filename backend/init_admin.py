#!/usr/bin/env python3
"""
初始化管理员账号脚本
用于首次部署时创建管理员账号
"""
import asyncio
import secrets
import sys
from getpass import getpass

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


async def create_admin():
    """创建管理员账号"""
    print("=" * 50)
    print("哪吒家庭 - 管理员账号初始化")
    print("=" * 50)
    print()

    # 检查是否已有管理员
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.role == "admin")
        result = await db.execute(stmt)
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"⚠️  管理员账号已存在: {existing_admin.username}")
            print(f"📧 邮箱: {existing_admin.email}")
            print(f"🎟️  邀请码: {existing_admin.invite_code}")
            print()
            choice = input("是否创建新的管理员账号？(y/N): ").strip().lower()
            if choice != "y":
                print("取消创建")
                return

        # 获取用户输入
        print()
        username = input("请输入管理员用户名 (默认: admin): ").strip() or "admin"
        email = input("请输入管理员邮箱: ").strip()

        if not email:
            print("❌ 邮箱不能为空")
            sys.exit(1)

        # 检查用户名和邮箱是否已存在
        stmt = select(User).where(
            (User.username == username) | (User.email == email)
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            print("❌ 用户名或邮箱已被使用")
            sys.exit(1)

        password = getpass("请输入管理员密码（至少6位）: ")
        password_confirm = getpass("请再次输入密码: ")

        if password != password_confirm:
            print("❌ 两次输入的密码不一致")
            sys.exit(1)

        if len(password) < 6:
            print("❌ 密码长度至少为 6 位")
            sys.exit(1)

        # 生成邀请码
        invite_code = secrets.token_urlsafe(8)

        # 创建管理员账号
        admin = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role="admin",
            invite_code=invite_code,
        )

        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print()
        print("=" * 50)
        print("✅ 管理员账号创建成功！")
        print("=" * 50)
        print(f"👤 用户名: {admin.username}")
        print(f"📧 邮箱: {admin.email}")
        print(f"🆔 ID: {admin.id}")
        print(f"🎟️  邀请码: {admin.invite_code}")
        print()
        print("⚠️  请妥善保管邀请码，用于邀请其他家庭成员注册")
        print("=" * 50)


if __name__ == "__main__":
    try:
        asyncio.run(create_admin())
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 创建失败: {e}")
        sys.exit(1)
