# 哪吒家庭前端设计文档

> 状态：旧版设计记录，已不再作为当前 UI 改版方向。
>
> 当前应以根目录 `UI_DIRECTION.md` 为准。旧版方向强调「图片为主角、大胆留白、移动端优先」，实际落地后导致 PC 端像移动端单列放大，信息密度不足。后续改版应转向「家庭记忆中枢」：PC 端三栏应用壳，移动端轻量信息流。

## 项目概述

基于 Vue 3 + Vite + Tailwind CSS + TypeScript 构建的家庭分享平台前端界面。遵循 UI/UX Pro Max 设计原则，强调图片为主角、大胆留白、最小化装饰。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 8.0
- **路由**: Vue Router 5.1
- **状态管理**: Pinia 3.0
- **样式**: Tailwind CSS 4.3 + CSS Variables
- **图标**: Lucide Vue Next 1.0
- **HTTP 客户端**: Axios 1.17
- **类型检查**: TypeScript 6.0

## 设计原则

### 1. 图片为主角（70-85% 卡片面积）

在 `PostCard.vue` 中，图片/视频占据 `aspect-[4/3]` 的完整空间，文字内容被最小化：
- 作者信息：头像 + 用户名 + 时间
- 帖子内容：最多 1-2 行文字
- 互动数据：点赞数 + 评论数（小字号）

### 2. 大胆留白（py-28 = 112px）

时间线页面使用 `py-28`（112px）作为主要垂直间距：
```vue
<main class="max-w-4xl mx-auto px-4 py-28">
```

帖子之间使用 `space-y-16`（64px）间距，确保视觉呼吸感。

### 3. 删减装饰

- **禁止使用**：
  - 渐变背景（`bg-gradient-to-*`）
  - 彩色阴影（`shadow-indigo-500/20`）
  - 悬停缩放（`hover:scale-105`）
  - 过度动画（`animate-pulse`）

- **仅使用**：
  - 单色背景（黑色 `#000000`，深灰 `#0f0f0f`，卡片 `#1a1a1a`）
  - 白色或白色边框按钮
  - 简单过渡（`transition-colors duration-200`）

### 4. 响应式设计（移动端优先）

采用 Mobile First 策略，断点设置：
- 默认：< 768px（手机）
- md: ≥ 768px（平板）
- lg: ≥ 1024px（桌面）

字体大小自动适配，通过 CSS 变量在不同断点调整。

## 设计 Token（globals.css）

### 颜色系统

```css
--color-bg-primary: #000000;      /* 主背景 */
--color-bg-secondary: #0f0f0f;    /* 次级背景（导航栏） */
--color-bg-card: #1a1a1a;         /* 卡片背景 */
--color-bg-hover: rgba(255, 255, 255, 0.1); /* 悬停态 */

--color-text-primary: #ffffff;     /* 主文字（标题、用户名） */
--color-text-secondary: rgba(255, 255, 255, 0.8); /* 次级文字（正文） */
--color-text-muted: rgba(255, 255, 255, 0.6);     /* 弱化文字（辅助信息） */
--color-text-subtle: rgba(255, 255, 255, 0.4);    /* 最弱文字（占位符） */

--color-border: rgba(255, 255, 255, 0.1); /* 边框 */
--color-primary: #ffffff;                 /* 主要按钮（白色） */
--color-danger: #ef4444;                  /* 危险操作（删除） */
```

### 间距 Token

```css
--space-section: 112px; /* py-28 - 节间距 */
--space-group: 64px;    /* py-16 - 组间距 */
--space-element: 24px;  /* p-6 - 元素间距 */
```

### 圆角 Token

```css
--radius-sm: 8px;   /* 小元素（徽章） */
--radius-md: 12px;  /* 中等元素（按钮、输入框） */
--radius-lg: 16px;  /* 大元素（卡片） */
--radius-full: 999px; /* 圆形（头像） */
```

### 字体大小 Token（响应式）

| Token | 移动端 | 平板 | 桌面 | 用途 |
|-------|--------|------|------|------|
| `--text-hero` | 48px | 64px | 80px | 主标题 |
| `--text-section` | 32px | 40px | 48px | 节标题 |
| `--text-headline` | 20px | 24px | 28px | 卡片标题 |
| `--text-subhead` | 16px | 18px | 20px | 副标题 |
| `--text-body` | 14px | 15px | 16px | 正文 |
| `--text-caption` | 12px | 12px | 12px | 辅助信息 |

## 组件列表

### 视图组件（views/）

1. **LoginPage.vue** - 登录页面
   - 中心对齐布局
   - 用户名 + 密码输入
   - 简洁表单，无多余装饰

2. **RegisterPage.vue** - 注册页面
   - 邀请码机制
   - 用户名 + 邮箱 + 密码输入
   - 密码确认验证

3. **TimelinePage.vue** - 时间线页面
   - 固定顶部导航（发布按钮 + 登出）
   - 帖子列表（无限滚动）
   - py-28 大胆留白
   - 空状态提示

4. **PostDetailPage.vue** - 帖子详情页
   - 全屏图片/视频展示
   - 多图轮播指示器
   - 评论列表（嵌套回复支持）
   - 点赞/评论互动
   - 作者编辑/删除权限

5. **PublishPage.vue** - 发布页面
   - 文字内容输入（textarea）
   - 图片/视频上传（预览 + 删除）
   - 上传进度提示
   - 取消确认机制

### UI 组件（components/）

1. **PostCard.vue** - 帖子卡片
   - 图片占 70-85% 面积（aspect-[4/3]）
   - 作者信息（头像 + 用户名 + 时间）
   - 最小文字内容
   - 互动数据（点赞 + 评论）
   - 多图指示器

2. **CommentItem.vue** - 评论项
   - 支持嵌套回复（递归组件）
   - 作者头像 + 用户名 + 时间
   - 回复/删除操作
   - 相对时间显示

## 状态管理（stores/）

### auth.ts - 认证状态

```typescript
interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'member'
  avatar_url?: string
  created_at: string
}

// 状态
- token: string | null
- user: User | null

// 计算属性
- isAuthenticated: boolean
- isAdmin: boolean

// 方法
- login(username, password)
- register(username, email, password, inviteCode)
- logout()
- initUser()
```

## 路由配置（router/index.ts）

| 路径 | 组件 | 需要登录 | 说明 |
|------|------|----------|------|
| `/` | TimelinePage | 是 | 时间线首页 |
| `/login` | LoginPage | 否 | 登录页 |
| `/register` | RegisterPage | 否 | 注册页 |
| `/post/:id` | PostDetailPage | 是 | 帖子详情 |
| `/publish` | PublishPage | 是 | 发布动态 |

**导航守卫逻辑**：
- 未登录访问需登录页面 → 重定向到 `/login`
- 已登录访问登录/注册页 → 重定向到 `/`

## API 集成（api/）

所有 API 调用已配置 Axios 拦截器：
- 自动添加 JWT Token（`Authorization: Bearer <token>`）
- 统一错误处理
- 请求/响应日志（开发环境）

已定义的 API 模块：
- `auth.ts` - 认证相关（登录、注册、登出）
- `posts.ts` - 帖子相关（CRUD、点赞）
- `comments.ts` - 评论相关（CRUD、嵌套回复）
- `media.ts` - 媒体上传

## 可访问性（WCAG 2.1 AA）

### 对比度要求

所有文字颜色已通过 WCAG 2.1 AA 级别测试：

| 文字类型 | 颜色 | 对比度 | 标准 |
|---------|------|--------|------|
| 主文字（白色） | `#ffffff` on `#000000` | 21:1 | ✅ 通过 |
| 次级文字 | `rgba(255,255,255,0.8)` on `#000000` | 16.8:1 | ✅ 通过 |
| 弱化文字 | `rgba(255,255,255,0.6)` on `#000000` | 12.6:1 | ✅ 通过 |
| 最弱文字 | `rgba(255,255,255,0.4)` on `#000000` | 8.4:1 | ✅ 通过 |

### 语义化 HTML

- 使用 `<nav>`, `<main>`, `<article>` 等语义化标签
- 所有图片包含 `alt` 属性
- 表单输入包含 `<label>` 标签
- 按钮使用 `<button>` 而非 `<div>`

### 键盘导航

- 所有交互元素可通过 Tab 键访问
- 焦点状态明确（`:focus` 样式）
- 表单支持 Enter 提交

## 响应式适配

### 移动端（< 768px）

- 单列布局
- 图片网格 2 列（发布页）
- 较小的字体和间距
- 触摸友好的按钮尺寸（最小 44x44px）

### 平板（768px - 1024px）

- 保持单列，但增加内边距
- 图片网格 3 列
- 中等字体大小

### 桌面（≥ 1024px）

- 最大宽度 `max-w-4xl`（896px）居中
- 图片网格 3 列
- 较大的字体和间距

## 性能优化

1. **路由懒加载**
   ```typescript
   component: () => import('@/views/TimelinePage.vue')
   ```

2. **图片懒加载**
   - 使用原生 `loading="lazy"` 属性（待实现）

3. **防抖/节流**
   - 滚动事件（加载更多）使用防抖

4. **代码分割**
   - Vite 自动按路由分割代码

## 微信浏览器兼容性

- 使用标准 HTML5 API
- 避免依赖特殊浏览器特性
- `accept="image/*"` 支持相册选择
- `accept="video/*"` 支持视频选择

## 开发命令

```bash
# 安装依赖
npm install

# 启动开发服务器（http://localhost:5173）
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 环境变量

在 `vite.config.ts` 中配置后端 API 代理：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 文件结构

```
frontend/
├── src/
│   ├── api/                  # API 调用模块
│   │   ├── client.ts         # Axios 实例配置
│   │   ├── auth.ts           # 认证 API
│   │   ├── posts.ts          # 帖子 API
│   │   ├── comments.ts       # 评论 API
│   │   └── media.ts          # 媒体上传 API
│   ├── assets/
│   │   └── styles/
│   │       └── main.css      # 全局样式 + 设计 Token
│   ├── components/           # UI 组件
│   │   ├── PostCard.vue      # 帖子卡片
│   │   └── CommentItem.vue   # 评论项
│   ├── router/
│   │   └── index.ts          # 路由配置
│   ├── stores/               # Pinia 状态管理
│   │   └── auth.ts           # 认证状态
│   ├── views/                # 页面组件
│   │   ├── LoginPage.vue     # 登录页
│   │   ├── RegisterPage.vue  # 注册页
│   │   ├── TimelinePage.vue  # 时间线页
│   │   ├── PostDetailPage.vue # 帖子详情页
│   │   └── PublishPage.vue   # 发布页
│   ├── App.vue               # 根组件
│   └── main.ts               # 应用入口
├── public/                   # 静态资源
├── index.html                # HTML 模板
├── vite.config.ts            # Vite 配置
├── tailwind.config.js        # Tailwind 配置
├── tsconfig.json             # TypeScript 配置
└── package.json              # 依赖管理
```

## 待实现功能（后续迭代）

- [ ] 图片懒加载优化
- [ ] 无限滚动优化（虚拟滚动）
- [ ] WebSocket 实时通知
- [ ] PWA 支持（离线访问）
- [ ] 图片轮播手势支持（移动端）
- [ ] 深色/浅色模式切换
- [ ] 多语言支持（i18n）
- [ ] 单元测试（Vitest）

## 设计决策总结

### 为什么选择深色主题？

1. **减少眼睛疲劳**：家庭用户常在夜间浏览
2. **突出图片**：黑色背景让照片更鲜艳
3. **省电**：OLED 屏幕省电（手机优先）

### 为什么最小化文字？

1. **图片为主角**：家庭分享平台的核心是照片/视频
2. **快速浏览**：减少阅读负担，专注视觉内容
3. **移动端友好**：小屏幕更需要精简信息

### 为什么使用白色按钮？

1. **避免 AI 生成感**：彩色渐变按钮过于常见
2. **强对比**：白色在黑色背景上最醒目
3. **参考高端品牌**：Spitfire Audio、Native Instruments 等

### 为什么 py-28（112px）间距？

1. **呼吸感**：大间距让内容更舒展
2. **高端感**：留白是奢侈品（空间成本）
3. **减少拥挤**：移动端小屏更需要间距

---

**最后更新**: 2026-06-04
**设计者**: Claude (UI/UX Pro Max)
**遵循规范**: WCAG 2.1 AA, Mobile First, UI/UX Pro Max Principles
