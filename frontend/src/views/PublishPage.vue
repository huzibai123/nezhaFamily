<template>
  <AppShell page-title="发布记忆" page-description="支持文字、图片、视频，也可以只发一组照片">
    <template #header>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <button
            @click="handleCancel"
            :disabled="isBusy"
            class="soft-button mb-4 inline-flex rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-40"
            type="button"
          >
            取消
          </button>
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">新的家庭动态</p>
          <h1 class="mt-2 text-2xl font-semibold tracking-normal text-[var(--text)] sm:text-3xl">
            发布记忆
          </h1>
        </div>
        <button
          @click="handlePublish"
          :disabled="!canPublish || isBusy"
          class="primary-button inline-flex w-full items-center justify-center rounded-lg bg-[var(--text)] px-5 py-2.5 text-sm font-medium text-[var(--surface)] active:scale-[0.98] disabled:opacity-30 sm:w-auto"
          type="button"
        >
          {{ publishing ? '发布中...' : '发布' }}
        </button>
      </div>
    </template>

    <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_22rem] xl:gap-6">
      <section class="editor-panel rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)]">
        <div class="mb-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <label class="block text-sm font-semibold text-[var(--text)]" for="post-content">
            今天想留下什么？
          </label>
          <button
            @click="handleCaptionAI"
            :disabled="!canUseCaptionAI || isBusy"
            class="ai-caption-button inline-flex w-full min-w-0 items-center justify-center gap-2 rounded-lg border border-[color:rgb(45_108_104_/_0.24)] bg-[color:rgb(45_108_104_/_0.08)] px-3 py-2 text-sm font-medium text-[var(--accent-leaf)] hover:bg-[color:rgb(45_108_104_/_0.12)] disabled:opacity-45 sm:w-auto"
            type="button"
          >
            <Loader2 v-if="aiGenerating" class="h-4 w-4 shrink-0 animate-spin" :stroke-width="2" aria-hidden="true" />
            <Sparkles v-else class="h-4 w-4 shrink-0" :stroke-width="2" aria-hidden="true" />
            <span class="min-w-0 truncate">{{ aiGenerating ? '生成中...' : aiCaptionButtonLabel }}</span>
          </button>
        </div>
        <textarea
          id="post-content"
          v-model="content"
          placeholder="分享家人的美好时刻..."
          rows="12"
          :disabled="isBusy"
          class="editor-input min-h-[18rem] w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-4 text-base leading-7 text-[var(--text)] outline-none placeholder:text-[var(--text-muted)] focus:border-[var(--border-focus)] disabled:cursor-not-allowed disabled:opacity-60"
        />

        <p class="mt-3 text-xs leading-5 text-[var(--text-muted)]">
          家庭照片不一定需要长文字。只上传图片或视频也可以发布。
        </p>
      </section>

      <aside class="space-y-4">
        <section class="media-panel rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4 shadow-[var(--shadow-panel)]">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-[var(--text)]">媒体</h2>
            <span class="text-xs text-[var(--text-muted)]">{{ mediaFiles.length }}/9</span>
          </div>

          <div v-if="previews.length" class="mb-4 grid grid-cols-3 gap-2 sm:grid-cols-4 xl:grid-cols-3">
            <div
              v-for="(preview, index) in previews"
              :key="preview"
              class="preview-tile relative aspect-square overflow-hidden rounded-lg bg-[var(--surface-card)]"
            >
              <video
                v-if="mediaFiles[index]?.type.startsWith('video/')"
                :src="preview"
                class="h-full w-full object-cover"
                muted
              />
              <img v-else :src="preview" class="h-full w-full object-cover" alt="" />
              <button
                @click="removeMedia(index)"
                :disabled="isBusy"
                class="absolute right-1.5 top-1.5 grid h-7 w-7 place-items-center rounded-lg bg-[color:rgb(75_40_25_/_0.58)] text-xs text-[var(--text-inverse)] transition-opacity hover:opacity-85"
                type="button"
              >
                ×
              </button>
              <div class="absolute bottom-1.5 left-1.5 flex gap-1">
                <button
                  @click="moveMedia(index, -1)"
                  :disabled="isBusy || index === 0"
                  class="preview-sort-button"
                  type="button"
                  aria-label="向前移动"
                >
                  ‹
                </button>
                <button
                  @click="moveMedia(index, 1)"
                  :disabled="isBusy || index === previews.length - 1"
                  class="preview-sort-button"
                  type="button"
                  aria-label="向后移动"
                >
                  ›
                </button>
              </div>
            </div>
          </div>

          <button
            v-if="mediaFiles.length < 9"
            @click="triggerFileInput"
            :disabled="isBusy"
            class="upload-dropzone grid w-full place-items-center rounded-lg border border-dashed border-[var(--border)] px-4 py-10 text-center text-sm text-[var(--text-muted)] hover:border-[var(--border-focus)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text-secondary)] disabled:opacity-45 sm:py-12"
            type="button"
          >
            添加图片或视频
          </button>
          <input ref="fileInput" type="file" accept="image/*,video/*" multiple class="hidden" :disabled="isBusy" @change="onFilesSelected" />

          <div class="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3">
            <label class="mb-2 block text-xs font-medium uppercase tracking-[0.12em] text-[var(--text-muted)]" for="target-album">
              目标相册
            </label>
            <select
              id="target-album"
              v-model="selectedAlbumId"
              class="editor-input h-10 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none"
              :disabled="isBusy || albumsLoading || !albums.length"
            >
              <option value="">发布后不加入相册</option>
              <option v-for="album in albums" :key="album.id" :value="album.id">
                {{ album.name }}
              </option>
            </select>
            <p class="mt-2 text-xs leading-5 text-[var(--text-muted)]">
              {{ albums.length ? '本次上传的媒体会按当前排序加入相册。' : '还没有可选相册，可以稍后在媒体库整理。' }}
            </p>
          </div>
        </section>

        <RightRail
          title="发布检查"
          description="内容会保存到家庭私有时间线，仅家庭成员可见。"
          :sections="publishChecklist"
        />

        <p v-if="errorMessage" class="ui-feedback ui-feedback-error">
          {{ errorMessage }}
        </p>
        <p v-else-if="statusMessage" class="ui-feedback ui-feedback-success">
          {{ statusMessage }}
        </p>
      </aside>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Loader2, Sparkles } from 'lucide-vue-next'
import { generatePostCaption, type PostCaptionMode } from '@/api/ai'
import { createPost, type MediaItem } from '@/api/posts'
import { getAlbums, type Album } from '@/api/albums'
import { bulkMediaAction, uploadMedia } from '@/api/media'
import AppShell from '@/components/AppShell.vue'
import RightRail from '@/components/RightRail.vue'

const router = useRouter()
const content = ref('')
const publishing = ref(false)
const aiGenerating = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const fileInput = ref<HTMLInputElement>()
const mediaFiles = ref<File[]>([])
const previews = ref<string[]>([])
const uploadedUrls = ref<MediaItem[]>([])
const uploadedMediaIds = ref<string[]>([])
const albums = ref<Album[]>([])
const selectedAlbumId = ref('')
const albumsLoading = ref(false)

const canPublish = computed(() => content.value.trim().length > 0 || mediaFiles.value.length > 0)
const hasTextContent = computed(() => content.value.trim().length > 0)
const canUseCaptionAI = computed(() => hasTextContent.value || mediaFiles.value.length > 0)
const aiCaptionButtonLabel = computed(() => (hasTextContent.value ? '润色文案' : '帮我写文案'))
const isBusy = computed(() => publishing.value || aiGenerating.value)
const publishChecklist = computed(() => [
  {
    title: canPublish.value ? '可以发布' : '还没有内容',
    body: canPublish.value ? '文字或媒体至少有一项。' : '写一句话，或上传一张照片。',
    meta: '状态',
  },
  {
    title: `${mediaFiles.value.length} 个媒体文件`,
    body: '单次最多 9 个，图片和视频可以混合。',
    meta: '媒体',
  },
  {
    title: selectedAlbumId.value
      ? `加入「${albums.value.find((album) => album.id === selectedAlbumId.value)?.name || '相册'}」`
      : '不指定相册',
    body: '发布后仍可在媒体库批量整理。',
    meta: '相册',
  },
])

onMounted(() => {
  loadAlbums()
})

function triggerFileInput() {
  if (isBusy.value) return
  fileInput.value?.click()
}

function onFilesSelected(event: Event) {
  if (isBusy.value) {
    ;(event.target as HTMLInputElement).value = ''
    return
  }
  const files = Array.from((event.target as HTMLInputElement).files || [])
  for (const file of files) {
    if (mediaFiles.value.length >= 9) break
    if (file.size > 10 * 1024 * 1024) {
      errorMessage.value = `${file.name} 超过10MB`
      continue
    }
    mediaFiles.value.push(file)
    previews.value.push(URL.createObjectURL(file))
  }
  ;(event.target as HTMLInputElement).value = ''
}

function removeMedia(index: number) {
  if (isBusy.value) return
  revokePreview(index)
  mediaFiles.value.splice(index, 1)
  previews.value.splice(index, 1)
  uploadedUrls.value.splice(index, 1)
  uploadedMediaIds.value.splice(index, 1)
}

function moveMedia(index: number, direction: -1 | 1) {
  if (isBusy.value) return
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= mediaFiles.value.length) return
  swap(mediaFiles.value, index, targetIndex)
  swap(previews.value, index, targetIndex)
  swap(uploadedUrls.value, index, targetIndex)
  swap(uploadedMediaIds.value, index, targetIndex)
}

function swap<T>(items: T[], from: number, to: number) {
  const item = items[from]
  items[from] = items[to]
  items[to] = item
}

function revokePreview(index: number) {
  const preview = previews.value[index]
  if (preview) URL.revokeObjectURL(preview)
}

function revokeAllPreviews() {
  previews.value.forEach((preview) => URL.revokeObjectURL(preview))
  previews.value = []
}

function resetMediaState() {
  revokeAllPreviews()
  mediaFiles.value = []
  uploadedUrls.value = []
  uploadedMediaIds.value = []
}

async function loadAlbums() {
  if (albumsLoading.value) return
  albumsLoading.value = true
  try {
    const response = await getAlbums()
    albums.value = response.albums
    if (!albums.value.some((album) => album.id === selectedAlbumId.value)) {
      selectedAlbumId.value = ''
    }
  } catch {
    albums.value = []
    selectedAlbumId.value = ''
  } finally {
    albumsLoading.value = false
  }
}

async function handlePublish() {
  if (!canPublish.value || isBusy.value) return
  publishing.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    if (mediaFiles.value.length) {
      const response = await uploadMedia(mediaFiles.value)
      if (response.files) {
        uploadedUrls.value = response.files.map((file) => ({
          type: file.type === 'video' ? 'video' : 'image',
          url: file.raw_url || file.url,
        }))
        uploadedMediaIds.value = response.files.map((file) => file.id)
      }
    }
    await createPost(content.value.trim(), uploadedUrls.value)
    let albumAttachFailed = false
    if (selectedAlbumId.value && uploadedMediaIds.value.length) {
      try {
        await bulkMediaAction({
          action: 'add_to_album',
          album_id: selectedAlbumId.value,
          media_ids: uploadedMediaIds.value,
        })
      } catch {
        albumAttachFailed = true
      }
    }
    if (albumAttachFailed) {
      resetMediaState()
      content.value = ''
      selectedAlbumId.value = ''
      statusMessage.value = '动态已发布，但加入相册失败。可以稍后在媒体库整理。'
      publishing.value = false
      return
    }
    resetMediaState()
    router.push('/')
  } catch (e) {
    errorMessage.value = typeof e === 'string' ? e : '发布失败'
    publishing.value = false
  }
}

async function handleCaptionAI() {
  if (!canUseCaptionAI.value || isBusy.value) return
  const trimmed = content.value.trim()
  const mode: PostCaptionMode = trimmed ? 'polish' : 'generate'

  aiGenerating.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    const response = await generatePostCaption({
      mode,
      content: trimmed || undefined,
      files: mediaFiles.value,
    })
    content.value = response.content
    statusMessage.value = response.mode === 'polish' ? '文案已润色' : '文案已生成'
  } catch (e) {
    errorMessage.value = typeof e === 'string' ? e : 'AI 文案生成失败'
  } finally {
    aiGenerating.value = false
  }
}

function handleCancel() {
  if (isBusy.value) return
  resetMediaState()
  router.back()
}

onBeforeUnmount(() => {
  revokeAllPreviews()
})
</script>

<style scoped>
.soft-button,
.ai-caption-button,
.primary-button,
.editor-panel,
.editor-input,
.media-panel,
.preview-tile,
.preview-tile img,
.preview-tile video,
.upload-dropzone {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    filter 220ms ease,
    opacity 180ms ease,
    transform 180ms ease;
}

.soft-button:hover,
.ai-caption-button:hover:not(:disabled),
.primary-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.primary-button:hover:not(:disabled) {
  box-shadow: 0 10px 26px rgba(201, 67, 47, 0.14);
}

.editor-panel,
.media-panel {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.36), rgba(45, 108, 104, 0.05)),
    var(--surface-card);
}

.editor-panel:focus-within,
.media-panel:hover {
  border-color: rgba(201, 67, 47, 0.16);
  box-shadow: 0 20px 50px rgba(47, 39, 35, 0.1);
}

.editor-input:focus {
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.preview-tile {
  animation: preview-in 220ms ease-out both;
}

.preview-tile:hover img,
.preview-tile:hover video {
  filter: saturate(1.04) contrast(1.02);
  transform: scale(1.03);
}

.upload-dropzone:hover {
  transform: translateY(-1px);
}

@keyframes preview-in {
  from {
    opacity: 0;
    transform: scale(0.97);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .soft-button,
  .ai-caption-button,
  .primary-button,
  .editor-panel,
  .editor-input,
  .media-panel,
  .preview-tile,
  .preview-tile img,
  .preview-tile video,
  .upload-dropzone {
    animation: none;
    transition: none;
  }

  .soft-button:hover,
  .ai-caption-button:hover:not(:disabled),
  .primary-button:hover:not(:disabled),
  .preview-tile:hover img,
  .preview-tile:hover video,
  .upload-dropzone:hover {
    transform: none;
  }
}
</style>
