<template>
  <AppShell page-title="记忆详情" page-description="查看照片、正文和家人的互动">
    <template #header>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <button
            @click="router.back()"
            class="soft-button mb-4 inline-flex rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
            type="button"
          >
            返回
          </button>
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">家庭时间线</p>
          <h1 class="mt-2 text-2xl font-semibold tracking-normal text-[var(--text)] sm:text-3xl">
            记忆详情
          </h1>
        </div>

        <button
          v-if="post?.author_id === user?.id"
          @click="handleDelete"
          class="soft-button inline-flex rounded-lg border border-[color:rgb(227_107_93_/_0.35)] px-3 py-2 text-sm text-[var(--accent)] hover:bg-[var(--accent-soft)]"
          type="button"
          data-testid="delete-post"
        >
          删除这条记忆
        </button>
      </div>
    </template>

    <div v-if="error" class="rounded-lg border border-[color:rgb(227_107_93_/_0.24)] bg-[var(--accent-soft)] p-4 text-sm text-[var(--accent)]">
      {{ error }}
    </div>

    <div v-else-if="post" class="grid gap-6 xl:grid-cols-[minmax(0,1.12fr)_minmax(21rem,0.88fr)]">
      <section class="space-y-4">
        <div
          v-if="post.media_urls.length"
          class="detail-media overflow-hidden rounded-lg border border-[var(--border)] bg-[color:rgb(132_74_40_/_0.12)]"
        >
          <div v-for="m in post.media_urls" :key="m.url" class="detail-media-item border-b border-[var(--border)] last:border-b-0">
            <video
              v-if="m.type === 'video'"
              :src="mediaUrl(m.url)"
              class="max-h-[72vh] w-full bg-[color:rgb(75_40_25_/_0.18)] object-contain"
              controls
              preload="metadata"
            />
            <img
              v-else
              :src="mediaUrl(m.url)"
              class="max-h-[72vh] w-full object-contain"
              loading="lazy"
              alt=""
            />
          </div>
        </div>

        <div v-else class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-8 text-sm text-[var(--text-muted)]">
          这是一条没有媒体的文字记忆。
        </div>
      </section>

      <section class="space-y-5 xl:sticky xl:top-8 xl:self-start">
        <article class="detail-card rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)]">
          <div class="flex items-start gap-3">
            <div
              class="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-[var(--accent-soft)] text-base font-semibold text-[var(--accent)]"
            >
              {{ authorInitial }}
            </div>
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-[var(--text)]">{{ post.author_username }}</p>
              <p class="mt-0.5 text-xs text-[var(--text-muted)]">{{ detailDate }}</p>
            </div>
          </div>

          <p
            v-if="post.content"
            class="mt-5 whitespace-pre-wrap text-sm leading-7 text-[var(--text-secondary)]"
          >
            {{ post.content }}
          </p>
          <p v-else class="mt-5 text-sm text-[var(--text-muted)]">这组影像没有文字说明。</p>

          <div class="mt-5 flex items-center gap-6 border-t border-[var(--border)] pt-4">
            <button
              @click="handleLike"
              class="detail-action inline-flex items-center gap-2 text-sm transition-opacity hover:opacity-80"
              :class="post.is_liked ? 'text-[var(--accent)]' : 'text-[var(--text-muted)]'"
              type="button"
              data-testid="post-like"
            >
              <Heart class="h-4 w-4" :fill="post.is_liked ? 'currentColor' : 'none'" :stroke-width="1.9" />
              {{ post.like_count }}
            </button>
            <span class="inline-flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <MessageCircle class="h-4 w-4" :stroke-width="1.9" />
              {{ post.comment_count }}
            </span>
            <span v-if="post.media_urls.length" class="inline-flex items-center gap-2 text-sm text-[var(--text-muted)]">
              <Images class="h-4 w-4" :stroke-width="1.9" />
              {{ post.media_urls.length }}
            </span>
          </div>
        </article>

        <section class="detail-card rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4 shadow-[var(--shadow-panel)]">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-[var(--text)]">家人评论</h2>
            <div class="flex items-center gap-2">
              <span class="text-xs text-[var(--text-muted)]">{{ commentTotal }} 条</span>
              <button
                @click="refreshComments"
                class="soft-button grid h-8 w-8 place-items-center rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-50"
                type="button"
                :disabled="commentsLoading"
                title="刷新评论"
              >
                <RefreshCw class="h-3.5 w-3.5" :class="{ 'animate-spin': commentsLoading }" :stroke-width="2" />
              </button>
            </div>
          </div>

          <form @submit.prevent="handleComment" class="space-y-3">
            <div
              v-if="replyingTo"
              class="flex items-center justify-between rounded-lg bg-[var(--surface-elevated)] px-3 py-2 text-xs text-[var(--text-muted)]"
            >
              <span>正在回复一条评论</span>
              <button @click="cancelReply" class="text-[var(--text-secondary)] hover:text-[var(--text)]" type="button">
                取消
              </button>
            </div>
            <textarea
              ref="commentInputRef"
              v-model="newComment"
              :placeholder="replyingTo ? '写回复...' : '写评论...'"
              class="comment-input min-h-24 w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-4 py-3 text-sm leading-6 text-[var(--text)] outline-none placeholder:text-[var(--text-muted)] focus:border-[var(--border-focus)]"
              data-testid="comment-input"
            />
            <button
              type="submit"
              :disabled="!newComment.trim()"
              class="primary-button inline-flex rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)] active:scale-[0.98] disabled:opacity-30"
              data-testid="comment-submit"
            >
              发送
            </button>
          </form>

          <div class="mt-5 space-y-3">
            <CommentItem
              v-for="c in topLevelComments"
              :key="c.id"
              :comment="c"
              :user-id="user?.id"
              :highlighted-id="highlightedCommentId"
              @reply="handleReply"
              @delete="handleDeleteComment"
              @like="handleLikeComment"
            />
            <p v-if="!commentTotal" class="rounded-lg border border-dashed border-[var(--border)] p-5 text-center text-sm text-[var(--text-muted)]">
              还没有评论，写下第一句回应。
            </p>
          </div>
        </section>
      </section>
    </div>

    <div v-else class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-8 text-center text-sm text-[var(--text-muted)]">
      加载中...
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Heart, Images, MessageCircle, RefreshCw } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth'
import {
  createComment,
  deleteComment,
  deletePost,
  getComments,
  getPost,
  toggleCommentLike,
  togglePostLike,
  type Comment,
  type Post,
} from '@/api/posts'
import AppShell from '@/components/AppShell.vue'
import CommentItem from '@/components/CommentItem.vue'
import { mediaUrl } from '@/utils/media'

const route = useRoute()
const router = useRouter()
const { user } = useAuth()

const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])
const commentTotal = ref(0)
const commentsLoading = ref(false)
const newComment = ref('')
const error = ref('')
const replyingTo = ref<string | null>(null)
const highlightedCommentId = ref('')
const commentInputRef = ref<HTMLTextAreaElement | null>(null)
let highlightTimer: number | undefined

const topLevelComments = computed(() => comments.value)

const authorInitial = computed(() => post.value?.author_username.trim().slice(0, 1).toUpperCase() || '家')
const detailDate = computed(() => {
  if (!post.value) return ''
  return new Date(post.value.created_at).toLocaleString('zh-CN')
})

onMounted(async () => {
  const id = route.params.id as string
  try {
    post.value = await getPost(id)
    await loadComments(id)
    await focusCommentFromQuery()
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '加载失败'
  }
})

onBeforeUnmount(() => {
  if (highlightTimer) {
    window.clearTimeout(highlightTimer)
  }
})

watch(
  () => route.query.comment,
  async () => {
    await focusCommentFromQuery()
  }
)

async function loadComments(postId: string) {
  commentsLoading.value = true
  try {
    const response = await getComments(postId)
    comments.value = normalizeComments(response.comments)
    commentTotal.value = response.total
    if (post.value) {
      post.value.comment_count = response.total
    }
  } finally {
    commentsLoading.value = false
  }
}

function normalizeComments(items: Comment[] = []): Comment[] {
  return items.map((item) => ({
    ...item,
    replies: normalizeComments(item.replies || []),
  }))
}

function insertReply(items: Comment[], parentId: string, reply: Comment): Comment[] {
  return items.map((item) => {
    if (item.id === parentId) {
      return {
        ...item,
        replies: [...(item.replies || []), reply],
      }
    }
    return {
      ...item,
      replies: insertReply(item.replies || [], parentId, reply),
    }
  })
}

function updateCommentInTree(
  items: Comment[],
  commentId: string,
  updater: (comment: Comment) => Comment
): Comment[] {
  return items.map((item) => {
    if (item.id === commentId) {
      return updater(item)
    }
    return {
      ...item,
      replies: updateCommentInTree(item.replies || [], commentId, updater),
    }
  })
}

async function refreshComments() {
  if (!post.value) return
  try {
    await loadComments(post.value.id)
    await focusCommentFromQuery()
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '刷新评论失败'
  }
}

async function focusCommentFromQuery() {
  const commentId = typeof route.query.comment === 'string' ? route.query.comment : ''
  if (!commentId || !comments.value.length) return
  if (!findCommentById(comments.value, commentId)) return
  if (highlightTimer) {
    window.clearTimeout(highlightTimer)
  }
  highlightedCommentId.value = commentId
  await nextTick()
  const target = document.getElementById(`comment-${commentId}`)
  target?.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  })
  highlightTimer = window.setTimeout(() => {
    if (highlightedCommentId.value === commentId) {
      highlightedCommentId.value = ''
    }
    highlightTimer = undefined
  }, 2600)
}

function findCommentById(items: Comment[], commentId: string): Comment | null {
  for (const item of items) {
    if (item.id === commentId) return item
    const reply = findCommentById(item.replies || [], commentId)
    if (reply) return reply
  }
  return null
}

async function handleLike() {
  if (!post.value) return
  try {
    const result = await togglePostLike(post.value.id)
    post.value.is_liked = result.liked
    post.value.like_count = result.like_count
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '操作失败'
  }
}

async function handleComment() {
  if (!post.value || !newComment.value.trim()) return
  try {
    const parentId = replyingTo.value || undefined
    const comment = normalizeComments([
      await createComment(post.value.id, newComment.value.trim(), parentId),
    ])[0]
    comments.value = parentId ? insertReply(comments.value, parentId, comment) : [...comments.value, comment]
    commentTotal.value += 1
    post.value.comment_count = commentTotal.value
    newComment.value = ''
    replyingTo.value = null
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '评论失败'
  }
}

async function handleDelete() {
  if (!post.value) return
  try {
    await deletePost(post.value.id)
    router.push('/')
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '删除失败'
  }
}

function handleReply(commentId: string) {
  replyingTo.value = commentId
  nextTick(() => commentInputRef.value?.focus())
}

function cancelReply() {
  replyingTo.value = null
}

async function handleDeleteComment(commentId: string) {
  if (!post.value) return
  try {
    await deleteComment(commentId)
    await loadComments(post.value.id)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '删除评论失败'
  }
}

async function handleLikeComment(commentId: string) {
  try {
    const result = await toggleCommentLike(commentId)
    comments.value = updateCommentInTree(comments.value, commentId, (comment) =>
      ({ ...comment, is_liked: result.liked, like_count: result.like_count }),
    )
  } catch (e: any) {
    error.value = e?.response?.data?.detail || e?.message || '点赞失败'
  }
}
</script>

<style scoped>
.soft-button,
.primary-button,
.detail-media,
.detail-media-item img,
.detail-card,
.detail-action,
.comment-input {
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
.primary-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.primary-button:hover:not(:disabled) {
  box-shadow: 0 10px 26px rgba(217, 77, 48, 0.16);
}

.detail-media,
.detail-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 238, 211, 0.08)),
    var(--surface-card);
}

.detail-media:hover,
.detail-card:hover {
  border-color: rgba(217, 77, 48, 0.18);
  box-shadow: 0 20px 50px rgba(143, 80, 40, 0.14);
}

.detail-media-item {
  overflow: hidden;
}

.detail-media-item:hover img {
  filter: saturate(1.03) contrast(1.02);
}

.detail-action {
  border-radius: 8px;
  margin: -0.35rem;
  padding: 0.35rem;
}

.detail-action:hover {
  background: rgba(227, 107, 93, 0.08);
  opacity: 1;
}

.detail-action:active {
  transform: scale(0.95);
}

.comment-input:focus {
  box-shadow: 0 0 0 3px rgba(227, 107, 93, 0.09);
}

@media (prefers-reduced-motion: reduce) {
  .soft-button,
  .primary-button,
  .detail-media,
  .detail-media-item img,
  .detail-card,
  .detail-action,
  .comment-input {
    transition: none;
  }

  .soft-button:hover,
  .primary-button:hover:not(:disabled),
  .detail-action:active {
    transform: none;
  }
}
</style>
