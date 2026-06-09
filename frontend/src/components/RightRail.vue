<script setup lang="ts">
export interface RightRailSection {
  title: string
  body?: string
  meta?: string
}

withDefaults(
  defineProps<{
    title?: string
    description?: string
    sections?: RightRailSection[]
  }>(),
  {
    title: '',
    description: '',
    sections: () => [],
  }
)
</script>

<template>
  <aside class="right-rail rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4 shadow-[var(--shadow-panel)]">
    <slot name="header">
      <header v-if="title || description" class="mb-4 space-y-1">
        <h2 v-if="title" class="text-sm font-semibold text-[var(--text)]">{{ title }}</h2>
        <p v-if="description" class="text-xs leading-5 text-[var(--text-muted)]">{{ description }}</p>
      </header>
    </slot>

    <slot>
      <div v-if="sections.length" class="divide-y divide-[var(--border)]">
        <section v-for="section in sections" :key="section.title" class="rail-section py-3 first:pt-0 last:pb-0">
          <p v-if="section.meta" class="mb-1 text-[11px] font-medium uppercase tracking-[0.08em] text-[var(--text-muted)]">
            {{ section.meta }}
          </p>
          <h3 class="text-sm font-medium text-[var(--text)]">{{ section.title }}</h3>
          <p v-if="section.body" class="mt-1 text-xs leading-5 text-[var(--text-secondary)]">{{ section.body }}</p>
        </section>
      </div>
    </slot>

    <slot name="footer" />
  </aside>
</template>

<style scoped>
.right-rail {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.34), rgba(255, 238, 211, 0.12)),
    var(--surface-panel);
  transition:
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.right-rail:hover {
  border-color: rgba(217, 77, 48, 0.18);
  box-shadow: 0 18px 42px rgba(143, 80, 40, 0.13);
  transform: translateY(-1px);
}

.rail-section {
  transition: opacity 170ms ease, transform 170ms ease;
}

.rail-section:hover {
  opacity: 0.94;
  transform: translateX(2px);
}

@media (prefers-reduced-motion: reduce) {
  .right-rail,
  .rail-section {
    transition: none;
  }

  .right-rail:hover,
  .rail-section:hover {
    transform: none;
  }
}
</style>
