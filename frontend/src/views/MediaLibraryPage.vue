<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Archive,
  CalendarDays,
  Check,
  FolderPlus,
  Grid3X3,
  Heart,
  Image as ImageIcon,
  LayoutGrid,
  Loader2,
  Plus,
  RotateCcw,
  Search,
  SlidersHorizontal,
  Trash2,
  Video,
  X,
} from 'lucide-vue-next'
import { getAlbums, type Album } from '@/api/albums'
import {
  bulkMediaAction,
  getMediaLibrary,
  restoreMedia,
  toggleMediaFavorite,
  trashMedia,
  type MediaLibraryParams,
  type MediaMonthFacet,
  type MediaSearchItem,
  type MediaSearchUploader,
} from '@/api/media'
import AppShell from '@/components/AppShell.vue'
import MediaLightbox from '@/components/MediaLightbox.vue'
import RightRail from '@/components/RightRail.vue'
import { mediaUrl } from '@/utils/media'

type MediaKind = '' | 'image' | 'video'
type Density = 'comfortable' | 'compact'

const loading = ref(false)
const bulkLoading = ref(false)
const albumsLoading = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const mediaItems = ref<MediaSearchItem[]>([])
const uploaders = ref<MediaSearchUploader[]>([])
const months = ref<MediaMonthFacet[]>([])
const albums = ref<Album[]>([])
const selectedIds = ref<string[]>([])
const page = ref(1)
const total = ref(0)
const hasMore = ref(false)
const trashCount = ref(0)
const favoriteCount = ref(0)
const selectedAlbumId = ref('')
const lightboxIndex = ref<number | null>(null)
const density = ref<Density>('comfortable')

const filters = reactive({
  q: '',
  uploaderId: '',
  type: '' as MediaKind,
  dateFrom: '',
  dateTo: '',
  favoriteOnly: false,
  trashOnly: false,
})

const selectedSet = computed(() => new Set(selectedIds.value))
const hasSelection = computed(() => selectedIds.value.length > 0)
const currentLightboxIndex = computed(() => lightboxIndex.value ?? 0)
const currentAlbum = computed(() => albums.value.find((album) => album.id === selectedAlbumId.value))
const activeFilterCount = computed(() => {
  return [
    filters.q.trim(),
    filters.uploaderId,
    filters.type,
    filters.dateFrom,
    filters.dateTo,
    filters.favoriteOnly,
    filters.trashOnly,
  ].filter(Boolean).length
})
const pageSummary = computed(() => {
  if (loading.value && !mediaItems.value.length) return '正在整理家庭影像'
  if (filters.trashOnly) return `回收站中有 ${total.value} 个媒体`
  if (filters.favoriteOnly) return `你收藏了 ${total.value} 个媒体`
  return `当前显示 ${mediaItems.value.length} / ${total.value} 个媒体`
})
const railSections = computed(() => [
  {
    title: `${total.value} 个结果`,
    body: filters.trashOnly ? '当前回收站视图' : '当前筛选条件下的媒体数量',
    meta: 'Results',
  },
  {
    title: `${favoriteCount.value} 个收藏`,
    body: '收藏按当前登录成员单独保存',
    meta: 'Favorite',
  },
  {
    title: `${trashCount.value} 个回收站媒体`,
    body: '回收站不出现在相册选择和常规媒体库中',
    meta: 'Trash',
  },
])
const groupedMedia = computed(() => {
  const groups = new Map<string, MediaSearchItem[]>()
  for (const item of mediaItems.value) {
    const key = monthKey(item.captured_at || item.created_at)
    const list = groups.get(key) || []
    list.push(item)
    groups.set(key, list)
  }
  return Array.from(groups.entries()).map(([month, items]) => ({ month, items }))
})
const gridClass = computed(() => {
  if (density.value === 'compact') {
    return 'grid-cols-3 gap-2 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6'
  }
  return 'grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
})
const canBulkAddToAlbum = computed(() => hasSelection.value && selectedAlbumId.value && !filters.trashOnly)

onMounted(async () => {
  await Promise.all([loadLibrary(1), loadAlbums()])
})

async function loadLibrary(targetPage = 1) {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  statusMessage.value = ''
  try {
    const params: MediaLibraryParams = {
      q: filters.q.trim() || undefined,
      uploader_id: filters.uploaderId || undefined,
      type: filters.type || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
      favorite_only: filters.favoriteOnly || undefined,
      trash_only: filters.trashOnly || undefined,
      page: targetPage,
      page_size: 48,
    }
    const response = await getMediaLibrary(params)
    page.value = response.page
    total.value = response.total
    hasMore.value = response.has_more
    trashCount.value = response.trash_count
    favoriteCount.value = response.favorite_count
    uploaders.value = response.uploaders
    months.value = response.months
    mediaItems.value = targetPage === 1 ? response.media : [...mediaItems.value, ...response.media]
    selectedIds.value = selectedIds.value.filter((id) =>
      mediaItems.value.some((item) => item.id === id)
    )
    if (lightboxIndex.value !== null && lightboxIndex.value >= mediaItems.value.length) {
      lightboxIndex.value = mediaItems.value.length ? mediaItems.value.length - 1 : null
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '加载媒体库失败')
  } finally {
    loading.value = false
  }
}

async function loadAlbums() {
  if (albumsLoading.value) return
  albumsLoading.value = true
  try {
    const response = await getAlbums()
    albums.value = response.albums
    if (!selectedAlbumId.value || !albums.value.some((album) => album.id === selectedAlbumId.value)) {
      selectedAlbumId.value = albums.value[0]?.id || ''
    }
  } catch {
    albums.value = []
    selectedAlbumId.value = ''
  } finally {
    albumsLoading.value = false
  }
}

function submitFilters() {
  selectedIds.value = []
  lightboxIndex.value = null
  loadLibrary(1)
}

function resetFilters() {
  filters.q = ''
  filters.uploaderId = ''
  filters.type = ''
  filters.dateFrom = ''
  filters.dateTo = ''
  filters.favoriteOnly = false
  filters.trashOnly = false
  submitFilters()
}

function setFavoriteOnly(value: boolean) {
  filters.favoriteOnly = value
  if (value) filters.trashOnly = false
  submitFilters()
}

function setTrashOnly(value: boolean) {
  filters.trashOnly = value
  if (value) filters.favoriteOnly = false
  selectedIds.value = []
  submitFilters()
}

function showAllMedia() {
  filters.favoriteOnly = false
  filters.trashOnly = false
  selectedIds.value = []
  submitFilters()
}

function chooseMonth(month: string) {
  const [year, monthNumber] = month.split('-')
  if (!year || !monthNumber) return
  const lastDay = new Date(Number(year), Number(monthNumber), 0).getDate()
  filters.dateFrom = `${month}-01`
  filters.dateTo = `${month}-${String(lastDay).padStart(2, '0')}`
  submitFilters()
}

function toggleSelected(id: string) {
  selectedIds.value = selectedSet.value.has(id)
    ? selectedIds.value.filter((selectedId) => selectedId !== id)
    : [...selectedIds.value, id]
}

function selectAllLoaded() {
  selectedIds.value = mediaItems.value.map((item) => item.id)
}

function clearSelection() {
  selectedIds.value = []
}

function openLightbox(item: MediaSearchItem) {
  lightboxIndex.value = mediaItems.value.findIndex((media) => media.id === item.id)
}

function closeLightbox() {
  lightboxIndex.value = null
}

function updateMediaItem(id: string, patch: Partial<MediaSearchItem>) {
  mediaItems.value = mediaItems.value.map((item) => (item.id === id ? { ...item, ...patch } : item))
}

function removeMediaItem(id: string) {
  mediaItems.value = mediaItems.value.filter((item) => item.id !== id)
  selectedIds.value = selectedIds.value.filter((selectedId) => selectedId !== id)
  total.value = Math.max(0, total.value - 1)
  if (lightboxIndex.value !== null) {
    if (!mediaItems.value.length) {
      lightboxIndex.value = null
    } else if (lightboxIndex.value >= mediaItems.value.length) {
      lightboxIndex.value = mediaItems.value.length - 1
    }
  }
}

async function handleToggleFavorite(item: MediaSearchItem) {
  if (bulkLoading.value || item.deleted_at) return
  bulkLoading.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    const response = await toggleMediaFavorite(item.id)
    updateMediaItem(item.id, { is_favorite: response.is_favorite })
    favoriteCount.value += response.is_favorite ? 1 : -1
    if (filters.favoriteOnly && !response.is_favorite) {
      removeMediaItem(item.id)
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '收藏操作失败')
  } finally {
    bulkLoading.value = false
  }
}

async function handleTrash(item: MediaSearchItem) {
  if (bulkLoading.value) return
  bulkLoading.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    const response = await trashMedia(item.id)
    if (response.affected) {
      trashCount.value += 1
      if (filters.trashOnly) {
        updateMediaItem(item.id, { deleted_at: new Date().toISOString() })
      } else {
        removeMediaItem(item.id)
      }
      statusMessage.value = '已移入回收站'
    } else {
      statusMessage.value = '没有可移动的媒体'
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '移入回收站失败')
  } finally {
    bulkLoading.value = false
  }
}

async function handleRestore(item: MediaSearchItem) {
  if (bulkLoading.value) return
  bulkLoading.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    const response = await restoreMedia(item.id)
    if (response.affected) {
      trashCount.value = Math.max(0, trashCount.value - 1)
      if (filters.trashOnly) {
        removeMediaItem(item.id)
      } else {
        updateMediaItem(item.id, { deleted_at: null })
      }
      statusMessage.value = '已恢复媒体'
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '恢复媒体失败')
  } finally {
    bulkLoading.value = false
  }
}

async function handleBulkFavorite(favorite: boolean) {
  if (!hasSelection.value || bulkLoading.value) return
  bulkLoading.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    const response = await bulkMediaAction({
      action: favorite ? 'favorite' : 'unfavorite',
      media_ids: selectedIds.value,
    })
    for (const id of selectedIds.value) {
      updateMediaItem(id, { is_favorite: favorite })
    }
    favoriteCount.value = Math.max(0, favoriteCount.value + (favorite ? response.affected : -response.affected))
    if (filters.favoriteOnly && !favorite) {
      mediaItems.value = mediaItems.value.filter((item) => !selectedSet.value.has(item.id))
      total.value = Math.max(0, total.value - response.affected)
    }
    statusMessage.value = `已处理 ${response.affected} 个媒体`
    clearSelection()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '批量收藏失败')
  } finally {
    bulkLoading.value = false
  }
}

async function handleBulkTrashOrRestore() {
  if (!hasSelection.value || bulkLoading.value) return
  bulkLoading.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  const selected = [...selectedIds.value]
  try {
    const action = filters.trashOnly ? 'restore' : 'trash'
    const response = await bulkMediaAction({ action, media_ids: selected })
    if (filters.trashOnly) {
      trashCount.value = Math.max(0, trashCount.value - response.affected)
      mediaItems.value = mediaItems.value.filter((item) => !selected.includes(item.id))
    } else {
      trashCount.value += response.affected
      mediaItems.value = mediaItems.value.filter((item) => !selected.includes(item.id))
    }
    total.value = Math.max(0, total.value - response.affected)
    statusMessage.value = filters.trashOnly ? '已恢复选中媒体' : '已将选中媒体移入回收站'
    clearSelection()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, filters.trashOnly ? '批量恢复失败' : '批量移入回收站失败')
  } finally {
    bulkLoading.value = false
  }
}

async function handleAddToAlbum(item: MediaSearchItem, albumId: string) {
  if (bulkLoading.value || item.deleted_at) return
  bulkLoading.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    const response = await bulkMediaAction({
      action: 'add_to_album',
      album_id: albumId,
      media_ids: [item.id],
    })
    statusMessage.value = response.affected
      ? `已加入「${albumName(albumId)}」`
      : '这个媒体已经在相册中'
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '加入相册失败')
  } finally {
    bulkLoading.value = false
  }
}

async function handleBulkAddToAlbum() {
  if (!canBulkAddToAlbum.value || bulkLoading.value) return
  bulkLoading.value = true
  statusMessage.value = ''
  errorMessage.value = ''
  try {
    const response = await bulkMediaAction({
      action: 'add_to_album',
      album_id: selectedAlbumId.value,
      media_ids: selectedIds.value,
    })
    statusMessage.value = `已加入 ${response.affected} 个媒体到「${currentAlbum.value?.name || '相册'}」`
    clearSelection()
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '批量加入相册失败')
  } finally {
    bulkLoading.value = false
  }
}

function albumName(id: string) {
  return albums.value.find((album) => album.id === id)?.name || '相册'
}

function mediaTitle(item: MediaSearchItem): string {
  return item.caption || item.original_name || (item.type === 'video' ? '家庭视频' : '家庭照片')
}

function uploaderName(item: MediaSearchItem): string {
  return item.uploader.role_in_family || item.uploader.username
}

function monthKey(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '未知月份'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

function formatMonth(value: string): string {
  if (value === '未知月份') return value
  const [year, month] = value.split('-')
  return `${year}年${Number(month)}月`
}

function formatDate(value?: string | null): string {
  if (!value) return '未知时间'
  return new Date(value).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function getErrorMessage(error: unknown, fallback: string) {
  if (typeof error === 'string') return error
  if (error && typeof error === 'object') {
    const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
    const message = (error as { message?: string }).message
    return detail || message || fallback
  }
  return fallback
}
</script>

<template>
  <AppShell page-title="媒体库" page-description="照片和视频的家庭总入口，按月份、上传者、收藏和回收站整理">
    <template #header>
      <div class="library-hero overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
        <div class="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div class="min-w-0">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Family media hub</p>
            <h1 class="mt-2 text-3xl font-semibold leading-tight tracking-normal text-[var(--text)] sm:text-4xl">
              媒体库
            </h1>
            <p class="mt-3 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
              把照片和视频从动态附件里解放出来。筛选、收藏、整理进相册，或从回收站恢复。
            </p>
          </div>

          <div class="grid grid-cols-3 gap-2 sm:w-auto sm:min-w-[22rem]">
            <button
              class="metric-button"
              type="button"
              :class="{ 'is-active': !filters.favoriteOnly && !filters.trashOnly }"
              @click="showAllMedia"
            >
              <span>{{ total }}</span>
              <small>当前结果</small>
            </button>
            <button
              class="metric-button"
              type="button"
              :class="{ 'is-active': filters.favoriteOnly }"
              @click="setFavoriteOnly(!filters.favoriteOnly)"
            >
              <span>{{ favoriteCount }}</span>
              <small>收藏</small>
            </button>
            <button
              class="metric-button"
              type="button"
              :class="{ 'is-active': filters.trashOnly }"
              @click="setTrashOnly(!filters.trashOnly)"
            >
              <span>{{ trashCount }}</span>
              <small>回收站</small>
            </button>
          </div>
        </div>
      </div>
    </template>

    <div class="space-y-5">
      <section class="library-toolbar rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4 shadow-[var(--shadow-panel)]">
        <form class="grid gap-3 xl:grid-cols-[minmax(0,1fr)_11rem_9rem_9rem_9rem_minmax(10rem,auto)]" @submit.prevent="submitFilters">
          <label class="relative min-w-0">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--accent)]" :stroke-width="2" />
            <input
              v-model="filters.q"
              class="library-input h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] pl-9 pr-3 text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-muted)]"
              placeholder="搜索文件名、说明..."
            />
          </label>

          <select v-model="filters.uploaderId" class="library-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none">
            <option value="">全部上传者</option>
            <option v-for="uploader in uploaders" :key="uploader.id" :value="uploader.id">
              {{ uploader.role_in_family || uploader.username }}
            </option>
          </select>

          <select v-model="filters.type" class="library-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none">
            <option value="">全部类型</option>
            <option value="image">照片</option>
            <option value="video">视频</option>
          </select>

          <input v-model="filters.dateFrom" class="library-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none" type="date" aria-label="开始日期" />
          <input v-model="filters.dateTo" class="library-input h-11 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none" type="date" aria-label="结束日期" />

          <div class="grid grid-cols-2 gap-2 xl:flex">
            <button
              class="primary-action inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-4 text-sm font-medium text-[var(--surface)] disabled:opacity-45"
              type="submit"
              :disabled="loading"
            >
              <Loader2 v-if="loading" class="h-4 w-4 animate-spin" :stroke-width="2" />
              <SlidersHorizontal v-else class="h-4 w-4" :stroke-width="2" />
              筛选
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

        <div class="mt-3 flex flex-wrap items-center gap-2">
          <button
            class="filter-chip"
            type="button"
            :class="{ 'is-active': filters.favoriteOnly }"
            @click="setFavoriteOnly(!filters.favoriteOnly)"
          >
            <Heart class="h-3.5 w-3.5" :stroke-width="2" />
            我的收藏
          </button>
          <button
            class="filter-chip"
            type="button"
            :class="{ 'is-active': filters.trashOnly }"
            @click="setTrashOnly(!filters.trashOnly)"
          >
            <Archive class="h-3.5 w-3.5" :stroke-width="2" />
            回收站
          </button>
          <span v-if="activeFilterCount" class="text-xs text-[var(--text-muted)]">
            已启用 {{ activeFilterCount }} 个条件
          </span>
          <span class="ml-auto hidden text-xs text-[var(--text-muted)] sm:inline">
            {{ pageSummary }}
          </span>
        </div>
      </section>

      <section
        v-if="hasSelection"
        class="bulk-bar sticky top-[7.25rem] z-20 rounded-lg border border-[var(--border-focus)] bg-[var(--surface-card)] p-3 shadow-[var(--shadow-panel)]"
      >
        <div class="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div class="flex flex-wrap items-center gap-2 text-sm text-[var(--text-secondary)]">
            <span class="font-medium text-[var(--text)]">已选择 {{ selectedIds.length }} 个</span>
            <button class="text-[var(--accent)] hover:underline" type="button" @click="selectAllLoaded">选择当前页</button>
            <button class="text-[var(--text-muted)] hover:text-[var(--text)]" type="button" @click="clearSelection">取消选择</button>
          </div>

          <div class="grid gap-2 sm:grid-cols-[auto_auto_minmax(10rem,1fr)_auto] xl:min-w-[36rem]">
            <button class="bulk-action" type="button" :disabled="bulkLoading || filters.trashOnly" @click="handleBulkFavorite(true)">
              <Heart class="h-4 w-4" :stroke-width="2" />
              收藏
            </button>
            <button class="bulk-action" type="button" :disabled="bulkLoading || filters.trashOnly" @click="handleBulkFavorite(false)">
              <X class="h-4 w-4" :stroke-width="2" />
              取消收藏
            </button>
            <select
              v-model="selectedAlbumId"
              class="library-input h-10 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none"
              :disabled="filters.trashOnly || albumsLoading || !albums.length"
            >
              <option value="">选择相册</option>
              <option v-for="album in albums" :key="album.id" :value="album.id">{{ album.name }}</option>
            </select>
            <button class="bulk-action" type="button" :disabled="!canBulkAddToAlbum || bulkLoading" @click="handleBulkAddToAlbum">
              <FolderPlus class="h-4 w-4" :stroke-width="2" />
              加入
            </button>
            <button class="bulk-action sm:col-span-4 xl:col-span-1" type="button" :disabled="bulkLoading" @click="handleBulkTrashOrRestore">
              <RotateCcw v-if="filters.trashOnly" class="h-4 w-4" :stroke-width="2" />
              <Trash2 v-else class="h-4 w-4" :stroke-width="2" />
              {{ filters.trashOnly ? '恢复' : '回收站' }}
            </button>
          </div>
        </div>
      </section>

      <p v-if="errorMessage" class="rounded-lg border border-[color:rgb(227_107_93_/_0.24)] bg-[var(--accent-soft)] p-3 text-sm text-[var(--accent)]">
        {{ errorMessage }}
      </p>
      <p v-else-if="statusMessage" class="rounded-lg border border-[color:rgb(45_108_104_/_0.22)] bg-[color:rgb(45_108_104_/_0.08)] p-3 text-sm text-[color:rgb(45_108_104)]">
        {{ statusMessage }}
      </p>

      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="month in months.slice(0, 8)"
            :key="month.month"
            class="month-chip"
            type="button"
            @click="chooseMonth(month.month)"
          >
            <CalendarDays class="h-3.5 w-3.5" :stroke-width="2" />
            {{ formatMonth(month.month) }}
            <span>{{ month.count }}</span>
          </button>
        </div>

        <div class="grid w-full grid-cols-2 gap-2 sm:w-auto">
          <button
            class="view-button"
            type="button"
            :class="{ 'is-active': density === 'comfortable' }"
            @click="density = 'comfortable'"
          >
            <LayoutGrid class="h-4 w-4" :stroke-width="2" />
            舒展
          </button>
          <button
            class="view-button"
            type="button"
            :class="{ 'is-active': density === 'compact' }"
            @click="density = 'compact'"
          >
            <Grid3X3 class="h-4 w-4" :stroke-width="2" />
            紧凑
          </button>
        </div>
      </div>

      <div v-if="loading && !mediaItems.length" class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <div v-for="index in 12" :key="index" class="aspect-square animate-pulse rounded-lg border border-[var(--border)] bg-[var(--surface-panel)]" />
      </div>

      <div v-else-if="groupedMedia.length" class="space-y-7">
        <section v-for="group in groupedMedia" :key="group.month" class="space-y-3">
          <div class="flex items-center gap-3">
            <h2 class="shrink-0 text-sm font-semibold text-[var(--text-secondary)]">{{ formatMonth(group.month) }}</h2>
            <div class="h-px flex-1 bg-[var(--border)]" />
            <span class="text-xs text-[var(--text-muted)]">{{ group.items.length }} 个</span>
          </div>

          <div class="grid" :class="gridClass">
            <article
              v-for="item in group.items"
              :key="item.id"
              class="media-tile group relative overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-card)] shadow-[var(--shadow-panel)]"
              :class="{ 'is-selected': selectedSet.has(item.id), 'is-deleted': item.deleted_at }"
            >
              <button class="block aspect-square w-full text-left" type="button" @click="openLightbox(item)">
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
                  :alt="mediaTitle(item)"
                />
              </button>

              <div class="tile-gradient pointer-events-none absolute inset-x-0 bottom-0 h-24" />

              <button
                class="select-button absolute left-2 top-2"
                type="button"
                :aria-label="selectedSet.has(item.id) ? '取消选择' : '选择媒体'"
                @click="toggleSelected(item.id)"
              >
                <Check v-if="selectedSet.has(item.id)" class="h-3.5 w-3.5" :stroke-width="2.3" />
              </button>

              <span class="type-pill absolute right-2 top-2">
                <Video v-if="item.type === 'video'" class="h-3.5 w-3.5" :stroke-width="2" />
                <ImageIcon v-else class="h-3.5 w-3.5" :stroke-width="2" />
              </span>

              <div class="absolute inset-x-0 bottom-0 min-w-0 p-2.5">
                <p class="truncate text-xs font-medium text-white">{{ mediaTitle(item) }}</p>
                <p class="mt-0.5 truncate text-[11px] text-white/72">
                  {{ uploaderName(item) }} · {{ formatDate(item.captured_at || item.created_at) }}
                </p>
              </div>

              <div class="tile-actions absolute right-2 top-10 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100">
                <button
                  class="tile-action"
                  type="button"
                  :disabled="bulkLoading || Boolean(item.deleted_at)"
                  :aria-label="item.is_favorite ? '取消收藏' : '收藏'"
                  @click="handleToggleFavorite(item)"
                >
                  <Heart class="h-3.5 w-3.5" :class="{ 'fill-current text-[var(--accent)]': item.is_favorite }" :stroke-width="2" />
                </button>
                <button
                  class="tile-action"
                  type="button"
                  :disabled="bulkLoading"
                  :aria-label="item.deleted_at ? '恢复媒体' : '移入回收站'"
                  @click="item.deleted_at ? handleRestore(item) : handleTrash(item)"
                >
                  <RotateCcw v-if="item.deleted_at" class="h-3.5 w-3.5" :stroke-width="2" />
                  <Trash2 v-else class="h-3.5 w-3.5" :stroke-width="2" />
                </button>
              </div>
            </article>
          </div>
        </section>

        <button
          v-if="hasMore"
          class="soft-action mx-auto flex h-11 items-center justify-center rounded-lg border border-[var(--border)] px-5 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] disabled:opacity-45"
          type="button"
          :disabled="loading"
          @click="loadLibrary(page + 1)"
        >
          <Loader2 v-if="loading" class="mr-2 h-4 w-4 animate-spin" :stroke-width="2" />
          {{ loading ? '加载中...' : '加载更多' }}
        </button>
      </div>

      <div v-else class="empty-state rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface-card)] p-10 text-center">
        <p class="text-base font-medium text-[var(--text)]">{{ filters.trashOnly ? '回收站是空的' : '没有找到媒体' }}</p>
        <p class="mt-2 text-sm text-[var(--text-muted)]">
          {{ filters.trashOnly ? '被恢复或未删除的媒体会回到普通媒体库。' : '换个筛选条件，或发布新的家庭照片。' }}
        </p>
        <RouterLink
          v-if="!filters.trashOnly"
          to="/publish"
          class="primary-action mt-5 inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)]"
        >
          <Plus class="h-4 w-4" :stroke-width="2" />
          发布记忆
        </RouterLink>
      </div>
    </div>

    <template #right>
      <RightRail
        title="媒体库状态"
        description="收藏是个人维度，相册和回收站是家庭共享维度。"
        :sections="railSections"
      >
        <template #footer>
          <div class="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3">
            <p class="text-xs font-medium uppercase tracking-[0.12em] text-[var(--text-muted)]">相册快捷加入</p>
            <select
              v-model="selectedAlbumId"
              class="library-input mt-2 h-10 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none"
              :disabled="albumsLoading || !albums.length"
            >
              <option value="">选择相册</option>
              <option v-for="album in albums" :key="album.id" :value="album.id">{{ album.name }}</option>
            </select>
            <p class="mt-2 text-xs leading-5 text-[var(--text-muted)]">
              打开媒体详情后也可以把单张照片加入相册。
            </p>
          </div>
        </template>
      </RightRail>
    </template>

    <MediaLightbox
      v-if="lightboxIndex !== null"
      :items="mediaItems"
      :index="currentLightboxIndex"
      :albums="albums"
      :busy="bulkLoading"
      @close="closeLightbox"
      @select="lightboxIndex = $event"
      @favorite="handleToggleFavorite"
      @trash="handleTrash"
      @restore="handleRestore"
      @add-to-album="handleAddToAlbum"
    />
  </AppShell>
</template>

<style scoped>
.library-hero,
.library-toolbar,
.bulk-bar,
.media-tile,
.empty-state,
.metric-button,
.filter-chip,
.month-chip,
.view-button,
.bulk-action,
.tile-action,
.select-button,
.primary-action,
.soft-action,
.library-input {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    filter 220ms ease,
    opacity 180ms ease,
    transform 180ms ease;
}

.library-hero,
.library-toolbar,
.bulk-bar,
.empty-state {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(45, 108, 104, 0.05)),
    var(--surface-card);
}

.metric-button {
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  display: grid;
  min-height: 4rem;
  padding: 0.75rem;
  text-align: left;
}

.metric-button span {
  color: var(--text);
  font-size: 1.35rem;
  font-weight: 650;
  line-height: 1;
}

.metric-button small {
  color: var(--text-muted);
  font-size: 0.72rem;
  margin-top: 0.35rem;
}

.metric-button:hover,
.metric-button.is-active,
.filter-chip:hover,
.filter-chip.is-active,
.month-chip:hover,
.view-button:hover,
.view-button.is-active,
.bulk-action:hover:not(:disabled) {
  background: var(--surface-elevated);
  border-color: var(--border-focus);
  color: var(--text);
  transform: translateY(-1px);
}

.filter-chip,
.month-chip,
.view-button,
.bulk-action {
  align-items: center;
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  color: var(--text-secondary);
  display: inline-flex;
  gap: 0.4rem;
  min-height: 2.5rem;
  padding: 0 0.75rem;
  white-space: nowrap;
}

.month-chip span {
  color: var(--text-muted);
  font-size: 0.72rem;
}

.bulk-action:disabled {
  opacity: 0.42;
}

.library-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.media-tile {
  animation: media-tile-in 280ms ease-out both;
  min-width: 0;
}

.media-tile:hover {
  border-color: var(--border-focus);
  box-shadow: 0 18px 42px rgba(47, 39, 35, 0.13);
  transform: translateY(-2px);
}

.media-tile img,
.media-tile video {
  transition: filter 240ms ease, transform 240ms ease;
}

.media-tile:hover img,
.media-tile:hover video {
  filter: saturate(1.05) contrast(1.02);
  transform: scale(1.025);
}

.media-tile.is-selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(201, 67, 47, 0.2), 0 18px 42px rgba(47, 39, 35, 0.14);
}

.media-tile.is-deleted {
  filter: saturate(0.8);
}

.tile-gradient {
  background: linear-gradient(180deg, transparent, rgba(31, 24, 22, 0.74));
}

.select-button,
.type-pill,
.tile-action {
  align-items: center;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(49, 38, 33, 0.12);
  border-radius: 0.5rem;
  color: var(--text);
  display: inline-flex;
  height: 1.9rem;
  justify-content: center;
  width: 1.9rem;
}

.select-button {
  background: rgba(255, 255, 255, 0.78);
}

.media-tile.is-selected .select-button {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.type-pill {
  color: var(--text-secondary);
  pointer-events: none;
}

.tile-action:hover:not(:disabled),
.select-button:hover {
  background: white;
  transform: scale(1.04);
}

.tile-action:disabled {
  opacity: 0.38;
}

.primary-action:hover:not(:disabled),
.soft-action:hover:not(:disabled) {
  transform: translateY(-1px);
}

@keyframes media-tile-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (hover: none) {
  .tile-actions {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .library-hero,
  .library-toolbar,
  .bulk-bar,
  .media-tile,
  .empty-state,
  .metric-button,
  .filter-chip,
  .month-chip,
  .view-button,
  .bulk-action,
  .tile-action,
  .select-button,
  .primary-action,
  .soft-action,
  .library-input,
  .media-tile img,
  .media-tile video {
    animation: none;
    transition: none;
  }

  .metric-button:hover,
  .metric-button.is-active,
  .filter-chip:hover,
  .filter-chip.is-active,
  .month-chip:hover,
  .view-button:hover,
  .view-button.is-active,
  .bulk-action:hover:not(:disabled),
  .media-tile:hover,
  .media-tile:hover img,
  .media-tile:hover video,
  .tile-action:hover:not(:disabled),
  .select-button:hover,
  .primary-action:hover:not(:disabled),
  .soft-action:hover:not(:disabled) {
    transform: none;
  }
}
</style>
