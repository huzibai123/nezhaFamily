<template>
  <AppShell page-title="AI 家庭管家" page-description="模型连接、角色身份和自动任务">
    <template #header>
      <div class="ai-hero rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-panel)] sm:p-7">
        <div class="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div class="min-w-0">
            <RouterLink
              to="/admin"
              class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
            >
              <ArrowLeft :size="16" stroke-width="2" aria-hidden="true" />
              家庭管理
            </RouterLink>
            <div class="mt-6 flex flex-wrap items-center gap-3">
              <span class="grid h-11 w-11 place-items-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
                <Bot :size="22" stroke-width="1.9" aria-hidden="true" />
              </span>
              <span
                class="rounded-md px-2.5 py-1 text-xs font-medium"
                :class="aiStatusClass(aiStatus?.status)"
              >
                {{ aiStatusLabel(aiStatus?.status) }}
              </span>
            </div>
            <h1 class="mt-4 text-3xl font-semibold leading-tight tracking-normal text-[var(--text)] sm:text-4xl">
              AI 家庭管家
            </h1>
            <p class="mt-3 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
              把模型连接放在主位，角色、任务和回忆草稿分开管理。
            </p>
          </div>
          <button
            @click="loadAIState"
            :disabled="loading"
            class="soft-button inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm text-[var(--text-secondary)] disabled:opacity-50"
            type="button"
          >
            <RefreshCw :size="16" stroke-width="2" aria-hidden="true" />
            {{ loading ? '刷新中' : '刷新' }}
          </button>
        </div>
      </div>
    </template>

    <div class="space-y-8">
      <p
        v-if="message"
        class="rounded-lg border border-[var(--border-focus)] bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--accent)]"
      >
        {{ message }}
      </p>

      <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-7">
        <div class="flex flex-col gap-4 border-b border-[var(--border)] pb-5 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Provider</p>
            <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">模型供应商</h2>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              @click="testAIConnection"
              :disabled="!aiStateLoaded || loading || aiTestingProvider || aiSavingProvider"
              class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm text-[var(--text-secondary)] disabled:opacity-50"
              type="button"
            >
              <FlaskConical :size="16" stroke-width="2" aria-hidden="true" />
              {{ aiTestingProvider ? '保存并测试中' : '保存并测试' }}
            </button>
            <button
              @click="saveAIProvider"
              :disabled="!aiStateLoaded || loading || aiSavingProvider || aiTestingProvider"
              class="primary-button inline-flex items-center gap-2 rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
              type="button"
            >
              <Save :size="16" stroke-width="2" aria-hidden="true" />
              {{ aiSavingProvider ? '保存中' : '保存配置' }}
            </button>
          </div>
        </div>

        <div class="mt-7 grid gap-7 xl:grid-cols-[minmax(0,1fr)_20rem]">
          <div class="space-y-5">
            <div class="grid gap-5 md:grid-cols-2">
              <label class="ai-field">
                <span>供应商名称</span>
                <input v-model="providerDraft.name" class="ai-input" />
              </label>
              <label class="ai-field">
                <span>Base URL</span>
                <input
                  v-model="providerDraft.base_url"
                  class="ai-input"
                  placeholder="https://api.openai.com/v1"
                />
              </label>
              <label class="ai-field">
                <span>Text model</span>
                <input
                  v-model="providerDraft.text_model"
                  class="ai-input"
                  placeholder="deepseek-chat / gpt-4o-mini"
                />
              </label>
              <label class="ai-field">
                <span>Vision model</span>
                <input v-model="providerDraft.vision_model" class="ai-input" placeholder="可留空" />
              </label>
              <label class="ai-field">
                <span>API Key</span>
                <input
                  v-model="providerDraft.api_key"
                  class="ai-input"
                  :placeholder="aiStatus?.provider?.has_api_key ? '已配置，留空则不修改' : 'sk-...'"
                  type="password"
                />
              </label>
              <label class="ai-field">
                <span>超时秒数</span>
                <input
                  v-model.number="providerDraft.timeout_seconds"
                  class="ai-input"
                  max="120"
                  min="5"
                  type="number"
                />
              </label>
            </div>

            <label class="ai-switch">
              <input v-model="providerDraft.enabled" type="checkbox" />
              <span class="ai-switch__track" aria-hidden="true">
                <span class="ai-switch__thumb" />
              </span>
              <span>启用 AI 管家</span>
            </label>
          </div>

          <aside class="provider-summary rounded-xl border border-[var(--border)] bg-[var(--surface-panel)] p-5">
            <p class="text-xs font-medium uppercase tracking-[0.16em] text-[var(--text-muted)]">Current</p>
            <p class="mt-3 text-lg font-semibold text-[var(--text)]">
              {{ aiStatus?.provider?.name || providerDraft.name || '默认模型' }}
            </p>
            <p class="mt-1 break-words text-sm text-[var(--text-secondary)]">
              {{ aiStatus?.provider?.text_model || providerDraft.text_model || '未配置模型' }}
            </p>
            <div class="mt-5 space-y-3 text-sm">
              <div class="flex items-center justify-between gap-4">
                <span class="text-[var(--text-muted)]">密钥</span>
                <span class="font-medium text-[var(--text)]">{{ aiStatus?.provider?.has_api_key ? '已配置' : '未配置' }}</span>
              </div>
              <div class="flex items-center justify-between gap-4">
                <span class="text-[var(--text-muted)]">超时</span>
                <span class="font-medium text-[var(--text)]">{{ providerDraft.timeout_seconds || 30 }} 秒</span>
              </div>
              <div class="flex items-center justify-between gap-4">
                <span class="text-[var(--text-muted)]">状态</span>
                <span class="font-medium text-[var(--text)]">{{ aiStatusLabel(aiStatus?.status) }}</span>
              </div>
            </div>
            <p
              v-if="aiStatus?.provider?.paused_reason || aiStatus?.provider?.last_error"
              class="mt-5 break-words rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3 text-xs leading-5 text-[var(--text-secondary)]"
            >
              {{ aiStatus.provider.paused_reason || aiStatus.provider.last_error }}
            </p>
          </aside>
        </div>
      </section>

      <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-7">
        <div class="flex flex-col gap-3 border-b border-[var(--border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Personas</p>
            <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">AI 角色</h2>
          </div>
          <span class="text-sm text-[var(--text-muted)]">{{ aiPersonas.length }} 个角色</span>
        </div>

        <div class="mt-6 grid gap-4 xl:grid-cols-2">
          <article
            v-for="persona in aiPersonas"
            :key="persona.id"
            class="persona-card rounded-xl border border-[var(--border)] bg-[var(--surface-panel)] p-4"
          >
            <div v-if="personaDrafts[persona.id]" class="space-y-4">
              <div class="grid gap-3 sm:grid-cols-[minmax(0,1fr)_10rem]">
                <label class="ai-field">
                  <span>名称</span>
                  <input v-model="personaDrafts[persona.id].name" class="ai-input" />
                </label>
                <label class="ai-field">
                  <span>类型</span>
                  <select v-model="personaDrafts[persona.id].persona_type" class="ai-input">
                    <option value="steward">总管</option>
                    <option value="nanny">嬷嬷</option>
                    <option value="pet_dog">小金毛</option>
                    <option value="pet_cat">小猫</option>
                    <option value="custom">自定义</option>
                  </select>
                </label>
              </div>

              <label class="ai-field">
                <span>语气</span>
                <input v-model="personaDrafts[persona.id].tone" class="ai-input" placeholder="温暖、真诚、简短" />
              </label>

              <label class="ai-field">
                <span>简介</span>
                <textarea
                  v-model="personaDrafts[persona.id].bio"
                  class="ai-input min-h-24 resize-y"
                  placeholder="这个角色在家庭里的身份"
                />
              </label>

              <div class="grid gap-2 sm:grid-cols-2">
                <label class="ai-check">
                  <input v-model="personaDrafts[persona.id].enabled" type="checkbox" />
                  启用
                </label>
                <label class="ai-check">
                  <input v-model="personaDrafts[persona.id].auto_comment_enabled" type="checkbox" />
                  自动评论
                </label>
                <label class="ai-check">
                  <input v-model="personaDrafts[persona.id].report_enabled" type="checkbox" />
                  回忆报告
                </label>
                <label class="ai-check">
                  <input v-model="personaDrafts[persona.id].album_suggestion_enabled" type="checkbox" />
                  相册建议
                </label>
              </div>

              <div class="flex flex-wrap gap-2 pt-1">
                <button
                  @click="saveAIPersona(persona)"
                  :disabled="aiPersonaSavingId === persona.id"
                  class="primary-button inline-flex items-center gap-2 rounded-lg bg-[var(--text)] px-4 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
                  type="button"
                >
                  <Check :size="15" stroke-width="2" aria-hidden="true" />
                  保存
                </button>
                <button
                  @click="disableAIPersona(persona)"
                  class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)]"
                  type="button"
                >
                  <Power :size="15" stroke-width="2" aria-hidden="true" />
                  停用
                </button>
              </div>
            </div>
          </article>
        </div>

        <div class="mt-6 rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-4">
          <div class="grid gap-3 lg:grid-cols-[minmax(0,0.8fr)_10rem_minmax(0,1fr)_auto]">
            <input v-model="newPersonaDraft.name" class="ai-input" placeholder="新角色名" />
            <select v-model="newPersonaDraft.persona_type" class="ai-input">
              <option value="steward">总管</option>
              <option value="nanny">嬷嬷</option>
              <option value="pet_dog">小金毛</option>
              <option value="pet_cat">小猫</option>
              <option value="custom">自定义</option>
            </select>
            <input v-model="newPersonaDraft.tone" class="ai-input" placeholder="语气" />
            <button
              @click="addAIPersona"
              :disabled="aiPersonaCreating"
              class="primary-button inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
              type="button"
            >
              <Plus :size="16" stroke-width="2" aria-hidden="true" />
              {{ aiPersonaCreating ? '添加中' : '添加' }}
            </button>
          </div>
        </div>
      </section>

      <section class="grid gap-6 xl:grid-cols-2">
        <article class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
          <div class="border-b border-[var(--border)] pb-4">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Jobs</p>
            <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">自动任务</h2>
          </div>
          <div class="mt-5 grid gap-3 sm:grid-cols-2">
            <button
              @click="runAIJob('history_learning')"
              :disabled="Boolean(aiJobRunning)"
              class="task-action"
              type="button"
            >
              <BrainCircuit :size="18" stroke-width="2" aria-hidden="true" />
              历史学习
            </button>
            <button
              @click="runAIJob('album_suggestions')"
              :disabled="Boolean(aiJobRunning)"
              class="task-action"
              type="button"
            >
              <Images :size="18" stroke-width="2" aria-hidden="true" />
              相册建议
            </button>
            <button
              @click="generateAIReportDraft('week')"
              :disabled="aiGeneratingReport"
              class="task-action"
              type="button"
            >
              <Sparkles :size="18" stroke-width="2" aria-hidden="true" />
              周报草稿
            </button>
            <button
              @click="generateAIReportDraft('month')"
              :disabled="aiGeneratingReport"
              class="task-action"
              type="button"
            >
              <Sparkles :size="18" stroke-width="2" aria-hidden="true" />
              月报草稿
            </button>
          </div>
        </article>

        <article class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
          <div class="border-b border-[var(--border)] pb-4">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Progress</p>
            <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">任务进度</h2>
          </div>
          <div class="mt-5 space-y-3">
            <div
              v-for="job in aiJobs.slice(0, 5)"
              :key="job.id"
              class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-medium text-[var(--text)]">{{ aiJobLabel(job.job_type) }}</p>
                <span class="rounded-md px-2 py-1 text-[11px]" :class="aiJobStatusClass(job.status)">
                  {{ aiJobStatusLabel(job.status) }}
                </span>
              </div>
              <p class="mt-2 text-xs text-[var(--text-muted)]">
                {{ job.progress_current }} / {{ job.progress_total }} · {{ formatDateTime(job.created_at) }}
              </p>
              <p v-if="job.error_message" class="mt-2 line-clamp-2 text-xs leading-5 text-[var(--accent)]">
                {{ job.error_message }}
              </p>
            </div>
            <p v-if="!aiJobs.length" class="empty-state">暂无 AI 任务。</p>
          </div>
        </article>
      </section>

      <section class="grid gap-6 xl:grid-cols-2">
        <article class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
          <div class="flex items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Reports</p>
              <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">回忆报告</h2>
            </div>
            <span class="text-sm text-[var(--text-muted)]">{{ aiReports.length }} 个草稿</span>
          </div>
          <div class="mt-5 space-y-3">
            <div
              v-for="report in aiReports.slice(0, 4)"
              :key="report.id"
              class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-medium text-[var(--text)]">{{ report.title }}</p>
                  <p class="mt-1 text-xs text-[var(--text-muted)]">{{ report.status }} · {{ formatDate(report.created_at) }}</p>
                </div>
                <button
                  v-if="!report.published_post_id"
                  @click="publishReportDraft(report)"
                  class="soft-button rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)]"
                  type="button"
                >
                  发布
                </button>
              </div>
              <p class="mt-3 line-clamp-3 text-xs leading-5 text-[var(--text-secondary)]">{{ report.content }}</p>
            </div>
            <p v-if="!aiReports.length" class="empty-state">暂无回忆报告。</p>
          </div>
        </article>

        <article class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
          <div class="flex items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Albums</p>
              <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">相册建议</h2>
            </div>
            <span class="text-sm text-[var(--text-muted)]">{{ aiPendingSuggestions.length }} 条待审</span>
          </div>
          <div class="mt-5 space-y-3">
            <div
              v-for="suggestion in aiPendingSuggestions.slice(0, 4)"
              :key="suggestion.id"
              class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4"
            >
              <p class="text-sm font-medium text-[var(--text)]">{{ suggestion.suggested_album_name || '家庭影像整理' }}</p>
              <p class="mt-2 line-clamp-3 text-xs leading-5 text-[var(--text-muted)]">{{ suggestion.reason || '等待管理员确认。' }}</p>
              <div class="mt-4 flex gap-2">
                <button
                  @click="reviewAlbumSuggestion(suggestion, 'approve')"
                  class="primary-button rounded-lg bg-[var(--text)] px-3 py-1.5 text-xs font-medium text-[var(--surface)]"
                  type="button"
                >
                  通过
                </button>
                <button
                  @click="reviewAlbumSuggestion(suggestion, 'reject')"
                  class="soft-button rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)]"
                  type="button"
                >
                  忽略
                </button>
              </div>
            </div>
            <p v-if="!aiPendingSuggestions.length" class="empty-state">暂无待审建议。</p>
          </div>
        </article>
      </section>
    </div>

    <template #right>
      <RightRail>
        <section class="rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)]">
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Status</p>
          <div class="mt-4 space-y-3">
            <div class="metric-tile">
              <span>启用角色</span>
              <strong>{{ enabledPersonaCount }}</strong>
            </div>
            <div class="metric-tile">
              <span>自动评论</span>
              <strong>{{ autoCommentPersonaCount }}</strong>
            </div>
            <div class="metric-tile">
              <span>待审建议</span>
              <strong>{{ aiPendingSuggestions.length }}</strong>
            </div>
          </div>
        </section>

        <section class="rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)]">
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Profiles</p>
          <div class="mt-4 space-y-3">
            <div v-for="profile in aiProfiles.slice(0, 4)" :key="profile.id" class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
              <p class="truncate text-sm font-medium text-[var(--text)]">{{ profile.title }}</p>
              <p class="mt-1 line-clamp-2 text-xs leading-5 text-[var(--text-muted)]">{{ profile.summary || '暂无摘要' }}</p>
            </div>
            <p v-if="!aiProfiles.length" class="empty-state !p-3">暂无画像。</p>
          </div>
        </section>
      </RightRail>
    </template>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  ArrowLeft,
  Bot,
  BrainCircuit,
  Check,
  FlaskConical,
  Images,
  Plus,
  Power,
  RefreshCw,
  Save,
  Sparkles,
} from 'lucide-vue-next'
import AppShell from '@/components/AppShell.vue'
import RightRail from '@/components/RightRail.vue'
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
  type AIProviderUpdate,
  type AIReportDraft,
  type AIStatus,
} from '@/api/admin'

type AIJobType = 'history_learning' | 'album_suggestions'
type AIReportPeriod = 'week' | 'month'
type ProviderDraft = AIProviderUpdate & { api_key: string }
type PersonaDraft = AIPersonaPayload

const emptyProviderDraft = (): ProviderDraft => ({
  name: '默认模型',
  base_url: 'https://api.openai.com/v1',
  api_key: '',
  text_model: 'gpt-4o-mini',
  vision_model: '',
  timeout_seconds: 30,
  enabled: false,
})

const emptyPersonaDraft = (): PersonaDraft => ({
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
    text_model: provider?.text_model || 'gpt-4o-mini',
    vision_model: provider?.vision_model || '',
    timeout_seconds: provider?.timeout_seconds || 30,
    enabled: Boolean(provider?.enabled),
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

async function persistProviderDraft() {
  const payload: AIProviderUpdate = {
    name: providerDraft.name.trim() || '默认模型',
    base_url: providerDraft.base_url.trim(),
    text_model: providerDraft.text_model.trim(),
    vision_model: providerDraft.vision_model?.trim() || null,
    timeout_seconds: clampNumber(providerDraft.timeout_seconds, 5, 120, 30),
    enabled: providerDraft.enabled,
  }
  if (providerDraft.api_key.trim()) {
    payload.api_key = providerDraft.api_key.trim()
  }
  const provider = await updateAIProvider(payload)
  providerDraft.api_key = ''
  aiStatus.value = {
    enabled: provider.enabled && provider.status === 'active' && provider.has_api_key,
    status: provider.status,
    provider,
    personas_enabled: aiStatus.value?.personas_enabled ?? enabledPersonaCount.value,
    auto_comment_personas: aiStatus.value?.auto_comment_personas ?? autoCommentPersonaCount.value,
  }
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

function personaToDraft(persona: AIPersona): PersonaDraft {
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

function cleanPersonaPayload(draft: PersonaDraft): AIPersonaPayload {
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

function clampNumber(value: number | undefined, min: number, max: number, fallback: number) {
  if (typeof value !== 'number' || Number.isNaN(value)) return fallback
  return Math.min(max, Math.max(min, value))
}

function formatErrorMessage(error: unknown, fallback: string): string {
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

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('zh-CN')
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function aiStatusLabel(status?: string): string {
  if (status === 'active') return '运行中'
  if (status === 'paused_billing_or_auth') return '欠费或鉴权暂停'
  if (status === 'paused_rate_limit') return '限流暂停'
  if (status === 'paused_error') return '异常暂停'
  return '关闭'
}

function aiStatusClass(status?: string): string {
  if (status === 'active') return 'ai-badge-active'
  if (status?.startsWith('paused')) return 'ai-badge-paused'
  return 'ai-badge-disabled'
}

function aiJobLabel(jobType: string): string {
  if (jobType === 'history_learning') return '历史学习'
  if (jobType === 'album_suggestions') return '相册建议'
  return jobType
}

function aiJobStatusLabel(status: string): string {
  if (status === 'pending') return '等待中'
  if (status === 'running') return '运行中'
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  if (status === 'skipped') return '已跳过'
  return status
}

function aiJobStatusClass(status: string): string {
  if (status === 'completed') return 'ai-badge-active'
  if (status === 'failed' || status === 'skipped') return 'ai-badge-paused'
  return 'ai-badge-disabled'
}
</script>

<style scoped>
.ai-hero,
.ai-panel,
.persona-card,
.ai-input,
.soft-button,
.primary-button,
.task-action,
.metric-tile {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.ai-hero,
.ai-panel {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.42), rgba(45, 108, 104, 0.06)),
    var(--surface-card);
}

.ai-field {
  display: grid;
  gap: 0.45rem;
}

.ai-field > span {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.ai-input {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 0.65rem;
  color: var(--text);
  font-size: 0.875rem;
  min-width: 0;
  outline: none;
  padding: 0.7rem 0.85rem;
  width: 100%;
}

.ai-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.ai-switch,
.ai-check {
  align-items: center;
  color: var(--text-secondary);
  display: inline-flex;
  font-size: 0.875rem;
  gap: 0.65rem;
}

.ai-switch input,
.ai-check input {
  accent-color: var(--accent);
}

.ai-switch input {
  position: absolute;
  opacity: 0;
}

.ai-switch__track {
  background: rgba(87, 77, 69, 0.16);
  border: 1px solid rgba(49, 38, 33, 0.12);
  border-radius: 999px;
  display: inline-flex;
  height: 1.55rem;
  padding: 0.15rem;
  width: 2.75rem;
}

.ai-switch__thumb {
  background: var(--surface-card);
  border-radius: 999px;
  box-shadow: 0 4px 12px rgba(47, 39, 35, 0.16);
  height: 1.15rem;
  transform: translateX(0);
  transition: transform 180ms ease;
  width: 1.15rem;
}

.ai-switch input:checked + .ai-switch__track {
  background: var(--accent);
}

.ai-switch input:checked + .ai-switch__track .ai-switch__thumb {
  transform: translateX(1.18rem);
}

.provider-summary,
.persona-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(45, 108, 104, 0.05)),
    var(--surface-panel);
}

.persona-card:hover,
.ai-panel:focus-within {
  border-color: rgba(201, 67, 47, 0.16);
  box-shadow: 0 18px 44px rgba(47, 39, 35, 0.1);
}

.task-action {
  align-items: center;
  background: var(--surface-panel);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  color: var(--text-secondary);
  display: inline-flex;
  font-size: 0.9rem;
  gap: 0.65rem;
  justify-content: flex-start;
  min-height: 3.4rem;
  padding: 0.9rem 1rem;
}

.task-action:hover,
.primary-button:hover,
.soft-button:hover {
  transform: translateY(-1px);
}

.task-action:disabled {
  opacity: 0.5;
}

.metric-tile {
  align-items: center;
  background: var(--surface-panel);
  border: 1px solid var(--border);
  border-radius: 0.7rem;
  display: flex;
  justify-content: space-between;
  padding: 0.85rem;
}

.metric-tile span {
  color: var(--text-muted);
  font-size: 0.8rem;
}

.metric-tile strong {
  color: var(--text);
  font-size: 1.15rem;
}

.empty-state {
  border: 1px dashed var(--border);
  border-radius: 0.7rem;
  color: var(--text-muted);
  font-size: 0.8rem;
  padding: 1rem;
  text-align: center;
}

.ai-badge-active,
.ai-badge-paused,
.ai-badge-disabled {
  border: 1px solid rgba(49, 38, 33, 0.12);
}

.ai-badge-active {
  background: rgba(92, 121, 84, 0.14);
  color: var(--accent-leaf);
}

.ai-badge-paused {
  background: rgba(201, 67, 47, 0.12);
  color: var(--accent);
}

.ai-badge-disabled {
  background: rgba(87, 77, 69, 0.1);
  color: var(--text-secondary);
}

@media (prefers-reduced-motion: reduce) {
  .ai-hero,
  .ai-panel,
  .persona-card,
  .ai-input,
  .soft-button,
  .primary-button,
  .task-action,
  .metric-tile,
  .ai-switch__thumb {
    transition: none;
  }

  .task-action:hover,
  .primary-button:hover,
  .soft-button:hover {
    transform: none;
  }
}
</style>
