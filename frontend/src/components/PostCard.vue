<template>
  <article
    @click="$emit('click', post.id)"
    class="post-card enter group cursor-pointer overflow-hidden rounded-xl border"
    style="background:var(--surface-card);border-color:var(--border)"
  >
    <div class="flex items-start gap-3 px-4 pt-4 sm:px-5 sm:pt-5">
      <router-link
        :to="`/profile/${post.author_id}`"
        @click.stop
        class="author-avatar flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-semibold transition-opacity hover:opacity-85"
        style="background:rgba(217,77,48,0.1);color:var(--text-secondary)"
      >
        {{ initial }}
      </router-link>
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
          <router-link
            :to="`/profile/${post.author_id}`"
            @click.stop
            class="text-sm font-semibold hover:opacity-80"
            style="color:var(--text)"
          >
            {{ post.author_username }}
          </router-link>
          <span
            class="rounded-md px-2 py-0.5 text-[11px]"
            style="background:var(--accent-soft);color:var(--accent)"
          >
            {{ familyRole }}
          </span>
        </div>
        <p class="mt-0.5 text-xs" style="color:var(--text-muted)">{{ fmt(post.created_at) }} · 家庭时间线</p>
      </div>
    </div>

    <div v-if="post.media_urls?.length" class="media-frame relative mt-4 bg-[color:rgb(132_74_40_/_0.12)]">
      <video
        v-if="firstMedia?.type === 'video'"
        :src="mediaUrl(firstMedia.url)"
        class="aspect-[16/10] w-full object-cover"
        controls
        preload="metadata"
        @click.stop
      />
      <img
        v-else-if="firstMedia"
        :src="mediaUrl(firstMedia.url)"
        class="post-photo aspect-[16/10] w-full object-cover"
        loading="lazy"
        alt=""
      />
      <span
        v-if="post.media_urls.length > 1"
        class="absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs backdrop-blur"
        style="background:rgba(255,248,235,0.78);color:var(--text-secondary);border:1px solid var(--border)"
      >
        <Images class="h-3.5 w-3.5" :stroke-width="1.8" />
        {{ post.media_urls.length }}
      </span>
    </div>

    <div class="space-y-4 px-4 py-4 sm:px-5 sm:py-5">
      <p
        v-if="post.content"
        class="text-sm leading-6 whitespace-pre-wrap"
        :class="post.media_urls?.length ? 'line-clamp-3' : 'line-clamp-6'"
        style="color:var(--text-secondary)"
      >
        {{ post.content }}
      </p>
      <p v-else class="text-sm" style="color:var(--text-muted)">这是一组没有文字说明的家庭影像。</p>

      <div
        class="flex flex-wrap items-center justify-between gap-3 border-t pt-4"
        style="border-color:var(--border)"
      >
        <div class="flex items-center gap-4 text-xs" style="color:var(--text-muted)">
          <button
            @click.stop="$emit('like', post)"
            class="like-button inline-flex items-center gap-1.5 transition-opacity hover:opacity-80"
            :style="{ color: post.is_liked ? 'var(--accent)' : undefined }"
            type="button"
          >
            <Heart class="h-4 w-4" :fill="post.is_liked ? 'currentColor' : 'none'" :stroke-width="1.8" />
            <span>{{ post.like_count }}</span>
          </button>
          <span class="inline-flex items-center gap-1.5">
            <MessageCircle class="h-4 w-4" :stroke-width="1.8" />
            <span>{{ post.comment_count }}</span>
          </span>
          <span v-if="post.media_urls?.length" class="inline-flex items-center gap-1.5">
            <Images class="h-4 w-4" :stroke-width="1.8" />
            <span>{{ post.media_urls.length }}</span>
          </span>
        </div>
        <span class="detail-hint text-xs" style="color:var(--text-muted)">查看详情</span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Heart, Images, MessageCircle } from 'lucide-vue-next'
import type { Post } from '@/api/posts'
import { mediaUrl } from '@/utils/media'

const props = defineProps<{ post: Post }>()
defineEmits<{ click: [id: string]; like: [post: Post] }>()

const firstMedia = computed(() => props.post.media_urls?.[0])
const initial = computed(() => props.post.author_username.trim().slice(0, 1).toUpperCase() || '家')
const familyRole = computed(() => {
  const roles = ['家庭记录者', '照片分享', '最近陪伴', '日常片段']
  const sum = Array.from(props.post.author_username).reduce((total, char) => total + char.charCodeAt(0), 0)
  return roles[sum % roles.length]
})

function fmt(t: string): string {
  const d = Date.now() - new Date(t).getTime()
  if (d < 6e4) return '刚刚'
  if (d < 36e5) return `${Math.floor(d / 6e4)}分`
  if (d < 864e5) return `${Math.floor(d / 36e5)}时`
  return new Date(t).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.post-card {
  box-shadow: 0 16px 42px rgba(47, 39, 35, 0.09);
  transition:
    border-color 190ms ease,
    box-shadow 190ms ease,
    transform 190ms ease,
    background-color 190ms ease;
}

.post-card:hover {
  border-color: rgba(201, 67, 47, 0.18) !important;
  box-shadow: 0 22px 54px rgba(47, 39, 35, 0.12);
  transform: translateY(-2px);
}

.author-avatar {
  transition:
    background-color 180ms ease,
    color 180ms ease,
    transform 180ms ease,
    opacity 180ms ease;
}

.post-card:hover .author-avatar {
  background: rgba(201, 67, 47, 0.12) !important;
  color: var(--accent) !important;
}

.media-frame {
  overflow: hidden;
}

.media-frame::after {
  background: linear-gradient(180deg, rgba(255, 255, 252, 0.14), rgba(255, 255, 252, 0) 34%);
  content: '';
  inset: 0;
  opacity: 0;
  pointer-events: none;
  position: absolute;
  transition: opacity 240ms ease;
}

.post-card:hover .media-frame::after {
  opacity: 1;
}

.post-photo {
  transition: filter 260ms ease, transform 720ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.post-card:hover .post-photo {
  filter: saturate(1.04) contrast(1.02);
  transform: scale(1.018);
}

.like-button {
  border-radius: 8px;
  margin: -0.35rem;
  padding: 0.35rem;
  transition:
    background-color 170ms ease,
    color 170ms ease,
    opacity 170ms ease,
    transform 170ms ease;
}

.like-button:hover {
  background: rgba(201, 67, 47, 0.1);
  opacity: 1;
}

.like-button:active {
  transform: scale(0.94);
}

.detail-hint {
  transition: color 170ms ease, transform 170ms ease;
}

.post-card:hover .detail-hint {
  color: var(--text-secondary) !important;
  transform: translateX(2px);
}

@media (prefers-reduced-motion: reduce) {
  .post-card,
  .author-avatar,
  .media-frame::after,
  .post-photo,
  .like-button,
  .detail-hint {
    transition: none;
  }

  .post-card:hover,
  .post-card:hover .post-photo,
  .like-button:active,
  .post-card:hover .detail-hint {
    transform: none;
  }
}
</style>
