import api from './index'

export interface MediaUploadResponse {
  files: Array<{
    id: string
    url: string
    raw_url?: string
    type: string
  }>
}

export interface UserMediaItem {
  id: string
  url: string
  type: string
  created_at: string
}

export interface UserMediaResponse {
  media: UserMediaItem[]
  skip: number
  limit: number
}

export interface MediaSearchUploader {
  id: string
  username: string
  avatar_url?: string | null
  role_in_family?: string | null
}

export interface MediaSearchItem {
  id: string
  url: string
  thumbnail_url?: string | null
  type: 'image' | 'video'
  original_name?: string | null
  file_size?: number | null
  mime_type?: string | null
  width?: number | null
  height?: number | null
  duration?: number | null
  created_at: string
  uploader: MediaSearchUploader
}

export interface MediaSearchResponse {
  media: MediaSearchItem[]
  uploaders: MediaSearchUploader[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface MediaSearchParams {
  q?: string
  uploader_id?: string
  type?: 'image' | 'video'
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export function uploadMedia(files: File[]): Promise<MediaUploadResponse> {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  return api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getUserMedia(params: { skip?: number; limit?: number } = {}): Promise<UserMediaResponse> {
  return api.get('/media', { params })
}

export function searchMedia(params: MediaSearchParams = {}): Promise<MediaSearchResponse> {
  return api.get('/media/search', { params })
}
