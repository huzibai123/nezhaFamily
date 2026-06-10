<template>
  <div class="min-h-dvh px-4 py-8 sm:px-6 lg:grid lg:grid-cols-[minmax(0,1fr)_28rem] lg:gap-10 lg:px-10" style="background:var(--surface)">
    <section class="mx-auto flex max-w-5xl flex-col justify-center py-10 lg:min-h-[calc(100dvh-4rem)]">
      <div class="max-w-2xl space-y-8">
        <div class="space-y-3 enter">
          <p class="text-xs font-medium uppercase tracking-[0.18em]" style="color:var(--text-muted)">Invitation only</p>
          <div class="flex items-center gap-4">
            <FamilySeal :label="familyName" :logo-url="logoUrl" />
            <h1 class="text-4xl font-semibold tracking-normal sm:text-5xl">加入家庭</h1>
          </div>
          <p class="max-w-xl text-sm leading-7 sm:text-base" style="color:var(--text-secondary)">
            {{ familyName }}只为一个家庭服务。拿到邀请码后，创建自己的账号，就可以一起发布照片、评论和整理家庭日历。
          </p>
        </div>

        <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-5">
          <p class="text-sm font-semibold text-[var(--text)]">注册后你可以做什么</p>
          <div class="mt-4 grid gap-3 sm:grid-cols-3">
            <div v-for="item in registerNotes" :key="item.title">
              <p class="text-sm text-[var(--text)]">{{ item.title }}</p>
              <p class="mt-1 text-xs leading-5 text-[var(--text-muted)]">{{ item.body }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto flex w-full max-w-[28rem] flex-col justify-center py-8 lg:min-h-[calc(100dvh-4rem)]">
      <form @submit.prevent="handleRegister" class="space-y-3.5 enter" style="animation-delay:0.08s">
        <div class="mb-6 space-y-2">
          <h2 class="text-2xl font-semibold text-[var(--text)]">创建账号</h2>
          <p class="text-sm text-[var(--text-muted)]">需要家人给你的邀请码。</p>
        </div>
        <input
          v-for="f in fields"
          :key="f.key"
          v-model="form[f.key]"
          :type="f.type"
          :placeholder="f.placeholder"
          required
          class="w-full px-4 py-3.5 text-sm rounded-xl border outline-none transition-colors"
          style="background:var(--surface-card);border-color:var(--border);color:var(--text)"
          @blur="f.key === 'inviteCode' && checkInvite()"
        />

        <p
          v-if="inviteMessage"
          class="rounded-lg border px-3 py-2 text-xs leading-5"
          :class="inviteValid ? 'invite-ok' : 'invite-warn'"
        >
          {{ checkingInvite ? '正在校验邀请码...' : inviteMessage }}
        </p>

        <p v-if="errorMessage" class="text-xs" style="color:var(--accent)">{{ errorMessage }}</p>

        <button type="submit" :disabled="loading"
          class="w-full py-3.5 text-sm font-semibold rounded-xl transition-all active:scale-[0.98] disabled:opacity-30"
          style="background:var(--text);color:var(--surface)">注册</button>

        <p class="text-center text-xs" style="color:var(--text-muted)">
          已有账号？<router-link to="/login" class="underline underline-offset-4 hover:opacity-80" style="color:var(--text-secondary)">立即登录</router-link>
        </p>
      </form>
    </section>
  </div>
</template>
<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { lookupInvite } from '@/api/auth'
import { useAuth } from '@/composables/useAuth'
import { useFamilySettings } from '@/composables/useFamilySettings'
import FamilySeal from '@/components/FamilySeal.vue'

const router = useRouter()
const route = useRoute()
const { register } = useAuth()
const { familyName, logoUrl, loadFamilySettings } = useFamilySettings()
loadFamilySettings()
const fields = [
  { key:'inviteCode', type:'text', placeholder:'邀请码' },
  { key:'username', type:'text', placeholder:'用户名' },
  { key:'email', type:'email', placeholder:'邮箱' },
  { key:'password', type:'password', placeholder:'密码（至少8位）' },
  { key:'confirmPassword', type:'password', placeholder:'确认密码' },
]
const form = reactive<Record<string,string>>({inviteCode:'',username:'',email:'',password:'',confirmPassword:''})
const loading = ref(false)
const checkingInvite = ref(false)
const inviteValid = ref(false)
const inviteMessage = ref('')
const errorMessage = ref('')
const registerNotes = [
  { title: '发布动态', body: '上传照片、视频或文字。' },
  { title: '参与互动', body: '评论、回复和点赞。' },
  { title: '整理记忆', body: '查看相册与家庭日历。' },
]

onMounted(() => {
  const inviteFromQuery = route.query.invite
  if (typeof inviteFromQuery === 'string' && inviteFromQuery.trim()) {
    form.inviteCode = inviteFromQuery.trim()
    checkInvite()
  }
})

async function checkInvite() {
  if (!form.inviteCode.trim()) {
    inviteValid.value = false
    inviteMessage.value = ''
    return
  }

  checkingInvite.value = true
  try {
    const result = await lookupInvite(form.inviteCode.trim())
    inviteValid.value = result.valid
    inviteMessage.value = result.valid
      ? `来自 ${result.inviter_username || '家人'} 的邀请${result.inviter_role_in_family ? ` · ${result.inviter_role_in_family}` : ''}`
      : result.message || '邀请码无效'
  } catch (error) {
    inviteValid.value = false
    inviteMessage.value = typeof error === 'string' ? error : '邀请码暂时无法校验'
  } finally {
    checkingInvite.value = false
  }
}

async function handleRegister() {
  if (form.password !== form.confirmPassword) {
    errorMessage.value = '两次密码不一致'
    return
  }

  loading.value = true
  errorMessage.value = ''
  const r = await register(form.username, form.email, form.password, form.inviteCode)
  loading.value = false
  r.success ? router.push('/') : errorMessage.value = r.message || '注册失败'
}
</script>

<style scoped>
.invite-ok {
  background: rgba(83, 127, 73, 0.08);
  border-color: rgba(83, 127, 73, 0.2);
  color: #496f3f;
}

.invite-warn {
  background: var(--accent-soft);
  border-color: rgba(201, 67, 47, 0.18);
  color: var(--accent);
}
</style>
