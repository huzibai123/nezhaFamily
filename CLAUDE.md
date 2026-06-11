# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**哪吒家庭（Nezha Family）** —— 私有化、可自托管的家庭内容分享平台（类亲宝宝 App），通过 Docker Compose 一键部署到自己的 VPS/NAS。单租户（一个实例服务一个家庭）、仅家庭内部使用、不做公开分享。功能：图片/视频帖子、评论与嵌套回复、点赞、时间线、相册、家庭日历。

完整产品需求见 `nezha-family.prd.md`（PRD 是唯一权威的产品文档，README 为空）。

## ⚠️ 当前代码状态（2026-06-11 更新）

**✅ 项目已完成 MVP + 生产加固**（产品背景见 `nezha-family.prd.md`，部署说明见 `docker/DEPLOY.md`）

- 主路径代码已纳入 git，开发时以当前 `main` 为准；不要从旧 worktree 或历史报告里直接复制未核对内容。

- **✅ 核心功能已实现并验证**：
  - 用户认证（注册/登录/JWT）+ 档案编辑
  - 帖子 CRUD + 点赞（实时统计）+ 评论（嵌套回复）
  - 相册 CRUD + 媒体管理（权限校验）
  - 事件 CRUD（权限校验）
  - 媒体上传 + Celery 异步处理（压缩/缩略图）
  - 前端 Vue 3 全套页面（Timeline/Profile/Albums/Publish/PostDetail/Calendar）
  - Docker Compose 一键部署 + Alembic 自动迁移
  - 19 个测试通过（相册/媒体/认证 API）

- **✅ 已修复的问题**（阶段一 P0）：
  - 后端导入错误（album/event 模型的 `base_class` → `base`）
  - 媒体模型统一（`Media` 类不存在 → 统一用 `MediaFile`，响应字段用 `url`/`type`）
  - 依赖缺失（补 `psycopg2-binary`）
  - 登录 500 错误（数据库连接 + 管理员账号创建）

- **✅ 生产加固完成**（阶段三 P2）：
  - CORS 环境变量配置（`settings.ALLOWED_ORIGINS`）
  - DEBUG 模式可控（SQL 日志 `echo=settings.DEBUG`）
  - 点赞计数一致性（Like 表实时统计，移除冗余字段维护）
  - 路由冲突修复（删除 auth.py 的重复 `/users/{user_id}`）
  - SQLAlchemy 警告消除（Comment.likes 加 `overlaps="likes"`）
  - 删帖级联清理（手动删除关联 Like 记录）

- **文档与代码约定**（已统一）：
  - 根目录 `package.json` 已过时（写 React，实际是 Vue 3），忽略它
  - API 响应：直接返回资源 Schema（如 `PostResponse`），错误用 `HTTPException(detail="...")`，**不要用 `{success, data, message}` 封装**
  - 媒体响应字段统一：`url`（=file_path）、`type`（=file_type）
  - 前端请求层：`api/*.ts` 函数返回业务数据本身（不是 AxiosResponse），调用方直接 `await getXxx()` 拿对象，`catch(e)` 的 e 是字符串

## 技术栈（实际版本）

- **后端**：FastAPI 0.110 + SQLAlchemy 2.0（异步 / asyncpg）+ Pydantic 2.6 + Alembic + Celery 5.3（Redis broker）+ PostgreSQL 16 + Redis 7；JWT 用 `python-jose`，密码用 `passlib[bcrypt]`（pin `bcrypt<4.2`）。本地 venv 为 Python 3.11。
- **前端**：Vue 3.5 + vue-router 4 + Vite 8 + Tailwind 3.4 + axios + `lucide-vue-next` + TypeScript（`vue-tsc`）。**状态管理用 composable（`composables/useAuth.ts`），不是 Pinia**。
- **基础设施**：Caddy 2.7 反代（自动 HTTPS），Docker Compose 编排。

## 常用命令

### 后端（在 `backend/` 下）
```bash
source venv/bin/activate                 # 已有 venv（Python 3.11）；新建则 python3 -m venv venv && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # 或 python run.py
ruff check app/ && black app/            # 提交前必跑（项目规范）

# 数据库迁移（Alembic 用同步驱动，env.py 会自动把 asyncpg URL 转同步）
alembic upgrade head
alembic revision --autogenerate -m "描述"   # 改完模型后生成；注意新模型必须能被 app/db/base.py 的导入链加载到
alembic downgrade -1

# 创建初始管理员（二选一）
python init_admin.py                     # 交互式，推荐；会校验是否已存在管理员
INITIAL_ADMIN_USERNAME=admin INITIAL_ADMIN_EMAIL=admin@example.com INITIAL_ADMIN_PASSWORD='强密码' python create_admin.py
```

### 后端测试（需要真实 PostgreSQL，测试用 PG 专属的 UUID/JSONB，不能用 SQLite）
```bash
# 1) 起库并建独立测试库（conftest.py 连的是 nezha_family_test）
docker-compose up -d postgres redis
docker-compose exec postgres psql -U nezha_user -d nezha_family -c "CREATE DATABASE nezha_family_test;"

# 2) 跑测试（pyproject.toml 已设 asyncio_mode=auto、testpaths=tests）
pytest                                            # 全部
pytest tests/test_auth.py                         # 单文件
pytest tests/test_auth.py::test_register_success -v   # 单个用例

# 在容器内跑（避免本地 Python 版本差异，推荐）
docker-compose run --rm backend pytest tests/ -v
```

### 前端
```bash
npm run build      # 根目录会转发到 frontend

cd frontend
npm install
npm run dev        # Vite 开发服务器，默认端口 5173，已配 /api → http://localhost:8000 代理
npm run build      # vue-tsc -b && vite build（带类型检查）
npm run preview
```

### Docker Compose（在仓库根）
```bash
docker-compose up -d            # 全栈：postgres / redis / backend / celery-worker / frontend / caddy
docker-compose ps && docker-compose logs -f
docker-compose down [-v]        # -v 连数据卷一起删（重置数据库）
# 端口：前端 3000（compose 用 --port 3000 覆盖了 vite 的 5173）、后端 8000、Caddy 8080
# 生产用 docker-compose.prod.yml；首次管理员请运行 docker compose -f docker-compose.prod.yml exec backend python init_admin.py
```

## 架构与跨文件关键约定

### 后端分层（`backend/app/`）
`api/`（路由）→ `schemas/`（Pydantic 出入参）→ `models/`（SQLAlchemy ORM）→ `db/`（引擎与会话）；`core/` 放配置、安全、依赖注入；`tasks/` 放 Celery。`main.py` 把 8 个 router 全部挂在 `settings.API_V1_PREFIX`（`/api/v1`）下。

### 请求与数据库会话
`db/session.py` 的 `get_db()` 依赖：每个请求开一个 `AsyncSession`，异常时自动 rollback，成功提交由路由显式 `await db.commit()` 控制。数据库 URL 统一来自 `core/config.py` 的 `settings.DATABASE_URL`；API、Alembic 和 Celery 任务应保持同一来源。

### 认证
- JWT 载荷的用户标识 claim 是 **`user_id`（字符串 UUID），不是 `sub`**；`create_access_token`/`get_current_user_id`（在 `core/security.py`）配套使用。请求头 `Authorization: Bearer <token>`，默认有效期 7 天。
- 鉴权依赖有**两份重复实现**：`core/security.py` 和 `core/dependencies.py` 各有一个 `get_current_user`。**现有路由都从 `core.security` 导入**（如 `posts.py`），新代码请保持一致；`dependencies.py` 里还有 `get_current_active_admin`（管理员守卫）。
- 端点总览（均在 `/api/v1` 下）：auth `register/login/me/logout`；posts `CRUD /posts`；comments `/posts/{id}/comments`、`/comments/{id}`；likes `/posts/{id}/like`、`/comments/{id}/like`；users `/users/{id}`(+`/posts`/`/stats`)；media `/upload`；albums `/albums...`；events `/events...`。（注意 auth 与 users 都定义了 `GET /users/{user_id}`，存在重叠。）

### 模型注册链（改模型/加表时必看）
`db/base.py` 里 `Base = declarative_base()` 并导入 User/Post/Comment/Like/MediaFile；导入任一模型会触发 `app/models/__init__.py` 再额外导入 Album/Event。Alembic（`alembic/env.py`）和测试（`conftest.py`）都以 `app.db.base.Base.metadata` 为准。**新增模型必须能通过这条导入链被加载，否则 autogenerate / 建表会漏掉。**（如上所述，album/event 目前 import 了错误的 base，需先修。）

### 媒体存储
媒体文件落盘路径统一走 `MEDIA_ROOT` 配置，DB 中保存原始 `/media/...` 路径，响应时按登录态签发带 token 的访问 URL。开发和生产由 Caddy/FastAPI 公开媒体访问入口；图片压缩、缩略图和回收站清理由 Celery 任务处理。

### 前端结构与 API 客户端
- 视图在 `src/views/`、组件在 `src/components/`，路由 `src/router/index.ts`（用 `meta.requiresAuth` + `beforeEach` 守卫），登录态在 `src/composables/useAuth.ts`（`ref` 全局态 + `localStorage`）。`@` 别名指向 `src/`。
- 前端请求统一使用 `src/api/index.ts` 的 axios 实例，baseURL 为 `VITE_API_BASE_URL || '/api/v1'`，请求拦截器读取 `localStorage('token')`，错误字段读取 FastAPI 的 `detail`。
- `useAuth.ts` 调用 `src/api/auth.ts`，不再硬编码后端地址；新增接口时优先放在 `src/api/*.ts`，让调用方直接拿业务数据对象。

## 配置与环境变量
- `.env` 有两处：仓库根 `.env`（给 docker-compose 用，`POSTGRES_*`/`REDIS_PASSWORD`/`DOMAIN` 等）和 `backend/.env`（给后端进程用，`DATABASE_URL`/`SECRET_KEY` 等）。模板见 `.env.example`。
- `backend/.env` 里的 `DATABASE_URL` 主机名是 **`postgres`（Docker 服务名）**，在容器内可用；**本地直接跑后端要改成 `localhost`** 才连得上。
- 统一的开发库凭据是 `nezha_user / nezha_dev_password`，库名 `nezha_family`（测试库 `nezha_family_test`）。注意 `alembic/env.py` 的默认回退 URL 仍是过时的 `nezha:nezha123`——靠 env 覆盖，别被它误导。
- 生产部署前必须改 `SECRET_KEY`（`openssl rand -hex 32`），开发默认值是 `dev_secret_key_change_in_production`。
- AI Provider 数据库 Key 使用 `AI_KEY_ENCRYPTION_SECRET` 独立加密；该值必须长期稳定，不要随 JWT `SECRET_KEY` 轮换。

## 代码规范（项目约定）
- Python：black + ruff，4 空格缩进、行长 100，必加类型提示，公共函数写中文 docstring；提交前过 `ruff check && pytest`。
- 安全：密码 bcrypt；入参一律 Pydantic 校验；媒体访问需登录鉴权（仅家庭成员）；ORM 参数化防注入；前端转义防 XSS。
- 注释、docstring、commit message 一律中文。
