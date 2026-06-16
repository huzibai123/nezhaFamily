import type { Theme } from '@/types/theme'
import { defaultTheme } from './default'
import { classicTheme } from './classic'
import { timelineTheme } from './timeline'
import { gridTheme } from './grid'
import { listTheme } from './list'
import { warmTheme } from './warm'

/**
 * 所有可用主题列表
 */
export const THEMES: Theme[] = [
  defaultTheme,
  classicTheme,
  timelineTheme,
  gridTheme,
  listTheme,
  warmTheme
]

/**
 * 按 ID 查找主题
 */
export function getThemeById(id: string): Theme | undefined {
  return THEMES.find(theme => theme.id === id)
}

export {
  defaultTheme,
  classicTheme,
  timelineTheme,
  gridTheme,
  listTheme,
  warmTheme
}
