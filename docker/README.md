# Docker 文档入口

哪吒家庭的部署文档以 [DEPLOY.md](./DEPLOY.md) 为准。那里包含：

- 开发和生产 Docker Compose 启动方式。
- `.env` 必填项、AI Key 加密迁移、Caddy 路由和健康检查。
- 数据库迁移、管理员初始化、备份与恢复演练。
- Caddy validate、worker ping、生产 smoke checklist。

发布候选验收顺序见仓库根目录 [../RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md)。

快速开发启动：

```bash
docker compose up -d
docker compose exec backend python init_admin.py
```

生产部署请不要只复制片段，先完整阅读 [DEPLOY.md](./DEPLOY.md)。
