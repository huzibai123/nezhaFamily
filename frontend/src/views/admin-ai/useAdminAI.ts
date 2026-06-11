import { computed, inject, onMounted, provide, reactive, ref } from 'vue'
import type { ComputedRef, InjectionKey, Reactive, Ref } from 'vue'
import {
  createAIJob,
  createAIPersona,
  createAIReport,
  deleteAIPersona,
  getAIAlbumSuggestions,
  getAIJobs,
  getAIPersonas,
  getAIProfiles,
  getAIReports,
  getAIStatus,
  publishAIReport,
  reviewAIAlbumSuggestion,
  testAIProvider,
  updateAIPersona,
  updateAIProvider,
  type AIAlbumSuggestion,
  type AIJob,
  type AIPersona,
  type AIPersonaPayload,
  type AIProfile,
  type AIProvider,
  type AIProviderUpdate,
  type AIReportDraft,
  type AIStatus,
} from '@/api/admin'

export type AIJobType = 'history_learning' | 'album_suggestions'
export type AIReportPeriod = 'week' | 'month'
export type ProviderDraft = AIProviderUpdate & { api_key: string; clear_api_key: boolean }
export type PersonaDraft = AIPersonaPayload

export interface AdminAIContext {
  aiStatus: Ref<AIStatus | null>
  aiPersonas: Ref<AIPersona[]>
  aiJobs: Ref<AIJob[]>
  aiProfiles: Ref<AIProfile[]>
  aiReports: Ref<AIReportDraft[]>
  aiAlbumSuggestions: Ref<AIAlbumSuggestion[]>
  providerDraft: Reactive<ProviderDraft>
  personaDrafts: Reactive<Record<string, PersonaDraft>>
  newPersonaDraft: Reactive<PersonaDraft>
  message: Ref<string>
  loading: Ref<boolean>
  aiStateLoaded: Ref<boolean>
  aiSavingProvider: Ref<boolean>
  aiTestingProvider: Ref<boolean>
  aiPersonaSavingId: Ref<string>
  aiPersonaCreating: Ref<boolean>
  aiJobRunning: Ref<AIJobType | ''>
  aiGeneratingReport: Ref<boolean>
  aiPendingSuggestions: ComputedRef<AIAlbumSuggestion[]>
  enabledPersonaCount: ComputedRef<number>
  autoCommentPersonaCount: ComputedRef<number>
  loadAIState: () => Promise<void>
  saveAIProvider: () => Promise<void>
  testAIConnection: () => Promise<void>
  clearAIProviderKey: () => Promise<void>
  saveAIPersona: (persona: AIPersona) => Promise<void>
  addAIPersona: () => Promise<void>
  disableAIPersona: (persona: AIPersona) => Promise<void>
  runAIJob: (jobType: AIJobType) => Promise<void>
  generateAIReportDraft: (period: AIReportPeriod) => Promise<void>
  publishReportDraft: (report: AIReportDraft) => Promise<void>
  reviewAlbumSuggestion: (suggestion: AIAlbumSuggestion, action: 'approve' | 'reject') => Promise<void>
}

const adminAIContextKey: InjectionKey<AdminAIContext> = Symbol('admin-ai-context')

export const emptyProviderDraft = (): ProviderDraft => ({
  name: '默认模型',
  base_url: 'https://api.openai.com/v1',
  api_key: '',
  clear_api_key: false,
  text_model: 'gpt-4o-mini',
  vision_model: '',
  timeout_seconds: 30,
  enabled: false,
  wire_api: 'chat_completions',
  model_reasoning_effort: '',
  disable_response_storage: false,
})

export const emptyPersonaDraft = (): PersonaDraft => ({
  name: '',
  avatar_url: '',
  persona_type: 'steward',
  tone: '温暖、真诚、简短',
  bio: '',
  enabled: true,
  auto_comment_enabled: true,
  report_enabled: true,
  album_suggestion_enabled: true,
  sort_order: 0,
})

export function provideAdminAI(): AdminAIContext {
  const aiStatus = ref<AIStatus | null>(null)
  const aiPersonas = ref<AIPersona[]>([])
  const aiJobs = ref<AIJob[]>([])
  const aiProfiles = ref<AIProfile[]>([])
  const aiReports = ref<AIReportDraft[]>([])
  const aiAlbumSuggestions = ref<AIAlbumSuggestion[]>([])
  const providerDraft = reactive<ProviderDraft>(emptyProviderDraft())
  const personaDrafts = reactive<Record<string, PersonaDraft>>({})
  const newPersonaDraft = reactive<PersonaDraft>(emptyPersonaDraft())
  const message = ref('')
  const loading = ref(false)
  const aiStateLoaded = ref(false)
  const aiSavingProvider = ref(false)
  const aiTestingProvider = ref(false)
  const aiPersonaSavingId = ref('')
  const aiPersonaCreating = ref(false)
  const aiJobRunning = ref<AIJobType | ''>('')
  const aiGeneratingReport = ref(false)

  const aiPendingSuggestions = computed(() =>
    aiAlbumSuggestions.value.filter((suggestion) => suggestion.status === 'pending')
  )
  const enabledPersonaCount = computed(() => aiPersonas.value.filter((persona) => persona.enabled).length)
  const autoCommentPersonaCount = computed(() =>
    aiPersonas.value.filter((persona) => persona.enabled && persona.auto_comment_enabled).length
  )

  onMounted(loadAIState)

  async function loadAIState() {
    loading.value = true
    message.value = ''
    const [statusResult, personasResult, jobsResult, profilesResult, reportsResult, suggestionsResult] =
      await Promise.allSettled([
        getAIStatus(),
        getAIPersonas(),
        getAIJobs(),
        getAIProfiles(),
        getAIReports(),
        getAIAlbumSuggestions(),
      ])
    const failedSections: string[] = []

    if (statusResult.status === 'fulfilled') {
      const status = statusResult.value
      aiStatus.value = status
      syncProviderDraft(status)
      aiStateLoaded.value = true
    } else {
      failedSections.push(formatErrorMessage(statusResult.reason, '模型状态加载失败'))
    }

    if (personasResult.status === 'fulfilled') {
      const personas = personasResult.value
      aiPersonas.value = personas
      syncPersonaDrafts(personas)
    } else {
      failedSections.push(formatErrorMessage(personasResult.reason, '角色加载失败'))
    }

    if (jobsResult.status === 'fulfilled') {
      aiJobs.value = jobsResult.value
    } else {
      failedSections.push(formatErrorMessage(jobsResult.reason, '任务加载失败'))
    }

    if (profilesResult.status === 'fulfilled') {
      aiProfiles.value = profilesResult.value
    } else {
      failedSections.push(formatErrorMessage(profilesResult.reason, '画像加载失败'))
    }

    if (reportsResult.status === 'fulfilled') {
      aiReports.value = reportsResult.value
    } else {
      failedSections.push(formatErrorMessage(reportsResult.reason, '报告加载失败'))
    }

    if (suggestionsResult.status === 'fulfilled') {
      aiAlbumSuggestions.value = suggestionsResult.value
    } else {
      failedSections.push(formatErrorMessage(suggestionsResult.reason, '相册建议加载失败'))
    }

    message.value = failedSections.length ? `部分 AI 数据加载失败：${failedSections.join('；')}` : ''
    loading.value = false
  }

  function syncProviderDraft(status: AIStatus) {
    const provider = status.provider
    Object.assign(providerDraft, emptyProviderDraft(), {
      name: provider?.name || '默认模型',
      base_url: provider?.base_url || 'https://api.openai.com/v1',
      api_key: '',
      clear_api_key: false,
      text_model: provider?.text_model || 'gpt-4o-mini',
      vision_model: provider?.vision_model || '',
      timeout_seconds: provider?.timeout_seconds || 30,
      enabled: Boolean(provider?.enabled),
      wire_api: provider?.wire_api || 'chat_completions',
      model_reasoning_effort: provider?.model_reasoning_effort || '',
      disable_response_storage: Boolean(provider?.disable_response_storage),
    })
  }

  async function saveAIProvider() {
    if (aiSavingProvider.value || aiTestingProvider.value) return
    if (!ensureAIStateLoaded()) return
    aiSavingProvider.value = true
    message.value = ''
    try {
      const provider = await persistProviderDraft()
      message.value = provider.enabled ? 'AI 配置已保存' : 'AI 配置已保存，当前保持关闭。'
    } catch (error) {
      message.value = formatErrorMessage(error, 'AI 配置保存失败')
    } finally {
      aiSavingProvider.value = false
    }
  }

  async function testAIConnection() {
    if (aiTestingProvider.value || aiSavingProvider.value) return
    if (!ensureAIStateLoaded()) return
    aiTestingProvider.value = true
    message.value = ''
    try {
      message.value = '正在保存当前配置并测试连接...'
      await persistProviderDraft()
      const result = await testAIProvider()
      await loadAIState()
      message.value = result.ok ? result.message : `连接失败：${result.message}`
    } catch (error) {
      message.value = formatErrorMessage(error, 'AI 连接测试失败')
    } finally {
      aiTestingProvider.value = false
    }
  }

  async function clearAIProviderKey() {
    if (aiSavingProvider.value || aiTestingProvider.value) return
    if (!ensureAIStateLoaded()) return
    aiSavingProvider.value = true
    message.value = ''
    try {
      providerDraft.clear_api_key = true
      providerDraft.api_key = ''
      await persistProviderDraft()
      message.value = 'API Key 已清除'
    } catch (error) {
      message.value = formatErrorMessage(error, 'API Key 清除失败')
    } finally {
      aiSavingProvider.value = false
    }
  }

  async function persistProviderDraft(): Promise<AIProvider> {
    const payload: AIProviderUpdate = {
      name: providerDraft.name.trim() || '默认模型',
      base_url: providerDraft.base_url.trim(),
      text_model: providerDraft.text_model.trim(),
      vision_model: providerDraft.vision_model?.trim() || null,
      timeout_seconds: clampNumber(providerDraft.timeout_seconds, 5, 120, 30),
      enabled: providerDraft.enabled,
      wire_api: providerDraft.wire_api || 'chat_completions',
      model_reasoning_effort: providerDraft.model_reasoning_effort?.trim() || null,
      disable_response_storage: Boolean(providerDraft.disable_response_storage),
    }
    const apiKey = providerDraft.api_key.trim()
    if (apiKey) {
      payload.api_key = apiKey
    }
    if (providerDraft.clear_api_key) {
      payload.clear_api_key = true
    }
    const provider = await updateAIProvider(payload)
    providerDraft.api_key = ''
    providerDraft.clear_api_key = false
    aiStatus.value = await getAIStatus()
    syncProviderDraft(aiStatus.value)
    return provider
  }

  function syncPersonaDrafts(personas: AIPersona[]) {
    const activeIds = new Set(personas.map((persona) => persona.id))
    for (const personaId of Object.keys(personaDrafts)) {
      if (!activeIds.has(personaId)) {
        delete personaDrafts[personaId]
      }
    }
    personas.forEach((persona) => {
      personaDrafts[persona.id] = personaToDraft(persona)
    })
  }

  async function saveAIPersona(persona: AIPersona) {
    const draft = personaDrafts[persona.id]
    if (!draft || aiPersonaSavingId.value) return
    aiPersonaSavingId.value = persona.id
    message.value = ''
    try {
      const updated = await updateAIPersona(persona.id, cleanPersonaPayload(draft))
      aiPersonas.value = aiPersonas.value.map((item) => (item.id === persona.id ? updated : item))
      personaDrafts[updated.id] = personaToDraft(updated)
      await reloadAIStatusOnly()
      message.value = `${updated.name} 已保存`
    } catch (error) {
      message.value = formatErrorMessage(error, 'AI 角色保存失败')
    } finally {
      aiPersonaSavingId.value = ''
    }
  }

  async function addAIPersona() {
    if (aiPersonaCreating.value) return
    if (!newPersonaDraft.name.trim()) {
      message.value = '请先填写 AI 角色名'
      return
    }
    aiPersonaCreating.value = true
    try {
      const created = await createAIPersona(cleanPersonaPayload(newPersonaDraft))
      aiPersonas.value = [...aiPersonas.value, created]
      personaDrafts[created.id] = personaToDraft(created)
      Object.assign(newPersonaDraft, emptyPersonaDraft())
      await reloadAIStatusOnly()
      message.value = `${created.name} 已添加`
    } catch (error) {
      message.value = formatErrorMessage(error, 'AI 角色创建失败')
    } finally {
      aiPersonaCreating.value = false
    }
  }

  async function disableAIPersona(persona: AIPersona) {
    try {
      await deleteAIPersona(persona.id)
      const updated = { ...persona, enabled: false, auto_comment_enabled: false }
      aiPersonas.value = aiPersonas.value.map((item) => (item.id === persona.id ? updated : item))
      personaDrafts[persona.id] = personaToDraft(updated)
      await reloadAIStatusOnly()
      message.value = `${persona.name} 已停用`
    } catch (error) {
      message.value = formatErrorMessage(error, 'AI 角色停用失败')
    }
  }

  async function runAIJob(jobType: AIJobType) {
    if (aiJobRunning.value) return
    aiJobRunning.value = jobType
    message.value = ''
    try {
      const job = await createAIJob(jobType)
      aiJobs.value = [job, ...aiJobs.value.filter((item) => item.id !== job.id)]
      message.value = `${aiJobLabel(job.job_type)}已启动`
    } catch (error) {
      message.value = formatErrorMessage(error, `${aiJobLabel(jobType)}启动失败`)
    } finally {
      aiJobRunning.value = ''
    }
  }

  async function generateAIReportDraft(period: AIReportPeriod) {
    if (aiGeneratingReport.value) return
    aiGeneratingReport.value = true
    message.value = ''
    try {
      const now = new Date()
      const start = new Date(now)
      start.setDate(now.getDate() - (period === 'week' ? 7 : 30))
      const draft = await createAIReport({
        period_type: period,
        period_start: start.toISOString(),
        period_end: now.toISOString(),
        persona_id: aiPersonas.value.find((persona) => persona.enabled && persona.report_enabled)?.id || null,
      })
      aiReports.value = [draft, ...aiReports.value.filter((item) => item.id !== draft.id)]
      message.value = `${draft.title} 已生成草稿`
    } catch (error) {
      message.value = formatErrorMessage(error, 'AI 回忆报告生成失败')
    } finally {
      aiGeneratingReport.value = false
    }
  }

  async function publishReportDraft(report: AIReportDraft) {
    try {
      const updated = await publishAIReport(report.id)
      aiReports.value = aiReports.value.map((item) => (item.id === report.id ? updated : item))
      message.value = `${updated.title} 已发布到时间线`
    } catch (error) {
      message.value = formatErrorMessage(error, 'AI 报告发布失败')
    }
  }

  async function reviewAlbumSuggestion(suggestion: AIAlbumSuggestion, action: 'approve' | 'reject') {
    try {
      const updated = await reviewAIAlbumSuggestion(suggestion.id, {
        action,
        album_name: suggestion.suggested_album_name || null,
      })
      aiAlbumSuggestions.value = aiAlbumSuggestions.value.map((item) =>
        item.id === suggestion.id ? updated : item
      )
      message.value = action === 'approve' ? '相册建议已通过' : '相册建议已忽略'
    } catch (error) {
      message.value = formatErrorMessage(error, '相册建议处理失败')
    }
  }

  async function reloadAIStatusOnly() {
    aiStatus.value = await getAIStatus()
  }

  function ensureAIStateLoaded(): boolean {
    if (aiStateLoaded.value) return true
    message.value = 'AI 配置仍在加载，请稍后再保存。'
    return false
  }

  const context: AdminAIContext = {
    aiStatus,
    aiPersonas,
    aiJobs,
    aiProfiles,
    aiReports,
    aiAlbumSuggestions,
    providerDraft,
    personaDrafts,
    newPersonaDraft,
    message,
    loading,
    aiStateLoaded,
    aiSavingProvider,
    aiTestingProvider,
    aiPersonaSavingId,
    aiPersonaCreating,
    aiJobRunning,
    aiGeneratingReport,
    aiPendingSuggestions,
    enabledPersonaCount,
    autoCommentPersonaCount,
    loadAIState,
    saveAIProvider,
    testAIConnection,
    clearAIProviderKey,
    saveAIPersona,
    addAIPersona,
    disableAIPersona,
    runAIJob,
    generateAIReportDraft,
    publishReportDraft,
    reviewAlbumSuggestion,
  }

  provide(adminAIContextKey, context)
  return context
}

export function useAdminAI(): AdminAIContext {
  const context = inject(adminAIContextKey)
  if (!context) {
    throw new Error('useAdminAI must be used under AdminAIPage')
  }
  return context
}

export function personaToDraft(persona: AIPersona): PersonaDraft {
  return {
    name: persona.name,
    avatar_url: persona.avatar_url || '',
    persona_type: persona.persona_type || 'steward',
    tone: persona.tone || '',
    bio: persona.bio || '',
    enabled: persona.enabled,
    auto_comment_enabled: persona.auto_comment_enabled,
    report_enabled: persona.report_enabled,
    album_suggestion_enabled: persona.album_suggestion_enabled,
    sort_order: persona.sort_order || 0,
  }
}

export function cleanPersonaPayload(draft: PersonaDraft): AIPersonaPayload {
  return {
    name: draft.name.trim(),
    avatar_url: draft.avatar_url?.trim() || null,
    persona_type: draft.persona_type || 'custom',
    tone: draft.tone?.trim() || null,
    bio: draft.bio?.trim() || null,
    enabled: Boolean(draft.enabled),
    auto_comment_enabled: Boolean(draft.auto_comment_enabled),
    report_enabled: Boolean(draft.report_enabled),
    album_suggestion_enabled: Boolean(draft.album_suggestion_enabled),
    sort_order: Number(draft.sort_order || 0),
  }
}

export function clampNumber(value: number | undefined, min: number, max: number, fallback: number) {
  if (typeof value !== 'number' || Number.isNaN(value)) return fallback
  return Math.min(max, Math.max(min, value))
}

export function formatErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string') return error
  if (Array.isArray(error)) {
    return error
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) return String(item.msg)
        return ''
      })
      .filter(Boolean)
      .join('；') || fallback
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message)
  }
  return fallback
}

export function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('zh-CN')
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function aiStatusLabel(status?: string): string {
  if (status === 'active') return '运行中'
  if (status === 'paused_billing_or_auth') return '欠费或鉴权暂停'
  if (status === 'paused_rate_limit') return '限流暂停'
  if (status === 'paused_error') return '异常暂停'
  return '关闭'
}

export function aiKeySourceLabel(source?: string | null): string {
  if (source === 'database') return '后台保存'
  if (source === 'environment') return '环境变量'
  return '未配置'
}

export function aiStatusClass(status?: string): string {
  if (status === 'active') return 'ai-badge-active'
  if (status?.startsWith('paused')) return 'ai-badge-paused'
  return 'ai-badge-disabled'
}

export function aiJobLabel(jobType: string): string {
  if (jobType === 'history_learning') return '历史学习'
  if (jobType === 'album_suggestions') return '相册建议'
  return jobType
}

export function aiJobStatusLabel(status: string): string {
  if (status === 'pending') return '等待中'
  if (status === 'running') return '运行中'
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'skipped') return '已跳过'
  return status
}

export function aiJobStatusClass(status: string): string {
  if (status === 'completed') return 'ai-badge-active'
  if (status === 'failed' || status === 'skipped') return 'ai-badge-paused'
  return 'ai-badge-disabled'
}
