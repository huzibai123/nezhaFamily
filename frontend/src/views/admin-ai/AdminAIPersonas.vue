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
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div class="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-xl bg-[var(--accent-soft)] text-2xl font-semibold text-[var(--accent)]">
              <img
                v-if="personaAvatarUrl(persona)"
                :src="personaAvatarUrl(persona)"
                :alt="`${personaDrafts[persona.id].name || persona.name} 的头像`"
                class="h-full w-full object-cover"
              />
              <span v-else>{{ personaInitial(persona) }}</span>
            </div>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-[var(--text)]">角色头像</p>
              <p class="mt-1 text-xs text-[var(--text-muted)]">会显示在 AI 评论、点赞和通知里。</p>
              <div class="mt-3 grid gap-2 sm:flex sm:flex-wrap">
                <label class="soft-button inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]">
                  <Camera :size="15" stroke-width="2" aria-hidden="true" />
                  {{ uploadingPersonaId === persona.id ? '上传中' : '更换头像' }}
                  <input
                    class="hidden"
                    type="file"
                    accept="image/png,image/jpeg,image/webp,image/gif"
                    :disabled="uploadingPersonaId === persona.id || aiPersonaSavingId === persona.id"
                    @change="uploadPersonaAvatar(persona, $event)"
                  />
                </label>
                <button
                  v-if="personaDrafts[persona.id].avatar_url"
                  @click="clearPersonaAvatar(persona)"
                  :disabled="uploadingPersonaId === persona.id || aiPersonaSavingId === persona.id"
                  class="soft-button inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] disabled:opacity-40"
                  type="button"
                >
                  <Trash2 :size="15" stroke-width="2" aria-hidden="true" />
                  移除
                </button>
              </div>
            </div>
          </div>

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
            <textarea v-model="personaDrafts[persona.id].tone" class="ai-input min-h-16 resize-y" placeholder="温暖、真诚、简短" />
          </label>

          <div class="grid gap-3 sm:grid-cols-3">
            <label class="ai-field">
              <span>评论风格</span>
              <select v-model="personaDrafts[persona.id].comment_style" class="ai-input">
                <option value="warm">温暖</option>
                <option value="gentle">细腻</option>
                <option value="playful">轻快</option>
                <option value="brief">克制</option>
              </select>
            </label>
            <label class="ai-field">
              <span>评论长度</span>
              <select v-model="personaDrafts[persona.id].comment_length" class="ai-input">
                <option value="short">简短</option>
                <option value="medium">中等</option>
              </select>
            </label>
            <label class="ai-field">
              <span>互动频率</span>
              <select v-model="personaDrafts[persona.id].interaction_frequency" class="ai-input">
                <option value="low">低频</option>
                <option value="normal">常规</option>
                <option value="high">积极</option>
              </select>
            </label>
          </div>

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
              <input v-model="personaDrafts[persona.id].auto_like_enabled" type="checkbox" />
              自动点赞
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

          <div class="grid gap-2 pt-1 sm:flex sm:flex-wrap">
            <button
              @click="saveAIPersona(persona)"
              :disabled="aiPersonaSavingId === persona.id"
              class="primary-button inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-4 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
              type="button"
            >
              <Check :size="15" stroke-width="2" aria-hidden="true" />
              保存
            </button>
            <button
              @click="disableAIPersona(persona)"
              class="soft-button inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)]"
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
      <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div class="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-xl bg-[var(--accent-soft)] text-xl font-semibold text-[var(--accent)]">
          <img
            v-if="newPersonaAvatarUrl"
            :src="newPersonaAvatarUrl"
            alt="新 AI 角色头像预览"
            class="h-full w-full object-cover"
          />
          <span v-else>{{ newPersonaInitial }}</span>
        </div>
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-[var(--text)]">新角色头像</p>
          <div class="mt-2 grid gap-2 sm:flex sm:flex-wrap">
            <label class="soft-button inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]">
              <Camera :size="15" stroke-width="2" aria-hidden="true" />
              {{ newPersonaAvatarUploading ? '上传中' : '上传头像' }}
              <input
                class="hidden"
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                :disabled="newPersonaAvatarUploading || aiPersonaCreating"
                @change="uploadNewPersonaAvatar"
              />
            </label>
            <button
              v-if="newPersonaDraft.avatar_url"
              @click="newPersonaDraft.avatar_url = ''"
              :disabled="newPersonaAvatarUploading || aiPersonaCreating"
              class="soft-button inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] disabled:opacity-40"
              type="button"
            >
              <Trash2 :size="15" stroke-width="2" aria-hidden="true" />
              移除
            </button>
          </div>
        </div>
      </div>
      <div class="grid gap-3 lg:grid-cols-[minmax(0,0.8fr)_10rem_minmax(0,1fr)_auto]">
        <input v-model="newPersonaDraft.name" class="ai-input" placeholder="新角色名" />
        <select v-model="newPersonaDraft.persona_type" class="ai-input">
          <option value="steward">总管</option>
          <option value="nanny">嬷嬷</option>
          <option value="pet_dog">小金毛</option>
          <option value="pet_cat">小猫</option>
          <option value="custom">自定义</option>
        </select>
        <textarea v-model="newPersonaDraft.tone" class="ai-input min-h-12 resize-y" placeholder="语气" />
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
      <div class="mt-3 grid gap-3 sm:grid-cols-3">
        <label class="ai-field">
          <span>评论风格</span>
          <select v-model="newPersonaDraft.comment_style" class="ai-input">
            <option value="warm">温暖</option>
            <option value="gentle">细腻</option>
            <option value="playful">轻快</option>
            <option value="brief">克制</option>
          </select>
        </label>
        <label class="ai-field">
          <span>评论长度</span>
          <select v-model="newPersonaDraft.comment_length" class="ai-input">
            <option value="short">简短</option>
            <option value="medium">中等</option>
          </select>
        </label>
        <label class="ai-field">
          <span>互动频率</span>
          <select v-model="newPersonaDraft.interaction_frequency" class="ai-input">
            <option value="low">低频</option>
            <option value="normal">常规</option>
            <option value="high">积极</option>
          </select>
        </label>
      </div>
      <label class="ai-check mt-3">
        <input v-model="newPersonaDraft.auto_like_enabled" type="checkbox" />
        新角色参与自动点赞
      </label>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Camera, Check, Plus, Power, Trash2 } from 'lucide-vue-next'
import { uploadMedia } from '@/api/media'
import type { AIPersona } from '@/api/admin'
import { mediaUrl } from '@/utils/media'
import { useAdminAI } from './useAdminAI'

const {
  aiPersonas,
  personaDrafts,
  newPersonaDraft,
  message,
  aiPersonaSavingId,
  aiPersonaCreating,
  saveAIPersona,
  addAIPersona,
  disableAIPersona,
} = useAdminAI()

const uploadingPersonaId = ref('')
const newPersonaAvatarUploading = ref(false)
const newPersonaAvatarUrl = computed(() =>
  newPersonaDraft.avatar_url ? mediaUrl(newPersonaDraft.avatar_url) : ''
)
const newPersonaInitial = computed(() =>
  (newPersonaDraft.name.trim().charAt(0) || 'A').toUpperCase()
)

function personaAvatarUrl(persona: AIPersona): string {
  const avatar = personaDrafts[persona.id]?.avatar_url || persona.avatar_url || ''
  return avatar ? mediaUrl(avatar) : ''
}

function personaInitial(persona: AIPersona): string {
  const name = personaDrafts[persona.id]?.name || persona.name || 'A'
  return name.charAt(0).toUpperCase()
}

function clearPersonaAvatar(persona: AIPersona) {
  personaDrafts[persona.id].avatar_url = ''
}

async function uploadImageFile(file: File): Promise<string> {
  if (!file.type.startsWith('image/')) {
    throw new Error('头像只支持图片文件')
  }
  const response = await uploadMedia([file])
  const uploaded = response.files[0]
  if (!uploaded || uploaded.type !== 'image') {
    throw new Error('头像只支持图片文件')
  }
  return uploaded.url || uploaded.raw_url || ''
}

async function uploadPersonaAvatar(persona: AIPersona, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || uploadingPersonaId.value) return

  uploadingPersonaId.value = persona.id
  message.value = ''
  try {
    personaDrafts[persona.id].avatar_url = await uploadImageFile(file)
    message.value = '头像已上传，保存角色后生效'
  } catch (error) {
    message.value = error instanceof Error ? error.message : '头像上传失败'
  } finally {
    uploadingPersonaId.value = ''
  }
}

async function uploadNewPersonaAvatar(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || newPersonaAvatarUploading.value) return

  newPersonaAvatarUploading.value = true
  message.value = ''
  try {
    newPersonaDraft.avatar_url = await uploadImageFile(file)
    message.value = '头像已上传，添加角色后生效'
  } catch (error) {
    message.value = error instanceof Error ? error.message : '头像上传失败'
  } finally {
    newPersonaAvatarUploading.value = false
  }
}
</script>
