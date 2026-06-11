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

export interface AdminRuntimeTaskTimeouts {
  task_time_limit_seconds: number
  task_soft_time_limit_seconds: number
  image_task_time_limit_seconds: number
  image_task_soft_time_limit_seconds: number
  ai_task_time_limit_seconds: number
  ai_task_soft_time_limit_seconds: number
  media_cleanup_task_time_limit_seconds: number
  media_cleanup_task_soft_time_limit_seconds: number
}

export interface AdminRuntimeStatus {
  database_available: boolean
  redis_available: boolean
  celery_ping_available: boolean
  celery_ping_error?: string | null
  celery_broker_url: string
  celery_result_backend: string
  celery_broker_configured: boolean
  celery_result_backend_configured: boolean
  task_timeouts: AdminRuntimeTaskTimeouts
  media_trash_retention_days: number
  latest_backup_verification_status?: string | null
  latest_backup_verified_at?: string | null
  latest_backup_message?: string | null
  ai_provider_status?: string | null
  ai_provider_last_error?: string | null
  ai_provider_paused_reason?: string | null
  ai_provider_checked_at?: string | null
  checked_at: string
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
  runtime?: AdminRuntimeStatus
  backups?: AdminBackupStatus
}

export interface AdminUserUpdate {
  role?: AdminRole
  role_in_family?: string | null
  bio?: string | null
}

export type AIProviderStatus =
  | 'disabled'
  | 'active'
  | 'paused_billing_or_auth'
  | 'paused_rate_limit'
  | 'paused_error'
  | string

export interface AIProvider {
  id: string
  name: string
  base_url: string
  text_model: string
  vision_model?: string | null
  timeout_seconds: number
  enabled: boolean
  status: AIProviderStatus
  has_api_key: boolean
  api_key_source?: string | null
  wire_api: 'chat_completions' | 'responses'
  model_reasoning_effort?: string | null
  disable_response_storage: boolean
  failure_count: number
  last_error?: string | null
  paused_reason?: string | null
  last_checked_at?: string | null
  notified_pause_at?: string | null
  created_at: string
  updated_at: string
}

export interface AIProviderUpdate {
  name: string
  base_url: string
  api_key?: string | null
  clear_api_key?: boolean
  text_model: string
  vision_model?: string | null
  timeout_seconds: number
  enabled: boolean
  wire_api: 'chat_completions' | 'responses'
  model_reasoning_effort?: string | null
  disable_response_storage: boolean
}

export interface AIProviderTestResponse {
  ok: boolean
  status: AIProviderStatus
  message: string
}

export interface AIStatus {
  enabled: boolean
  status: AIProviderStatus
  provider?: AIProvider | null
  personas_enabled: number
  auto_comment_personas: number
}

export interface AIPersona {
  id: string
  user_id?: string | null
  name: string
  avatar_url?: string | null
  persona_type: string
  tone?: string | null
  bio?: string | null
  enabled: boolean
  auto_comment_enabled: boolean
  auto_like_enabled: boolean
  comment_style: 'warm' | 'gentle' | 'playful' | 'brief'
  comment_length: 'short' | 'medium'
  interaction_frequency: 'low' | 'normal' | 'high'
  report_enabled: boolean
  album_suggestion_enabled: boolean
  sort_order: number
  created_at: string
  updated_at: string
}

export type AIPersonaPayload = Omit<AIPersona, 'id' | 'user_id' | 'created_at' | 'updated_at'>

export interface AIJob {
  id: string
  job_type: string
  status: string
  target_type?: string | null
  target_id?: string | null
  persona_id?: string | null
  progress_current: number
  progress_total: number
  retry_count: number
  max_retries: number
  error_message?: string | null
  result: Record<string, unknown>
  created_by?: string | null
  started_at?: string | null
  completed_at?: string | null
  created_at: string
  updated_at: string
}

export interface AIProfile {
  id: string
  subject_type: string
  subject_id?: string | null
  title: string
  summary?: string | null
  traits: string[]
  preferences: string[]
  memories: string[]
  editable_notes?: string | null
  updated_by?: string | null
  created_at: string
  updated_at: string
}

export interface AIReportDraft {
  id: string
  persona_id?: string | null
  period_type: string
  period_start: string
  period_end: string
  title: string
  content: string
  status: string
  source_metadata: Record<string, unknown>
  created_by?: string | null
  published_post_id?: string | null
  created_at: string
  updated_at: string
}

export interface AIAlbumSuggestion {
  id: string
  target_type: string
  target_id: string
  album_id?: string | null
  suggested_album_name?: string | null
  reason?: string | null
  status: string
  created_by_persona_id?: string | null
  reviewed_by?: string | null
  reviewed_at?: string | null
  created_at: string
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

export function getAIStatus(): Promise<AIStatus> {
  return api.get('/admin/ai/status')
}

export function updateAIProvider(data: AIProviderUpdate): Promise<AIProvider> {
  return api.put('/admin/ai/providers/default', data)
}

export function testAIProvider(): Promise<AIProviderTestResponse> {
  return api.post('/admin/ai/providers/default/test')
}

export function getAIPersonas(): Promise<AIPersona[]> {
  return api.get('/admin/ai/personas')
}

export function createAIPersona(data: AIPersonaPayload): Promise<AIPersona> {
  return api.post('/admin/ai/personas', data)
}

export function updateAIPersona(
  personaId: string,
  data: Partial<AIPersonaPayload>
): Promise<AIPersona> {
  return api.patch(`/admin/ai/personas/${personaId}`, data)
}

export function deleteAIPersona(personaId: string): Promise<void> {
  return api.delete(`/admin/ai/personas/${personaId}`)
}

export function getAIJobs(): Promise<AIJob[]> {
  return api.get('/admin/ai/jobs')
}

export function createAIJob(jobType: 'history_learning' | 'album_suggestions'): Promise<AIJob> {
  return api.post('/admin/ai/jobs', { job_type: jobType })
}

export function getAIProfiles(): Promise<AIProfile[]> {
  return api.get('/admin/ai/profiles')
}

export function getAIReports(): Promise<AIReportDraft[]> {
  return api.get('/admin/ai/reports')
}

export function createAIReport(data: {
  period_type: 'week' | 'month' | 'custom'
  period_start: string
  period_end: string
  persona_id?: string | null
}): Promise<AIReportDraft> {
  return api.post('/admin/ai/reports', data)
}

export function publishAIReport(reportId: string): Promise<AIReportDraft> {
  return api.post(`/admin/ai/reports/${reportId}/publish`)
}

export function getAIAlbumSuggestions(): Promise<AIAlbumSuggestion[]> {
  return api.get('/admin/ai/album-suggestions')
}

export function reviewAIAlbumSuggestion(
  suggestionId: string,
  data: { action: 'approve' | 'reject'; album_id?: string | null; album_name?: string | null }
): Promise<AIAlbumSuggestion> {
  return api.post(`/admin/ai/album-suggestions/${suggestionId}/review`, data)
}
