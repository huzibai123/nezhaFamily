<template>
  <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
    <div class="flex flex-col gap-3 border-b border-[var(--border)] pb-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Albums</p>
        <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">相册建议</h2>
      </div>
      <span class="text-sm text-[var(--text-muted)]">{{ aiPendingSuggestions.length }} 条待审</span>
    </div>

    <div class="mt-5 grid gap-4">
      <article
        v-for="suggestion in aiAlbumSuggestions"
        :key="suggestion.id"
        class="ai-surface rounded-lg border border-[var(--border)] p-4"
      >
        <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div class="min-w-0">
            <p class="break-words text-sm font-medium text-[var(--text)]">
              {{ suggestion.suggested_album_name || '家庭影像整理' }}
            </p>
            <p class="mt-1 text-xs text-[var(--text-muted)]">
              {{ suggestion.status }} · {{ formatDate(suggestion.created_at) }}
            </p>
          </div>
          <div v-if="suggestion.status === 'pending'" class="grid shrink-0 grid-cols-2 gap-2 sm:flex">
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
        <p class="mt-3 break-words text-xs leading-5 text-[var(--text-muted)]">
          {{ suggestion.reason || '等待管理员确认。' }}
        </p>
      </article>
      <p v-if="!aiAlbumSuggestions.length" class="empty-state">暂无相册建议。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { formatDate, useAdminAI } from './useAdminAI'

const {
  aiAlbumSuggestions,
  aiPendingSuggestions,
  reviewAlbumSuggestion,
} = useAdminAI()
</script>
