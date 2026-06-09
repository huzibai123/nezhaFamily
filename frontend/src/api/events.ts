import api from './index'

export interface Event {
  id: string
  title: string
  description?: string
  start_time: string
  end_time?: string
  is_all_day: boolean
  event_type: 'birthday' | 'anniversary' | 'appointment' | 'holiday' | 'other'
  recurrence_rule?: string
  location?: string
  reminder_minutes?: number
  created_by: string
  created_at: string
  updated_at: string
}

export interface EventListResponse {
  events: Event[]
  total: number
}

// 获取事件列表（按月份查询）
export function getEvents(year: number, month: number): Promise<EventListResponse> {
  return api.get('/events', { params: { year, month } })
}

// 获取事件详情
export function getEvent(eventId: string): Promise<Event> {
  return api.get(`/events/${eventId}`)
}

// 创建事件
export function createEvent(data: {
  title: string
  description?: string
  start_time: string
  end_time?: string
  is_all_day: boolean
  event_type: string
  recurrence_rule?: string
  location?: string
  reminder_minutes?: number
}): Promise<Event> {
  return api.post('/events', data)
}

// 更新事件
export function updateEvent(eventId: string, data: {
  title?: string
  description?: string
  start_time?: string
  end_time?: string
  is_all_day?: boolean
  event_type?: string
  recurrence_rule?: string
  location?: string
  reminder_minutes?: number
}): Promise<Event> {
  return api.put(`/events/${eventId}`, data)
}

// 删除事件
export function deleteEvent(eventId: string): Promise<void> {
  return api.delete(`/events/${eventId}`)
}
