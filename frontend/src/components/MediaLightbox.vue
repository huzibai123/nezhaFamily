<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Download,
  Heart,
  Image as ImageIcon,
  Info,
  Plus,
  RotateCcw,
  Trash2,
  User,
  Video,
  X,
} from 'lucide-vue-next'
import type { Album } from '@/api/albums'
import type { MediaSearchItem } from '@/api/media'
import { mediaUrl } from '@/utils/media'

const props = defineProps<{
  items: MediaSearchItem[]
  index: number
  albums: Album[]
  busy?: boolean
}>()

const emit = defineEmits<{
  close: []
  select: [index: number]
  favorite: [item: MediaSearchItem]
  trash: [item: MediaSearchItem]
  restore: [item: MediaSearchItem]
  addToAlbum: [item: MediaSearchItem, albumId: string]
}>()

const selectedAlbumId = ref('')
const showDetails = ref(true)

const current = computed(() => props.items[props.index])
const canPrev = computed(() => props.index > 0)
const canNext = computed(() => props.index < props.items.length - 1)
const isDeleted = computed(() => Boolean(current.value?.deleted_at))
const displaySource = computed(() => current.value ? mediaUrl(current.value.url) : '')
const previewSource = computed(() => {
  if (!current.value) return ''
  return mediaUrl(current.value.thumbnail_url || current.value.url)
})

watch(
  () => props.albums,
  (albums) => {
    if (!selectedAlbumId.value || !albums.some((album) => album.id === selectedAlbumId.value)) {
      selectedAlbumId.value = albums[0]?.id || ''
    }
  },
  { immediate: true }
)

function close() {
  emit('close')
}

function move(delta: number) {
  const nextIndex = props.index + delta
  if (nextIndex < 0 || nextIndex >= props.items.length) return
  emit('select', nextIndex)
}

function selectIndex(index: number) {
  emit('select', index)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') close()
  if (event.key === 'ArrowLeft') move(-1)
  if (event.key === 'ArrowRight') move(1)
}

function addToAlbum() {
  if (!current.value || !selectedAlbumId.value) return
  emit('addToAlbum', current.value, selectedAlbumId.value)
}

function formatDate(value?: string | null): string {
  if (!value) return '未知时间'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
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

function mediaTitle(item?: MediaSearchItem): string {
  if (!item) return '家庭媒体'
  return item.caption || item.original_name || (item.type === 'video' ? '家庭视频' : '家庭照片')
}

function uploaderName(item?: MediaSearchItem): string {
  if (!item) return '家庭成员'
  return item.uploader.role_in_family || item.uploader.username
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="current"
      class="media-lightbox fixed inset-0 z-[120] grid bg-[rgba(30,24,22,0.88)] text-white"
      role="dialog"
      aria-modal="true"
    >
      <header class="lightbox-bar absolute inset-x-0 top-0 z-20 flex items-center justify-between gap-3 px-3 py-3 sm:px-5">
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold">{{ mediaTitle(current) }}</p>
          <p class="mt-0.5 truncate text-xs text-white/62">
            {{ uploaderName(current) }} · {{ formatDate(current.captured_at || current.created_at) }}
          </p>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <button
            class="icon-action"
            type="button"
            :aria-label="current.is_favorite ? '取消收藏' : '收藏'"
            :disabled="busy || isDeleted"
            @click="emit('favorite', current)"
          >
            <Heart class="h-4 w-4" :class="{ 'fill-current text-[var(--accent)]': current.is_favorite }" :stroke-width="2" />
          </button>
          <a
            class="icon-action"
            :href="displaySource"
            :download="current.original_name || 'family-media'"
            aria-label="下载"
          >
            <Download class="h-4 w-4" :stroke-width="2" />
          </a>
          <button
            class="icon-action lg:hidden"
            type="button"
            aria-label="详情"
            @click="showDetails = !showDetails"
          >
            <Info class="h-4 w-4" :stroke-width="2" />
          </button>
          <button class="icon-action" type="button" aria-label="关闭" @click="close">
            <X class="h-4 w-4" :stroke-width="2" />
          </button>
        </div>
      </header>

      <main class="grid h-dvh min-h-0 grid-rows-[1fr_auto] lg:grid-cols-[minmax(0,1fr)_22rem] lg:grid-rows-1">
        <section class="relative grid min-h-0 place-items-center px-3 pb-24 pt-20 sm:px-8 lg:pb-20">
          <button
            class="nav-arrow left-3 sm:left-5"
            type="button"
            aria-label="上一张"
            :disabled="!canPrev"
            @click="move(-1)"
          >
            <ChevronLeft class="h-5 w-5" :stroke-width="2" />
          </button>

          <div class="media-stage grid max-h-full w-full place-items-center">
            <video
              v-if="current.type === 'video'"
              :src="displaySource"
              class="max-h-[calc(100dvh-9rem)] max-w-full rounded-lg object-contain shadow-[0_30px_90px_rgba(0,0,0,0.32)]"
              controls
              autoplay
            />
            <img
              v-else
              :src="displaySource"
              class="max-h-[calc(100dvh-9rem)] max-w-full rounded-lg object-contain shadow-[0_30px_90px_rgba(0,0,0,0.32)]"
              :alt="mediaTitle(current)"
            />
          </div>

          <button
            class="nav-arrow right-3 sm:right-5"
            type="button"
            aria-label="下一张"
            :disabled="!canNext"
            @click="move(1)"
          >
            <ChevronRight class="h-5 w-5" :stroke-width="2" />
          </button>
        </section>

        <aside
          class="details-pane z-10 min-h-0 overflow-y-auto border-t border-white/12 bg-[rgba(255,255,255,0.08)] p-4 backdrop-blur-xl lg:border-l lg:border-t-0 lg:pt-20"
          :class="showDetails ? 'block' : 'hidden lg:block'"
        >
          <div class="space-y-4">
            <div class="overflow-hidden rounded-lg border border-white/12 bg-white/8">
              <img
                v-if="current.type === 'image'"
                :src="previewSource"
                class="h-40 w-full object-cover"
                alt=""
              />
              <video
                v-else
                :src="displaySource"
                class="h-40 w-full object-cover"
                muted
                playsinline
              />
            </div>

            <div class="space-y-3">
              <h2 class="text-lg font-semibold leading-7">{{ mediaTitle(current) }}</h2>
              <p v-if="current.caption" class="text-sm leading-6 text-white/72">{{ current.caption }}</p>

              <dl class="grid gap-2 text-sm">
                <div class="detail-row">
                  <User class="h-4 w-4 text-white/55" :stroke-width="1.9" />
                  <span>{{ uploaderName(current) }}</span>
                </div>
                <div class="detail-row">
                  <CalendarDays class="h-4 w-4 text-white/55" :stroke-width="1.9" />
                  <span>{{ formatDate(current.captured_at || current.created_at) }}</span>
                </div>
                <div class="detail-row">
                  <Video v-if="current.type === 'video'" class="h-4 w-4 text-white/55" :stroke-width="1.9" />
                  <ImageIcon v-else class="h-4 w-4 text-white/55" :stroke-width="1.9" />
                  <span>{{ current.type === 'video' ? '视频' : '图片' }} · {{ formatBytes(current.file_size) }}</span>
                </div>
              </dl>
            </div>

            <div v-if="!isDeleted" class="rounded-lg border border-white/12 bg-white/8 p-3">
              <label class="text-xs font-medium uppercase tracking-[0.16em] text-white/48" for="lightbox-album">
                加入相册
              </label>
              <div class="mt-2 grid grid-cols-[minmax(0,1fr)_auto] gap-2">
                <select
                  id="lightbox-album"
                  v-model="selectedAlbumId"
                  class="h-10 min-w-0 rounded-lg border border-white/14 bg-[rgba(34,26,23,0.88)] px-3 text-sm text-white outline-none"
                  :disabled="!albums.length || busy"
                >
                  <option value="">选择相册</option>
                  <option v-for="album in albums" :key="album.id" :value="album.id">
                    {{ album.name }}
                  </option>
                </select>
                <button
                  class="icon-action !h-10 !w-10"
                  type="button"
                  :disabled="!selectedAlbumId || busy"
                  aria-label="加入相册"
                  @click="addToAlbum"
                >
                  <Plus class="h-4 w-4" :stroke-width="2" />
                </button>
              </div>
            </div>

            <button
              v-if="isDeleted"
              class="danger-action border-[rgba(92,186,145,0.28)] bg-[rgba(92,186,145,0.16)] text-[rgb(182,244,214)]"
              type="button"
              :disabled="busy"
              @click="emit('restore', current)"
            >
              <RotateCcw class="h-4 w-4" :stroke-width="2" />
              恢复媒体
            </button>
            <button
              v-else
              class="danger-action"
              type="button"
              :disabled="busy"
              @click="emit('trash', current)"
            >
              <Trash2 class="h-4 w-4" :stroke-width="2" />
              移入回收站
            </button>
          </div>
        </aside>
      </main>

      <footer class="thumb-strip absolute inset-x-0 bottom-0 z-20 overflow-x-auto border-t border-white/10 bg-[rgba(30,24,22,0.62)] px-3 py-2 backdrop-blur-xl lg:right-[22rem]">
        <div class="flex gap-2">
          <button
            v-for="(item, itemIndex) in items"
            :key="item.id"
            class="thumb-button relative h-14 w-14 shrink-0 overflow-hidden rounded-md border border-white/12 bg-white/8"
            :class="{ 'is-active': itemIndex === index }"
            type="button"
            @click="selectIndex(itemIndex)"
          >
            <video
              v-if="item.type === 'video'"
              :src="mediaUrl(item.url)"
              class="h-full w-full object-cover"
              muted
            />
            <img v-else :src="mediaUrl(item.thumbnail_url || item.url)" class="h-full w-full object-cover" alt="" />
          </button>
        </div>
      </footer>
    </div>
  </Teleport>
</template>

<style scoped>
.media-lightbox {
  animation: lightbox-in 160ms ease-out both;
}

.lightbox-bar {
  background: linear-gradient(180deg, rgba(30, 24, 22, 0.72), rgba(30, 24, 22, 0));
}

.media-stage {
  isolation: isolate;
  position: relative;
}

.media-stage::before {
  background:
    linear-gradient(45deg, rgba(255, 255, 255, 0.035) 25%, transparent 25%),
    linear-gradient(-45deg, rgba(255, 255, 255, 0.035) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, rgba(255, 255, 255, 0.035) 75%),
    linear-gradient(-45deg, transparent 75%, rgba(255, 255, 255, 0.035) 75%),
    rgba(18, 14, 13, 0.78);
  background-position:
    0 0,
    0 0.75rem,
    0.75rem -0.75rem,
    -0.75rem 0;
  background-size: 1.5rem 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.22), 0 30px 90px rgba(0, 0, 0, 0.2);
  content: '';
  inset: clamp(0rem, 2vw, 2rem);
  opacity: 0.9;
  position: absolute;
  z-index: 0;
}

.media-stage > img,
.media-stage > video {
  position: relative;
  z-index: 1;
}

.icon-action,
.nav-arrow,
.danger-action,
.thumb-button {
  transition:
    background-color 170ms ease,
    border-color 170ms ease,
    color 170ms ease,
    opacity 170ms ease,
    transform 170ms ease;
}

.icon-action {
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
  display: inline-flex;
  height: 2.25rem;
  justify-content: center;
  width: 2.25rem;
}

.icon-action:hover:not(:disabled),
.nav-arrow:hover:not(:disabled),
.danger-action:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.18);
  transform: translateY(-1px);
}

.icon-action:disabled,
.nav-arrow:disabled,
.danger-action:disabled {
  opacity: 0.38;
}

.nav-arrow {
  align-items: center;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  color: white;
  display: inline-flex;
  height: 2.75rem;
  justify-content: center;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 2.75rem;
  z-index: 12;
}

.nav-arrow:hover:not(:disabled) {
  transform: translateY(-50%) scale(1.03);
}

.detail-row {
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  display: flex;
  gap: 0.625rem;
  min-height: 2.625rem;
  padding: 0.625rem 0.75rem;
}

.danger-action {
  align-items: center;
  background: rgba(201, 67, 47, 0.18);
  border: 1px solid rgba(255, 126, 104, 0.28);
  border-radius: 0.5rem;
  color: rgb(255, 206, 197);
  display: inline-flex;
  gap: 0.5rem;
  height: 2.75rem;
  justify-content: center;
  width: 100%;
}

.thumb-button.is-active {
  border-color: rgba(255, 255, 255, 0.82);
  box-shadow: 0 0 0 2px rgba(201, 67, 47, 0.58);
}

@keyframes lightbox-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .media-lightbox,
  .icon-action,
  .nav-arrow,
  .danger-action,
  .thumb-button {
    animation: none;
    transition: none;
  }

  .icon-action:hover:not(:disabled),
  .nav-arrow:hover:not(:disabled),
  .danger-action:hover:not(:disabled),
  .nav-arrow:hover:not(:disabled) {
    transform: none;
  }
}
</style>
