<script setup lang="ts">
import { computed } from 'vue'
import { Bell, CalendarDays, Home, Images, Plus, Settings, UserCircle } from 'lucide-vue-next'
import { useAuth } from '@/composables/useAuth'
import FamilySeal from '@/components/FamilySeal.vue'

withDefaults(
  defineProps<{
    familyName?: string
  }>(),
  {
    familyName: '哪吒家庭',
  }
)

const { user } = useAuth()

const navItems = computed(() => [
  { label: '时间线', to: '/', icon: Home },
  { label: '相册', to: '/albums', icon: Images },
  { label: '日历', to: '/calendar', icon: CalendarDays },
  { label: '通知', to: '/notifications', icon: Bell },
  ...(user.value ? [{ label: '我的主页', to: `/profile/${user.value.id}`, icon: UserCircle }] : []),
  ...(user.value?.role === 'admin' ? [{ label: '家庭管理', to: '/admin', icon: Settings }] : []),
])

const userInitial = computed(() => user.value?.username?.slice(0, 1).toUpperCase() || '家')
const roleLabel = computed(() => {
  if (!user.value) return '未登录'
  return user.value.role === 'admin' ? '管理员' : '家庭成员'
})
</script>

<template>
  <aside class="desktop-sidebar h-dvh flex-col border-r border-[var(--border)] px-4 py-5">
    <div class="flex items-center gap-3 px-2">
      <div class="brand-mark">
        <FamilySeal compact :label="familyName" />
      </div>
      <div class="min-w-0">
        <p class="truncate text-base font-semibold leading-5 text-[var(--text)]">{{ familyName }}</p>
        <p class="mt-0.5 text-xs text-[var(--text-muted)]">家庭记忆中枢</p>
      </div>
    </div>

    <RouterLink
      to="/publish"
      class="publish-button mt-6 inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-[var(--accent)] px-4 text-sm font-semibold text-white hover:bg-[var(--accent-strong)] active:scale-[0.99]"
    >
      <Plus :size="18" stroke-width="2" aria-hidden="true" />
      发布记忆
    </RouterLink>

    <nav class="mt-7 space-y-1.5" aria-label="主导航">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sidebar-link flex h-11 items-center gap-3 rounded-lg border border-transparent px-3 text-sm font-medium text-[var(--text-secondary)]"
        active-class="sidebar-link-active !border-[var(--border-focus)] !bg-[var(--surface-elevated)] !text-[var(--text)]"
      >
        <component :is="item.icon" :size="18" stroke-width="1.9" aria-hidden="true" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>

    <div class="profile-card mt-auto rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)] p-3">
      <RouterLink
        v-if="user"
        :to="`/profile/${user.id}`"
        class="flex items-center gap-3 transition-opacity hover:opacity-90"
      >
        <img
          v-if="user.avatar_url"
          :src="user.avatar_url"
          :alt="user.username"
          class="h-10 w-10 rounded-lg object-cover"
        />
        <div
          v-else
          class="grid h-10 w-10 place-items-center rounded-lg bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]"
          aria-hidden="true"
        >
          {{ userInitial }}
        </div>
        <div class="min-w-0">
          <p class="truncate text-sm font-medium text-[var(--text)]">{{ user.username }}</p>
          <p class="text-xs text-[var(--text-muted)]">{{ roleLabel }}</p>
        </div>
      </RouterLink>

      <RouterLink v-else to="/login" class="flex items-center gap-3 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text)]">
        <div class="grid h-10 w-10 place-items-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
          <UserCircle :size="19" stroke-width="1.9" aria-hidden="true" />
        </div>
        <span>登录家庭空间</span>
      </RouterLink>
    </div>
  </aside>
</template>

<style scoped>
.desktop-sidebar {
  background:
    linear-gradient(180deg, rgba(255, 248, 235, 0.92), rgba(250, 225, 196, 0.9)),
    var(--surface-panel);
  backdrop-filter: blur(18px);
  box-shadow: inset -1px 0 rgba(132, 74, 40, 0.06), 10px 0 34px rgba(143, 80, 40, 0.08);
}

.brand-mark {
  display: grid;
  height: 2.5rem;
  place-items: center;
  width: 2.5rem;
  box-shadow: 0 8px 22px rgba(217, 74, 74, 0.1);
  transition: border-color 180ms ease, transform 180ms ease;
}

.desktop-sidebar:hover .brand-mark {
  border-color: rgba(227, 107, 93, 0.36);
  transform: translateY(-1px);
}

.publish-button,
.sidebar-link,
.profile-card {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.publish-button {
  box-shadow: 0 10px 26px rgba(217, 74, 74, 0.18);
}

.publish-button:hover {
  box-shadow: 0 14px 34px rgba(217, 74, 74, 0.24);
  transform: translateY(-1px);
}

.sidebar-link {
  position: relative;
}

.sidebar-link::before {
  background: var(--accent);
  border-radius: 999px;
  content: '';
  height: 1.15rem;
  left: -0.15rem;
  opacity: 0;
  position: absolute;
  transform: scaleY(0.55);
  transition: opacity 180ms ease, transform 180ms ease;
  width: 0.18rem;
}

.sidebar-link:hover {
  background: rgba(217, 77, 48, 0.08);
  border-color: rgba(217, 77, 48, 0.16);
  color: var(--text);
  transform: translateX(2px);
}

.sidebar-link-active {
  box-shadow: inset 0 0 0 1px rgba(217, 77, 48, 0.08), 0 10px 24px rgba(143, 80, 40, 0.1);
}

.sidebar-link-active::before {
  opacity: 1;
  transform: scaleY(1);
}

.profile-card:hover {
  border-color: rgba(217, 77, 48, 0.18);
  box-shadow: 0 10px 28px rgba(143, 80, 40, 0.12);
}

@media (prefers-reduced-motion: reduce) {
  .brand-mark,
  .publish-button,
  .sidebar-link,
  .profile-card,
  .sidebar-link::before {
    transition: none;
  }

  .desktop-sidebar:hover .brand-mark,
  .publish-button:hover,
  .sidebar-link:hover {
    transform: none;
  }
}
</style>
