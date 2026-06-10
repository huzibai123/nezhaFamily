import { computed, ref } from 'vue'
import { getFamilySettings, type FamilySettings, type FamilyThemeAssets } from '@/api/admin'

const defaultThemeAssets: FamilyThemeAssets = {
  backgrounds: [],
  cursor: null,
  ornaments: [],
}

const defaultSettings: FamilySettings = {
  family_name: '哪吒家庭',
  tagline: '私有的家庭记忆中枢',
  theme_color: '#f6f1e8',
  accent_color: '#c9432f',
  background_image_url: '',
  logo_url: '',
  theme_assets: defaultThemeAssets,
}

const settings = ref<FamilySettings>({ ...defaultSettings })
const loaded = ref(false)
const loading = ref(false)

const familyName = computed(() => settings.value.family_name || defaultSettings.family_name)
const tagline = computed(() => settings.value.tagline || defaultSettings.tagline)
const themeAssets = computed(() => normalizeThemeAssets(settings.value.theme_assets))
const backgroundImage = computed(() => {
  const activeUrl = settings.value.background_image_url || ''
  if (activeUrl) return activeUrl
  return themeAssets.value.backgrounds.find(asset => asset.enabled)?.url || ''
})
const logoUrl = computed(() => settings.value.logo_url || '')

async function loadFamilySettings(force = false) {
  if (loading.value || (loaded.value && !force)) return settings.value
  if (!localStorage.getItem('token')) {
    applySettings(settings.value)
    return settings.value
  }

  loading.value = true

  try {
    const remoteSettings = await getFamilySettings()
    setFamilySettings(remoteSettings)
    loaded.value = true
  } catch {
    applySettings(settings.value)
  } finally {
    loading.value = false
  }

  return settings.value
}

function setFamilySettings(nextSettings: Partial<FamilySettings>) {
  const nextThemeAssets = normalizeThemeAssets(
    nextSettings.theme_assets ?? settings.value.theme_assets ?? defaultThemeAssets,
  )
  settings.value = {
    ...settings.value,
    ...nextSettings,
    family_name: nextSettings.family_name || settings.value.family_name || defaultSettings.family_name,
    tagline: nextSettings.tagline ?? settings.value.tagline ?? defaultSettings.tagline,
    theme_color: nextSettings.theme_color || settings.value.theme_color || defaultSettings.theme_color,
    accent_color: nextSettings.accent_color || settings.value.accent_color || defaultSettings.accent_color,
    background_image_url: nextSettings.background_image_url ?? settings.value.background_image_url ?? '',
    logo_url: nextSettings.logo_url ?? settings.value.logo_url ?? '',
    theme_assets: nextThemeAssets,
  }
  applySettings(settings.value)
}

function applySettings(value: FamilySettings) {
  const root = document.documentElement
  if (value.theme_color) root.style.setProperty('--surface', value.theme_color)
  if (value.accent_color) {
    root.style.setProperty('--accent', value.accent_color)
    const rgb = hexToRgb(value.accent_color)
    if (rgb) {
      root.style.setProperty('--accent-soft', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.12)`)
      root.style.setProperty('--border-focus', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.38)`)
      root.style.setProperty('--accent-strong', darkenRgb(rgb, 0.18))
    }
  }
}

function normalizeThemeAssets(value?: FamilyThemeAssets | null): FamilyThemeAssets {
  return {
    backgrounds: (value?.backgrounds || []).slice(0, 12).map(asset => ({
      id: asset.id,
      url: asset.url,
      label: asset.label || '',
      enabled: asset.enabled !== false,
    })),
    cursor: value?.cursor
      ? {
          url: value.cursor.url || '',
          enabled: Boolean(value.cursor.enabled && value.cursor.url),
          size: clampNumber(value.cursor.size, 24, 160, 76),
        }
      : null,
    ornaments: (value?.ornaments || []).slice(0, 8).map(asset => ({
      id: asset.id,
      url: asset.url,
      position: asset.position,
      enabled: asset.enabled !== false,
      size: clampNumber(asset.size, 24, 220, 96),
      opacity: clampNumber(asset.opacity, 0.1, 1, 0.72),
    })),
  }
}

function clampNumber(value: number | undefined, min: number, max: number, fallback: number) {
  if (typeof value !== 'number' || Number.isNaN(value)) return fallback
  return Math.min(max, Math.max(min, value))
}

function hexToRgb(value: string): { r: number; g: number; b: number } | null {
  const match = value.trim().match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i)
  if (!match) return null
  return {
    r: parseInt(match[1], 16),
    g: parseInt(match[2], 16),
    b: parseInt(match[3], 16),
  }
}

function darkenRgb(rgb: { r: number; g: number; b: number }, amount: number): string {
  const darken = (channel: number) => Math.max(0, Math.round(channel * (1 - amount)))
  return `rgb(${darken(rgb.r)}, ${darken(rgb.g)}, ${darken(rgb.b)})`
}

export function useFamilySettings() {
  return {
    settings,
    familyName,
    tagline,
    backgroundImage,
    logoUrl,
    themeAssets,
    loaded,
    loading,
    loadFamilySettings,
    setFamilySettings,
  }
}
