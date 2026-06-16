import { ref } from 'vue'

const isThemeSwitcherOpen = ref(false)

export function useThemeSwitcher() {
  const openThemeSwitcher = () => {
    isThemeSwitcherOpen.value = true
  }

  const closeThemeSwitcher = () => {
    isThemeSwitcherOpen.value = false
  }

  return {
    isThemeSwitcherOpen,
    openThemeSwitcher,
    closeThemeSwitcher,
  }
}
