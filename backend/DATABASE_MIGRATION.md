# 数据库迁移指南

## 概述

本项目使用 Alembic 管理数据库迁移。所有的数据库表结构都通过 SQLAlchemy ORM 模型定义，并由 Alembic 自动生成迁移脚本。

## 目录结构

```
backend/
├── alembic/                    # Alembic 迁移目录
│   ├── versions/               # 迁移脚本存放目录
│   │   └── 20260604_2330_001_initial_initial_database_schema.py  # 初始化迁移
│   ├── env.py                  # Alembic 环境配置
│   └── script.py.mako          # 迁移脚本模板
├── alembic.ini                 # Alembic 配置文件
├── app/
│   ├── db/
│   │   ├── base.py             # SQLAlchemy Base 类
│   │   ├── session.py          # 异步 Session 管理
│   │   └── __init__.py
│   └── models/                 # SQLAlchemy 模型
│       ├── user.py             # 用户模型
│       ├── post.py             # 帖子模型
│       ├── comment.py          # 评论模型
│       ├── like.py             # 点赞模型
│       ├── media.py            # 媒体文件模型
│       └── __init__.py
```

## 数据库模型说明

### 1. User（用户表）
- UUID 主键
- 用户名、邮箱、密码哈希
- 角色（admin/member）
- 邀请码机制（invite_code、invited_by）
- 头像 URL

### 2. Post（帖子表）
- UUID 主键
- 作者 ID（外键关联 users）
- 内容（文本）
- 媒体 URLs（JSONB 格式）
- 点赞数、评论数（冗余统计）
- 创建时间（用于时间线排序）

### 3. Comment（评论表）
- UUID 主键
- 帖子 ID（外键关联 posts）
- 作者 ID（外键关联 users）
- 父评论 ID（支持嵌套回复）
- 内容（文本）
- 点赞数

### 4. Like（点赞表）
- UUID 主键
- 用户 ID（外键关联 users）
- 目标类型（post/comment）
- 目标 ID（帖子或评论的 ID）
- 唯一约束（user_id, target_type, target_id）防止重复点赞

### 5. MediaFile（媒体文件表）
- UUID 主键
- 上传者 ID（外键关联 users）
- 文件类型（image/video）
- 文件路径、缩略图路径
- 文件大小、MIME 类型
- 宽度、高度、时长（视频）

## 使用方法

### 环境准备

1. 安装依赖：
```bash
cd backend
pip install alembic sqlalchemy asyncpg psycopg2-binary
```

2. 配置数据库连接（.env 文件）：
```bash
DATABASE_URL=postgresql+asyncpg://nezha:nezha123@localhost:5432/nezha_family
```

### 执行迁移

1. **首次初始化数据库**：
```bash
cd backend
alembic upgrade head
```

2. **查看当前迁移状态**：
```bash
alembic current
```

3. **查看迁移历史**：
```bash
alembic history
```

4. **回滚到上一个版本**：
```bash
alembic downgrade -1
```

5. **回滚到初始状态（清空所有表）**：
```bash
alembic downgrade base
```

### 创建新的迁移

当修改模型后，需要创建新的迁移脚本：

1. **自动生成迁移**：
```bash
alembic revision --autogenerate -m "描述变更内容"
```

2. **手动创建空白迁移**：
```bash
alembic revision -m "描述变更内容"
```

3. **检查生成的迁移脚本**，确认无误后执行：
```bash
alembic upgrade head
```

## 索引说明

为了优化查询性能，已创建以下索引：

- `users.username` - 用户名查询
- `users.email` - 邮箱查询
- `posts.created_at DESC` - 时间线倒序查询（核心功能）
- `posts.author_id` - 按作者查询
- `comments.post_id` - 按帖子查询评论
- `comments.parent_id` - 查询子回复
- `likes(target_type, target_id)` - 查询点赞数
- `media_files.uploader_id` - 按上传者查询

## 注意事项

1. **异步 vs 同步**：
   - SQLAlchemy 模型和业务代码使用异步（asyncpg）
   - Alembic 迁移使用同步（psycopg2），env.py 会自动转换 URL

2. **UUID 类型**：
   - 所有主键使用 UUID 代替自增 ID，更安全且支持分布式
   - PostgreSQL 原生支持 UUID，性能优秀

3. **JSONB 字段**：
   - `posts.media_urls` 使用 JSONB 存储媒体列表
   - 支持 JSON 查询和索引

4. **级联删除**：
   - 删除用户时，自动删除其帖子、评论、点赞、媒体文件
   - 删除帖子时，自动删除评论和点赞
   - 删除评论时，自动删除子回复

5. **时间戳**：
   - `created_at` 使用 `server_default=now()` 由数据库自动填充
   - `updated_at` 使用 `onupdate` 自动更新

## 故障排查

1. **连接失败**：
   - 检查 PostgreSQL 是否运行：`pg_isready`
   - 检查环境变量 `DATABASE_URL` 是否正确

2. **迁移失败**：
   - 查看错误信息，可能是表已存在或外键约束冲突
   - 如需重新初始化，执行 `alembic downgrade base` 再 `alembic upgrade head`

3. **模型不一致**：
   - 确保 `app/db/base.py` 导入了所有模型
   - 重新生成迁移：`alembic revision --autogenerate -m "fix schema"`

## 下一步

完成数据库初始化后，可以开始开发：

1. 实现用户认证 API（阶段 2）
2. 实现帖子 CRUD API（阶段 3）
3. 实现媒体上传 API（阶段 4）
4. 实现评论和点赞 API（阶段 5）
