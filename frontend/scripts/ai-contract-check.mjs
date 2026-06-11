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
  providerPage,
  "aiStatus?.provider?.api_key_source !== 'database'",
  'Clear key button only enabled for database key'
)
assertIncludes(providerPage, '清除后台 Key', 'Clear key button copy')

console.log('AI frontend contract check passed')
