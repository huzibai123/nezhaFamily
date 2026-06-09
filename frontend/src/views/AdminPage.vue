<template>
  <AppShell page-title="家庭管理" page-description="管理成员、邀请码和家庭空间的视觉身份">
    <template #header>
      <div class="admin-hero overflow-hidden rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
        <div class="grid gap-5 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center">
          <FamilySeal :label="settings.family_name || '哪吒家庭'" />
          <div class="min-w-0">
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-[var(--text-muted)]">
              Family archive console
            </p>
            <h1 class="mt-2 text-2xl font-semibold text-[var(--text)] sm:text-3xl">
              {{ settings.family_name || '哪吒家庭' }}
            </h1>
            <p class="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
              {{ settings.tagline || '把家庭成员、邀请入口和空间气质收在一个安静的资料台里。' }}
            </p>
          </div>
          <button
            @click="loadAll"
            class="soft-button inline-flex justify-center rounded-lg border border-[var(--border)] px-4 py-2.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
            type="button"
          >
            刷新
          </button>
        </div>
      </div>
    </template>

    <div class="space-y-6">
      <p
        v-if="message"
        class="rounded-lg border border-[color:rgb(217_77_48_/_0.22)] bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--accent)]"
      >
        {{ message }}
      </p>

      <section class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="stat in statCards"
          :key="stat.label"
          class="stat-card rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)]"
        >
          <p class="text-xs font-medium uppercase tracking-[0.12em] text-[var(--text-muted)]">{{ stat.label }}</p>
          <p class="mt-2 text-2xl font-semibold text-[var(--text)]">{{ stat.value }}</p>
          <p class="mt-1 text-xs text-[var(--text-muted)]">{{ stat.meta }}</p>
        </article>
      </section>

      <section class="grid gap-4 xl:grid-cols-3">
        <article class="admin-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
          <div class="border-b border-[var(--border)] pb-3">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Comments</p>
            <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">最近评论</h2>
          </div>
          <div class="mt-4 space-y-3">
            <RouterLink
              v-for="comment in recentComments"
              :key="comment.id"
              :to="{ path: `/post/${comment.post_id}`, query: { comment: comment.id } }"
              class="activity-row block rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3"
            >
              <p class="truncate text-sm font-medium text-[var(--text)]">{{ comment.author_username }}</p>
              <p class="mt-1 line-clamp-2 text-xs leading-5 text-[var(--text-secondary)]">{{ comment.content }}</p>
              <p class="mt-2 text-[11px] text-[var(--text-muted)]">{{ formatDateTime(comment.created_at) }}</p>
            </RouterLink>
            <p v-if="!recentComments.length" class="rounded-lg border border-dashed border-[var(--border)] p-4 text-center text-xs text-[var(--text-muted)]">
              还没有评论记录。
            </p>
          </div>
        </article>

        <article class="admin-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
          <div class="border-b border-[var(--border)] pb-3">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Media</p>
            <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">最近媒体</h2>
          </div>
          <div class="mt-4 space-y-3">
            <div
              v-for="media in recentMedia"
              :key="media.id"
              class="activity-row rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-medium text-[var(--text)]">{{ media.original_name || (media.file_type === 'video' ? '家庭视频' : '家庭照片') }}</p>
                  <p class="mt-1 text-xs text-[var(--text-muted)]">{{ media.uploader_username }} · {{ formatBytes(media.file_size) }}</p>
                </div>
                <span class="rounded-md bg-[var(--accent-soft)] px-2 py-1 text-[11px] text-[var(--accent)]">
                  {{ media.file_type === 'video' ? '视频' : '图片' }}
                </span>
              </div>
            </div>
            <p v-if="!recentMedia.length" class="rounded-lg border border-dashed border-[var(--border)] p-4 text-center text-xs text-[var(--text-muted)]">
              还没有媒体上传。
            </p>
          </div>
        </article>

        <article class="admin-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
          <div class="border-b border-[var(--border)] pb-3">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Upload checks</p>
            <h2 class="mt-2 text-lg font-semibold text-[var(--text)]">上传异常线索</h2>
          </div>
          <div class="mt-4 space-y-3">
            <div
              v-for="media in uploadWarnings"
              :key="media.id"
              class="activity-row rounded-lg border border-[color:rgb(217_77_48_/_0.22)] bg-[var(--accent-soft)] p-3"
            >
              <p class="truncate text-sm font-medium text-[var(--accent)]">{{ media.original_name || media.id }}</p>
              <p class="mt-1 text-xs leading-5 text-[var(--text-secondary)]">
                {{ media.warning || '媒体元数据需要检查' }} · {{ media.uploader_username }}
              </p>
            </div>
            <p v-if="!uploadWarnings.length" class="rounded-lg border border-dashed border-[var(--border)] p-4 text-center text-xs text-[var(--text-muted)]">
              暂无异常上传线索。
            </p>
          </div>
        </article>
      </section>

      <section class="admin-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
        <div class="flex flex-col gap-3 border-b border-[var(--border)] pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Members</p>
            <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">家庭成员</h2>
          </div>
          <p class="text-sm text-[var(--text-muted)]">{{ users.length }} 位成员</p>
        </div>

        <div class="mt-4 space-y-3">
          <article
            v-for="member in users"
            :key="member.id"
            class="member-card rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4"
          >
            <div class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_12rem_9rem_9rem] xl:items-center">
              <div class="flex min-w-0 items-center gap-3">
                <div class="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]">
                  {{ initial(member.username) }}
                </div>
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-2">
                    <h3 class="truncate text-sm font-semibold text-[var(--text)]">{{ member.username }}</h3>
                    <span class="rounded-md px-2 py-0.5 text-[11px]" :class="memberDrafts[member.id]?.role === 'admin' ? 'role-admin' : 'role-member'">
                      {{ memberDrafts[member.id]?.role === 'admin' ? '管理员' : '成员' }}
                    </span>
                  </div>
                  <p class="mt-1 truncate text-xs text-[var(--text-muted)]">{{ member.email }}</p>
                </div>
              </div>

              <input
                v-model="memberDrafts[member.id].role_in_family"
                class="admin-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2 text-sm text-[var(--text)] outline-none"
                placeholder="家庭角色"
              />

              <select
                v-model="memberDrafts[member.id].role"
                class="admin-input rounded-lg border border-[var(--border)] bg-[var(--surface-card)] px-3 py-2 text-sm text-[var(--text)] outline-none"
              >
                <option value="member">成员</option>
                <option value="admin">管理员</option>
              </select>

              <div class="flex gap-2">
                <button
                  @click="saveMember(member)"
                  :disabled="savingMemberId === member.id"
                  class="primary-button flex-1 rounded-lg bg-[var(--text)] px-3 py-2 text-sm font-medium text-[var(--surface)] disabled:opacity-50"
                  type="button"
                >
                  {{ savingMemberId === member.id ? '保存中' : '保存' }}
                </button>
                <button
                  @click="regenInvite(member)"
                  class="soft-button rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]"
                  type="button"
                >
                  邀请
                </button>
                <button
                  @click="copyInvite(member)"
                  class="soft-button rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]"
                  type="button"
                >
                  复制
                </button>
              </div>
            </div>

            <div class="mt-3 grid gap-2 text-xs text-[var(--text-muted)] sm:grid-cols-3">
              <span>帖子 {{ member.post_count ?? 0 }}</span>
              <span>评论 {{ member.comment_count ?? 0 }}</span>
              <span class="truncate">邀请码 {{ member.invite_code || '未生成' }}</span>
            </div>
          </article>
        </div>
      </section>

      <section class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <article class="admin-panel storage-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Storage</p>
              <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">存储状态</h2>
              <p class="mt-2 text-sm leading-6 text-[var(--text-secondary)]">
                媒体目录 {{ storageStatus.media_root || '未加载' }}，剩余空间
                {{ storageStatus.disk_free_percent.toFixed(1) }}%。
              </p>
            </div>
            <div class="wind-wheel" aria-hidden="true"></div>
          </div>
          <div class="mt-5 grid gap-3 sm:grid-cols-3">
            <div v-for="item in storageCards" :key="item.label" class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
              <p class="text-lg font-semibold text-[var(--text)]">{{ item.value }}</p>
              <p class="mt-1 text-xs text-[var(--text-muted)]">{{ item.label }}</p>
            </div>
          </div>
        </article>

        <article class="admin-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Backup</p>
              <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">备份状态</h2>
            </div>
            <button
              @click="runBackup"
              class="primary-button rounded-lg bg-[var(--text)] px-4 py-2 text-sm font-medium text-[var(--surface)] disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="backupRunning"
            >
              {{ backupRunning ? '备份中' : '立即备份' }}
            </button>
          </div>

          <div class="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
            <p class="text-sm font-medium text-[var(--text)]">
              {{ latestBackup ? '最近备份已完成' : '还没有备份记录' }}
            </p>
            <p class="mt-1 text-xs leading-5 text-[var(--text-muted)]">
              {{ latestBackupSummary }}
            </p>
          </div>

          <div class="mt-4 space-y-3">
            <div
              v-for="item in recentBackups"
              :key="item.backup_id"
              class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3"
            >
              <div class="flex gap-3">
                <span class="mt-1 h-2 w-2 shrink-0 rounded-full bg-[var(--accent)]"></span>
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-medium text-[var(--text)]">
                    {{ formatDateTime(item.created_at) }}
                  </p>
                  <p class="mt-1 text-xs leading-5 text-[var(--text-muted)]">
                    {{ formatBytes(item.size_bytes) }} · {{ item.database_record_count }} 条记录 ·
                    {{ item.media_file_count }} 个媒体文件
                  </p>
                  <p class="mt-1 truncate text-[11px] text-[var(--text-muted)]">
                    {{ item.snapshot_file }}
                  </p>
                </div>
              </div>

              <div class="mt-3 flex flex-wrap gap-2">
                <button
                  @click="verifyBackup(item)"
                  class="backup-action rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-50"
                  type="button"
                  :disabled="verifyingBackupId === item.backup_id"
                >
                  {{ verifyingBackupId === item.backup_id ? '校验中' : '校验' }}
                </button>
                <button
                  @click="downloadBackup(item, 'database')"
                  class="backup-action rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-50"
                  type="button"
                  :disabled="downloadingBackupKey === `${item.backup_id}:database`"
                >
                  数据库
                </button>
                <button
                  v-if="item.media_archive_file"
                  @click="downloadBackup(item, 'media')"
                  class="backup-action rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-50"
                  type="button"
                  :disabled="downloadingBackupKey === `${item.backup_id}:media`"
                >
                  媒体包
                </button>
                <button
                  @click="downloadBackup(item, 'manifest')"
                  class="backup-action rounded-lg border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)] disabled:opacity-50"
                  type="button"
                  :disabled="downloadingBackupKey === `${item.backup_id}:manifest`"
                >
                  清单
                </button>
              </div>

              <div
                v-if="backupVerificationText[item.backup_id]"
                class="mt-3 rounded-lg border border-[color:rgb(217_77_48_/_0.16)] bg-[var(--accent-soft)] px-3 py-2 text-xs leading-5 text-[var(--accent)]"
              >
                {{ backupVerificationText[item.backup_id] }}
              </div>
            </div>
          </div>
        </article>
      </section>

      <section class="admin-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
        <div class="border-b border-[var(--border)] pb-4">
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Identity</p>
          <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">家庭设置</h2>
        </div>

        <div class="mt-4 grid gap-4 lg:grid-cols-2">
          <label class="space-y-1.5">
            <span class="text-xs text-[var(--text-muted)]">家庭名称</span>
            <input v-model="settings.family_name" class="admin-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] outline-none" />
          </label>
          <label class="space-y-1.5">
            <span class="text-xs text-[var(--text-muted)]">一句话说明</span>
            <input v-model="settings.tagline" class="admin-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] outline-none" />
          </label>
          <label class="space-y-1.5">
            <span class="text-xs text-[var(--text-muted)]">主题色</span>
            <input v-model="settings.theme_color" type="color" class="color-input h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1" />
          </label>
          <label class="space-y-1.5">
            <span class="text-xs text-[var(--text-muted)]">强调色</span>
            <input v-model="settings.accent_color" type="color" class="color-input h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1" />
          </label>
          <label class="space-y-1.5 lg:col-span-2">
            <span class="text-xs text-[var(--text-muted)]">本地背景图 URL</span>
            <input
              v-model="settings.background_image_url"
              class="admin-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] outline-none"
              placeholder="/media/your-family-background.jpg"
            />
          </label>
        </div>

        <div class="mt-5 flex justify-end">
          <button
            @click="saveSettings"
            class="primary-button rounded-lg bg-[var(--text)] px-5 py-2.5 text-sm font-medium text-[var(--surface)]"
            type="button"
          >
            保存家庭设置
          </button>
        </div>
      </section>
    </div>

    <template #right>
      <div class="space-y-4">
        <RightRail title="管理建议">
          <div class="space-y-3 text-sm leading-6 text-[var(--text-secondary)]">
            <p>邀请码可以按成员重新生成，适合单独发给家人。</p>
            <p>家庭名称和本地背景图会逐步成为整个空间的视觉身份。</p>
          </div>
        </RightRail>
        <RightRail title="最近加入">
          <div class="space-y-3">
            <div v-for="member in recentMembers" :key="member.id" class="flex items-center gap-3">
              <span class="grid h-9 w-9 place-items-center rounded-lg bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]">
                {{ initial(member.username) }}
              </span>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-[var(--text)]">{{ member.username }}</p>
                <p class="text-xs text-[var(--text-muted)]">{{ formatDate(member.created_at) }}</p>
              </div>
            </div>
          </div>
        </RightRail>
        <RightRail title="最近发布">
          <div class="space-y-3">
            <div v-for="member in recentPosters" :key="member.id" class="flex items-center gap-3">
              <span class="grid h-9 w-9 place-items-center rounded-lg bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]">
                {{ initial(member.username) }}
              </span>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-[var(--text)]">{{ member.username }}</p>
                <p class="text-xs text-[var(--text-muted)]">{{ member.post_count ?? 0 }} 条动态</p>
              </div>
            </div>
          </div>
        </RightRail>
      </div>
    </template>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import FamilySeal from '@/components/FamilySeal.vue'
import RightRail from '@/components/RightRail.vue'
import { useAuth } from '@/composables/useAuth'
import {
  createAdminBackup,
  downloadAdminBackupFile,
  getAdminOverview,
  getAdminUsers,
  getFamilySettings,
  regenerateUserInviteCode,
  updateAdminUser,
  updateFamilySettings,
  verifyAdminBackup,
  type AdminBackupFileKind,
  type AdminOverview,
  type AdminUser,
  type AdminRole,
  type AdminBackupItem,
  type AdminStorageStatus,
  type FamilySettings,
} from '@/api/admin'
import { useFamilySettings } from '@/composables/useFamilySettings'

interface MemberDraft {
  role: AdminRole
  role_in_family: string
  bio: string
}

const router = useRouter()
const { user: currentUser, refreshCurrentUser, setUser } = useAuth()
const overview = ref<AdminOverview | null>(null)
const users = ref<AdminUser[]>([])
const memberDrafts = reactive<Record<string, MemberDraft>>({})
const message = ref('')
const backupRunning = ref(false)
const savingMemberId = ref('')
const verifyingBackupId = ref('')
const downloadingBackupKey = ref('')
const backupVerificationText = reactive<Record<string, string>>({})
const { setFamilySettings } = useFamilySettings()
const settings = reactive<FamilySettings>({
  family_name: '哪吒家庭',
  tagline: '私有的家庭记忆中枢',
  theme_color: '#f8d9b7',
  accent_color: '#d94d30',
  background_image_url: '',
})

const statCards = computed(() => {
  const totals = overviewTotals.value
  return [
    { label: '成员', value: totals?.users ?? users.value.length, meta: '家庭账号' },
    { label: '动态', value: totals?.posts ?? 0, meta: '时间线记忆' },
    { label: '评论', value: totals?.comments ?? 0, meta: '家人互动' },
    { label: '影像', value: totals?.media ?? 0, meta: '照片和视频' },
    { label: '相册', value: totals?.albums ?? 0, meta: '整理集合' },
    { label: '日历', value: totals?.events ?? 0, meta: '家庭事件' },
  ]
})

const overviewTotals = computed(() => ({
  users: overview.value?.totals?.users ?? overview.value?.user_count ?? users.value.length,
  posts: overview.value?.totals?.posts ?? overview.value?.post_count ?? 0,
  comments: overview.value?.totals?.comments ?? overview.value?.comment_count ?? 0,
  media: overview.value?.totals?.media ?? overview.value?.media_count ?? 0,
  albums: overview.value?.totals?.albums ?? overview.value?.album_count ?? 0,
  events: overview.value?.totals?.events ?? overview.value?.event_count ?? 0,
}))

const recentMembers = computed(() =>
  (overview.value?.recent_members?.length ? overview.value.recent_members : users.value)
    .slice()
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)
)

const recentPosters = computed(() =>
  (overview.value?.recent_posting_members || [])
    .slice()
    .sort((a, b) => (b.post_count ?? 0) - (a.post_count ?? 0))
    .slice(0, 5)
)

const recentComments = computed(() => overview.value?.recent_comments ?? [])
const recentMedia = computed(() => overview.value?.recent_media ?? [])
const uploadWarnings = computed(() => overview.value?.upload_warnings ?? [])

const storageCards = computed(() => [
  { label: '目录文件', value: storageStatus.value.media_file_count },
  { label: '目录占用', value: formatBytes(storageStatus.value.media_directory_bytes) },
  { label: '磁盘剩余', value: formatBytes(storageStatus.value.disk_free_bytes) },
])

const storageStatus = computed<AdminStorageStatus>(() => overview.value?.storage ?? {
  media_root: '',
  backup_root: '',
  media_file_count: 0,
  media_directory_bytes: 0,
  database_media_bytes: 0,
  disk_total_bytes: 0,
  disk_used_bytes: 0,
  disk_free_bytes: 0,
  disk_free_percent: 0,
  last_scanned_at: '',
})

const latestBackup = computed(() => overview.value?.backups?.latest ?? null)
const recentBackups = computed(() => overview.value?.backups?.recent ?? [])
const latestBackupSummary = computed(() => {
  if (!latestBackup.value) {
    return `备份目录：${overview.value?.backups?.backup_root || storageStatus.value.backup_root || '未加载'}`
  }

  return `${formatDateTime(latestBackup.value.created_at)} · ${formatBytes(latestBackup.value.size_bytes)}`
})

onMounted(loadAll)

async function loadAll() {
  message.value = ''
  try {
    const [overviewResult, usersResult, settingsResult] = await Promise.allSettled([
      getAdminOverview(),
      getAdminUsers(),
      getFamilySettings(),
    ])

    if (overviewResult.status === 'fulfilled') {
      overview.value = overviewResult.value
    }

    if (usersResult.status === 'fulfilled') {
      users.value = Array.isArray(usersResult.value) ? usersResult.value : usersResult.value.users
      syncMemberDrafts(users.value)
    }

    if (settingsResult.status === 'fulfilled') {
      Object.assign(settings, withDefaultSettings(settingsResult.value))
    }

    const failed = [overviewResult, usersResult, settingsResult].some((item) => item.status === 'rejected')
    if (failed) message.value = '部分管理数据暂时不可用，已显示可加载内容。'
  } catch (error) {
    message.value = typeof error === 'string' ? error : '管理数据加载失败'
  }
}

async function saveMember(member: AdminUser) {
  if (savingMemberId.value) return
  const draft = memberDrafts[member.id] ?? resetMemberDraft(member)
  const snapshot = { ...member }
  savingMemberId.value = member.id
  message.value = ''

  try {
    const updated = await updateAdminUser(member.id, {
      role: draft.role,
      role_in_family: draft.role_in_family.trim() || null,
      bio: draft.bio.trim() || null,
    })
    const merged = { ...member, ...updated }
    users.value = users.value.map((item) => (item.id === member.id ? { ...item, ...merged } : item))
    resetMemberDraft(merged)

    if (currentUser.value?.id === member.id) {
      setUser({ ...currentUser.value, ...merged })
      const refreshed = await refreshCurrentUser()
      if (!refreshed) return
      if (refreshed.role !== 'admin') {
        await router.replace({ name: 'Timeline' })
      }
    }

    message.value = `已保存 ${merged.username} 的资料`
  } catch (error) {
    resetMemberDraft(snapshot)
    message.value = typeof error === 'string' ? error : '成员保存失败'
  } finally {
    savingMemberId.value = ''
  }
}

function syncMemberDrafts(nextUsers: AdminUser[]) {
  const activeIds = new Set(nextUsers.map((member) => member.id))
  for (const memberId of Object.keys(memberDrafts)) {
    if (!activeIds.has(memberId)) {
      delete memberDrafts[memberId]
    }
  }
  nextUsers.forEach(resetMemberDraft)
}

function resetMemberDraft(member: AdminUser): MemberDraft {
  const draft = {
    role: member.role,
    role_in_family: member.role_in_family || '',
    bio: member.bio || '',
  }
  memberDrafts[member.id] = draft
  return draft
}

async function regenInvite(member: AdminUser) {
  try {
    const result = await regenerateUserInviteCode(member.id)
    member.invite_code = result.invite_code || result.code || member.invite_code
    message.value = `${member.username} 的邀请码已更新：${member.invite_code || '已生成'}`
  } catch (error) {
    message.value = typeof error === 'string' ? error : '邀请码生成失败'
  }
}

async function runBackup() {
  backupRunning.value = true
  message.value = ''
  try {
    const backup = await createAdminBackup()
    mergeBackup(backup)
    message.value = `备份完成：${formatBytes(backup.size_bytes)}`
  } catch (error) {
    message.value = typeof error === 'string' ? error : '备份创建失败'
  } finally {
    backupRunning.value = false
  }
}

async function verifyBackup(backup: AdminBackupItem) {
  verifyingBackupId.value = backup.backup_id
  try {
    const verification = await verifyAdminBackup(backup.backup_id)
    const failedChecks = verification.checks.filter((item) => !item.ok)
    backupVerificationText[backup.backup_id] = failedChecks.length
      ? `${verification.message}：${failedChecks.map((item) => item.detail).join('；')}`
      : `${verification.message}。${verification.restore_hint}`
  } catch (error) {
    backupVerificationText[backup.backup_id] = typeof error === 'string' ? error : '备份校验失败'
  } finally {
    verifyingBackupId.value = ''
  }
}

async function downloadBackup(backup: AdminBackupItem, fileKind: AdminBackupFileKind) {
  const key = `${backup.backup_id}:${fileKind}`
  downloadingBackupKey.value = key
  try {
    const blob = await downloadAdminBackupFile(backup.backup_id, fileKind)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = backupFileName(backup, fileKind)
    link.click()
    URL.revokeObjectURL(url)
    message.value = `${backupFileLabel(fileKind)}已开始下载`
  } catch (error) {
    message.value = typeof error === 'string' ? error : '备份文件下载失败'
  } finally {
    downloadingBackupKey.value = ''
  }
}

function mergeBackup(backup: AdminBackupItem) {
  if (!overview.value) return
  const currentBackups = overview.value.backups ?? {
    backup_root: storageStatus.value.backup_root,
    latest: null,
    recent: [],
  }
  overview.value = {
    ...overview.value,
    backups: {
      ...currentBackups,
      latest: backup,
      recent: [backup, ...currentBackups.recent.filter((item) => item.backup_id !== backup.backup_id)]
        .slice(0, 5),
    },
  }
}

async function copyInvite(member: AdminUser) {
  if (!member.invite_code) {
    message.value = '请先生成邀请码'
    return
  }

  try {
    const inviteLink = `${window.location.origin}/register?invite=${encodeURIComponent(member.invite_code)}`
    await navigator.clipboard.writeText(inviteLink)
    message.value = `${member.username} 的邀请链接已复制`
  } catch {
    message.value = `邀请链接：/register?invite=${member.invite_code}`
  }
}

async function saveSettings() {
  try {
    const updated = await updateFamilySettings(settings)
    Object.assign(settings, withDefaultSettings(updated))
    setFamilySettings(settings)
    message.value = '家庭设置已保存'
  } catch (error) {
    message.value = typeof error === 'string' ? error : '家庭设置保存失败'
  }
}

function withDefaultSettings(value: FamilySettings): FamilySettings {
  return {
    family_name: value.family_name || '哪吒家庭',
    tagline: value.tagline || '私有的家庭记忆中枢',
    theme_color: value.theme_color || '#f8d9b7',
    accent_color: value.accent_color || '#d94d30',
    background_image_url: value.background_image_url || '',
    updated_by: value.updated_by,
    created_at: value.created_at,
    updated_at: value.updated_at,
  }
}

function initial(name: string): string {
  return name.trim().slice(0, 1).toUpperCase() || '家'
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString('zh-CN')
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatBytes(value?: number | null): string {
  const bytes = value ?? 0
  if (bytes < 1024) return `${bytes} B`

  const units = ['KB', 'MB', 'GB', 'TB']
  let size = bytes / 1024
  let index = 0
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index += 1
  }
  return `${size.toFixed(size >= 10 ? 1 : 2)} ${units[index]}`
}

function backupFileName(backup: AdminBackupItem, fileKind: AdminBackupFileKind): string {
  if (fileKind === 'media') return `${backup.backup_id}-media.tar.gz`
  if (fileKind === 'manifest') return `manifest-${backup.backup_id}.json`
  return `${backup.backup_id}-database.json`
}

function backupFileLabel(fileKind: AdminBackupFileKind): string {
  if (fileKind === 'media') return '媒体包'
  if (fileKind === 'manifest') return '备份清单'
  return '数据库快照'
}
</script>

<style scoped>
.admin-hero,
.admin-panel,
.stat-card,
.member-card,
.activity-row,
.admin-input,
.soft-button,
.primary-button {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.backup-action {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

.backup-action:hover {
  transform: translateY(-1px);
}

.admin-hero,
.admin-panel,
.stat-card {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.34), rgba(217, 77, 48, 0.06)),
    var(--surface-card);
}

.storage-panel {
  overflow: hidden;
  position: relative;
}

.wind-wheel {
  animation: admin-wheel-spin 2.8s linear infinite;
  background:
    radial-gradient(circle, rgba(255, 248, 235, 0.9) 0 18%, transparent 19%),
    conic-gradient(from 20deg, rgba(217, 77, 48, 0), rgba(217, 77, 48, 0.72), rgba(212, 137, 37, 0.82), rgba(217, 77, 48, 0));
  border: 1px solid rgba(132, 74, 40, 0.16);
  border-radius: 999px;
  height: 3.2rem;
  opacity: 0.88;
  width: 3.2rem;
}

.admin-hero {
  position: relative;
}

.admin-hero::after {
  animation: admin-ribbon 9s ease-in-out infinite alternate;
  background: linear-gradient(90deg, rgba(217, 77, 48, 0), rgba(217, 77, 48, 0.18), rgba(212, 137, 37, 0.12), rgba(217, 77, 48, 0));
  border-radius: 999px;
  bottom: 1.3rem;
  content: '';
  height: 1.9rem;
  pointer-events: none;
  position: absolute;
  right: -4rem;
  transform: rotate(-8deg);
  width: min(22rem, 46vw);
}

.stat-card:hover,
.member-card:hover,
.activity-row:hover,
.admin-panel:focus-within {
  border-color: rgba(217, 77, 48, 0.18);
  box-shadow: 0 18px 44px rgba(143, 80, 40, 0.14);
  transform: translateY(-1px);
}

.member-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.28), rgba(255, 238, 211, 0.08)),
    var(--surface-panel);
}

.admin-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(217, 77, 48, 0.1);
}

.primary-button:hover,
.soft-button:hover {
  transform: translateY(-1px);
}

.role-admin,
.role-member {
  border: 1px solid rgba(132, 74, 40, 0.12);
}

.role-admin {
  background: rgba(217, 77, 48, 0.12);
  color: var(--accent);
}

.role-member {
  background: rgba(92, 121, 84, 0.12);
  color: var(--accent-leaf);
}

.color-input {
  min-width: 0;
}

@keyframes admin-ribbon {
  from {
    transform: translate3d(0, 0, 0) rotate(-8deg);
  }
  to {
    transform: translate3d(-1rem, -0.35rem, 0) rotate(-4deg);
  }
}

@keyframes admin-wheel-spin {
  to {
    transform: rotate(1turn);
  }
}

@media (prefers-reduced-motion: reduce) {
  .admin-hero,
  .admin-panel,
  .wind-wheel,
  .stat-card,
  .member-card,
  .activity-row,
  .admin-input,
  .soft-button,
  .primary-button,
    .admin-hero::after {
    animation: none;
    transition: none;
  }

  .stat-card:hover,
  .member-card:hover,
  .activity-row:hover,
  .admin-panel:focus-within,
  .primary-button:hover,
  .soft-button:hover {
    transform: none;
  }
}
</style>
