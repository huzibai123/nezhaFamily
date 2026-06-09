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

      <div v-if="albumMedia.length" class="columns-1 gap-4 sm:columns-2 xl:columns-3">
        <div
          v-for="media in albumMedia"
          :key="media.id"
          class="photo-card relative mb-4 break-inside-avoid overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-card)]"
        >
          <video
            v-if="media.type === 'video'"
            :src="mediaUrl(media.url)"
            class="w-full"
            controls
            preload="metadata"
          />
          <img v-else :src="mediaUrl(media.url)" class="w-full" loading="lazy" alt="" />
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
        </div>
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
import { Plus, RefreshCw, Trash2 } from 'lucide-vue-next'
import {
  addMediaToAlbum,
  getAlbumDetail,
  removeMediaFromAlbum,
  type AlbumDetail,
} from '@/api/albums'
import { getUserMedia, type UserMediaItem } from '@/api/media'
import AppShell from '@/components/AppShell.vue'
import RightRail from '@/components/RightRail.vue'
import { mediaUrl } from '@/utils/media'

const route = useRoute()
const albumId = computed(() => String(route.params.id))
const album = ref<AlbumDetail | null>(null)
const userMedia = ref<UserMediaItem[]>([])
const error = ref('')
const mediaError = ref('')
const mediaLoading = ref(false)
const processingMediaId = ref('')
const showMediaPicker = ref(false)
const albumMedia = computed(() => album.value?.media ?? [])
const albumMediaIds = computed(() => new Set(albumMedia.value.map((media) => media.id)))
const availableMedia = computed(() =>
  userMedia.value.filter((media) => !albumMediaIds.value.has(media.id))
)
const isMutatingMedia = computed(() => processingMediaId.value !== '')
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
  } catch (e) {
    error.value = getErrorMessage(e, '加载相册失败')
  }
}

async function toggleMediaPicker() {
  showMediaPicker.value = !showMediaPicker.value
  mediaError.value = ''
  if (showMediaPicker.value && userMedia.value.length === 0) {
    await loadCandidateMedia()
  }
}

async function loadCandidateMedia() {
  if (mediaLoading.value) return
  mediaLoading.value = true
  mediaError.value = ''
  try {
    const response = await getUserMedia({ limit: 100 })
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
  try {
    await addMediaToAlbum(albumId.value, mediaId)
    await loadAlbum()
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
  try {
    await removeMediaFromAlbum(albumId.value, mediaId)
    await loadAlbum()
  } catch (e) {
    mediaError.value = getErrorMessage(e, '移除媒体失败')
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
