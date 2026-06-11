# Cleanup Candidates

> 记录当前审计发现的无用文件、临时文件和待确认代码。
> 本文档只做收尾备忘；当前阶段不删除任何文件。

审计时间：2026-06-10
审计基准：`main` / `origin/main` 最新提交 `38a8b06`

## 处理原则

- 以 GitHub 上的 `main` 作为部署来源时，未提交到 Git 的代码文件不影响服务器部署。
- 不删除本地数据、密钥、媒体、备份和 VPS 运维资料，除非已确认另有备份。
- 已跟踪文件如果要删除，需要同步清理相关文档引用，并跑一次构建和测试。

## 可直接删除的本地未跟踪文件

这些文件当前未进入 Git，也没有被 `package.json`、Docker Compose 或 CI 引用。

| 文件 | 原因 | 建议 |
| --- | --- | --- |
| `Dockerfile.test` | Playwright E2E 测试镜像草稿，未被部署或脚本引用 | 项目收尾时可删除 |
| `tests/test_e2e_playwright.py` | 未跟踪；硬编码 `admin/admin123456` 和 localhost 端口；当前不是稳定测试链路 | 项目收尾时可删除，或重写后纳入正式 E2E |
| `frontend/package.json.bak` | 旧依赖备份文件，不参与构建 | 可删除 |
| `COMPLETION_REPORT.md` | 会话完成报告，不参与项目运行 | 可删除或归档 |
| `DEVELOPMENT_COMPLETE.md` | 历史完成报告，部分内容已过期 | 可删除或归档 |
| `SESSION_HANDOFF_2026-06-10.md` | 会话交接记录，不参与项目运行 | 可删除或归档 |
| `SESSION_SUMMARY.md` | 会话摘要，不参与项目运行 | 可删除或归档 |
| `TEST_SUCCESS.md` | 早期测试记录，内容已过期 | 可删除或归档 |

## 已跟踪但可考虑删除的文件

这些文件已经在 Git 中，删除前建议同步文档并重新验证。

| 文件 | 当前状态 | 删除影响 | 建议 |
| --- | --- | --- | --- |
| `backend/app/schemas/common.py` | 文件内标记 `DEPRECATED`，当前业务代码无引用 | 不影响运行；但 `backend/PROJECT_SETUP.md` 仍提到 `APIResponse` / `PaginatedResponse` | 可删除，并同步更新旧文档 |
| `backend/validate_migration.py` | 人工迁移诊断脚本，不在运行链路中 | 不影响部署和运行；少一个诊断工具 | 可删除，或保留作运维辅助 |
| `docker/nginx.conf` | 与 `frontend/nginx.conf` 内容几乎相同，但实际 Dockerfile 使用的是 `frontend/nginx.conf` | 不影响当前 Docker 构建；`docker/` 下少一个备用 Nginx 配置 | 可删除，或保留为历史备用配置 |

## 未使用但需确认的 Schema

| 文件/符号 | 当前状态 | 建议 |
| --- | --- | --- |
| `backend/app/schemas/user.py` 的 `InviteCodeCreate` | 仅在 `backend/app/schemas/__init__.py` 导出，当前业务代码无引用 | 如果确认不做独立邀请码创建 API，可删除并同步更新 `__init__.py` 与旧文档 |
| `backend/app/schemas/user.py` 的 `InviteCodeResponse` | 仅在 `backend/app/schemas/__init__.py` 导出，当前业务代码无引用；实际后台邀请码响应使用 `AdminInviteCodeResponse` | 同上 |

## 暂时保留的重复/辅助脚本

| 文件 | 原因 | 建议 |
| --- | --- | --- |
| `backend/init_admin.py` | 首次部署创建管理员会用；文档和部署提示主要引用它 | 保留 |
| `backend/create_admin.py` | 与 `init_admin.py` 功能重叠，但支持环境变量方式创建管理员，适合非交互场景；`CLAUDE.md`、`docker/DEPLOY.md`、`docker/README.md` 有引用 | 暂时保留；若删除，需同步文档 |

## 前端模板残留

这些文件来自 Vite/Vue 模板，当前应用未引用。它们已进入 Git，如要删除需单独提交。

| 文件 | 原因 | 建议 |
| --- | --- | --- |
| `frontend/src/components/HelloWorld.vue` | 未被任何页面或入口引用 | 可删除 |
| `frontend/src/assets/hero.png` | 仅被 `HelloWorld.vue` 引用 | 删除 `HelloWorld.vue` 时一并删除 |
| `frontend/src/assets/vite.svg` | 仅被 `HelloWorld.vue` 引用 | 删除 `HelloWorld.vue` 时一并删除 |
| `frontend/src/assets/vue.svg` | 仅被 `HelloWorld.vue` 引用 | 删除 `HelloWorld.vue` 时一并删除 |
| `frontend/public/icons.svg` | 仅被 `HelloWorld.vue` 引用 | 删除 `HelloWorld.vue` 时一并删除 |
| `frontend/public/test.html` | 手工测试页，不参与应用入口 | 可删除 |
| `frontend/src/style.css` | 未被 `main.ts` 或其它入口导入 | 可删除 |
| `frontend/src/assets/styles/main.css` | 文件内容标注已被 `globals.css` 替代，当前无引用 | 可删除 |

## 本地生成物与缓存

这些通常不进入 Git，清理时可按需删除。

| 路径/模式 | 说明 |
| --- | --- |
| `.playwright-mcp/` | 浏览器验证日志和截图 |
| `backend/**/__pycache__/` | Python 字节码缓存 |
| `backend/.pytest_cache/` | pytest 缓存 |
| `backend/.ruff_cache/` | ruff 缓存 |
| `frontend/dist/` | 前端构建产物 |
| `frontend/node_modules/` | 前端依赖 |
| `backend/venv/` | 本地 Python 虚拟环境 |
| `nezha-*.png` | 本地视觉验证截图 |
| `mitm_mcp_traffic.db` | 本地调试流量数据库 |
| `test_login.py` | 本地临时测试脚本 |
| `test_git/` | 本地临时 Git 测试目录 |

## 可考虑补充的忽略规则

根目录 `.gitignore` 已覆盖大多数本地产物；`backend/.gitignore` 已覆盖 `backend/.ruff_cache/`。后续可考虑补充：

| 规则 | 原因 |
| --- | --- |
| `*.bak` | 避免 `frontend/package.json.bak` 这类备份文件误入库 |
| `COMPLETION_REPORT.md`、`DEVELOPMENT_COMPLETE.md`、`SESSION_*.md`、`TEST_SUCCESS.md` | 避免会话报告/临时总结误入库 |

## 不应误删

| 路径/文件 | 原因 |
| --- | --- |
| `.env`、`backend/.env` | 本地/部署环境变量，不能进 Git，但运行需要 |
| `backend/media/` | 用户上传媒体数据 |
| `backend/backups/` | 本地备份数据 |
| `vps配置信息.md` | 已被 Git 跟踪且可能包含运维信息；`.gitignore` 对已跟踪文件不生效，需单独确认处理策略 |
| `backend/alembic/versions/*` | 数据库迁移链路，不能当作历史文件删除 |
| `docker-compose*.yml`、`docker/Caddyfile*`、`docker/Dockerfile.*`、`docker/deploy.sh`、`docker/init-db.sql` | 当前部署链路依赖 |

## 过时文档待更新

这些不是删除项，但文档描述与当前代码不完全一致，后续整理文档时建议修正。

| 文件 | 过时点 |
| --- | --- |
| `CLAUDE.md` | 仍提到根目录 `package.json` 是 React/过时，但当前已是 Vue monorepo helper |
| `CLAUDE.md` | 仍提到前端存在两套 axios/token key，但当前已统一到 `frontend/src/api/index.ts` 和 `localStorage('token')` |
| `CLAUDE.md` | 仍提到 `get_current_user` 重复实现问题；当前 `core/dependencies.py` 已复用 `core/security.py` |
| `CLAUDE.md` | 仍提到媒体静态服务/Celery 任务缺失；当前已有 `media.public_router` 和 `compress_image` / `generate_thumbnail` |
| `docker/README.md`、`docker/DEPLOY.md` | 两份 Docker 部署文档内容高度重复，当前需要双写同类部署说明 | 后续可合并为单一权威部署文档，另一份改为跳转说明 |

## 清理前验证建议

执行正式删除后，至少运行：

```bash
npm --prefix frontend run build
docker compose exec -T backend pytest -q
DOMAIN=example.com ADMIN_EMAIL=admin@example.com POSTGRES_PASSWORD=change_me REDIS_PASSWORD=change_me SECRET_KEY=change_me_secret ALLOWED_ORIGINS=https://example.com docker compose -f docker-compose.prod.yml config
```
