<template>
  <AppShell page-title="家庭日历" page-description="把生日、纪念日、预约和家庭安排放在同一张月历里">
    <template #header>
      <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p class="text-xs font-medium uppercase tracking-[0.18em] text-[var(--text-muted)]">Calendar</p>
          <h1 class="mt-2 text-2xl font-semibold tracking-normal text-[var(--text)] sm:text-3xl">
            家庭日历
          </h1>
          <p class="mt-2 max-w-2xl text-sm leading-6 text-[var(--text-secondary)]">
            宽屏月历用于查看整月安排，右侧聚焦当前日期的事件。
          </p>
        </div>
        <button
          @click="handleCreateEvent"
          class="calendar-action inline-flex rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)] active:scale-[0.98]"
          type="button"
        >
          创建事件
        </button>
      </div>
    </template>

    <div class="calendar-panel rounded-lg border border-[var(--border)] bg-[var(--surface-card)] shadow-[var(--shadow-panel)]">
      <div class="flex items-center justify-between border-b border-[var(--border)] px-4 py-4 sm:px-5">
        <button
          @click="prevMonth"
          class="calendar-nav-button grid h-10 w-10 place-items-center rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
          type="button"
          aria-label="上个月"
        >
          ‹
        </button>
        <h2 class="text-lg font-semibold text-[var(--text)]">{{ currentYear }}年{{ currentMonth }}月</h2>
        <button
          @click="nextMonth"
          class="calendar-nav-button grid h-10 w-10 place-items-center rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)] hover:text-[var(--text)]"
          type="button"
          aria-label="下个月"
        >
          ›
        </button>
      </div>

      <div class="grid grid-cols-7 border-b border-[var(--border)]">
        <div
          v-for="day in weekDays"
          :key="day"
          class="px-2 py-3 text-center text-xs font-medium text-[var(--text-muted)]"
        >
          {{ day }}
        </div>
      </div>

      <div class="grid grid-cols-7">
        <button
          v-for="(day, index) in calendarDays"
          :key="`${day.fullDate}-${index}`"
          @click="handleDayClick(day)"
          class="calendar-day min-h-24 border-b border-r border-[var(--border)] p-2 text-left hover:bg-[var(--surface-elevated)] sm:min-h-28 sm:p-3"
          :class="{
            'opacity-35': !day.isCurrentMonth,
            'bg-[var(--surface-elevated)]': day.fullDate === selectedDate,
          }"
          :disabled="!day.isCurrentMonth"
          type="button"
        >
          <span
            class="inline-flex h-7 min-w-7 items-center justify-center rounded-md px-1.5 text-sm font-medium"
            :class="day.isToday ? 'bg-[var(--accent-soft)] text-[var(--accent)]' : 'text-[var(--text)]'"
          >
            {{ day.date }}
          </span>
          <div v-if="day.events.length" class="mt-2 space-y-1">
            <div
              v-for="event in day.events.slice(0, 2)"
              :key="event.id"
              class="event-pill truncate rounded-md px-2 py-1 text-[11px]"
              :style="{ background: eventBackground(event.event_type), color: 'var(--text-secondary)' }"
            >
              {{ event.title }}
            </div>
            <p v-if="day.events.length > 2" class="text-[11px] text-[var(--text-muted)]">
              +{{ day.events.length - 2 }} 个
            </p>
          </div>
        </button>
      </div>
    </div>

    <template #right>
      <div class="space-y-4">
        <RightRail :title="selectedDate ? selectedDateTitle : '选择日期'" description="点击月历中的日期查看当天安排。">
          <div v-if="selectedDayEvents.length" class="space-y-3">
            <button
              v-for="event in selectedDayEvents"
              :key="event.id"
              @click="handleEditEvent(event)"
              class="event-card w-full rounded-lg border border-[var(--border)] bg-[var(--surface-elevated)] p-3 text-left hover:border-[var(--border-focus)]"
              type="button"
            >
              <div class="flex items-start gap-3">
                <span class="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: getEventColor(event.event_type) }" />
                <div class="min-w-0">
                  <h3 class="truncate text-sm font-medium text-[var(--text)]">{{ event.title }}</h3>
                  <p v-if="event.description" class="mt-1 line-clamp-2 text-xs leading-5 text-[var(--text-muted)]">
                    {{ event.description }}
                  </p>
                  <p class="mt-2 text-xs text-[var(--text-secondary)]">
                    {{ event.is_all_day ? '全天' : formatTime(event.start_time) }}
                    <span v-if="event.location"> · {{ event.location }}</span>
                  </p>
                </div>
              </div>
            </button>
          </div>
          <div v-else class="rounded-lg border border-dashed border-[var(--border)] p-5 text-sm text-[var(--text-muted)]">
            这一天还没有事件。
          </div>

          <template #footer>
            <button
              @click="handleCreateEvent"
              class="calendar-action mt-4 w-full rounded-lg bg-[var(--text)] px-4 py-2.5 text-sm font-medium text-[var(--surface)]"
              type="button"
            >
              为这一天创建事件
            </button>
          </template>
        </RightRail>

        <RightRail
          title="事件类型"
          :sections="eventTypeSections"
        />
      </div>
    </template>

    <EventModal
      v-model="showModal"
      :event="editingEvent"
      :selected-date="selectedDate"
      @submit="handleSubmitEvent"
      @delete="handleDeleteEvent"
    />
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createEvent, deleteEvent, getEvents, updateEvent, type Event } from '@/api/events'
import AppShell from '@/components/AppShell.vue'
import EventModal from '@/components/EventModal.vue'
import RightRail from '@/components/RightRail.vue'

const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const selectedDate = ref('')
const events = ref<Event[]>([])
const showModal = ref(false)
const editingEvent = ref<Event | undefined>(undefined)

const weekDays = ['日', '一', '二', '三', '四', '五', '六']
const eventTypeSections = [
  { title: '生日', body: '家人生日、宝宝纪念日', meta: 'Birthday' },
  { title: '纪念日', body: '值得每年回看的日子', meta: 'Anniversary' },
  { title: '预约', body: '体检、课程、出行安排', meta: 'Appointment' },
]

interface CalendarDay {
  date: number
  isCurrentMonth: boolean
  isToday: boolean
  fullDate: string
  events: Event[]
}

const calendarDays = computed<CalendarDay[]>(() => {
  const year = currentYear.value
  const month = currentMonth.value
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const firstDayOfWeek = firstDay.getDay()
  const daysInMonth = lastDay.getDate()
  const days: CalendarDay[] = []
  const todayStr = toDateString(new Date())

  const prevMonthLastDay = new Date(year, month - 1, 0).getDate()
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const date = prevMonthLastDay - i
    const fullDate = toDateString(new Date(year, month - 2, date))
    days.push({ date, isCurrentMonth: false, isToday: false, fullDate, events: getEventsForDate(fullDate) })
  }

  for (let date = 1; date <= daysInMonth; date++) {
    const fullDate = toDateString(new Date(year, month - 1, date))
    days.push({
      date,
      isCurrentMonth: true,
      isToday: fullDate === todayStr,
      fullDate,
      events: getEventsForDate(fullDate),
    })
  }

  const remainingDays = 42 - days.length
  for (let date = 1; date <= remainingDays; date++) {
    const fullDate = toDateString(new Date(year, month, date))
    days.push({ date, isCurrentMonth: false, isToday: false, fullDate, events: getEventsForDate(fullDate) })
  }

  return days
})

const selectedDayEvents = computed(() => {
  if (!selectedDate.value) return []
  return getEventsForDate(selectedDate.value)
})

const selectedDateTitle = computed(() => {
  if (!selectedDate.value) return ''
  return new Date(`${selectedDate.value}T00:00:00`).toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'short',
  })
})

function getEventsForDate(dateStr: string): Event[] {
  return events.value.filter((event) => event.start_time.split('T')[0] === dateStr)
}

function getEventColor(type: string): string {
  const colors: Record<string, string> = {
    birthday: '#e36b5d',
    anniversary: '#d877a9',
    appointment: '#7ba6dd',
    holiday: '#72c99b',
    other: 'rgba(247,243,236,0.5)',
  }
  return colors[type] || colors.other
}

function eventBackground(type: string): string {
  return `${getEventColor(type)}24`
}

function formatTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function prevMonth() {
  if (currentMonth.value === 1) {
    currentYear.value--
    currentMonth.value = 12
  } else {
    currentMonth.value--
  }
  loadEvents()
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentYear.value++
    currentMonth.value = 1
  } else {
    currentMonth.value++
  }
  loadEvents()
}

function handleDayClick(day: CalendarDay) {
  if (!day.isCurrentMonth) return
  selectedDate.value = day.fullDate
}

function handleCreateEvent() {
  editingEvent.value = undefined
  showModal.value = true
}

function handleEditEvent(event: Event) {
  editingEvent.value = event
  showModal.value = true
}

async function handleSubmitEvent(data: {
  title: string
  description?: string
  start_time: string
  end_time?: string
  is_all_day: boolean
  event_type: string
  location?: string
  reminder_minutes?: number
}) {
  try {
    if (editingEvent.value) {
      await updateEvent(editingEvent.value.id, data)
    } else {
      await createEvent(data)
    }
    showModal.value = false
    await loadEvents()
  } catch (e) {
    console.error('Failed to save event:', e)
  }
}

async function handleDeleteEvent(eventId: string) {
  try {
    await deleteEvent(eventId)
    showModal.value = false
    await loadEvents()
  } catch (e) {
    console.error('Failed to delete event:', e)
  }
}

async function loadEvents() {
  try {
    const result = await getEvents(currentYear.value, currentMonth.value)
    events.value = result.events
  } catch (e) {
    console.error('Failed to load events:', e)
  }
}

function toDateString(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

onMounted(() => {
  loadEvents()
  selectedDate.value = toDateString(new Date())
})
</script>

<style scoped>
.calendar-action,
.calendar-panel,
.calendar-nav-button,
.calendar-day,
.event-pill,
.event-card {
  transition:
    background-color 170ms ease,
    border-color 170ms ease,
    box-shadow 170ms ease,
    color 170ms ease,
    opacity 170ms ease,
    transform 170ms ease;
}

.calendar-action:hover {
  box-shadow: 0 10px 26px rgba(255, 239, 222, 0.12);
  transform: translateY(-1px);
}

.calendar-panel {
  background:
    linear-gradient(180deg, rgba(255, 238, 220, 0.035), rgba(255, 238, 220, 0)),
    var(--surface-card);
}

.calendar-panel:hover {
  border-color: rgba(255, 239, 222, 0.12);
}

.calendar-nav-button:hover,
.event-card:hover {
  transform: translateY(-1px);
}

.calendar-day {
  position: relative;
}

.calendar-day::before {
  background: rgba(227, 107, 93, 0.18);
  border-radius: 999px;
  content: '';
  height: 0.2rem;
  left: 0.75rem;
  opacity: 0;
  position: absolute;
  top: 0.45rem;
  transition: opacity 170ms ease, transform 170ms ease;
  width: 1rem;
}

.calendar-day:hover::before {
  opacity: 1;
  transform: translateY(1px);
}

.calendar-day:disabled::before {
  opacity: 0;
}

.event-pill:hover {
  transform: translateX(1px);
}

.event-card:hover {
  box-shadow: 0 12px 30px rgba(143, 80, 40, 0.12);
}

@media (prefers-reduced-motion: reduce) {
  .calendar-action,
  .calendar-panel,
  .calendar-nav-button,
  .calendar-day,
  .calendar-day::before,
  .event-pill,
  .event-card {
    transition: none;
  }

  .calendar-action:hover,
  .calendar-nav-button:hover,
  .event-card:hover,
  .event-pill:hover,
  .calendar-day:hover::before {
    transform: none;
  }
}
</style>
