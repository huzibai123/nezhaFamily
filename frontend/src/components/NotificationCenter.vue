<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import { Bell, CheckCheck, Inbox, Loader2 } from 'lucide-vue-next'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
  type NotificationType,
} from '@/api/notifications'

const props = withDefaults(
  defineProps<{
    compact?: boolean
  }>(),
  {
    compact: true,
  }
)

const notifications = ref<NotificationItem[]>([])
const unreadCount = ref(0)
const total = ref(0)
const page = ref(1)
const hasMore = ref(false)
const loading = ref(false)
const errorMessage = ref('')
const unreadOnly = ref(false)
const selectedType = ref<NotificationType | ''>('')

const pageSize = computed(() => (props.compact ? 8 : 12))
const visibleNotifications = computed(() =>
  props.compact ? notifications.value.slice(0, 5) : notifications.value
)

const typeOptions: Array<{ label: string; value: NotificationType | '' }> = [
  { label: '全部类型', value: '' },
  { label: '新动态', value: 'new_post' },
  { label: '评论', value: 'comment' },
  { label: '回复', value: 'reply' },
  { label: '帖子点赞', value: 'like_post' },
  { label: '评论点赞', value: 'like_comment' },
]

onMounted(() => loadNotifications(1))

watch([unreadOnly, selectedType], () => {
  if (!props.compact) {
    loadNotifications(1)
  }
})

async function loadNotifications(targetPage = 1, append = false) {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await getNotifications({
      unreadOnly: unreadOnly.value,
      type: selectedType.value,
      page: targetPage,
      pageSize: pageSize.value,
    })
    page.value = response.page
    total.value = response.total
    hasMore.value = response.has_more
    unreadCount.value = response.unread_count || 0
    notifications.value = append
      ? [...notifications.value, ...(response.notifications || [])]
      : response.notifications || []
  } catch {
    errorMessage.value = '通知暂时不可用'
  } finally {
    loading.value = false
  }
}

async function markRead(item: NotificationItem) {
  if (item.is_read) return
  try {
    const updated = await markNotificationRead(item.id)
    if (unreadOnly.value && !props.compact) {
      notifications.value = notifications.value.filter((current) => current.id !== item.id)
      total.value = Math.max(0, total.value - 1)
    } else {
      notifications.value = notifications.value.map((current) =>
        current.id === item.id ? { ...current, ...updated, is_read: true } : current
      )
    }
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch {
    errorMessage.value = '标记失败'
  }
}

async function readAll() {
  try {
    await markAllNotificationsRead()
    unreadCount.value = 0
    if (unreadOnly.value && !props.compact) {
      notifications.value = []
      total.value = 0
      hasMore.value = false
      return
    }
    notifications.value = notifications.value.map((item) => ({ ...item, is_read: true }))
  } catch {
    errorMessage.value = '标记失败'
  }
}

function notificationLink(item: NotificationItem): RouteLocationRaw {
  if (!item.post_id) return '/'
  if (item.target_type === 'comment') {
    return { path: `/post/${item.post_id}`, query: { comment: item.target_id } }
  }
  return `/post/${item.post_id}`
}

function typeLabel(type: NotificationType): string {
  return typeOptions.find((item) => item.value === type)?.label || '通知'
}

function formatTime(value: string): string {
  const diff = Date.now() - new Date(value).getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return new Date(value).toLocaleDateString('zh-CN')
}
</script>

<template>
  <section class="notification-center rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4 shadow-[var(--shadow-panel)]">
    <header class="mb-4 flex items-start justify-between gap-3">
      <div class="flex min-w-0 items-center gap-2">
        <span class="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
          <Bell :size="16" stroke-width="1.9" aria-hidden="true" />
        </span>
        <div class="min-w-0">
          <h2 class="text-sm font-semibold text-[var(--text)]">通知中心</h2>
          <p class="text-xs text-[var(--text-muted)]">
            {{ unreadCount }} 条未读<span v-if="!compact"> · 共 {{ total }} 条</span>
          </p>
        </div>
      </div>
      <button
        v-if="unreadCount"
        @click="readAll"
        class="notify-action grid h-8 w-8 place-items-center rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
        type="button"
        title="全部标为已读"
      >
        <CheckCheck :size="15" stroke-width="1.9" aria-hidden="true" />
      </button>
    </header>

    <div v-if="!compact" class="mb-4 grid gap-2 sm:grid-cols-[minmax(0,1fr)_11rem]">
      <div class="grid grid-cols-2 gap-2">
        <button
          class="filter-button rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
          :class="!unreadOnly ? 'is-active' : ''"
          type="button"
          @click="unreadOnly = false"
        >
          全部
        </button>
        <button
          class="filter-button rounded-lg border border-[var(--border)] px-3 py-2 text-sm"
          :class="unreadOnly ? 'is-active' : ''"
          type="button"
          @click="unreadOnly = true"
        >
          未读
        </button>
      </div>
      <select
        v-model="selectedType"
        class="notify-select h-10 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 text-sm text-[var(--text)] outline-none"
      >
        <option v-for="item in typeOptions" :key="item.value || 'all'" :value="item.value">
          {{ item.label }}
        </option>
      </select>
    </div>

    <div v-if="loading && !notifications.length" class="space-y-2">
      <div v-for="i in 3" :key="i" class="h-12 animate-pulse rounded-lg bg-[var(--surface-card)]"></div>
    </div>

    <p v-else-if="errorMessage" class="rounded-lg border border-[color:rgb(217_77_48_/_0.18)] bg-[var(--accent-soft)] p-3 text-xs text-[var(--accent)]">
      {{ errorMessage }}
    </p>

    <div v-else-if="visibleNotifications.length" class="space-y-2">
      <RouterLink
        v-for="item in visibleNotifications"
        :key="item.id"
        :to="notificationLink(item)"
        @click="markRead(item)"
        class="notification-item block rounded-lg border border-[var(--border)] p-3"
        :class="{ 'is-unread': !item.is_read }"
      >
        <div class="flex items-start gap-2">
          <span class="mt-1 h-1.5 w-1.5 shrink-0 rounded-full" :class="item.is_read ? 'bg-[var(--border)]' : 'bg-[var(--accent)]'"></span>
          <div class="min-w-0 flex-1">
            <div class="flex items-center justify-between gap-2">
              <p class="line-clamp-2 text-xs leading-5 text-[var(--text-secondary)]">{{ item.message }}</p>
              <span v-if="!compact" class="shrink-0 rounded-md bg-[var(--surface-elevated)] px-2 py-1 text-[11px] text-[var(--text-muted)]">
                {{ typeLabel(item.type) }}
              </span>
            </div>
            <p class="mt-1 text-[11px] text-[var(--text-muted)]">{{ formatTime(item.created_at) }}</p>
          </div>
        </div>
      </RouterLink>
    </div>

    <div v-else class="rounded-lg border border-dashed border-[var(--border)] p-5 text-center">
      <Inbox class="mx-auto h-5 w-5 text-[var(--text-muted)]" :stroke-width="1.8" aria-hidden="true" />
      <p class="mt-2 text-xs leading-5 text-[var(--text-muted)]">暂时没有通知。</p>
    </div>

    <div v-if="compact && total > 5" class="mt-3">
      <RouterLink
        to="/notifications"
        class="notify-action flex h-9 items-center justify-center rounded-lg border border-[var(--border)] text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
      >
        查看全部通知
      </RouterLink>
    </div>

    <button
      v-if="!compact && hasMore"
      class="notify-action mx-auto mt-4 flex h-10 items-center justify-center gap-2 rounded-lg border border-[var(--border)] px-4 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-60"
      type="button"
      :disabled="loading"
      @click="loadNotifications(page + 1, true)"
    >
      <Loader2 v-if="loading" class="h-4 w-4 animate-spin" :stroke-width="2" aria-hidden="true" />
      {{ loading ? '加载中' : '加载更多' }}
    </button>
  </section>
</template>

<style scoped>
.notification-center,
.notification-item,
.notify-action,
.filter-button,
.notify-select {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.notification-center {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 238, 211, 0.12)),
    var(--surface-panel);
}

.notification-item {
  background: rgba(255, 248, 235, 0.4);
  min-height: 4rem;
}

.notification-item.is-unread {
  border-color: rgba(217, 77, 48, 0.18);
  background: rgba(217, 77, 48, 0.08);
  box-shadow: inset 3px 0 0 var(--accent);
}

.notification-item:hover,
.notify-action:hover,
.filter-button:hover {
  transform: translateY(-1px);
}

.filter-button {
  color: var(--text-muted);
}

.filter-button.is-active {
  background: var(--text);
  border-color: var(--text);
  color: var(--surface);
}

.notify-select:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(217, 77, 48, 0.09);
}

@media (prefers-reduced-motion: reduce) {
  .notification-center,
  .notification-item,
  .notify-action,
  .filter-button,
  .notify-select {
    transition: none;
  }

  .notification-item:hover,
  .notify-action:hover,
  .filter-button:hover {
    transform: none;
  }
}
</style>
