import { expect, request as playwrightRequest, test } from '@playwright/test'
import type { APIRequestContext, Page } from '@playwright/test'

const apiURL = process.env.E2E_API_URL || 'http://localhost:8000'
const adminUsername = process.env.E2E_ADMIN_USERNAME
const adminPassword = process.env.E2E_ADMIN_PASSWORD
const hasAdminCredentials = Boolean(adminUsername && adminPassword)
const createdPostIds: string[] = []

async function login(page: Page) {
  await page.goto('/login')
  await page.getByPlaceholder('用户名').fill(adminUsername || '')
  await page.getByPlaceholder('密码').fill(adminPassword || '')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL('/')
  await expect(page.getByRole('heading', { name: '家庭今日' })).toBeVisible()
}

async function fetchToken(requestContext: APIRequestContext): Promise<string | null> {
  if (!hasAdminCredentials) return null
  const response = await requestContext.post(`${apiURL}/api/v1/login`, {
    data: {
      username: adminUsername,
      password: adminPassword,
    },
  })
  if (!response.ok()) return null
  const payload = await response.json()
  return typeof payload.access_token === 'string' ? payload.access_token : null
}

async function cleanupCreatedPosts() {
  if (!createdPostIds.length) return
  const requestContext = await playwrightRequest.newContext()
  try {
    const token = await fetchToken(requestContext)
    if (!token) {
      console.warn(`E2E cleanup skipped: missing API token for posts ${createdPostIds.join(', ')}`)
      return
    }
    for (const postId of createdPostIds.splice(0)) {
      const response = await requestContext.delete(`${apiURL}/api/v1/posts/${postId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok() && response.status() !== 404) {
        console.warn(`E2E cleanup failed for post ${postId}: HTTP ${response.status()}`)
      }
    }
  } finally {
    await requestContext.dispose()
  }
}

test.afterAll(async () => {
  await cleanupCreatedPosts()
})

test('public login page renders', async ({ page }) => {
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: '欢迎回家' })).toBeVisible()
  await expect(page.getByPlaceholder('用户名')).toBeVisible()
  await expect(page.getByPlaceholder('密码')).toBeVisible()
})

test.describe('authenticated release smoke', () => {
  test.skip(
    !hasAdminCredentials,
    'Set E2E_ADMIN_USERNAME and E2E_ADMIN_PASSWORD to run login and write-flow E2E tests.'
  )

  test('covers login, publish, detail, comment, like, notifications, profile and admin AI', async ({ page }) => {
    const marker = `E2E-NEZHA-${Date.now()}`
    const postContent = `${marker} 开源发布回归测试`
    const commentContent = `${marker} 评论回归测试`

    await login(page)

    await page.goto('/publish')
    await expect(page.getByRole('heading', { name: '发布记忆' })).toBeVisible()
    await page.getByTestId('publish-content').fill(postContent)
    await page.getByTestId('publish-submit').click()
    await expect(page).toHaveURL('/')

    const postCard = page.locator('article').filter({ hasText: marker }).first()
    await expect(postCard).toBeVisible()
    await postCard.getByText('查看详情').click()
    await expect(page).toHaveURL(/\/post\/[0-9a-f-]+$/i)

    const postId = page.url().split('/post/')[1]?.split(/[?#]/)[0]
    if (!postId) {
      throw new Error('Could not extract created post id from detail URL')
    }
    createdPostIds.push(postId)

    await expect(page.getByText(postContent)).toBeVisible()
    await page.getByTestId('post-like').click()
    await page.getByTestId('comment-input').fill(commentContent)
    await page.getByTestId('comment-submit').click()
    await expect(page.getByText(commentContent)).toBeVisible()

    await page.goto('/notifications')
    await expect(page.getByRole('heading', { name: '通知中心' })).toBeVisible()

    const user = await page.evaluate(() => JSON.parse(localStorage.getItem('user') || '{}'))
    expect(user.id).toBeTruthy()
    await page.goto(`/profile/${user.id}`)
    await expect(page.getByTestId('profile-edit')).toBeVisible()
    await page.getByTestId('profile-edit').click()
    await expect(page.getByRole('button', { name: '保存资料' })).toBeVisible()
    await page.getByRole('button', { name: '取消' }).click()

    await page.goto('/albums')
    await expect(page.getByRole('heading', { name: '家庭相册' })).toBeVisible()

    await page.goto('/library')
    await expect(page.getByRole('heading', { name: '媒体库' })).toBeVisible()

    await page.goto('/admin/ai')
    await expect(page.getByRole('heading', { name: 'AI 家庭管家' })).toBeVisible()
  })
})
