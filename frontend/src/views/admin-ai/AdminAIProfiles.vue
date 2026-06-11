<template>
  <section class="ai-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
    <div class="flex items-center justify-between gap-3 border-b border-[var(--border)] pb-4">
      <div>
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Profiles</p>
        <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">家庭画像</h2>
      </div>
      <span class="text-sm text-[var(--text-muted)]">只读</span>
    </div>

    <div class="mt-5 grid gap-4 xl:grid-cols-2">
      <article v-for="profile in aiProfiles" :key="profile.id" class="ai-surface rounded-lg border border-[var(--border)] p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-medium text-[var(--text)]">{{ profile.title }}</p>
            <p class="mt-1 text-xs text-[var(--text-muted)]">
              {{ profile.subject_type }} · {{ formatDate(profile.updated_at) }}
            </p>
          </div>
        </div>
        <p class="mt-3 break-words text-xs leading-5 text-[var(--text-secondary)]">{{ profile.summary || '暂无摘要' }}</p>

        <div v-if="profile.traits?.length" class="mt-4">
          <p class="text-xs font-medium text-[var(--text-muted)]">特征</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <span v-for="trait in profile.traits" :key="trait" class="rounded-md bg-[var(--accent-soft)] px-2 py-1 text-xs text-[var(--accent)]">
              {{ trait }}
            </span>
          </div>
        </div>

        <div v-if="profile.preferences?.length" class="mt-4">
          <p class="text-xs font-medium text-[var(--text-muted)]">偏好</p>
          <div class="mt-2 flex flex-wrap gap-2">
            <span v-for="preference in profile.preferences" :key="preference" class="rounded-md border border-[var(--border)] px-2 py-1 text-xs text-[var(--text-secondary)]">
              {{ preference }}
            </span>
          </div>
        </div>

        <div v-if="profile.memories?.length" class="mt-4">
          <p class="text-xs font-medium text-[var(--text-muted)]">记忆片段</p>
          <ul class="mt-2 space-y-2 text-xs leading-5 text-[var(--text-secondary)]">
            <li v-for="memory in profile.memories.slice(0, 4)" :key="memory" class="break-words">
              {{ memory }}
            </li>
          </ul>
        </div>
      </article>
      <p v-if="!aiProfiles.length" class="empty-state xl:col-span-2">暂无画像。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { formatDate, useAdminAI } from './useAdminAI'

const { aiProfiles } = useAdminAI()
</script>
