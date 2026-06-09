<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" @click.self="$emit('update:modelValue', false)"
        class="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4"
        style="background:rgba(75,40,25,0.38);backdrop-filter:blur(6px)">
        <div @click.stop
          class="w-full max-w-md rounded-2xl overflow-hidden"
          style="background:var(--surface-card);max-height:90vh;overflow-y:auto">

          <!-- 头部 -->
          <div class="flex items-center justify-between px-6 py-5 border-b" style="border-color:var(--border)">
            <h2 class="text-lg font-semibold">{{ event ? '编辑事件' : '新建事件' }}</h2>
            <button @click="$emit('update:modelValue', false)"
              class="text-2xl leading-none hover:opacity-60 transition-opacity"
              style="color:var(--text-muted)">&times;</button>
          </div>

          <!-- 表单 -->
          <form @submit.prevent="handleSubmit" class="p-6 space-y-5">
            <!-- 标题 -->
            <div>
              <label class="block text-sm font-medium mb-2" style="color:var(--text)">标题*</label>
              <input v-model="form.title" type="text" required
                class="w-full px-4 py-3 rounded-xl border transition-all"
                style="background:var(--surface-hover);border-color:var(--border);color:var(--text)"
                placeholder="事件标题" />
            </div>

            <!-- 类型 -->
            <div>
              <label class="block text-sm font-medium mb-2" style="color:var(--text)">类型</label>
              <div class="grid grid-cols-3 gap-2">
                <button v-for="t in types" :key="t.value" type="button"
                  @click="form.event_type = t.value"
                  class="px-3 py-2 rounded-lg text-sm transition-all"
                  :style="{
                    background: form.event_type === t.value ? 'var(--accent)' : 'var(--surface-hover)',
                    color: form.event_type === t.value ? '#fff' : 'var(--text-secondary)',
                    borderColor: form.event_type === t.value ? 'var(--accent)' : 'var(--border)'
                  }">{{ t.label }}</button>
              </div>
            </div>

            <!-- 全天 -->
            <label class="flex items-center gap-3 cursor-pointer">
              <input v-model="form.is_all_day" type="checkbox"
                class="w-5 h-5 rounded border"
                style="accent-color:var(--accent)" />
              <span class="text-sm font-medium" style="color:var(--text)">全天事件</span>
            </label>

            <!-- 开始时间 -->
            <div>
              <label class="block text-sm font-medium mb-2" style="color:var(--text)">开始时间*</label>
              <input v-model="form.start_time" :type="form.is_all_day ? 'date' : 'datetime-local'" required
                class="w-full px-4 py-3 rounded-xl border transition-all"
                style="background:var(--surface-hover);border-color:var(--border);color:var(--text)" />
            </div>

            <!-- 结束时间 -->
            <div v-if="!form.is_all_day">
              <label class="block text-sm font-medium mb-2" style="color:var(--text)">结束时间</label>
              <input v-model="form.end_time" type="datetime-local"
                class="w-full px-4 py-3 rounded-xl border transition-all"
                style="background:var(--surface-hover);border-color:var(--border);color:var(--text)" />
            </div>

            <!-- 地点 -->
            <div>
              <label class="block text-sm font-medium mb-2" style="color:var(--text)">地点</label>
              <input v-model="form.location" type="text"
                class="w-full px-4 py-3 rounded-xl border transition-all"
                style="background:var(--surface-hover);border-color:var(--border);color:var(--text)"
                placeholder="事件地点" />
            </div>

            <!-- 描述 -->
            <div>
              <label class="block text-sm font-medium mb-2" style="color:var(--text)">描述</label>
              <textarea v-model="form.description" rows="3"
                class="w-full px-4 py-3 rounded-xl border transition-all resize-none"
                style="background:var(--surface-hover);border-color:var(--border);color:var(--text)"
                placeholder="事件描述"></textarea>
            </div>

            <!-- 提醒 -->
            <div>
              <label class="block text-sm font-medium mb-2" style="color:var(--text)">提醒</label>
              <select v-model="form.reminder_minutes"
                class="w-full px-4 py-3 rounded-xl border transition-all"
                style="background:var(--surface-hover);border-color:var(--border);color:var(--text)">
                <option :value="null">不提醒</option>
                <option :value="0">事件开始时</option>
                <option :value="15">提前 15 分钟</option>
                <option :value="30">提前 30 分钟</option>
                <option :value="60">提前 1 小时</option>
                <option :value="1440">提前 1 天</option>
              </select>
            </div>

            <!-- 按钮 -->
            <div class="flex gap-3 pt-2">
              <button v-if="event" type="button" @click="handleDelete"
                class="px-5 py-3 rounded-xl text-sm font-medium transition-all active:scale-[0.98]"
                style="background:var(--surface-hover);color:var(--accent)">删除</button>
              <button type="submit"
                class="flex-1 px-5 py-3 rounded-xl text-sm font-medium transition-all active:scale-[0.98]"
                style="background:var(--text);color:var(--surface)">{{ event ? '保存' : '创建' }}</button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Event } from '@/api/events'

const props = defineProps<{
  modelValue: boolean
  event?: Event
  selectedDate?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'submit': [data: {
    title: string
    description?: string
    start_time: string
    end_time?: string
    is_all_day: boolean
    event_type: string
    location?: string
    reminder_minutes?: number
  }]
  'delete': [eventId: string]
}>()

const types = [
  { value: 'birthday', label: '生日' },
  { value: 'anniversary', label: '纪念日' },
  { value: 'appointment', label: '约会' },
  { value: 'holiday', label: '假期' },
  { value: 'other', label: '其他' }
]

const form = ref({
  title: '',
  description: '' as string | undefined,
  start_time: '',
  end_time: '' as string | undefined,
  is_all_day: false,
  event_type: 'other',
  location: '' as string | undefined,
  reminder_minutes: undefined as number | undefined
})

// 监听 event 和 selectedDate 变化，初始化表单
watch(() => [props.event, props.selectedDate, props.modelValue], () => {
  if (!props.modelValue) return

  if (props.event) {
    form.value = {
      title: props.event.title,
      description: props.event.description || '',
      start_time: formatDateForInput(props.event.start_time, props.event.is_all_day),
      end_time: props.event.end_time ? formatDateForInput(props.event.end_time, props.event.is_all_day) : '',
      is_all_day: props.event.is_all_day,
      event_type: props.event.event_type,
      location: props.event.location || '',
      reminder_minutes: props.event.reminder_minutes
    }
  } else if (props.selectedDate) {
    form.value = {
      title: '',
      description: '',
      start_time: props.selectedDate,
      end_time: '',
      is_all_day: true,
      event_type: 'other',
      location: '',
      reminder_minutes: undefined
    }
  }
}, { immediate: true })

function formatDateForInput(isoString: string, isAllDay: boolean): string {
  const date = new Date(isoString)
  if (isAllDay) {
    return date.toISOString().split('T')[0]
  }
  const offset = date.getTimezoneOffset()
  const localDate = new Date(date.getTime() - offset * 60000)
  return localDate.toISOString().slice(0, 16)
}

function handleSubmit() {
  // 将空字符串转为 null，避免 Pydantic 验证失败
  const data = { ...form.value }
  if (!data.end_time) data.end_time = undefined
  if (!data.description) data.description = undefined
  if (!data.location) data.location = undefined
  if (data.reminder_minutes === null) data.reminder_minutes = undefined
  emit('submit', data)
}

function handleDelete() {
  if (props.event && confirm('确定删除这个事件吗？')) {
    emit('delete', props.event.id)
  }
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active > div, .modal-leave-active > div { transition: transform 0.2s ease; }
.modal-enter-from > div { transform: translateY(20px); }
.modal-leave-to > div { transform: translateY(20px); }
</style>
