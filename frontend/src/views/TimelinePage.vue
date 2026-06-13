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
              <p class="text-lg font-semibold leading-none" style="color:var(--text)">{{ totalPostCount }}</p>
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
          <div class="mb-3 flex items-center justify-between gap-3">
            <p class="text-sm font-semibold text-[var(--text)]">筛选记忆</p>
            <button
              @click="resetFilters"
              :disabled="!hasActiveFilters"
              class="soft-button rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] disabled:opacity-40"
              type="button"
            >
              清空筛选
            </button>
          </div>
          <div class="grid gap-3 sm:grid-cols-2">
            <input
              v-model="searchKeyword"
              class="filter-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none placeholder:text-[var(--text-muted)] sm:col-span-2"
              placeholder="搜索文字、家人..."
            />
            <select
              v-model="selectedAuthorId"
              class="filter-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
            >
              <option value="">全部成员</option>
              <option v-for="member in memberOptions" :key="member.id" :value="member.id">{{ member.name }}</option>
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
            <input
              v-model="dateFrom"
              type="date"
              class="filter-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
              aria-label="开始日期"
            />
            <input
              v-model="dateTo"
              type="date"
              class="filter-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
              aria-label="结束日期"
            />
          </div>
          <p class="mt-3 text-xs leading-5 text-[var(--text-muted)]">
            {{ filterSummary }} · 当前显示 {{ posts.length }} / {{ totalPostCount }} 条记忆。
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
          v-else-if="!posts.length"
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
              <div class="mt-6 flex flex-wrap gap-2">
                <button
                  v-if="hasActiveFilters"
                  @click="resetFilters"
                  class="soft-button inline-flex items-center justify-center rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm text-[var(--text-secondary)]"
                  type="button"
                >
                  清空筛选
                </button>
                <router-link
                  to="/publish"
                  class="primary-button inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-medium active:scale-[0.98]"
                  style="background:var(--text);color:var(--surface)"
                >
                  发布新记忆
                </router-link>
              </div>
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
          <div v-if="hasMore" class="flex justify-center pt-2">
            <button
              @click="loadMorePosts"
              :disabled="loadingMore"
              class="soft-button inline-flex min-w-28 items-center justify-center rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm text-[var(--text-secondary)] disabled:opacity-40"
              type="button"
            >
              {{ loadingMore ? '加载中' : '加载更多' }}
            </button>
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
                  placeholder="搜索文字、家人..."
                />
                <select
                  v-model="selectedAuthorId"
                  class="filter-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
                >
                  <option value="">全部成员</option>
                  <option v-for="member in memberOptions" :key="member.id" :value="member.id">{{ member.name }}</option>
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
                <div class="grid grid-cols-2 gap-2">
                  <input
                    v-model="dateFrom"
                    type="date"
                    class="filter-input min-w-0 rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
                    aria-label="开始日期"
                  />
                  <input
                    v-model="dateTo"
                    type="date"
                    class="filter-input min-w-0 rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
                    aria-label="结束日期"
                  />
                </div>
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
            <section class="mt-7 rounded-xl border border-[var(--border)] bg-[var(--surface-panel)] p-4">
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Current</p>
              <h3 class="mt-2 text-base font-semibold text-[var(--text)]">当前筛选</h3>
              <p class="mt-2 text-sm leading-6 text-[var(--text-secondary)]">{{ filterSummary }}</p>
            </section>

            <section class="mt-7">
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Members</p>
              <div class="mt-4 space-y-2">
                <button
                  v-for="member in memberOptions"
                  :key="member.id"
                  @click="selectedAuthorId = member.id"
                  class="member-filter-row flex w-full items-center gap-3 rounded-lg border border-transparent px-2 py-2 text-left"
                  type="button"
                >
                  <span class="grid h-8 w-8 place-items-center rounded-lg bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]">
                    {{ initial(member.name) }}
                  </span>
                  <span class="min-w-0">
                    <span class="block truncate text-sm font-medium text-[var(--text)]">{{ member.name }}</span>
                    <span class="text-xs text-[var(--text-muted)]">{{ roleFor(member.name) }}</span>
                  </span>
                </button>
              </div>
            </section>
          </aside>

          <section class="desktop-archive__content min-w-0 p-5 xl:p-6">
            <div class="mb-5 flex flex-col gap-3 border-b border-[var(--border)] pb-4 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <p class="text-sm font-medium text-[var(--text)]">
                  当前显示 {{ pagedPosts.length }} / {{ totalPostCount }} 条记忆
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
              v-else-if="!pagedPosts.length"
              class="empty-state rounded-xl border border-[var(--border)] bg-[var(--surface-panel)] p-8"
            >
              <h3 class="text-xl font-semibold text-[var(--text)]">没有匹配的家庭动态</h3>
              <p class="mt-3 text-sm leading-6 text-[var(--text-secondary)]">
                可以清空筛选，或换一个成员、媒体类型继续找。
              </p>
              <button
                v-if="hasActiveFilters"
                @click="resetFilters"
                class="soft-button mt-5 rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)]"
                type="button"
              >
                清空筛选
              </button>
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
            <div v-for="member in memberOptions" :key="member.id" class="member-row flex items-center gap-3">
              <span
                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-sm font-semibold"
                style="background:rgba(255,255,255,0.06);color:var(--text-secondary)"
              >
                {{ initial(member.name) }}
              </span>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium" style="color:var(--text)">{{ member.name }}</p>
                <p class="text-xs" style="color:var(--text-muted)">{{ roleFor(member.name) }}</p>
              </div>
            </div>
            <p v-if="!memberOptions.length" class="text-sm leading-6" style="color:var(--text-muted)">
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
import { getPosts, togglePostLike, type Post, type PostListParams } from '@/api/posts'
import AppShell from '@/components/AppShell.vue'
import NotificationCenter from '@/components/NotificationCenter.vue'
import PostCard from '@/components/PostCard.vue'
import RightRail from '@/components/RightRail.vue'

interface PostGroup {
  label: string
  posts: Post[]
}

interface MemberOption {
  id: string
  name: string
}

const router = useRouter()
const { logout } = useAuth()
const posts = ref<Post[]>([])
const loading = ref(false)
const loadingMore = ref(false)
const errorMessage = ref('')
const searchKeyword = ref('')
const debouncedSearchKeyword = ref('')
const selectedAuthorId = ref('')
const mediaFilter = ref<'all' | 'image' | 'video' | 'text'>('all')
const dateFrom = ref('')
const dateTo = ref('')
const isDesktop = ref(false)
const currentPage = ref(1)
const totalPostCount = ref(0)
const hasMore = ref(false)
const memberMap = ref<Record<string, MemberOption>>({})
const desktopPageSize = 8
const mobilePageSize = 20
let desktopMediaQuery: MediaQueryList | null = null
let searchDebounceTimer: number | undefined
let requestSerial = 0
let suppressPageWatch = false
let hasLoadedInitialPosts = false

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
  { label: '全部记忆', value: totalPostCount.value, meta: '时间线动态' },
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

const memberOptions = computed(() =>
  Object.values(memberMap.value)
    .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
    .slice(0, 12)
)

const memberNames = computed(() => memberOptions.value.map((member) => member.name))

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
  posts.value.forEach((post) => {
    const label = dateGroupLabel(post.created_at)
    const group = groups.get(label) ?? []
    group.push(post)
    groups.set(label, group)
  })
  return Array.from(groups, ([label, groupPosts]) => ({ label, posts: groupPosts }))
})

const pageSize = computed(() => isDesktop.value ? desktopPageSize : mobilePageSize)
const totalPages = computed(() => Math.max(1, Math.ceil(totalPostCount.value / pageSize.value)))
const pagedPosts = computed(() => posts.value)
const hasActiveFilters = computed(() =>
  Boolean(
    searchKeyword.value.trim()
    || debouncedSearchKeyword.value
    || selectedAuthorId.value
    || mediaFilter.value !== 'all'
    || dateFrom.value
    || dateTo.value
  )
)
const filterSummary = computed(() => {
  const parts: string[] = []
  if (debouncedSearchKeyword.value || searchKeyword.value.trim()) {
    parts.push(`关键词「${debouncedSearchKeyword.value || searchKeyword.value.trim()}」`)
  }
  const member = memberOptions.value.find((item) => item.id === selectedAuthorId.value)
  if (member) parts.push(`成员「${member.name}」`)
  if (mediaFilter.value !== 'all') {
    const labels = { image: '照片', video: '视频', text: '纯文字' }
    parts.push(labels[mediaFilter.value])
  }
  if (dateFrom.value || dateTo.value) {
    parts.push(`${dateFrom.value || '不限'} 至 ${dateTo.value || '不限'}`)
  }
  return parts.length ? parts.join(' · ') : '未设置筛选'
})

watch(searchKeyword, () => {
  if (searchDebounceTimer) {
    window.clearTimeout(searchDebounceTimer)
  }
  searchDebounceTimer = window.setTimeout(() => {
    debouncedSearchKeyword.value = searchKeyword.value.trim()
  }, 320)
})

watch([debouncedSearchKeyword, selectedAuthorId, mediaFilter, dateFrom, dateTo], () => {
  void loadPosts({ reset: true })
})

watch(currentPage, () => {
  if (suppressPageWatch) {
    suppressPageWatch = false
    return
  }
  if (isDesktop.value) {
    void loadPosts({ reset: false })
  }
})

watch(pageSize, () => {
  if (hasLoadedInitialPosts) {
    void loadPosts({ reset: true })
  }
})

onMounted(() => {
  setupViewportWatcher()
  void loadPosts({ reset: true })
})

onBeforeUnmount(() => {
  desktopMediaQuery?.removeEventListener('change', syncDesktopState)
  if (searchDebounceTimer) {
    window.clearTimeout(searchDebounceTimer)
  }
})

async function loadPosts({ reset, page }: { reset: boolean; page?: number }) {
  const requestedPage = page ?? (reset ? 1 : currentPage.value)
  const serial = ++requestSerial
  if (reset) {
    if (currentPage.value !== 1) {
      suppressPageWatch = true
      currentPage.value = 1
    }
    loading.value = true
  } else if (!isDesktop.value) {
    loadingMore.value = true
  } else {
    loading.value = true
  }
  errorMessage.value = ''

  try {
    const params = buildPostParams(requestedPage)
    const response = await getPosts(params)
    if (serial !== requestSerial) return

    posts.value = !isDesktop.value && !reset
      ? mergePosts(posts.value, response.posts)
      : response.posts
    totalPostCount.value = response.total
    hasMore.value = response.has_more
    if (currentPage.value !== response.page) {
      suppressPageWatch = true
      currentPage.value = response.page
    }
    rememberMembers(response.posts)
  } catch (e) {
    if (serial === requestSerial) {
      errorMessage.value = typeof e === 'string' ? e : '加载失败'
    }
  } finally {
    if (serial === requestSerial) {
      loading.value = false
      loadingMore.value = false
      hasLoadedInitialPosts = true
    }
  }
}

function buildPostParams(page: number): PostListParams {
  return {
    page,
    page_size: pageSize.value,
    q: debouncedSearchKeyword.value || undefined,
    author_id: selectedAuthorId.value || undefined,
    type: mediaFilter.value === 'all' ? undefined : mediaFilter.value,
    date_from: dateFrom.value || undefined,
    date_to: dateTo.value || undefined,
  }
}

function rememberMembers(items: Post[]) {
  if (!items.length) return
  const nextMembers = { ...memberMap.value }
  items.forEach((post) => {
    nextMembers[post.author_id] = {
      id: post.author_id,
      name: post.author_username,
    }
  })
  memberMap.value = nextMembers
}

function mergePosts(current: Post[], incoming: Post[]): Post[] {
  const seen = new Set(current.map((post) => post.id))
  return [
    ...current,
    ...incoming.filter((post) => !seen.has(post.id)),
  ]
}

async function loadMorePosts() {
  if (loadingMore.value || loading.value || !hasMore.value) return
  await loadPosts({ reset: false, page: currentPage.value + 1 })
}

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

async function handleLogout() {
  await logout()
  router.push('/login')
}

function resetFilters() {
  const shouldReloadFirstPage =
    currentPage.value !== 1
    && !searchKeyword.value
    && !debouncedSearchKeyword.value
    && !selectedAuthorId.value
    && mediaFilter.value === 'all'
    && !dateFrom.value
    && !dateTo.value

  searchKeyword.value = ''
  debouncedSearchKeyword.value = ''
  selectedAuthorId.value = ''
  mediaFilter.value = 'all'
  dateFrom.value = ''
  dateTo.value = ''

  if (shouldReloadFirstPage) {
    void loadPosts({ reset: true })
  }
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
