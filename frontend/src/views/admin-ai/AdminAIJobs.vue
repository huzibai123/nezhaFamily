<template>
  <section class="grid gap-6 xl:grid-cols-2">
    <article class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
      <div class="border-b border-[var(--border)] pb-4">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Jobs</p>
        <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">自动任务</h2>
      </div>
      <div class="mt-5 rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3 text-xs leading-5 text-[var(--text-muted)]">
        <p class="font-medium text-[var(--text-secondary)]">Provider：{{ aiStatus?.provider?.name || '默认模型' }} · {{ aiStatusLabel(aiStatus?.status) }}</p>
        <p v-if="aiStatus?.provider?.paused_reason || aiStatus?.provider?.last_error" class="mt-1 text-[var(--accent)]">
          {{ aiStatus?.provider?.paused_reason || aiStatus?.provider?.last_error }}
        </p>
      </div>
      <div class="mt-5 grid gap-3 sm:grid-cols-2">
        <button @click="runAIJob('history_learning')" :disabled="Boolean(aiJobRunning)" class="task-action" type="button">
          <BrainCircuit :size="18" stroke-width="2" aria-hidden="true" />
          历史学习
        </button>
        <button @click="runAIJob('album_suggestions')" :disabled="Boolean(aiJobRunning)" class="task-action" type="button">
          <Images :size="18" stroke-width="2" aria-hidden="true" />
          相册建议
        </button>
        <button @click="generateAIReportDraft('week')" :disabled="aiGeneratingReport" class="task-action" type="button">
          <Sparkles :size="18" stroke-width="2" aria-hidden="true" />
          周报草稿
        </button>
        <button @click="generateAIReportDraft('month')" :disabled="aiGeneratingReport" class="task-action" type="button">
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
        <div v-for="job in aiJobs" :key="job.id" class="ai-surface rounded-lg border border-[var(--border)] p-4">
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
          <p v-if="jobResultSummary(job.result)" class="mt-2 line-clamp-2 text-xs leading-5 text-[var(--text-muted)]">
            {{ jobResultSummary(job.result) }}
          </p>
        </div>
        <p v-if="!aiJobs.length" class="empty-state">暂无 AI 任务。</p>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { BrainCircuit, Images, Sparkles } from 'lucide-vue-next'
import {
  aiJobLabel,
  aiStatusLabel,
  aiJobStatusClass,
  aiJobStatusLabel,
  formatDateTime,
  jobResultSummary,
  useAdminAI,
} from './useAdminAI'

const {
  aiStatus,
  aiJobs,
  aiJobRunning,
  aiGeneratingReport,
  runAIJob,
  generateAIReportDraft,
} = useAdminAI()
</script>
