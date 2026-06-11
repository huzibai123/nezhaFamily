<template>
  <div
    :id="`comment-${comment.id}`"
    class="comment-item"
    :class="{ 'is-reply': depth > 0, 'is-highlighted': comment.id === highlightedId }"
  >
    <div v-if="depth > 0" class="reply-indicator" :style="replyIndicatorStyle" />

    <div
      class="comment-card"
      :style="{
        marginLeft: depth > 0 ? '36px' : '0',
      }"
    >
      <div class="comment-body">
        <div
          class="avatar"
          :style="{ background: avatarGradient }"
        >
          <img
            v-if="comment.author_avatar_url"
            :src="mediaUrl(comment.author_avatar_url)"
            class="avatar-image"
            alt=""
          />
          <span v-else class="avatar-initial">{{ avatarInitial }}</span>
        </div>

        <div class="comment-content">
          <div class="comment-header">
            <span class="comment-author">{{ comment.author_username || '未知用户' }}</span>
            <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
          </div>

          <p class="comment-text">{{ comment.content }}</p>

          <div class="comment-actions">
            <button
              class="action-btn like-btn"
              :class="{ active: isLiked }"
              @click="toggleLike"
            >
              <Heart :size="14" :class="{ 'fill-current': isLiked }" />
              <span v-if="likeCount > 0" class="like-count">{{ likeCount }}</span>
              <span v-else class="like-label">赞</span>
            </button>

            <button
              class="action-btn reply-btn"
              @click="$emit('reply', comment.id)"
            >
              <CornerDownRight :size="14" />
              <span>回复</span>
            </button>

            <button
              v-if="isAuthor"
              class="action-btn delete-btn"
              @click="$emit('delete', comment.id)"
            >
              <Trash2 :size="14" />
              <span>删除</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="comment.replies && comment.replies.length > 0" class="replies-container">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :depth="depth + 1"
        :user-id="userId"
        :highlighted-id="highlightedId"
        @reply="$emit('reply', $event)"
        @delete="$emit('delete', $event)"
        @like="$emit('like', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Heart, CornerDownRight, Trash2 } from 'lucide-vue-next'
import type { Comment } from '@/api/posts'
import { mediaUrl } from '@/utils/media'

const props = withDefaults(defineProps<{
  comment: Comment
  depth?: number
  userId?: string | null
  highlightedId?: string | null
}>(), {
  depth: 0,
  userId: null,
  highlightedId: null,
})

const emit = defineEmits<{
  (e: 'reply', commentId: string): void
  (e: 'delete', commentId: string): void
  (e: 'like', commentId: string): void
}>()

const isAuthor = computed(() => {
  if (!props.userId) return false
  return props.comment.author_id === props.userId
})

const isLiked = computed(() => props.comment.is_liked ?? false)
const likeCount = computed(() => props.comment.like_count ?? 0)

const avatarGradient = computed(() => {
  const username = props.comment.author_username || 'unknown'
  const hue = hashString(username) % 360
  return `linear-gradient(135deg, hsl(${hue}, 42%, 48%), hsl(${(hue + 28) % 360}, 46%, 38%))`
})

const avatarInitial = computed(() => {
  const username = props.comment.author_username || '?'
  return username.charAt(0).toUpperCase()
})

const replyIndicatorColor = computed(() => {
  const username = props.comment.author_username || 'unknown'
  const hue = hashString(username) % 360
  return `hsl(${hue}, 60%, 60%)`
})

const replyIndicatorStyle = computed(() => ({
  background: `linear-gradient(to bottom, ${replyIndicatorColor.value}, transparent)`,
}))

function toggleLike() {
  emit('like', props.comment.id)
}

function hashString(str: string): number {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`

  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.comment-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3), rgba(255, 238, 211, 0.08)),
    rgba(255, 248, 235, 0.48);
  border: 1px solid rgba(132, 74, 40, 0.14);
  border-radius: 12px;
  padding: 14px 16px;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.comment-card:hover {
  background: rgba(255, 248, 235, 0.62);
  border-color: rgba(217, 77, 48, 0.18);
  box-shadow: 0 10px 26px rgba(143, 80, 40, 0.12);
  transform: translateY(-1px);
}

.comment-item {
  position: relative;
  scroll-margin-top: 7rem;
}

.comment-item.is-reply {
  margin-top: 8px;
}

.comment-item.is-highlighted > .comment-card {
  animation: comment-highlight 2.4s ease-out both;
  border-color: rgba(217, 77, 48, 0.42);
  box-shadow: 0 0 0 3px rgba(217, 77, 48, 0.12), 0 16px 34px rgba(143, 80, 40, 0.16);
}

.reply-indicator {
  position: absolute;
  left: 8px;
  top: 4px;
  bottom: 4px;
  width: 3px;
  border-radius: 2px;
  opacity: 0.6;
}

.comment-body {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(143, 80, 40, 0.16);
  overflow: hidden;
}

.avatar-image {
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.avatar-initial {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(75, 40, 25, 0.18);
  user-select: none;
}

.comment-content {
  flex: 1;
  min-width: 0;
}

.comment-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 4px;
}

.comment-author {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
}

.comment-time {
  font-size: 12px;
  color: var(--text-muted);
}

.comment-text {
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary);
  margin-bottom: 10px;
  word-break: break-word;
  white-space: pre-wrap;
}

.comment-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 20px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s ease, background 0.2s ease, transform 0.2s ease;
  line-height: 1;
}

.action-btn:hover {
  background: rgba(255, 244, 232, 0.07);
}

.action-btn:active {
  transform: scale(0.95);
}

.reply-btn:hover {
  color: var(--text-secondary);
}

.delete-btn:hover {
  color: rgba(255, 100, 100, 0.85);
  background: rgba(255, 80, 80, 0.12);
}

.like-btn.active {
  color: var(--accent);
}

.like-btn.active:hover {
  color: var(--accent);
  background: rgba(227, 107, 93, 0.12);
}

.like-btn:hover {
  color: var(--accent);
  background: rgba(227, 107, 93, 0.08);
}

.like-count,
.like-label {
  font-size: 13px;
}

.replies-container {
  margin-top: 8px;
}

@media (prefers-reduced-motion: reduce) {
  .comment-card,
  .action-btn {
    transition: none;
  }

  .comment-card:hover,
  .action-btn:active {
    transform: none;
  }

  .comment-item.is-highlighted > .comment-card {
    animation: none;
  }
}

@keyframes comment-highlight {
  0% {
    background: rgba(217, 77, 48, 0.18);
  }
  100% {
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.3), rgba(255, 238, 211, 0.08)),
      rgba(255, 248, 235, 0.48);
  }
}
</style>
