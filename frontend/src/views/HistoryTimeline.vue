<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { ScrollSmoother } from 'gsap/ScrollSmoother'

gsap.registerPlugin(ScrollTrigger, ScrollSmoother)

const root = ref<HTMLElement | null>(null)
let smoother: ScrollSmoother | undefined
let ctx: gsap.Context | undefined

function scrollToShape() {
  smoother?.scrollTo('.shape', true, 'center center')
}

onMounted(() => {
  if (!root.value) return

  ctx = gsap.context(() => {
    smoother = ScrollSmoother.create({
      smooth: 2,
      effects: true,
      normalizeScroll: true,
    })

    ScrollTrigger.create({
      trigger: '.shape',
      pin: true,
      start: 'center center',
      end: '+=300',
    })
  }, root.value)
})

onUnmounted(() => {
  ctx?.revert()
  smoother = undefined
})
</script>

<template>
  <div
    id="smooth-wrapper"
    ref="root"
  >
    <div id="smooth-content">
      <header class="header">
        <h1 class="heading-l heading-scroll">ScrollSmoother</h1>
        <button
          class="button"
          type="button"
          @click="scrollToShape"
        >
          Jump to shape
        </button>
      </header>
      <div
        class="box box-a gradient-pink"
        data-speed="clamp(0.5)"
      >
        a
      </div>
      <div
        class="box box-b gradient-purple"
        data-speed="clamp(0.8)"
      >
        b
      </div>
      <img
        class="shape"
        data-speed="1.5"
        src="https://assets.codepen.io/16327/2D-keyframe-2.png"
        alt=""
      />
      <div class="line"></div>
    </div>
  </div>
</template>
<style lang="scss" scoped>
body {
  background-color: var(--color-just-black);
  overscroll-behavior: none;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

.header {
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  padding-top: 2.5rem;
}

#smooth-content {
  overflow: visible;
  width: 100%;
  /* set a height because the contents are position: absolute, thus natively there's no height */
  height: 4000px;
  background-image: linear-gradient(
      rgba(255, 255, 255, 0.07) 2px,
      transparent 2px
    ),
    linear-gradient(90deg, rgba(255, 255, 255, 0.07) 2px, transparent 2px),
    linear-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.06) 1px, transparent 1px);
  background-size: 100px 100px, 100px 100px, 20px 20px, 20px 20px;
  background-position: -2px -2px, -2px -2px, -1px -1px, -1px -1px;
}

button {
  position: relative;
  margin-top: 1rem;
}

heading-l {
  margin-top: 2rem;
}

.box,
.shape {
  width: 100px;
  height: 100px;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  line-height: 100px;
  text-align: center;
  will-change: transform;
}
.box.active {
  outline: 2px var(--color-surface-white);
}

.box-a {
  top: 400px;
}

.box-b {
  top: 900px;
}

.shape {
  top: 1300px;
  will-change: transform;
}

.line {
  visibility: hidden;
  width: 2px;
  height: 4000px;
  position: absolute;
  left: 400px;
  top: 0px;
  background-color: #777;
}

footer {
  position: fixed;
  right: 0px;
  bottom: 0px;
  padding: 6px 10px 10px 12px;
  border-top-left-radius: 26px;
  z-index: 100;
  background-color: rgba(0, 0, 0, 0.5);
}

.end {
  position: absolute;
  /*   bottom: 0; */
  top: 2400px;
  transform: translateY(-100%);
  font-size: 30px;
  color: white;
}

</style>
