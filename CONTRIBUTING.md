# Contributing

感谢你愿意改进哪吒家庭。这个项目优先服务“一个家庭自托管一个实例”的私有场景，所以稳定、隐私和可维护性比功能膨胀更重要。

## 开发原则

- 不破坏核心流程：登录、发布、上传、评论、点赞、通知、相册和备份。
- AI 功能必须可关闭；AI 失败不能阻断家庭核心功能。
- 不提交真实密钥、真实家庭数据、备份、媒体文件、VPS 配置或本地扫描报告。
- 后端优先补测试；前端至少保证构建通过，涉及核心流程时补 E2E 或稳定的契约检查。

## 本地启动

```bash
docker compose up -d
docker compose exec backend python init_admin.py
npm --prefix frontend install
```

应用入口通常是 `http://localhost:8080`，直接 Vite 入口是 `http://localhost:3000`。

## 提交前检查

```bash
docker compose run --rm --no-deps -v "$PWD:/workspace" -w /workspace/backend backend pytest -q
npm --prefix frontend run build
npm --prefix frontend run test:e2e
docker compose config
git diff --check
```

完整 E2E 写入流需要设置：

```bash
E2E_BASE_URL=http://localhost:8080 \
E2E_API_URL=http://localhost:8000 \
E2E_ADMIN_USERNAME=admin \
E2E_ADMIN_PASSWORD='your-password' \
npm --prefix frontend run test:e2e
```

## Pull Request 建议

- 一次 PR 聚焦一个主题。
- 描述用户可见变化、风险和测试结果。
- 涉及部署、备份、AI Key、数据库迁移时同步更新文档。
- 不把格式化、重命名和业务改动混在一起，除非是同一收口任务的一部分。
