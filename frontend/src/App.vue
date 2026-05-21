<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import IconMenu from '~icons/mdi/menu'

const router = useRouter()
const route = useRoute()
const isMenuOpen = ref(false)

const menuRoutes = computed(() =>
  router
    .getRoutes()
    .filter((item) => item.meta.visibleInMenu && item.components?.default && !item.redirect)
    .sort((left, right) => {
      const leftOrder = left.meta.menuOrder ?? Number.MAX_SAFE_INTEGER
      const rightOrder = right.meta.menuOrder ?? Number.MAX_SAFE_INTEGER

      if (leftOrder !== rightOrder) {
        return leftOrder - rightOrder
      }

      return String(left.meta.menuLabel ?? left.name ?? left.path).localeCompare(
        String(right.meta.menuLabel ?? right.name ?? right.path),
      )
    }),
)

watch(
  () => route.fullPath,
  () => {
    isMenuOpen.value = false
  },
)
</script>

<template>
  <div class="platform-shell">
    <RouterView />

    <div class="floating-menu">
      <button
        type="button"
        class="floating-menu__trigger"
        :aria-expanded="isMenuOpen"
        aria-controls="platform-floating-menu"
        aria-label="Abrir navegación"
        @click="isMenuOpen = !isMenuOpen"
      >
        <IconMenu class="floating-menu__icon" />
      </button>

      <transition name="floating-menu-panel">
        <nav
          v-if="isMenuOpen"
          id="platform-floating-menu"
          class="floating-menu__panel"
          aria-label="Navegación de la plataforma"
        >
          <RouterLink
            v-for="item in menuRoutes"
            :key="item.name ?? item.path"
            :to="{ name: item.name as string }"
            class="floating-menu__link"
            :class="{ 'floating-menu__link--active': route.name === item.name }"
          >
            {{ item.meta.menuLabel ?? item.name ?? item.path }}
          </RouterLink>
        </nav>
      </transition>
    </div>
  </div>
</template>

<style scoped lang="sass">
.platform-shell
  min-height: 100vh

.floating-menu
  position: fixed
  left: 1.5rem
  top: 1.5rem
  z-index: 1000
  display: grid
  justify-items: start
  gap: 0.9rem

.floating-menu__trigger
  width: 4rem
  height: 4rem
  border: 0
  border-radius: 1.4rem
  display: flex
  align-items: center
  justify-content: center
  padding: 0
  cursor: pointer
  background: linear-gradient(135deg, #0f172a, #1d4ed8)
  box-shadow: 0 18px 40px -18px rgba(15, 23, 42, 0.75)

.floating-menu__icon
  font-size: 1.7rem
  color: #f8fafc

.floating-menu__panel
  min-width: 15rem
  padding: 0.75rem
  display: grid
  gap: 0.45rem
  border-radius: 1.35rem
  border: 1px solid rgba(148, 163, 184, 0.22)
  background: rgba(15, 23, 42, 0.92)
  backdrop-filter: blur(16px)
  box-shadow: 0 24px 60px -28px rgba(15, 23, 42, 0.7)

.floating-menu__link
  padding: 0.85rem 1rem
  border-radius: 0.95rem
  color: #e2e8f0
  text-decoration: none
  font-weight: 600
  transition: background-color 0.2s ease, transform 0.2s ease

  &:hover
    background: rgba(59, 130, 246, 0.18)
    transform: translateX(-0.15rem)

.floating-menu__link--active
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.35), rgba(14, 165, 233, 0.28))
  color: #ffffff

.floating-menu-panel-enter-active,
.floating-menu-panel-leave-active
  transition: opacity 0.18s ease, transform 0.18s ease

.floating-menu-panel-enter-from,
.floating-menu-panel-leave-to
  opacity: 0
  transform: translateY(0.5rem) scale(0.97)

@media (max-width: 768px)
  .floating-menu
    left: 1rem
    top: 1rem

  .floating-menu__trigger
    width: 3.5rem
    height: 3.5rem

  .floating-menu__panel
    min-width: min(15rem, calc(100vw - 2rem))
</style>
