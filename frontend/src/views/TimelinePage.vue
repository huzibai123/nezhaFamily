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
          <p class="text-xs font-medium uppercase tracking-normal" style="color:var(--text-muted)">
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

    <div class="space-y-5" :class="useImmersiveLayout ? '' : 'lg:hidden'">
        <div
          v-if="errorMessage"
          class="rounded-xl border px-4 py-3 text-sm"
          style="background:rgba(217,74,74,0.08);border-color:rgba(217,74,74,0.22);color:#ffaaaa"
        >
          {{ errorMessage }}
        </div>

        <section
          v-if="!useImmersiveLayout"
          class="quick-publish rounded-xl border p-4 sm:p-5"
          style="background:var(--surface-card);border-color:var(--border)"
        >
          <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div class="min-w-0">
              <p class="text-xs font-medium uppercase tracking-normal" style="color:var(--text-muted)">
                今日家庭动态
              </p>
              <h1 class="mt-2 text-xl font-semibold tracking-normal sm:text-2xl" style="color:var(--text)">
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

        <div v-if="!isDesktop && !useImmersiveLayout" class="lg:hidden">
          <NotificationCenter />
        </div>

        <section
          v-if="!useImmersiveLayout && anniversaryPosts.length"
          class="anniversary-card rounded-xl border p-4 sm:p-5"
          style="background:var(--surface-card);border-color:var(--border)"
        >
          <div class="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
            <div>
              <p class="text-xs font-medium uppercase tracking-normal" style="color:var(--text-muted)">
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
          v-if="!useImmersiveLayout"
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
              <p class="text-xs font-medium uppercase tracking-normal" style="color:var(--text-muted)">
                没有匹配的家庭动态
              </p>
              <h2 class="mt-3 text-2xl font-semibold tracking-normal" style="color:var(--text)">
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
          <template v-if="layoutMode === 'default'">
            <div
              v-for="(group, groupIndex) in groupedPosts"
              :key="group.label"
              class="timeline-group space-y-3"
              :style="{ animationDelay: `${groupIndex * 0.05}s` }"
            >
              <div class="date-divider flex items-center gap-3">
                <span class="text-xs font-medium" style="color:var(--text-secondary)">{{ group.label }}</span>
                <span class="h-px flex-1" style="background:var(--border)" />
                <span class="text-xs" style="color:var(--text-muted)">{{ group.posts.length }} 条</span>
              </div>
              <div class="timeline-group__items" :style="{ display: 'flex', flexDirection: 'column', gap: 'var(--card-gap, 20px)' }">
                <PostCard
                  v-for="(p, i) in group.posts"
                  :key="p.id"
                  :post="p"
                  layout-mode="default"
                  :style="{ animationDelay: `${i * 0.04}s` }"
                  @click="go"
                  @like="like"
                />
              </div>
            </div>
          </template>

          <div v-else-if="layoutMode === 'single-dark'" class="cinema-stage">
            <article
              v-if="featuredPost"
              class="cinema-hero"
              @click="go(featuredPost.id)"
            >
              <div class="cinema-hero__media">
                <video
                  v-if="featuredMedia?.type === 'video'"
                  :src="mediaSource(featuredMedia.url)"
                  controls
                  preload="metadata"
                  @click.stop
                />
                <img
                  v-else-if="featuredMedia"
                  :src="mediaSource(featuredMedia.url)"
                  alt=""
                  loading="lazy"
                />
                <div v-else class="cinema-hero__empty">
                  {{ excerpt(featuredPost.content, 80) || '家庭影像' }}
                </div>
              </div>
              <div class="cinema-hero__copy">
                <p class="cinema-kicker">影像剧场</p>
                <h1>{{ excerpt(featuredPost.content, 72) || '今天的主画面' }}</h1>
                <div class="cinema-meta">
                  <span>{{ featuredPost.author_username }}</span>
                  <span>{{ displayDate(featuredPost.created_at) }}</span>
                  <span>{{ featuredPost.like_count }} 赞</span>
                </div>
              </div>
            </article>

            <div class="cinema-strip" aria-label="最近影像">
              <button
                v-for="post in secondaryPosts.slice(0, 6)"
                :key="post.id"
                class="cinema-strip__item"
                type="button"
                @click="go(post.id)"
              >
                <img
                  v-if="primaryMedia(post)"
                  :src="mediaSource(primaryMedia(post)!.url)"
                  alt=""
                  loading="lazy"
                />
                <span v-else>{{ excerpt(post.content, 18) || '文字记忆' }}</span>
              </button>
            </div>
          </div>

          <template v-else-if="layoutMode === 'timeline'">
            <section class="chronicle-board">
              <header class="chronicle-cover">
                <p>成长年轮</p>
                <h1>{{ timelineYearLabel }}</h1>
                <span>{{ totalPostCount }} 条家庭记忆</span>
              </header>
              <div class="chronicle-years">
                <article
                  v-for="(group, groupIndex) in groupedPosts"
                  :key="group.label"
                  class="chronicle-section"
                  :style="{ '--index': groupIndex }"
                >
                  <div class="chronicle-date">
                    <CalendarDays :size="20" stroke-width="1.7" aria-hidden="true" />
                    <strong>{{ group.label }}</strong>
                    <span>{{ group.posts.length }} 条</span>
                  </div>
                  <div class="chronicle-stack">
                    <button
                      v-for="post in group.posts"
                      :key="post.id"
                      class="chronicle-card"
                      type="button"
                      @click="go(post.id)"
                    >
                      <span>{{ displayDate(post.created_at) }}</span>
                      <strong>{{ excerpt(post.content, 48) || '家庭影像' }}</strong>
                      <small>{{ post.author_username }} / {{ post.comment_count }} 评论</small>
                    </button>
                  </div>
                </article>
              </div>
            </section>
          </template>

          <div
            v-else-if="layoutMode === 'grid'"
            class="photo-wall-grid"
          >
            <header class="photo-wall-header">
              <h1>照片墙</h1>
              <p>{{ mediaCount }} 张影像 / {{ totalPostCount }} 条记忆</p>
            </header>
            <button
              v-for="(post, i) in posts"
              :key="post.id"
              class="photo-tile"
              :class="[`photo-tile--${(i % 8) + 1}`, { 'photo-tile--text': !primaryMedia(post) }]"
              type="button"
              @click="go(post.id)"
            >
              <img
                v-if="primaryMedia(post)"
                :src="mediaSource(primaryMedia(post)!.url)"
                alt=""
                loading="lazy"
              />
              <span v-else>{{ excerpt(post.content, 32) || '文字记忆' }}</span>
            </button>
          </div>

          <div
            v-else-if="layoutMode === 'masonry'"
            class="magazine-layout"
          >
            <header class="magazine-header">
              <div>
                <p>家书杂志</p>
                <h1>今天的家庭小刊</h1>
              </div>
              <dl class="magazine-summary" aria-label="本期概览">
                <div>
                  <dt>日期</dt>
                  <dd>{{ todayLabel }}</dd>
                </div>
                <div>
                  <dt>记忆</dt>
                  <dd>{{ totalPostCount }} 条</dd>
                </div>
                <div>
                  <dt>成员</dt>
                  <dd>{{ memberNames.length || 1 }} 位</dd>
                </div>
              </dl>
            </header>

            <section class="magazine-stage" aria-label="家书杂志内容">
              <article
                v-if="featuredPost"
                class="magazine-feature"
                role="button"
                tabindex="0"
                :aria-label="`查看封面故事：${excerpt(featuredPost.content, 28) || '今天的家庭故事'}`"
                @click="go(featuredPost.id)"
                @keydown.enter.prevent="go(featuredPost.id)"
                @keydown.space.prevent="go(featuredPost.id)"
              >
                <figure class="magazine-feature__media">
                  <video
                    v-if="featuredMedia?.type === 'video'"
                    :src="mediaSource(featuredMedia.url)"
                    controls
                    preload="metadata"
                    @click.stop
                  />
                  <img
                    v-else-if="featuredMedia"
                    :src="mediaSource(featuredMedia.url)"
                    alt=""
                    loading="lazy"
                  />
                  <figcaption v-else>
                    {{ excerpt(featuredPost.content, 34) || '家庭札记' }}
                  </figcaption>
                </figure>
                <div class="magazine-feature__copy">
                  <span>封面故事</span>
                  <h2>{{ excerpt(featuredPost.content, 34) || '今天的家庭故事' }}</h2>
                  <p>{{ longExcerpt(featuredPost.content, 118) || '把一段日常放在封面，家人打开就能先看到今天最想保存的瞬间。' }}</p>
                  <small>{{ featuredPost.author_username }} / {{ displayDate(featuredPost.created_at) }}</small>
                </div>
              </article>

              <aside class="magazine-index" aria-label="本期目录">
                <h2>本期目录</h2>
                <button
                  v-for="post in magazineIndexPosts"
                  :key="post.id"
                  class="magazine-index__item"
                  type="button"
                  @click="go(post.id)"
                >
                  <span>{{ displayDate(post.created_at) }}</span>
                  <strong>{{ excerpt(post.content, 42) || '家庭简讯' }}</strong>
                  <small>{{ post.author_username }} / {{ post.comment_count }} 评论</small>
                </button>
              </aside>
            </section>

            <section v-if="magazineNotePosts.length" class="magazine-notes" aria-label="短篇札记">
              <button
                v-for="post in magazineNotePosts"
                :key="post.id"
                class="magazine-note"
                type="button"
                @click="go(post.id)"
              >
                <span>{{ post.author_username }}</span>
                <strong>{{ excerpt(post.content, 50) || '家庭札记' }}</strong>
                <small>{{ post.like_count }} 赞 / {{ post.comment_count }} 评论</small>
              </button>
            </section>
          </div>

          <div
            v-else-if="layoutMode === 'minimal'"
            class="album-book"
          >
            <header class="album-book__cover">
              <span>{{ todayLabel }}</span>
              <h1>留白相册</h1>
            </header>
            <article
              v-for="(post, i) in posts"
              :key="post.id"
              class="album-spread"
              :class="{ 'album-spread--reverse': i % 2 === 1 }"
              @click="go(post.id)"
            >
              <figure class="album-photo">
                <img
                  v-if="primaryMedia(post)"
                  :src="mediaSource(primaryMedia(post)!.url)"
                  alt=""
                  loading="lazy"
                />
                <figcaption v-else>{{ excerpt(post.content, 28) || '文字页' }}</figcaption>
              </figure>
              <div class="album-note">
                <time>{{ displayDate(post.created_at) }}</time>
                <p>{{ longExcerpt(post.content, 100) || '这一页留给今天的家庭影像。' }}</p>
                <span>{{ post.author_username }}</span>
              </div>
            </article>
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

    <div :class="useImmersiveLayout ? 'hidden' : 'hidden lg:block'">
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
              <p class="text-xs font-medium uppercase tracking-normal text-[var(--text-muted)]">
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
                <p class="text-xs font-medium uppercase tracking-normal text-[var(--text-muted)]">Filters</p>
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
              <p class="text-xs font-medium uppercase tracking-normal text-[var(--text-muted)]">On this day</p>
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
              <p class="text-xs font-medium uppercase tracking-normal text-[var(--text-muted)]">Current</p>
              <h3 class="mt-2 text-base font-semibold text-[var(--text)]">当前筛选</h3>
              <p class="mt-2 text-sm leading-6 text-[var(--text-secondary)]">{{ filterSummary }}</p>
            </section>

            <section class="mt-7">
              <p class="text-xs font-medium uppercase tracking-normal text-[var(--text-muted)]">Members</p>
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
import { CalendarDays } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth'
import { useTheme } from '@/composables/useTheme'
import { getPosts, togglePostLike, type Post, type PostListParams } from '@/api/posts'
import AppShell from '@/components/AppShell.vue'
import NotificationCenter from '@/components/NotificationCenter.vue'
import PostCard from '@/components/PostCard.vue'
import RightRail from '@/components/RightRail.vue'
import { mediaUrl } from '@/utils/media'

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
const { currentTheme } = useTheme()

// 从主题配置读取 layoutMode，默认为 'default'
const layoutMode = computed(() => currentTheme.value.layoutMode || 'default')

// 沉浸式布局：使用单栏/网格/瀑布流等模式时，跳过传统的桌面"档案"布局
const useImmersiveLayout = computed(() => {
  const mode = layoutMode.value
  return mode === 'single-dark' || mode === 'minimal' || mode === 'timeline' || mode === 'grid' || mode === 'masonry'
})

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
const selectedPostId = ref<string>('')
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

// timeline 模式标题的年度范围（取已加载帖子覆盖的年份；为空时回退当前年）
const timelineYearLabel = computed(() => {
  if (!posts.value.length) {
    return String(new Date().getFullYear())
  }
  const years = new Set<number>()
  posts.value.forEach((post) => {
    years.add(new Date(post.created_at).getFullYear())
  })
  const sorted = Array.from(years).sort((a, b) => a - b)
  if (sorted.length === 1) return String(sorted[0])
  return `${sorted[0]}-${sorted[sorted.length - 1]}`
})

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

const featuredPost = computed(() =>
  posts.value.find((post) => post.media_urls?.length) || posts.value[0]
)

const featuredMedia = computed(() => featuredPost.value ? primaryMedia(featuredPost.value) : undefined)

const secondaryPosts = computed(() =>
  featuredPost.value
    ? posts.value.filter((post) => post.id !== featuredPost.value?.id)
    : posts.value
)

const magazineIndexPosts = computed(() => secondaryPosts.value.slice(0, 5))

const magazineNotePosts = computed(() => {
  const notes = secondaryPosts.value.slice(5)
  return notes.length ? notes : secondaryPosts.value.slice(0, 3)
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

// 以下旧的计算属性已被删除，layoutMode 直接从主题配置读取
// postsLayoutClass、showTimelineDecoration、isListViewMode 等不再需要

// 当帖子列表更新时，自动选中第一个帖子（list 模式）
watch(posts, (newPosts) => {
  if (layoutMode.value === 'masonry' && isDesktop.value && newPosts.length > 0 && !selectedPostId.value) {
    selectedPostId.value = newPosts[0].id
  }
}, { immediate: true })

// 切换到 list 模式时，选中第一个帖子
watch(layoutMode, (newMode) => {
  if (newMode === 'masonry' && isDesktop.value && posts.value.length > 0 && !selectedPostId.value) {
    selectedPostId.value = posts.value[0].id
  }
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

function primaryMedia(post: Post) {
  return post.media_urls?.[0]
}

function mediaSource(url: string): string {
  return mediaUrl(url)
}

function excerpt(value: string | undefined, length: number): string {
  const text = (value || '').trim().replace(/\s+/g, ' ')
  if (text.length <= length) return text
  return `${text.slice(0, length)}...`
}

function longExcerpt(value: string | undefined, length: number): string {
  return excerpt(value, length)
}

function displayDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
  }).format(new Date(value))
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

.cinema-stage {
  min-height: calc(100dvh - 7.25rem);
  padding: clamp(0.75rem, 2.2vw, 1.75rem) 0 2rem;
}

.cinema-hero {
  cursor: pointer;
  display: grid;
  gap: clamp(1.25rem, 3vw, 3rem);
  grid-template-columns: minmax(0, 1.36fr) minmax(18rem, 0.64fr);
  min-height: min(58dvh, 38rem);
}

.cinema-hero__media {
  background: #090c12;
  border-radius: 2px;
  box-shadow: 0 32px 120px rgba(0, 0, 0, 0.55);
  min-height: min(58dvh, 38rem);
  overflow: hidden;
}

.cinema-hero__media img,
.cinema-hero__media video {
  display: block;
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.cinema-hero__empty {
  align-items: center;
  color: var(--text);
  display: flex;
  font-size: clamp(2rem, 5vw, 5rem);
  font-weight: 500;
  height: 100%;
  line-height: 1.1;
  padding: clamp(2rem, 6vw, 5rem);
}

.cinema-hero__copy {
  align-self: end;
  border-left: 1px solid var(--border);
  padding: 0 0 clamp(1.25rem, 3vw, 3rem) clamp(1.25rem, 2.6vw, 2rem);
}

.cinema-kicker {
  color: var(--accent);
  font-size: 0.82rem;
  font-weight: 700;
  margin-bottom: 1.25rem;
}

.cinema-hero__copy h1 {
  color: var(--text);
  display: -webkit-box;
  font-size: clamp(1.75rem, 2.65vw, 3rem);
  font-weight: 500;
  line-height: 1.12;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
}

.cinema-meta {
  color: var(--text-muted);
  display: grid;
  gap: 0.45rem;
  margin-top: 1.5rem;
}

.cinema-strip {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  margin-top: clamp(1rem, 2.5vw, 2rem);
}

.cinema-strip__item {
  aspect-ratio: 5 / 3;
  background: var(--surface-card);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  overflow: hidden;
  text-align: left;
}

.cinema-strip__item img {
  height: 100%;
  object-fit: cover;
  width: 100%;
}

.cinema-strip__item span {
  display: block;
  font-size: 0.85rem;
  line-height: 1.5;
  padding: 1rem;
}

.chronicle-board {
  display: grid;
  gap: clamp(1.25rem, 2.6vw, 2.5rem);
  grid-template-columns: minmax(11rem, 0.22fr) minmax(0, 1fr);
  min-height: calc(100dvh - 8rem);
}

.chronicle-cover {
  align-self: start;
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: 999px 999px 28px 28px;
  min-height: min(52dvh, 29rem);
  padding: clamp(1.75rem, 3.6vw, 2.5rem) 1.1rem;
  position: sticky;
  text-align: center;
  top: 2rem;
}

.chronicle-cover p {
  color: var(--accent);
  font-size: 0.82rem;
  font-weight: 700;
}

.chronicle-cover h1 {
  color: var(--text);
  font-size: clamp(2.5rem, 5.4vw, 5rem);
  font-weight: 800;
  line-height: 0.9;
  margin: 1.25rem auto;
  writing-mode: vertical-rl;
}

.chronicle-cover span {
  color: var(--text-muted);
  font-size: 0.82rem;
}

.chronicle-years {
  display: grid;
  gap: 1rem;
}

.chronicle-section {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: 9.75rem minmax(0, 1fr);
}

.chronicle-date {
  align-self: stretch;
  background: var(--accent-soft);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text);
  display: grid;
  gap: 0.42rem;
  justify-items: start;
  padding: 0.9rem;
}

.chronicle-date svg {
  color: var(--accent);
}

.chronicle-date span {
  color: var(--text-muted);
  font-size: 0.82rem;
}

.chronicle-stack {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.chronicle-card {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--card-radius);
  color: var(--text);
  min-height: 7.75rem;
  padding: 0.9rem;
  text-align: left;
}

.chronicle-card:nth-child(3n + 1) {
  grid-row: span 2;
  min-height: 16.25rem;
}

.chronicle-card span,
.chronicle-card small {
  color: var(--text-muted);
  display: block;
  font-size: 0.8rem;
}

.chronicle-card strong {
  display: block;
  display: -webkit-box;
  font-size: clamp(0.96rem, 1.28vw, 1.2rem);
  font-weight: 650;
  line-height: 1.34;
  margin: 0.72rem 0 0.85rem;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.photo-wall-grid {
  display: grid;
  gap: var(--card-gap, 10px);
  grid-auto-flow: dense;
  grid-auto-rows: minmax(6.5rem, 10.5vw);
  grid-template-columns: repeat(8, minmax(0, 1fr));
}

.photo-wall-header {
  align-content: end;
  background: var(--text);
  color: var(--surface);
  display: grid;
  grid-column: span 2;
  grid-row: span 2;
  padding: 1rem;
}

.photo-wall-header h1 {
  font-size: clamp(1.65rem, 3.5vw, 3.4rem);
  font-weight: 800;
  line-height: 0.95;
}

.photo-wall-header p {
  font-size: 0.78rem;
  margin-top: 0.65rem;
  opacity: 0.78;
}

.photo-tile {
  background: var(--surface-card);
  border: 0;
  color: var(--text);
  min-height: 0;
  overflow: hidden;
  padding: 0;
  position: relative;
  text-align: left;
}

.photo-tile--text {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.48), transparent),
    var(--surface-card);
  border: 1px solid var(--border);
}

.photo-tile img {
  display: block;
  height: 100%;
  object-fit: cover;
  transition: transform 400ms ease;
  width: 100%;
}

.photo-tile:hover img {
  transform: scale(1.05);
}

.photo-tile span {
  align-items: flex-start;
  display: flex;
  font-size: clamp(0.78rem, 1vw, 0.88rem);
  height: 100%;
  line-height: 1.46;
  padding: clamp(0.65rem, 1.6vw, 0.85rem);
}

.photo-tile--1,
.photo-tile--6 {
  grid-column: span 2;
  grid-row: span 3;
}

.photo-tile--2,
.photo-tile--7 {
  grid-column: span 3;
  grid-row: span 2;
}

.photo-tile--3,
.photo-tile--4,
.photo-tile--5,
.photo-tile--8 {
  grid-column: span 2;
  grid-row: span 2;
}

.magazine-layout {
  color: var(--text);
  font-family: var(--font-family-title, inherit);
  margin-inline: auto;
  /* 容器最大宽度按 layout 独立 token，回退值即当前实际值 */
  max-width: var(--magazine-max-width, 80rem);
}

.magazine-header {
  align-items: end;
  border-bottom: 1px solid var(--border);
  display: grid;
  gap: clamp(1rem, 3vw, 2rem);
  grid-template-columns: minmax(0, 1fr) minmax(17rem, 0.42fr);
  padding-bottom: clamp(0.85rem, 1.5vw, 1.15rem);
}

.magazine-header p {
  color: var(--accent);
  font-size: 0.85rem;
  font-weight: 700;
  margin-bottom: 0.55rem;
}

.magazine-header h1 {
  font-size: clamp(2rem, 4.6vw, 4.7rem);
  font-weight: 900;
  letter-spacing: 0;
  line-height: 1;
}

.magazine-summary {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.magazine-summary div {
  border-left: 1px solid var(--border);
  padding-left: 0.85rem;
}

.magazine-summary dt {
  color: var(--text-muted);
  font-size: 0.72rem;
  margin-bottom: 0.35rem;
}

.magazine-summary dd {
  color: var(--text);
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
}

.magazine-stage {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1fr) minmax(17rem, 20.5rem);
  margin-top: 1.15rem;
}

.magazine-feature {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: var(--card-radius, 18px);
  color: var(--text);
  cursor: pointer;
  display: grid;
  gap: clamp(1rem, 2.4vw, 1.5rem);
  grid-template-columns: minmax(15rem, 0.78fr) minmax(0, 1fr);
  min-height: 22rem;
  overflow: hidden;
  padding: 1rem;
  text-align: left;
  transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
}

.magazine-feature:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}

.magazine-feature__media {
  background: var(--surface-elevated);
  border-radius: calc(var(--card-radius, 18px) - 6px);
  margin: 0;
  min-height: 21rem;
  overflow: hidden;
}

.magazine-feature__media img,
.magazine-feature__media video {
  display: block;
  height: 100%;
  min-height: 21rem;
  object-fit: cover;
  width: 100%;
}

.magazine-feature__media img {
  filter: saturate(0.92) contrast(1.03);
}

.magazine-feature__media figcaption {
  align-items: center;
  color: var(--text-secondary);
  display: flex;
  font-size: clamp(1.5rem, 3vw, 2.4rem);
  height: 100%;
  justify-content: center;
  line-height: 1.25;
  min-height: 21rem;
  padding: 1.5rem;
  text-align: center;
}

.magazine-feature__copy {
  align-self: center;
  padding: clamp(0.5rem, 2.2vw, 1.75rem);
}

.magazine-feature__copy span {
  color: var(--accent);
  display: inline-block;
  font-size: 0.82rem;
  font-weight: 700;
  margin-bottom: 0.85rem;
}

.magazine-feature__copy h2 {
  font-size: clamp(1.55rem, 2.55vw, 2.65rem);
  font-weight: 900;
  letter-spacing: 0;
  line-height: 1.16;
}

.magazine-feature__copy p {
  color: var(--text-secondary);
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.78;
  margin-top: 0.85rem;
  max-width: 36rem;
}

.magazine-feature__copy small {
  color: var(--text-muted);
  display: block;
  font-size: 0.85rem;
  margin-top: 1.15rem;
}

.magazine-index {
  background: var(--surface-panel);
  border: 1px solid var(--border);
  border-radius: var(--card-radius, 18px);
  padding: 0.9rem;
}

.magazine-index h2 {
  color: var(--text);
  font-size: 1.15rem;
  font-weight: 900;
  margin-bottom: 0.35rem;
}

.magazine-index__item {
  background: transparent;
  border: 0;
  border-top: 1px solid var(--border);
  color: var(--text);
  cursor: pointer;
  display: block;
  padding: 0.78rem 0;
  text-align: left;
  width: 100%;
}

.magazine-index__item span,
.magazine-index__item small {
  color: var(--text-muted);
  display: block;
  font-size: 0.76rem;
}

.magazine-index__item strong {
  display: block;
  font-size: 1rem;
  font-weight: 800;
  line-height: 1.45;
  margin: 0.35rem 0;
}

.magazine-notes {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 1rem;
}

.magazine-note {
  background: var(--surface-card);
  border: 1px solid var(--border);
  border-radius: calc(var(--card-radius, 18px) - 4px);
  color: var(--text);
  cursor: pointer;
  min-height: 10rem;
  padding: 1rem;
  text-align: left;
  transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
}

.magazine-note:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-card);
  transform: translateY(-2px);
}

.magazine-note span,
.magazine-note small {
  color: var(--text-muted);
  display: block;
  font-size: 0.78rem;
}

.magazine-note strong {
  display: block;
  font-size: 1.12rem;
  font-weight: 800;
  line-height: 1.45;
  margin: 1rem 0 1.25rem;
}

.album-book {
  margin-inline: auto;
  /* 容器最大宽度按 layout 独立 token，回退值即当前实际值 */
  max-width: var(--album-max-width, 66rem);
}

.album-book__cover {
  align-items: center;
  border-bottom: 1px solid var(--border);
  border-top: 1px solid var(--border);
  display: grid;
  min-height: min(40dvh, 22rem);
  padding: clamp(2rem, 4.5vw, 4.25rem) 1rem;
  text-align: center;
}

.album-book__cover span {
  color: var(--text-muted);
}

.album-book__cover h1 {
  color: var(--text);
  font-size: clamp(2.7rem, 6.2vw, 5.9rem);
  font-weight: 200;
  line-height: 1;
}

.album-spread {
  cursor: pointer;
  display: grid;
  gap: clamp(1.5rem, 3.4vw, 3.4rem);
  grid-template-columns: minmax(0, 0.95fr) minmax(18rem, 0.62fr);
  min-height: 31rem;
  padding: clamp(2rem, 4.2vw, 3.75rem) 0;
}

.album-spread--reverse {
  grid-template-columns: minmax(18rem, 0.62fr) minmax(0, 0.95fr);
}

.album-spread--reverse .album-photo {
  order: 2;
}

.album-photo {
  align-self: center;
  background: var(--surface-card);
  border: 1px solid var(--border);
  margin: 0;
  min-height: 23rem;
  padding: clamp(0.8rem, 2vw, 1.25rem);
}

.album-photo img {
  display: block;
  filter: saturate(0.86);
  height: 100%;
  min-height: 21rem;
  object-fit: cover;
  width: 100%;
}

.album-photo figcaption {
  align-items: center;
  color: var(--text-secondary);
  display: flex;
  font-size: clamp(1.25rem, 2.2vw, 1.7rem);
  height: 21rem;
  justify-content: center;
  line-height: 1.3;
  text-align: center;
}

.album-note {
  align-self: center;
  border-top: 1px solid var(--border);
  color: var(--text);
  padding-top: 1.6rem;
}

.album-note time,
.album-note span {
  color: var(--text-muted);
  display: block;
  font-size: 0.85rem;
}

.album-note p {
  display: -webkit-box;
  font-size: clamp(1.2rem, 2.35vw, 2.25rem);
  font-weight: 300;
  line-height: 1.42;
  margin: 1rem 0;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 5;
}

@media (max-width: 1023px) {
  .cinema-stage {
    min-height: auto;
    padding: 1rem 0 2rem;
  }

  .cinema-hero,
  .chronicle-board,
  .chronicle-section,
  .magazine-header,
  .magazine-stage,
  .magazine-feature,
  .album-spread,
  .album-spread--reverse {
    grid-template-columns: minmax(0, 1fr);
  }

  .cinema-hero {
    gap: 1rem;
    min-height: auto;
  }

  .cinema-hero__media,
  .album-photo,
  .album-photo img,
  .album-photo figcaption {
    min-height: 20rem;
  }

  .cinema-hero__copy {
    border-left: 0;
    border-top: 1px solid var(--border);
    padding: 1.1rem 0 0;
  }

  .cinema-kicker {
    margin-bottom: 0.8rem;
  }

  .cinema-hero__copy h1 {
    font-size: clamp(1.45rem, 6.3vw, 2.05rem);
    line-height: 1.12;
    -webkit-line-clamp: 4;
  }

  .cinema-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .chronicle-cover {
    border-radius: var(--radius);
    min-height: auto;
    padding: 1.2rem;
    position: static;
    text-align: left;
  }

  .chronicle-cover h1 {
    font-size: clamp(2.1rem, 9.5vw, 3.2rem);
    line-height: 1;
    margin: 0.55rem 0;
    writing-mode: horizontal-tb;
  }

  .chronicle-stack {
    grid-template-columns: minmax(0, 1fr);
  }

  .chronicle-card:nth-child(3n + 1) {
    grid-row: auto;
    min-height: 7.5rem;
  }

  .chronicle-card strong {
    font-size: clamp(0.96rem, 4.2vw, 1.08rem);
    line-height: 1.42;
    margin: 0.65rem 0 0.75rem;
  }

  .photo-wall-grid {
    grid-auto-rows: minmax(6rem, 23vw);
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .magazine-header {
    gap: 0.9rem;
    padding-bottom: 0.9rem;
  }

  .magazine-summary {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .magazine-feature {
    min-height: auto;
  }

  .magazine-feature__media,
  .magazine-feature__media img,
  .magazine-feature__media video,
  .magazine-feature__media figcaption {
    min-height: clamp(14rem, 54vw, 20rem);
  }

  .magazine-index {
    padding: 0.85rem;
  }

  .magazine-notes {
    grid-template-columns: minmax(0, 1fr);
  }

  .album-book__cover {
    min-height: auto;
    padding: 1.7rem 0.35rem;
  }

  .album-spread,
  .album-spread--reverse {
    gap: 1.1rem;
    min-height: auto;
    padding: 1.6rem 0;
  }

  .album-note {
    padding-top: 1.25rem;
  }

  .album-note p {
    font-size: clamp(1.12rem, 5.6vw, 1.65rem);
    -webkit-line-clamp: 4;
  }

  .album-spread--reverse .album-photo {
    order: 0;
  }
}

@media (max-width: 640px) {
  .cinema-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .cinema-hero__media {
    min-height: clamp(16rem, 70vw, 19rem);
  }

  .cinema-meta {
    margin-top: 1rem;
  }

  .photo-wall-grid {
    gap: 0.4rem;
    grid-auto-rows: minmax(4.75rem, 25vw);
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .photo-wall-header {
    grid-column: 1 / -1;
    grid-row: span 1;
    min-height: 6.75rem;
    padding: 0.85rem;
  }

  .photo-wall-header h1 {
    font-size: clamp(1.55rem, 8vw, 2.45rem);
    line-height: 1;
  }

  .photo-wall-header p {
    font-size: 0.72rem;
    margin-top: 0.45rem;
  }

  .photo-tile--1,
  .photo-tile--2,
  .photo-tile--3,
  .photo-tile--4,
  .photo-tile--5,
  .photo-tile--6,
  .photo-tile--7,
  .photo-tile--8 {
    grid-column: span 1;
    grid-row: span 2;
  }

  .photo-tile span {
    align-items: flex-start;
    font-size: clamp(0.74rem, 3.15vw, 0.84rem);
    line-height: 1.46;
    padding: 0.65rem;
  }

  .magazine-summary {
    gap: 0.35rem;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .magazine-summary div {
    border-left: 1px solid var(--border);
    border-top: 0;
    padding-left: 0.55rem;
    padding-top: 0;
  }

  .magazine-summary dt {
    margin-bottom: 0.2rem;
  }

  .magazine-summary dd {
    font-size: 0.82rem;
  }

  .magazine-header h1 {
    font-size: clamp(2rem, 11vw, 3rem);
    line-height: 1.04;
  }

  .magazine-stage {
    margin-top: 1rem;
  }

  .magazine-feature {
    min-height: auto;
    padding: 0.65rem;
  }

  .magazine-feature__copy {
    padding: 0.35rem 0.15rem 0.4rem;
  }

  .magazine-feature__copy h2 {
    font-size: clamp(1.35rem, 7vw, 1.85rem);
    display: -webkit-box;
    overflow: hidden;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
  }

  .magazine-feature__copy p {
    display: -webkit-box;
    font-size: 0.9rem;
    line-height: 1.68;
    overflow: hidden;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
  }

  .magazine-index__item {
    padding: 0.68rem 0;
  }

  .album-book {
    max-width: 100%;
  }

  .album-book__cover {
    padding: 1.25rem 0.25rem;
  }

  .album-book__cover h1 {
    font-size: clamp(2.2rem, 12vw, 3.5rem);
  }

  .album-photo {
    min-height: clamp(12.5rem, 58vw, 16rem);
    padding: 0.65rem;
  }

  .album-photo img,
  .album-photo figcaption {
    min-height: clamp(11.5rem, 52vw, 14.75rem);
  }

  .album-spread,
  .album-spread--reverse {
    gap: 0.85rem;
    padding: 1.15rem 0;
  }

  .album-note {
    padding-top: 0.9rem;
  }

  .album-note p {
    display: -webkit-box;
    font-size: clamp(1rem, 4.9vw, 1.28rem);
    line-height: 1.42;
    margin: 0.7rem 0;
    overflow: hidden;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 4;
  }
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
  background: var(--surface-card);
}

.desktop-archive__top {
  background: var(--surface-card);
}

.desktop-archive__side {
  background: var(--surface-panel);
}

.desktop-archive__content {
  background: var(--surface-card);
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
  background: var(--surface-card) !important;
}

.anniversary-card,
.memory-filter {
  position: relative;
}

.anniversary-card {
  background: var(--surface-card) !important;
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
  background: var(--surface-panel) !important;
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
  .date-divider,
  .cinema-hero,
  .cinema-strip__item,
  .chronicle-card,
  .photo-tile,
  .magazine-feature,
  .magazine-note,
  .album-spread {
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
  .rail-stat:hover,
  .cinema-hero:hover,
  .cinema-strip__item:hover,
  .chronicle-card:hover,
  .photo-tile:hover,
  .magazine-feature:hover,
  .magazine-note:hover,
  .album-spread:hover {
    transform: none;
  }
}
</style>
