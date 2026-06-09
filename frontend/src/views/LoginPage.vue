<template>
  <div class="min-h-dvh px-4 py-8 sm:px-6 lg:grid lg:grid-cols-[minmax(0,1fr)_28rem] lg:gap-10 lg:px-10" style="background:var(--surface)">
    <section class="mx-auto flex max-w-5xl flex-col justify-center py-10 lg:min-h-[calc(100dvh-4rem)]">
      <div class="max-w-2xl space-y-8">
        <div class="space-y-3 enter">
          <p class="text-xs font-medium uppercase tracking-[0.18em]" style="color:var(--text-muted)">Private family hub</p>
          <div class="flex items-center gap-4">
            <FamilySeal :label="familyName" />
            <h1 class="text-4xl font-semibold tracking-normal sm:text-5xl" style="color:var(--text)">{{ familyName }}</h1>
          </div>
          <p class="max-w-xl text-sm leading-7 sm:text-base" style="color:var(--text-secondary)">
            {{ tagline }}。照片、视频、评论和日期记忆部署在自己的服务器里，家里的故事由家人自己保管。
          </p>
        </div>

        <div class="grid gap-3 sm:grid-cols-3">
          <div v-for="item in trustItems" :key="item.title" class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
            <p class="text-sm font-semibold text-[var(--text)]">{{ item.title }}</p>
            <p class="mt-2 text-xs leading-5 text-[var(--text-muted)]">{{ item.body }}</p>
          </div>
        </div>

        <div class="hidden grid-cols-3 gap-3 lg:grid">
          <div class="h-36 rounded-lg border border-[var(--border)] bg-[var(--surface-card)]" />
          <div class="mt-8 h-36 rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)]" />
          <div class="h-36 rounded-lg border border-[var(--border)] bg-[var(--surface-card)]" />
        </div>
      </div>
    </section>

    <section class="mx-auto flex w-full max-w-[28rem] flex-col justify-center py-8 lg:min-h-[calc(100dvh-4rem)]">
      <form @submit.prevent="handleLogin" class="space-y-4 enter" style="animation-delay:0.08s">
        <div class="mb-8 space-y-2">
          <h2 class="text-2xl font-semibold text-[var(--text)]">欢迎回家</h2>
          <p class="text-sm text-[var(--text-muted)]">使用家庭成员账号登录。</p>
        </div>
        <input v-model="form.username" type="text" placeholder="用户名" required
          class="w-full px-4 py-3.5 text-sm rounded-xl border border-[color:var(--border)] outline-none transition-colors focus:border-[color:var(--border-focus)]"
          style="background:var(--surface-card);color:var(--text)" />
        <input v-model="form.password" type="password" placeholder="密码" required
          class="w-full px-4 py-3.5 text-sm rounded-xl border border-[color:var(--border)] outline-none transition-colors focus:border-[color:var(--border-focus)]"
          style="background:var(--surface-card);color:var(--text)" />

        <p v-if="errorMessage" class="text-xs" style="color:var(--accent)">{{ errorMessage }}</p>

        <button type="submit" :disabled="loading"
          class="w-full py-3.5 text-sm font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-30"
          style="background:var(--text);color:var(--surface)">
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <p class="text-center text-xs" style="color:var(--text-muted)">
          还没有账号？<router-link to="/register" class="underline underline-offset-4 hover:opacity-80 transition-opacity" style="color:var(--text-secondary)">立即注册</router-link>
        </p>
      </form>
    </section>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useFamilySettings } from '@/composables/useFamilySettings'
import FamilySeal from '@/components/FamilySeal.vue'

const router = useRouter(); const route = useRoute(); const { login } = useAuth()
const { familyName, tagline, loadFamilySettings } = useFamilySettings()
loadFamilySettings()
const form = reactive({ username: '', password: '' })
const loading = ref(false); const errorMessage = ref('')
const trustItems = [
  { title: '私有部署', body: '照片和视频保存在自己的环境里。' },
  { title: '邀请码加入', body: '只让家庭成员进入这个空间。' },
  { title: '记忆聚合', body: '动态、相册和日历放在一起。' },
]

async function handleLogin() {
  loading.value = true; errorMessage.value = ''
  const r = await login(form.username, form.password)
  loading.value = false
  r.success ? router.push((route.query.redirect as string) || '/') : errorMessage.value = r.message || '登录失败'
}
</script>
