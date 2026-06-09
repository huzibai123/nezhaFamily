/**
 * 媒体 URL 辅助函数
 * 处理媒体资源的完整访问路径
 */

/**
 * 将后端返回的媒体 URL 转换为可访问的完整路径
 * @param u - 后端返回的媒体 URL（如 "/media/xxx.jpg" 或完整 URL）
 * @returns 完整的媒体访问路径
 */
export function mediaUrl(u: string): string {
  // 已经是完整 URL（http/https 开头），直接返回
  if (u.startsWith('http://') || u.startsWith('https://')) {
    return u
  }

  // 检查是否配置了专用媒体服务地址
  const mediaBase = import.meta.env.VITE_MEDIA_BASE_URL
  if (mediaBase) {
    // 确保 mediaBase 不以 / 结尾，u 以 / 开头
    return mediaBase.replace(/\/$/, '') + (u.startsWith('/') ? u : '/' + u)
  }

  // 默认：相对路径（/media/...），开发走 Vite 代理、生产走同域 nginx
  return u
}
