<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useFamilySettings } from '@/composables/useFamilySettings'
import { mediaUrl } from '@/utils/media'

const isEnabled = ref(false)
const cursorRef = ref<HTMLElement | null>(null)
const { themeAssets } = useFamilySettings()

const customCursor = computed(() => {
  const cursor = themeAssets.value.cursor
  return cursor?.enabled && cursor.url ? cursor : null
})

const cursorStyle = computed(() => ({
  '--cursor-size': customCursor.value ? `${customCursor.value.size}px` : '5.75rem',
}))

let pointerQuery: MediaQueryList | null = null
let motionQuery: MediaQueryList | null = null
let desktopQuery: MediaQueryList | null = null
let frameId = 0
let targetX = 0
let targetY = 0
let currentX = 0
let currentY = 0
let hasPointer = false

const applyPosition = () => {
  frameId = 0

  if (!cursorRef.value || !hasPointer) return

  currentX += (targetX - currentX) * 0.24
  currentY += (targetY - currentY) * 0.24

  cursorRef.value.style.setProperty('--nezha-x', `${currentX}px`)
  cursorRef.value.style.setProperty('--nezha-y', `${currentY}px`)

  if (Math.abs(targetX - currentX) > 0.2 || Math.abs(targetY - currentY) > 0.2) {
    frameId = window.requestAnimationFrame(applyPosition)
  }
}

const queuePosition = (event: PointerEvent) => {
  if (!isEnabled.value || event.pointerType !== 'mouse') return

  targetX = event.clientX
  targetY = event.clientY

  if (!hasPointer) {
    hasPointer = true
    currentX = targetX
    currentY = targetY
    cursorRef.value?.classList.add('is-visible')
  }

  if (!frameId) {
    frameId = window.requestAnimationFrame(applyPosition)
  }
}

const hideCursor = () => {
  hasPointer = false
  cursorRef.value?.classList.remove('is-visible')
}

const syncAvailability = () => {
  const canUsePointer = pointerQuery?.matches ?? false
  const allowsMotion = !(motionQuery?.matches ?? true)
  const hasDesktopViewport = desktopQuery?.matches ?? false
  isEnabled.value = canUsePointer && allowsMotion && hasDesktopViewport

  if (!isEnabled.value) {
    hideCursor()
    if (frameId) {
      window.cancelAnimationFrame(frameId)
      frameId = 0
    }
  }
}

onMounted(() => {
  pointerQuery = window.matchMedia('(hover: hover) and (pointer: fine)')
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  desktopQuery = window.matchMedia('(min-width: 1024px)')

  syncAvailability()

  pointerQuery.addEventListener('change', syncAvailability)
  motionQuery.addEventListener('change', syncAvailability)
  desktopQuery.addEventListener('change', syncAvailability)
  window.addEventListener('pointermove', queuePosition, { passive: true })
  window.addEventListener('pointerleave', hideCursor)
  window.addEventListener('blur', hideCursor)
})

onBeforeUnmount(() => {
  pointerQuery?.removeEventListener('change', syncAvailability)
  motionQuery?.removeEventListener('change', syncAvailability)
  desktopQuery?.removeEventListener('change', syncAvailability)
  window.removeEventListener('pointermove', queuePosition)
  window.removeEventListener('pointerleave', hideCursor)
  window.removeEventListener('blur', hideCursor)

  if (frameId) {
    window.cancelAnimationFrame(frameId)
  }
})
</script>

<template>
  <div v-if="isEnabled" ref="cursorRef" class="nezha-cursor" :style="cursorStyle" aria-hidden="true">
    <img
      v-if="customCursor"
      class="nezha-cursor__image"
      :src="mediaUrl(customCursor.url || '')"
      alt=""
    />
    <template v-else>
      <span class="nezha-cursor__silk nezha-cursor__silk--back"></span>
      <span class="nezha-cursor__wheel nezha-cursor__wheel--left"></span>
      <span class="nezha-cursor__ring"></span>
      <span class="nezha-cursor__wheel nezha-cursor__wheel--right"></span>
      <span class="nezha-cursor__silk nezha-cursor__silk--front"></span>
    </template>
  </div>
</template>

<style scoped>
.nezha-cursor {
  --cursor-size: 5.75rem;
  --nezha-x: -8rem;
  --nezha-y: -8rem;
  contain: layout style paint;
  height: var(--cursor-size);
  inset: 0 auto auto 0;
  opacity: 0;
  pointer-events: none;
  position: fixed;
  transform: translate3d(
    calc(var(--nezha-x) - (var(--cursor-size) / 2)),
    calc(var(--nezha-y) - (var(--cursor-size) / 2)),
    0
  );
  transition: opacity 180ms ease;
  width: var(--cursor-size);
  z-index: 35;
}

.nezha-cursor.is-visible {
  opacity: 0.82;
}

.nezha-cursor__image {
  height: 100%;
  object-fit: contain;
  width: 100%;
  filter: drop-shadow(0 12px 22px rgba(44, 32, 28, 0.2));
}

.nezha-cursor__ring,
.nezha-cursor__wheel,
.nezha-cursor__silk {
  left: 50%;
  position: absolute;
  top: 50%;
  transform-style: preserve-3d;
}

.nezha-cursor__ring {
  animation: nezha-ring-drift 2.8s ease-in-out infinite;
  border: 2px solid rgba(255, 211, 122, 0.86);
  border-left-color: rgba(255, 245, 215, 0.36);
  border-radius: 999px;
  box-shadow:
    0 0 0 1px rgba(159, 74, 38, 0.32),
    0 0 18px rgba(239, 121, 59, 0.22),
    inset 0 0 8px rgba(255, 238, 184, 0.14);
  height: 2.2rem;
  margin: -1.1rem 0 0 -1.1rem;
  width: 2.2rem;
}

.nezha-cursor__ring::before,
.nezha-cursor__ring::after {
  background: rgba(255, 234, 175, 0.9);
  border-radius: 999px;
  box-shadow: 0 0 8px rgba(246, 131, 72, 0.34);
  content: '';
  height: 0.26rem;
  position: absolute;
  top: 50%;
  width: 0.26rem;
}

.nezha-cursor__ring::before {
  left: 0.16rem;
  transform: translateY(-50%);
}

.nezha-cursor__ring::after {
  right: 0.16rem;
  transform: translateY(-50%);
}

.nezha-cursor__wheel {
  animation: nezha-wheel-spin 1.45s linear infinite;
  border: 1px solid rgba(255, 197, 98, 0.72);
  border-radius: 999px;
  height: 1.02rem;
  margin: -0.51rem 0 0 -0.51rem;
  width: 1.02rem;
}

.nezha-cursor__wheel::before,
.nezha-cursor__wheel::after {
  background:
    radial-gradient(circle at 50% 65%, rgba(255, 234, 159, 0.95) 0 11%, transparent 12%),
    conic-gradient(from 24deg, rgba(255, 82, 49, 0), rgba(255, 119, 47, 0.85), rgba(255, 205, 91, 0), rgba(255, 82, 49, 0.72), rgba(255, 82, 49, 0));
  border-radius: 60% 40% 64% 36%;
  content: '';
  inset: -0.54rem -0.36rem -0.12rem;
  opacity: 0.84;
  position: absolute;
}

.nezha-cursor__wheel::after {
  filter: blur(5px);
  opacity: 0.38;
}

.nezha-cursor__wheel--left {
  transform: translate3d(-1.58rem, 1.34rem, 0) rotate(-16deg);
}

.nezha-cursor__wheel--right {
  animation-direction: reverse;
  transform: translate3d(1.62rem, -1.18rem, 0) rotate(18deg);
}

.nezha-cursor__silk {
  background:
    linear-gradient(90deg, rgba(255, 87, 70, 0), rgba(255, 101, 78, 0.72) 22%, rgba(255, 55, 62, 0.76) 58%, rgba(255, 130, 89, 0)),
    linear-gradient(180deg, rgba(255, 235, 196, 0.42), rgba(255, 235, 196, 0));
  border-radius: 999px;
  filter: drop-shadow(0 0 8px rgba(241, 74, 49, 0.2));
  height: 0.52rem;
  margin: -0.26rem 0 0 -2.2rem;
  opacity: 0.78;
  transform-origin: 2.2rem 50%;
  width: 4.4rem;
}

.nezha-cursor__silk--back {
  animation: nezha-silk-back 2.2s ease-in-out infinite;
}

.nezha-cursor__silk--front {
  animation: nezha-silk-front 2.2s ease-in-out infinite;
}

@keyframes nezha-ring-drift {
  0%,
  100% {
    transform: rotate(-12deg) scale(0.98);
  }

  50% {
    transform: rotate(16deg) scale(1.06);
  }
}

@keyframes nezha-wheel-spin {
  to {
    rotate: 1turn;
  }
}

@keyframes nezha-silk-back {
  0%,
  100% {
    transform: translate3d(-0.58rem, 0.16rem, 0) rotate(24deg) scaleX(0.82);
  }

  50% {
    transform: translate3d(-0.82rem, 0.34rem, 0) rotate(7deg) scaleX(1);
  }
}

@keyframes nezha-silk-front {
  0%,
  100% {
    transform: translate3d(0.44rem, -0.22rem, 0) rotate(-27deg) scaleX(0.74);
  }

  50% {
    transform: translate3d(0.74rem, -0.42rem, 0) rotate(-8deg) scaleX(1.04);
  }
}

@media (max-width: 1023px), (hover: none), (pointer: coarse), (prefers-reduced-motion: reduce) {
  .nezha-cursor {
    display: none;
  }
}
</style>
