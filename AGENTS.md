# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述

**哪吒家庭（Nezha Family）** - 私有化家庭分享平台

一个开源的、可自托管的家庭内容分享平台，类似亲宝宝 App，但完全私有部署。用户可通过 Docker Compose 在自己的 VPS/NAS 上一键部署，实现图片/视频分享、评论互动、时间线浏览等功能，数据完全自主可控。

**核心定位**：
- 仅限家庭内部使用（不做公开分享）
- 单租户架构（一个实例服务一个家庭）
- 一键 Docker 部署（面向 Homelab 玩家）

## 技术栈

### 后端
- **框架**: FastAPI ^0.110（异步 API，类型提示）
- **ORM**: SQLAlchemy ^2.0（异步模式）
- **数据验证**: Pydantic ^2.6
- **数据库**: PostgreSQL ^16
- **缓存**: Redis ^7
- **任务队列**: Celery ^5.3（异步处理图片压缩/视频转码）
- **认证**: JWT（JSON Web Token）

### 前端
- **框架**: Vue 3 + Vite ^3.4
- **UI**: Tailwind CSS ^3.4
- **目标**: 响应式设计，适配移动端，微信浏览器兼容

### 基础设施
- **反向代理**: Caddy ^2.7（自动 HTTPS）
- **部署**: Docker Compose
- **存储**: 本地磁盘 或 Cloudflare R2（待定）

## 项目结构（规划）

```
nezha-family/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   │   ├── auth.py  # 认证相关
│   │   │   ├── posts.py # 帖子 CRUD
│   │   │   ├── comments.py
│   │   │   └── media.py
│   │   ├── models/      # SQLAlchemy 模型
│   │   ├── schemas/     # Pydantic 模型
│   │   ├── core/        # 配置、安全、依赖注入
│   │   └── tasks/       # Celery 异步任务
│   ├── alembic/         # 数据库迁移
│   ├── tests/
│   └── requirements.txt
├── frontend/            # Vue 3 前端
│   ├── src/
│   │   ├── components/  # 可复用组件
│   │   ├── views/       # 页面视图
│   │   ├── router/
│   │   ├── stores/      # Pinia 状态管理
│   │   └── api/         # API 调用封装
│   ├── public/
│   └── package.json
├── docker/
│   ├── Caddyfile        # Caddy 配置
│   └── nginx.conf       # 备选方案
├── docker-compose.yml   # 开发环境
├── docker-compose.prod.yml  # 生产环境
├── .env.example
└── README.md
```

## 数据库设计

核心表结构（参考 PRD 中的完整 Schema）：

- **users**: 用户表（邀请码机制、admin/member 角色）
- **posts**: 帖子表（内容 + 媒体 URLs，JSONB 存储）
- **comments**: 评论表（支持嵌套回复，parent_id）
- **likes**: 点赞表（防重复，UNIQUE 约束）
- **media_files**: 媒体文件元数据

**重要索引**：
- `posts(created_at DESC)` - 时间线查询
- `comments(post_id)` - 评论列表
- `likes(target_type, target_id)` - 点赞查询

## 核心功能（MVP v1）

**必须有（缺一不可）**：
1. 用户认证：邀请码注册、JWT 登录/登出
2. 帖子系统：发布/编辑/删除图片+文字、视频+文字帖子
3. 社交互动：评论、回复评论（嵌套）、点赞
4. 内容浏览：时间线（按时间倒序）、帖子详情页
5. Docker 部署：docker-compose 一键启动

**明确不做（v1）**：
- 公开分享链接
- 多家庭租户
- 原生 App（仅响应式 Web）
- 复杂权限系统（只有 admin/member）

## 开发规范

### 代码风格
- Python: black + ruff 格式化，类型提示必须
- TypeScript/Vue: Prettier 格式化
- 4 空格缩进，行长 100 字符

### API 设计
- RESTful 风格：`/api/v1/{resource}`
- 认证：Bearer Token（JWT）
- 响应格式统一：
  ```json
  {
    "success": true,
    "data": {...},
    "message": "操作成功"
  }
  ```

### 安全要求
- 密码使用 bcrypt 加密
- 所有用户输入必须验证（Pydantic）
- 媒体文件访问需鉴权（仅家庭成员）
- SQL 注入防护（ORM 参数化查询）
- XSS 防护（前端转义输出）

### 文件存储
- 媒体文件路径格式：`/{year}/{month}/{uuid}.{ext}`
- 图片自动生成缩略图（最大 1080p）
- 视频可选转码（H.264，待定）

## 实施阶段

项目按 8 个阶段推进（详见 `nezha-family.prd.md`）：

1. **项目初始化与基础架构**（当前阶段）
   - 初始化前后端项目结构
   - 配置 Docker Compose 开发环境
   - 数据库 Schema 设计与迁移脚本

2. **用户认证系统**
   - JWT 认证
   - 邀请码机制
   - 权限中间件

3. **帖子核心功能**（可与阶段 4 并行）
   - 帖子 CRUD API
   - 时间线分页

4. **媒体上传与处理**（可与阶段 3 并行）
   - 文件上传 API
   - Celery 异步压缩/缩略图

5. **评论与互动系统**
   - 评论/回复 API
   - 点赞机制

6. **前端界面开发**
   - Vue 3 组件
   - 响应式布局

7. **部署与文档**
   - 生产环境配置
   - 部署文档

8. **测试与优化**
   - 单元测试/集成测试
   - 性能优化

## 技术决策

### 为什么选 FastAPI 而不是 Django/Flask？
- **异步性能**：处理大文件上传/下载不阻塞
- **类型提示**：AI 生成代码更准确，减少 bug
- **自动文档**：Swagger UI 开箱即用，利于开源推广
- **权衡**：需手动实现用户系统（Django 有开箱即用的 Admin）

### 存储方案（待决策）
- **本地磁盘**：零成本，简单直接
- **Cloudflare R2**：免费 10GB，CDN 加速
- **决策依据**：性能测试 + 用户需求（20GB 预算）

## 未解决的问题

开发过程中需要决策的事项（参考 PRD "未解决的问题" 部分）：

1. 存储方案：本地磁盘 vs Cloudflare R2
2. 备份策略：rsync vs rclone，自动化方案
3. 视频转码：是否 v1 实现，HLS 流式传输？
4. AI 功能：相册分类、人脸识别的优先级

## 相关文档

- **PRD**: `./nezha-family.prd.md` - 完整产品需求文档
- **架构图**: 见 PRD "系统架构" 部分
- **数据库 Schema**: 见 PRD "数据模型" 部分（完整 SQL）
