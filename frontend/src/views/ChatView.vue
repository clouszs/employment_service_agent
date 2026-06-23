<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { SwitchButton, User } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import ConversationList from '@/components/chat/ConversationList.vue'
import MessageList from '@/components/chat/MessageList.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import ProfileDialog from '@/components/chat/ProfileDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()
const { user } = storeToRefs(userStore)
const { messages, loadingMessages, sending } = storeToRefs(chatStore)

const inputRef = ref<InstanceType<typeof ChatInput>>()

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
      // 401 由拦截器处理
    }
  }
  inputRef.value?.focus()
})

function onLogout() {
  userStore.logout()
  router.push('/login')
}

function onSend(text: string) {
  chatStore.send(text)
  inputRef.value?.focus()
}

const profileVisible = ref(false)
</script>

<template>
  <el-container class="chat-view">
    <el-aside width="260px" class="aside">
      <ConversationList />
    </el-aside>

    <el-container>
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
        <div v-if="messages.length === 0" class="welcome">
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
        <MessageList v-else v-loading="loadingMessages" :messages="messages" class="msg-area" />
        <ChatInput ref="inputRef" :sending="sending" @send="onSend" />
      </el-main>
    </el-container>

    <ProfileDialog v-model="profileVisible" />
  </el-container>
</template>

<style scoped>
.chat-view {
  height: 100%;
}
.aside {
  background: #fff;
  border-right: 1px solid #e5e7eb;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  font-size: 14px;
  color: #6b7280;
}
.main {
  background: #f5f7fa;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  max-width: 640px;
}
.welcome-title {
  font-size: 24px;
  color: #1f2937;
  margin: 0 0 8px;
}
.welcome-sub {
  color: #6b7280;
  margin: 0 0 28px;
}
.examples {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.example-item {
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.example-item:hover {
  border-color: #2563eb;
  color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}
</style>
