<template>
  <AppShell
    class="timeline-page"
    content-width="wide"
    page-title="家庭今日"
    :page-description="`私有记忆中枢 · ${todayLabel}`"
  >
    <template #header>
      <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <div>
          <p class="text-xs font-medium uppercase tracking-[0.18em]" style="color:var(--text-muted)">
            哪吒家庭
          </p>
          <h1 class="mt-2 text-2xl font-semibold tracking-normal text-[var(--text)] sm:text-3xl">
            家庭今日
          </h1>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
            私有记忆中枢 · {{ todayLabel }}。最近动态、相册入口和家庭互动在这里聚合。
          </p>
        </div>
        <button
          @click="handleLogout"
          class="soft-button hidden rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] lg:inline-flex"
          type="button"
        >
          退出登录
        </button>
      </div>
    </template>

    <div class="space-y-5 lg:hidden">
        <div
          v-if="errorMessage"
          class="rounded-xl border px-4 py-3 text-sm"
          style="background:rgba(217,74,74,0.08);border-color:rgba(217,74,74,0.22);color:#ffaaaa"
        >
          {{ errorMessage }}
        </div>

        <section
          class="quick-publish rounded-xl border p-4 sm:p-5"
          style="background:var(--surface-card);border-color:var(--border)"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="min-w-0">
              <p class="text-xs font-medium uppercase tracking-[0.18em]" style="color:var(--text-muted)">
                今日家庭动态
              </p>
              <h1 class="mt-2 text-xl font-semibold tracking-tight sm:text-2xl" style="color:var(--text)">
                记录今天的小事
              </h1>
              <p class="mt-1 max-w-2xl text-sm leading-6" style="color:var(--text-secondary)">
                一张照片、一段视频，或者一句话，都可以留在家里的时间线上。
              </p>
            </div>
            <router-link
              to="/publish"
              class="primary-button inline-flex shrink-0 items-center justify-center rounded-lg px-4 py-2.5 text-sm font-medium active:scale-[0.98]"
              style="background:var(--text);color:var(--surface)"
            >
              快速发布
            </router-link>
          </div>

          <div class="mt-5 grid grid-cols-3 gap-3 border-t pt-4" style="border-color:var(--border)">
            <div>
              <p class="text-lg font-semibold leading-none" style="color:var(--text)">{{ posts.length }}</p>
              <p class="mt-1 text-xs" style="color:var(--text-muted)">条记忆</p>
            </div>
            <div>
              <p class="text-lg font-semibold leading-none" style="color:var(--text)">{{ mediaCount }}</p>
              <p class="mt-1 text-xs" style="color:var(--text-muted)">张影像</p>
            </div>
            <div>
              <p class="text-lg font-semibold leading-none" style="color:var(--text)">
                {{ memberNames.length || 1 }}
              </p>
              <p class="mt-1 text-xs" style="color:var(--text-muted)">位成员</p>
            </div>
          </div>
        </section>

        <div v-if="!isDesktop" class="lg:hidden">
          <NotificationCenter />
        </div>

        <section
          v-if="anniversaryPosts.length"
          class="anniversary-card rounded-xl border p-4 sm:p-5"
          style="background:var(--surface-card);border-color:var(--border)"
        >
          <div class="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.18em]" style="color:var(--text-muted)">
                On this day
              </p>
              <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">那年今日</h2>
              <p class="mt-1 text-sm leading-6 text-[var(--text-secondary)]">
                找到 {{ anniversaryPosts.length }} 条发生在今天附近的旧记忆。
              </p>
            </div>
            <router-link
              :to="`/post/${anniversaryPosts[0].id}`"
              class="primary-button inline-flex justify-center rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)]"
            >
              看一眼
            </router-link>
          </div>
        </section>

        <section
          class="memory-filter rounded-xl border p-4"
          style="background:var(--surface-panel);border-color:var(--border)"
        >
          <div class="grid gap-3 md:grid-cols-[minmax(0,1fr)_10rem_10rem]">
            <input
              v-model="searchKeyword"
              class="filter-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-muted)]"
              placeholder="搜索文字、家人、日期..."
            />
            <select
              v-model="selectedMember"
              class="filter-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
            >
              <option value="">全部成员</option>
              <option v-for="name in memberNames" :key="name" :value="name">{{ name }}</option>
            </select>
            <select
              v-model="mediaFilter"
              class="filter-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
            >
              <option value="all">全部类型</option>
              <option value="image">有照片</option>
              <option value="video">有视频</option>
              <option value="text">纯文字</option>
            </select>
          </div>
          <p class="mt-3 text-xs text-[var(--text-muted)]">
            当前显示 {{ filteredPosts.length }} / {{ posts.length }} 条记忆。
          </p>
        </section>

        <div v-if="loading" class="space-y-4">
          <div
            v-for="i in 3"
            :key="i"
            class="h-48 animate-pulse rounded-xl border"
            style="background:var(--surface-card);border-color:var(--border)"
          />
        </div>

        <section
          v-else-if="!filteredPosts.length"
          class="empty-state rounded-xl border p-6 sm:p-8"
          style="background:var(--surface-card);border-color:var(--border)"
        >
          <div class="grid gap-6 md:grid-cols-[1fr_220px] md:items-center">
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.18em]" style="color:var(--text-muted)">
                没有匹配的家庭动态
              </p>
              <h2 class="mt-3 text-2xl font-semibold tracking-tight" style="color:var(--text)">
                换个条件找找看
              </h2>
              <p class="mt-3 text-sm leading-6" style="color:var(--text-secondary)">
                可以清空关键词，或换一个成员、媒体类型继续找。
              </p>
              <router-link
                to="/publish"
                class="primary-button mt-6 inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-medium active:scale-[0.98]"
                style="background:var(--text);color:var(--surface)"
              >
                发布新记忆
              </router-link>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div class="memory-tile h-24 rounded-xl border" style="border-color:var(--border)" />
              <div class="memory-tile mt-6 h-24 rounded-xl border" style="border-color:var(--border)" />
              <div class="memory-tile col-span-2 h-20 rounded-xl border" style="border-color:var(--border)" />
            </div>
          </div>
        </section>

        <section v-else class="space-y-8">
          <div v-for="(group, groupIndex) in groupedPosts" :key="group.label" class="timeline-group space-y-3" :style="{ animationDelay: `${groupIndex * 0.05}s` }">
            <div class="date-divider flex items-center gap-3">
              <span class="text-xs font-medium" style="color:var(--text-secondary)">{{ group.label }}</span>
              <span class="h-px flex-1" style="background:var(--border)" />
              <span class="text-xs" style="color:var(--text-muted)">{{ group.posts.length }} 条</span>
            </div>
            <PostCard
              v-for="(p, i) in group.posts"
              :key="p.id"
              :post="p"
              :style="{ animationDelay: `${i * 0.04}s` }"
              @click="go"
              @like="like"
            />
          </div>
        </section>
    </div>

    <div class="hidden lg:block">
      <div
        v-if="errorMessage"
        class="mb-5 rounded-xl border px-4 py-3 text-sm"
        style="background:rgba(217,74,74,0.08);border-color:rgba(217,74,74,0.22);color:var(--accent)"
      >
        {{ errorMessage }}
      </div>

      <section class="desktop-archive rounded-xl border border-[var(--border)] bg-[var(--surface-card)] shadow-[var(--shadow-panel)]">
        <div class="desktop-archive__top border-b border-[var(--border)] p-5 xl:p-6">
          <div class="grid gap-5 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end">
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">
                Family archive
              </p>
              <h2 class="mt-2 text-2xl font-semibold tracking-normal text-[var(--text)]">
                家庭记忆档案
              </h2>
              <p class="mt-2 max-w-3xl text-sm leading-6 text-[var(--text-secondary)]">
                桌面端按批次浏览，筛选和概览固定在左侧，右侧专注看内容。
              </p>
            </div>
            <router-link
              to="/publish"
              class="primary-button inline-flex items-center justify-center rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)]"
            >
              快速发布
            </router-link>
          </div>

          <div class="mt-5 grid gap-3 xl:grid-cols-4">
            <article v-for="stat in desktopStats" :key="stat.label" class="desktop-stat rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
              <p class="text-xs text-[var(--text-muted)]">{{ stat.label }}</p>
              <p class="mt-2 text-2xl font-semibold leading-none text-[var(--text)]">{{ stat.value }}</p>
              <p class="mt-1 text-xs text-[var(--text-muted)]">{{ stat.meta }}</p>
            </article>
          </div>
        </div>

        <div class="grid min-h-[42rem] xl:grid-cols-[20rem_minmax(0,1fr)]">
          <aside class="desktop-archive__side border-b border-[var(--border)] p-5 xl:border-b-0 xl:border-r xl:p-6">
            <section class="space-y-4">
              <div>
                <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Filters</p>
                <h3 class="mt-2 text-lg font-semibold text-[var(--text)]">筛选记忆</h3>
              </div>
              <div class="space-y-3">
                <input
                  v-model="searchKeyword"
                  class="filter-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-muted)]"
                  placeholder="搜索文字、家人、日期..."
                />
                <select
                  v-model="selectedMember"
                  class="filter-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
                >
                  <option value="">全部成员</option>
                  <option v-for="name in memberNames" :key="name" :value="name">{{ name }}</option>
                </select>
                <select
                  v-model="mediaFilter"
                  class="filter-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
                >
                  <option value="all">全部类型</option>
                  <option value="image">有照片</option>
                  <option value="video">有视频</option>
                  <option value="text">纯文字</option>
                </select>
              </div>
              <button
                @click="resetFilters"
                class="soft-button w-full rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]"
                type="button"
              >
                清空筛选
              </button>
            </section>

            <section v-if="anniversaryPosts.length" class="mt-7 rounded-xl border border-[var(--border)] bg-[var(--surface-panel)] p-4">
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">On this day</p>
              <h3 class="mt-2 text-base font-semibold text-[var(--text)]">那年今日</h3>
              <p class="mt-2 text-sm leading-6 text-[var(--text-secondary)]">
                找到 {{ anniversaryPosts.length }} 条旧记忆。
              </p>
              <router-link
                :to="`/post/${anniversaryPosts[0].id}`"
                class="context-link mt-3"
              >
                看一眼
              </router-link>
            </section>

            <section class="mt-7">
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Members</p>
              <div class="mt-4 space-y-2">
                <button
                  v-for="name in memberNames"
                  :key="name"
                  @click="selectedMember = name"
                  class="member-filter-row flex w-full items-center gap-3 rounded-lg border border-transparent px-2 py-2 text-left"
                  type="button"
                >
                  <span class="grid h-8 w-8 place-items-center rounded-lg bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]">
                    {{ initial(name) }}
                  </span>
                  <span class="min-w-0">
                    <span class="block truncate text-sm font-medium text-[var(--text)]">{{ name }}</span>
                    <span class="text-xs text-[var(--text-muted)]">{{ roleFor(name) }}</span>
                  </span>
                </button>
              </div>
            </section>
          </aside>

          <section class="desktop-archive__content min-w-0 p-5 xl:p-6">
            <div class="mb-5 flex flex-col gap-3 border-b border-[var(--border)] pb-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p class="text-sm font-medium text-[var(--text)]">
                  当前显示 {{ pagedPosts.length }} / {{ filteredPosts.length }} 条记忆
                </p>
                <p class="mt-1 text-xs text-[var(--text-muted)]">
                  第 {{ currentPage }} / {{ totalPages }} 页
                </p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  @click="previousPage"
                  :disabled="currentPage <= 1"
                  class="soft-button rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] disabled:opacity-40"
                  type="button"
                >
                  上一页
                </button>
                <button
                  @click="nextPage"
                  :disabled="currentPage >= totalPages"
                  class="soft-button rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] disabled:opacity-40"
                  type="button"
                >
                  下一页
                </button>
              </div>
            </div>

            <div v-if="loading" class="grid gap-4 xl:grid-cols-2">
              <div
                v-for="i in 4"
                :key="i"
                class="h-72 animate-pulse rounded-xl border border-[var(--border)] bg-[var(--surface-panel)]"
              />
            </div>

            <section
              v-else-if="!filteredPosts.length"
              class="empty-state rounded-xl border border-[var(--border)] bg-[var(--surface-panel)] p-8"
            >
              <h3 class="text-xl font-semibold text-[var(--text)]">没有匹配的家庭动态</h3>
              <p class="mt-3 text-sm leading-6 text-[var(--text-secondary)]">
                可以清空筛选，或换一个成员、媒体类型继续找。
              </p>
            </section>

            <div v-else class="grid gap-4 2xl:grid-cols-2">
              <PostCard
                v-for="post in pagedPosts"
                :key="post.id"
                :post="post"
                @click="go"
                @like="like"
              />
            </div>
          </section>
        </div>
      </section>
    </div>

    <template #right>
      <div class="space-y-4">
        <RightRail>
          <template #header>
            <div class="flex items-center justify-between">
              <h2 class="text-sm font-semibold" style="color:var(--text)">家庭概览</h2>
              <span class="rounded-md px-2 py-1 text-xs" style="background:rgba(255,255,255,0.05);color:var(--text-muted)">
                本月
              </span>
            </div>
          </template>
          <div class="space-y-4">
            <div class="rail-stat flex items-center justify-between text-sm">
              <span style="color:var(--text-secondary)">新增动态</span>
              <strong style="color:var(--text)">{{ postsThisMonth }}</strong>
            </div>
            <div class="rail-stat flex items-center justify-between text-sm">
              <span style="color:var(--text-secondary)">照片/视频</span>
              <strong style="color:var(--text)">{{ mediaCount }}</strong>
            </div>
            <div class="rail-stat flex items-center justify-between text-sm">
              <span style="color:var(--text-secondary)">最近互动</span>
              <strong style="color:var(--text)">{{ interactionCount }}</strong>
            </div>
          </div>
        </RightRail>

        <NotificationCenter v-if="isDesktop" />

        <RightRail title="最近家人">
          <div class="space-y-3">
            <div v-for="name in memberNames" :key="name" class="member-row flex items-center gap-3">
              <span
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold"
                style="background:rgba(255,255,255,0.06);color:var(--text-secondary)"
              >
                {{ initial(name) }}
              </span>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium" style="color:var(--text)">{{ name }}</p>
                <p class="text-xs" style="color:var(--text-muted)">{{ roleFor(name) }}</p>
              </div>
            </div>
            <p v-if="!memberNames.length" class="text-sm leading-6" style="color:var(--text-muted)">
              第一条动态发布后，这里会显示参与记录的家人。
            </p>
          </div>
        </RightRail>

        <RightRail title="记忆入口">
          <div class="grid gap-2">
            <router-link to="/publish" class="context-link">写一条今天的变化</router-link>
            <router-link to="/albums" class="context-link">查看最近照片</router-link>
            <router-link to="/calendar" class="context-link">整理家庭日历</router-link>
          </div>
        </RightRail>
      </div>
    </template>

  </AppShell>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { getPosts, togglePostLike, type Post } from '@/api/posts'
import AppShell from '@/components/AppShell.vue'
import NotificationCenter from '@/components/NotificationCenter.vue'
import PostCard from '@/components/PostCard.vue'
import RightRail from '@/components/RightRail.vue'

interface PostGroup {
  label: string
  posts: Post[]
}

const router = useRouter()
const { logout } = useAuth()
const posts = ref<Post[]>([])
const loading = ref(false)
const errorMessage = ref('')
const searchKeyword = ref('')
const selectedMember = ref('')
const mediaFilter = ref<'all' | 'image' | 'video' | 'text'>('all')
const isDesktop = ref(false)
const currentPage = ref(1)
const desktopPageSize = 8
let desktopMediaQuery: MediaQueryList | null = null

const todayLabel = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'short',
}).format(new Date())

const mediaCount = computed(() =>
  posts.value.reduce((count, post) => count + (post.media_urls?.length ?? 0), 0),
)

const interactionCount = computed(() =>
  posts.value.reduce((count, post) => count + post.like_count + post.comment_count, 0),
)

const desktopStats = computed(() => [
  { label: '全部记忆', value: posts.value.length, meta: '时间线动态' },
  { label: '影像', value: mediaCount.value, meta: '照片和视频' },
  { label: '互动', value: interactionCount.value, meta: '点赞与评论' },
  { label: '本月', value: postsThisMonth.value, meta: '新增动态' },
])

const postsThisMonth = computed(() => {
  const now = new Date()
  return posts.value.filter((post) => {
    const date = new Date(post.created_at)
    return date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth()
  }).length
})

const memberNames = computed(() => {
  const names = new Set<string>()
  posts.value.forEach((post) => names.add(post.author_username))
  return Array.from(names).slice(0, 5)
})

const filteredPosts = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  return posts.value.filter((post) => {
    const matchesKeyword = !keyword
      || post.content?.toLowerCase().includes(keyword)
      || post.author_username.toLowerCase().includes(keyword)
      || new Date(post.created_at).toLocaleDateString('zh-CN').includes(keyword)

    const matchesMember = !selectedMember.value || post.author_username === selectedMember.value

    const hasImage = post.media_urls?.some((media) => media.type === 'image')
    const hasVideo = post.media_urls?.some((media) => media.type === 'video')
    const matchesMedia =
      mediaFilter.value === 'all'
      || (mediaFilter.value === 'image' && hasImage)
      || (mediaFilter.value === 'video' && hasVideo)
      || (mediaFilter.value === 'text' && !post.media_urls?.length)

    return matchesKeyword && matchesMember && matchesMedia
  })
})

const anniversaryPosts = computed(() => {
  const now = new Date()
  return posts.value
    .filter((post) => {
      const date = new Date(post.created_at)
      return date.getFullYear() !== now.getFullYear()
        && date.getMonth() === now.getMonth()
        && Math.abs(date.getDate() - now.getDate()) <= 3
    })
    .slice(0, 3)
})

const groupedPosts = computed<PostGroup[]>(() => {
  const groups = new Map<string, Post[]>()
  filteredPosts.value.forEach((post) => {
    const label = dateGroupLabel(post.created_at)
    const group = groups.get(label) ?? []
    group.push(post)
    groups.set(label, group)
  })
  return Array.from(groups, ([label, groupPosts]) => ({ label, posts: groupPosts }))
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredPosts.value.length / desktopPageSize)))
const pagedPosts = computed(() => {
  const start = (currentPage.value - 1) * desktopPageSize
  return filteredPosts.value.slice(start, start + desktopPageSize)
})

watch([searchKeyword, selectedMember, mediaFilter], () => {
  currentPage.value = 1
})

onMounted(async () => {
  setupViewportWatcher()
  loading.value = true
  try {
    posts.value = (await getPosts(1, 50)).posts
  } catch (e) {
    errorMessage.value = typeof e === 'string' ? e : '加载失败'
  }
  loading.value = false
})

onBeforeUnmount(() => {
  desktopMediaQuery?.removeEventListener('change', syncDesktopState)
})

function go(id: string) {
  router.push(`/post/${id}`)
}

async function like(p: Post) {
  try {
    const r = await togglePostLike(p.id)
    p.is_liked = r.liked
    p.like_count = r.like_count
  } catch (e) {
    errorMessage.value = typeof e === 'string' ? e : '操作失败'
  }
}

function handleLogout() {
  logout()
  router.push('/login')
}

function resetFilters() {
  searchKeyword.value = ''
  selectedMember.value = ''
  mediaFilter.value = 'all'
}

function previousPage() {
  currentPage.value = Math.max(1, currentPage.value - 1)
}

function nextPage() {
  currentPage.value = Math.min(totalPages.value, currentPage.value + 1)
}

function dateGroupLabel(value: string): string {
  const date = new Date(value)
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)

  if (sameDate(date, today)) return '今天'
  if (sameDate(date, yesterday)) return '昨天'
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  }).format(date)
}

function sameDate(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

function initial(name: string): string {
  return name.trim().slice(0, 1).toUpperCase() || '家'
}

function roleFor(name: string): string {
  const roles = ['记录者', '照片守护者', '故事补充员', '家庭成员', '最近活跃']
  const sum = Array.from(name).reduce((total, char) => total + char.charCodeAt(0), 0)
  return roles[sum % roles.length]
}

function setupViewportWatcher() {
  desktopMediaQuery = window.matchMedia('(min-width: 1024px)')
  syncDesktopState()
  desktopMediaQuery.addEventListener('change', syncDesktopState)
}

function syncDesktopState(event?: MediaQueryListEvent) {
  isDesktop.value = event ? event.matches : Boolean(desktopMediaQuery?.matches)
}
</script>

<style scoped>
.timeline-page {
  background:
    linear-gradient(180deg, rgba(255, 255, 252, 0.4) 0%, rgba(246, 241, 232, 0) 340px),
    transparent;
}

.soft-button,
.primary-button,
.quick-publish,
.anniversary-card,
.memory-filter,
.desktop-archive,
.desktop-stat,
.member-filter-row,
.filter-input,
.empty-state,
.context-link,
.member-row,
.rail-stat,
.date-divider {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    box-shadow 180ms ease,
    opacity 180ms ease,
    transform 180ms ease;
}

.soft-button:hover,
.primary-button:hover {
  transform: translateY(-1px);
}

.primary-button:hover {
  box-shadow: 0 10px 26px rgba(201, 67, 47, 0.14);
}

.nav-link {
  border-radius: 8px;
  color: var(--text-secondary);
  flex-shrink: 0;
  font-size: 0.875rem;
  line-height: 1.25rem;
  padding: 0.5rem 0.75rem;
  transition: background-color 160ms ease, color 160ms ease;
}

.nav-link:hover,
.context-link:hover {
  background: rgba(201, 67, 47, 0.08);
  color: var(--text);
}

.publish-link {
  align-items: center;
  background: var(--text);
  border-radius: 8px;
  color: var(--surface);
  display: inline-flex;
  flex-shrink: 0;
  font-size: 0.875rem;
  font-weight: 600;
  justify-content: center;
  line-height: 1.25rem;
  padding: 0.5rem 0.9rem;
  transition: transform 160ms ease, opacity 160ms ease;
}

.publish-link:active {
  transform: scale(0.98);
}

.quick-publish,
.empty-state {
  box-shadow: 0 18px 45px rgba(47, 39, 35, 0.09);
}

.desktop-archive {
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.36), rgba(45, 108, 104, 0.05)),
    var(--surface-card);
}

.desktop-archive__top {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.24), rgba(201, 67, 47, 0.04));
}

.desktop-archive__side {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(45, 108, 104, 0.05)),
    var(--surface-panel);
}

.desktop-archive__content {
  background: rgba(255, 255, 252, 0.18);
}

.desktop-stat:hover,
.member-filter-row:hover {
  border-color: rgba(201, 67, 47, 0.16);
  box-shadow: 0 14px 34px rgba(47, 39, 35, 0.08);
  transform: translateY(-1px);
}

.member-filter-row:hover {
  background: rgba(201, 67, 47, 0.07);
}

.quick-publish {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.36), rgba(45, 108, 104, 0.08)),
    var(--surface-card) !important;
}

.anniversary-card,
.memory-filter {
  position: relative;
}

.anniversary-card {
  background:
    linear-gradient(135deg, rgba(201, 67, 47, 0.08), rgba(255, 255, 255, 0.34)),
    var(--surface-card) !important;
  overflow: hidden;
}

.anniversary-card::after {
  animation: anniversary-ring 10s linear infinite;
  background: conic-gradient(from 20deg, rgba(201, 67, 47, 0.14), rgba(45, 108, 104, 0.16), rgba(66, 81, 132, 0.12), rgba(201, 67, 47, 0.14));
  border-radius: 999px;
  content: '';
  height: 7rem;
  opacity: 0.44;
  pointer-events: none;
  position: absolute;
  right: -2rem;
  top: -2rem;
  width: 7rem;
}

.memory-filter {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 238, 211, 0.08)),
    var(--surface-panel) !important;
}

.filter-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.quick-publish:hover,
.anniversary-card:hover,
.memory-filter:hover,
.empty-state:hover {
  border-color: rgba(201, 67, 47, 0.16) !important;
  box-shadow: 0 22px 54px rgba(47, 39, 35, 0.12);
  transform: translateY(-1px);
}

.memory-tile {
  background:
    linear-gradient(135deg, rgba(201, 67, 47, 0.12), rgba(45, 108, 104, 0.1)),
    rgba(255, 255, 252, 0.36);
}

.context-link {
  border-radius: 8px;
  color: var(--text-secondary);
  display: block;
  font-size: 0.875rem;
  line-height: 1.25rem;
  padding: 0.625rem 0.75rem;
  transition: background-color 160ms ease, color 160ms ease;
}

.desktop-archive .context-link {
  border: 1px solid var(--border);
  background: var(--surface-card);
}

.timeline-group {
  animation: timeline-group-in 360ms ease-out both;
}

.date-divider:hover {
  opacity: 0.9;
}

.member-row {
  border-radius: 8px;
  margin: -0.25rem;
  padding: 0.25rem;
}

.member-row:hover,
.rail-stat:hover {
  transform: translateX(2px);
}

.rail-stat {
  border-radius: 8px;
  margin: -0.35rem;
  padding: 0.35rem;
}

.rail-stat:hover {
  background: rgba(255, 244, 232, 0.04);
}

@keyframes timeline-group-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes anniversary-ring {
  to {
    transform: rotate(1turn);
  }
}

@media (prefers-reduced-motion: reduce) {
  .soft-button,
  .primary-button,
    .quick-publish,
    .anniversary-card,
    .anniversary-card::after,
    .memory-filter,
    .desktop-archive,
    .desktop-stat,
    .member-filter-row,
    .filter-input,
    .empty-state,
  .context-link,
  .member-row,
  .rail-stat,
  .date-divider {
    transition: none;
  }

  .timeline-group {
    animation: none;
  }

  .soft-button:hover,
  .primary-button:hover,
  .quick-publish:hover,
  .anniversary-card:hover,
  .memory-filter:hover,
  .desktop-stat:hover,
  .member-filter-row:hover,
  .empty-state:hover,
  .member-row:hover,
  .rail-stat:hover {
    transform: none;
  }
}
</style>
