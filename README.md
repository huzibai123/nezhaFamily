# 哪吒家庭 Nezha Family

哪吒家庭是一个开源、可自托管的私有家庭分享平台。它面向一个家庭、一个实例的场景，用 Docker Compose 在 VPS、NAS 或 Homelab 中部署，让照片、视频、文字、评论、点赞、通知和相册都留在自己的服务器里。

> 默认不做公开分享，不做多租户 SaaS。项目目标是给家庭成员一个温暖、稳定、可控的私有时间线。

## 功能概览

- 家庭成员认证：管理员初始化、邀请码注册、JWT 登录。
- 私有时间线：发布文字、图片、视频，支持服务端筛选和分页。
- 家庭互动：评论、回复、点赞、通知跳转与评论高亮。
- 相册与媒体库：相册整理、封面设置、媒体收藏、回收站和批量操作。
- 成员资料：头像、简介、家庭角色、生日和个人发布记录。
- 管理后台：成员管理、运行状态、备份状态、部署健康信息。
- 可选 AI 管家：模型供应商配置、AI 文案助手、AI 评论/点赞、角色与任务管理。
- 部署闭环：Caddy 反代、PostgreSQL、Redis、Celery worker、备份校验文档。

## 技术栈

- 后端：FastAPI、SQLAlchemy 2 async、Pydantic 2、Alembic、Celery。
- 前端：Vue 3、Vite、TypeScript、Tailwind CSS、lucide-vue-next。
- 基础设施：PostgreSQL 16、Redis 7、Caddy 2、Docker Compose。
- 测试：pytest、vue-tsc/Vite build、Playwright Test。

## 快速开始

```bash
git clone https://github.com/huzibai123/nezhaFamily.git
cd nezhaFamily
docker compose up -d
docker compose exec backend python init_admin.py
```

启动后访问：

- 应用入口：http://localhost:8080
- 后端健康检查：http://localhost:8000/health
- 开发 API 文档：http://localhost:8000/api/docs

更多初始化、邀请家人、AI 配置和常见问题见 [QUICK_START.md](./QUICK_START.md)。

## 生产部署

生产部署以 [docker/DEPLOY.md](./docker/DEPLOY.md) 为权威指南。最小流程：

```bash
cp .env.example .env
# 编辑 .env，设置强密码、域名、SECRET_KEY、AI_KEY_ENCRYPTION_SECRET 等
docker compose -f docker-compose.prod.yml up -d
docker exec -it nezha-backend python init_admin.py
```

生产环境必须关注：

- `SECRET_KEY` 用于登录令牌，不要使用示例值。
- `AI_KEY_ENCRYPTION_SECRET` 用于后台保存的 AI Key 加密，应长期稳定保存。
- `TRUSTED_PROXY_COUNT=1` 适配生产 Caddy 反向代理。
- `backend/backups/`、媒体目录、`.env` 和本地 VPS 配置都包含敏感信息，不能提交或公开同步。

## AI 能力

AI 默认可以关闭，核心发布、上传、评论、点赞、相册流程不依赖 AI。管理员启用模型供应商后，可使用：

- 发布页 AI 文案助手：有文案时润色，无文案但有图片/视频时生成文案。
- AI 管家互动：按角色配置自动评论、自动点赞、频率和风格。
- AI 管理后台：Provider 测试连接、角色、任务、报告、建议和画像视图。

真实模型 Key 不进入测试和仓库；自动化测试使用 fake/mock client。

## 测试

常用门禁：

```bash
docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q
npm --prefix frontend run build
npm --prefix frontend run test:e2e
docker compose config
```

E2E 默认访问 `http://localhost:3000` 和 `http://localhost:8000`。未设置管理员账号环境变量时，写入流会被明确跳过：

```bash
E2E_BASE_URL=http://localhost:8080 \
E2E_API_URL=http://localhost:8000 \
E2E_ADMIN_USERNAME=admin \
E2E_ADMIN_PASSWORD='your-password' \
npm --prefix frontend run test:e2e
```

完整测试说明见 [TESTING.md](./TESTING.md)。
发布候选验收清单见 [RELEASE_CHECKLIST.md](./RELEASE_CHECKLIST.md)。

## 开发

```bash
docker compose up -d postgres redis
npm --prefix frontend install
npm --prefix frontend run dev
docker compose up -d backend celery-worker caddy
```

推荐在提交前运行：

```bash
npm --prefix frontend run build
docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q
git diff --check
```

## 安全与隐私

- 仅邀请可信家庭成员注册。
- 媒体文件访问需要登录鉴权。
- 备份包含密码哈希、邀请码、帖子内容和媒体索引，只能保存在可信或加密位置。
- 不提交 `.env`、`vps配置信息.md`、真实模型 Key、真实家庭数据截图、备份文件和媒体文件。
- 公开部署前请先验证 Caddy、数据库迁移、worker ping 和备份校验。

## 贡献

欢迎 issue 和 PR。请先阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)，并确保改动不破坏家庭核心流程：发布、上传、评论、点赞、通知、相册和登录。

## 许可证

本项目使用 MIT License，见 [LICENSE](./LICENSE)。
