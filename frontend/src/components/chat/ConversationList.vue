<script setup lang="ts">
import { onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ChatDotRound, Delete } from '@element-plus/icons-vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const { conversations, currentId, loadingList } = storeToRefs(chatStore)

onMounted(() => {
  chatStore.loadConversations()
})

function onNew() {
  chatStore.startNewConversation()
}

function onSelect(id: number) {
  if (id === currentId.value) return
  chatStore.selectConversation(id)
}

async function onDelete(id: number, e: Event) {
  e.stopPropagation()
  try {
    await ElMessageBox.confirm('确定删除该会话？', '提示', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await chatStore.removeConversation(id)
  ElMessage.success('已删除')
}
</script>

<template>
  <div class="conv-list">
    <el-button type="primary" class="new-btn" :icon="Plus" @click="onNew">新建会话</el-button>

    <div v-loading="loadingList" class="conv-items">
      <div
        v-for="c in conversations"
        :key="c.id"
        class="conv-item"
        :class="{ active: c.id === currentId }"
        @click="onSelect(c.id)"
      >
        <el-icon class="conv-icon"><ChatDotRound /></el-icon>
        <span class="conv-title">{{ c.title || '未命名会话' }}</span>
        <el-icon class="conv-del" @click="onDelete(c.id, $event)"><Delete /></el-icon>
      </div>

      <el-empty
        v-if="!loadingList && conversations.length === 0"
        description="暂无会话"
        :image-size="60"
      />
    </div>
  </div>
</template>

<style scoped>
.conv-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
}
.new-btn {
  width: 100%;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #4facfe, #00d4ff);
  border: none;
  color: #0a0e27;
  font-weight: 600;
}
.conv-items {
  flex: 1;
  overflow-y: auto;
}
.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 10px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: background 0.15s;
}
.conv-item:hover {
  background: rgba(79, 172, 254, 0.12);
}
.conv-item.active {
  background: linear-gradient(135deg, rgba(79, 172, 254, 0.32), rgba(0, 212, 255, 0.32));
  color: #ffffff;
  border: 1px solid rgba(79, 172, 254, 0.4);
}
.conv-icon {
  flex-shrink: 0;
  color: var(--accent-cyan);
}
.conv-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
  color: var(--text-secondary);
}
.conv-item.active .conv-title {
  color: #ffffff;
}
.conv-del {
  flex-shrink: 0;
  opacity: 0;
  color: var(--text-muted);
  transition: opacity 0.15s;
}
.conv-item:hover .conv-del {
  opacity: 1;
}
.conv-del:hover {
  color: #f87171;
}
</style>
