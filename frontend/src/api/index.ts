import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
let unauthorizedHandler: (() => void) | null = null
let unauthorizedStateHandler: (() => void) | null = null
let isHandlingUnauthorized = false

export function setUnauthorizedHandler(handler: () => void) {
  unauthorizedHandler = handler
}

export function setUnauthorizedStateHandler(handler: () => void) {
  unauthorizedStateHandler = handler
}

function handleUnauthorized() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  unauthorizedStateHandler?.()

  if (isHandlingUnauthorized) return
  isHandlingUnauthorized = true
  try {
    unauthorizedHandler?.()
  } finally {
    globalThis.setTimeout(() => {
      isHandlingUnauthorized = false
    }, 0)
  }
}

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 自动添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      // 401 未授权，清空本地状态并跳转登录
      if (error.response.status === 401) {
        handleUnauthorized()
      }
      // 返回错误信息
      return Promise.reject(error.response.data?.detail || '请求失败')
    } else if (error.request) {
      return Promise.reject('网络错误，请检查连接')
    } else {
      return Promise.reject(error.message || '未知错误')
    }
  }
)

export default api
