<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    color?: string // 粒子/连线基色 rgb，如 "56, 189, 248"
    linkDist?: number // 连线最大距离
    density?: number // 密度系数（每多少像素一个粒子，越小越密）
    interactive?: boolean // 是否鼠标交互
  }>(),
  { color: '56, 189, 248', linkDist: 130, density: 14000, interactive: true },
)

const canvasRef = ref<HTMLCanvasElement>()
let rafId = 0
let particles: { x: number; y: number; vx: number; vy: number }[] = []
const mouse = { x: -9999, y: -9999 }
let resizeHandler: (() => void) | null = null

function initParticles(w: number, h: number) {
  const count = Math.min(120, Math.floor((w * h) / props.density))
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.5,
    vy: (Math.random() - 0.5) * 0.5,
  }))
}

function start() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  resizeHandler = () => {
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight
    initParticles(canvas.width, canvas.height)
  }
  resizeHandler()
  window.addEventListener('resize', resizeHandler)

  const draw = () => {
    const w = canvas.width
    const h = canvas.height
    ctx.clearRect(0, 0, w, h)

    for (const p of particles) {
      p.x += p.vx
      p.y += p.vy
      if (p.x < 0 || p.x > w) p.vx *= -1
      if (p.y < 0 || p.y > h) p.vy *= -1
      ctx.beginPath()
      ctx.arc(p.x, p.y, 1.6, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${props.color}, 0.85)`
      ctx.fill()
    }

    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i]
        const b = particles[j]
        const dist = Math.hypot(a.x - b.x, a.y - b.y)
        if (dist < props.linkDist) {
          ctx.beginPath()
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(b.x, b.y)
          ctx.strokeStyle = `rgba(${props.color}, ${0.16 * (1 - dist / props.linkDist)})`
          ctx.lineWidth = 1
          ctx.stroke()
        }
      }
    }

    if (props.interactive) {
      for (const p of particles) {
        const dist = Math.hypot(p.x - mouse.x, p.y - mouse.y)
        if (dist < 160) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(mouse.x, mouse.y)
          ctx.strokeStyle = `rgba(${props.color}, ${0.45 * (1 - dist / 160)})`
          ctx.lineWidth = 1
          ctx.stroke()
        }
      }
    }

    rafId = requestAnimationFrame(draw)
  }
  draw()
}

function onMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
}

onMounted(() => start())
onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<template>
  <canvas
    ref="canvasRef"
    class="particles-bg"
    @mousemove="interactive && onMouseMove($event)"
  ></canvas>
</template>

<style scoped>
.particles-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
}
</style>
