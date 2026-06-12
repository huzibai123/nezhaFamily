# 快速开始

这份指南用于在本机或 Homelab 中快速跑起哪吒家庭。生产部署请以 [docker/DEPLOY.md](./docker/DEPLOY.md) 为准。

## 1. 启动开发栈

```bash
git clone https://github.com/huzibai123/nezhaFamily.git
cd nezhaFamily
docker compose up -d
```

等待服务健康后检查：

```bash
docker compose ps
curl -fsS http://localhost:8000/health
```

访问入口：

- 应用入口：http://localhost:8080
- 直接 Vite 入口：http://localhost:3000
- API 文档：http://localhost:8000/api/docs

## 2. 创建管理员

```bash
docker compose exec backend python init_admin.py
```

按提示输入管理员用户名、邮箱和密码。管理员用于家庭管理、AI 管家配置、运行状态和备份入口。

非交互初始化可使用：

```bash
docker compose exec \
  -e INITIAL_ADMIN_USERNAME=admin \
  -e INITIAL_ADMIN_EMAIL=you@example.com \
  -e INITIAL_ADMIN_PASSWORD='replace-with-a-strong-password' \
  backend python create_admin.py
```

## 3. 邀请家人

1. 用管理员账号登录。
2. 进入“家庭管理”。
3. 复制成员邀请码。
4. 家人在注册页填写邀请码、用户名、邮箱和密码。

## 4. 发布第一条记忆

1. 进入“发布记忆”。
2. 输入文字，或上传图片/视频。
3. 可选择目标相册。
4. 点击“发布”。

AI 启用后，发布页会出现文案助手：

- 有文案时：润色文案。
- 无文案但有媒体时：帮我写文案。
- 无文案且无媒体时：不可生成。

## 5. 常用操作

```bash
# 查看日志
docker compose logs -f backend
docker compose logs -f celery-worker

# 重启服务
docker compose restart backend frontend celery-worker caddy

# 停止服务
docker compose down

# 删除全部开发数据，谨慎使用
docker compose down -v
```

## 6. 可选 AI 配置

AI 默认可以关闭，不影响核心家庭功能。需要使用 AI 文案、AI 评论/点赞时：

1. 管理员进入“AI 管家”。
2. 配置 OpenAI-compatible provider 的 `base_url`、模型名和 Key。
3. 点击“保存并测试”。
4. 在角色页调整自动评论、自动点赞、风格和频率。

后台保存的模型 Key 会加密存储。生产环境请设置长期稳定的 `AI_KEY_ENCRYPTION_SECRET`，见 [docker/DEPLOY.md](./docker/DEPLOY.md)。

## 7. 验证安装

```bash
npm --prefix frontend run build
docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q
npm --prefix frontend run test:e2e
```

如果要跑完整 E2E 写入流，先设置管理员账号环境变量：

```bash
E2E_BASE_URL=http://localhost:8080 \
E2E_API_URL=http://localhost:8000 \
E2E_ADMIN_USERNAME=admin \
E2E_ADMIN_PASSWORD='your-password' \
npm --prefix frontend run test:e2e
```

E2E 会创建带 `E2E-NEZHA-` 前缀的测试内容，并在结束时尽量清理。

## 8. 下一步

- 生产部署：[docker/DEPLOY.md](./docker/DEPLOY.md)
- 测试说明：[TESTING.md](./TESTING.md)
- 清理候选：[CLEANUP_CANDIDATES.md](./CLEANUP_CANDIDATES.md)
