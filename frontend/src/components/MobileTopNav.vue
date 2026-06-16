<script setup lang="ts">
import { computed } from 'vue'
import { Bell, CalendarDays, Home, Image, Images, Palette, Plus, Settings, UserCircle } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth'
import FamilySeal from '@/components/FamilySeal.vue'
import { useThemeSwitcher } from '@/composables/useThemeSwitcher'

withDefaults(
  defineProps<{
    title?: string
    logoUrl?: string
  }>(),
  {
    title: '哪吒家庭',
    logoUrl: '',
  }
)

const { user } = useAuth()
const { openThemeSwitcher } = useThemeSwitcher()

const navItems = computed(() => [
  { label: '动态', to: '/', icon: Home },
  { label: '媒体', to: '/library', icon: Image },
  { label: '相册', to: '/albums', icon: Images },
  { label: '日历', to: '/calendar', icon: CalendarDays },
  { label: '通知', to: '/notifications', icon: Bell },
  ...(user.value ? [{ label: '我的', to: `/profile/${user.value.id}`, icon: UserCircle }] : []),
  ...(user.value?.role === 'admin' ? [{ label: '管理', to: '/admin', icon: Settings }] : []),
])
</script>

<template>
  <header class="mobile-top-nav sticky top-0 z-40 border-b border-[var(--border)] backdrop-blur-xl">
    <div class="mobile-brand-row flex h-12 items-center justify-between gap-3 px-3.5">
      <RouterLink to="/" class="brand-link flex min-w-0 items-center gap-2">
        <span class="brand-mark grid h-8 w-8 shrink-0 place-items-center">
          <FamilySeal compact :label="title" :logo-url="logoUrl" />
        </span>
        <span class="brand-title truncate text-[15px] font-semibold leading-none text-[var(--text)]">{{ title }}</span>
      </RouterLink>

      <div class="mobile-actions flex shrink-0 items-center gap-2">
        <button
          @click="openThemeSwitcher"
          aria-label="主题"
          class="grid h-8 w-8 place-items-center rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)] text-[var(--text-secondary)] hover:border-[var(--accent)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)] active:scale-[0.98]"
        >
          <Palette :size="16" stroke-width="2" aria-hidden="true" />
        </button>

        <RouterLink
          to="/publish"
          aria-label="发布记忆"
          class="mobile-publish grid h-8 w-8 place-items-center rounded-lg bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)] active:scale-[0.98]"
        >
          <Plus :size="18" stroke-width="2.1" aria-hidden="true" />
        </RouterLink>
      </div>
    </div>

    <nav
      class="mobile-nav-scroll flex overflow-x-auto border-t border-[var(--border)] px-2"
      aria-label="移动端主导航"
    >
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="mobile-nav-link flex h-11 min-w-[3.4rem] flex-1 flex-col items-center justify-center gap-0.5 rounded-t-lg px-2 text-[10px] font-medium text-[var(--text-muted)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text-secondary)]"
        active-class="mobile-nav-link-active !text-[var(--accent)]"
      >
        <component :is="item.icon" :size="16" stroke-width="1.9" aria-hidden="true" />
        <span class="truncate">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </header>
</template>

<style scoped>
.mobile-top-nav {
  background: var(--surface-panel);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.08);
}

.mobile-brand-row {
  min-width: 0;
}

.brand-link {
  max-width: min(58vw, 14rem);
  overflow: hidden;
}

.brand-mark {
  filter: drop-shadow(0 5px 12px rgba(47, 39, 35, 0.1));
}

.brand-title {
  letter-spacing: -0.01em;
}

.mobile-actions {
  min-width: 4.5rem;
}

.brand-link,
.mobile-publish,
.mobile-nav-link {
  transition:
    background-color 170ms ease,
    color 170ms ease,
    opacity 170ms ease,
    transform 170ms ease;
}

.brand-link:active,
.mobile-publish:active,
.mobile-nav-link:active {
  transform: scale(0.98);
}

.mobile-publish {
  box-shadow: 0 8px 22px rgba(201, 67, 47, 0.18);
}

.mobile-nav-link {
  position: relative;
}

.mobile-nav-scroll {
  scrollbar-width: none;
}

.mobile-nav-scroll::-webkit-scrollbar {
  display: none;
}

.mobile-nav-link::after {
  background: var(--accent);
  border-radius: 999px 999px 0 0;
  bottom: 0;
  content: '';
  height: 0.16rem;
  left: 50%;
  opacity: 0;
  position: absolute;
  transform: translateX(-50%) scaleX(0.45);
  transition: opacity 170ms ease, transform 170ms ease;
  width: 1.25rem;
}

.mobile-nav-link-active::after {
  opacity: 1;
  transform: translateX(-50%) scaleX(1);
}

@media (max-width: 380px) {
  .mobile-brand-row {
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }

  .brand-link {
    gap: 0.4rem;
    max-width: min(52vw, 11rem);
  }

  .brand-mark {
    height: 1.85rem;
    width: 1.85rem;
  }

  .brand-title {
    font-size: 0.86rem;
  }

  .mobile-actions {
    gap: 0.4rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .brand-link,
  .mobile-publish,
  .mobile-nav-link,
  .mobile-nav-link::after {
    transition: none;
  }

  .brand-link:active,
  .mobile-publish:active,
  .mobile-nav-link:active {
    transform: none;
  }
}
</style>
