# 测试运行指南

本文档说明如何在 Docker 安装完成后运行测试。

## 前置条件

✅ Docker Desktop 已安装并启动
✅ 代码问题已修复（数据库配置统一、conftest.py 已创建、pytest 配置完成）

## 快速开始（推荐方式）

### 1. 启动 Docker Desktop

```bash
# 打开 Docker Desktop 应用
open /Applications/Docker.app

# 等待 Docker 守护进程启动（状态栏图标变为可用）
# 或者通过命令检查：
docker ps
```

### 2. 启动数据库服务

```bash
cd /Users/baiyi/myCode/nezhaFamily

# 仅启动 PostgreSQL 和 Redis（不启动后端和前端）
docker-compose up -d postgres redis

# 等待服务就绪（大约 5-10 秒）
docker-compose ps

# 创建测试数据库
docker-compose exec postgres psql -U nezha_user -d nezha_family -c "CREATE DATABASE nezha_family_test;"
```

### 3. 在 Docker 容器内运行测试（推荐）

**优势**：
- 环境完全隔离（Python 3.11 + 所有依赖已安装）
- 避免本地 Python 3.13 兼容性问题
- 与生产环境一致

```bash
# 构建后端镜像
docker-compose build backend

# 运行所有认证测试
docker-compose run --rm backend pytest tests/test_auth.py -v

# 运行单个测试
docker-compose run --rm backend pytest tests/test_auth.py::test_register_success -v

# 运行所有测试（包括未来添加的测试）
docker-compose run --rm backend pytest tests/ -v
```

**预期输出**：
```
tests/test_auth.py::test_register_success PASSED                    [ 20%]
tests/test_auth.py::test_login_success PASSED                       [ 40%]
tests/test_auth.py::test_register_invalid_invite_code PASSED        [ 60%]
tests/test_auth.py::test_login_wrong_password PASSED                [ 80%]
tests/test_auth.py::test_get_current_user PASSED                    [100%]

======================== 5 passed in 2.34s =========================
```

---

## 备选方式：本地 Python 环境测试

如果你想在本地 Python 3.13 环境测试（不推荐，但可行）：

### 1. 确保数据库服务运行

```bash
# Docker 方式（推荐）
docker-compose up -d postgres redis
docker-compose exec postgres psql -U nezha_user -d nezha_family -c "CREATE DATABASE nezha_family_test;"

# 或本地安装方式
brew install postgresql@16 redis
brew services start postgresql@16 redis
createdb nezha_family_test
```

### 2. 安装 Python 依赖

```bash
cd /Users/baiyi/myCode/nezhaFamily/backend

# 创建虚拟环境（如果还没有）
python3 -m venv venv
source venv/bin/activate

# 安装依赖（pillow 已升级到 10.4.0，应该能装了）
pip install -r requirements.txt
```

### 3. 运行测试

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行测试
pytest tests/test_auth.py -v
```

---

## 常见问题

### Q1: 测试提示 "connection refused"

**原因**：数据库服务未启动或配置不正确

**解决**：
```bash
# 检查数据库服务状态
docker-compose ps postgres

# 如果未运行，启动服务
docker-compose up -d postgres redis

# 检查连接
docker-compose exec postgres psql -U nezha_user -d nezha_family -c "\l"
```

### Q2: 测试提示 "database nezha_family_test does not exist"

**原因**：测试数据库未创建

**解决**：
```bash
docker-compose exec postgres psql -U nezha_user -d nezha_family -c "CREATE DATABASE nezha_family_test;"
```

### Q3: pytest 提示 "ModuleNotFoundError"

**原因**：依赖未安装

**解决**：
```bash
# Docker 方式：重新构建镜像
docker-compose build backend

# 本地方式：重新安装依赖
pip install -r requirements.txt
```

### Q4: 测试卡住不动

**原因**：asyncio event loop 配置问题

**解决**：已在 `pyproject.toml` 中配置 `asyncio_mode = "auto"`，正常情况下不会出现此问题。如果仍然卡住，检查 pytest-asyncio 版本：
```bash
pip show pytest-asyncio
# 应该是 0.23.4 或更高
```

---

## 已修复的问题清单

在运行测试前，以下问题已被修复：

1. ✅ **依赖兼容性**：`pillow` 升级到 10.4.0（兼容 Python 3.13）
2. ✅ **数据库配置统一**：三处配置统一为 `nezha_user/nezha_dev_password`
3. ✅ **测试基础设施**：创建 `tests/conftest.py`（包含 db、client、test_admin、test_user fixtures）
4. ✅ **pytest 配置**：创建 `pyproject.toml`（设置 asyncio_mode）
5. ✅ **测试用例修正**：修正邀请码和密码，添加更多测试场景

---

## 下一步

测试通过后，可以继续开发：

1. **阶段 2**：实现帖子 API（posts.py）
2. **阶段 3**：实现媒体上传（media.py）
3. **阶段 4**：实现评论和点赞（comments.py, likes.py）
4. **阶段 5**：完善前端 UI

运行整个项目（前后端 + 数据库）：
```bash
docker-compose up -d
# 访问：
# - 前端：http://localhost:3000
# - 后端 API 文档：http://localhost:8000/api/docs
# - 数据库：localhost:5432
```

## 部署配置验收命令

部署配置变更后，至少执行以下 dry-run 检查；生产命令使用一次性环境变量，避免把临时密钥写入 `.env`。

```bash
cd /Users/baiyi/myCode/nezhaFamily

# 后端测试
docker compose run --rm backend pytest -q

# 前端构建
npm --prefix frontend run build

# 开发 Compose 配置
docker compose config

# 生产 Compose 配置
POSTGRES_PASSWORD=change-me-postgres \
REDIS_PASSWORD=change-me-redis \
SECRET_KEY=change-me-secret-key-32-bytes-min \
ALLOWED_ORIGINS=https://family.example.com \
DOMAIN=family.example.com \
ADMIN_EMAIL=admin@example.com \
TRUSTED_PROXY_COUNT=1 \
AI_ENABLED=false \
docker compose -f docker-compose.prod.yml config

# Caddy 配置校验
docker run --rm -v "$PWD/docker/Caddyfile.dev:/etc/caddy/Caddyfile:ro" caddy:2.7-alpine caddy validate --config /etc/caddy/Caddyfile
docker run --rm \
  -e DOMAIN=family.example.com \
  -e EMAIL=admin@example.com \
  -v "$PWD/docker/Caddyfile:/etc/caddy/Caddyfile:ro" \
  caddy:2.7-alpine caddy validate --config /etc/caddy/Caddyfile

# 可选 smoke test
docker compose up -d
curl -fsS http://localhost:8080/health || curl -fsS http://localhost:8080/
```

如果本机 `8080`/`8443` 已被占用，先用 `lsof -i :8080` 和 `lsof -i :8443` 定位占用；临时改 Compose 端口做验证时不要提交该端口改动。
