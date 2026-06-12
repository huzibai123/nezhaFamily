# 测试指南

本文档说明哪吒家庭的本地门禁、正式 E2E、部署配置校验和生产 smoke 建议。

## 前置条件

- Docker Desktop 或 Docker Engine 已启动。
- 已安装 Node.js，或使用仓库内 Docker/Vite 服务。
- 首次运行前安装前端依赖：

```bash
npm --prefix frontend install
npx --prefix frontend playwright install chromium
```

如果 Playwright 浏览器下载较慢，也可以使用本机已安装的 Chrome：

```bash
E2E_BROWSER_CHANNEL=chrome npm --prefix frontend run test:e2e
```

## 后端测试

推荐在 Docker 后端镜像中运行，避免本机 Python 版本差异：

```bash
docker compose run --rm --no-deps \
  -v "$PWD:/workspace" \
  -w /workspace/backend \
  backend pytest -q
```

运行单个文件：

```bash
docker compose run --rm --no-deps \
  -v "$PWD:/workspace" \
  -w /workspace/backend \
  backend pytest tests/test_auth.py -q
```

## 前端构建与契约检查

```bash
npm --prefix frontend run build
npm --prefix frontend run test:contracts
```

`build` 会执行 `vue-tsc -b` 和 Vite 构建；`test:contracts` 用于锁定 AI 管理子路由和 Provider payload 语义。

## 正式 E2E

Playwright Test 位于 `frontend/e2e`，脚本为：

```bash
npm --prefix frontend run test:e2e
```

默认环境变量：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `E2E_BASE_URL` | `http://localhost:3000` | 前端访问地址 |
| `E2E_API_URL` | `http://localhost:8000` | 后端 API 地址 |
| `E2E_ADMIN_USERNAME` | 空 | 管理员用户名 |
| `E2E_ADMIN_PASSWORD` | 空 | 管理员密码 |
| `E2E_BROWSER_CHANNEL` | 空 | 可选，例如 `chrome`，用于复用本机浏览器 |

未设置管理员账号时，E2E 只运行公开登录页渲染，并明确跳过登录写入流；不会创建或重置真实管理员账号。

使用现有 dev stack 跑完整流程：

```bash
E2E_BASE_URL=http://localhost:8080 \
E2E_API_URL=http://localhost:8000 \
E2E_ADMIN_USERNAME=admin \
E2E_ADMIN_PASSWORD='your-password' \
npm --prefix frontend run test:e2e
```

完整 E2E 会覆盖登录、发布文字帖、帖子详情、点赞、评论、通知页、相册、媒体库、资料弹窗和 AI 管家只读渲染。测试内容统一使用 `E2E-NEZHA-` 前缀，并在结束时尽量通过 API 删除；如果清理失败，输出需要人工清理的帖子 ID。

## Docker Compose 校验

开发配置：

```bash
docker compose config
```

生产配置 dry-run，不需要写入 `.env`：

```bash
POSTGRES_PASSWORD=change-me-postgres \
REDIS_PASSWORD=change-me-redis \
SECRET_KEY=change-me-secret-key-32-bytes-min \
AI_KEY_ENCRYPTION_SECRET=change-me-ai-key-secret-32-bytes-min \
ALLOWED_ORIGINS=https://family.example.com \
DOMAIN=family.example.com \
ADMIN_EMAIL=admin@example.com \
TRUSTED_PROXY_COUNT=1 \
AI_ENABLED=false \
docker compose -f docker-compose.prod.yml config
```

## Caddy Validate

开发 Caddyfile：

```bash
docker run --rm \
  -v "$PWD/docker/Caddyfile.dev:/etc/caddy/Caddyfile:ro" \
  caddy:2.7-alpine \
  caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

生产 Caddyfile：

```bash
docker run --rm \
  -e DOMAIN=family.example.com \
  -e EMAIL=admin@example.com \
  -v "$PWD/docker/Caddyfile:/etc/caddy/Caddyfile:ro" \
  caddy:2.7-alpine \
  caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

## Worker Smoke

开发栈启动后：

```bash
docker compose exec celery-worker celery -A app.tasks inspect ping
```

如果返回当前 worker 的 `pong`，说明 Redis broker、worker 导入和 Celery app 配置可用。

## 备份校验

管理后台可创建备份并执行校验。生产演练建议：

1. 创建一次备份。
2. 点击“校验备份”，确认 manifest、数据库快照和媒体归档均可读取。
3. 下载备份到可信位置。
4. 在临时 compose project 或新目录中做恢复演练。

不要直接覆盖正在使用的生产卷。恢复细节见 [docker/DEPLOY.md](./docker/DEPLOY.md)。

## AI Key 迁移验证

如果实例曾用旧版本保存过 AI Provider Key：

1. 部署新代码时保持旧 `SECRET_KEY` 不变。
2. 设置长期稳定的 `AI_KEY_ENCRYPTION_SECRET`。
3. 登录后台重新保存 Provider 配置。
4. 确认测试连接通过后，未来才考虑轮换 JWT `SECRET_KEY`。

自动化测试不会连接真实模型；真实供应商 smoke 只做人工最小闭环。

## 提交前建议门禁

```bash
docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q
npm --prefix frontend run build
npm --prefix frontend run test:e2e
docker compose config
POSTGRES_PASSWORD=change-me-postgres REDIS_PASSWORD=change-me-redis SECRET_KEY=change-me-secret-key-32-bytes-min AI_KEY_ENCRYPTION_SECRET=change-me-ai-key-secret-32-bytes-min ALLOWED_ORIGINS=https://family.example.com DOMAIN=family.example.com ADMIN_EMAIL=admin@example.com TRUSTED_PROXY_COUNT=1 AI_ENABLED=false docker compose -f docker-compose.prod.yml config
git diff --check
```
