<template>
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
            <input v-model="providerDraft.base_url" class="ai-input" placeholder="https://api.openai.com/v1" />
          </label>
          <label class="ai-field">
            <span>Text model</span>
            <input v-model="providerDraft.text_model" class="ai-input" placeholder="deepseek-chat / gpt-4o-mini" />
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
            <input v-model.number="providerDraft.timeout_seconds" class="ai-input" max="120" min="5" type="number" />
          </label>
        </div>

        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <label class="ai-switch">
            <input v-model="providerDraft.enabled" type="checkbox" />
            <span class="ai-switch__track" aria-hidden="true">
              <span class="ai-switch__thumb" />
            </span>
            <span>启用 AI 管家</span>
          </label>
          <button
            @click="clearAIProviderKey"
            :disabled="!aiStateLoaded || loading || aiSavingProvider || aiTestingProvider || aiStatus?.provider?.api_key_source !== 'database'"
            class="soft-button inline-flex w-fit items-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)] disabled:opacity-50"
            type="button"
          >
            <KeyRound :size="15" stroke-width="2" aria-hidden="true" />
            清除后台 Key
          </button>
        </div>
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
            <span class="text-[var(--text-muted)]">Key 来源</span>
            <span class="min-w-0 truncate font-medium text-[var(--text)]">{{ aiKeySourceLabel(aiStatus?.provider?.api_key_source) }}</span>
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
</template>

<script setup lang="ts">
import { FlaskConical, KeyRound, Save } from 'lucide-vue-next'
import { aiKeySourceLabel, aiStatusLabel, useAdminAI } from './useAdminAI'

const {
  aiStatus,
  providerDraft,
  loading,
  aiStateLoaded,
  aiSavingProvider,
  aiTestingProvider,
  saveAIProvider,
  testAIConnection,
  clearAIProviderKey,
} = useAdminAI()
</script>
