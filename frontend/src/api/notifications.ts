import api from './index'

export type NotificationType =
  | 'new_post'
  | 'comment'
  | 'reply'
  | 'like_post'
  | 'like_comment'

export interface NotificationItem {
  id: string
  recipient_id: string
  actor_id?: string | null
  actor_username?: string | null
  type: NotificationType
  target_type: string
  target_id: string
  post_id?: string | null
  message: string
  is_read: boolean
  created_at: string
}

export interface NotificationListResponse {
  notifications: NotificationItem[]
  unread_count: number
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface NotificationQuery {
  unreadOnly?: boolean
  page?: number
  pageSize?: number
  type?: NotificationType | ''
}

export function getNotifications(
  unreadOnlyOrQuery: boolean | NotificationQuery = false,
  page = 1
): Promise<NotificationListResponse> {
  const query =
    typeof unreadOnlyOrQuery === 'boolean'
      ? { unreadOnly: unreadOnlyOrQuery, page }
      : unreadOnlyOrQuery

  return api.get('/notifications', {
    params: {
      unread_only: query.unreadOnly ?? false,
      page: query.page ?? 1,
      page_size: query.pageSize,
      type: query.type || undefined,
    },
  })
}

export function markNotificationRead(notificationId: string): Promise<NotificationItem> {
  return api.patch(`/notifications/${notificationId}/read`)
}

export function markAllNotificationsRead(): Promise<{
  success: boolean
  updated_count: number
}> {
  return api.patch('/notifications/read-all')
}
