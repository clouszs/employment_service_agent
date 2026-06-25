<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import {
  DataLine,
  Document,
  Collection,
  ChatLineSquare,
  Connection,
  Tickets,
  Histogram,
  ChatRound,
  QuestionFilled,
  Warning,
  UserFilled,
  Key,
  SwitchButton,
  ChatLineRound,
  Monitor,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import ParticlesBg from '@/components/common/ParticlesBg.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { user, isAdmin } = storeToRefs(userStore)

const activeMenu = computed(() => route.path)

const TITLES: Record<string, string> = {
  'admin-dashboard': '概览',
  'admin-documents': '文档管理',
  'admin-categories': '分类管理',
  'admin-faqs': 'FAQ 管理',
  'admin-synonyms': '同义词管理',
  'admin-logs': '问答日志',
  'admin-feedback': '用户反馈',
  'admin-unanswered': '无答案问题',
  'admin-eval': '评测集',
  'admin-users': '用户管理',
  'admin-roles': '角色管理',
  'admin-sensitive': '敏感词管理',
  'admin-monitor': '监控中心',
}
const pageTitle = computed(() => TITLES[String(route.name)] || '管理后台')

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
  router.push('/chat')
}
function onLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="admin-layout">
    <!-- 深色科技感侧边栏 + 粒子 -->
    <el-aside width="220px" class="aside">
      <ParticlesBg color="56, 189, 248" :density="9000" :interactive="false" />
      <div class="aside-inner">
        <div class="logo">
          <span class="logo-mark">⬡</span>
          <span class="logo-text">就业问答 · 后台</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          class="menu"
          background-color="transparent"
          text-color="#a9c2e0"
          active-text-color="#7dd3fc"
          @select="go"
        >
          <el-menu-item index="/admin/dashboard">
            <el-icon><DataLine /></el-icon><span>概览</span>
          </el-menu-item>

          <el-menu-item-group title="知识库">
            <el-menu-item index="/admin/documents">
              <el-icon><Document /></el-icon><span>文档管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/categories">
              <el-icon><Collection /></el-icon><span>分类管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/faqs">
              <el-icon><ChatLineSquare /></el-icon><span>FAQ 管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/synonyms">
              <el-icon><Connection /></el-icon><span>同义词</span>
            </el-menu-item>
          </el-menu-item-group>

          <el-menu-item-group title="运营">
            <el-menu-item index="/admin/logs">
              <el-icon><Tickets /></el-icon><span>问答日志</span>
            </el-menu-item>
            <el-menu-item index="/admin/feedback">
              <el-icon><ChatRound /></el-icon><span>用户反馈</span>
            </el-menu-item>
            <el-menu-item index="/admin/unanswered">
              <el-icon><QuestionFilled /></el-icon><span>无答案问题</span>
            </el-menu-item>
            <el-menu-item index="/admin/eval">
              <el-icon><Histogram /></el-icon><span>评测集</span>
            </el-menu-item>
          </el-menu-item-group>

          <el-menu-item-group title="监控">
            <el-menu-item index="/admin/monitor">
              <el-icon><Monitor /></el-icon><span>监控中心</span>
            </el-menu-item>
          </el-menu-item-group>

          <el-menu-item-group v-if="isAdmin" title="系统">
            <el-menu-item index="/admin/users">
              <el-icon><UserFilled /></el-icon><span>用户管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/roles">
              <el-icon><Key /></el-icon><span>角色管理</span>
            </el-menu-item>
            <el-menu-item index="/admin/sensitive-words">
              <el-icon><Warning /></el-icon><span>敏感词</span>
            </el-menu-item>
          </el-menu-item-group>
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

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
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
.aside-tip {
  padding: 14px 18px;
  font-size: 12px;
  color: #5b7299;
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
</style>
