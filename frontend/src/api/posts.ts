import api from './index'

export interface Post {
  id: string
  author_id: string
  author_username: string
  author_avatar_url?: string
  content: string
  media_urls: MediaItem[]
  like_count: number
  comment_count: number
  is_liked: boolean
  created_at: string
  updated_at: string
}

export interface MediaItem {
  type: 'image' | 'video'
  url: string
  thumbnail_url?: string
  width?: number
  height?: number
}

export interface PostListResponse {
  posts: Post[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface Comment {
  id: string
  post_id: string
  author_id: string
  author_username: string
  author_avatar_url?: string
  content: string
  parent_id?: string
  like_count: number
  is_liked: boolean
  is_ai_generated?: boolean
  ai_persona_id?: string | null
  edited_by?: string | null
  edited_at?: string | null
  created_at: string
  updated_at: string
  replies?: Comment[]
}

export interface CommentListResponse {
  comments: Comment[]
  total: number
}

export interface LikeResponse {
  success: boolean
  liked: boolean
  like_count: number
}

// 获取帖子列表
export function getPosts(page = 1, pageSize = 20): Promise<PostListResponse> {
  return api.get('/posts', { params: { page, page_size: pageSize } })
}

// 获取帖子详情
export function getPost(postId: string): Promise<Post> {
  return api.get(`/posts/${postId}`)
}

// 创建帖子
export function createPost(content: string, media: MediaItem[] = []): Promise<Post> {
  return api.post('/posts', { content, media })
}

// 删除帖子
export function deletePost(postId: string): Promise<void> {
  return api.delete(`/posts/${postId}`)
}

// 点赞/取消点赞帖子
export function togglePostLike(postId: string): Promise<LikeResponse> {
  return api.post(`/posts/${postId}/like`)
}

// 获取评论列表
export function getComments(postId: string): Promise<CommentListResponse> {
  return api.get(`/posts/${postId}/comments`)
}

// 创建评论
export function createComment(postId: string, content: string, parentId?: string): Promise<Comment> {
  return api.post(`/posts/${postId}/comments`, { content, parent_id: parentId })
}

// 更新评论
export function updateComment(commentId: string, content: string): Promise<Comment> {
  return api.patch(`/comments/${commentId}`, { content })
}

// 删除评论
export function deleteComment(commentId: string): Promise<void> {
  return api.delete(`/comments/${commentId}`)
}

// 点赞/取消点赞评论
export function toggleCommentLike(commentId: string): Promise<LikeResponse> {
  return api.post(`/comments/${commentId}/like`)
}
