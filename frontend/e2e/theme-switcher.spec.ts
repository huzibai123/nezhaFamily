import { expect, test, type Page } from '@playwright/test'

const testUser = {
  id: 'theme-test-user',
  username: 'ThemeTester',
  email: 'theme@example.test',
  role: 'admin',
  avatar_url: null,
  bio: null,
  birthday: null,
  role_in_family: null,
  created_at: '2026-06-13T00:00:00.000Z',
  updated_at: '2026-06-13T00:00:00.000Z',
}

const allThemeIds = ['default', 'classic', 'timeline', 'grid', 'list', 'warm']

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/me', route => route.fulfill({ json: testUser }))
  await page.route('**/api/v1/admin/family-settings', route => route.fulfill({
    json: {
      family_name: '哪吒家庭',
      tagline: '私有的家庭记忆中枢',
      theme_color: '#f6f1e8',
      accent_color: '#c9432f',
      background_image_url: '',
      logo_url: '',
      theme_assets: {
        backgrounds: [],
        cursor: null,
        ornaments: [],
      },
    },
  }))
  await page.route('**/api/v1/posts**', route => route.fulfill({
    json: {
      posts: [],
      total: 0,
      page: 1,
      page_size: 8,
      has_more: false,
    },
  }))
  await page.route('**/api/v1/notifications**', route => route.fulfill({
    json: {
      notifications: [],
      unread_count: 0,
      total: 0,
      page: 1,
      page_size: 8,
      has_more: false,
    },
  }))
  await page.route('**/api/v1/albums**', route => route.fulfill({ json: { albums: [] } }))
})

async function openTimelineWithTheme(page: Page, themeId: string) {
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.addInitScript(({ user, themeId }) => {
    window.localStorage.setItem('token', 'theme-switcher-test-token')
    window.localStorage.setItem('user', JSON.stringify(user))
    window.localStorage.setItem('nezha-theme', themeId)
  }, { user: testUser, themeId })
  await page.goto('/')
}

test('theme switcher opens as a centered full-screen dialog', async ({ page }) => {
  await openTimelineWithTheme(page, 'default')
  await expect(page.getByRole('button', { name: '切换主题' })).toBeVisible()
  await page.getByRole('button', { name: '切换主题' }).click()

  const overlay = page.locator('.theme-switcher-overlay')
  const modal = page.locator('.theme-switcher-modal')
  const grid = page.locator('.themes-grid')

  await expect(overlay).toBeVisible()
  await expect(modal).toBeVisible()
  await expect(page.getByRole('heading', { name: '选择主题' })).toBeVisible()

  const metrics = await page.evaluate(() => {
    const overlay = document.querySelector('.theme-switcher-overlay')
    const modal = document.querySelector('.theme-switcher-modal')
    const grid = document.querySelector('.themes-grid')

    if (!(overlay instanceof HTMLElement) || !(modal instanceof HTMLElement) || !(grid instanceof HTMLElement)) {
      throw new Error('Theme switcher elements were not rendered')
    }

    const overlayRect = overlay.getBoundingClientRect()
    const modalRect = modal.getBoundingClientRect()
    const overlayStyle = getComputedStyle(overlay)
    const gridStyle = getComputedStyle(grid)

    return {
      overlayParent: overlay.parentElement?.tagName,
      overlayPosition: overlayStyle.position,
      overlayDisplay: overlayStyle.display,
      overlayJustifyContent: overlayStyle.justifyContent,
      overlayAlignItems: overlayStyle.alignItems,
      overlayRect: {
        left: overlayRect.left,
        top: overlayRect.top,
        width: overlayRect.width,
        height: overlayRect.height,
      },
      modalRect: {
        left: modalRect.left,
        width: modalRect.width,
        center: modalRect.left + modalRect.width / 2,
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight,
      },
      gridColumns: gridStyle.gridTemplateColumns.split(' ').length,
    }
  })

  expect(metrics.overlayParent).toBe('BODY')
  expect(metrics.overlayPosition).toBe('fixed')
  expect(metrics.overlayDisplay).toBe('flex')
  expect(metrics.overlayJustifyContent).toBe('center')
  expect(metrics.overlayAlignItems).toBe('center')
  expect(metrics.overlayRect.left).toBeCloseTo(0, 0)
  expect(metrics.overlayRect.top).toBeCloseTo(0, 0)
  expect(metrics.overlayRect.width).toBeCloseTo(metrics.viewport.width, 0)
  expect(metrics.overlayRect.height).toBeCloseTo(metrics.viewport.height, 0)
  expect(metrics.modalRect.center).toBeCloseTo(metrics.viewport.width / 2, 0)
  expect(metrics.modalRect.width).toBeGreaterThan(900)
  expect(metrics.gridColumns).toBe(3)
})

for (const themeId of ['classic', 'warm']) {
  test(`timeline keeps a usable content width for ${themeId} theme`, async ({ page }) => {
    await openTimelineWithTheme(page, themeId)
    await expect(page.getByRole('heading', { name: '家庭今日' })).toBeVisible()

    const metrics = await page.evaluate(() => {
      const shell = document.querySelector('.family-shell > .grid')
      const main = document.querySelector('.shell-main')
      const content = document.querySelector('.desktop-archive')

      if (!(shell instanceof HTMLElement) || !(main instanceof HTMLElement) || !(content instanceof HTMLElement)) {
        throw new Error('Timeline layout elements were not rendered')
      }

      const shellStyle = getComputedStyle(shell)
      const mainRect = main.getBoundingClientRect()
      const contentRect = content.getBoundingClientRect()

      return {
        gridTemplateColumns: shellStyle.gridTemplateColumns,
        mainWidth: mainRect.width,
        contentWidth: contentRect.width,
        viewportWidth: window.innerWidth,
      }
    })

    expect(metrics.gridTemplateColumns.split(' ').length).toBe(2)
    expect(metrics.mainWidth).toBeGreaterThan(metrics.viewportWidth * 0.8)
    expect(metrics.contentWidth).toBeGreaterThan(700)
  })
}

for (const themeId of allThemeIds) {
  test(`theme ${themeId} keeps core navigation and readable text`, async ({ page }) => {
    await openTimelineWithTheme(page, themeId)

    await expect(page.getByRole('link', { name: '发布记忆' })).toBeVisible()
    await expect(page.getByRole('button', { name: '切换主题' })).toBeVisible()
    await expect(page.getByText('搜索家庭照片、视频、上传者或文件名')).toBeVisible()
    await expect(page.getByRole('heading', { name: '家庭今日' })).toBeVisible()
    await expect(page.locator('[data-testid="app-right-rail"]')).toBeVisible()

    const contrastMetrics = await page.evaluate(() => {
      function parseColor(value: string) {
        const match = value.match(/rgba?\(([^)]+)\)/)
        if (!match) return null
        const parts = match[1].split(',').map(part => Number.parseFloat(part.trim()))
        return {
          r: parts[0],
          g: parts[1],
          b: parts[2],
          a: parts[3] ?? 1,
        }
      }

      function luminance(channel: number) {
        const value = channel / 255
        return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
      }

      function contrast(foreground: string, background: string) {
        const fg = parseColor(foreground)
        const bg = parseColor(background)
        if (!fg || !bg) return 21
        const blended = {
          r: fg.r * fg.a + bg.r * (1 - fg.a),
          g: fg.g * fg.a + bg.g * (1 - fg.a),
          b: fg.b * fg.a + bg.b * (1 - fg.a),
        }
        const fgLum = 0.2126 * luminance(blended.r) + 0.7152 * luminance(blended.g) + 0.0722 * luminance(blended.b)
        const bgLum = 0.2126 * luminance(bg.r) + 0.7152 * luminance(bg.g) + 0.0722 * luminance(bg.b)
        const lighter = Math.max(fgLum, bgLum)
        const darker = Math.min(fgLum, bgLum)
        return (lighter + 0.05) / (darker + 0.05)
      }

      const samples = [
        { label: 'archive-title', element: document.querySelector('.desktop-archive h2') },
        { label: 'archive-copy', element: document.querySelector('.desktop-archive p') },
        { label: 'stat-label', element: document.querySelector('.desktop-stat p') },
        { label: 'filter-input', element: document.querySelector('.filter-input') },
        { label: 'right-rail-title', element: document.querySelector('[data-testid="app-right-rail"] h2') },
      ].filter((sample): sample is { label: string; element: HTMLElement } => sample.element instanceof HTMLElement)

      return samples.map(({ label, element }) => {
        const style = getComputedStyle(element)
        let backgroundElement: HTMLElement | null = element
        let background = 'rgba(255, 255, 255, 1)'
        while (backgroundElement) {
          const candidate = getComputedStyle(backgroundElement).backgroundColor
          const parsed = parseColor(candidate)
          if (parsed && parsed.a > 0) {
            background = candidate
            break
          }
          backgroundElement = backgroundElement.parentElement
        }
        return {
          label,
          color: style.color,
          background,
          ratio: contrast(style.color, background),
        }
      })
    })

    for (const metric of contrastMetrics) {
      expect(metric.ratio, `${themeId}:${metric.label} ${metric.color} on ${metric.background}`).toBeGreaterThanOrEqual(4.5)
    }
  })
}
