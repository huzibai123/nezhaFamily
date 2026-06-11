import api from './index'

export type PostCaptionMode = 'polish' | 'generate'

export interface PostCaptionRequest {
  mode: PostCaptionMode
  content?: string
  files?: File[]
}

export interface PostCaptionResponse {
  content: string
  mode: PostCaptionMode
  used_media_count: number
}

export function generatePostCaption(payload: PostCaptionRequest): Promise<PostCaptionResponse> {
  const formData = new FormData()
  const trimmed = payload.content?.trim()

  formData.append('mode', payload.mode)
  if (trimmed) {
    formData.append('content', trimmed)
  }
  payload.files?.forEach((file) => formData.append('files[]', file))

  return api.post('/ai/post-caption', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
