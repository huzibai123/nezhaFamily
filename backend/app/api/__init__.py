"""
API 路由模块
"""
from app.api import auth, users, posts, comments, likes, media, albums, events, admin, notifications, ai

__all__ = [
    "auth",
    "users",
    "posts",
    "comments",
    "likes",
    "media",
    "albums",
    "events",
    "admin",
    "notifications",
    "ai",
]
