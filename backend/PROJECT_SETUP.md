# 后端项目设置完成说明

## 已创建的文件和目录

### 核心配置模块 (app/core/)
✅ `app/core/config.py` - 配置管理（已存在）
✅ `app/core/security.py` - JWT 认证和密码加密（已存在，已更新支持 UUID）
✅ `app/core/dependencies.py` - FastAPI 依赖注入函数（新增）

### API 路由 (app/api/)
✅ `app/api/__init__.py` - API 模块导出（已更新）
✅ `app/api/auth.py` - 认证相关 API（新增）
  - POST /api/v1/register - 用户注册
  - POST /api/v1/login - 用户登录
  - GET /api/v1/me - 获取当前用户信息
  - POST /api/v1/logout - 用户登出
  - GET /api/v1/users/{user_id} - 获取指定用户信息

### 数据模型 (app/schemas/)
✅ `app/schemas/__init__.py` - Schema 模块导出（已更新）
✅ `app/schemas/user.py` - 用户相关 Schema（新增）
  - UserBase - 用户基础字段
  - UserCreate - 注册请求
  - UserLogin - 登录请求
  - UserResponse - 用户公开信息响应
  - UserProfile - 用户详细信息响应
  - TokenResponse - 登录成功响应
  - InviteCodeCreate - 邀请码创建请求
  - InviteCodeResponse - 邀请码响应
✅ `app/schemas/common.py` - 通用响应模型（新增）
  - APIResponse - 统一 API 响应格式
  - PaginatedResponse - 分页响应

### 应用入口
✅ `app/main.py` - FastAPI 应用入口（已更新，注册了认证路由）

### 工具脚本
✅ `run.py` - 开发服务器启动脚本（新增）
✅ `init_admin.py` - 管理员账号初始化脚本（新增）

### 测试
✅ `tests/test_auth.py` - 认证 API 测试（新增）

### 文档
✅ `README.md` - 后端项目说明文档（新增）
✅ `PROJECT_SETUP.md` - 本文件

## 功能特性

### 已实现功能
- ✅ JWT Token 认证
- ✅ 用户注册（需要邀请码）
- ✅ 用户登录（支持用户名/邮箱）
- ✅ 获取当前用户信息
- ✅ 密码加密存储（bcrypt）
- ✅ 邀请码机制
- ✅ 角色权限（admin/member）
- ✅ 异步数据库操作
- ✅ 依赖注入封装
- ✅ 统一响应模型

### 待实现功能
- [ ] 帖子 CRUD API
- [ ] 评论和回复 API
- [ ] 点赞功能 API
- [ ] 媒体文件上传 API
- [ ] 管理员邀请码管理 API
- [ ] 用户权限中间件增强
- [ ] API 限流
- [ ] 日志记录

## 快速开始

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，修改数据库连接等配置
```

### 3. 启动数据库
```bash
cd ..
docker-compose up -d postgres redis
```

### 4. 运行数据库迁移
```bash
cd backend
alembic upgrade head
```

### 5. 创建管理员账号
```bash
python init_admin.py
```

### 6. 启动开发服务器
```bash
python run.py
# 或
uvicorn app.main:app --reload
```

### 7. 访问 API 文档
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API 使用示例

### 注册新用户
```bash
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "invite_code": "YOUR_INVITE_CODE"
  }'
```

### 用户登录
```bash
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 获取当前用户信息
```bash
curl -X GET http://localhost:8000/api/v1/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 技术架构

### 认证流程
1. 用户使用邀请码注册，密码经过 bcrypt 加密存储
2. 登录时验证密码，成功后返回 JWT Token
3. 后续请求在 Header 中携带 Token: `Authorization: Bearer <token>`
4. 服务端通过 `get_current_user_id` 或 `get_current_user` 依赖注入验证 Token

### 数据库模型
- User 模型使用 UUID 作为主键（更安全）
- 支持邀请链关系（invited_by 字段）
- 每个用户注册时自动生成自己的邀请码

### 安全特性
- 密码使用 bcrypt 哈希
- JWT Token 有效期 7 天（可配置）
- 邀请码机制防止公开注册
- 支持角色权限控制（admin/member）

## 注意事项

1. **生产环境必须修改 SECRET_KEY**
   ```bash
   # 生成强随机密钥
   openssl rand -hex 32
   ```

2. **首次部署必须创建管理员账号**
   ```bash
   python init_admin.py
   ```

3. **数据库迁移**
   - 修改 models 后需要生成新的迁移脚本
   - 使用 `alembic revision --autogenerate -m "描述"`

4. **测试运行**
   ```bash
   pytest tests/
   ```

## 下一步开发计划

1. **帖子功能** (app/api/posts.py)
   - 创建帖子
   - 编辑帖子
   - 删除帖子
   - 获取时间线
   - 帖子详情

2. **评论功能** (app/api/comments.py)
   - 发表评论
   - 回复评论
   - 删除评论
   - 获取评论列表

3. **点赞功能** (app/api/likes.py)
   - 点赞/取消点赞
   - 获取点赞列表

4. **媒体上传** (app/api/media.py)
   - 图片上传
   - 视频上传
   - 缩略图生成（Celery 异步任务）

## 联系方式

如有问题，请查看：
- 项目文档：`README.md`
- PRD 文档：`../nezha-family.prd.md`
- CLAUDE 配置：`../CLAUDE.md`
