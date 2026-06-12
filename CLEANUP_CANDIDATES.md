# Cleanup Candidates

> 开源发布前后的清理备忘。本文档只记录候选项，不自动删除真实数据、密钥、备份或运维资料。

审计时间：2026-06-12
审计基准：`main@8b25ec2` 之后的开源发布收口阶段

## 处理原则

- 不提交 `.env`、真实模型 Key、`vps配置信息.md`、`BUG_SCAN_2026-06-11.md`、真实家庭数据截图、媒体文件和备份。
- 已跟踪文件删除前，需要确认没有代码、文档或部署链路引用，并跑前端构建、后端测试和 compose config。
- 未跟踪本地报告可按需保留在本机，不作为开源仓库的一部分。

## 本地未跟踪或已忽略文件

| 文件/模式 | 状态 | 建议 |
| --- | --- | --- |
| `vps配置信息.md`、`*配置信息*.md` | 已被 `.gitignore` 覆盖 | 保留本地，不提交 |
| `BUG_SCAN_2026-06-11.md` | 本地扫描报告，当前未跟踪 | 保留本地或归档，不提交 |
| `Dockerfile.test` | 旧 Playwright 镜像草稿，已忽略 | 可删除；正式 E2E 已迁到 `frontend/e2e` |
| `tests/test_e2e_playwright.py` | 旧 E2E 草稿，硬编码账号和端口，已忽略 | 可删除；不要纳入正式链路 |
| `COMPLETION_REPORT.md`、`DEVELOPMENT_COMPLETE.md`、`TEST_SUCCESS.md` | 会话报告/旧测试记录，已忽略 | 可归档或删除 |
| `SESSION_*.md` | 会话交接记录，已忽略 | 可归档或删除 |
| `frontend/playwright-report/`、`frontend/test-results/` | Playwright 产物，已忽略 | 失败排查后可删除 |

## 已跟踪但可后续确认的文件

| 文件 | 当前状态 | 建议 |
| --- | --- | --- |
| `backend/app/schemas/common.py` | 文件内标记 `DEPRECATED`，业务代码未直接依赖 | 后续单独清理并同步旧文档 |
| `backend/validate_migration.py` | 人工迁移诊断脚本 | 可保留为运维工具，或确认无引用后删除 |
| `docker/nginx.conf` | 备用 Nginx 配置，当前生产构建使用 `frontend/nginx.conf` | 可保留历史备用，或后续删除 |
| `backend/create_admin.py` | 与 `init_admin.py` 功能重叠，但支持环境变量初始化 | 保留；部署文档仍引用 |

## 前端模板残留

上一阶段已删除未引用的 Vite 模板文件 `HelloWorld.vue` 和旧样式入口；后续只需确认新增页面没有引入新的 scaffold 资产。

## 清理前验证

```bash
npm --prefix frontend run build
docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q
docker compose config
POSTGRES_PASSWORD=change-me-postgres REDIS_PASSWORD=change-me-redis SECRET_KEY=change-me-secret-key-32-bytes-min AI_KEY_ENCRYPTION_SECRET=change-me-ai-key-secret-32-bytes-min ALLOWED_ORIGINS=https://family.example.com DOMAIN=family.example.com ADMIN_EMAIL=admin@example.com TRUSTED_PROXY_COUNT=1 AI_ENABLED=false docker compose -f docker-compose.prod.yml config
git diff --check
```
