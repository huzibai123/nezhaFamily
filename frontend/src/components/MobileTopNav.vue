<script setup lang="ts">
import { computed } from 'vue'
import { Bell, CalendarDays, Home, Images, Plus, Settings, UserCircle } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth'
import FamilySeal from '@/components/FamilySeal.vue'

withDefaults(
  defineProps<{
    title?: string
  }>(),
  {
    title: '哪吒家庭',
  }
)

const { user } = useAuth()

const navItems = computed(() => [
  { label: '动态', to: '/', icon: Home },
  { label: '相册', to: '/albums', icon: Images },
  { label: '日历', to: '/calendar', icon: CalendarDays },
  { label: '通知', to: '/notifications', icon: Bell },
  ...(user.value ? [{ label: '我的', to: `/profile/${user.value.id}`, icon: UserCircle }] : []),
  ...(user.value?.role === 'admin' ? [{ label: '管理', to: '/admin', icon: Settings }] : []),
])
</script>

<template>
  <header class="mobile-top-nav sticky top-0 z-40 border-b border-[var(--border)] backdrop-blur-xl">
    <div class="flex h-14 items-center justify-between px-4">
      <RouterLink to="/" class="brand-link flex min-w-0 items-center gap-2.5">
        <span class="grid h-8 w-8 shrink-0 place-items-center">
          <FamilySeal compact :label="title" />
        </span>
        <span class="truncate text-base font-semibold text-[var(--text)]">{{ title }}</span>
      </RouterLink>

      <RouterLink
        to="/publish"
        aria-label="发布记忆"
        class="mobile-publish grid h-9 w-9 place-items-center rounded-lg bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)] active:scale-[0.98]"
      >
        <Plus :size="19" stroke-width="2.1" aria-hidden="true" />
      </RouterLink>
    </div>

    <nav
      class="grid border-t border-[var(--border)]"
      :class="user?.role === 'admin' ? 'grid-cols-6' : user ? 'grid-cols-5' : 'grid-cols-4'"
      aria-label="移动端主导航"
    >
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="mobile-nav-link flex h-12 min-w-0 flex-col items-center justify-center gap-0.5 text-[11px] font-medium text-[var(--text-muted)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text-secondary)]"
        active-class="mobile-nav-link-active !text-[var(--accent)]"
      >
        <component :is="item.icon" :size="17" stroke-width="1.9" aria-hidden="true" />
        <span class="truncate">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </header>
</template>

<style scoped>
.mobile-top-nav {
  background:
    linear-gradient(180deg, rgba(255, 248, 235, 0.94), rgba(250, 225, 196, 0.9)),
    rgba(255, 248, 235, 0.88);
  box-shadow: 0 10px 28px rgba(143, 80, 40, 0.1);
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
  box-shadow: 0 8px 22px rgba(217, 74, 74, 0.2);
}

.mobile-nav-link {
  position: relative;
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
