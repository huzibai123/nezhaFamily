<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, type CSSProperties } from 'vue'
import type { ThemeOrnamentAsset } from '@/api/admin'
import { useFamilySettings } from '@/composables/useFamilySettings'
import { mediaUrl } from '@/utils/media'

defineOptions({ inheritAttrs: false })

const { backgroundImage, themeAssets } = useFamilySettings()
const petLayerRef = ref<HTMLElement | null>(null)

const enabledOrnaments = computed(() =>
  themeAssets.value.ornaments.filter(asset => asset.enabled && asset.url)
)

const floatingOrnaments = computed(() =>
  enabledOrnaments.value.map((ornament, index) => ({
    ornament,
    style: createPatrolStyle(ornament, index),
  }))
)

type PatrolStyle = CSSProperties & Record<`--${string}`, string>
type PatrolRange = {
  x: [number, number]
  y: [number, number]
}

const anchorRanges: Record<ThemeOrnamentAsset['position'], PatrolRange> = {
  'top-left': { x: [7, 22], y: [12, 30] },
  'top-right': { x: [62, 78], y: [12, 30] },
  'bottom-left': { x: [7, 24], y: [56, 74] },
  'bottom-right': { x: [60, 78], y: [56, 74] },
}

let pointerQuery: MediaQueryList | null = null
let motionQuery: MediaQueryList | null = null
let proximityFrame = 0
let lastPointerEvent: PointerEvent | null = null
let canTrackPointer = false

function createPatrolStyle(ornament: ThemeOrnamentAsset, index: number): PatrolStyle {
  const seed = hashString(`${ornament.id}:${ornament.url}:${index}`)
  const anchor = anchorRanges[ornament.position] || anchorRanges['top-left']
  const duration = seededRange(seed + 101, 24, 42)

  return {
    '--pet-size': `${ornament.size}px`,
    '--pet-opacity': `${ornament.opacity}`,
    '--pet-x-start': `${seededRange(seed + 1, anchor.x[0], anchor.x[1])}vw`,
    '--pet-y-start': `${seededRange(seed + 2, anchor.y[0], anchor.y[1])}vh`,
    '--pet-x-scout': `${seededRange(seed + 13, 18, 76)}vw`,
    '--pet-y-scout': `${seededRange(seed + 17, 14, 68)}vh`,
    '--pet-x-mid': `${seededRange(seed + 29, 10, 72)}vw`,
    '--pet-y-mid': `${seededRange(seed + 31, 18, 74)}vh`,
    '--pet-x-end': `${seededRange(seed + 43, 18, 78)}vw`,
    '--pet-y-end': `${seededRange(seed + 47, 12, 72)}vh`,
    '--pet-duration': `${duration}s`,
    '--pet-delay': `-${seededRange(seed + 53, 0, duration)}s`,
    '--pet-tilt-a': `${seededRange(seed + 59, -9, 9)}deg`,
    '--pet-tilt-b': `${seededRange(seed + 61, -13, 13)}deg`,
    '--pet-tilt-c': `${seededRange(seed + 67, -8, 8)}deg`,
    '--pet-hover-tilt-a': `${seededRange(seed + 71, -10, 10)}deg`,
    '--pet-hover-tilt-b': `${seededRange(seed + 73, -12, 12)}deg`,
  }
}

function hashString(value: string) {
  let hash = 2166136261

  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }

  return Math.abs(hash)
}

function seededRange(seed: number, min: number, max: number) {
  const value = Math.sin(seed) * 10000
  const unit = value - Math.floor(value)
  return Math.round((min + unit * (max - min)) * 100) / 100
}

function clearPetProximity() {
  petLayerRef.value
    ?.querySelectorAll<HTMLElement>('.family-decor-layer__pet.is-near')
    .forEach(pet => pet.classList.remove('is-near'))
}

function syncPointerTracking() {
  canTrackPointer = Boolean(pointerQuery?.matches) && !Boolean(motionQuery?.matches)

  if (!canTrackPointer) {
    clearPetProximity()
  }
}

function applyPetProximity() {
  proximityFrame = 0

  if (!canTrackPointer || !lastPointerEvent || !petLayerRef.value) return

  const pointerX = lastPointerEvent.clientX
  const pointerY = lastPointerEvent.clientY

  petLayerRef.value
    .querySelectorAll<HTMLElement>('.family-decor-layer__pet')
    .forEach(pet => {
      const rect = pet.getBoundingClientRect()
      if (!rect.width || !rect.height) return

      const centerX = rect.left + rect.width / 2
      const centerY = rect.top + rect.height / 2
      const distance = Math.hypot(pointerX - centerX, pointerY - centerY)
      const threshold = Math.max(rect.width * 1.15, 92)

      pet.classList.toggle('is-near', distance < threshold)
    })
}

function queuePetProximity(event: PointerEvent) {
  if (!canTrackPointer || event.pointerType !== 'mouse') return

  lastPointerEvent = event

  if (!proximityFrame) {
    proximityFrame = window.requestAnimationFrame(applyPetProximity)
  }
}

onMounted(() => {
  pointerQuery = window.matchMedia('(hover: hover) and (pointer: fine)')
  motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')

  syncPointerTracking()

  pointerQuery.addEventListener('change', syncPointerTracking)
  motionQuery.addEventListener('change', syncPointerTracking)
  window.addEventListener('pointermove', queuePetProximity, { passive: true })
  window.addEventListener('pointerleave', clearPetProximity)
  window.addEventListener('blur', clearPetProximity)
})

onBeforeUnmount(() => {
  pointerQuery?.removeEventListener('change', syncPointerTracking)
  motionQuery?.removeEventListener('change', syncPointerTracking)
  window.removeEventListener('pointermove', queuePetProximity)
  window.removeEventListener('pointerleave', clearPetProximity)
  window.removeEventListener('blur', clearPetProximity)

  if (proximityFrame) {
    window.cancelAnimationFrame(proximityFrame)
  }
})
</script>

<template>
  <div v-bind="$attrs" class="family-decor-layer" aria-hidden="true">
    <div
      v-if="backgroundImage"
      class="family-decor-layer__background"
      :style="{ backgroundImage: `url('${mediaUrl(backgroundImage)}')` }"
    ></div>
    <div class="family-decor-layer__scrim"></div>
  </div>

  <Teleport to="body">
    <div
      v-if="floatingOrnaments.length"
      ref="petLayerRef"
      class="family-decor-layer__pet-field"
      aria-hidden="true"
    >
      <span
        v-for="{ ornament, style } in floatingOrnaments"
        :key="ornament.id"
        class="family-decor-layer__pet"
        :class="`family-decor-layer__pet--${ornament.position}`"
        :style="style"
      >
        <img
          class="family-decor-layer__pet-image"
          :src="mediaUrl(ornament.url)"
          alt=""
          draggable="false"
        />
      </span>
    </div>
  </Teleport>
</template>

<style scoped>
.family-decor-layer {
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  position: fixed;
}

.family-decor-layer__background {
  background-position: center;
  background-size: cover;
  filter: saturate(0.96) contrast(0.94);
  inset: 0;
  opacity: 0.28;
  position: absolute;
}

.family-decor-layer__scrim {
  background:
    linear-gradient(180deg, rgba(246, 241, 232, 0.88), rgba(232, 224, 210, 0.62)),
    radial-gradient(circle at 18% 12%, rgba(201, 67, 47, 0.1), transparent 32%),
    radial-gradient(circle at 86% 24%, rgba(45, 108, 104, 0.12), transparent 30%),
    radial-gradient(circle at 62% 88%, rgba(66, 81, 132, 0.1), transparent 34%);
  inset: 0;
  position: absolute;
}

.family-decor-layer__pet-field {
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  position: fixed;
  z-index: 80;
}

.family-decor-layer__pet {
  --pet-size: 96px;
  --pet-opacity: 0.72;
  --pet-x-start: 12vw;
  --pet-y-start: 18vh;
  --pet-x-scout: 68vw;
  --pet-y-scout: 26vh;
  --pet-x-mid: 22vw;
  --pet-y-mid: 62vh;
  --pet-x-end: 76vw;
  --pet-y-end: 58vh;
  --pet-duration: 32s;
  --pet-delay: 0s;
  --pet-tilt-a: -4deg;
  --pet-tilt-b: 8deg;
  --pet-tilt-c: -6deg;
  --pet-hover-tilt-a: -7deg;
  --pet-hover-tilt-b: 9deg;
  animation: pet-patrol var(--pet-duration) ease-in-out var(--pet-delay) infinite;
  aspect-ratio: 1;
  display: none;
  left: 0;
  opacity: var(--pet-opacity);
  pointer-events: none;
  position: absolute;
  top: 0;
  transform: translate3d(var(--pet-x-start), var(--pet-y-start), 0) rotate(var(--pet-tilt-a));
  transform-origin: center;
  width: min(var(--pet-size), 18vw, 220px);
  will-change: transform;
}

.family-decor-layer__pet::after {
  background:
    radial-gradient(circle, rgba(255, 247, 216, 0.44), rgba(255, 247, 216, 0) 58%),
    linear-gradient(135deg, rgba(201, 67, 47, 0.2), rgba(45, 108, 104, 0.16));
  border: 1px solid rgba(201, 67, 47, 0.16);
  border-radius: 999px;
  content: '';
  inset: -1rem;
  opacity: 0;
  position: absolute;
  transform: scale(0.68);
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}

.family-decor-layer__pet-image {
  display: block;
  filter: drop-shadow(0 18px 28px rgba(44, 32, 28, 0.18));
  height: 100%;
  object-fit: contain;
  pointer-events: none;
  position: relative;
  transform-origin: center;
  user-select: none;
  width: 100%;
  z-index: 1;
  animation: pet-bob 4.6s ease-in-out infinite alternate;
  transition: filter 180ms ease;
}

.family-decor-layer__pet.is-near {
  animation-play-state: paused;
  z-index: 81;
}

.family-decor-layer__pet.is-near::after {
  opacity: 0.88;
  transform: scale(1);
  animation: pet-halo 820ms ease-in-out infinite alternate;
}

.family-decor-layer__pet.is-near .family-decor-layer__pet-image {
  animation: pet-alert 520ms ease-in-out infinite alternate;
  filter:
    drop-shadow(0 20px 30px rgba(201, 67, 47, 0.2))
    drop-shadow(0 0 16px rgba(255, 210, 120, 0.34));
}

@media (min-width: 768px) {
  .family-decor-layer__pet {
    display: block;
  }
}

@keyframes pet-patrol {
  0% {
    transform: translate3d(var(--pet-x-start), var(--pet-y-start), 0) rotate(var(--pet-tilt-a));
  }
  26% {
    transform: translate3d(var(--pet-x-scout), var(--pet-y-scout), 0) rotate(var(--pet-tilt-b));
  }
  52% {
    transform: translate3d(var(--pet-x-mid), var(--pet-y-mid), 0) rotate(var(--pet-tilt-c));
  }
  78% {
    transform: translate3d(var(--pet-x-end), var(--pet-y-end), 0) rotate(var(--pet-tilt-b));
  }
  100% {
    transform: translate3d(var(--pet-x-start), var(--pet-y-start), 0) rotate(var(--pet-tilt-a));
  }
}

@keyframes pet-bob {
  from {
    transform: translateY(-5px) scale(0.98) rotate(-1deg);
  }
  to {
    transform: translateY(7px) scale(1.02) rotate(1deg);
  }
}

@keyframes pet-alert {
  from {
    transform: translateY(-8px) scale(1.06) rotate(var(--pet-hover-tilt-a));
  }
  to {
    transform: translateY(3px) scale(1.14) rotate(var(--pet-hover-tilt-b));
  }
}

@keyframes pet-halo {
  from {
    filter: blur(0);
    transform: scale(0.92);
  }
  to {
    filter: blur(1px);
    transform: scale(1.08);
  }
}

@media (prefers-reduced-motion: reduce) {
  .family-decor-layer__background {
    filter: none;
  }

  .family-decor-layer__pet,
  .family-decor-layer__pet-image,
  .family-decor-layer__pet.is-near .family-decor-layer__pet-image,
  .family-decor-layer__pet.is-near::after {
    animation: none;
  }

  .family-decor-layer__pet {
    transform: translate3d(var(--pet-x-start), var(--pet-y-start), 0) rotate(var(--pet-tilt-a));
  }

  .family-decor-layer__pet.is-near::after {
    opacity: 0;
  }
}
</style>
