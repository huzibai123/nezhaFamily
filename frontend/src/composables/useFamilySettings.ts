import { computed, ref } from 'vue'
import { getFamilySettings, type FamilySettings } from '@/api/admin'

const defaultSettings: FamilySettings = {
  family_name: '哪吒家庭',
  tagline: '私有的家庭记忆中枢',
  theme_color: '#f8d9b7',
  accent_color: '#d94d30',
  background_image_url: '',
}

const settings = ref<FamilySettings>({ ...defaultSettings })
const loaded = ref(false)
const loading = ref(false)

const familyName = computed(() => settings.value.family_name || defaultSettings.family_name)
const tagline = computed(() => settings.value.tagline || defaultSettings.tagline)
const backgroundImage = computed(() => settings.value.background_image_url || '')

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
  settings.value = {
    ...settings.value,
    ...nextSettings,
    family_name: nextSettings.family_name || settings.value.family_name || defaultSettings.family_name,
    tagline: nextSettings.tagline ?? settings.value.tagline ?? defaultSettings.tagline,
    theme_color: nextSettings.theme_color || settings.value.theme_color || defaultSettings.theme_color,
    accent_color: nextSettings.accent_color || settings.value.accent_color || defaultSettings.accent_color,
    background_image_url: nextSettings.background_image_url ?? settings.value.background_image_url ?? '',
  }
  applySettings(settings.value)
}

function applySettings(value: FamilySettings) {
  const root = document.documentElement
  if (value.theme_color) root.style.setProperty('--surface', value.theme_color)
  if (value.accent_color) root.style.setProperty('--accent', value.accent_color)
}

export function useFamilySettings() {
  return {
    settings,
    familyName,
    tagline,
    backgroundImage,
    loaded,
    loading,
    loadFamilySettings,
    setFamilySettings,
  }
}
