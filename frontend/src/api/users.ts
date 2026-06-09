import api from './index'
import type { Post } from './posts'

export interface UserProfile {
  id: string
  username: string
  email: string
  avatar_url?: string
  bio?: string
  birthday?: string
  role_in_family?: string
  created_at: string
}

export interface UserStats {
  post_count: number
  comment_count: number
  like_count: number
}

export function getUserProfile(userId: string): Promise<UserProfile> {
  return api.get(`/users/${userId}`)
}

export function updateUserProfile(
  userId: string,
  data: Partial<UserProfile>
): Promise<UserProfile> {
  return api.put(`/users/${userId}`, data)
}

export function getUserPosts(userId: string, page = 1): Promise<{
  posts: Post[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}> {
  return api.get(`/users/${userId}/posts`, { params: { page } })
}

export function getUserStats(userId: string): Promise<UserStats> {
  return api.get(`/users/${userId}/stats`)
}
