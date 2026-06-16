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

// 将 FastAPI 的 detail 归一化为可读中文字符串（保持 catch(e) 拿到字符串的契约）
function formatErrorDetail(detail: unknown): string | null {
  // 字符串：直接使用
  if (typeof detail === 'string') {
    return detail
  }

  // 数组：FastAPI 422 校验错误格式 [{loc, msg, type}, ...]
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== 'object') return ''
        const msg = typeof item.msg === 'string' ? item.msg : ''
        if (!msg) return ''
        // 取末级 loc 字段名，拼成「字段: 提示」便于定位
        const loc = Array.isArray(item.loc) ? item.loc : []
        const field = loc.length > 0 ? String(loc[loc.length - 1]) : ''
        return field ? `${field}: ${msg}` : msg
      })
      .filter((text) => text.length > 0)

    if (messages.length > 0) {
      return messages.join('；')
    }
  }

  return null
}

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      // 401 未授权，清空本地状态并跳转登录
      if (status === 401) {
        handleUnauthorized()
      }

      const detailMessage = formatErrorDetail(error.response.data?.detail)

      // 按状态码给出更明确的兜底文案，始终 reject 字符串
      if (status === 429) {
        return Promise.reject(detailMessage || '操作过于频繁，请稍后再试')
      }
      if (status === 403) {
        return Promise.reject(detailMessage || '没有权限')
      }
      return Promise.reject(detailMessage || '请求失败')
    } else if (error.request) {
      return Promise.reject('网络错误，请检查连接')
    } else {
      return Promise.reject(error.message || '未知错误')
    }
  }
)

export default api
