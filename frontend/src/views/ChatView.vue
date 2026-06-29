<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { User, SwitchButton, Star, Bell, CaretBottom } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { useMonitorStore } from '@/stores/monitor'
import ConversationList from '@/components/chat/ConversationList.vue'
import MessageList from '@/components/chat/MessageList.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import SearchBox from '@/components/chat/SearchBox.vue'
import DashboardPanels from '@/components/dashboard/DashboardPanels.vue'
import ProfileDialog from '@/components/chat/ProfileDialog.vue'
import * as chatApi from '@/api/chat'
import * as annApi from '@/api/announcements'
import type { ChatMessage } from '@/types/chat'
import type { AnnouncementBanner } from '@/types/announcements'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()
const monitorStore = useMonitorStore()
const { user } = storeToRefs(userStore)
const { messages, sending } = storeToRefs(chatStore)
const { refreshDashboardCards } = monitorStore

const inputRef = ref<InstanceType<typeof ChatInput>>()
const showSearch = ref(true)

const latestAnnouncement = ref<AnnouncementBanner | null>(null)
const announcementExpanded = ref(false)
const loadingAnnouncement = ref(false)

const examples = [
  '应届毕业生落户需要准备哪些材料？',
  '三方协议违约金最多是多少？',
  '毕业生档案怎么转递？',
  '报到证抬头写错了如何改派？',
]

onMounted(async () => {
  if (!user.value) {
    try {
      await userStore.loadMe()
    } catch {
      // 401 handled by interceptor
    }
  }
  if (userStore.hasAdminAccess) {
    refreshDashboardCards()
  }
  await loadLatestAnnouncement()
  inputRef.value?.focus()
})

async function loadLatestAnnouncement() {
  loadingAnnouncement.value = true
  try {
    const list = await annApi.listActiveAnnouncements()
    if (list.length > 0) {
      latestAnnouncement.value = {
        id: list[0].id,
        title: list[0].title,
        content: list[0].content,
        priority: list[0].priority,
        created_at: list[0].created_at,
      }
    }
  } catch {
    // 静默降级，不影响主功能
  } finally {
    loadingAnnouncement.value = false
  }
}

function onLogout() {
  userStore.logout()
  router.push('/login')
}

function onSend(payload: string | { text: string; mode: 'agent' | 'search' }) {
  const text = typeof payload === 'string' ? payload : payload.text
  const mode = typeof payload === 'object' ? payload.mode : 'agent'

  if (mode === 'search') {
    handlePureSearch(text)
  } else {
    chatStore.sendAgent(text)
  }
  inputRef.value?.focus()
}

async function handlePureSearch(query: string) {
  if (!query.trim() || sending.value) return

  messages.value.push({ role: 'user', content: query })
  const placeholder: ChatMessage = { role: 'assistant', content: '正在检索知识库...', streaming: true }
  messages.value.push(placeholder)
  const placeholderIndex = messages.value.length - 1
  sending.value = true

  try {
    const hits = await chatApi.search(query, 5)
    if (hits.length === 0) {
      messages.value[placeholderIndex] = {
        ...placeholder,
        content: '未在知识库中找到相关内容。',
        streaming: false,
        isNoAnswer: true,
        references: [],
        citations: [],
      }
      return
    }

    const lines = hits.map((h, i) => {
      const title = h.document_title || '未知文档'
      const snippet = (h.content || '').slice(0, 200)
      return `【${i + 1}】《${title}》\n${snippet}`
    })
    messages.value[placeholderIndex] = {
      ...placeholder,
      content: `找到 ${hits.length} 条相关结果：\n\n` + lines.join('\n\n'),
      streaming: false,
      isNoAnswer: false,
      references: hits.map((h, i) => ({
        document_id: null,
        document_title: h.document_title,
        chunk_id: null,
        content: h.content,
        score: h.score,
        rank_no: i + 1,
        page_no: h.page_no,
        source_type: 'local',
      })),
      citations: hits.map((h, i) => ({
        document_id: null,
        document_title: h.document_title,
        chunk_id: null,
        content: h.content,
        score: h.score,
        rank_no: i + 1,
        page_no: h.page_no,
        source_type: 'local',
      })),
    }
  } catch (e) {
    messages.value[placeholderIndex] = {
      ...placeholder,
      content: e instanceof Error ? e.message : '检索失败，请稍后重试。',
      isNoAnswer: true,
      isError: true,
      streaming: false,
    }
  } finally {
    sending.value = false
  }
}

function onCancel() {
  chatStore.cancelSend()
}

function onSearchResult(_result: unknown) {
  showSearch.value = false
  setTimeout(() => (showSearch.value = true), 0)
}

function goFavorites() {
  router.push('/student/conversations')
}

const profileVisible = ref(false)

const isAdminOrEditor = computed(
  () => (user.value?.roles || []).some((r) => r === 'admin' || r === 'editor'),
)
</script>

<template>
  <el-container class="chat-view">
    <!-- 左侧面板：公告 + 侧边栏快捷入口 + 会话 -->
    <el-aside width="300px" class="left-panel">
      <div class="left-inner">
        <!-- 最新公告横幅 -->
        <div v-if="latestAnnouncement && !loadingAnnouncement" class="announcement-banner">
          <div class="banner-header" @click="announcementExpanded = !announcementExpanded">
            <el-icon class="banner-icon"><Bell /></el-icon>
            <span class="banner-title">最新公告</span>
            <span class="banner-priority" :class="'priority-' + latestAnnouncement.priority">
              {{ latestAnnouncement.priority === 1 ? '高' : latestAnnouncement.priority === 2 ? '中' : '低' }}
            </span>
            <el-icon class="banner-arrow" :class="{ expanded: announcementExpanded }">
              <CaretBottom />
            </el-icon>
          </div>
          <div v-if="announcementExpanded" class="banner-body">
            <div class="banner-title-full">{{ latestAnnouncement.title }}</div>
            <div class="banner-content">{{ latestAnnouncement.content }}</div>
            <div class="banner-date">
              {{ new Date(latestAnnouncement.created_at || '').toLocaleString('zh-CN') }}
            </div>
          </div>
        </div>

        <div class="sidebar-shortcuts">
          <div class="shortcut-item" @click="goFavorites">
            <el-icon><Star /></el-icon>
            <span>我的收藏</span>
          </div>
        </div>

        <ConversationList />

        <div v-if="isAdminOrEditor" class="left-dashboard">
          <DashboardPanels @pick="onSend" />
        </div>
      </div>
    </el-aside>

    <!-- 中央面板：搜索 + 对话 -->
    <el-container class="center-panel">
      <el-header class="header">
        <span class="header-title">高校智慧就业服务平台</span>
        <div class="header-right">
          <el-button text :icon="User" @click="profileVisible = true">
            {{ user?.real_name || user?.username }}
          </el-button>
          <el-button text :icon="SwitchButton" @click="onLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="main">
        <div class="chat-scroll">
          <template v-if="messages.length === 0">
            <SearchBox
              v-if="showSearch"
              :sending="sending"
              @send="onSend"
              @searching="onSearchResult"
            />
            <div class="welcome">
              <div class="welcome-inner">
                <h2 class="welcome-title">👋 你好，我是智慧就业助手</h2>
                <p class="welcome-sub">基于高校就业知识库，为你解答政策、流程、招聘等问题</p>
                <div class="examples">
                  <div
                    v-for="(q, i) in examples"
                    :key="i"
                    class="example-item"
                    @click="onSend(q)"
                  >
                    {{ q }}
                  </div>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <MessageList :messages="messages" class="msg-area" />
            <ChatInput ref="inputRef" :sending="sending" @send="onSend" @cancel="onCancel" />
          </template>
        </div>
      </el-main>
    </el-container>

    <!-- 右侧面板：热门问题 + 监控摘要 -->
    <el-aside width="340px" class="right-panel" v-if="isAdminOrEditor">
      <div class="right-inner">
        <el-card class="right-card" shadow="never">
          <template #header>
            <div class="right-card-head">
              <span class="right-card-title">热门问题</span>
            </div>
          </template>
          <HotQuestions @pick="onSend" />
        </el-card>
      </div>
    </el-aside>

    <ProfileDialog v-model="profileVisible" />
  </el-container>
</template>


<style scoped>
.chat-view {
  height: 100%;
  background: linear-gradient(135deg, #0a0e27 0%, #111837 50%, #1a1f3a 100%);
  color: var(--text-primary);
}
.left-panel {
  background: rgba(15, 23, 42, 0.72);
  border-right: 1px solid var(--glass-border-solid);
}
.left-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.announcement-banner {
  margin: 10px;
  border-radius: 8px;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.25);
  overflow: hidden;
  flex-shrink: 0;
}
.banner-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
}
.banner-header:hover {
  background: rgba(56, 189, 248, 0.06);
}
.banner-icon {
  color: #38bdf8;
  font-size: 16px;
}
.banner-title {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  flex: 1;
}
.banner-priority {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  color: #fff;
}
.banner-priority.priority-1 {
  background: #ef4444;
}
.banner-priority.priority-2 {
  background: #f59e0b;
}
.banner-priority.priority-3 {
  background: #6b7280;
}
.banner-arrow {
  font-size: 14px;
  color: #94a3b8;
  transition: transform 0.2s;
}
.banner-arrow.expanded {
  transform: rotate(180deg);
}
.banner-body {
  padding: 0 12px 12px;
  border-top: 1px solid rgba(56, 189, 248, 0.12);
}
.banner-title-full {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 10px 0 6px;
}
.banner-content {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.7;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}
.banner-date {
  font-size: 11px;
  color: #64748b;
  margin-top: 8px;
}
.sidebar-shortcuts {
  display: flex;
  gap: 8px;
  padding: 4px 10px 8px;
  flex-shrink: 0;
}
.shortcut-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #7dd3fc;
  cursor: pointer;
  transition: background 0.15s;
  flex: 1;
  justify-content: center;
}
.shortcut-item:hover {
  background: rgba(56, 189, 248, 0.1);
}
.left-dashboard {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.center-panel {
  background: transparent;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(15, 23, 42, 0.6);
  border-bottom: 1px solid var(--glass-border-solid);
  color: var(--text-primary);
}
.header-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--accent-cyan);
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
}
.header-right .el-button {
  color: var(--text-muted);
}
.header-right .el-button:hover {
  color: var(--accent-cyan);
}
.main {
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.chat-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
}
.msg-area {
  flex: 1;
  min-height: 0;
}
.welcome {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.welcome-inner {
  text-align: center;
  max-width: 680px;
}
.welcome-title {
  font-size: 24px;
  color: var(--text-primary);
  margin: 0 0 8px;
}
.welcome-sub {
  color: var(--text-muted);
  margin: 0 0 28px;
}
.examples {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.example-item {
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--glass-border-solid);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.example-item:hover {
  border-color: var(--accent-blue);
  color: var(--accent-cyan);
  box-shadow: 0 0 24px var(--accent-glow);
  background: rgba(79, 172, 254, 0.12);
}
.right-panel {
  background: rgba(15, 23, 42, 0.6);
  border-left: 1px solid var(--glass-border-solid);
}
.right-inner {
  height: 100%;
  overflow-y: auto;
  padding: 12px;
}
.right-card {
  background: transparent;
  border: 1px solid var(--glass-border-solid);
}
.right-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.right-card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}
</style>
