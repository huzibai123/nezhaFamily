import { ref, computed } from 'vue'
import {
  getMe,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  type AuthUser,
} from '@/api/auth'
import { setUnauthorizedStateHandler } from '@/api'
import { useTheme } from '@/composables/useTheme'

// 用户信息接口
export type User = AuthUser

// 全局状态
const token = ref<string | null>(localStorage.getItem('token'))
const user = ref<User | null>(null)
const { syncThemeForUser } = useTheme()

// 计算属性
const isAuthenticated = computed(() => !!token.value)
const isAdmin = computed(() => user.value?.role === 'admin')

// 初始化用户信息
function initUser() {
  const savedUser = localStorage.getItem('user')
  if (savedUser && token.value) {
    try {
      user.value = JSON.parse(savedUser)
      syncThemeForUser(user.value)
    } catch (e) {
      console.error('Failed to parse user data:', e)
    }
  } else {
    syncThemeForUser(null)
  }
}

// 登录
async function login(username: string, password: string) {
  try {
    const data = await loginRequest(username, password)
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    syncThemeForUser(data.user)
    return { success: true, message: '登录成功' }
  } catch (error) {
    const message = typeof error === 'string' ? error : '网络错误'
    return { success: false, message }
  }
}

// 注册
async function register(username: string, email: string, password: string, inviteCode: string) {
  try {
    const data = await registerRequest(username, email, password, inviteCode)
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    syncThemeForUser(data.user)
    return { success: true, message: '注册成功' }
  } catch (error) {
    const message = typeof error === 'string' ? error : '网络错误'
    return { success: false, message }
  }
}

async function refreshCurrentUser() {
  if (!token.value) {
    syncThemeForUser(null)
    return null
  }
  try {
    const currentUser = await getMe()
    user.value = currentUser
    localStorage.setItem('user', JSON.stringify(currentUser))
    syncThemeForUser(currentUser)
    return currentUser
  } catch {
    clearAuthState()
    return null
  }
}

function clearAuthState() {
  token.value = null
  user.value = null
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  syncThemeForUser(null)
}

setUnauthorizedStateHandler(clearAuthState)

// 登出
async function logout() {
  try {
    await logoutRequest()
  } catch {
    // 即使服务端撤销暂时失败，也要让当前设备退出登录。
  } finally {
    clearAuthState()
  }
}

// 更新用户信息
function setUser(userData: User) {
  user.value = userData
  localStorage.setItem('user', JSON.stringify(userData))
  syncThemeForUser(userData)
}

// 导出状态和方法
export function useAuth() {
  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    clearAuthState,
    initUser,
    refreshCurrentUser,
    setUser,
  }
}
