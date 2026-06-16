<script setup lang="ts">
import { computed, useSlots } from 'vue'
import DesktopSidebar from '@/components/DesktopSidebar.vue'
import FamilyDecorLayer from '@/components/FamilyDecorLayer.vue'
import MediaSearchPanel from '@/components/MediaSearchPanel.vue'
import MobileTopNav from '@/components/MobileTopNav.vue'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { useFamilySettings } from '@/composables/useFamilySettings'
import { useTheme } from '@/composables/useTheme'
import { useThemeSwitcher } from '@/composables/useThemeSwitcher'

const props = withDefaults(
  defineProps<{
    familyName?: string
    pageTitle?: string
    pageDescription?: string
    contentWidth?: 'normal' | 'wide'
  }>(),
  {
    familyName: '',
    pageTitle: '',
    pageDescription: '',
    contentWidth: 'normal',
  }
)

const slots = useSlots()
const hasRightRail = computed(() => Boolean(slots.right))
const { familyName: configuredFamilyName, logoUrl } = useFamilySettings()
const { currentTheme } = useTheme()
const { isThemeSwitcherOpen, closeThemeSwitcher } = useThemeSwitcher()
const displayFamilyName = computed(() => props.familyName || configuredFamilyName.value)
const shouldShowRightRail = computed(() => {
  const mode = currentTheme.value.layoutMode
  if (mode === 'single-dark' || mode === 'minimal' || mode === 'timeline' || mode === 'masonry' || mode === 'grid') {
    return false
  }
  return hasRightRail.value
})

const shellLayoutClass = computed(() => {
  const mode = currentTheme.value.layoutMode
  if (mode === 'single-dark' || mode === 'minimal' || mode === 'grid' || mode === 'timeline' || mode === 'masonry') {
    return 'lg:grid-cols-[minmax(0,1fr)]'
  }
  return 'lg:grid-cols-[16rem_minmax(0,1fr)] xl:grid-cols-[17rem_minmax(0,1fr)]'
})

const shouldShowSidebar = computed(() => {
  const mode = currentTheme.value.layoutMode
  return mode === 'default'
})

const useImmersiveLayout = computed(() => {
  const mode = currentTheme.value.layoutMode
  return mode === 'single-dark' || mode === 'minimal' || mode === 'timeline' || mode === 'masonry' || mode === 'grid'
})

const shellWidthClass = computed(() => {
  if (props.contentWidth === 'wide') return 'max-w-[92rem]'
  return shouldShowRightRail.value ? 'max-w-[76rem]' : 'max-w-[58rem]'
})

const contentGridClass = computed(() => {
  if (!shouldShowRightRail.value) {
    return props.contentWidth === 'wide' ? 'max-w-[92rem]' : 'max-w-[58rem]'
  }
  if (props.contentWidth === 'wide') {
    return 'max-w-[92rem] lg:grid-cols-[minmax(0,1fr)_17rem] xl:grid-cols-[minmax(0,1fr)_20rem] 2xl:grid-cols-[minmax(0,1fr)_21rem]'
  }
  return 'max-w-[76rem] lg:grid-cols-[minmax(0,1fr)_17rem] xl:grid-cols-[minmax(0,54rem)_20rem] 2xl:grid-cols-[minmax(0,58rem)_21rem]'
})
</script>

<template>
  <div class="family-shell min-h-dvh text-[var(--text)]" :class="`theme-${currentTheme.layoutMode}`">
    <FamilyDecorLayer class="family-shell-decor" />
    <!-- 移动端始终显示，桌面端在隐藏侧边栏的主题下也显示，保证导航和主题切换可用 -->
    <MobileTopNav
      :class="shouldShowSidebar ? 'lg:hidden' : ''"
      :title="displayFamilyName"
      :logo-url="logoUrl"
    />

    <div class="mx-auto grid min-h-dvh w-full" :class="shellLayoutClass">
      <DesktopSidebar
        v-if="shouldShowSidebar"
        class="hidden lg:flex"
        :family-name="displayFamilyName"
        :logo-url="logoUrl"
      />

      <div class="min-w-0">
        <main class="shell-main mx-auto w-full px-4 pb-16 pt-5 sm:px-6 lg:px-8 lg:py-8 xl:px-10">
          <div
            v-if="!useImmersiveLayout"
            class="mx-auto mb-5 w-full"
            :class="shellWidthClass"
          >
            <MediaSearchPanel />
          </div>

          <div
            v-if="!useImmersiveLayout && (pageTitle || pageDescription || $slots.header)"
            class="mx-auto mb-6 w-full"
            :class="shellWidthClass"
          >
            <slot name="header">
              <div class="space-y-2">
                <p v-if="pageDescription" class="max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
                  {{ pageDescription }}
                </p>
                <h1 v-if="pageTitle" class="text-2xl font-semibold leading-tight tracking-normal text-[var(--text)] sm:text-3xl">
                  {{ pageTitle }}
                </h1>
              </div>
            </slot>
          </div>

          <div
            class="mx-auto grid w-full gap-6 lg:gap-7 xl:gap-8"
            :class="contentGridClass"
          >
            <section class="min-w-0">
              <slot />
            </section>

            <aside
              v-if="shouldShowRightRail"
              data-testid="app-right-rail"
              class="hidden min-w-0 lg:sticky lg:top-8 lg:block lg:self-start"
            >
              <slot name="right" />
            </aside>
          </div>
        </main>
      </div>
    </div>

    <ThemeSwitcher v-if="isThemeSwitcherOpen" @close="closeThemeSwitcher" />
  </div>
</template>

<style scoped>
.family-shell {
  isolation: isolate;
  overflow: hidden;
  position: relative;
  background: var(--surface);
}

/* 环形 + 丝带装饰仅在 default 主题下显示，其他主题保持简洁 */
.family-shell.theme-default::before,
.family-shell.theme-default::after {
  content: '';
  pointer-events: none;
  position: fixed;
  z-index: 0;
}

.family-shell > :not(.family-shell-decor) {
  position: relative;
  z-index: 1;
}

.family-shell.theme-default::before {
  animation: ring-drift 16s ease-in-out infinite;
  background:
    conic-gradient(from 16deg, var(--accent-soft), rgba(45, 108, 104, 0.12), rgba(66, 81, 132, 0.08), var(--accent-soft));
  border: 1px solid var(--border);
  border-radius: 999px;
  height: min(26vw, 16rem);
  opacity: 0.26;
  right: clamp(1rem, 6vw, 5rem);
  top: 5.5rem;
  width: min(26vw, 16rem);
}

.family-shell.theme-default::after {
  animation: ribbon-breathe 13s ease-in-out infinite alternate;
  background:
    linear-gradient(92deg, transparent, var(--accent-soft), rgba(45, 108, 104, 0.08), transparent);
  border-radius: 999px;
  bottom: 12vh;
  filter: blur(0.5px);
  height: 4rem;
  left: clamp(-5rem, -3vw, -1rem);
  opacity: 0.34;
  transform: rotate(-9deg);
  width: min(34rem, 58vw);
}

/* 沉浸式深色：整体深色渐晕背景（与 FamilyDecorLayer 协同） */
.family-shell.theme-single-dark {
  background:
    radial-gradient(circle at 82% 8%, rgba(124, 158, 217, 0.16), transparent 30rem),
    radial-gradient(circle at 18% 88%, rgba(72, 219, 251, 0.08), transparent 28rem),
    var(--surface);
  color-scheme: dark;
}

.family-shell.theme-grid .shell-main {
  padding-left: var(--page-padding, 1rem);
  padding-right: var(--page-padding, 1rem);
}

.family-shell.theme-minimal .shell-main {
  padding-top: clamp(2rem, 6vw, 5rem);
}

.shell-main {
  animation: shell-content-in 420ms ease-out;
  /* 让主内容区的左右内边距也响应主题（默认 24px） */
  padding-left: var(--page-padding, 24px);
  padding-right: var(--page-padding, 24px);
}

@keyframes shell-content-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes ring-drift {
  0% {
    transform: translate3d(0, 0, 0) rotate(0deg) scale(1);
  }
  45% {
    transform: translate3d(-0.6rem, 0.8rem, 0) rotate(18deg) scale(0.98);
  }
  100% {
    transform: translate3d(0.4rem, -0.35rem, 0) rotate(38deg) scale(1.02);
  }
}

@keyframes ribbon-breathe {
  from {
    transform: translate3d(0, 0, 0) rotate(-9deg) scaleX(1);
  }
  to {
    transform: translate3d(1.4rem, -0.9rem, 0) rotate(-5deg) scaleX(1.04);
  }
}

@media (prefers-reduced-motion: reduce) {
  .shell-main,
  .family-shell.theme-default::before,
  .family-shell.theme-default::after {
    animation: none;
  }
}
</style>
