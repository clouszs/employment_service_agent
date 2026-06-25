<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { User, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import { useMonitorStore } from '@/stores/monitor'
import ConversationList from '@/components/chat/ConversationList.vue'
import MessageList from '@/components/chat/MessageList.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import SearchBox from '@/components/chat/SearchBox.vue'
import DashboardPanels from '@/components/dashboard/DashboardPanels.vue'
import ProfileDialog from '@/components/chat/ProfileDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()
const monitorStore = useMonitorStore()
const { user } = storeToRefs(userStore)
const { messages, sending } = storeToRefs(chatStore)
const { refreshDashboardCards } = monitorStore

const inputRef = ref<InstanceType<typeof ChatInput>>()
const showSearch = ref(true)

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
  refreshDashboardCards()
  inputRef.value?.focus()
})

function onLogout() {
  userStore.logout()
  router.push('/login')
}

function onSend(text: string) {
  chatStore.sendAgent(text)
  inputRef.value?.focus()
}

function onSearchResult(_result: unknown) {
  showSearch.value = false
  setTimeout(() => (showSearch.value = true), 0)
}

const profileVisible = ref(false)

const isAdminOrEditor = computed(
  () => (user.value?.roles || []).some((r) => r === 'admin' || r === 'editor'),
)
</script>

<template>
  <el-container class="chat-view">
    <!-- 左侧面板：会话 + 统计 -->
    <el-aside width="300px" class="left-panel">
      <div class="left-inner">
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
            <ChatInput ref="inputRef" :sending="sending" @send="onSend" />
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
  background: linear-gradient(135deg, #0a0e27 0%, #1a1f4e 60%, #0b1026 100%);
  color: #e0f2fe;
}
.left-panel {
  background: rgba(15, 23, 42, 0.55);
  border-right: 1px solid rgba(56, 189, 248, 0.18);
}
.left-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
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
  background: rgba(15, 23, 42, 0.4);
  border-bottom: 1px solid rgba(56, 189, 248, 0.18);
  color: #e0f2fe;
}
.header-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
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
  color: #e0f2fe;
  margin: 0 0 8px;
}
.welcome-sub {
  color: #a9c2e0;
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
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 10px;
  font-size: 14px;
  color: #e0f2fe;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.example-item:hover {
  border-color: #38bdf8;
  color: #38bdf8;
  box-shadow: 0 0 24px rgba(56, 189, 248, 0.15);
}
.right-panel {
  background: rgba(15, 23, 42, 0.55);
  border-left: 1px solid rgba(56, 189, 248, 0.18);
}
.right-inner {
  height: 100%;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.right-card {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
}
.right-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.right-card-title {
  font-weight: 600;
  color: #0f172a;
}
</style>
