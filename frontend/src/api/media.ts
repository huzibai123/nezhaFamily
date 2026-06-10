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
  caption?: string | null
  captured_at?: string | null
  deleted_at?: string | null
  is_favorite: boolean
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

export interface MediaMonthFacet {
  month: string
  count: number
}

export interface MediaLibraryResponse extends MediaSearchResponse {
  months: MediaMonthFacet[]
  trash_count: number
  favorite_count: number
}

export interface MediaLibraryParams extends MediaSearchParams {
  favorite_only?: boolean
  trash_only?: boolean
}

export interface MediaUpdatePayload {
  caption?: string | null
  captured_at?: string | null
}

export interface MediaFavoriteResponse {
  success: boolean
  is_favorite: boolean
}

export type MediaBulkAction = 'favorite' | 'unfavorite' | 'add_to_album' | 'trash' | 'restore'

export interface MediaBulkPayload {
  action: MediaBulkAction
  media_ids: string[]
  album_id?: string
}

export interface MediaBulkResponse {
  action: MediaBulkAction
  requested: number
  affected: number
  skipped: number
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

export function getMediaLibrary(params: MediaLibraryParams = {}): Promise<MediaLibraryResponse> {
  return api.get('/media/library', { params })
}

export function updateMedia(id: string, payload: MediaUpdatePayload): Promise<MediaSearchItem> {
  return api.patch(`/media/${id}`, payload)
}

export function toggleMediaFavorite(id: string): Promise<MediaFavoriteResponse> {
  return api.post(`/media/${id}/favorite`)
}

export function bulkMediaAction(payload: MediaBulkPayload): Promise<MediaBulkResponse> {
  return api.post('/media/bulk', payload)
}

export function trashMedia(id: string): Promise<MediaBulkResponse> {
  return api.delete(`/media/${id}`)
}

export function restoreMedia(id: string): Promise<MediaBulkResponse> {
  return api.post(`/media/${id}/restore`)
}
