<template>
  <AppShell page-title="PostCard 布局演示" page-description="对比不同布局模式的视觉效果">
    <div class="space-y-12">
      <!-- Timeline 模式 -->
      <section>
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold" style="color:var(--text)">Timeline 模式</h2>
            <p class="mt-1 text-sm" style="color:var(--text-secondary)">大留白，适合主时间线</p>
          </div>
          <span
            class="rounded-lg border px-3 py-1.5 text-xs font-medium"
            style="background:var(--accent-soft);color:var(--accent);border-color:var(--accent)"
          >
            layout-mode="timeline"
          </span>
        </div>
        <div class="space-y-6">
          <PostCard
            v-for="post in samplePosts.slice(0, 2)"
            :key="`timeline-${post.id}`"
            :post="post"
            layout-mode="timeline"
            @click="handleClick"
            @like="handleLike"
          />
        </div>
      </section>

      <!-- Grid 模式 -->
      <section>
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold" style="color:var(--text)">Grid 模式</h2>
            <p class="mt-1 text-sm" style="color:var(--text-secondary)">图片优先，正方形展示</p>
          </div>
          <span
            class="rounded-lg border px-3 py-1.5 text-xs font-medium"
            style="background:var(--accent-soft);color:var(--accent);border-color:var(--accent)"
          >
            layout-mode="grid"
          </span>
        </div>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <PostCard
            v-for="post in samplePosts"
            :key="`grid-${post.id}`"
            :post="post"
            layout-mode="grid"
            @click="handleClick"
            @like="handleLike"
          />
        </div>
      </section>

      <!-- List 模式 -->
      <section>
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold" style="color:var(--text)">List 模式</h2>
            <p class="mt-1 text-sm" style="color:var(--text-secondary)">紧凑横向，适合列表和搜索</p>
          </div>
          <span
            class="rounded-lg border px-3 py-1.5 text-xs font-medium"
            style="background:var(--accent-soft);color:var(--accent);border-color:var(--accent)"
          >
            layout-mode="list"
          </span>
        </div>
        <div class="space-y-2">
          <PostCard
            v-for="post in samplePosts"
            :key="`list-${post.id}`"
            :post="post"
            layout-mode="list"
            @click="handleClick"
            @like="handleLike"
          />
        </div>
      </section>

      <!-- Default 模式 -->
      <section>
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold" style="color:var(--text)">Default 模式</h2>
            <p class="mt-1 text-sm" style="color:var(--text-secondary)">标准样式，通用场景</p>
          </div>
          <span
            class="rounded-lg border px-3 py-1.5 text-xs font-medium"
            style="background:var(--surface-elevated);color:var(--text-secondary);border-color:var(--border)"
          >
            无需指定或 layout-mode="default"
          </span>
        </div>
        <div class="space-y-5">
          <PostCard
            v-for="post in samplePosts.slice(0, 3)"
            :key="`default-${post.id}`"
            :post="post"
            @click="handleClick"
            @like="handleLike"
          />
        </div>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import PostCard from '@/components/PostCard.vue'
import type { Post } from '@/api/posts'

const router = useRouter()

// 示例数据
const samplePosts = ref<Post[]>([
  {
    id: '1',
    author_id: 'user1',
    author_username: '爸爸',
    content: '今天带宝宝去公园玩，天气真好！看到好多小朋友在放风筝，宝宝也很开心地跑来跑去。',
    media_urls: [
      { url: '/api/v1/media/sample1.jpg', type: 'image' }
    ],
    like_count: 12,
    comment_count: 5,
    is_liked: false,
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
  },
  {
    id: '2',
    author_id: 'user2',
    author_username: '妈妈',
    content: '宝宝今天第一次自己穿鞋子，虽然左右穿反了，但是看到他认真的样子真的好可爱！',
    media_urls: [
      { url: '/api/v1/media/sample2.jpg', type: 'image' },
      { url: '/api/v1/media/sample3.jpg', type: 'image' }
    ],
    like_count: 18,
    comment_count: 8,
    is_liked: true,
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString()
  },
  {
    id: '3',
    author_id: 'user3',
    author_username: '奶奶',
    content: '给宝宝做了他最爱吃的红烧肉，看着他吃得香香的，心里暖暖的。',
    media_urls: [],
    like_count: 6,
    comment_count: 3,
    is_liked: false,
    created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: '4',
    author_id: 'user4',
    author_username: '爷爷',
    content: '陪宝宝看动画片，他笑得好开心。',
    media_urls: [
      { url: '/api/v1/media/sample4.jpg', type: 'image' }
    ],
    like_count: 9,
    comment_count: 2,
    is_liked: false,
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
  }
])

function handleClick(postId: string) {
  console.log('点击帖子:', postId)
  router.push(`/post/${postId}`)
}

function handleLike(post: Post) {
  console.log('点赞帖子:', post.id)
  post.is_liked = !post.is_liked
  post.like_count += post.is_liked ? 1 : -1
}
</script>

<style scoped>
section {
  padding: 1.5rem;
  border-radius: 1rem;
  background: var(--surface-panel);
  border: 1px solid var(--border);
}
</style>
