<script setup lang="ts">
import { mediaUrl } from '@/utils/media'

withDefaults(
  defineProps<{
    label?: string
    compact?: boolean
    logoUrl?: string
  }>(),
  {
    label: '哪吒家庭',
    compact: false,
    logoUrl: '',
  }
)
</script>

<template>
  <div class="family-seal" :class="{ 'family-seal-compact': compact }" aria-hidden="true">
    <template v-if="logoUrl">
      <span class="seal-logo-ring"></span>
      <img class="seal-logo" :src="mediaUrl(logoUrl)" :alt="label" />
    </template>
    <template v-else>
      <span class="seal-ring"></span>
      <span class="seal-flame seal-flame-a"></span>
      <span class="seal-flame seal-flame-b"></span>
      <span class="seal-text">{{ label.slice(0, 4) }}</span>
    </template>
  </div>
</template>

<style scoped>
.family-seal {
  aspect-ratio: 1;
  display: grid;
  isolation: isolate;
  place-items: center;
  position: relative;
  width: 6.5rem;
}

.family-seal-compact {
  width: 3rem;
}

.seal-ring {
  animation: seal-ring-turn 12s linear infinite;
  background:
    conic-gradient(from 18deg, rgba(201, 67, 47, 0.78), rgba(45, 108, 104, 0.62), rgba(66, 81, 132, 0.44), rgba(201, 67, 47, 0.78));
  border-radius: 999px;
  inset: 0;
  mask: radial-gradient(circle, transparent 0 54%, #000 55% 63%, transparent 64%);
  position: absolute;
}

.seal-logo-ring {
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.72), rgba(246, 241, 232, 0.34)),
    conic-gradient(from 18deg, rgba(201, 67, 47, 0.72), rgba(45, 108, 104, 0.46), rgba(66, 81, 132, 0.36), rgba(201, 67, 47, 0.72));
  border: 1px solid rgba(63, 45, 36, 0.14);
  border-radius: 18px;
  box-shadow: 0 18px 38px rgba(63, 45, 36, 0.14);
  inset: 0.35rem;
  position: absolute;
}

.seal-logo {
  aspect-ratio: 1;
  border-radius: 14px;
  height: calc(100% - 1rem);
  object-fit: cover;
  position: relative;
  width: calc(100% - 1rem);
}

.seal-ring::before,
.seal-ring::after {
  background: rgba(255, 255, 252, 0.74);
  border: 1px solid rgba(49, 38, 33, 0.14);
  border-radius: 999px;
  content: '';
  height: 0.45rem;
  position: absolute;
  top: calc(50% - 0.225rem);
  width: 0.45rem;
}

.seal-ring::before {
  left: 0.55rem;
}

.seal-ring::after {
  right: 0.55rem;
}

.seal-flame {
  background:
    radial-gradient(circle at 45% 64%, rgba(255, 243, 197, 0.9) 0 12%, transparent 13%),
    conic-gradient(from 24deg, rgba(201, 67, 47, 0), rgba(201, 67, 47, 0.66), rgba(45, 108, 104, 0.42), rgba(201, 67, 47, 0));
  border-radius: 68% 32% 62% 38%;
  filter: drop-shadow(0 6px 12px rgba(201, 67, 47, 0.14));
  height: 1.4rem;
  position: absolute;
  width: 2.1rem;
  z-index: -1;
}

.seal-flame-a {
  animation: seal-flame-a 4.8s ease-in-out infinite;
  right: 0.35rem;
  top: 0.8rem;
}

.seal-flame-b {
  animation: seal-flame-b 5.4s ease-in-out infinite;
  bottom: 0.9rem;
  left: 0.5rem;
  opacity: 0.72;
}

.seal-text {
  align-items: center;
  background:
    linear-gradient(180deg, rgba(255, 255, 252, 0.88), rgba(238, 231, 219, 0.8));
  border: 1px solid rgba(49, 38, 33, 0.16);
  border-radius: 12px;
  box-shadow: 0 14px 32px rgba(47, 39, 35, 0.1);
  color: var(--accent);
  display: inline-flex;
  font-size: 0.86rem;
  font-weight: 700;
  height: 3.1rem;
  justify-content: center;
  line-height: 1.1;
  padding: 0.35rem;
  text-align: center;
  width: 3.1rem;
}

.family-seal-compact .seal-text {
  border-radius: 9px;
  font-size: 0;
  height: 1.65rem;
  width: 1.65rem;
}

.family-seal-compact .seal-text::before {
  content: '家';
  font-size: 0.82rem;
}

.family-seal-compact .seal-flame {
  height: 0.72rem;
  width: 1rem;
}

.family-seal-compact .seal-logo-ring {
  border-radius: 12px;
  inset: 0.22rem;
}

.family-seal-compact .seal-logo {
  border-radius: 10px;
  height: calc(100% - 0.64rem);
  width: calc(100% - 0.64rem);
}

@keyframes seal-ring-turn {
  to {
    transform: rotate(1turn);
  }
}

@keyframes seal-flame-a {
  0%,
  100% {
    transform: translate3d(0, 0, 0) rotate(18deg) scale(0.94);
  }
  50% {
    transform: translate3d(-0.25rem, 0.15rem, 0) rotate(32deg) scale(1.04);
  }
}

@keyframes seal-flame-b {
  0%,
  100% {
    transform: translate3d(0, 0, 0) rotate(198deg) scale(0.9);
  }
  50% {
    transform: translate3d(0.18rem, -0.1rem, 0) rotate(182deg) scale(1.06);
  }
}

@media (prefers-reduced-motion: reduce) {
  .seal-ring,
  .seal-flame-a,
  .seal-flame-b {
    animation: none;
  }
}
</style>
