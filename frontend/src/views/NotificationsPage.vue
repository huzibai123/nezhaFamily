<template>
  <AppShell page-title="通知中心" page-description="查看评论、回复、点赞和新动态提醒">
    <template #header>
      <div class="grid gap-2">
        <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Family signals</p>
        <h1 class="text-2xl font-semibold leading-tight tracking-normal text-[var(--text)] sm:text-3xl">
          通知中心
        </h1>
        <p class="max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
          家庭互动会汇总在这里，点进评论通知时会自动定位到对应回复。
        </p>
      </div>
    </template>

    <NotificationCenter :compact="false" />
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from '@/components/AppShell.vue'
import NotificationCenter from '@/components/NotificationCenter.vue'
</script>
