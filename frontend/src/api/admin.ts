import api from './index'
import type { MediaUploadResponse } from './media'

export type AdminRole = 'admin' | 'member'
export type ThemeAssetKind = 'background' | 'logo' | 'cursor' | 'ornament'
export type ThemeOrnamentPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'

export interface ThemeBackgroundAsset {
  id: string
  url: string
  label?: string | null
  enabled: boolean
}

export interface ThemeCursorAsset {
  url?: string | null
  enabled: boolean
  size: number
}

export interface ThemeOrnamentAsset {
  id: string
  url: string
  position: ThemeOrnamentPosition
  enabled: boolean
  size: number
  opacity: number
}

export interface FamilyThemeAssets {
  backgrounds: ThemeBackgroundAsset[]
  cursor?: ThemeCursorAsset | null
  ornaments: ThemeOrnamentAsset[]
}

export interface FamilySettings {
  family_name: string
  tagline?: string | null
  theme_color?: string | null
  accent_color?: string | null
  background_image_url?: string | null
  logo_url?: string | null
  theme_assets?: FamilyThemeAssets | null
  updated_by?: string | null
  created_at?: string
  updated_at?: string
}

export interface AdminUser {
  id: string
  username: string
  email: string
  role: AdminRole
  avatar_url?: string | null
  bio?: string | null
  birthday?: string | null
  role_in_family?: string | null
  invite_code?: string | null
  invited_by?: string | null
  created_at: string
  updated_at?: string
  post_count?: number
  comment_count?: number
  media_count?: number
}

export interface AdminOverviewTotals {
  users: number
  posts: number
  comments: number
  media: number
  albums: number
  events: number
}

export interface AdminStorageStatus {
  media_root: string
  backup_root: string
  media_file_count: number
  media_directory_bytes: number
  database_media_bytes: number
  disk_total_bytes: number
  disk_used_bytes: number
  disk_free_bytes: number
  disk_free_percent: number
  last_scanned_at: string
}

export interface AdminBackupItem {
  backup_id: string
  status: string
  created_at: string
  snapshot_file: string
  media_archive_file?: string | null
  size_bytes: number
  database_record_count: number
  media_file_count: number
  message?: string | null
}

export interface AdminBackupStatus {
  backup_root: string
  latest?: AdminBackupItem | null
  recent: AdminBackupItem[]
}

export interface AdminRecentComment {
  id: string
  post_id: string
  author_id: string
  author_username: string
  content: string
  created_at: string
}

export interface AdminRecentMedia {
  id: string
  uploader_id: string
  uploader_username: string
  original_name?: string | null
  file_type: 'image' | 'video' | string
  file_size?: number | null
  mime_type?: string | null
  created_at: string
  warning?: string | null
}

export interface AdminBackupCheck {
  label: string
  ok: boolean
  detail: string
}

export interface AdminBackupVerification {
  backup_id: string
  status: string
  verified_at: string
  checks: AdminBackupCheck[]
  message: string
  restore_hint: string
}

export type AdminBackupFileKind = 'manifest' | 'database' | 'media'

export interface AdminOverview {
  user_count?: number
  post_count?: number
  comment_count?: number
  media_count?: number
  album_count?: number
  event_count?: number
  totals?: Partial<AdminOverviewTotals>
  recent_members?: AdminUser[]
  recent_posting_members?: AdminUser[]
  recent_comments?: AdminRecentComment[]
  recent_media?: AdminRecentMedia[]
  upload_warnings?: AdminRecentMedia[]
  storage?: AdminStorageStatus
  backups?: AdminBackupStatus
}

export interface AdminUserUpdate {
  role?: AdminRole
  role_in_family?: string | null
  bio?: string | null
}

export function getAdminOverview(): Promise<AdminOverview> {
  return api.get('/admin/overview')
}

export function createAdminBackup(): Promise<AdminBackupItem> {
  return api.post('/admin/backups')
}

export function verifyAdminBackup(backupId: string): Promise<AdminBackupVerification> {
  return api.post(`/admin/backups/${backupId}/verify`)
}

export function downloadAdminBackupFile(
  backupId: string,
  fileKind: AdminBackupFileKind
): Promise<Blob> {
  return api.get(`/admin/backups/${backupId}/download/${fileKind}`, {
    responseType: 'blob',
  })
}

export function getAdminUsers(): Promise<{ users: AdminUser[]; total?: number } | AdminUser[]> {
  return api.get('/admin/users')
}

export function updateAdminUser(userId: string, data: AdminUserUpdate): Promise<AdminUser> {
  return api.patch(`/admin/users/${userId}`, data)
}

export function regenerateUserInviteCode(userId: string): Promise<{ invite_code?: string; code?: string }> {
  return api.post(`/admin/users/${userId}/invite-code`)
}

export function getFamilySettings(): Promise<FamilySettings> {
  return api.get('/admin/family-settings')
}

export function updateFamilySettings(data: Partial<FamilySettings>): Promise<FamilySettings> {
  return api.put('/admin/family-settings', data)
}

export function uploadThemeAsset(
  kind: ThemeAssetKind,
  files: File[]
): Promise<MediaUploadResponse> {
  const formData = new FormData()
  files.forEach(file => formData.append('files', file))
  return api.post('/admin/theme-assets/upload', formData, {
    params: { kind },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
