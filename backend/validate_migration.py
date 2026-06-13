#!/usr/bin/env python3
"""
验证数据库模型和迁移配置是否正确
在执行实际迁移前运行此脚本
"""
import sys
import os

# 将项目根目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def validate_models():
    """验证所有模型是否能正确导入"""
    print("验证模型导入...")

    try:
        from app.models import User, Post, Comment, PostLike, CommentLike, MediaFile
        print("✓ 所有模型导入成功")
        print(f"  - User: {User.__tablename__}")
        print(f"  - Post: {Post.__tablename__}")
        print(f"  - Comment: {Comment.__tablename__}")
        print(f"  - PostLike: {PostLike.__tablename__}")
        print(f"  - CommentLike: {CommentLike.__tablename__}")
        print(f"  - MediaFile: {MediaFile.__tablename__}")
        return True
    except ImportError as e:
        print(f"✗ 模型导入失败: {e}")
        return False

def validate_base():
    """验证 Base 是否正确配置"""
    print("\n验证 Base 配置...")

    try:
        from app.db.base import Base, import_all_models
        import_all_models()
        print("✓ Base 导入成功")

        # 检查所有注册的表
        tables = Base.metadata.tables.keys()
        print(f"✓ 已注册 {len(tables)} 个表:")
        for table in sorted(tables):
            print(f"  - {table}")

        # 验证期望的表都存在
        expected_tables = {
            "users",
            "posts",
            "comments",
            "post_likes",
            "comment_likes",
            "media_files",
        }
        if expected_tables.issubset(tables):
            print("✓ 所有必需的表都已注册")
            return True
        else:
            missing = expected_tables - tables
            print(f"✗ 缺失的表: {missing}")
            return False
    except Exception as e:
        print(f"✗ Base 配置验证失败: {e}")
        return False

def validate_session():
    """验证 Session 配置"""
    print("\n验证 Session 配置...")

    try:
        from app.db.session import get_db, AsyncSessionLocal, engine
        print("✓ Session 配置导入成功")
        print(f"✓ 数据库引擎: {engine.url}")
        return True
    except Exception as e:
        print(f"✗ Session 配置验证失败: {e}")
        return False

def validate_alembic():
    """验证 Alembic 配置"""
    print("\n验证 Alembic 配置...")

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(config)

        print("✓ Alembic 配置文件读取成功")

        # 检查迁移脚本
        revisions = list(script_dir.walk_revisions())
        print(f"✓ 找到 {len(revisions)} 个迁移脚本:")
        for rev in revisions:
            print(f"  - {rev.revision}: {rev.doc}")

        if len(revisions) > 0:
            print("✓ 初始迁移脚本已创建")
            return True
        else:
            print("✗ 未找到迁移脚本")
            return False
    except Exception as e:
        print(f"✗ Alembic 配置验证失败: {e}")
        return False

def main():
    """执行所有验证"""
    print("=" * 60)
    print("数据库迁移配置验证")
    print("=" * 60)

    results = []
    results.append(("模型导入", validate_models()))
    results.append(("Base 配置", validate_base()))
    results.append(("Session 配置", validate_session()))
    results.append(("Alembic 配置", validate_alembic()))

    print("\n" + "=" * 60)
    print("验证结果汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name:20s} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ 所有验证通过！可以执行数据库迁移了。")
        print("\n下一步:")
        print("  1. 确保 PostgreSQL 数据库正在运行")
        print("  2. 配置 DATABASE_URL 环境变量")
        print("  3. 执行: alembic upgrade head")
        return 0
    else:
        print("\n✗ 验证失败，请修复上述问题后重试。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
