<script setup lang="ts">
import { computed, useSlots } from 'vue'
import DesktopSidebar from '@/components/DesktopSidebar.vue'
import MediaSearchPanel from '@/components/MediaSearchPanel.vue'
import MobileTopNav from '@/components/MobileTopNav.vue'
import { useFamilySettings } from '@/composables/useFamilySettings'

const props = withDefaults(
  defineProps<{
    familyName?: string
    pageTitle?: string
    pageDescription?: string
  }>(),
  {
    familyName: '',
    pageTitle: '',
    pageDescription: '',
  }
)

const slots = useSlots()
const hasRightRail = computed(() => Boolean(slots.right))
const { familyName: configuredFamilyName, backgroundImage } = useFamilySettings()
const displayFamilyName = computed(() => props.familyName || configuredFamilyName.value)
const shellStyle = computed(() => ({
  '--family-background-image': backgroundImage.value ? `url("${backgroundImage.value}")` : 'none',
}))
</script>

<template>
  <div class="family-shell min-h-dvh text-[var(--text)]" :style="shellStyle">
    <MobileTopNav class="lg:hidden" :title="displayFamilyName" />

    <div class="mx-auto grid min-h-dvh w-full lg:grid-cols-[16rem_minmax(0,1fr)] xl:grid-cols-[17rem_minmax(0,1fr)]">
      <DesktopSidebar class="hidden lg:flex" :family-name="displayFamilyName" />

      <div class="min-w-0">
        <main class="shell-main mx-auto w-full px-4 pb-14 pt-5 sm:px-6 lg:px-8 lg:py-8 xl:px-10">
          <div
            class="mx-auto mb-5 w-full"
            :class="hasRightRail ? 'max-w-[76rem]' : 'max-w-[58rem]'"
          >
            <MediaSearchPanel />
          </div>

          <div
            v-if="pageTitle || pageDescription || $slots.header"
            class="mx-auto mb-6 w-full"
            :class="hasRightRail ? 'max-w-[76rem]' : 'max-w-[58rem]'"
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
            :class="
              hasRightRail
                ? 'max-w-[76rem] lg:grid-cols-[minmax(0,1fr)_17rem] xl:grid-cols-[minmax(0,54rem)_20rem] 2xl:grid-cols-[minmax(0,58rem)_21rem]'
                : 'max-w-[58rem]'
            "
          >
            <section class="min-w-0">
              <slot />
            </section>

            <aside v-if="hasRightRail" class="hidden min-w-0 lg:sticky lg:top-8 lg:block lg:self-start">
              <slot name="right" />
            </aside>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.family-shell {
  --family-background-image: none;
  isolation: isolate;
  overflow: hidden;
  position: relative;
  background:
    linear-gradient(180deg, rgba(255, 248, 235, 0.78), rgba(255, 238, 211, 0.54)),
    var(--family-background-image),
    linear-gradient(180deg, rgba(255, 248, 235, 0.78) 0%, rgba(255, 238, 211, 0.46) 34%, rgba(242, 189, 119, 0.28) 100%),
    linear-gradient(100deg, rgba(217, 77, 48, 0.08), rgba(255, 255, 255, 0) 42%, rgba(92, 121, 84, 0.08)),
    transparent;
  background-attachment: fixed;
  background-position: center;
  background-size: auto, cover, auto, auto;
}

.family-shell::before,
.family-shell::after {
  content: '';
  pointer-events: none;
  position: fixed;
  z-index: 0;
}

.family-shell > * {
  position: relative;
  z-index: 1;
}

.family-shell::before {
  animation: ring-drift 16s ease-in-out infinite;
  background:
    conic-gradient(from 16deg, rgba(217, 77, 48, 0.2), rgba(212, 137, 37, 0.26), rgba(92, 121, 84, 0.16), rgba(217, 77, 48, 0.2));
  border: 1px solid rgba(132, 74, 40, 0.14);
  border-radius: 999px;
  height: min(26vw, 16rem);
  opacity: 0.42;
  right: clamp(1rem, 6vw, 5rem);
  top: 5.5rem;
  width: min(26vw, 16rem);
}

.family-shell::after {
  animation: ribbon-breathe 13s ease-in-out infinite alternate;
  background:
    linear-gradient(92deg, rgba(217, 77, 48, 0), rgba(217, 77, 48, 0.22), rgba(212, 137, 37, 0.18), rgba(217, 77, 48, 0));
  border-radius: 999px;
  bottom: 12vh;
  filter: blur(0.5px);
  height: 4rem;
  left: clamp(-5rem, -3vw, -1rem);
  opacity: 0.54;
  transform: rotate(-9deg);
  width: min(34rem, 58vw);
}

.shell-main {
  animation: shell-content-in 420ms ease-out both;
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
  .family-shell::before,
  .family-shell::after {
    animation: none;
  }
}
</style>
