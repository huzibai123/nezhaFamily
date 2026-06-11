# Docker 部署指南

## 快速开始

### 前置要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少 2GB 可用内存
- 至少 20GB 可用磁盘空间

### 开发环境部署

1. **克隆项目**
```bash
git clone https://github.com/your-repo/nezha-family.git
cd nezha-family
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **访问应用**
- 前端：http://localhost:8080
- 后端 API：http://localhost:8080/api/v1
- API 文档：http://localhost:8000/api/docs

4. **查看日志**
```bash
docker-compose logs -f
```

### 生产环境部署

1. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件
vim .env
```

必须修改的配置：
- `POSTGRES_PASSWORD`: 数据库密码（强密码）
- `REDIS_PASSWORD`: Redis 密码（强密码）
- `SECRET_KEY`: JWT 密钥（使用 `openssl rand -hex 32` 生成）
- `AI_KEY_ENCRYPTION_SECRET`: AI 模型供应商数据库 Key 的独立加密密钥（使用 `openssl rand -hex 32` 生成，长期保持稳定）
- `ALLOWED_ORIGINS`: 生产站点来源，例如 `https://family.example.com`
- `DOMAIN`: 你的域名（如 family.example.com）
- `ADMIN_EMAIL`: 管理员邮箱（用于 HTTPS 证书）
- `TRUSTED_PROXY_COUNT`: 保持 `1`，对应生产链路 `Caddy -> backend`

AI 管家生产默认关闭：`AI_ENABLED=false`，`AI_API_KEY` 可以留空。后台保存的模型 Key 会使用
`AI_KEY_ENCRYPTION_SECRET` 加密；该值不要随 JWT `SECRET_KEY` 轮换。旧版本已保存过后台 Key 的实例，
请先保持旧 `SECRET_KEY` 不变、设置新的 `AI_KEY_ENCRYPTION_SECRET` 部署本版本，然后在后台重新保存
模型供应商配置，使密文升级为新格式；之后再按需轮换 JWT `SECRET_KEY`。

2. **启动生产环境**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

启动时会先运行 `migrate` 服务完成数据库迁移，后端和 Celery worker 会等待迁移成功后再启动。

3. **创建管理员账号**
```bash
docker exec -it nezha-backend python init_admin.py
```

按提示设置管理员用户名、邮箱和密码。请使用独立强密码，不要在生产环境使用固定默认密码。

如果需要在自动化脚本中非交互创建首个管理员，可使用一次性环境变量；脚本会读取容器内的
`DATABASE_URL`，并在已存在管理员时直接退出，不会覆盖已有账号：

```bash
docker exec \
  -e INITIAL_ADMIN_USERNAME=admin \
  -e INITIAL_ADMIN_EMAIL=you@example.com \
  -e INITIAL_ADMIN_PASSWORD='replace-with-a-strong-password' \
  nezha-backend python create_admin.py
```

## 服务说明

### 服务列表

- **postgres**: PostgreSQL 16 数据库
- **redis**: Redis 7 缓存和任务队列
- **migrate**: 一次性数据库迁移任务
- **backend**: FastAPI 后端服务
- **celery-worker**: Celery 异步任务处理，使用 Redis DB 1/2 作为 broker/result backend
- **frontend**: Vue 3 前端（开发环境）或 Nginx 静态服务（生产环境）
- **caddy**: 反向代理和自动 HTTPS

### 健康检查与路由

- 后端健康检查端点为 `GET /health`；开发和生产 Compose 都通过容器内 `http://localhost:8000/health` 检查 backend。
- 开发 Caddy (`docker/Caddyfile.dev`) 监听 Compose 内部 `:80`，宿主机通过 `8080` 访问；`/api/*` 和 `/media/*` 代理到 backend，其他请求代理到 Vite `frontend:3000`，支持 HMR WebSocket。
- 生产 Caddy (`docker/Caddyfile`) 使用 `DOMAIN` 和 `ADMIN_EMAIL` 自动申请 HTTPS；`/api/*` 代理到 backend 并配置 upstream health check，`/media/*` 代理到 backend，其他请求代理到 `frontend:80`。
- 后端生产文档页默认关闭；开发环境 API 文档为 `http://localhost:8000/api/docs`。

### 端口映射

#### 开发环境
- 8080: Caddy 入口（前端 + API）
- 8443: Caddy HTTPS（开发环境未启用）
- 3000: Vue 开发服务器（内部）
- 8000: FastAPI（内部，可通过 localhost:8000 直接访问）
- 5432: PostgreSQL（可通过 localhost:5432 连接）
- 6379: Redis（可通过 localhost:6379 连接）

#### 生产环境
- 80: HTTP（自动重定向到 HTTPS）
- 443: HTTPS（Caddy 自动证书）
- 其他端口均为内部端口，不暴露到宿主机

### 数据卷

- `postgres_data`: 数据库数据
- `redis_data`: Redis 持久化数据
- `media_files`: 用户上传的媒体文件
- `backup_files`: 管理后台生成的备份快照
- `caddy_data`: Caddy 数据（包括 HTTPS 证书）
- `caddy_config`: Caddy 配置缓存

## 常用命令

### 启动和停止

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启服务
docker-compose restart

# 停止并删除数据卷（⚠️ 会删除所有数据）
docker-compose down -v
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### 服务管理

```bash
# 查看服务状态
docker-compose ps

# 重启特定服务
docker-compose restart backend

# 重新构建并启动
docker-compose up -d --build
```

### 数据库操作

```bash
# 连接到数据库
docker exec -it nezha-postgres psql -U nezha_user -d nezha_family

# 数据库迁移
docker exec -it nezha-backend alembic upgrade head

# 创建新迁移
docker exec -it nezha-backend alembic revision --autogenerate -m "描述"
```

### 备份和恢复

```bash
# 备份数据库
docker exec nezha-postgres pg_dump -U nezha_user nezha_family > backup.sql

# 恢复数据库
docker exec -i nezha-postgres psql -U nezha_user nezha_family < backup.sql

# 备份媒体文件（使用 backend 容器挂载，避免 Docker Compose 项目名导致卷名不同）
docker run --rm --volumes-from nezha-backend -v $(pwd):/backup alpine tar czf /backup/media-backup.tar.gz -C /app/media .

# 恢复媒体文件
docker run --rm --volumes-from nezha-backend -v $(pwd):/backup alpine tar xzf /backup/media-backup.tar.gz -C /app/media

# 备份管理后台生成的快照文件
docker run --rm --volumes-from nezha-backend -v $(pwd):/backup alpine tar czf /backup/admin-backups.tar.gz -C /app/backups .

# 恢复管理后台生成的快照文件
docker run --rm --volumes-from nezha-backend -v $(pwd):/backup alpine tar xzf /backup/admin-backups.tar.gz -C /app/backups
```

### 媒体回收站清理

后端提供手动 Celery 任务清理媒体回收站，不默认启用 Celery Beat。任务会删除
`deleted_at` 超过 `MEDIA_TRASH_RETENTION_DAYS` 的媒体磁盘文件、缩略图和数据库记录；
保留天数默认 30 天。

```bash
docker exec nezha-backend celery -A app.tasks call app.tasks.media_processing.cleanup_expired_media_trash
```

生产环境如需定时执行，可后续接 Celery Beat 或宿主机 cron。在启用周期任务前，建议先确认备份策略和软删除入口已经就绪。

## 故障排查

### 服务无法启动

1. **检查端口占用**
```bash
sudo lsof -i :80
sudo lsof -i :443
```

开发机如果 `8080` 或 `8443` 被占用，可临时覆盖端口后再做 smoke test，例如：
```bash
docker compose up -d
# 或先在 docker-compose.yml 中临时改为 18080:80、18443:443，验证后不要提交本地端口改动。
curl -fsS http://localhost:8080/health || curl -fsS http://localhost:8080/
```

2. **查看服务日志**
```bash
docker-compose logs backend
```

3. **检查配置文件**
```bash
# 验证 .env 文件
cat .env

# 验证 Docker Compose 配置
docker compose config
docker compose -f docker-compose.prod.yml config
```

生产配置 dry-run 可使用一次性环境变量，不需要写入 `.env`：
```bash
POSTGRES_PASSWORD=change-me-postgres \
REDIS_PASSWORD=change-me-redis \
SECRET_KEY=change-me-secret-key-32-bytes-min \
AI_KEY_ENCRYPTION_SECRET=change-me-ai-key-encryption-secret \
ALLOWED_ORIGINS=https://family.example.com \
DOMAIN=family.example.com \
ADMIN_EMAIL=admin@example.com \
TRUSTED_PROXY_COUNT=1 \
AI_ENABLED=false \
docker compose -f docker-compose.prod.yml config
```

### 数据库连接失败

1. **检查数据库是否健康**
```bash
docker-compose ps postgres
```

2. **检查数据库日志**
```bash
docker-compose logs postgres
```

3. **手动连接测试**
```bash
docker exec -it nezha-postgres psql -U nezha_user -d nezha_family
```

### HTTPS 证书问题

1. **检查域名解析**
```bash
dig your-domain.com
```

2. **查看 Caddy 日志**
```bash
docker-compose logs caddy
```

3. **手动申请证书**
```bash
docker exec -it nezha-caddy caddy reload --config /etc/caddy/Caddyfile
```

## 性能优化

### 生产环境建议

1. **增加 worker 数量**（根据 CPU 核心数）
```yaml
# docker-compose.prod.yml
backend:
  command: gunicorn app.main:app --workers 8 ...
```

2. **配置数据库连接池**
```bash
# 在 .env 中添加
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

3. **启用 Redis 持久化**
```yaml
redis:
  command: redis-server --appendonly yes --save 60 1000
```

## 安全建议

1. **使用强密码**：所有密码至少 16 位，包含大小写字母、数字、特殊字符
2. **定期更新镜像**：`docker-compose pull && docker-compose up -d`
3. **备份策略**：每日自动备份数据库和媒体文件
4. **监控告警**：配置日志监控和异常告警
5. **防火墙规则**：只开放 80/443 端口，其他端口禁止外部访问

## 更新升级

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重新构建镜像
docker-compose -f docker-compose.prod.yml build

# 3. 停止旧服务
docker-compose -f docker-compose.prod.yml down

# 4. 启动新服务
docker-compose -f docker-compose.prod.yml up -d
```

## 卸载

```bash
# 停止并删除所有容器、网络、数据卷
docker-compose down -v

# 删除镜像
docker rmi $(docker images | grep nezha | awk '{print $3}')

# 删除项目目录
rm -rf nezha-family
```
