<template>
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
            <textarea v-model="personaDrafts[persona.id].bio" class="ai-input min-h-24 resize-y" placeholder="这个角色在家庭里的身份" />
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
</template>

<script setup lang="ts">
import { Check, Plus, Power } from 'lucide-vue-next'
import { useAdminAI } from './useAdminAI'

const {
  aiPersonas,
  personaDrafts,
  newPersonaDraft,
  aiPersonaSavingId,
  aiPersonaCreating,
  saveAIPersona,
  addAIPersona,
  disableAIPersona,
} = useAdminAI()
</script>
