<template>
  <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
    <div class="flex flex-col gap-3 border-b border-[var(--border)] pb-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Reports</p>
        <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">回忆报告</h2>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          @click="generateAIReportDraft('week')"
          :disabled="aiGeneratingReport"
          class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-xs text-[var(--text-secondary)] disabled:opacity-50"
          type="button"
        >
          <Sparkles :size="15" stroke-width="2" aria-hidden="true" />
          周报草稿
        </button>
        <button
          @click="generateAIReportDraft('month')"
          :disabled="aiGeneratingReport"
          class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-xs text-[var(--text-secondary)] disabled:opacity-50"
          type="button"
        >
          <Sparkles :size="15" stroke-width="2" aria-hidden="true" />
          月报草稿
        </button>
      </div>
    </div>

    <div class="mt-5 grid gap-4">
      <article v-for="report in aiReports" :key="report.id" class="ai-surface rounded-lg border border-[var(--border)] p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-medium text-[var(--text)]">{{ report.title }}</p>
            <p class="mt-1 text-xs text-[var(--text-muted)]">
              {{ report.status }} · {{ formatDate(report.created_at) }}
            </p>
          </div>
          <button
            v-if="!report.published_post_id"
            @click="publishReportDraft(report)"
            class="soft-button shrink-0 rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)]"
            type="button"
          >
            发布
          </button>
        </div>
        <p class="mt-3 whitespace-pre-wrap break-words text-xs leading-5 text-[var(--text-secondary)]">{{ report.content }}</p>
      </article>
      <p v-if="!aiReports.length" class="empty-state">暂无回忆报告。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { Sparkles } from 'lucide-vue-next'
import { formatDate, useAdminAI } from './useAdminAI'

const {
  aiReports,
  aiGeneratingReport,
  generateAIReportDraft,
  publishReportDraft,
} = useAdminAI()
</script>
