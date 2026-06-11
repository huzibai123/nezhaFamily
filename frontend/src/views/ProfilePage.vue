<template>
  <AppShell :page-title="profile?.username || '成员主页'" page-description="家庭成员资料、统计和发布过的记忆">
    <template #header>
      <button
        @click="$router.back()"
        class="soft-button mb-4 inline-flex rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
        type="button"
      >
        返回
      </button>
    </template>

    <div v-if="profile" class="space-y-6">
      <p
        v-if="errorMessage"
        class="rounded-lg border border-[color:rgb(227_107_93_/_0.24)] bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--accent)]"
      >
        {{ errorMessage }}
      </p>

      <section class="profile-card rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)]">
        <div class="grid gap-5 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center">
          <div class="grid h-20 w-20 place-items-center overflow-hidden rounded-xl bg-[var(--accent-soft)] text-3xl font-semibold text-[var(--accent)]">
            <img
              v-if="profileAvatarUrl"
              :src="profileAvatarUrl"
              :alt="`${profile.username} 的头像`"
              class="h-full w-full object-cover"
            />
            <span v-else>{{ profileInitial }}</span>
          </div>
          <div class="min-w-0">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">家庭成员</p>
            <h1 class="mt-2 truncate text-2xl font-semibold tracking-normal text-[var(--text)]">
              {{ profile.username }}
            </h1>
            <p class="mt-1 text-sm text-[var(--text-secondary)]">
              {{ profile.role_in_family || '还没有设置家庭角色' }}
            </p>
          </div>
          <button
            v-if="isOwn"
            @click="openEditModal"
            class="soft-button inline-flex rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
            type="button"
          >
            编辑资料
          </button>
        </div>

        <p v-if="profile.bio" class="mt-5 text-sm leading-7 text-[var(--text-secondary)]">{{ profile.bio }}</p>
        <p v-else class="mt-5 text-sm text-[var(--text-muted)]">还没有写个人简介。</p>
      </section>

      <section class="grid gap-3 sm:grid-cols-3">
        <div class="stat-card rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
          <p class="text-2xl font-semibold text-[var(--text)]">{{ stats.post_count }}</p>
          <p class="mt-1 text-xs text-[var(--text-muted)]">发布记忆</p>
        </div>
        <div class="stat-card rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
          <p class="text-2xl font-semibold text-[var(--text)]">{{ stats.like_count }}</p>
          <p class="mt-1 text-xs text-[var(--text-muted)]">收到点赞</p>
        </div>
        <div class="stat-card rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
          <p class="text-2xl font-semibold text-[var(--text)]">{{ stats.comment_count }}</p>
          <p class="mt-1 text-xs text-[var(--text-muted)]">参与评论</p>
        </div>
      </section>

      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <h2 class="text-base font-semibold text-[var(--text)]">发布的记忆</h2>
          <span class="text-xs text-[var(--text-muted)]">{{ posts.length }} 条</span>
        </div>
        <PostCard
          v-for="postItem in posts"
          :key="postItem.id"
          :post="postItem"
          @click="$router.push(`/post/${postItem.id}`)"
          @like="handleLike"
        />
        <div
          v-if="!posts.length"
          class="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--text-muted)]"
        >
          还没有发布帖子。
        </div>
      </section>
    </div>

    <div v-else class="rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-8 text-center text-sm text-[var(--text-muted)]">
      {{ loading ? '加载中...' : errorMessage || '成员资料加载失败' }}
    </div>

    <template #right>
      <div class="space-y-4">
        <RightRail
          title="成员信息"
          :sections="profileSections"
        />
        <RightRail
          title="快捷入口"
          :sections="quickSections"
        />
      </div>
    </template>

    <div
      v-if="showEdit"
      @click.self="closeEditModal"
      class="fixed inset-0 z-50 overflow-y-auto px-4 py-6 sm:py-10"
      style="background:rgba(75,40,25,0.38);backdrop-filter:blur(6px)"
    >
      <div class="flex min-h-full items-start justify-center">
        <div @click.stop class="modal-panel flex max-h-[calc(100dvh-3rem)] w-full max-w-lg flex-col overflow-hidden rounded-lg border border-[var(--border)] bg-[var(--surface-card)] shadow-[var(--shadow-panel)]">
          <div class="flex items-center justify-between border-b border-[var(--border)] px-5 py-4 sm:px-6">
            <h2 class="text-lg font-semibold text-[var(--text)]">编辑个人资料</h2>
            <button
              @click="closeEditModal"
              :disabled="saving || avatarUploading"
              class="soft-button grid h-9 w-9 place-items-center rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-40"
              type="button"
              aria-label="关闭"
            >
              <X :size="17" stroke-width="2" aria-hidden="true" />
            </button>
          </div>

          <div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4 sm:px-6">
            <div class="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
              <div class="flex items-center gap-4">
                <div class="grid h-16 w-16 shrink-0 place-items-center overflow-hidden rounded-xl bg-[var(--accent-soft)] text-2xl font-semibold text-[var(--accent)]">
                  <img
                    v-if="editAvatarPreview"
                    :src="editAvatarPreview"
                    alt="头像预览"
                    class="h-full w-full object-cover"
                  />
                  <span v-else>{{ profileInitial }}</span>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-medium text-[var(--text)]">头像</p>
                  <p class="mt-1 text-xs text-[var(--text-muted)]">支持 JPG、PNG、WebP、GIF 图片。</p>
                  <div class="mt-3 flex flex-wrap gap-2">
                    <button
                      @click="avatarInput?.click()"
                      :disabled="saving || avatarUploading"
                      class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] disabled:opacity-40"
                      type="button"
                    >
                      <Camera :size="15" stroke-width="2" aria-hidden="true" />
                      {{ avatarUploading ? '上传中' : '更换头像' }}
                    </button>
                    <button
                      v-if="editForm.avatar_url"
                      @click="removeAvatar"
                      :disabled="saving || avatarUploading"
                      class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] disabled:opacity-40"
                      type="button"
                    >
                      <Trash2 :size="15" stroke-width="2" aria-hidden="true" />
                      移除
                    </button>
                  </div>
                </div>
                <input
                  ref="avatarInput"
                  class="hidden"
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  @change="handleAvatarUpload"
                />
              </div>
            </div>

            <div>
              <label class="mb-1 block text-xs text-[var(--text-muted)]">个人简介</label>
              <textarea
                v-model="editForm.bio"
                placeholder="介绍一下自己..."
                rows="4"
                class="profile-input w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)] outline-none"
              />
            </div>
            <div>
              <label class="mb-1 block text-xs text-[var(--text-muted)]">家庭角色</label>
              <input
                v-model="editForm.role_in_family"
                placeholder="如：爸爸、妈妈、宝宝..."
                class="profile-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)] outline-none"
              />
            </div>
            <div>
              <label class="mb-1 block text-xs text-[var(--text-muted)]">生日</label>
              <input
                v-model="editForm.birthday"
                type="date"
                class="profile-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)] outline-none"
              />
            </div>
          </div>

          <div class="flex flex-col-reverse gap-3 border-t border-[var(--border)] bg-[var(--surface-card)] px-5 py-4 sm:flex-row sm:px-6">
            <button @click="closeEditModal" :disabled="saving || avatarUploading" class="flex-1 rounded-lg py-3 text-sm text-[var(--text-muted)] disabled:opacity-40" type="button">
              取消
            </button>
            <button
              @click="handleSaveEdit"
              :disabled="saving || avatarUploading"
              class="primary-button flex-1 rounded-lg bg-[var(--text)] py-3 text-sm font-medium text-[var(--surface)] disabled:opacity-30"
              type="button"
            >
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Camera, Trash2, X } from 'lucide-vue-next'
import { useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import {
  getUserPosts,
  getUserProfile,
  getUserStats,
  updateUserProfile,
  type UserProfile,
  type UserStats,
} from '@/api/users'
import { togglePostLike, type Post } from '@/api/posts'
import { uploadMedia } from '@/api/media'
import AppShell from '@/components/AppShell.vue'
import PostCard from '@/components/PostCard.vue'
import RightRail from '@/components/RightRail.vue'
import { mediaUrl } from '@/utils/media'

const route = useRoute()
const { user, setUser } = useAuth()
const profile = ref<UserProfile | null>(null)
const stats = ref<UserStats>({ post_count: 0, comment_count: 0, like_count: 0 })
const posts = ref<Post[]>([])
const showEdit = ref(false)
const saving = ref(false)
const avatarUploading = ref(false)
const avatarInput = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const editForm = reactive({
  avatar_url: '',
  bio: '',
  role_in_family: '',
  birthday: '',
})

const isOwn = computed(() => user.value?.id === profile.value?.id)
const profileInitial = computed(() => profile.value?.username.charAt(0).toUpperCase() || '?')
const profileAvatarUrl = computed(() => profile.value?.avatar_url ? mediaUrl(profile.value.avatar_url) : '')
const editAvatarPreview = computed(() => editForm.avatar_url ? mediaUrl(editForm.avatar_url) : '')
const profileSections = computed(() => [
  { title: profile.value?.role_in_family || '未设置', body: '家庭角色', meta: 'Role' },
  { title: profile.value?.birthday || '未设置', body: '生日', meta: 'Birthday' },
  { title: profile.value?.email || '未设置', body: '登录邮箱', meta: 'Email' },
])
const quickSections = computed(() => [
  { title: '发布新记忆', body: '记录今天的照片或文字', meta: 'Create' },
  { title: '查看家庭相册', body: '浏览整理好的照片集合', meta: 'Albums' },
])

let currentLoadId = 0

watch(
  () => route.params.id,
  (value) => {
    const id = Array.isArray(value) ? value[0] : value
    void loadProfile(id ? String(id) : '')
  },
  { immediate: true }
)

async function loadProfile(id: string) {
  const loadId = ++currentLoadId
  resetProfileState()

  if (!id) {
    errorMessage.value = '成员 ID 无效'
    return
  }

  loading.value = true
  try {
    const [profileResult, statsResult, postsResult] = await Promise.all([
      getUserProfile(id),
      getUserStats(id),
      getUserPosts(id),
    ])

    if (loadId !== currentLoadId) return

    profile.value = profileResult
    stats.value = statsResult
    posts.value = postsResult.posts
    syncEditForm()
  } catch (e) {
    if (loadId !== currentLoadId) return
    errorMessage.value = typeof e === 'string' ? e : '加载失败'
  } finally {
    if (loadId === currentLoadId) {
      loading.value = false
    }
  }
}

function resetProfileState() {
  loading.value = false
  errorMessage.value = ''
  profile.value = null
  stats.value = { post_count: 0, comment_count: 0, like_count: 0 }
  posts.value = []
  showEdit.value = false
  avatarUploading.value = false
  editForm.avatar_url = ''
  editForm.bio = ''
  editForm.role_in_family = ''
  editForm.birthday = ''
}

function syncEditForm() {
  editForm.avatar_url = profile.value?.avatar_url || ''
  editForm.bio = profile.value?.bio || ''
  editForm.role_in_family = profile.value?.role_in_family || ''
  editForm.birthday = profile.value?.birthday || ''
}

function openEditModal() {
  syncEditForm()
  errorMessage.value = ''
  showEdit.value = true
}

function closeEditModal() {
  if (saving.value || avatarUploading.value) return
  showEdit.value = false
}

async function handleLike(postItem: Post) {
  try {
    const result = await togglePostLike(postItem.id)
    postItem.is_liked = result.liked
    postItem.like_count = result.like_count
  } catch (e) {
    errorMessage.value = typeof e === 'string' ? e : '操作失败'
  }
}

async function handleSaveEdit() {
  if (!profile.value || saving.value || avatarUploading.value) return
  saving.value = true
  errorMessage.value = ''
  try {
    const updated = await updateUserProfile(profile.value.id, {
      avatar_url: editForm.avatar_url || null,
      bio: editForm.bio.trim() || undefined,
      role_in_family: editForm.role_in_family.trim() || undefined,
      birthday: editForm.birthday || undefined,
    })
    profile.value = updated
    syncEditForm()
    if (isOwn.value && user.value) {
      setUser({ ...user.value, ...updated })
    }
    showEdit.value = false
  } catch (e) {
    errorMessage.value = typeof e === 'string' ? e : '保存失败'
  } finally {
    saving.value = false
  }
}

async function handleAvatarUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || avatarUploading.value) return

  if (!file.type.startsWith('image/')) {
    errorMessage.value = '头像只支持图片文件'
    return
  }

  avatarUploading.value = true
  errorMessage.value = ''
  try {
    const response = await uploadMedia([file])
    const uploaded = response.files[0]
    if (!uploaded || uploaded.type !== 'image') {
      errorMessage.value = '头像只支持图片文件'
      return
    }
    editForm.avatar_url = uploaded.url || uploaded.raw_url || ''
  } catch (e) {
    errorMessage.value = typeof e === 'string' ? e : '头像上传失败'
  } finally {
    avatarUploading.value = false
  }
}

function removeAvatar() {
  editForm.avatar_url = ''
}
</script>

<style scoped>
.soft-button,
.primary-button,
.profile-card,
.stat-card,
.profile-input,
.modal-panel {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    opacity 180ms ease,
    transform 180ms ease;
}

.soft-button:hover,
.primary-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.profile-card,
.stat-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 238, 211, 0.08)),
    var(--surface-card);
}

.profile-card:hover,
.stat-card:hover {
  border-color: rgba(217, 77, 48, 0.18);
  box-shadow: 0 18px 44px rgba(143, 80, 40, 0.14);
}

.stat-card:hover {
  transform: translateY(-2px);
}

.profile-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(227, 107, 93, 0.09);
}

.modal-panel {
  animation: modal-in 180ms ease-out both;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.985);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .soft-button,
  .primary-button,
  .profile-card,
  .stat-card,
  .profile-input,
  .modal-panel {
    animation: none;
    transition: none;
  }

  .soft-button:hover,
  .primary-button:hover:not(:disabled),
  .stat-card:hover {
    transform: none;
  }
}
</style>
