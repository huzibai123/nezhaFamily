import api from './index'

export interface Album {
  id: string
  name: string
  description?: string
  cover_image_url?: string
  created_by: string
  created_at: string
  media_count: number
}

export interface AlbumMediaItem {
  id: string
  url: string
  type: string
}

export interface AlbumDetail {
  id: string
  name: string
  description?: string
  cover_image_url?: string
  created_by: string
  created_at: string
  media: AlbumMediaItem[]
}

export function getAlbums(): Promise<{ albums: Album[] }> {
  return api.get('/albums')
}

export function getAlbumDetail(id: string): Promise<AlbumDetail> {
  return api.get(`/albums/${id}`)
}

export function createAlbum(data: {
  name: string
  description?: string
  cover_image_url?: string
}): Promise<Album> {
  return api.post('/albums', data)
}

export function addMediaToAlbum(albumId: string, mediaId: string): Promise<void> {
  return api.post(`/albums/${albumId}/media/${mediaId}`)
}

export function removeMediaFromAlbum(albumId: string, mediaId: string): Promise<void> {
  return api.delete(`/albums/${albumId}/media/${mediaId}`)
}
