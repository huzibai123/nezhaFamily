<template>
  <AppShell page-title="家庭相册" page-description="按主题整理照片和视频，让时间线里的记忆有归处">
    <template #header>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Albums</p>
          <h1 class="mt-2 text-2xl font-semibold tracking-normal text-[var(--text)] sm:text-3xl">家庭相册</h1>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
            用相册保存阶段性回忆，比如成长记录、旅行、节日和日常照片集合。
          </p>
        </div>
        <button
          @click="showCreate = true"
          class="album-action inline-flex rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)] active:scale-[0.98]"
          type="button"
        >
          创建相册
        </button>
      </div>
    </template>

    <div v-if="error" class="rounded-lg border border-[color:rgb(227_107_93_/_0.24)] bg-[var(--accent-soft)] p-4 text-sm text-[var(--accent)]">
      {{ error }}
    </div>

    <div v-else-if="albums.length" class="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
      <router-link
        v-for="album in albums"
        :key="album.id"
        :to="`/albums/${album.id}`"
        class="album-card group overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-card)] shadow-[var(--shadow-panel)] hover:border-[var(--border-focus)]"
      >
        <div class="album-cover aspect-square bg-[color:rgb(132_74_40_/_0.12)]">
          <img
            v-if="album.cover_image_url"
            :src="mediaUrl(album.cover_image_url)"
            class="h-full w-full object-cover"
            alt=""
          />
          <div v-else class="grid h-full place-items-center text-sm text-[var(--text-muted)]">等待照片</div>
        </div>
        <div class="p-4">
          <h3 class="truncate text-base font-medium text-[var(--text)]">{{ album.name }}</h3>
          <p v-if="album.description" class="mt-1 line-clamp-2 text-sm leading-6 text-[var(--text-muted)]">
            {{ album.description }}
          </p>
        </div>
      </router-link>
    </div>

    <div v-else class="rounded-lg border border-dashed border-[var(--border)] bg-[var(--surface-card)] p-10 text-center">
      <p class="text-base text-[var(--text-muted)]">还没有相册</p>
      <button
        @click="showCreate = true"
        class="album-action mt-5 rounded-lg bg-[var(--text)] px-5 py-2.5 text-sm font-medium text-[var(--surface)]"
        type="button"
      >
        创建第一个
      </button>
    </div>

    <template #right>
      <RightRail
        title="相册整理建议"
        :sections="railSections"
      />
    </template>

    <div
      v-if="showCreate"
      @click="showCreate = false"
      class="fixed inset-0 z-50 flex items-center justify-center px-4"
      style="background:rgba(75,40,25,0.38);backdrop-filter:blur(6px)"
    >
      <div @click.stop class="modal-panel w-full max-w-md space-y-4 rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-6 shadow-[var(--shadow-panel)]">
        <h2 class="text-xl font-semibold text-[var(--text)]">创建相册</h2>
        <input
          v-model="newAlbum.name"
          placeholder="相册名称"
          class="album-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)] outline-none"
        />
        <textarea
          v-model="newAlbum.description"
          placeholder="描述（可选）"
          rows="3"
          class="album-input w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)] outline-none"
        />
        <div class="flex gap-3">
          <button @click="showCreate = false" class="flex-1 rounded-lg py-3 text-sm text-[var(--text-muted)]" type="button">
            取消
          </button>
          <button
            @click="handleCreate"
            :disabled="!newAlbum.name.trim()"
            class="album-action flex-1 rounded-lg bg-[var(--text)] py-3 text-sm font-medium text-[var(--surface)] disabled:opacity-30"
            type="button"
          >
            创建
          </button>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { createAlbum, getAlbums, type Album } from '@/api/albums'
import AppShell from '@/components/AppShell.vue'
import RightRail from '@/components/RightRail.vue'
import { mediaUrl } from '@/utils/media'

const albums = ref<Album[]>([])
const showCreate = ref(false)
const error = ref('')
const newAlbum = reactive({ name: '', description: '' })
const railSections = [
  { title: '按主题整理', body: '生日、旅行、节日、成长记录都适合单独建相册。', meta: 'Theme' },
  { title: '保留描述', body: '相册描述可以写下这组照片的背景。', meta: 'Context' },
  { title: '从时间线补充', body: '发布动态后，可以继续把媒体加入相册。', meta: 'Memory' },
]

onMounted(async () => {
  try {
    const response = await getAlbums()
    albums.value = response.albums
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '加载相册失败'
  }
})

async function handleCreate() {
  if (!newAlbum.name.trim()) return
  try {
    await createAlbum({ name: newAlbum.name.trim(), description: newAlbum.description.trim() || undefined })
    const response = await getAlbums()
    albums.value = response.albums
    showCreate.value = false
    newAlbum.name = ''
    newAlbum.description = ''
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '创建相册失败'
  }
}
</script>

<style scoped>
.album-action,
.album-card,
.album-cover img,
.album-input,
.modal-panel {
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    filter 240ms ease,
    opacity 180ms ease,
    transform 180ms ease;
}

.album-action:hover:not(:disabled) {
  box-shadow: 0 10px 26px rgba(217, 77, 48, 0.16);
  transform: translateY(-1px);
}

.album-card {
  animation: album-card-in 360ms ease-out both;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 238, 211, 0.08)),
    var(--surface-card);
}

.album-card:hover {
  box-shadow: 0 22px 54px rgba(143, 80, 40, 0.16);
  transform: translateY(-2px);
}

.album-cover {
  overflow: hidden;
  position: relative;
}

.album-cover::after {
  background: linear-gradient(180deg, rgba(255, 248, 235, 0.18), rgba(255, 248, 235, 0) 36%);
  content: '';
  inset: 0;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  transition: opacity 220ms ease;
}

.album-card:hover .album-cover::after {
  opacity: 1;
}

.album-card:hover .album-cover img {
  filter: saturate(1.04) contrast(1.02);
  transform: scale(1.025);
}

.album-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(227, 107, 93, 0.09);
}

.modal-panel {
  animation: modal-in 180ms ease-out both;
}

@keyframes album-card-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .album-action,
  .album-card,
  .album-cover::after,
  .album-cover img,
  .album-input,
  .modal-panel {
    animation: none;
    transition: none;
  }

  .album-action:hover:not(:disabled),
  .album-card:hover,
  .album-card:hover .album-cover img {
    transform: none;
  }
}
</style>
