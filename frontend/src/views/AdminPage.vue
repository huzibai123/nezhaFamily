<template>
  <AppShell page-title="家庭管理" page-description="管理成员、邀请码和家庭空间的视觉身份">
    <template #header>
      <div class="admin-hero overflow-hidden rounded-xl border border-[var(--border)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
        <div class="grid gap-5 sm:grid-cols-[auto_minmax(0,1fr)_auto] sm:items-center">
          <FamilySeal
            :label="settings.family_name || '哪吒家庭'"
            :logo-url="previewUrl(settings.logo_url || '')"
          />
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
        class="rounded-lg border border-[var(--border-focus)] bg-[var(--accent-soft)] px-4 py-3 text-sm text-[var(--accent)]"
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

      <section class="admin-panel rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-panel)] sm:p-6">
        <div class="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex min-w-0 gap-4">
            <span class="grid h-12 w-12 shrink-0 place-items-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
              <Bot :size="22" stroke-width="1.9" aria-hidden="true" />
            </span>
            <div class="min-w-0">
              <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">AI housekeeper</p>
              <div class="mt-2 flex flex-wrap items-center gap-2">
                <h2 class="text-xl font-semibold text-[var(--text)]">AI 家庭管家</h2>
                <span class="rounded-md px-2 py-1 text-[11px] font-medium" :class="aiStatusClass(aiStatus?.status)">
                  {{ aiStatusLabel(aiStatus?.status) }}
                </span>
              </div>
              <p class="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
                {{ aiStatusSummary }}
              </p>
            </div>
          </div>
          <RouterLink
            to="/admin/ai"
            class="primary-button inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)]"
          >
            进入 AI 配置
          </RouterLink>
        </div>

        <div class="mt-5 grid gap-3 sm:grid-cols-3">
          <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
            <p class="text-lg font-semibold text-[var(--text)]">{{ aiStatus?.personas_enabled ?? 0 }}</p>
            <p class="mt-1 text-xs text-[var(--text-muted)]">启用角色</p>
          </div>
          <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
            <p class="text-lg font-semibold text-[var(--text)]">{{ aiStatus?.auto_comment_personas ?? 0 }}</p>
            <p class="mt-1 text-xs text-[var(--text-muted)]">自动评论</p>
          </div>
          <div class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-4">
            <p class="text-lg font-semibold text-[var(--text)]">{{ aiPendingSuggestions.length }}</p>
            <p class="mt-1 text-xs text-[var(--text-muted)]">待审建议</p>
          </div>
        </div>
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
              class="activity-row rounded-lg border border-[var(--border-focus)] bg-[var(--accent-soft)] p-3"
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
          <div class="border-b border-[var(--border)] pb-4">
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Runtime</p>
            <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">运行状态</h2>
            <p class="mt-2 text-sm leading-6 text-[var(--text-secondary)]">
              Celery 与数据库连接的只读检查，适合部署后快速确认任务环境。
            </p>
          </div>

          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <div v-for="item in runtimeHealthCards" :key="item.label" class="rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
              <p class="text-sm font-semibold" :class="item.ok ? 'text-[var(--accent-leaf)]' : 'text-[var(--accent)]'">
                {{ item.ok ? '正常' : '需检查' }}
              </p>
              <p class="mt-1 text-xs text-[var(--text-muted)]">{{ item.label }}</p>
            </div>
          </div>

          <div class="mt-4 space-y-2 rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3 text-xs leading-5 text-[var(--text-muted)]">
            <p class="truncate">Broker: {{ runtimeStatus.celery_broker_url || '未配置' }}</p>
            <p class="truncate">Result: {{ runtimeStatus.celery_result_backend || '未配置' }}</p>
            <p v-if="runtimeStatus.celery_ping_error" class="text-[var(--accent)]">Worker: {{ runtimeStatus.celery_ping_error }}</p>
            <p>AI 任务超时 {{ runtimeStatus.task_timeouts.ai_task_time_limit_seconds }}s / 清理任务 {{ runtimeStatus.task_timeouts.media_cleanup_task_time_limit_seconds }}s</p>
            <p>媒体回收站保留 {{ runtimeStatus.media_trash_retention_days }} 天</p>
            <p>
              最近备份校验：{{ runtimeStatus.latest_backup_verification_status ? runtimeStatus.latest_backup_verification_status : '暂无' }}
              <span v-if="runtimeStatus.latest_backup_message"> · {{ runtimeStatus.latest_backup_message }}</span>
            </p>
            <p>
              AI Provider：{{ runtimeStatus.ai_provider_status || '未初始化' }}
              <span v-if="runtimeStatus.ai_provider_paused_reason || runtimeStatus.ai_provider_last_error" class="text-[var(--accent)]">
                · {{ runtimeStatus.ai_provider_paused_reason || runtimeStatus.ai_provider_last_error }}
              </span>
            </p>
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
                class="mt-3 rounded-lg border border-[var(--border-focus)] bg-[var(--accent-soft)] px-3 py-2 text-xs leading-5 text-[var(--accent)]"
              >
                {{ backupVerificationText[item.backup_id] }}
              </div>
            </div>
          </div>
        </article>
      </section>

      <section class="theme-studio rounded-xl border border-[var(--border)] bg-[var(--surface-card)] p-4 shadow-[var(--shadow-panel)] sm:p-5">
        <div class="flex flex-col gap-3 border-b border-[var(--border)] pb-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Theme studio</p>
            <h2 class="mt-2 text-xl font-semibold text-[var(--text)]">家庭主题工作台</h2>
          </div>
          <button
            @click="saveSettings"
            class="primary-button inline-flex items-center justify-center gap-2 rounded-lg bg-[var(--text)] px-5 py-2.5 text-sm font-medium text-[var(--surface)]"
            type="button"
          >
            <Check :size="16" stroke-width="2" aria-hidden="true" />
            保存主题
          </button>
        </div>

        <div class="mt-5 grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <div
            class="theme-preview overflow-hidden rounded-lg border border-[var(--border)]"
            :style="{ '--preview-background': activeBackgroundUrl ? `url('${previewUrl(activeBackgroundUrl)}')` : 'none' }"
          >
            <div class="theme-preview__stage">
              <img
                v-for="ornament in enabledOrnaments"
                :key="ornament.id"
                :src="previewUrl(ornament.url)"
                alt=""
                class="theme-preview__ornament"
                :class="`theme-preview__ornament--${ornament.position}`"
                :style="{ width: `${Math.round(ornament.size * 0.52)}px`, opacity: ornament.opacity }"
              />
              <div class="theme-preview__content">
                <FamilySeal
                  compact
                  :label="settings.family_name || '哪吒家庭'"
                  :logo-url="previewUrl(settings.logo_url || '')"
                />
                <div class="min-w-0">
                  <p class="text-xs font-medium uppercase tracking-[0.16em] text-[var(--text-muted)]">Live preview</p>
                  <h3 class="mt-2 truncate text-2xl font-semibold text-[var(--text)]">
                    {{ settings.family_name || '哪吒家庭' }}
                  </h3>
                  <p class="mt-2 line-clamp-2 text-sm leading-6 text-[var(--text-secondary)]">
                    {{ settings.tagline || '私有的家庭记忆中枢' }}
                  </p>
                </div>
              </div>
              <div v-if="cursorAsset?.enabled && cursorAsset.url" class="theme-preview__cursor">
                <MousePointer2 :size="16" stroke-width="2" aria-hidden="true" />
                <img :src="previewUrl(cursorAsset.url)" alt="" :style="{ width: `${Math.round(cursorAsset.size * 0.52)}px` }" />
              </div>
            </div>
          </div>

          <div class="grid gap-4">
            <div class="grid gap-4 lg:grid-cols-2">
              <label class="space-y-1.5">
                <span class="text-xs text-[var(--text-muted)]">家庭名称</span>
                <input v-model="settings.family_name" class="admin-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] outline-none" />
              </label>
              <label class="space-y-1.5">
                <span class="text-xs text-[var(--text-muted)]">一句话说明</span>
                <input v-model="settings.tagline" class="admin-input w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] outline-none" />
              </label>
              <label class="space-y-1.5">
                <span class="text-xs text-[var(--text-muted)]">画布色</span>
                <input v-model="settings.theme_color" type="color" class="color-input h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1" />
              </label>
              <label class="space-y-1.5">
                <span class="text-xs text-[var(--text-muted)]">强调色</span>
                <input v-model="settings.accent_color" type="color" class="color-input h-11 w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] p-1" />
              </label>
            </div>

            <div class="theme-tool-row rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-[var(--text)]">家庭 Logo</p>
                  <p class="text-xs text-[var(--text-muted)]">{{ settings.logo_url ? '已使用上传图片' : '使用默认动态印章' }}</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button @click="logoInput?.click()" class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]" type="button">
                    <Upload :size="15" stroke-width="2" aria-hidden="true" />
                    上传
                  </button>
                  <button v-if="settings.logo_url" @click="settings.logo_url = ''" class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]" type="button">
                    <Trash2 :size="15" stroke-width="2" aria-hidden="true" />
                    移除
                  </button>
                </div>
              </div>
              <input ref="logoInput" class="hidden" type="file" accept="image/jpeg,image/png,image/gif,image/webp" @change="uploadThemeFile('logo', $event)" />
            </div>

            <div class="theme-tool-row rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-[var(--text)]">背景图库</p>
                  <p class="text-xs text-[var(--text-muted)]">{{ themeAssetDraft.backgrounds.length }} / 12</p>
                </div>
                <button @click="backgroundInput?.click()" class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]" type="button">
                  <ImageIcon :size="15" stroke-width="2" aria-hidden="true" />
                  上传背景
                </button>
              </div>
              <input ref="backgroundInput" class="hidden" type="file" accept="image/jpeg,image/png,image/gif,image/webp" @change="uploadThemeFile('background', $event)" />
              <div v-if="themeAssetDraft.backgrounds.length" class="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
                <article
                  v-for="asset in themeAssetDraft.backgrounds"
                  :key="asset.id"
                  class="background-choice overflow-hidden rounded-lg border"
                  :class="settings.background_image_url === asset.url ? 'background-choice-active' : 'border-[var(--border)]'"
                >
                  <button @click="selectBackground(asset.url)" class="block w-full text-left" type="button">
                    <img :src="previewUrl(asset.url)" alt="" class="aspect-[4/3] w-full object-cover" />
                    <span class="block truncate px-2 py-1.5 text-xs text-[var(--text-muted)]">{{ asset.label || '家庭背景' }}</span>
                  </button>
                  <button
                    @click="removeBackground(asset.id)"
                    class="background-choice__delete grid h-8 w-full place-items-center border-t border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--accent)]"
                    type="button"
                    aria-label="移除背景"
                  >
                    <Trash2 :size="14" stroke-width="2" aria-hidden="true" />
                  </button>
                </article>
              </div>
            </div>

            <div class="theme-tool-row rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-[var(--text)]">鼠标跟随小动图</p>
                  <p class="text-xs text-[var(--text-muted)]">桌面端精细指针启用</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button @click="cursorInput?.click()" class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]" type="button">
                    <MousePointer2 :size="15" stroke-width="2" aria-hidden="true" />
                    上传
                  </button>
                  <button v-if="cursorAsset?.url" @click="removeCursorAsset" class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]" type="button">
                    <Trash2 :size="15" stroke-width="2" aria-hidden="true" />
                    移除
                  </button>
                </div>
              </div>
              <input ref="cursorInput" class="hidden" type="file" accept="image/jpeg,image/png,image/gif,image/webp" @change="uploadThemeFile('cursor', $event)" />
              <div v-if="cursorAsset" class="mt-3 grid gap-3 sm:grid-cols-[auto_minmax(0,1fr)] sm:items-center">
                <label class="inline-flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                  <input v-model="cursorAsset.enabled" type="checkbox" class="h-4 w-4 rounded border-[var(--border)]" />
                  启用
                </label>
                <label class="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                  大小
                  <input v-model.number="cursorAsset.size" type="range" min="24" max="160" class="min-w-0 flex-1" />
                  <span class="w-10 text-right">{{ cursorAsset.size }}</span>
                </label>
              </div>
            </div>

            <div class="theme-tool-row rounded-lg border border-[var(--border)] bg-[var(--surface-panel)] p-3">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-[var(--text)]">UI 小挂饰</p>
                  <p class="text-xs text-[var(--text-muted)]">{{ themeAssetDraft.ornaments.length }} / 8</p>
                </div>
                <button @click="ornamentInput?.click()" class="soft-button inline-flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--text-secondary)]" type="button">
                  <Sparkles :size="15" stroke-width="2" aria-hidden="true" />
                  上传挂饰
                </button>
              </div>
              <input ref="ornamentInput" class="hidden" type="file" accept="image/jpeg,image/png,image/gif,image/webp" @change="uploadThemeFile('ornament', $event)" />
              <div v-if="themeAssetDraft.ornaments.length" class="mt-3 space-y-2">
                <article
                  v-for="ornament in themeAssetDraft.ornaments"
                  :key="ornament.id"
                  class="ornament-row grid gap-3 rounded-lg border border-[var(--border)] bg-[var(--surface-card)] p-3 lg:grid-cols-[auto_minmax(0,1fr)_auto]"
                >
                  <img :src="previewUrl(ornament.url)" alt="" class="h-14 w-14 rounded-lg object-cover" />
                  <div class="grid gap-2 sm:grid-cols-3">
                    <select v-model="ornament.position" class="admin-input rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text)] outline-none">
                      <option v-for="option in ornamentPositions" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>
                    <label class="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                      尺寸
                      <input v-model.number="ornament.size" type="range" min="24" max="220" class="min-w-0 flex-1" />
                    </label>
                    <label class="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                      透明
                      <input v-model.number="ornament.opacity" type="range" min="0.1" max="1" step="0.05" class="min-w-0 flex-1" />
                    </label>
                  </div>
                  <div class="flex items-center gap-2">
                    <label class="inline-flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
                      <input v-model="ornament.enabled" type="checkbox" class="h-4 w-4 rounded border-[var(--border)]" />
                      显示
                    </label>
                    <button @click="removeOrnament(ornament.id)" class="soft-button grid h-9 w-9 place-items-center rounded-lg border border-[var(--border)] text-[var(--text-muted)]" type="button" aria-label="移除挂饰">
                      <Trash2 :size="15" stroke-width="2" aria-hidden="true" />
                    </button>
                  </div>
                </article>
              </div>
            </div>
          </div>
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
import {
  Bot,
  Check,
  Image as ImageIcon,
  MousePointer2,
  Sparkles,
  Trash2,
  Upload,
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import FamilySeal from '@/components/FamilySeal.vue'
import RightRail from '@/components/RightRail.vue'
import { mediaUrl } from '@/utils/media'
import { useAuth } from '@/composables/useAuth'
import {
  createAdminBackup,
  downloadAdminBackupFile,
  getAIAlbumSuggestions,
  getAIStatus,
  getAdminOverview,
  getAdminUsers,
  getFamilySettings,
  regenerateUserInviteCode,
  updateAdminUser,
  updateFamilySettings,
  uploadThemeAsset,
  verifyAdminBackup,
  type AIAlbumSuggestion,
  type AIStatus,
  type AdminBackupFileKind,
  type AdminOverview,
  type AdminUser,
  type AdminRole,
  type AdminBackupItem,
  type AdminRuntimeStatus,
  type AdminStorageStatus,
  type FamilySettings,
  type FamilyThemeAssets,
  type ThemeAssetKind,
  type ThemeBackgroundAsset,
  type ThemeOrnamentPosition,
} from '@/api/admin'
import { useFamilySettings } from '@/composables/useFamilySettings'

interface MemberDraft {
  role: AdminRole
  role_in_family: string
  bio: string
}

const emptyThemeAssets = (): FamilyThemeAssets => ({
  backgrounds: [],
  cursor: null,
  ornaments: [],
})

const router = useRouter()
const { user: currentUser, refreshCurrentUser, setUser } = useAuth()
const overview = ref<AdminOverview | null>(null)
const users = ref<AdminUser[]>([])
const memberDrafts = reactive<Record<string, MemberDraft>>({})
const aiStatus = ref<AIStatus | null>(null)
const aiAlbumSuggestions = ref<AIAlbumSuggestion[]>([])
const message = ref('')
const backupRunning = ref(false)
const savingMemberId = ref('')
const verifyingBackupId = ref('')
const downloadingBackupKey = ref('')
const backupVerificationText = reactive<Record<string, string>>({})
const { setFamilySettings } = useFamilySettings()
const logoInput = ref<HTMLInputElement>()
const backgroundInput = ref<HTMLInputElement>()
const cursorInput = ref<HTMLInputElement>()
const ornamentInput = ref<HTMLInputElement>()
const themePreviewUrls = reactive<Record<string, string>>({})
const settings = reactive<FamilySettings>({
  family_name: '哪吒家庭',
  tagline: '私有的家庭记忆中枢',
  theme_color: '#f6f1e8',
  accent_color: '#c9432f',
  background_image_url: '',
  logo_url: '',
  theme_assets: emptyThemeAssets(),
})

const ornamentPositions: Array<{ value: ThemeOrnamentPosition; label: string }> = [
  { value: 'top-left', label: '左上' },
  { value: 'top-right', label: '右上' },
  { value: 'bottom-left', label: '左下' },
  { value: 'bottom-right', label: '右下' },
]

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
const aiPendingSuggestions = computed(() =>
  aiAlbumSuggestions.value.filter((suggestion) => suggestion.status === 'pending')
)
const aiStatusSummary = computed(() => {
  const provider = aiStatus.value?.provider
  if (provider?.paused_reason || provider?.last_error) {
    return provider.paused_reason || provider.last_error || 'AI 管家已暂停。'
  }
  if (aiStatus.value?.status === 'active') {
    return `${provider?.name || '默认模型'} · ${provider?.text_model || '已连接'}`
  }
  return '默认关闭。模型、角色和自动任务已移到独立配置页。'
})
const themeAssetDraft = computed(() => ensureThemeAssets())
const cursorAsset = computed(() => themeAssetDraft.value.cursor)
const enabledOrnaments = computed(() =>
  themeAssetDraft.value.ornaments.filter(ornament => ornament.enabled && ornament.url)
)
const activeBackgroundUrl = computed(() => {
  if (settings.background_image_url) return settings.background_image_url
  return themeAssetDraft.value.backgrounds.find(asset => asset.enabled)?.url || ''
})

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

const runtimeStatus = computed<AdminRuntimeStatus>(() => overview.value?.runtime ?? {
  database_available: false,
  redis_available: false,
  celery_ping_available: false,
  celery_ping_error: null,
  celery_broker_url: '',
  celery_result_backend: '',
  celery_broker_configured: false,
  celery_result_backend_configured: false,
  task_timeouts: {
    task_time_limit_seconds: 0,
    task_soft_time_limit_seconds: 0,
    image_task_time_limit_seconds: 0,
    image_task_soft_time_limit_seconds: 0,
    ai_task_time_limit_seconds: 0,
    ai_task_soft_time_limit_seconds: 0,
    media_cleanup_task_time_limit_seconds: 0,
    media_cleanup_task_soft_time_limit_seconds: 0,
  },
  media_trash_retention_days: 0,
  latest_backup_verification_status: null,
  latest_backup_verified_at: null,
  latest_backup_message: null,
  ai_provider_status: null,
  ai_provider_last_error: null,
  ai_provider_paused_reason: null,
  ai_provider_checked_at: null,
  checked_at: '',
})
const runtimeHealthCards = computed(() => [
  { label: '数据库连接', ok: runtimeStatus.value.database_available },
  { label: 'Redis 连接', ok: runtimeStatus.value.redis_available },
  { label: 'Worker Ping', ok: runtimeStatus.value.celery_ping_available },
  { label: 'Celery Broker', ok: runtimeStatus.value.celery_broker_configured },
  { label: '结果后端', ok: runtimeStatus.value.celery_result_backend_configured },
])

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
    const [
      overviewResult,
      usersResult,
      settingsResult,
      aiStatusResult,
      aiSuggestionsResult,
    ] = await Promise.allSettled([
      getAdminOverview(),
      getAdminUsers(),
      getFamilySettings(),
      getAIStatus(),
      getAIAlbumSuggestions(),
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

    if (aiStatusResult.status === 'fulfilled') {
      aiStatus.value = aiStatusResult.value
    }

    if (aiSuggestionsResult.status === 'fulfilled') {
      aiAlbumSuggestions.value = aiSuggestionsResult.value
    }

    const failed = [
      overviewResult,
      usersResult,
      settingsResult,
      aiStatusResult,
      aiSuggestionsResult,
    ].some((item) => item.status === 'rejected')
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

async function uploadThemeFile(kind: ThemeAssetKind, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  const assets = ensureThemeAssets()
  if (kind === 'background' && assets.backgrounds.length >= 12) {
    message.value = '背景图库最多保存 12 张'
    return
  }
  if (kind === 'ornament' && assets.ornaments.length >= 8) {
    message.value = 'UI 挂饰最多保存 8 个'
    return
  }

  try {
    const response = await uploadThemeAsset(kind, [file])
    const uploaded = response.files[0]
    const rawUrl = uploaded.raw_url || stripMediaToken(uploaded.url)
    const signedUrl = uploaded.url || rawUrl
    if (!rawUrl) throw new Error('upload_missing_url')
    themePreviewUrls[rawUrl] = signedUrl

    if (kind === 'logo') {
      settings.logo_url = rawUrl
    } else if (kind === 'background') {
      const asset: ThemeBackgroundAsset = {
        id: createThemeAssetId('bg'),
        url: rawUrl,
        label: file.name,
        enabled: true,
      }
      assets.backgrounds.unshift(asset)
      settings.background_image_url = rawUrl
    } else if (kind === 'cursor') {
      assets.cursor = {
        url: rawUrl,
        enabled: true,
        size: 76,
      }
    } else {
      assets.ornaments.push({
        id: createThemeAssetId('orn'),
        url: rawUrl,
        position: ornamentPositions[assets.ornaments.length % ornamentPositions.length].value,
        enabled: true,
        size: 96,
        opacity: 0.72,
      })
    }

    settings.theme_assets = normalizeThemeAssets(assets)
    message.value = `${themeAssetLabel(kind)}已上传，保存后对全家生效`
  } catch (error) {
    message.value = typeof error === 'string' ? error : `${themeAssetLabel(kind)}上传失败`
  }
}

function selectBackground(url: string) {
  settings.background_image_url = url
  ensureThemeAssets().backgrounds.forEach((asset) => {
    asset.enabled = asset.url === url
  })
}

function removeBackground(assetId: string) {
  const assets = ensureThemeAssets()
  const removed = assets.backgrounds.find(asset => asset.id === assetId)
  assets.backgrounds = assets.backgrounds.filter(asset => asset.id !== assetId)
  if (removed?.url === settings.background_image_url) {
    settings.background_image_url = assets.backgrounds[0]?.url || ''
  }
}

function removeCursorAsset() {
  ensureThemeAssets().cursor = null
}

function removeOrnament(assetId: string) {
  const assets = ensureThemeAssets()
  assets.ornaments = assets.ornaments.filter(ornament => ornament.id !== assetId)
}

function ensureThemeAssets(): FamilyThemeAssets {
  if (!settings.theme_assets) {
    settings.theme_assets = emptyThemeAssets()
  }
  settings.theme_assets.backgrounds ||= []
  settings.theme_assets.ornaments ||= []
  return settings.theme_assets
}

function normalizeThemeAssets(value: FamilyThemeAssets): FamilyThemeAssets {
  return {
    backgrounds: (value.backgrounds || []).slice(0, 12).map((asset) => ({
      id: asset.id || createThemeAssetId('bg'),
      url: asset.url,
      label: asset.label || '',
      enabled: asset.enabled !== false,
    })),
    cursor: value.cursor?.url
      ? {
          url: value.cursor.url,
          enabled: Boolean(value.cursor.enabled),
          size: clampNumber(value.cursor.size, 24, 160, 76),
        }
      : null,
    ornaments: (value.ornaments || []).slice(0, 8).map((ornament, index) => ({
      id: ornament.id || createThemeAssetId('orn'),
      url: ornament.url,
      position: ornament.position || ornamentPositions[index % ornamentPositions.length].value,
      enabled: ornament.enabled !== false,
      size: clampNumber(ornament.size, 24, 220, 96),
      opacity: clampNumber(ornament.opacity, 0.1, 1, 0.72),
    })),
  }
}

function createThemeAssetId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
}

function clampNumber(value: number | undefined, min: number, max: number, fallback: number) {
  if (typeof value !== 'number' || Number.isNaN(value)) return fallback
  return Math.min(max, Math.max(min, value))
}

function previewUrl(url: string): string {
  if (!url) return ''
  return mediaUrl(themePreviewUrls[url] || url)
}

function stripMediaToken(url: string): string {
  if (!url.startsWith('/media/')) return url
  return url.split('?', 1)[0]
}

function themeAssetLabel(kind: ThemeAssetKind): string {
  if (kind === 'background') return '背景图'
  if (kind === 'logo') return '家庭 Logo'
  if (kind === 'cursor') return '鼠标小动图'
  return 'UI 挂饰'
}

async function saveSettings() {
  try {
    settings.theme_assets = normalizeThemeAssets(ensureThemeAssets())
    const updated = await updateFamilySettings(settings)
    Object.assign(settings, withDefaultSettings(updated))
    setFamilySettings(settings)
    message.value = '家庭设置已保存'
  } catch (error) {
    message.value = formatErrorMessage(error, '家庭设置保存失败')
  }
}

function formatErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string') return error
  if (Array.isArray(error)) {
    return error
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) return String(item.msg)
        return ''
      })
      .filter(Boolean)
      .join('；') || fallback
  }
  if (error && typeof error === 'object' && 'message' in error) {
    return String((error as { message: unknown }).message)
  }
  return fallback
}

function withDefaultSettings(value: FamilySettings): FamilySettings {
  return {
    family_name: value.family_name || '哪吒家庭',
    tagline: value.tagline || '私有的家庭记忆中枢',
    theme_color: value.theme_color || '#f6f1e8',
    accent_color: value.accent_color || '#c9432f',
    background_image_url: value.background_image_url || '',
    logo_url: value.logo_url || '',
    theme_assets: normalizeThemeAssets(value.theme_assets || emptyThemeAssets()),
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

function aiStatusLabel(status?: string): string {
  if (status === 'active') return '运行中'
  if (status === 'paused_billing_or_auth') return '欠费或鉴权暂停'
  if (status === 'paused_rate_limit') return '限流暂停'
  if (status === 'paused_error') return '异常暂停'
  return '关闭'
}

function aiStatusClass(status?: string): string {
  if (status === 'active') return 'ai-badge-active'
  if (status?.startsWith('paused')) return 'ai-badge-paused'
  return 'ai-badge-disabled'
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
    linear-gradient(135deg, rgba(255, 255, 255, 0.38), rgba(45, 108, 104, 0.06)),
    var(--surface-card);
}

.storage-panel {
  overflow: hidden;
  position: relative;
}

.theme-studio,
.theme-tool-row,
.theme-preview,
.background-choice,
.ornament-row {
  transition:
    background-color 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    transform 180ms ease;
}

.theme-preview {
  --preview-background: none;
  background:
    linear-gradient(180deg, rgba(246, 241, 232, 0.74), rgba(232, 224, 210, 0.52)),
    var(--preview-background),
    var(--surface-panel);
  background-position: center;
  background-size: auto, cover, auto;
  min-height: 24rem;
  position: relative;
}

.theme-preview__stage {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.36), rgba(45, 108, 104, 0.06)),
    rgba(255, 255, 255, 0.22);
  display: grid;
  inset: 1rem;
  overflow: hidden;
  padding: 1.25rem;
  place-items: center;
  position: absolute;
  border: 1px solid rgba(63, 45, 36, 0.12);
  border-radius: 14px;
}

.theme-preview__content {
  align-items: center;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(63, 45, 36, 0.12);
  border-radius: 14px;
  box-shadow: 0 18px 42px rgba(63, 45, 36, 0.12);
  display: grid;
  gap: 1rem;
  grid-template-columns: auto minmax(0, 1fr);
  max-width: 24rem;
  padding: 1rem;
  position: relative;
  width: 100%;
  z-index: 1;
}

.theme-preview__cursor {
  align-items: center;
  background: rgba(255, 255, 255, 0.64);
  border: 1px solid rgba(63, 45, 36, 0.12);
  border-radius: 999px;
  bottom: 1rem;
  color: var(--text-muted);
  display: inline-flex;
  gap: 0.55rem;
  padding: 0.45rem 0.7rem;
  position: absolute;
  right: 1rem;
}

.theme-preview__cursor img {
  max-height: 3rem;
  object-fit: contain;
}

.theme-preview__ornament {
  filter: drop-shadow(0 12px 18px rgba(63, 45, 36, 0.16));
  position: absolute;
  z-index: 0;
}

.theme-preview__ornament--top-left {
  left: 1rem;
  top: 1rem;
}

.theme-preview__ornament--top-right {
  right: 1rem;
  top: 1rem;
}

.theme-preview__ornament--bottom-left {
  bottom: 1rem;
  left: 1rem;
}

.theme-preview__ornament--bottom-right {
  bottom: 1rem;
  right: 1rem;
}

.theme-tool-row:hover,
.background-choice:hover,
.ornament-row:hover {
  border-color: rgba(201, 67, 47, 0.18);
  box-shadow: 0 14px 34px rgba(63, 45, 36, 0.1);
}

.background-choice-active {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-soft);
}

.background-choice__delete {
  transition: color 160ms ease, background-color 160ms ease;
}

.background-choice__delete:hover {
  background: var(--accent-soft);
}

.wind-wheel {
  animation: admin-wheel-spin 2.8s linear infinite;
  background:
    radial-gradient(circle, rgba(255, 255, 252, 0.9) 0 18%, transparent 19%),
    conic-gradient(from 20deg, rgba(201, 67, 47, 0), rgba(201, 67, 47, 0.62), rgba(45, 108, 104, 0.58), rgba(201, 67, 47, 0));
  border: 1px solid rgba(49, 38, 33, 0.14);
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
  background: linear-gradient(90deg, rgba(201, 67, 47, 0), rgba(201, 67, 47, 0.12), rgba(45, 108, 104, 0.1), rgba(201, 67, 47, 0));
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
  border-color: rgba(201, 67, 47, 0.16);
  box-shadow: 0 18px 44px rgba(47, 39, 35, 0.1);
  transform: translateY(-1px);
}

.member-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.3), rgba(45, 108, 104, 0.05)),
    var(--surface-panel);
}

.admin-input:focus {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.primary-button:hover,
.soft-button:hover {
  transform: translateY(-1px);
}

.role-admin,
.role-member {
  border: 1px solid rgba(49, 38, 33, 0.12);
}

.role-admin {
  background: rgba(201, 67, 47, 0.12);
  color: var(--accent);
}

.role-member {
  background: rgba(92, 121, 84, 0.12);
  color: var(--accent-leaf);
}

.ai-badge-active,
.ai-badge-paused,
.ai-badge-disabled {
  border: 1px solid rgba(49, 38, 33, 0.12);
}

.ai-badge-active {
  background: rgba(92, 121, 84, 0.14);
  color: var(--accent-leaf);
}

.ai-badge-paused {
  background: rgba(201, 67, 47, 0.12);
  color: var(--accent);
}

.ai-badge-disabled {
  background: rgba(87, 77, 69, 0.1);
  color: var(--text-secondary);
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
  .theme-studio,
  .theme-tool-row,
  .theme-preview,
  .background-choice,
  .ornament-row,
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
  .theme-tool-row:hover,
  .background-choice:hover,
  .ornament-row:hover,
  .primary-button:hover,
  .soft-button:hover {
    transform: none;
  }
}
</style>
