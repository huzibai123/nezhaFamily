<template>
  <div class="grid gap-6 xl:grid-cols-2">
    <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
      <div class="flex flex-col gap-4 border-b border-[var(--border)] pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Status</p>
          <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">连接概览</h2>
        </div>
        <span class="w-fit rounded-md px-2.5 py-1 text-xs font-medium" :class="aiStatusClass(aiStatus?.status)">
          {{ aiStatusLabel(aiStatus?.status) }}
        </span>
      </div>

      <div class="mt-5 grid gap-3 sm:grid-cols-2">
        <div class="metric-tile">
          <span>启用角色</span>
          <strong>{{ enabledPersonaCount }}</strong>
        </div>
        <div class="metric-tile">
          <span>自动评论</span>
          <strong>{{ autoCommentPersonaCount }}</strong>
        </div>
        <div class="metric-tile">
          <span>自动点赞</span>
          <strong>{{ autoLikePersonaCount }}</strong>
        </div>
        <div class="metric-tile">
          <span>待审建议</span>
          <strong>{{ aiPendingSuggestions.length }}</strong>
        </div>
        <div class="metric-tile">
          <span>任务记录</span>
          <strong>{{ aiJobs.length }}</strong>
        </div>
      </div>
    </section>

    <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
      <div class="border-b border-[var(--border)] pb-5">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Provider</p>
        <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">模型供应商</h2>
      </div>
      <div class="mt-5 space-y-3 text-sm">
        <div class="flex items-center justify-between gap-4">
          <span class="text-[var(--text-muted)]">名称</span>
          <span class="min-w-0 truncate font-medium text-[var(--text)]">{{ aiStatus?.provider?.name || '默认模型' }}</span>
        </div>
        <div class="flex items-center justify-between gap-4">
          <span class="text-[var(--text-muted)]">Text model</span>
          <span class="min-w-0 truncate font-medium text-[var(--text)]">{{ aiStatus?.provider?.text_model || '未配置' }}</span>
        </div>
        <div class="flex items-center justify-between gap-4">
          <span class="text-[var(--text-muted)]">密钥</span>
          <span class="font-medium text-[var(--text)]">{{ aiStatus?.provider?.has_api_key ? '已配置' : '未配置' }}</span>
        </div>
        <div class="flex items-center justify-between gap-4">
          <span class="text-[var(--text-muted)]">Key 来源</span>
          <span class="min-w-0 truncate font-medium text-[var(--text)]">{{ aiKeySourceLabel(aiStatus?.provider?.api_key_source) }}</span>
        </div>
        <p v-if="aiStatus?.provider?.paused_reason || aiStatus?.provider?.last_error" class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3 text-xs leading-5 text-[var(--accent)]">
          {{ aiStatus?.provider?.paused_reason || aiStatus?.provider?.last_error }}
        </p>
      </div>
    </section>

    <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
      <div class="border-b border-[var(--border)] pb-5">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Jobs</p>
        <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">最近任务</h2>
      </div>
      <div class="mt-5 space-y-3">
        <div v-for="job in aiJobs.slice(0, 4)" :key="job.id" class="ai-surface rounded-lg border border-[var(--border)] p-4">
          <div class="flex items-center justify-between gap-3">
            <p class="text-sm font-medium text-[var(--text)]">{{ aiJobLabel(job.job_type) }}</p>
            <span class="rounded-md px-2 py-1 text-[11px]" :class="aiJobStatusClass(job.status)">
              {{ aiJobStatusLabel(job.status) }}
            </span>
          </div>
          <p class="mt-2 text-xs text-[var(--text-muted)]">
            {{ job.progress_current }} / {{ job.progress_total }} · {{ formatDateTime(job.created_at) }}
          </p>
          <p v-if="job.error_message || jobResultSummary(job.result)" class="mt-2 line-clamp-2 text-xs leading-5 text-[var(--text-muted)]">
            {{ job.error_message || jobResultSummary(job.result) }}
          </p>
        </div>
        <p v-if="!aiJobs.length" class="empty-state">暂无 AI 任务。</p>
      </div>
    </section>

    <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
      <div class="border-b border-[var(--border)] pb-5">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Drafts</p>
        <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">内容草稿</h2>
      </div>
      <div class="mt-5 grid gap-3 sm:grid-cols-2">
        <div class="metric-tile">
          <span>回忆报告</span>
          <strong>{{ aiReports.length }}</strong>
        </div>
        <div class="metric-tile">
          <span>家庭画像</span>
          <strong>{{ aiProfiles.length }}</strong>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import {
  aiJobLabel,
  aiJobStatusClass,
  aiJobStatusLabel,
  aiKeySourceLabel,
  aiStatusClass,
  aiStatusLabel,
  formatDateTime,
  jobResultSummary,
  useAdminAI,
} from './useAdminAI'

const {
  aiStatus,
  aiJobs,
  aiReports,
  aiProfiles,
  aiPendingSuggestions,
  enabledPersonaCount,
  autoCommentPersonaCount,
  autoLikePersonaCount,
} = useAdminAI()
</script>
