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
              <span class="rounded-md px-2.5 py-1 text-xs font-medium" :class="aiStatusClass(aiStatus?.status)">
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

    <div class="space-y-6">
      <nav class="rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-2 shadow-[var(--shadow-panel)]" aria-label="AI 管家二级导航">
        <div class="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-7">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="ai-tab inline-flex min-h-10 items-center justify-center rounded-lg px-3 py-2 text-center text-sm font-medium text-[var(--text-secondary)]"
            active-class="!bg-[var(--text)] !text-[var(--surface)]"
          >
            {{ item.label }}
          </RouterLink>
        </div>
      </nav>

      <p
        v-if="message"
        class="rounded-lg border border-[var(--border-focus)] bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--accent)]"
      >
        {{ message }}
      </p>

      <RouterView />
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
            <div
              v-for="profile in aiProfiles.slice(0, 4)"
              :key="profile.id"
              class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3"
            >
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
import { ArrowLeft, Bot, RefreshCw } from 'lucide-vue-next'
import AppShell from '@/components/AppShell.vue'
import RightRail from '@/components/RightRail.vue'
import { aiStatusClass, aiStatusLabel, provideAdminAI } from './admin-ai/useAdminAI'
import './admin-ai/admin-ai.css'

const {
  aiStatus,
  aiProfiles,
  message,
  loading,
  aiPendingSuggestions,
  enabledPersonaCount,
  autoCommentPersonaCount,
  loadAIState,
} = provideAdminAI()

const navItems = [
  { label: '概览', to: '/admin/ai' },
  { label: 'Provider', to: '/admin/ai/provider' },
  { label: '角色', to: '/admin/ai/personas' },
  { label: '任务', to: '/admin/ai/jobs' },
  { label: '报告', to: '/admin/ai/reports' },
  { label: '建议', to: '/admin/ai/suggestions' },
  { label: '画像', to: '/admin/ai/profiles' },
]
</script>
