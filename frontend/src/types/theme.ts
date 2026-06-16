export interface Theme {
  id: string
  name: string
  description: string
  layoutMode: 'default' | 'single-dark' | 'timeline' | 'grid' | 'masonry' | 'minimal'
  appearance: 'light' | 'dark'
  allowFamilyColorOverride?: boolean
  cssVars: Record<string, string>
}
