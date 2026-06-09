import { createApp } from 'vue'
import router from '@/router'
import App from '@/App.vue'
import { useAuth } from '@/composables/useAuth'
import { useFamilySettings } from '@/composables/useFamilySettings'
import { setUnauthorizedHandler } from '@/api'

// 导入全局样式
import '@/assets/styles/globals.css'

// 创建应用实例
const app = createApp(App)

// 注册路由
app.use(router)

setUnauthorizedHandler(() => {
  if (router.currentRoute.value.name !== 'Login') {
    router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
  }
})

// 初始化用户状态
const { initUser, refreshCurrentUser, isAdmin } = useAuth()
initUser()
refreshCurrentUser().then(() => {
  if (router.currentRoute.value.meta.requiresAdmin && !isAdmin.value) {
    router.replace({ name: 'Timeline' })
  }
})

const { loadFamilySettings } = useFamilySettings()
loadFamilySettings()

// 挂载应用
app.mount('#app')
