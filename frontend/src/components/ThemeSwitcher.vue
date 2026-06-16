<script setup lang="ts">
import { Check, Loader2, X } from 'lucide-vue-next'
import { useTheme } from '@/composables/useTheme'

const emit = defineEmits<{
  close: []
}>()

const { themes, currentThemeId, savingTheme, themeSaveError, switchTheme } = useTheme()

async function handleThemeClick(themeId: string) {
  await switchTheme(themeId)
}
</script>

<template>
  <Teleport to="body">
    <div
      class="theme-switcher-overlay fixed inset-0 z-[90] flex items-center justify-center bg-black/50 p-4 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-labelledby="theme-switcher-title"
      @click.self="$emit('close')"
    >
      <div class="theme-switcher-modal relative w-full max-w-6xl overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface-card)] shadow-2xl">
        <!-- 头部 -->
        <div class="border-b border-[var(--border)] bg-[var(--surface-elevated)] px-8 py-6">
          <div class="flex items-start justify-between gap-5">
            <div>
              <h2 id="theme-switcher-title" class="text-2xl font-bold text-[var(--text)]">选择主题</h2>
              <p class="mt-2 text-sm text-[var(--text-muted)]">每个账号独立保存自己的浏览视角。</p>
              <p v-if="themeSaveError" class="mt-2 text-xs text-[var(--accent)]">{{ themeSaveError }}</p>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <span v-if="savingTheme" class="inline-flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                <Loader2 :size="14" class="animate-spin" aria-hidden="true" />
                保存中
              </span>
              <button
                @click="$emit('close')"
                class="grid h-10 w-10 place-items-center rounded-lg border border-[var(--border)] bg-[var(--surface-card)] text-[var(--text-secondary)] transition-all hover:border-[var(--accent)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)]"
                aria-label="关闭"
              >
                <X :size="18" stroke-width="2" />
              </button>
            </div>
          </div>
        </div>

        <!-- 主题网格 -->
        <div class="max-h-[70vh] overflow-y-auto px-8 py-8">
          <div class="themes-grid grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <button
              v-for="theme in themes"
              :key="theme.id"
              @click="handleThemeClick(theme.id)"
              :aria-pressed="currentThemeId === theme.id"
              :data-theme-option="theme.id"
              :data-layout-mode="theme.layoutMode"
              class="theme-card group relative flex min-h-[19rem] flex-col overflow-hidden rounded-xl border-2 bg-[var(--surface-elevated)] text-left transition-all duration-300"
              :class="
                currentThemeId === theme.id
                  ? 'border-[var(--accent)] shadow-2xl ring-4 ring-[var(--accent)]/20'
                  : 'border-[var(--border)] hover:border-[var(--accent)] hover:shadow-xl hover:-translate-y-1'
              "
            >
              <!-- 大预览图 -->
              <div
                class="preview-image relative h-48 w-full overflow-hidden border-b border-[var(--border)] transition-transform duration-300 group-hover:scale-105"
                :style="{
                  background: theme.cssVars['--surface']
                }"
              >
                <!-- 根据 layoutMode 显示不同的预览布局 -->

                <!-- default: 温馨奶白 / 三栏 (左导航 + 中卡片 + 右栏) -->
                <div v-if="theme.layoutMode === 'default'" class="absolute inset-0 flex">
                  <!-- 左侧导航 -->
                  <div class="flex w-1/5 flex-col gap-1.5 p-2" :style="{ background: theme.cssVars['--surface-elevated'] }">
                    <div class="h-2 w-3/4 rounded-full" :style="{ background: `linear-gradient(90deg, ${theme.cssVars['--accent']}, ${theme.cssVars['--accent-strong']})` }" />
                    <div class="h-1.5 w-2/3 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.35 }" />
                    <div class="h-1.5 w-1/2 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.25 }" />
                    <div class="h-1.5 w-2/3 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.25 }" />
                  </div>
                  <!-- 中央内容卡片 -->
                  <div class="flex flex-1 flex-col gap-2 p-3">
                    <!-- 强调条 (橙红渐变) -->
                    <div class="h-1.5 w-12 rounded-full" :style="{ background: `linear-gradient(90deg, ${theme.cssVars['--accent']}, ${theme.cssVars['--accent-strong']})` }" />
                    <!-- 主卡片 -->
                    <div class="flex-1 rounded-xl border p-2 shadow-sm" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }">
                      <!-- 卡片缩略图 -->
                      <div class="mb-2 h-12 rounded-md" :style="{ background: `linear-gradient(135deg, ${theme.cssVars['--accent']}, ${theme.cssVars['--accent-strong']})`, opacity: 0.85 }" />
                      <div class="mb-1 h-1.5 w-3/4 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.7 }" />
                      <div class="h-1 w-1/2 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.35 }" />
                    </div>
                  </div>
                  <!-- 右侧栏 -->
                  <div class="flex w-1/6 flex-col gap-1.5 p-2" :style="{ background: theme.cssVars['--surface-elevated'] }">
                    <div class="h-1.5 w-full rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.4 }" />
                    <div class="h-1 w-3/4 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.25 }" />
                    <div class="mt-auto h-5 rounded-md" :style="{ background: theme.cssVars['--accent-soft'] }" />
                  </div>
                </div>

                <!-- single-dark: 深色沉浸 (全黑背景 + 80% 大图 + 极少底部白字) -->
                <div v-else-if="theme.layoutMode === 'single-dark'" class="absolute inset-0 flex flex-col bg-black">
                  <!-- 大图占据 80% (深蓝渐变) -->
                  <div class="flex-1" style="background: linear-gradient(135deg, #1e3a5f 0%, #2d3748 50%, #0f172a 100%);" />
                  <!-- 底部一行小白字 -->
                  <div class="flex flex-col gap-1 px-3 py-2.5">
                    <div class="h-1.5 w-20 rounded-full bg-white/85" />
                    <div class="h-1 w-12 rounded-full bg-white/40" />
                  </div>
                </div>

                <!-- timeline: 时间线叙事 (左侧蓝色竖线 + 圆点 + 旁边小卡片) -->
                <div v-else-if="theme.layoutMode === 'timeline'" class="absolute inset-0 p-3">
                  <!-- 左侧蓝色竖线 -->
                  <div class="absolute bottom-3 left-6 top-3 w-1 rounded-full" :style="{ background: theme.cssVars['--accent'] }" />
                  <!-- 时间节点 + 卡片 -->
                  <div class="relative flex h-full flex-col justify-around pl-2">
                    <div class="flex items-center gap-3">
                      <div class="ml-3 h-3 w-3 shrink-0 rounded-full ring-2 ring-white" :style="{ background: theme.cssVars['--accent'] }" />
                      <div class="flex-1 rounded-md border p-1.5" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }">
                        <div class="mb-1 h-1 w-10 rounded-full" :style="{ background: theme.cssVars['--accent'], opacity: 0.85 }" />
                        <div class="h-1 w-3/4 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.4 }" />
                      </div>
                    </div>
                    <div class="flex items-center gap-3">
                      <div class="ml-3 h-3 w-3 shrink-0 rounded-full ring-2 ring-white" :style="{ background: theme.cssVars['--accent'] }" />
                      <div class="flex-1 rounded-md border p-1.5" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }">
                        <div class="mb-1 h-1 w-8 rounded-full" :style="{ background: theme.cssVars['--accent'], opacity: 0.85 }" />
                        <div class="h-1 w-2/3 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.4 }" />
                      </div>
                    </div>
                    <div class="flex items-center gap-3">
                      <div class="ml-3 h-3 w-3 shrink-0 rounded-full ring-2 ring-white" :style="{ background: theme.cssVars['--accent'] }" />
                      <div class="flex-1 rounded-md border p-1.5" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }">
                        <div class="mb-1 h-1 w-12 rounded-full" :style="{ background: theme.cssVars['--accent'], opacity: 0.85 }" />
                        <div class="h-1 w-4/5 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.4 }" />
                      </div>
                    </div>
                    <div class="flex items-center gap-3">
                      <div class="ml-3 h-3 w-3 shrink-0 rounded-full ring-2 ring-white" :style="{ background: theme.cssVars['--accent'] }" />
                      <div class="flex-1 rounded-md border p-1.5" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }">
                        <div class="mb-1 h-1 w-9 rounded-full" :style="{ background: theme.cssVars['--accent'], opacity: 0.85 }" />
                        <div class="h-1 w-3/5 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.4 }" />
                      </div>
                    </div>
                  </div>
                </div>

                <!-- grid: 卡片网格 (3x2 多色块, 几乎无文字) -->
                <div v-else-if="theme.layoutMode === 'grid'" class="absolute inset-0 grid grid-cols-3 grid-rows-2 gap-1.5 p-2">
                  <div class="rounded" style="background: linear-gradient(135deg, #FFB5B8, #FF8E91);" />
                  <div class="rounded" style="background: linear-gradient(135deg, #A8C7F0, #6FA3E8);" />
                  <div class="rounded" style="background: linear-gradient(135deg, #FFE5A0, #FFD060);" />
                  <div class="rounded" style="background: linear-gradient(135deg, #B8E0B8, #80C880);" />
                  <div class="rounded" style="background: linear-gradient(135deg, #D4B5E8, #B080D8);" />
                  <div class="rounded" style="background: linear-gradient(135deg, #FFCBA4, #FFA070);" />
                </div>

                <!-- masonry: 家庭小刊 (封面故事 + 目录 + 短篇札记) -->
                <div v-else-if="theme.layoutMode === 'masonry'" class="absolute inset-0 p-3" :style="{ background: theme.cssVars['--surface'] }">
                  <div class="mb-2 flex items-end justify-between gap-2">
                    <div
                      class="leading-none preview-serif-title"
                      :style="{
                        color: theme.cssVars['--text']
                      }"
                    >
                      小刊
                    </div>
                    <div class="flex flex-col items-end gap-1">
                      <div class="h-1 w-7 rounded-full" :style="{ background: theme.cssVars['--accent'], opacity: 0.75 }" />
                      <div class="h-1 w-4 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.25 }" />
                    </div>
                  </div>
                  <div class="grid grid-cols-[1.15fr_0.85fr] gap-2">
                    <div class="overflow-hidden rounded-md border p-1.5" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }">
                      <div class="mb-1.5 h-10 rounded-sm" :style="{ background: `linear-gradient(135deg, ${theme.cssVars['--accent']}, ${theme.cssVars['--accent-honey']})`, opacity: 0.82 }" />
                      <div class="mb-1 h-1 w-11/12 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.5 }" />
                      <div class="h-1 w-2/3 rounded-full" :style="{ background: theme.cssVars['--text'], opacity: 0.32 }" />
                    </div>
                    <div class="rounded-md border p-1.5" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-panel'] }">
                      <div class="mb-1 h-1.5 w-9 rounded-full" :style="{ background: theme.cssVars['--accent'], opacity: 0.7 }" />
                      <div v-for="i in 4" :key="i" class="border-t py-1" :style="{ borderColor: theme.cssVars['--border'] }">
                        <div class="h-1 rounded-full" :style="{ width: `${74 - i * 8}%`, background: theme.cssVars['--text'], opacity: 0.36 }" />
                      </div>
                    </div>
                  </div>
                  <div class="mt-2 grid grid-cols-3 gap-1.5">
                    <div v-for="i in 3" :key="i" class="h-5 rounded-md border" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }" />
                  </div>
                </div>

                <!-- minimal: 极简日式 (纯白 + 居中小图 + 大量留白 + 极小灰字) -->
                <div v-else-if="theme.layoutMode === 'minimal'" class="absolute inset-0 flex flex-col items-center justify-center bg-white">
                  <!-- 居中小图 -->
                  <div class="h-14 w-20 rounded-sm" style="background: #EAEAEA;" />
                  <!-- 大量留白 -->
                  <div class="mt-5 h-px w-8" style="background: #C8C8C8;" />
                  <!-- 极小灰色文字行 (日期) -->
                  <div
                    class="mt-2 tracking-normal"
                    style="font-size: 8px; color: #999999; font-family: ui-sans-serif, system-ui, sans-serif;"
                  >
                    2024.06.14
                  </div>
                </div>

                <!-- 兜底布局 (理论上不会触发) -->
                <div v-else class="absolute inset-0 flex flex-col p-4">
                  <div class="mb-3 flex items-center gap-2">
                    <div class="h-6 w-6 rounded-lg" :style="{ background: theme.cssVars['--accent'] }" />
                    <div class="h-3 w-20 rounded" :style="{ background: theme.cssVars['--text'], opacity: 0.6 }" />
                  </div>
                  <div class="flex-1 rounded-lg border p-3" :style="{ borderColor: theme.cssVars['--border'], background: theme.cssVars['--surface-card'] }">
                    <div class="mb-2 h-2 w-16 rounded" :style="{ background: theme.cssVars['--text'], opacity: 0.8 }" />
                    <div class="h-2 w-full rounded" :style="{ background: theme.cssVars['--text'], opacity: 0.4 }" />
                    <div class="mt-1 h-2 w-4/5 rounded" :style="{ background: theme.cssVars['--text'], opacity: 0.4 }" />
                  </div>
                </div>

                <!-- 当前选中标记 -->
                <div
                  v-if="currentThemeId === theme.id"
                  class="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-[var(--accent)] shadow-lg"
                >
                  <Check :size="16" stroke-width="3" class="text-white" aria-hidden="true" />
                </div>
              </div>

              <!-- 主题信息 -->
              <div class="flex flex-col gap-2 p-5">
                <div class="flex items-center justify-between gap-2">
                  <h3 class="text-lg font-bold text-[var(--text)]">{{ theme.name }}</h3>
                  <div
                    v-if="currentThemeId === theme.id"
                    class="rounded-full bg-[var(--accent-soft)] px-2.5 py-0.5 text-xs font-semibold text-[var(--accent)]"
                  >
                    当前
                  </div>
                </div>
                <p class="text-sm leading-relaxed text-[var(--text-muted)]">{{ theme.description }}</p>
              </div>

              <!-- hover 发光效果 -->
              <div
                class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                :style="{
                  background: `radial-gradient(circle at 50% 0%, ${theme.cssVars['--accent']}15, transparent 70%)`
                }"
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.theme-switcher-overlay {
  animation: overlay-fade-in 250ms ease-out;
}

.theme-switcher-modal {
  animation: modal-scale-in 350ms cubic-bezier(0.16, 1, 0.3, 1);
}

.theme-card {
  cursor: pointer;
}

/* masonry 主题预览中的衬线大标题 */
.preview-serif-title {
  font-family: "Noto Serif SC", "Source Han Serif", Georgia, serif;
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 0;
}

@keyframes overlay-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes modal-scale-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* 自定义滚动条 */
.theme-switcher-modal ::-webkit-scrollbar {
  width: 8px;
}

.theme-switcher-modal ::-webkit-scrollbar-track {
  background: var(--surface-elevated);
  border-radius: 4px;
}

.theme-switcher-modal ::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 4px;
  transition: background 200ms ease;
}

.theme-switcher-modal ::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

@media (prefers-reduced-motion: reduce) {
  .theme-switcher-overlay,
  .theme-switcher-modal,
  .theme-card,
  .preview-image {
    animation: none;
    transition: none;
  }

  .theme-card:hover {
    transform: none;
  }
}

@media (max-width: 640px) {
  .theme-switcher-modal {
    max-height: 90vh;
  }

  .themes-grid {
    grid-template-columns: minmax(0, 1fr) !important;
  }
}
</style>
