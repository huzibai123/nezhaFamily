# 哪吒家庭 - 使用指南

## 🚀 快速开始（5 分钟搞定）

### 1. 启动项目

```bash
cd nezha-family
docker-compose up -d
```

等待 30 秒，所有服务启动完成。

### 2. 访问应用

打开浏览器访问：**http://localhost:3000**

### 3. 初始化管理员并登录

```bash
docker exec -it nezha-backend-dev python init_admin.py
```

按提示设置管理员用户名、邮箱和密码，然后用刚创建的账号登录。

### 4. 开始使用

- ✅ 发布第一条帖子
- ✅ 上传照片/视频
- ✅ 评论和点赞
- ✅ 浏览时间线

---

## 📱 功能演示

### 发布帖子

1. 点击右上角 **"+"** 或 **"发布"** 按钮
2. 输入文字内容
3. （可选）上传图片或视频
4. 点击 **"发布"**

### 评论互动

1. 在帖子下方评论框输入内容
2. 点击 **"发送"** 发表评论
3. 点击评论可以进行回复

### 点赞

- 点击 ❤️ 图标即可点赞
- 再次点击取消点赞

---

## 🛠️ 常见问题

### Q: 如何停止服务？

```bash
docker-compose down
```

### Q: 如何查看日志？

```bash
docker-compose logs -f
```

### Q: 如何重置数据库？

```bash
docker-compose down -v  # 删除所有数据
docker-compose up -d    # 重新启动
```

### Q: 如何创建新用户？

1. 管理员登录后，进入“家庭管理”
2. 在成员卡片里生成或复制邀请码
3. 新用户使用邀请码注册

### Q: 前端无法访问后端？

检查 CORS 配置：

```bash
# 查看后端日志
docker-compose logs backend | grep CORS
```

---

## 🔧 配置修改

### 修改端口

编辑 `docker-compose.yml`：

```yaml
services:
  frontend:
    ports:
      - "3000:3000"  # 改为你想要的端口
  backend:
    ports:
      - "8000:8000"
```

### 修改数据库密码

编辑 `.env` 文件：

```env
POSTGRES_PASSWORD=your_new_password
```

然后重启：

```bash
docker-compose down -v
docker-compose up -d
```

---

## 📊 系统状态检查

### 检查所有服务

```bash
docker-compose ps
```

应该看到 4 个服务都是 `Up` 状态：
- nezha-frontend-dev
- nezha-backend-dev
- nezha-postgres-dev
- nezha-redis-dev

### 测试后端 API

```bash
curl http://localhost:8000/health
```

返回 `{"status":"healthy"}` 表示正常。

### 测试前端

```bash
curl http://localhost:3000
```

返回 HTML 页面表示正常。

---

## 🎉 完成！

现在你已经成功部署了哪吒家庭！

**下一步：**
- 邀请家人注册
- 开始分享美好时刻
- 享受私有化的家庭空间

**需要帮助？**
- 查看 API 文档：http://localhost:8000/api/docs
- 查看部署说明：`docker/DEPLOY.md`
- 查看产品需求：`nezha-family.prd.md`

---

*祝你使用愉快！💙*
