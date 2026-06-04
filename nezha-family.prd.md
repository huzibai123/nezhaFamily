# 哪吒家庭 - 私有化家庭分享平台

## 问题陈述

现有家庭分享平台（如亲宝宝 App）虽然功能完善，但数据完全托管在第三方服务器上，用户无法真正掌控自己的家庭记忆数据。对于重视数据主权和隐私的家庭用户，缺少一个易部署、功能完整、完全自主可控的私有化解决方案。当前的替代方案（微信群、云盘）要么内容易丢失，要么缺少社交互动功能。

## 证据

- 用户痛点：现有工具（亲宝宝 App）功能满足需求，但数据私有化诉求无法满足
- 市场空白：现有开源方案（Immich、PhotoPrism）偏向个人相册管理，缺少家庭社交互动功能（评论、回复、时间线）
- 目标用户画像：拥有 NAS/VPS 的 Homelab 玩家，具备基本 Docker 部署能力，重视数据主权

## 提议的解决方案

构建一个开源的、一键部署的私有化家庭分享平台，结合亲宝宝的社交互动体验和自托管的数据主权优势。用户可以通过 Docker Compose 在自己的 VPS/NAS 上快速部署，实现图片/视频/文本内容分享、评论互动、时间线浏览等核心功能，数据完全掌握在自己手中。

选择这个方案的原因：
- 现有开源方案都缺少"家庭社交"这一核心场景
- 技术栈成熟（FastAPI + Vue 3），AI 辅助开发效率高
- 一键部署降低使用门槛，有利于开源推广

## 核心假设

我相信**一键 Docker 部署 + 简洁的时间线界面**能解决**家庭数据私有化**的问题。
我们通过以下指标验证假设是否成立：**100 个家庭成功部署并持续使用超过 3 个月**。

## 我们明确不做的事

- **不做公开分享** - 仅限家庭内部成员访问，不支持公开链接分享
- **不做多租户** - 一个实例只服务一个家庭（简化架构和权限模型）
- **不做原生 App（v1）** - 仅提供响应式 Web 应用，适配移动浏览器（后期根据反馈决定是否开发）
- **不做复杂权限系统** - v1 仅支持管理员/成员两种角色，不做细粒度权限控制
- **不做付费功能** - 完全开源免费，不设置功能限制

## 成功指标

| 指标 | 目标 | 如何衡量 |
|--------|--------|--------------|
| 部署数量 | 100 个家庭实例 | GitHub Releases 下载量 + Docker Hub pulls |
| 活跃度 | 3 个月留存率 > 60% | 匿名统计（可选功能，用户可关闭） |
| 社区反馈 | GitHub Star > 500 | GitHub 数据 |
| 功能完整度 | 核心功能可用率 100% | 测试用例通过率 |

## 未解决的问题

- [ ] **存储方案选择**：Cloudflare R2 对象存储 vs 本地磁盘，需要性能测试和成本对比
- [ ] **备份策略实现**：自动备份到本地物理机的具体技术方案（rsync? rclone?）
- [ ] **原生 App 开发**：是否需要开发独立 App（小程序/原生 App），需根据用户反馈决策
- [ ] **视频转码策略**：海外 VPS 视频加载速度优化方案（HLS 流式传输? 分辨率自适应?）
- [ ] **AI 功能集成**：相册自动分类、人脸识别等 AI 功能的优先级和实现方式

---

## 用户与场景

**主要用户**
- **谁**：拥有 NAS/VPS 的 Homelab 玩家，熟悉 Docker 基本操作，重视数据隐私和主权
- **当前行为**：使用亲宝宝 App 或微信群分享家庭内容，但担心数据安全或平台倒闭
- **触发时刻**：当拍摄家庭照片/视频后，希望快速分享给所有家庭成员并保留互动记录
- **成功状态**：家庭成员每周主动分享内容，平台成为家庭记忆的主要载体，数据完全自主可控

**要完成的任务**
当家人拍了照片/视频时，我想要快速分享给所有家庭成员并保留评论互动，这样我就能将家庭回忆永久保存且完全掌控数据。

**非目标用户**
- 完全不懂技术的普通用户（无法完成 Docker 部署）
- 企业/商业用途（本项目仅面向家庭场景）
- 需要公开分享内容的博主/自媒体
- 超大家族（50+ 人，需要复杂权限管理）

---

## 解决方案细节

### 核心能力（MoSCoW 优先级）

| 优先级 | 功能 | 理由 |
|----------|------------|-----------|
| Must | 用户注册/登录（邀请码机制） | 保证私密性，仅限家庭成员访问 |
| Must | 发布图片+文字帖子 | 核心分享功能 |
| Must | 发布视频帖子 | 视频是家庭记忆的重要载体 |
| Must | 评论功能 | 社交互动的基础 |
| Must | 评论回复（嵌套） | 完整的互动体验 |
| Must | 时间线（按时间排序） | 浏览家庭动态的主要方式 |
| Should | 点赞功能 | 增强互动体验 |
| Should | 相册视图（按日期分组） | 便于查找特定时期的内容 |
| Should | 实时通知（新评论/新帖子） | 提升活跃度 |
| Could | AI 相册分类（人脸识别/场景分类） | 提升内容组织能力，但非刚需 |
| Could | 视频自动转码（多分辨率） | 优化加载速度，但增加复杂度 |
| Won't | 公开分享链接 | 与"家庭内部"定位冲突，v1 不做 |
| Won't | 多家庭租户支持 | 增加架构复杂度，v1 不做 |
| Won't | 原生移动 App | 响应式 Web 优先，后期根据反馈决定 |

### MVP 范围

**v1 最小可用版本必须包含：**
1. **用户系统**：邀请码注册、登录/登出、基本权限控制（管理员/成员）
2. **内容发布**：图片+文字帖子、视频+文字帖子、编辑/删除自己的帖子
3. **社交互动**：评论、回复评论、点赞
4. **内容浏览**：时间线（最新在前）、单帖详情页
5. **部署方案**：Docker Compose 一键部署、环境变量配置

**如果缺少以上任一功能，产品不可用。**

### 用户流程

**核心路径：从分享到互动**

```
1. 家人 A 拍摄照片/视频
   ↓
2. 打开网站（手机浏览器/微信内置浏览器）
   ↓
3. 点击"发布"按钮
   ↓
4. 上传图片/视频 + 填写文字描述
   ↓
5. 发布成功，出现在时间线首位
   ↓
6. 家人 B/C 看到新内容，点赞/评论
   ↓
7. 家人 A 收到通知，查看评论并回复
```

**辅助路径：**
- 管理员邀请新成员：生成邀请码 → 分享给家人 → 家人注册
- 浏览历史内容：时间线滚动加载 → 点击帖子查看详情 → 查看全部评论
- 编辑/删除内容：进入帖子详情 → 点击"编辑/删除"（仅作者可见）

---

## 技术方案

**可行性评估**: 高

### 技术栈

| 层级 | 技术选型 | 版本 | 理由 |
|------|----------|------|------|
| **前端** | Vue 3 + Vite | ^3.4 | 响应式设计，打包体积小，适配移动端 |
| **UI 框架** | Tailwind CSS | ^3.4 | 快速构建响应式界面 |
| **后端** | FastAPI | ^0.110 | 异步性能好，类型提示友好 AI 开发 |
| **ORM** | SQLAlchemy | ^2.0 | 成熟稳定，支持异步 |
| **数据验证** | Pydantic | ^2.6 | 与 FastAPI 无缝集成 |
| **数据库** | PostgreSQL | ^16 | 关系型数据，事务支持 |
| **缓存** | Redis | ^7 | 会话管理、任务队列 |
| **任务队列** | Celery | ^5.3 | 异步处理图片压缩/视频转码 |
| **反向代理** | Caddy | ^2.7 | 自动 HTTPS，配置简单 |
| **部署** | Docker Compose | ^2.24 | 一键部署 |

### 系统架构

```
┌─────────────────────────────────────────────┐
│  前端 (Vue 3 SPA)                            │
│  - 时间线组件                                │
│  - 发布/编辑组件                             │
│  - 评论/回复组件                             │
│  - 响应式布局（适配手机）                    │
└─────────────────────────────────────────────┘
                    ↓ HTTPS
┌─────────────────────────────────────────────┐
│  Caddy (反向代理)                            │
│  - 自动 HTTPS (Let's Encrypt)               │
│  - 静态资源服务                              │
│  - API 请求转发                              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  FastAPI (后端 API)                          │
│  - /api/auth/* (认证)                       │
│  - /api/posts/* (帖子)                      │
│  - /api/comments/* (评论)                   │
│  - /api/media/* (媒体上传/下载)             │
└─────────────────────────────────────────────┘
        ↓                      ↓
┌──────────────┐      ┌────────────────────┐
│ PostgreSQL   │      │  存储层             │
│ - 用户表     │      │  - 本地磁盘 或      │
│ - 帖子表     │      │  - Cloudflare R2   │
│ - 评论表     │      │  （待定）          │
│ - 媒体元数据 │      └────────────────────┘
└──────────────┘
        ↓
┌──────────────┐      ┌────────────────────┐
│ Redis        │      │  Celery Worker     │
│ - 会话       │      │  - 图片压缩        │
│ - 缓存       │      │  - 缩略图生成      │
│ - 任务队列   │←─────│  - 视频转码（可选）│
└──────────────┘      └────────────────────┘
```

### 数据模型

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'member', -- admin/member
    invite_code VARCHAR(32) UNIQUE,
    invited_by UUID REFERENCES users(id),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 帖子表
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT,
    media_urls JSONB, -- [{type: 'image', url: '...', thumbnail: '...'}, ...]
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 评论表
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE, -- 支持回复
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 点赞表（防止重复点赞）
CREATE TABLE likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type VARCHAR(20) NOT NULL, -- post/comment
    target_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, target_type, target_id)
);

-- 媒体文件表
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploader_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL, -- image/video
    original_name VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    file_size BIGINT,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    duration INTEGER, -- 视频时长（秒）
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_likes_target ON likes(target_type, target_id);
```

### 技术风险

| 风险 | 可能性 | 缓解方案 |
|------|------------|------------|
| 海外 VPS 视频加载慢（150ms 延迟） | 高 | 1. 视频压缩（H.264 编码，分辨率降低）<br>2. HLS 流式传输<br>3. Cloudflare CDN 加速 |
| 100GB 磁盘存储不足 | 中 | 1. 图片自动压缩（最大 1080p）<br>2. 视频限制时长/大小<br>3. Cloudflare R2 对象存储（免费 10GB）<br>4. 定期归档到本地物理机 |
| 并发上传冲突 | 低 | 1. 分块上传（大文件）<br>2. 文件去重（MD5 校验）<br>3. 上传队列限制 |
| 微信浏览器兼容性问题 | 低 | 1. 使用标准 HTML5 API<br>2. 避免依赖特殊浏览器特性<br>3. 测试微信内置浏览器 |
| Docker 部署失败（端口冲突/权限问题） | 中 | 1. 详细的部署文档<br>2. 健康检查脚本<br>3. 常见问题 FAQ |
| 备份脚本失败（网络中断/磁盘满） | 中 | 1. 健康检查 + 邮件告警<br>2. 增量备份<br>3. 备份验证机制 |

---

## 实施阶段

<!--
  STATUS: pending | in-progress | complete
  PARALLEL: 可以并行的阶段（如 "with 3" 或 "-"）
  DEPENDS: 必须先完成的阶段（如 "1, 2" 或 "-"）
  PRP: 生成计划文件后的链接
-->

| # | 阶段 | 描述 | 状态 | 并行 | 依赖 | PRP 计划 |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | 项目初始化与基础架构 | 搭建开发环境、数据库设计、Docker 配置 | pending | - | - | - |
| 2 | 用户认证系统 | 实现注册/登录、邀请码、JWT 认证 | pending | - | 1 | - |
| 3 | 帖子核心功能 | 发布/编辑/删除帖子、时间线 API | pending | with 4 | 2 | - |
| 4 | 媒体上传与处理 | 图片/视频上传、压缩、缩略图生成 | pending | with 3 | 2 | - |
| 5 | 评论与互动系统 | 评论/回复/点赞功能 | pending | - | 3 | - |
| 6 | 前端界面开发 | Vue 3 组件、响应式布局、移动端适配 | pending | - | 3, 4, 5 | - |
| 7 | 部署与文档 | Docker Compose 打包、部署文档、使用指南 | pending | - | 6 | - |
| 8 | 测试与优化 | 功能测试、性能优化、Bug 修复 | pending | - | 7 | - |

### 阶段详情

**阶段 1: 项目初始化与基础架构**
- **目标**：搭建完整的开发环境，确立技术基础
- **范围**：
  - 初始化 Git 仓库，设置 .gitignore
  - 创建后端项目结构（FastAPI + SQLAlchemy）
  - 创建前端项目结构（Vue 3 + Vite）
  - 设计数据库 Schema（PostgreSQL）
  - 编写 docker-compose.yml（开发环境）
  - 配置 Caddy 反向代理
- **成功信号**：
  - `docker-compose up` 能启动所有服务
  - 数据库迁移脚本可执行
  - 前后端能通过 API 互相通信

**阶段 2: 用户认证系统**
- **目标**：实现安全的用户认证和授权
- **范围**：
  - 用户注册（邀请码验证）
  - 登录/登出（JWT Token）
  - 密码加密（bcrypt）
  - 权限中间件（admin/member）
  - 邀请码生成与管理
- **成功信号**：
  - 新用户通过邀请码注册成功
  - 登录后获得有效 Token
  - 未授权请求被拦截

**阶段 3: 帖子核心功能**
- **目标**：实现帖子的 CRUD 和时间线展示
- **范围**：
  - 创建帖子 API（文字 + 媒体 URL）
  - 编辑/删除帖子 API（权限校验）
  - 时间线 API（分页加载）
  - 帖子详情 API
  - 帖子点赞功能
- **成功信号**：
  - 用户能发布包含文字和媒体的帖子
  - 时间线按时间倒序显示
  - 只有作者能编辑/删除自己的帖子

**阶段 4: 媒体上传与处理**
- **目标**：实现高效的媒体文件处理流程
- **范围**：
  - 文件上传 API（分块上传支持）
  - 图片压缩与缩略图生成（Celery 异步任务）
  - 视频压缩（可选，H.264 编码）
  - 文件存储（本地磁盘 或 Cloudflare R2）
  - 文件访问鉴权（私有文件）
- **成功信号**：
  - 图片上传后自动生成缩略图
  - 大文件（视频）上传不阻塞请求
  - 媒体文件只有家庭成员能访问

**阶段 5: 评论与互动系统**
- **目标**：完成社交互动功能
- **范围**：
  - 评论 API（创建/删除）
  - 回复 API（嵌套评论）
  - 点赞 API（防止重复点赞）
  - 评论数/点赞数统计
  - WebSocket 实时通知（可选）
- **成功信号**：
  - 用户能对帖子发表评论
  - 评论支持多层嵌套回复
  - 点赞/取消点赞实时更新

**阶段 6: 前端界面开发**
- **目标**：构建用户友好的响应式界面
- **范围**：
  - 登录/注册页面
  - 时间线页面（无限滚动）
  - 帖子详情页（包含评论列表）
  - 发布帖子页面（支持图片/视频上传）
  - 个人中心页面
  - 响应式适配（手机/平板/桌面）
  - 微信浏览器兼容性测试
- **成功信号**：
  - 手机浏览器体验流畅
  - 微信内置浏览器能正常访问
  - 所有核心功能可通过 UI 操作

**阶段 7: 部署与文档**
- **目标**：实现一键部署和完整文档
- **范围**：
  - 生产环境 docker-compose.yml
  - 环境变量配置文档
  - 部署指南（VPS/NAS 部署步骤）
  - 使用手册（管理员/用户操作指南）
  - 备份脚本（rsync/rclone）
  - 常见问题 FAQ
- **成功信号**：
  - 新用户能在 30 分钟内完成部署
  - 所有配置项有清晰说明
  - 备份脚本能自动运行

**阶段 8: 测试与优化**
- **目标**：确保产品质量和性能
- **范围**：
  - 单元测试（后端 API）
  - 集成测试（前后端联调）
  - 性能测试（并发上传/加载速度）
  - 安全测试（SQL 注入、XSS）
  - Bug 修复
  - 性能优化（数据库索引、缓存策略）
- **成功信号**：
  - 测试覆盖率 > 80%
  - 关键路径响应时间 < 500ms
  - 无严重安全漏洞

### 并行性说明

- **阶段 3 和 4 可以并行**：帖子功能和媒体处理相对独立，可以两个团队/开发者同时进行
- **阶段 6 依赖 3/4/5 完成**：前端需要后端 API 完成后才能集成
- **阶段 7/8 必须串行**：部署依赖功能完成，测试依赖部署完成

---

## 决策日志

| 决策 | 选择 | 备选方案 | 理由 |
|----------|--------|--------------|-----------|
| 后端框架 | FastAPI | Flask/Django/Sanic | 异步性能好 + 类型提示友好 AI 开发 + 自动文档 |
| 前端框架 | Vue 3 | React/Svelte | 轻量级 + 响应式支持好 + 中文生态友好 |
| 数据库 | PostgreSQL | MySQL/SQLite | 事务支持强 + JSON 字段支持 + 开源生态成熟 |
| 部署方式 | Docker Compose | Kubernetes/裸机部署 | 简单易用 + 适合小规模部署 + 一键启动 |
| 存储方案 | 待定（本地磁盘 or R2） | 阿里云 OSS/AWS S3 | Cloudflare R2 免费额度高 + 本地磁盘零成本，需性能测试决策 |
| 视频转码 | 可选功能 | 必选 | 增加复杂度，v1 可暂不做，优先保证基础功能稳定 |
| AI 功能 | v2 考虑 | v1 集成 | 非刚需，避免过度设计 |

---

## 调研总结

**市场背景**
- 现有开源相册管理系统（Immich、PhotoPrism）主要面向个人，缺少家庭社交互动功能
- 家庭协作平台（HomeHub、Cloudreve）偏向工具性，缺少时间线和评论体验
- 市场空白：结合"私有部署 + 社交互动"的家庭分享平台

**技术背景**
- FastAPI + Vue 3 技术栈成熟，社区活跃，AI 辅助开发效率高
- 6GB VPS 配置足够运行全栈服务（预估内存占用 ~1GB）
- Docker Compose 降低部署门槛，适合开源项目推广
- Cloudflare CDN 能缓解海外 VPS 延迟问题（150ms 可接受）

**主要技术挑战**
1. 海外 VPS 视频加载速度优化
2. 存储方案选择（本地 vs 对象存储）
3. 备份自动化实现
4. 移动端浏览器兼容性

---

*生成时间：2026-06-04*  
*状态：DRAFT - 需验证*
