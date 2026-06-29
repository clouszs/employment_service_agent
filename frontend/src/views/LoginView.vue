<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(form.username, form.password)
      ElMessage.success('登录成功')
      // 登录后按角色 homeRoute 落地
      router.push(userStore.homeRoute)
    } catch {
      // 错误提示已由 axios 拦截器处理
    } finally {
      loading.value = false
    }
  })
}

// ===== 科技感粒子网络背景（纯 canvas） =====
const canvasRef = ref<HTMLCanvasElement>()
let rafId = 0
let particles: { x: number; y: number; vx: number; vy: number }[] = []
const mouse = { x: -9999, y: -9999 }

function initParticles(w: number, h: number) {
  // 粒子数随屏幕面积自适应（控制密度）
  const count = Math.min(120, Math.floor((w * h) / 12000))
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.6,
    vy: (Math.random() - 0.5) * 0.6,
  }))
}

function start() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const resize = () => {
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight
    initParticles(canvas.width, canvas.height)
  }
  resize()
  window.addEventListener('resize', resize)
  ;(canvas as HTMLCanvasElement & { _resize?: () => void })._resize = resize

  const LINK_DIST = 140
  const draw = () => {
    const w = canvas.width
    const h = canvas.height
    ctx.clearRect(0, 0, w, h)

    // 更新并绘制粒子
    for (const p of particles) {
      p.x += p.vx
      p.y += p.vy
      if (p.x < 0 || p.x > w) p.vx *= -1
      if (p.y < 0 || p.y > h) p.vy *= -1
      ctx.beginPath()
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(56, 189, 248, 0.9)'
      ctx.fill()
    }

    // 粒子间连线
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i]
        const b = particles[j]
        const dx = a.x - b.x
        const dy = a.y - b.y
        const dist = Math.hypot(dx, dy)
        if (dist < LINK_DIST) {
          ctx.beginPath()
          ctx.moveTo(a.x, a.y)
          ctx.lineTo(b.x, b.y)
          ctx.strokeStyle = `rgba(56, 189, 248, ${0.18 * (1 - dist / LINK_DIST)})`
          ctx.lineWidth = 1
          ctx.stroke()
        }
      }
    }

    // 鼠标附近粒子高亮连线（交互感）
    for (const p of particles) {
      const dx = p.x - mouse.x
      const dy = p.y - mouse.y
      const dist = Math.hypot(dx, dy)
      if (dist < 180) {
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(mouse.x, mouse.y)
        ctx.strokeStyle = `rgba(125, 211, 252, ${0.5 * (1 - dist / 180)})`
        ctx.lineWidth = 1
        ctx.stroke()
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

function onMouseLeave() {
  mouse.x = -9999
  mouse.y = -9999
}

onMounted(() => start())

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  const canvas = canvasRef.value as
    | (HTMLCanvasElement & { _resize?: () => void })
    | undefined
  if (canvas?._resize) window.removeEventListener('resize', canvas._resize)
})
</script>

<template>
  <div class="login-page" @mousemove="onMouseMove" @mouseleave="onMouseLeave">
    <canvas ref="canvasRef" class="particles"></canvas>

    <el-card class="login-card" shadow="never">
      <div class="login-header">
        <h1 class="title">高校智慧就业服务平台</h1>
        <p class="subtitle">AI问答模块 · 智能就业咨询服务</p>
      </div>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="账号 / 学工号" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="login-btn" :loading="loading" @click="onSubmit">
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  /* 深色科技感渐变底 */
  background: radial-gradient(circle at 20% 30%, #15294d 0%, #0a1128 45%, #060a1a 100%);
}

/* 粒子画布铺满 */
.particles {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

/* 玻璃拟态登录卡片 */
.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(56, 189, 248, 0.35);
  box-shadow:
    0 8px 40px rgba(0, 0, 0, 0.45),
    0 0 60px rgba(56, 189, 248, 0.15);
}
.login-card :deep(.el-card__body) {
  padding: 32px 28px;
}
.login-header {
  text-align: center;
  margin-bottom: 28px;
}
.title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px;
  color: #e0f2fe;
  letter-spacing: 1px;
  text-shadow: 0 0 18px rgba(56, 189, 248, 0.6);
}
.subtitle {
  font-size: 13px;
  color: #93b4d8;
  margin: 0;
}
.login-btn {
  width: 100%;
  background: linear-gradient(90deg, #0ea5e9, #2563eb);
  border: none;
  font-weight: 600;
  letter-spacing: 2px;
  box-shadow: 0 0 18px rgba(37, 99, 235, 0.5);
}
.login-btn:hover {
  background: linear-gradient(90deg, #38bdf8, #3b82f6);
}

/* 暗背景下输入框微调，提升可读性 */
.login-card :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.92);
}
</style>
