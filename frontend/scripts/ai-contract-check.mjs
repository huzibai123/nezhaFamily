import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')

function read(relativePath) {
  return readFileSync(resolve(root, relativePath), 'utf8')
}

function assertIncludes(source, expected, label) {
  if (!source.includes(expected)) {
    throw new Error(`${label}: missing ${JSON.stringify(expected)}`)
  }
}

function assertMatches(source, pattern, label) {
  if (!pattern.test(source)) {
    throw new Error(`${label}: pattern not found`)
  }
}

const router = read('src/router/index.ts')
const useAdminAI = read('src/views/admin-ai/useAdminAI.ts')
const providerPage = read('src/views/admin-ai/AdminAIProvider.vue')
const aiApi = read('src/api/ai.ts')
const publishPage = read('src/views/PublishPage.vue')

assertIncludes(router, "path: '/admin/ai'", 'AI parent route')
assertIncludes(router, "name: 'AdminAI'", 'AI parent route')
assertMatches(
  router,
  /path:\s*''[\s\S]*name:\s*'AdminAIOverview'[\s\S]*requiresAuth:\s*true,\s*requiresAdmin:\s*true/,
  'AI overview route requires admin'
)

for (const [path, name] of [
  ['provider', 'AdminAIProvider'],
  ['personas', 'AdminAIPersonas'],
  ['jobs', 'AdminAIJobs'],
  ['reports', 'AdminAIReports'],
  ['suggestions', 'AdminAISuggestions'],
  ['profiles', 'AdminAIProfiles'],
]) {
  assertMatches(
    router,
    new RegExp(
      `path:\\s*'${path}'[\\s\\S]*name:\\s*'${name}'[\\s\\S]*requiresAuth:\\s*true,\\s*requiresAdmin:\\s*true`
    ),
    `AI child route ${path}`
  )
}

assertIncludes(router, "path: 'overview'", 'AI overview compatibility route')
assertIncludes(router, "redirect: { name: 'AdminAIOverview' }", 'AI overview compatibility redirect')

assertMatches(
  useAdminAI,
  /const apiKey = providerDraft\.api_key\.trim\(\)[\s\S]*if \(apiKey\) \{[\s\S]*payload\.api_key = apiKey[\s\S]*\}/,
  'Provider payload only sends non-empty api_key'
)
assertMatches(
  useAdminAI,
  /if \(providerDraft\.clear_api_key\) \{[\s\S]*payload\.clear_api_key = true[\s\S]*\}/,
  'Provider payload sends explicit clear_api_key'
)
assertIncludes(
  useAdminAI,
  "wire_api: providerDraft.wire_api || 'chat_completions'",
  'Provider payload sends wire_api'
)
assertIncludes(
  useAdminAI,
  'disable_response_storage: Boolean(providerDraft.disable_response_storage)',
  'Provider payload sends response storage setting'
)

assertIncludes(
  providerPage,
  "aiStatus?.provider?.api_key_source !== 'database'",
  'Clear key button only enabled for database key'
)
assertIncludes(providerPage, '清除后台 Key', 'Clear key button copy')
assertIncludes(providerPage, 'value="responses"', 'Provider page exposes Responses wire API option')
assertIncludes(providerPage, '关闭响应存储', 'Provider page exposes Responses storage toggle')

assertIncludes(aiApi, "api.post('/ai/post-caption'", 'Post caption API endpoint')
assertIncludes(aiApi, "formData.append('mode', payload.mode)", 'Post caption sends mode')
assertIncludes(aiApi, "formData.append('content', trimmed)", 'Post caption sends trimmed content only')
assertMatches(
  aiApi,
  /payload\.files\?\.forEach\(\(file\)\s*=>\s*formData\.append\('files\[\]',\s*file\)\)/,
  'Post caption sends selected files as files[]'
)
assertIncludes(publishPage, 'generatePostCaption', 'Publish page calls post caption API')
assertMatches(
  publishPage,
  /generatePostCaption\(\{[\s\S]*mode,[\s\S]*content:\s*trimmed\s*\|\|\s*undefined,[\s\S]*files:\s*mediaFiles\.value,[\s\S]*\}\)/,
  'Publish page sends content and files to post caption API'
)
assertIncludes(publishPage, "'润色文案'", 'Publish page exposes polish label')
assertIncludes(publishPage, "'帮我写文案'", 'Publish page exposes generate label')
assertIncludes(publishPage, ':disabled="!canUseCaptionAI || isBusy"', 'Publish AI button is disabled while unavailable or busy')
assertIncludes(
  publishPage,
  'await createPost(content.value.trim(), uploadedUrls.value)',
  'Publish flow still uses normal createPost contract'
)

console.log('AI frontend contract check passed')
