<template>
  <article
    @click="$emit('click', post.id)"
    :class="cardClass"
    class="post-card enter group cursor-pointer"
  >
    <!-- ==================== default 模式：标准卡片 ==================== -->
    <template v-if="layoutMode === 'default'">
      <header class="post-header">
        <router-link
          :to="`/profile/${post.author_id}`"
          @click.stop
          class="author-avatar"
        >
          {{ initial }}
        </router-link>
        <div class="post-header-meta">
          <div class="post-header-row">
            <router-link
              :to="`/profile/${post.author_id}`"
              @click.stop
              class="post-author"
            >
              {{ post.author_username }}
            </router-link>
            <span class="post-role-tag">{{ familyRole }}</span>
          </div>
          <p class="post-meta">{{ fmt(post.created_at) }} / 家庭时间线</p>
        </div>
      </header>

      <div v-if="post.media_urls?.length" class="image-area">
        <video
          v-if="firstMedia?.type === 'video'"
          :src="mediaUrl(firstMedia.url)"
          class="post-media"
          controls
          preload="metadata"
          @click.stop
        />
        <img
          v-else-if="firstMedia"
          :src="mediaUrl(firstMedia.url)"
          class="post-media"
          loading="lazy"
          alt=""
        />
        <span v-if="post.media_urls.length > 1" class="image-count-badge">
          <Images class="icon" :stroke-width="1.8" />
          {{ post.media_urls.length }}
        </span>
      </div>

      <div class="post-content-area">
        <p v-if="post.content" class="post-body line-clamp-3">{{ post.content }}</p>
        <p v-else class="post-body post-body--empty">这是一组没有文字说明的家庭影像。</p>

        <div class="post-action-bar">
          <div class="post-action-group">
            <button
              @click.stop="$emit('like', post)"
              class="like-button"
              :class="{ 'is-liked': post.is_liked }"
              type="button"
            >
              <Heart class="icon" :fill="post.is_liked ? 'currentColor' : 'none'" :stroke-width="1.8" />
              <span>{{ post.like_count }}</span>
            </button>
            <span class="action-stat">
              <MessageCircle class="icon" :stroke-width="1.8" />
              <span>{{ post.comment_count }}</span>
            </span>
            <span v-if="post.media_urls?.length" class="action-stat">
              <Images class="icon" :stroke-width="1.8" />
              <span>{{ post.media_urls.length }}</span>
            </span>
          </div>
          <span class="detail-hint">查看详情</span>
        </div>
      </div>
    </template>

    <!-- ==================== single-dark 模式：大图叠字 ==================== -->
    <template v-else-if="layoutMode === 'single-dark'">
      <div class="single-dark-card">
        <video
          v-if="firstMedia?.type === 'video'"
          :src="mediaUrl(firstMedia.url)"
          class="single-dark-image"
          controls
          preload="metadata"
          @click.stop
        />
        <img
          v-else-if="firstMedia"
          :src="mediaUrl(firstMedia.url)"
          class="single-dark-image"
          loading="lazy"
          alt=""
        />
        <div v-else class="single-dark-image single-dark-image--empty"></div>
        <div class="single-dark-overlay">
          <h3 v-if="post.content" class="single-dark-title line-clamp-3">{{ post.content }}</h3>
          <h3 v-else class="single-dark-title">家庭影像</h3>
          <p class="single-dark-meta">
            <span>{{ post.author_username }}</span>
            <span class="dot-sep">/</span>
            <span>{{ fmt(post.created_at) }}</span>
          </p>
          <div class="single-dark-actions">
            <button
              @click.stop="$emit('like', post)"
              class="like-button like-button--dark"
              :class="{ 'is-liked': post.is_liked }"
              type="button"
            >
              <Heart class="icon" :fill="post.is_liked ? 'currentColor' : 'none'" :stroke-width="1.8" />
              <span>{{ post.like_count }}</span>
            </button>
            <span class="action-stat action-stat--dark">
              <MessageCircle class="icon" :stroke-width="1.8" />
              <span>{{ post.comment_count }}</span>
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- ==================== timeline 模式：左侧装饰条 + 时间圆点 ==================== -->
    <template v-else-if="layoutMode === 'timeline'">
      <div class="timeline-card">
        <header class="post-header">
          <router-link
            :to="`/profile/${post.author_id}`"
            @click.stop
            class="author-avatar"
          >
            {{ initial }}
          </router-link>
          <div class="post-header-meta">
            <router-link
              :to="`/profile/${post.author_id}`"
              @click.stop
              class="post-author"
            >
              {{ post.author_username }}
            </router-link>
            <p class="post-meta">{{ fmt(post.created_at) }}</p>
          </div>
        </header>

        <div v-if="post.media_urls?.length" class="image-area image-area--timeline">
          <video
            v-if="firstMedia?.type === 'video'"
            :src="mediaUrl(firstMedia.url)"
            class="post-media"
            controls
            preload="metadata"
            @click.stop
          />
          <img
            v-else-if="firstMedia"
            :src="mediaUrl(firstMedia.url)"
            class="post-media"
            loading="lazy"
            alt=""
          />
        </div>

        <div class="post-content-area">
          <p v-if="post.content" class="post-body post-body--timeline line-clamp-3">{{ post.content }}</p>
          <div class="post-action-group post-action-group--timeline">
            <button
              @click.stop="$emit('like', post)"
              class="like-button"
              :class="{ 'is-liked': post.is_liked }"
              type="button"
            >
              <Heart class="icon icon--sm" :fill="post.is_liked ? 'currentColor' : 'none'" :stroke-width="1.8" />
              <span>{{ post.like_count }}</span>
            </button>
            <span class="action-stat">
              <MessageCircle class="icon icon--sm" :stroke-width="1.8" />
              <span>{{ post.comment_count }}</span>
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- ==================== grid 模式：正方形 hover overlay ==================== -->
    <template v-else-if="layoutMode === 'grid'">
      <div class="grid-card">
        <video
          v-if="firstMedia?.type === 'video'"
          :src="mediaUrl(firstMedia.url)"
          class="grid-image"
          preload="metadata"
          @click.stop
        />
        <img
          v-else-if="firstMedia"
          :src="mediaUrl(firstMedia.url)"
          class="grid-image"
          loading="lazy"
          alt=""
        />
        <div v-else class="grid-image grid-image--empty">
          <p class="grid-empty-text">{{ post.content?.slice(0, 48) || '文字记忆' }}</p>
        </div>
        <div class="grid-overlay">
          <p class="grid-author">{{ post.author_username }}</p>
          <p v-if="post.content" class="grid-content line-clamp-3">{{ post.content }}</p>
          <div class="grid-actions">
            <span class="action-stat action-stat--dark">
              <Heart class="icon icon--sm" :stroke-width="2" />
              {{ post.like_count }}
            </span>
            <span class="action-stat action-stat--dark">
              <MessageCircle class="icon icon--sm" :stroke-width="2" />
              {{ post.comment_count }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- ==================== masonry 模式：衬线大标题 + 引言式 ==================== -->
    <template v-else-if="layoutMode === 'masonry'">
      <div class="masonry-card">
        <h3 v-if="post.content" class="masonry-title">
          {{ post.content.slice(0, 60) }}{{ post.content.length > 60 ? '…' : '' }}
        </h3>
        <h3 v-else class="masonry-title">家庭影像</h3>

        <div v-if="post.media_urls?.length" class="image-area image-area--masonry" :class="masonryAspectClass">
          <video
            v-if="firstMedia?.type === 'video'"
            :src="mediaUrl(firstMedia.url)"
            class="post-media post-media--masonry"
            controls
            preload="metadata"
            @click.stop
          />
          <img
            v-else-if="firstMedia"
            :src="mediaUrl(firstMedia.url)"
            class="post-media post-media--masonry"
            loading="lazy"
            alt=""
          />
        </div>

        <p v-if="post.content && post.content.length > 60" class="masonry-pullquote line-clamp-3">
          {{ post.content.slice(60) }}
        </p>

        <footer class="masonry-footer">
          <span class="masonry-byline">{{ post.author_username }}</span>
          <span class="dot-sep">/</span>
          <span>{{ fmt(post.created_at) }}</span>
          <span class="dot-sep">/</span>
          <span>{{ post.like_count }} 赞</span>
        </footer>
      </div>
    </template>

    <!-- ==================== minimal 模式：极简留白 ==================== -->
    <template v-else-if="layoutMode === 'minimal'">
      <div class="minimal-card">
        <p class="minimal-meta">
          <span>{{ fmt(post.created_at) }}</span>
        </p>
        <div v-if="post.media_urls?.length" class="image-area image-area--minimal">
          <video
            v-if="firstMedia?.type === 'video'"
            :src="mediaUrl(firstMedia.url)"
            class="post-media post-media--minimal"
            controls
            preload="metadata"
            @click.stop
          />
          <img
            v-else-if="firstMedia"
            :src="mediaUrl(firstMedia.url)"
            class="post-media post-media--minimal"
            loading="lazy"
            alt=""
          />
        </div>
        <h3 v-if="post.content" class="minimal-title line-clamp-2">
          {{ post.content.slice(0, 58) }}{{ post.content.length > 58 ? '...' : '' }}
        </h3>
        <p class="minimal-byline">{{ post.author_username }}</p>
        <div class="minimal-actions">
          <button
            @click.stop="$emit('like', post)"
            class="like-button like-button--minimal"
            :class="{ 'is-liked': post.is_liked }"
            type="button"
          >
            <Heart class="icon icon--sm" :fill="post.is_liked ? 'currentColor' : 'none'" :stroke-width="1" />
            <span>{{ post.like_count }}</span>
          </button>
          <span class="action-stat action-stat--minimal">
            <MessageCircle class="icon icon--sm" :stroke-width="1" />
            <span>{{ post.comment_count }}</span>
          </span>
        </div>
      </div>
    </template>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Heart, Images, MessageCircle } from 'lucide-vue-next'
import type { Post } from '@/api/posts'
import { mediaUrl } from '@/utils/media'

const props = withDefaults(defineProps<{ post: Post; layoutMode?: string }>(), {
  layoutMode: 'default'
})
defineEmits<{ click: [id: string]; like: [post: Post] }>()

const firstMedia = computed(() => props.post.media_urls?.[0])
const initial = computed(() => props.post.author_username.trim().slice(0, 1).toUpperCase() || '家')
const familyRole = computed(() => {
  const roles = ['家庭记录者', '照片分享', '最近陪伴', '日常片段']
  const sum = Array.from(props.post.author_username).reduce((total, char) => total + char.charCodeAt(0), 0)
  return roles[sum % roles.length]
})

const cardClass = computed(() => {
  const base = 'post-card'
  switch (props.layoutMode) {
    case 'single-dark':
      return `${base} post-card--single-dark`
    case 'timeline':
      return `${base} post-card--timeline`
    case 'grid':
      return `${base} post-card--grid`
    case 'masonry':
      return `${base} post-card--masonry`
    case 'minimal':
      return `${base} post-card--minimal`
    default:
      return `${base} post-card--default`
  }
})

const masonryAspectClass = computed(() => {
  const hash = props.post.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  const variants = ['aspect-4-5', 'aspect-3-4', 'aspect-1-1', 'aspect-16-9']
  return variants[hash % variants.length]
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
/* ============================================================
 * PostCard 基础变量驱动样式
 * 所有可主题化的视觉量都来自 CSS 变量（带回退默认值）
 * ============================================================ */
.post-card {
  position: relative;
  overflow: hidden;
  background: var(--surface-card, #fafaf9);
  border: 1px solid var(--border, #f0ede8);
  border-radius: var(--card-radius, 12px);
  box-shadow: var(--card-shadow, 0 2px 8px rgba(0, 0, 0, 0.08));
  transition:
    border-color 200ms ease,
    box-shadow 200ms ease,
    transform 200ms ease,
    background-color 200ms ease;
}

/* ---------- 通用基础组件 ---------- */
.post-header {
  display: flex;
  align-items: flex-start;
  gap: 11px;
  padding: var(--card-padding, 16px);
  padding-bottom: 0;
}

.post-header-meta {
  min-width: 0;
  flex: 1;
}

.post-header-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.author-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  background: var(--accent-soft, rgba(217, 77, 48, 0.1));
  color: var(--text-secondary, #403b35);
  transition: background-color 180ms ease, color 180ms ease, opacity 180ms ease;
  text-decoration: none;
}

.author-avatar:hover {
  opacity: 0.85;
}

.post-card:not(.post-card--minimal):not(.post-card--single-dark):hover .author-avatar {
  background: var(--accent-soft, rgba(217, 77, 48, 0.12));
  color: var(--accent, #d94d30);
}

.post-author {
  font-size: 13.5px;
  font-weight: var(--font-weight-title, 600);
  font-family: var(--font-family-title, inherit);
  color: var(--text, #2f2723);
  text-decoration: none;
}

.post-author:hover {
  opacity: 0.8;
}

.post-role-tag {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 6px;
  font-size: 10.5px;
  background: var(--accent-soft, rgba(217, 77, 48, 0.1));
  color: var(--accent, #d94d30);
}

.post-meta {
  margin-top: 2px;
  font-size: 11.5px;
  color: var(--text-muted, #5d554c);
}

.image-area {
  position: relative;
  margin-top: 13px;
  overflow: hidden;
  background: rgba(132, 74, 40, 0.12);
  height: var(--card-image-height, 220px);
  aspect-ratio: var(--card-image-ratio, 16 / 10);
}

.image-area .post-media {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: filter 260ms ease, transform 720ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.post-card:hover .image-area .post-media {
  transform: scale(1.02);
}

.image-count-badge {
  position: absolute;
  bottom: 12px;
  right: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 12px;
  background: rgba(255, 248, 235, 0.78);
  color: var(--text-secondary, #403b35);
  border: 1px solid var(--border, #f0ede8);
  backdrop-filter: blur(8px);
}

.post-content-area {
  padding: var(--card-padding, 16px);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.post-body {
  font-size: clamp(13px, 0.92vw, var(--font-size-body, 14px));
  font-weight: var(--font-weight-body, 400);
  line-height: 1.66;
  color: var(--text-secondary, #403b35);
  white-space: pre-wrap;
  word-break: break-word;
}

.post-body--empty {
  color: var(--text-muted, #5d554c);
}

.post-action-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 12px;
  border-top: 1px solid var(--border, #f0ede8);
}

.post-action-group {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 11.5px;
  color: var(--text-muted, #5d554c);
}

.action-stat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.icon {
  width: 16px;
  height: 16px;
}

.icon--sm {
  width: 13px;
  height: 13px;
}

.like-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  margin: -4px -6px;
  border-radius: 8px;
  background: transparent;
  color: inherit;
  border: none;
  cursor: pointer;
  font-size: inherit;
  transition: background-color 170ms ease, color 170ms ease, transform 170ms ease;
}

.like-button:hover {
  background: var(--accent-soft, rgba(217, 77, 48, 0.1));
}

.like-button:active {
  transform: scale(0.94);
}

.like-button.is-liked {
  color: var(--accent, #d94d30);
}

.detail-hint {
  font-size: 11.5px;
  color: var(--text-muted, #5d554c);
  transition: color 170ms ease, transform 170ms ease;
}

.post-card--default:hover .detail-hint {
  color: var(--text-secondary, #403b35);
  transform: translateX(2px);
}

.dot-sep {
  opacity: 0.55;
}

/* line-clamp 工具 */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ============================================================
 * 1. default - 标准卡片：头像顶部、图片中部、互动条底部
 * ============================================================ */
.post-card--default:hover {
  border-color: var(--border-focus, rgba(217, 77, 48, 0.18));
  box-shadow: 0 22px 54px rgba(47, 39, 35, 0.12);
  transform: translateY(-2px);
}

.post-card--default:hover .image-area .post-media {
  filter: saturate(1.04) contrast(1.02);
  transform: scale(1.018);
}

.post-card--default .image-area {
  border-radius: calc(var(--card-radius, 12px) - 4px);
  margin-left: var(--card-padding, 16px);
  margin-right: var(--card-padding, 16px);
  width: auto;
}

.post-card--default .post-body {
  color: var(--text-secondary, #403b35);
  max-width: 58ch;
}

/* ============================================================
 * 2. single-dark - 大图卡片，文字叠在图片底部
 * ============================================================ */
.post-card--single-dark {
  border: none;
  box-shadow: var(--card-shadow, 0 24px 60px rgba(0, 0, 0, 0.35));
  background: var(--surface-card, #121722);
}

.post-card--single-dark:hover {
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.5);
  transform: translateY(-4px);
}

.single-dark-card {
  position: relative;
  height: min(var(--card-image-height, 500px), 32rem);
  overflow: hidden;
  border-radius: inherit;
}

.single-dark-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 800ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.single-dark-image--empty {
  background: linear-gradient(135deg, #2c2520 0%, #1a1614 100%);
}

.post-card--single-dark:hover .single-dark-image {
  transform: scale(1.05);
}

.single-dark-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: clamp(1.2rem, 3vw, 1.6rem);
  color: var(--text-inverse, #f8f8f5);
  background: linear-gradient(to top, rgba(9, 12, 18, 0.88) 0%, rgba(9, 12, 18, 0.42) 60%, transparent 100%);
}

.single-dark-title {
  font-family: var(--font-family-title, inherit);
  font-size: clamp(1.05rem, 1.75vw, 1.45rem);
  font-weight: var(--font-weight-title, 600);
  line-height: 1.32;
  margin-bottom: 10px;
}

.single-dark-meta {
  font-size: 12px;
  opacity: 0.78;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.single-dark-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
}

.like-button--dark {
  color: rgba(255, 255, 255, 0.85);
}

.like-button--dark:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.like-button--dark.is-liked {
  color: var(--accent, #ff6b6b);
}

.action-stat--dark {
  color: rgba(255, 255, 255, 0.85);
}

/* ============================================================
 * 3. timeline - 左侧 4px 装饰条 + 时间圆点
 * ============================================================ */
.post-card--timeline {
  border-left: none;
  padding-left: 0;
  background: transparent;
  box-shadow: none;
  border: none;
  border-radius: 0;
}

.post-card--timeline .timeline-card {
  position: relative;
  background: var(--surface-card, #fafaf9);
  border: 1px solid var(--border, #f0ede8);
  border-radius: var(--card-radius, 16px);
  border-left: 3px solid var(--accent, #d94d30);
  box-shadow: var(--card-shadow, 0 8px 24px rgba(47, 39, 35, 0.06));
  margin-left: 6px;
  transition: box-shadow 200ms ease, transform 200ms ease;
}

.post-card--timeline .timeline-card::before {
  content: '';
  position: absolute;
  left: -9px;
  top: 26px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--accent, #d94d30);
  border: 3px solid var(--surface, #fff);
  box-shadow: 0 0 0 4px var(--accent-soft, rgba(217, 77, 48, 0.1));
  transition: transform 200ms ease, box-shadow 200ms ease;
}

.post-card--timeline:hover .timeline-card {
  box-shadow: 0 12px 36px rgba(47, 39, 35, 0.1);
  transform: translateX(4px);
}

.post-card--timeline:hover .timeline-card::before {
  transform: scale(1.2);
  box-shadow: 0 0 0 6px var(--accent-soft, rgba(217, 77, 48, 0.18));
}

.image-area--timeline {
  margin: 13px var(--card-padding, 18px) 0;
  border-radius: 8px;
  /* 媒体宽高比按 layout 独立 token，回退值即当前实际值，避免跨主题相互影响 */
  aspect-ratio: var(--post-media-ratio-timeline, 16 / 9);
  height: auto;
}

.post-body--timeline {
  font-size: clamp(13px, 1vw, 14px);
  line-height: 1.62;
}

.post-action-group--timeline {
  margin-top: 10px;
}

/* ============================================================
 * 4. grid - 正方形 + hover overlay
 * ============================================================ */
.post-card--grid {
  border-radius: var(--card-radius, 12px);
  box-shadow: var(--card-shadow, 0 4px 16px rgba(47, 39, 35, 0.08));
  min-height: 11rem;
}

.post-card--grid:hover {
  box-shadow: 0 12px 32px rgba(47, 39, 35, 0.18);
  transform: translateY(-3px);
}

.grid-card {
  position: relative;
  /* 媒体宽高比按 layout 独立 token，回退值即当前实际值 */
  aspect-ratio: var(--post-media-ratio-grid, 1 / 1);
  height: 100%;
  overflow: hidden;
  border-radius: inherit;
  background: var(--surface-card, #fafaf9);
}

.grid-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 400ms cubic-bezier(0.2, 0.8, 0.2, 1);
}

.grid-image--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: clamp(0.75rem, 3vw, 1.2rem);
  background: var(--surface-card, #fafaf9);
  color: var(--text-secondary, #403b35);
}

.grid-empty-text {
  font-size: clamp(11.5px, 2.8vw, 13px);
  text-align: center;
  line-height: 1.45;
}

.post-card--grid:hover .grid-image {
  transform: scale(1.08);
}

.grid-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: clamp(0.75rem, 2.2vw, 1rem);
  color: #fff;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.78) 0%, rgba(0, 0, 0, 0.35) 50%, rgba(0, 0, 0, 0) 100%);
  opacity: 0;
  transition: opacity 280ms ease;
  pointer-events: none;
}

.post-card--grid:hover .grid-overlay {
  opacity: 1;
}

.grid-author {
  font-size: 11.5px;
  font-weight: 600;
  margin-bottom: 4px;
}

.grid-content {
  font-size: clamp(12px, 1.2vw, 13px);
  line-height: 1.46;
}

.grid-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
  font-size: 11px;
  opacity: 0.85;
}

/* ============================================================
 * 5. masonry - 衬线大标题在前 + 引言式排版 + 首字下沉
 * ============================================================ */
.post-card--masonry {
  break-inside: avoid;
  margin-bottom: var(--card-gap, 20px);
  border-radius: var(--card-radius, 8px);
  box-shadow: var(--card-shadow, 0 2px 12px rgba(0, 0, 0, 0.06));
}

.post-card--masonry:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.14);
  transform: translateY(-2px);
}

.masonry-card {
  padding: clamp(1.1rem, 2.4vw, 1.5rem);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.masonry-title {
  font-family: var(--font-family-title, Georgia, 'Times New Roman', serif);
  font-size: clamp(1.15rem, 2.1vw, 1.45rem);
  font-weight: 700;
  line-height: 1.34;
  letter-spacing: 0;
  color: var(--text, #2f2723);
  margin: 0;
}

.masonry-title::first-letter {
  font-size: 1.28em;
  font-weight: 900;
  line-height: 1;
  margin-right: 2px;
}

.image-area--masonry {
  margin-top: 0;
  height: auto;
  border-radius: 4px;
  overflow: hidden;
}

.image-area--masonry.aspect-4-5 {
  aspect-ratio: 4 / 5;
}
.image-area--masonry.aspect-3-4 {
  aspect-ratio: 3 / 4;
}
.image-area--masonry.aspect-1-1 {
  aspect-ratio: 1 / 1;
}
.image-area--masonry.aspect-16-9 {
  aspect-ratio: 16 / 9;
}

.post-media--masonry {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: grayscale(0.08) contrast(1.04);
  transition: transform 500ms ease, filter 300ms ease;
}

.post-card--masonry:hover .post-media--masonry {
  transform: scale(1.02);
  filter: grayscale(0) contrast(1.08);
}

.masonry-pullquote {
  font-family: var(--font-family-title, Georgia, 'Times New Roman', serif);
  font-size: 14px;
  font-style: italic;
  line-height: 1.68;
  color: var(--text-secondary, #403b35);
  border-left: 2px solid var(--accent, #d94d30);
  padding-left: 14px;
  margin: 0;
}

.masonry-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 14px;
  border-top: 1px solid var(--border, #f0ede8);
  font-size: 11.5px;
  color: var(--text-muted, #5d554c);
  font-family: var(--font-family-title, inherit);
}

.masonry-byline {
  font-weight: 600;
  letter-spacing: 0;
}

/* ============================================================
 * 6. minimal - 无阴影、居中、大量留白
 * ============================================================ */
.post-card--minimal {
  border: none;
  box-shadow: none;
  background: transparent;
  border-radius: 0;
}

.post-card--minimal:hover {
  box-shadow: none;
  transform: none;
  border: none;
}

.minimal-card {
  padding: clamp(2.2rem, 6vw, 4rem) clamp(1rem, 5vw, 3rem);
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.minimal-meta {
  font-size: 11px;
  font-weight: 300;
  color: var(--text-muted, #5d554c);
  letter-spacing: 0;
  text-transform: uppercase;
  margin-bottom: clamp(1.5rem, 4vw, 2rem);
}

.image-area--minimal {
  width: 100%;
  margin: 0 0 clamp(1.5rem, 4vw, 2.25rem);
  height: min(var(--card-image-height, 320px), 28rem);
  /* 媒体宽高比按 layout 独立 token，回退值即当前实际值 */
  aspect-ratio: var(--post-media-ratio-minimal, 4 / 3);
  background: rgba(0, 0, 0, 0.02);
  overflow: hidden;
}

.post-media--minimal {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: grayscale(0.18);
  transition: opacity 400ms ease, filter 400ms ease;
}

.post-card--minimal:hover .post-media--minimal {
  filter: grayscale(0);
  opacity: 0.95;
}

.minimal-title {
  font-family: var(--font-family-title, inherit);
  font-size: clamp(1rem, 1.9vw, 1.28rem);
  font-weight: 300;
  line-height: 1.48;
  letter-spacing: 0;
  color: var(--text, #2f2723);
  margin: 0 0 12px;
  max-width: 34rem;
}

.minimal-byline {
  font-size: 11px;
  font-weight: 300;
  color: var(--text-muted, #5d554c);
  letter-spacing: 0;
  text-transform: uppercase;
  margin-bottom: clamp(1.5rem, 4vw, 2rem);
}

.minimal-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  font-size: 11.5px;
  font-weight: 300;
  color: var(--text-muted, #5d554c);
}

.like-button--minimal {
  font-weight: 300;
}

.like-button--minimal:hover {
  background: transparent;
  opacity: 0.6;
}

.action-stat--minimal {
  font-weight: 300;
}

/* ============================================================
 * 动画减弱偏好
 * ============================================================ */
@media (prefers-reduced-motion: reduce) {
  .post-card,
  .author-avatar,
  .post-media,
  .single-dark-image,
  .grid-image,
  .post-media--masonry,
  .post-media--minimal,
  .like-button,
  .detail-hint,
  .grid-overlay,
  .post-card--timeline .timeline-card,
  .post-card--timeline .timeline-card::before {
    transition: none;
  }

  .post-card:hover,
  .post-card:hover .post-media,
  .post-card:hover .single-dark-image,
  .post-card:hover .grid-image,
  .post-card:hover .post-media--masonry,
  .like-button:active,
  .post-card:hover .detail-hint,
  .post-card--timeline:hover .timeline-card,
  .post-card--timeline:hover .timeline-card::before {
    transform: none;
  }
}
</style>
