import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

// 路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Timeline',
    component: () => import('@/views/TimelinePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/post/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetailPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/publish',
    name: 'Publish',
    component: () => import('@/views/PublishPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: () => import('@/views/CalendarPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/views/NotificationsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/albums',
    name: 'Albums',
    component: () => import('@/views/AlbumsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/library',
    name: 'MediaLibrary',
    component: () => import('@/views/MediaLibraryPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/albums/:id',
    name: 'AlbumDetail',
    component: () => import('@/views/AlbumDetailPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile/:id',
    name: 'Profile',
    component: () => import('@/views/ProfilePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/AdminPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/ai',
    name: 'AdminAI',
    component: () => import('@/views/AdminAIPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminAIOverview',
        component: () => import('@/views/admin-ai/AdminAIOverview.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'overview',
        name: 'AdminAIOverviewAlias',
        redirect: { name: 'AdminAIOverview' },
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'provider',
        name: 'AdminAIProvider',
        component: () => import('@/views/admin-ai/AdminAIProvider.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'personas',
        name: 'AdminAIPersonas',
        component: () => import('@/views/admin-ai/AdminAIPersonas.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'jobs',
        name: 'AdminAIJobs',
        component: () => import('@/views/admin-ai/AdminAIJobs.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'reports',
        name: 'AdminAIReports',
        component: () => import('@/views/admin-ai/AdminAIReports.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'suggestions',
        name: 'AdminAISuggestions',
        component: () => import('@/views/admin-ai/AdminAISuggestions.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
      {
        path: 'profiles',
        name: 'AdminAIProfiles',
        component: () => import('@/views/admin-ai/AdminAIProfiles.vue'),
        meta: { requiresAuth: true, requiresAdmin: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 导航守卫 - 验证登录状态
router.beforeEach((to, _from, next) => {
  const { isAuthenticated, isAdmin } = useAuth()
  const requiresAuth = to.meta.requiresAuth
  const requiresAdmin = to.meta.requiresAdmin

  if (requiresAuth && !isAuthenticated.value) {
    // 需要登录但未登录，重定向到登录页
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (requiresAdmin && !isAdmin.value) {
    next({ name: 'Timeline' })
  } else if (!requiresAuth && isAuthenticated.value && (to.name === 'Login' || to.name === 'Register')) {
    // 已登录用户访问登录/注册页，重定向到首页
    next({ name: 'Timeline' })
  } else {
    next()
  }
})

export default router
