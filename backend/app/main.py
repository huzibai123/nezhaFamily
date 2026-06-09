"""
哪吒家庭 - FastAPI 应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import auth, users, posts, comments, likes, media, albums, events, admin, notifications

# 创建 FastAPI 应用实例
# 生产环境（DEBUG=False）禁用 API 文档，避免暴露接口定义
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="私有化家庭分享平台 API",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

# 配置 CORS 中间件
# 从配置读取允许的跨域源（支持环境变量动态配置）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "哪吒家庭 API 服务运行中",
        "version": settings.VERSION,
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


# 注册路由
app.include_router(media.public_router, tags=["媒体"])
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["认证"])
app.include_router(users.router, prefix=settings.API_V1_PREFIX, tags=["用户"])
app.include_router(posts.router, prefix=settings.API_V1_PREFIX, tags=["帖子"])
app.include_router(comments.router, prefix=settings.API_V1_PREFIX, tags=["评论"])
app.include_router(likes.router, prefix=settings.API_V1_PREFIX, tags=["点赞"])
app.include_router(media.router, prefix=settings.API_V1_PREFIX, tags=["媒体"])
app.include_router(albums.router, prefix=settings.API_V1_PREFIX, tags=["相册"])
app.include_router(events.router, prefix=settings.API_V1_PREFIX, tags=["日历"])
app.include_router(admin.router, prefix=settings.API_V1_PREFIX, tags=["管理员"])
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX, tags=["通知"])
