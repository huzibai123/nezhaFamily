<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import {
  Image as ImageIcon,
  Loader2,
  PlusCircle,
  Search,
  SlidersHorizontal,
  Video,
  X,
} from 'lucide-vue-next'
import { addMediaToAlbum, getAlbums, type Album } from '@/api/albums'
import {
  searchMedia,
  type MediaSearchItem,
  type MediaSearchUploader,
} from '@/api/media'
import { useAuth } from '@/composables/useAuth'
import { mediaUrl } from '@/utils/media'

const { user } = useAuth()

type MediaKind = '' | 'image' | 'video'

const isOpen = ref(false)
const loading = ref(false)
const albumsLoading = ref(false)
const addingToAlbum = ref(false)
const errorMessage = ref('')
const addMessage = ref('')
const results = ref<MediaSearchItem[]>([])
const uploaders = ref<MediaSearchUploader[]>([])
const albums = ref<Album[]>([])
const selectedMedia = ref<MediaSearchItem | null>(null)
const selectedAlbumId = ref('')
const page = ref(1)
const total = ref(0)
const hasMore = ref(false)

const filters = reactive({
  q: '',
  uploaderId: '',
  type: '' as MediaKind,
  dateFrom: '',
  dateTo: '',
})

const canSearch = computed(() => Boolean(user.value))
const resultSummary = computed(() => {
  if (loading.value && !results.value.length) return '正在搜索家庭媒体库'
  if (!results.value.length) return '输入关键词或选择条件，找到家里的照片和视频'
  return `找到 ${total.value} 个媒体，当前显示 ${results.value.length} 个`
})
const selectedAlbum = computed(() => albums.value.find((album) => album.id === selectedAlbumId.value))

function openPanel() {
  if (!canSearch.value) return
  isOpen.value = true
  if (!results.value.length && !loading.value) {
    loadResults(1)
  }
  loadAlbums()
}

function closePanel() {
  isOpen.value = false
  selectedMedia.value = null
}

async function loadResults(targetPage = 1) {
  if (!canSearch.value || loading.value) return
  loading.value = true
  errorMessage.value = ''
  addMessage.value = ''
  try {
    const response = await searchMedia({
      q: filters.q.trim() || undefined,
      uploader_id: filters.uploaderId || undefined,
      type: filters.type || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      page: targetPage,
      page_size: 24,
    })
    page.value = response.page
    total.value = response.total
    hasMore.value = response.has_more
    results.value = targetPage === 1 ? response.media : [...results.value, ...response.media]
    uploaders.value = (response.uploaders?.length ? response.uploaders : response.media.map((item) => item.uploader))
      .slice()
      .sort((a, b) => a.username.localeCompare(b.username))
  } catch (error) {
    errorMessage.value = typeof error === 'string' ? error : '搜索媒体失败'
  } finally {
    loading.value = false
  }
}

async function loadAlbums() {
  if (albumsLoading.value) return
  albumsLoading.value = true
  try {
    const response = await getAlbums()
    const previousAlbumId = selectedAlbumId.value
    albums.value = response.albums
    selectedAlbumId.value = response.albums.some((album) => album.id === previousAlbumId)
      ? previousAlbumId
      : response.albums[0]?.id || ''
  } catch {
    albums.value = []
    selectedAlbumId.value = ''
  } finally {
    albumsLoading.value = false
  }
}

function submitSearch() {
  selectedMedia.value = null
  loadResults(1)
}

function resetFilters() {
  filters.q = ''
  filters.uploaderId = ''
  filters.type = ''
  filters.dateFrom = ''
  filters.dateTo = ''
  selectedMedia.value = null
  loadResults(1)
}

function openPreview(item: MediaSearchItem) {
  selectedMedia.value = item
  selectedAlbumId.value = selectedAlbumId.value || albums.value[0]?.id || ''
  addMessage.value = ''
  loadAlbums()
}

async function addSelectedToAlbum() {
  if (!selectedMedia.value || !selectedAlbumId.value || addingToAlbum.value) return
  addingToAlbum.value = true
  addMessage.value = ''
  try {
    await addMediaToAlbum(selectedAlbumId.value, selectedMedia.value.id)
    addMessage.value = `已加入「${selectedAlbum.value?.name || '相册'}」`
  } catch (error) {
    addMessage.value = typeof error === 'string' ? error : '加入相册失败'
  } finally {
    addingToAlbum.value = false
  }
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatBytes(value?: number | null): string {
  if (!value) return '未知大小'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = value
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

function uploaderName(item: MediaSearchItem): string {
  return item.uploader.role_in_family || item.uploader.username
}

function mediaTitle(item: MediaSearchItem): string {
  return item.original_name || (item.type === 'video' ? '家庭视频' : '家庭照片')
}
</script>

<template>
  <div v-if="canSearch" class="media-search-root">
    <button
      class="search-trigger flex w-full items-center gap-3 rounded-xl border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-left shadow-[var(--shadow-panel)] hover:border-[var(--border-focus)] sm:px-4"
      type="button"
      @click="openPanel"
    >
      <Search class="h-4 w-4 shrink-0 text-[var(--accent)]" :stroke-width="2" aria-hidden="true" />
      <span class="min-w-0 flex-1 truncate text-sm text-[var(--text-secondary)]">
        搜索家庭照片、视频、上传者或文件名
      </span>
      <span class="hidden rounded-md border border-[var(--border)] px-2 py-1 text-[11px] text-[var(--text-muted)] sm:inline-flex">
        Media
      </span>
    </button>

    <div v-if="isOpen" class="search-overlay fixed inset-0 z-50">
      <button class="absolute inset-0 cursor-default bg-[rgba(75,40,25,0.34)] backdrop-blur-sm" type="button" aria-label="关闭搜索" @click="closePanel" />

      <section class="search-panel absolute inset-x-3 top-3 mx-auto flex max-h-[calc(100dvh-1.5rem)] max-w-6xl flex-col overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--surface-card)] shadow-[0_28px_80px_rgba(75,40,25,0.28)] sm:inset-x-5 sm:top-5 sm:max-h-[calc(100dvh-2.5rem)]">
        <header class="flex items-start justify-between gap-4 border-b border-[var(--border)] px-4 py-4 sm:px-5">
          <div class="min-w-0">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Media search</p>
            <h2 class="mt-1 text-xl font-semibold text-[var(--text)]">家庭媒体库</h2>
            <p class="mt-1 text-sm text-[var(--text-secondary)]">{{ resultSummary }}</p>
          </div>
          <button
            class="grid h-10 w-10 shrink-0 place-items-center rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]"
            type="button"
            aria-label="关闭搜索"
            @click="closePanel"
          >
            <X class="h-4 w-4" :stroke-width="2" aria-hidden="true" />
          </button>
        </header>

        <form class="grid gap-3 border-b border-[var(--border)] p-4 sm:grid-cols-[minmax(0,1fr)_10rem_9rem] sm:p-5 xl:grid-cols-[minmax(0,1fr)_11rem_9rem_9rem_9rem_auto]" @submit.prevent="submitSearch">
          <label class="relative min-w-0">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" :stroke-width="2" aria-hidden="true" />
            <input
              v-model="filters.q"
              class="search-input h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] pl-9 pr-3 text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-muted)]"
              placeholder="文件名关键词"
            />
          </label>

          <select v-model="filters.uploaderId" class="search-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none">
            <option value="">全部上传者</option>
            <option v-for="item in uploaders" :key="item.id" :value="item.id">
              {{ item.role_in_family || item.username }}
            </option>
          </select>

          <select v-model="filters.type" class="search-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none">
            <option value="">全部类型</option>
            <option value="image">图片</option>
            <option value="video">视频</option>
          </select>

          <input v-model="filters.dateFrom" class="search-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none" type="date" aria-label="开始日期" />
          <input v-model="filters.dateTo" class="search-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none" type="date" aria-label="结束日期" />

          <div class="grid grid-cols-2 gap-2 sm:grid-cols-none xl:flex">
            <button
              class="primary-action inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-4 text-sm font-medium text-[var(--surface)] disabled:opacity-55"
              type="submit"
              :disabled="loading"
            >
              <Loader2 v-if="loading" class="h-4 w-4 animate-spin" :stroke-width="2" aria-hidden="true" />
              <SlidersHorizontal v-else class="h-4 w-4" :stroke-width="2" aria-hidden="true" />
              搜索
            </button>
            <button
              class="soft-action h-11 rounded-lg border border-[var(--border)] px-4 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]"
              type="button"
              @click="resetFilters"
            >
              清空
            </button>
          </div>
        </form>

        <div class="grid min-h-0 flex-1 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div class="min-h-0 overflow-y-auto p-4 sm:p-5">
            <p v-if="errorMessage" class="mb-4 rounded-lg border border-[color:rgb(217_77_48_/_0.22)] bg-[var(--accent-soft)] px-3 py-2 text-sm text-[var(--accent)]">
              {{ errorMessage }}
            </p>

            <div v-if="loading && !results.length" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <div v-for="index in 6" :key="index" class="h-48 animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-panel)]" />
            </div>

            <div v-else-if="results.length" class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              <button
                v-for="item in results"
                :key="item.id"
                class="media-result group overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] text-left hover:border-[var(--border-focus)]"
                type="button"
                @click="openPreview(item)"
              >
                <div class="relative aspect-square bg-[color:rgb(132_74_40_/_0.12)]">
                  <video
                    v-if="item.type === 'video'"
                    :src="mediaUrl(item.url)"
                    class="h-full w-full object-cover"
                    muted
                    playsinline
                    preload="metadata"
                  />
                  <img
                    v-else
                    :src="mediaUrl(item.thumbnail_url || item.url)"
                    class="h-full w-full object-cover"
                    loading="lazy"
                    alt=""
                  />
                  <span class="absolute left-2 top-2 inline-flex items-center gap-1 rounded-md bg-[rgba(75,40,25,0.68)] px-2 py-1 text-[11px] text-[var(--text-inverse)]">
                    <Video v-if="item.type === 'video'" class="h-3.5 w-3.5" :stroke-width="2" aria-hidden="true" />
                    <ImageIcon v-else class="h-3.5 w-3.5" :stroke-width="2" aria-hidden="true" />
                    {{ item.type === 'video' ? '视频' : '图片' }}
                  </span>
                </div>
                <div class="space-y-1 p-3">
                  <p class="truncate text-sm font-medium text-[var(--text)]">{{ mediaTitle(item) }}</p>
                  <p class="truncate text-xs text-[var(--text-muted)]">
                    {{ uploaderName(item) }} · {{ formatDate(item.created_at) }}
                  </p>
                </div>
              </button>
            </div>

            <div v-else class="rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface-panel)] p-8 text-center">
              <p class="text-sm font-medium text-[var(--text)]">没有找到媒体</p>
              <p class="mt-2 text-sm text-[var(--text-muted)]">换一个关键词、上传者或日期范围试试。</p>
            </div>

            <button
              v-if="hasMore"
              class="soft-action mx-auto mt-5 flex h-11 items-center justify-center rounded-lg border border-[var(--border)] px-5 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] disabled:opacity-55"
              type="button"
              :disabled="loading"
              @click="loadResults(page + 1)"
            >
              {{ loading ? '加载中...' : '加载更多' }}
            </button>
          </div>

          <aside class="preview-pane min-h-0 border-t border-[var(--border)] bg-[var(--surface-panel)] p-4 lg:border-l lg:border-t-0 lg:p-5">
            <div v-if="selectedMedia" class="flex h-full min-h-0 flex-col">
              <div class="overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-card)]">
                <video
                  v-if="selectedMedia.type === 'video'"
                  :src="mediaUrl(selectedMedia.url)"
                  class="max-h-[34vh] w-full object-contain"
                  controls
                />
                <img
                  v-else
                  :src="mediaUrl(selectedMedia.url)"
                  class="max-h-[34vh] w-full object-contain"
                  alt=""
                />
              </div>

              <div class="mt-4 min-w-0 space-y-3">
                <div>
                  <p class="truncate text-base font-semibold text-[var(--text)]">{{ mediaTitle(selectedMedia) }}</p>
                  <p class="mt-1 text-sm text-[var(--text-secondary)]">
                    {{ uploaderName(selectedMedia) }} · {{ formatDate(selectedMedia.created_at) }}
                  </p>
                </div>

                <dl class="grid grid-cols-2 gap-2 text-xs">
                  <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3">
                    <dt class="text-[var(--text-muted)]">大小</dt>
                    <dd class="mt-1 font-medium text-[var(--text)]">{{ formatBytes(selectedMedia.file_size) }}</dd>
                  </div>
                  <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3">
                    <dt class="text-[var(--text-muted)]">类型</dt>
                    <dd class="mt-1 font-medium text-[var(--text)]">{{ selectedMedia.type === 'video' ? '视频' : '图片' }}</dd>
                  </div>
                  <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3">
                    <dt class="text-[var(--text-muted)]">尺寸</dt>
                    <dd class="mt-1 font-medium text-[var(--text)]">
                      {{ selectedMedia.width && selectedMedia.height ? `${selectedMedia.width}×${selectedMedia.height}` : '未记录' }}
                    </dd>
                  </div>
                  <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3">
                    <dt class="text-[var(--text-muted)]">上传者</dt>
                    <dd class="mt-1 truncate font-medium text-[var(--text)]">{{ uploaderName(selectedMedia) }}</dd>
                  </div>
                </dl>

                <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3">
                  <p class="text-sm font-medium text-[var(--text)]">加入相册</p>
                  <div class="mt-3 grid gap-2">
                    <select
                      v-model="selectedAlbumId"
                      class="search-input h-10 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none"
                      :disabled="albumsLoading || !albums.length"
                    >
                      <option value="">{{ albumsLoading ? '相册加载中' : '选择相册' }}</option>
                      <option v-for="album in albums" :key="album.id" :value="album.id">{{ album.name }}</option>
                    </select>
                    <button
                      class="primary-action inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-3 text-sm font-medium text-[var(--surface)] disabled:opacity-55"
                      type="button"
                      :disabled="!selectedAlbumId || addingToAlbum"
                      @click="addSelectedToAlbum"
                    >
                      <PlusCircle class="h-4 w-4" :stroke-width="2" aria-hidden="true" />
                      {{ addingToAlbum ? '加入中...' : '加入相册' }}
                    </button>
                  </div>
                  <p v-if="!albumsLoading && !albums.length" class="mt-2 text-xs text-[var(--text-muted)]">
                    还没有相册，可以先到相册页创建。
                  </p>
                  <p v-if="addMessage" class="mt-2 text-xs text-[var(--accent)]">{{ addMessage }}</p>
                </div>
              </div>
            </div>

            <div v-else class="grid h-full min-h-[18rem] place-items-center rounded-lg border border-dashed border-[var(--border)] p-6 text-center">
              <div>
                <div class="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                  <ImageIcon class="h-5 w-5" :stroke-width="2" aria-hidden="true" />
                </div>
                <p class="mt-4 text-sm font-medium text-[var(--text)]">选择一个媒体预览</p>
                <p class="mt-2 text-sm leading-6 text-[var(--text-muted)]">预览后可以直接加入家庭相册。</p>
              </div>
            </div>
          </aside>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.search-trigger,
.search-panel,
.search-input,
.primary-action,
.soft-action,
.media-result {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    opacity 180ms ease,
    transform 180ms ease;
}

.search-trigger:hover,
.media-result:hover {
  box-shadow: 0 18px 42px rgba(143, 80, 40, 0.15);
  transform: translateY(-1px);
}

.search-panel {
  animation: search-panel-in 180ms ease-out both;
}

.search-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(217, 77, 48, 0.09);
}

.primary-action:hover:not(:disabled) {
  box-shadow: 0 10px 26px rgba(217, 77, 48, 0.16);
  transform: translateY(-1px);
}

.media-result img,
.media-result video {
  transition: filter 220ms ease, transform 360ms ease;
}

.media-result:hover img,
.media-result:hover video {
  filter: saturate(1.04) contrast(1.02);
  transform: scale(1.025);
}

.preview-pane {
  overflow-y: auto;
}

@keyframes search-panel-in {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (max-width: 1023px) {
  .preview-pane {
    max-height: 44dvh;
  }
}

@media (prefers-reduced-motion: reduce) {
  .search-trigger,
  .search-panel,
  .search-input,
  .primary-action,
  .soft-action,
  .media-result,
  .media-result img,
  .media-result video {
    animation: none;
    transition: none;
  }

  .search-trigger:hover,
  .media-result:hover,
  .primary-action:hover:not(:disabled),
  .media-result:hover img,
  .media-result:hover video {
    transform: none;
  }
}
</style>
