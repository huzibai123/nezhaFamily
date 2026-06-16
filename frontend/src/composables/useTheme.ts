import { computed, ref, watch } from 'vue'
import type { AuthUser } from '@/api/auth'
import { updateUserProfile } from '@/api/users'
import type { Theme } from '@/types/theme'
import { THEMES, defaultTheme, getThemeById } from '@/themes'

const GUEST_STORAGE_KEY = 'nezha-theme:guest'
const LEGACY_STORAGE_KEY = 'nezha-theme'

const themes = ref<Theme[]>(THEMES)
const currentThemeId = ref<string>(readInitialThemeId())
const currentTheme = computed<Theme>(() => getThemeById(currentThemeId.value) || defaultTheme)
const activeUserId = ref<string | null>(null)
const savingTheme = ref(false)
const themeSaveError = ref('')

let themeWatcherStarted = false

function readInitialThemeId(): string {
  if (typeof window === 'undefined') return defaultTheme.id

  const legacyTheme = localStorage.getItem(LEGACY_STORAGE_KEY)
  if (legacyTheme && isThemeId(legacyTheme)) {
    localStorage.setItem(GUEST_STORAGE_KEY, legacyTheme)
    localStorage.removeItem(LEGACY_STORAGE_KEY)
    return legacyTheme
  }

  const guestTheme = localStorage.getItem(GUEST_STORAGE_KEY)
  return guestTheme && isThemeId(guestTheme) ? guestTheme : defaultTheme.id
}

function userThemeKey(userId: string): string {
  return `nezha-theme:user:${userId}`
}

function isThemeId(themeId: string | null | undefined): themeId is string {
  return Boolean(themeId && getThemeById(themeId))
}

function localThemeForUser(userId: string): string | null {
  if (typeof window === 'undefined') return null
  const themeId = localStorage.getItem(userThemeKey(userId))
  return isThemeId(themeId) ? themeId : null
}

function writeLocalTheme(themeId: string, userId = activeUserId.value): void {
  if (typeof window === 'undefined') return

  if (userId) {
    localStorage.setItem(userThemeKey(userId), themeId)
    return
  }

  localStorage.setItem(GUEST_STORAGE_KEY, themeId)
}

function applyTheme(theme: Theme): void {
  if (typeof window === 'undefined') return

  requestAnimationFrame(() => {
    const root = document.documentElement
    root.classList.add('theme-changing')
    root.style.colorScheme = theme.appearance
    root.dataset.theme = theme.id
    root.dataset.themeMode = theme.layoutMode

    Object.entries(theme.cssVars).forEach(([key, value]) => {
      root.style.setProperty(key, value)
    })

    const body = document.body
    const oldClasses = body.className
      .split(' ')
      .filter(cls => !cls.startsWith('theme-'))
    body.className = [...oldClasses, `theme-${theme.layoutMode}`, `theme-id-${theme.id}`]
      .join(' ')
      .trim()

    requestAnimationFrame(() => {
      root.classList.remove('theme-changing')
    })
  })
}

function startThemeWatcher(): void {
  if (themeWatcherStarted) return
  themeWatcherStarted = true

  watch(
    currentTheme,
    (theme) => {
      applyTheme(theme)
    },
    { immediate: true }
  )
}

function syncThemeForUser(user: Pick<AuthUser, 'id' | 'preferred_theme'> | null): void {
  if (!user) {
    activeUserId.value = null
    const guestTheme = typeof window === 'undefined' ? null : localStorage.getItem(GUEST_STORAGE_KEY)
    currentThemeId.value = isThemeId(guestTheme) ? guestTheme : defaultTheme.id
    return
  }

  activeUserId.value = user.id
  const preferredTheme = isThemeId(user.preferred_theme) ? user.preferred_theme : null
  const localTheme = localThemeForUser(user.id)
  const nextThemeId = preferredTheme || localTheme || defaultTheme.id
  currentThemeId.value = nextThemeId
  writeLocalTheme(nextThemeId, user.id)
}

async function persistThemeForCurrentUser(themeId: string): Promise<boolean> {
  if (!activeUserId.value) return true

  savingTheme.value = true
  themeSaveError.value = ''

  try {
    const updatedUser = await updateUserProfile(activeUserId.value, { preferred_theme: themeId })
    writeLocalTheme(updatedUser.preferred_theme || themeId, activeUserId.value)
    syncCachedUserTheme(updatedUser.preferred_theme || themeId)
    return true
  } catch {
    themeSaveError.value = '主题仅本次在本机生效，未同步到账号；下次登录可能恢复为账号设置'
    return false
  } finally {
    savingTheme.value = false
  }
}

function syncCachedUserTheme(themeId: string): void {
  if (typeof window === 'undefined') return

  const rawUser = localStorage.getItem('user')
  if (!rawUser) return

  try {
    const cachedUser = JSON.parse(rawUser)
    if (cachedUser?.id === activeUserId.value) {
      localStorage.setItem('user', JSON.stringify({ ...cachedUser, preferred_theme: themeId }))
    }
  } catch {
    // Ignore invalid cache. Auth refresh will repair it.
  }
}

async function switchTheme(themeId: string): Promise<boolean> {
  if (!isThemeId(themeId)) {
    console.warn(`主题 "${themeId}" 不存在，切换失败`)
    return false
  }

  currentThemeId.value = themeId
  writeLocalTheme(themeId)
  syncCachedUserTheme(themeId)
  return persistThemeForCurrentUser(themeId)
}

export function useTheme() {
  startThemeWatcher()

  return {
    themes,
    currentTheme,
    currentThemeId,
    savingTheme,
    themeSaveError,
    applyTheme,
    switchTheme,
    syncThemeForUser,
  }
}
