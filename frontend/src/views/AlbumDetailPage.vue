<template>
  <AppShell :page-title="album?.name || '相册详情'" :page-description="album?.description || '查看这个相册里的家庭影像'">
    <template #header>
      <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <button
          @click="$router.push('/albums')"
          class="soft-button inline-flex rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
          type="button"
        >
          返回相册
        </button>
        <button
          @click="toggleMediaPicker"
          :disabled="!album"
          class="soft-button inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-4 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-30"
          type="button"
        >
          <Plus class="h-4 w-4" :stroke-width="2" />
          {{ showMediaPicker ? '收起添加' : '添加媒体' }}
        </button>
      </div>
    </template>

    <div v-if="error" class="rounded-lg border border-[color:rgb(227_107_93_/_0.24)] bg-[var(--accent-soft)] p-4 text-sm text-[var(--accent)]">
      {{ error }}
    </div>

    <div v-else-if="album">
      <div
        v-if="mediaError && !showMediaPicker"
        class="mb-4 rounded-lg border border-[color:rgb(227_107_93_/_0.24)] bg-[var(--accent-soft)] p-4 text-sm text-[var(--accent)]"
      >
        {{ mediaError }}
      </div>
      <div
        v-else-if="statusMessage && !showMediaPicker"
        class="mb-4 rounded-lg border border-[color:rgb(45_108_104_/_0.22)] bg-[color:rgb(45_108_104_/_0.08)] p-4 text-sm text-[color:rgb(45_108_104)]"
      >
        {{ statusMessage }}
      </div>

      <section
        v-if="showMediaPicker"
        class="media-manager mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)]"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 class="text-base font-semibold text-[var(--text)]">添加媒体到相册</h2>
            <p class="mt-1 text-sm text-[var(--text-muted)]">
              {{ availableMedia.length ? `${availableMedia.length} 个可添加媒体` : '没有可添加媒体' }}
            </p>
          </div>
          <button
            @click="loadCandidateMedia"
            :disabled="mediaLoading"
            class="soft-button inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-40"
            type="button"
          >
            <RefreshCw class="h-4 w-4" :class="{ 'animate-spin': mediaLoading }" :stroke-width="1.9" />
            {{ mediaLoading ? '刷新中' : '刷新' }}
          </button>
        </div>

        <div
          v-if="mediaError"
          class="mt-4 rounded-lg border border-[color:rgb(227_107_93_/_0.24)] bg-[var(--accent-soft)] p-3 text-sm text-[var(--accent)]"
        >
          {{ mediaError }}
        </div>

        <div v-else-if="mediaLoading" class="mt-4 rounded-lg border border-dashed border-[var(--border)] p-6 text-center text-sm text-[var(--text-muted)]">
          加载媒体...
        </div>

        <div v-else-if="availableMedia.length" class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4">
          <button
            v-for="media in availableMedia"
            :key="media.id"
            @click="handleAddMedia(media.id)"
            :disabled="isMutatingMedia"
            class="candidate-card group relative aspect-square overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)] text-left disabled:opacity-55"
            type="button"
          >
            <video
              v-if="media.type === 'video'"
              :src="mediaUrl(media.url)"
              class="h-full w-full object-cover"
              muted
              preload="metadata"
            />
            <img v-else :src="mediaUrl(media.url)" class="h-full w-full object-cover" loading="lazy" alt="" />
            <span class="candidate-action absolute right-2 top-2 inline-flex items-center gap-1.5 rounded-lg bg-[color:rgb(75_40_25_/_0.68)] px-2 py-1 text-xs font-medium text-[var(--text-inverse)]">
              <Plus class="h-3.5 w-3.5" :stroke-width="2" />
              {{ processingMediaId === media.id ? '添加中' : '添加' }}
            </span>
          </button>
        </div>

        <div v-else class="mt-4 rounded-lg border border-dashed border-[var(--border)] p-6 text-center text-sm text-[var(--text-muted)]">
          当前没有可添加媒体。
        </div>
      </section>

      <section
        v-if="selectedMediaIds.length"
        class="bulk-bar mb-4 rounded-lg border border-[var(--border-focus)] bg-[var(--surface-card)] p-3 shadow-[var(--shadow-panel)]"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="text-sm text-[var(--text-secondary)]">
            <span class="font-medium text-[var(--text)]">已选择 {{ selectedMediaIds.length }} 个媒体</span>
            <button class="ml-3 text-[var(--text-muted)] hover:text-[var(--text)]" type="button" @click="clearSelection">
              取消选择
            </button>
          </div>
          <div class="grid grid-cols-2 gap-2 sm:flex">
            <button
              class="soft-button inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-3 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] disabled:opacity-40"
              type="button"
              :disabled="selectedMediaIds.length !== 1 || isMutatingMedia"
              @click="handleSetCover(selectedAlbumMedia[0])"
            >
              <ImageIcon class="h-4 w-4" :stroke-width="1.9" />
              设为封面
            </button>
            <button
              class="soft-button inline-flex h-10 items-center justify-center gap-2 rounded-lg border border-[color:rgb(227_107_93_/_0.24)] px-3 text-sm text-[var(--accent)] hover:bg-[var(--accent-soft)] disabled:opacity-40"
              type="button"
              :disabled="isMutatingMedia"
              @click="handleBulkRemove"
            >
              <Trash2 class="h-4 w-4" :stroke-width="1.9" />
              批量移除
            </button>
          </div>
        </div>
      </section>

      <div v-if="albumMedia.length" class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p class="text-sm text-[var(--text-muted)]">按加入时间倒序显示。</p>
        <div class="grid grid-cols-2 gap-2 sm:w-auto">
          <button
            class="view-button"
            type="button"
            :class="{ 'is-active': density === 'comfortable' }"
            @click="density = 'comfortable'"
          >
            <LayoutGrid class="h-4 w-4" :stroke-width="1.9" />
            舒展
          </button>
          <button
            class="view-button"
            type="button"
            :class="{ 'is-active': density === 'compact' }"
            @click="density = 'compact'"
          >
            <Grid3X3 class="h-4 w-4" :stroke-width="1.9" />
            紧凑
          </button>
        </div>
      </div>

      <div v-if="albumMedia.length" class="grid" :class="albumGridClass">
        <article
          v-for="media in albumMedia"
          :key="media.id"
          class="photo-card relative overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-card)]"
          :class="{ 'is-selected': selectedMediaSet.has(media.id) }"
        >
          <div class="aspect-square bg-[color:rgb(132_74_40_/_0.12)]">
            <video
              v-if="media.type === 'video'"
              :src="mediaUrl(media.url)"
              class="h-full w-full object-cover"
              controls
              preload="metadata"
            />
            <img v-else :src="mediaUrl(media.url)" class="h-full w-full object-cover" loading="lazy" alt="" />
          </div>
          <button
            @click="toggleMediaSelection(media.id)"
            class="select-button absolute left-2 top-2"
            type="button"
            :aria-label="selectedMediaSet.has(media.id) ? '取消选择' : '选择媒体'"
          >
            <Check v-if="selectedMediaSet.has(media.id)" class="h-3.5 w-3.5" :stroke-width="2.2" />
          </button>
          <button
            @click="handleRemoveMedia(media.id)"
            :disabled="isMutatingMedia"
            class="media-card-action absolute right-2 top-2 inline-flex items-center gap-1.5 rounded-lg bg-[color:rgb(75_40_25_/_0.68)] px-2.5 py-1.5 text-xs font-medium text-[var(--text-inverse)] disabled:opacity-55"
            type="button"
            aria-label="从相册移除"
          >
            <Trash2 class="h-3.5 w-3.5" :stroke-width="1.9" />
            <span class="hidden sm:inline">{{ processingMediaId === media.id ? '移除中' : '移除' }}</span>
          </button>
          <button
            @click="handleSetCover(media)"
            :disabled="isMutatingMedia"
            class="media-card-action absolute bottom-2 right-2 inline-flex items-center gap-1.5 rounded-lg bg-[color:rgb(75_40_25_/_0.68)] px-2.5 py-1.5 text-xs font-medium text-[var(--text-inverse)] disabled:opacity-55"
            type="button"
          >
            <ImageIcon class="h-3.5 w-3.5" :stroke-width="1.9" />
            <span class="hidden sm:inline">封面</span>
          </button>
        </article>
      </div>

      <div v-else class="rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface-card)] p-10 text-center">
        <p class="text-base text-[var(--text-muted)]">这个相册还没有照片。</p>
      </div>
    </div>

    <div v-else class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-8 text-center text-sm text-[var(--text-muted)]">
      加载中...
    </div>

    <template #right>
      <RightRail
        title="相册信息"
        :description="album?.description || '还没有描述。'"
        :sections="albumSections"
      />
    </template>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Check, Grid3X3, Image as ImageIcon, LayoutGrid, Plus, RefreshCw, Trash2 } from 'lucide-vue-next'
import {
  addMediaToAlbum,
  getAlbumDetail,
  removeMediaFromAlbum,
  updateAlbum,
  type AlbumDetail,
  type AlbumMediaItem,
} from '@/api/albums'
import { getMediaLibrary, type MediaSearchItem } from '@/api/media'
import AppShell from '@/components/AppShell.vue'
import RightRail from '@/components/RightRail.vue'
import { mediaUrl } from '@/utils/media'

const route = useRoute()
const albumId = computed(() => String(route.params.id))
const album = ref<AlbumDetail | null>(null)
const userMedia = ref<MediaSearchItem[]>([])
const error = ref('')
const mediaError = ref('')
const statusMessage = ref('')
const mediaLoading = ref(false)
const processingMediaId = ref('')
const showMediaPicker = ref(false)
const selectedMediaIds = ref<string[]>([])
const density = ref<'comfortable' | 'compact'>('comfortable')
const albumMedia = computed(() => album.value?.media ?? [])
const albumMediaIds = computed(() => new Set(albumMedia.value.map((media) => media.id)))
const availableMedia = computed(() =>
  userMedia.value.filter((media) => !albumMediaIds.value.has(media.id))
)
const selectedMediaSet = computed(() => new Set(selectedMediaIds.value))
const selectedAlbumMedia = computed(() =>
  albumMedia.value.filter((media) => selectedMediaSet.value.has(media.id))
)
const isMutatingMedia = computed(() => processingMediaId.value !== '')
const albumGridClass = computed(() =>
  density.value === 'compact'
    ? 'grid-cols-3 gap-2 sm:grid-cols-4 xl:grid-cols-5'
    : 'grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-4'
)
const albumSections = computed(() => [
  { title: `${albumMedia.value.length} 个媒体`, body: '当前相册收录数量', meta: 'Media' },
  { title: album.value?.name || '相册', body: '相册名称', meta: 'Name' },
])

onMounted(async () => {
  await loadAlbum()
})

async function loadAlbum() {
  try {
    album.value = await getAlbumDetail(albumId.value)
    selectedMediaIds.value = selectedMediaIds.value.filter((id) =>
      album.value?.media.some((media) => media.id === id)
    )
  } catch (e) {
    error.value = getErrorMessage(e, '加载相册失败')
  }
}

async function toggleMediaPicker() {
  showMediaPicker.value = !showMediaPicker.value
  mediaError.value = ''
  statusMessage.value = ''
  if (showMediaPicker.value && userMedia.value.length === 0) {
    await loadCandidateMedia()
  }
}

async function loadCandidateMedia() {
  if (mediaLoading.value) return
  mediaLoading.value = true
  mediaError.value = ''
  statusMessage.value = ''
  try {
    const response = await getMediaLibrary({ page_size: 100 })
    userMedia.value = response.media
  } catch (e) {
    mediaError.value = getErrorMessage(e, '加载媒体列表失败')
  } finally {
    mediaLoading.value = false
  }
}

async function handleAddMedia(mediaId: string) {
  if (processingMediaId.value) return
  processingMediaId.value = mediaId
  mediaError.value = ''
  statusMessage.value = ''
  try {
    await addMediaToAlbum(albumId.value, mediaId)
    await loadAlbum()
    userMedia.value = userMedia.value.filter((media) => media.id !== mediaId)
    statusMessage.value = '已添加到相册'
  } catch (e) {
    mediaError.value = getErrorMessage(e, '添加媒体失败')
  } finally {
    processingMediaId.value = ''
  }
}

async function handleRemoveMedia(mediaId: string) {
  if (processingMediaId.value) return
  processingMediaId.value = mediaId
  mediaError.value = ''
  statusMessage.value = ''
  try {
    await removeMediaFromAlbum(albumId.value, mediaId)
    selectedMediaIds.value = selectedMediaIds.value.filter((id) => id !== mediaId)
    await loadAlbum()
    statusMessage.value = '已从相册移除'
  } catch (e) {
    mediaError.value = getErrorMessage(e, '移除媒体失败')
  } finally {
    processingMediaId.value = ''
  }
}

function toggleMediaSelection(mediaId: string) {
  selectedMediaIds.value = selectedMediaSet.value.has(mediaId)
    ? selectedMediaIds.value.filter((id) => id !== mediaId)
    : [...selectedMediaIds.value, mediaId]
}

function clearSelection() {
  selectedMediaIds.value = []
}

async function handleBulkRemove() {
  if (!selectedMediaIds.value.length || processingMediaId.value) return
  processingMediaId.value = '__bulk__'
  mediaError.value = ''
  statusMessage.value = ''
  const ids = [...selectedMediaIds.value]
  try {
    await Promise.all(ids.map((mediaId) => removeMediaFromAlbum(albumId.value, mediaId)))
    clearSelection()
    await loadAlbum()
    statusMessage.value = '已批量移除选中媒体'
  } catch (e) {
    mediaError.value = getErrorMessage(e, '批量移除失败')
  } finally {
    processingMediaId.value = ''
  }
}

async function handleSetCover(media?: AlbumMediaItem) {
  if (!media || processingMediaId.value) return
  processingMediaId.value = media.id
  mediaError.value = ''
  statusMessage.value = ''
  try {
    const updatedAlbum = await updateAlbum(albumId.value, { cover_image_url: media.url })
    if (album.value) {
      album.value.cover_image_url = updatedAlbum.cover_image_url
    }
    statusMessage.value = '已更新相册封面'
  } catch (e) {
    mediaError.value = getErrorMessage(e, '设置封面失败')
  } finally {
    processingMediaId.value = ''
  }
}

function getErrorMessage(errorValue: unknown, fallback: string) {
  if (typeof errorValue === 'string') return errorValue
  if (errorValue && typeof errorValue === 'object') {
    const detail = (errorValue as { response?: { data?: { detail?: string } } }).response?.data?.detail
    const message = (errorValue as { message?: string }).message
    return detail || message || fallback
  }
  return fallback
}
</script>

<style scoped>
.soft-button,
.candidate-card,
.candidate-card img,
.candidate-card video,
.media-card-action,
.media-manager,
.photo-card,
.photo-card img,
.photo-card video {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    filter 240ms ease,
    transform 180ms ease;
}

.soft-button:hover:not(:disabled),
.media-card-action:hover:not(:disabled) {
  transform: translateY(-1px);
}

.candidate-card,
.photo-card {
  animation: photo-card-in 320ms ease-out both;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 238, 211, 0.08)),
    var(--surface-card);
}

.media-manager:hover,
.candidate-card:hover:not(:disabled),
.photo-card:hover {
  border-color: rgba(217, 77, 48, 0.18);
  box-shadow: 0 18px 44px rgba(143, 80, 40, 0.14);
  transform: translateY(-2px);
}

.candidate-card:hover:not(:disabled) img,
.candidate-card:hover:not(:disabled) video,
.photo-card:hover img,
.photo-card:hover video {
  filter: saturate(1.04) contrast(1.02);
}

@keyframes photo-card-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .soft-button,
  .candidate-card,
  .candidate-card img,
  .candidate-card video,
  .media-card-action,
  .media-manager,
  .photo-card,
  .photo-card img,
  .photo-card video {
    animation: none;
    transition: none;
  }

  .soft-button:hover,
  .candidate-card:hover,
  .media-card-action:hover,
  .media-manager:hover,
  .photo-card:hover {
    transform: none;
  }
}
</style>
