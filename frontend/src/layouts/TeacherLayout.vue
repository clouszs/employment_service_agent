<script setup lang="ts">
/**
 * 教师工作台布局：左侧分组侧边栏（克隆管理端样式），内容聚焦内容维护。
 * 教师 = editor 角色；可访问数据看板 / FAQ管理 / 对话监控 / 就业数据 / 个人资料。
 */
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { SwitchButton, ChatLineRound } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { TEACHER_MENU } from '@/config/menus'
import ParticlesBg from '@/components/common/ParticlesBg.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => {
  for (const g of TEACHER_MENU) {
    const hit = g.items.find((it) => it.path === route.path)
    if (hit) return hit.label
  }
  return '教师工作台'
})

onMounted(async () => {
  if (!user.value) {
    try {
      await userStore.loadMe()
    } catch {
      /* 守卫已处理 */
    }
  }
})

function go(path: string) {
  if (path !== route.path) router.push(path)
}
function toChat() {
  router.push('/student/chat')
}
function onLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="teacher-layout">
    <el-aside width="220px" class="aside">
      <ParticlesBg color="56, 189, 248" :density="9000" :interactive="false" />
      <div class="aside-inner">
        <div class="logo">
          <span class="logo-mark">⬡</span>
          <span class="logo-text">就业问答 · 教师</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="menu"
          background-color="transparent"
          text-color="#a9c2e0"
          active-text-color="#7dd3fc"
          @select="go"
        >
          <template v-for="group in TEACHER_MENU" :key="group.title || 'root'">
            <el-menu-item-group v-if="group.title" :title="group.title">
              <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
                <el-icon><component :is="item.icon" /></el-icon><span>{{ item.label }}</span>
              </el-menu-item>
            </el-menu-item-group>
            <template v-else>
              <el-menu-item v-for="item in group.items" :key="item.path" :index="item.path">
                <el-icon><component :is="item.icon" /></el-icon><span>{{ item.label }}</span>
              </el-menu-item>
            </template>
          </template>
        </el-menu>
      </div>
    </el-aside>

    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="header-right">
          <el-button text class="link-btn" :icon="ChatLineRound" @click="toChat">问答端</el-button>
          <span class="username">{{ user?.real_name || user?.username }}</span>
          <el-tag size="small" effect="dark" type="info">{{ (user?.roles || []).join('/') }}</el-tag>
          <el-button text class="link-btn" :icon="SwitchButton" @click="onLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="main light-content">
        <div class="content-wrapper">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.teacher-layout {
  height: 100%;
}
.aside {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #0d1b34 0%, #0a1226 100%);
  border-right: 1px solid rgba(56, 189, 248, 0.18);
}
.aside-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 18px;
  color: #e0f2fe;
}
.logo-mark {
  font-size: 22px;
  color: #38bdf8;
  text-shadow: 0 0 12px rgba(56, 189, 248, 0.8);
}
.logo-text {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
}
.menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}
.menu :deep(.el-menu-item-group__title) {
  color: #5b7299;
  font-size: 12px;
  padding-left: 18px;
}
.menu :deep(.el-menu-item.is-active) {
  background: rgba(56, 189, 248, 0.12);
  border-right: 2px solid #38bdf8;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #0d1b34;
  border-bottom: 1px solid rgba(56, 189, 248, 0.18);
  color: #e0f2fe;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #e0f2fe;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  font-size: 14px;
  color: #a9c2e0;
}
.link-btn {
  color: #a9c2e0;
}
.link-btn:hover {
  color: #7dd3fc;
}
.main {
  background: #f5f7fa;
  padding: 20px;
}
.main.light-content {
  background: #f5f7fa;
}
.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
