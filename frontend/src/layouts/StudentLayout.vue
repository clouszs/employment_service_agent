<script setup lang="ts">
/**
 * 学生端布局：左侧栏导航 + 内容区（参考 conversations.html 设计稿）
 * 侧栏分 3 组：对话 / 工具 / 设置
 */
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ChatDotRound, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { STUDENT_MENU } from '@/config/menus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { user } = storeToRefs(userStore)

const activeMenu = computed(() => route.path)

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
function onLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="student-layout">
    <el-aside width="240px" class="sidebar">
      <div class="brand">
        <span class="logo-mark">⬡</span>
        <span class="logo-text">智慧就业</span>
      </div>

      <el-button type="primary" class="new-chat-btn" :icon="ChatDotRound" @click="go('/student/chat')">
        新建对话
      </el-button>

      <el-scrollbar class="menu-scrollbar">
        <div v-for="group in STUDENT_MENU" :key="group.title" class="menu-group">
          <div v-if="group.title" class="group-title">{{ group.title }}</div>
          <div
            v-for="item in group.items"
            :key="item.path"
            class="menu-item"
            :class="{ active: activeMenu === item.path }"
            @click="go(item.path)"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </el-scrollbar>

      <div class="user-block">
        <div class="user-info">
          <div class="username">{{ user?.real_name || user?.username }}</div>
          <div class="user-role">学生</div>
        </div>
        <el-button text :icon="SwitchButton" class="logout-btn" @click="onLogout">退出</el-button>
      </div>
    </el-aside>

    <el-main class="main light-content">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.student-layout {
  height: 100%;
  background: #f5f7fa;
}
.sidebar {
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0d1b34 0%, #0a1226 100%);
  border-right: 1px solid rgba(56, 189, 248, 0.18);
  padding: 20px 16px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  color: #e0f2fe;
}
.logo-mark {
  font-size: 24px;
  color: #38bdf8;
  text-shadow: 0 0 12px rgba(56, 189, 248, 0.8);
}
.logo-text {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
}
.new-chat-btn {
  width: 100%;
  margin-bottom: 20px;
}
.menu-scrollbar {
  flex: 1;
  margin-bottom: 16px;
}
.menu-group {
  margin-bottom: 24px;
}
.group-title {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
  padding: 0 8px;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 2px;
  color: #a9c2e0;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}
.menu-item:hover {
  background: rgba(56, 189, 248, 0.1);
  color: #7dd3fc;
}
.menu-item.active {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  font-weight: 600;
}
.user-block {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(56, 189, 248, 0.15);
}
.user-info {
  flex: 1;
}
.username {
  font-size: 14px;
  color: #e0f2fe;
  font-weight: 600;
  margin-bottom: 2px;
}
.user-role {
  font-size: 12px;
  color: #64748b;
}
.logout-btn {
  color: #a9c2e0;
}
.logout-btn:hover {
  color: #7dd3fc;
}
.main {
  padding: 24px;
  overflow-y: auto;
}
</style>
