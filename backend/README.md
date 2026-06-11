# 哪吒家庭后端服务

基于 FastAPI 的异步 RESTful API，提供用户认证、内容分享等功能。

## 技术栈

- **FastAPI** ^0.110 - 异步 Web 框架
- **SQLAlchemy** ^2.0 - 异步 ORM
- **PostgreSQL** ^16 - 数据库
- **Redis** ^7 - 缓存和任务队列
- **Alembic** - 数据库迁移
- **JWT** - 用户认证
- **Pydantic** ^2.6 - 数据验证

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

**重要**：生产环境必须修改 `SECRET_KEY`：

```bash
# 生成随机密钥
openssl rand -hex 32
```

### 3. 启动数据库

```bash
# 使用 Docker Compose 启动 PostgreSQL 和 Redis
cd ..
docker-compose up -d postgres redis
```

### 4. 运行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 5. 启动开发服务器

```bash
# 方式1：使用 uvicorn 直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式2：使用启动脚本
python run.py
```

服务启动后访问：
- API 文档（Swagger UI）: http://localhost:8000/api/docs
- API 文档（ReDoc）: http://localhost:8000/api/redoc
- 健康检查: http://localhost:8000/health

## API 使用说明

### 认证流程

#### 1. 注册新用户

```bash
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "invite_code": "VALID_INVITE_CODE"
  }'
```

响应示例：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "testuser",
    "email": "test@example.com",
    "role": "member",
    "avatar_url": null,
    "created_at": "2024-06-04T12:00:00"
  }
}
```

#### 2. 用户登录

```bash
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

#### 3. 获取当前用户信息

```bash
curl -X GET http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 4. 登出

```bash
curl -X POST http://localhost:8000/api/v1/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 认证方式

所有需要认证的接口都需要在请求头中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

Token 默认有效期为 7 天，过期后需要重新登录。

## 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── __init__.py
│   │   └── auth.py       # 认证相关 API
│   ├── core/             # 核心模块
│   │   ├── config.py     # 配置管理
│   │   ├── security.py   # 安全和 JWT
│   │   └── dependencies.py  # 依赖注入
│   ├── db/               # 数据库
│   │   ├── base.py       # Base 模型
│   │   └── session.py    # 会话管理
│   ├── models/           # SQLAlchemy 模型
│   │   ├── user.py       # 用户模型
│   │   ├── post.py       # 帖子模型
│   │   ├── comment.py    # 评论模型
│   │   ├── like.py       # 点赞模型
│   │   └── media.py      # 媒体文件模型
│   ├── schemas/          # Pydantic 模型
│   │   ├── user.py       # 用户 Schema
│   │   └── common.py     # 通用响应模型
│   ├── tasks/            # Celery 异步任务
│   │   └── __init__.py
│   └── main.py           # 应用入口
├── alembic/              # 数据库迁移
│   ├── versions/         # 迁移脚本
│   └── env.py
├── tests/                # 测试
│   └── __init__.py
├── .env.example          # 环境变量示例
├── requirements.txt      # Python 依赖
├── run.py                # 启动脚本
└── README.md             # 本文件
```

## 开发规范

### 代码风格

- 使用 `black` 和 `ruff` 进行代码格式化和检查
- 所有函数必须添加类型提示
- 所有公共函数必须添加中文文档字符串

```bash
# 格式化代码
black app/

# 代码检查
ruff check app/
```

### 数据库迁移

创建新的迁移脚本：

```bash
# 自动生成迁移脚本（根据模型变化）
alembic revision --autogenerate -m "描述信息"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_auth.py

# 查看覆盖率
pytest --cov=app tests/
```

测试数据库默认仍使用 `nezha_family_test`。如需在本机或 CI 指向其他数据库，可设置：

```bash
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/nezha_family_test pytest
```

### 媒体回收站清理

媒体回收站物理清理提供为手动 Celery 任务，不默认启用 Celery Beat。任务会删除
`deleted_at` 早于 `MEDIA_TRASH_RETENTION_DAYS` 的媒体主文件、缩略图和数据库记录，
保留天数默认 30 天：

```bash
celery -A app.tasks call app.tasks.media_processing.cleanup_expired_media_trash
```

后续可接入 Celery Beat 或宿主机 cron 定时调用；接入前建议先确认备份策略和软删除入口已经完成。

## 邀请码机制

### 初始化管理员账号

首次部署时需要手动创建管理员账号并生成邀请码。参考项目根目录的部署文档。

## 常见问题

### 1. 数据库连接失败

检查 `.env` 中的 `DATABASE_URL` 是否正确，确保 PostgreSQL 服务已启动：

```bash
docker-compose ps
```

### 2. 迁移失败

清空数据库重新迁移：

```bash
alembic downgrade base
alembic upgrade head
```

### 3. JWT Token 无效

检查 `SECRET_KEY` 是否一致，Token 是否过期。

## 待实现功能

- [ ] 帖子 CRUD API
- [ ] 评论和回复 API
- [ ] 点赞功能
- [ ] 媒体文件上传
- [ ] 图片压缩和缩略图生成（Celery 任务）
- [ ] 视频转码（可选）
- [ ] 用户权限管理增强
- [ ] API 限流
- [ ] 日志记录

## 许可证

MIT License
