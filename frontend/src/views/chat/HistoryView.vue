<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Delete, ArrowRight } from '@element-plus/icons-vue'
import * as conversationApi from '@/api/conversation'

const router = useRouter()
const loading = ref(false)
const kpi = reactive({
  total_conversations: 0,
  avg_confidence: null as number | null,
  top_source: { label: null as string | null, percent: 0 },
})
const conversations = ref<any[]>([])
const keyword = ref('')

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    const res = await conversationApi.getHistory({ keyword: keyword.value || undefined })
    Object.assign(kpi, res.kpi || {})
    conversations.value = (res.items || []).map((c: any) => ({
      ...c,
      preview: c.preview || '',
      message_count: c.message_count || 0,
      avg_confidence: c.avg_confidence ?? null,
      source_label: c.source_label || '',
      created_at: c.created_at,
      updated_at: c.updated_at,
    }))
  } catch (err: any) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function continueChat(conv: any) {
  router.push(`/student/chat?conversation_id=${conv.id}`)
}

async function deleteConv(id: number) {
  try {
    await conversationApi.deleteConversation(id)
    ElMessage.success('已删除')
    loadData()
  } catch (err: any) {
    ElMessage.error(err.message || '删除失败')
  }
}

const filteredConversations = ref<any[]>([])
function applyFilter() {
  let list = conversations.value
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter((c) => (c.title || '').toLowerCase().includes(kw) || (c.preview || '').toLowerCase().includes(kw))
  }
  filteredConversations.value = list
}

watch(keyword, applyFilter)
</script>

<template>
  <div v-loading="loading" class="history-view">
    <div class="header">
      <h2>会话历史</h2>
      <p class="desc">查看和管理你的所有对话记录</p>
    </div>

    <div class="kpi-cards">
      <div class="kpi-card">
        <div class="kpi-label">总对话数</div>
        <div class="kpi-value">{{ kpi.total_conversations || 0 }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">平均置信度</div>
        <div class="kpi-value">{{ kpi.avg_confidence ? (kpi.avg_confidence * 100).toFixed(1) : '-' }}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">高频来源</div>
        <div class="kpi-value">{{ kpi.top_source?.label || '-' }}</div>
      </div>
    </div>

    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索对话内容..." :prefix-icon="Search" style="width: 280px" clearable />
    </div>

    <div class="conv-list">
      <div v-for="conv in filteredConversations" :key="conv.id" class="conv-card">
        <div class="conv-header">
          <h3>{{ conv.title || '未命名对话' }}</h3>
          <span class="time">{{ new Date(conv.updated_at).toLocaleString() }}</span>
        </div>
        <div class="conv-meta">
          <span>消息数: {{ conv.message_count }}</span>
          <span v-if="conv.avg_confidence">置信度: {{ (conv.avg_confidence * 100).toFixed(1) }}%</span>
          <span v-if="conv.source_label">来源: {{ conv.source_label }}</span>
        </div>
        <div class="conv-actions">
          <el-button type="primary" :icon="ArrowRight" @click="continueChat(conv)">继续</el-button>
          <el-button :icon="Delete" @click="deleteConv(conv.id)">删除</el-button>
        </div>
      </div>
      <el-empty v-if="!loading && !filteredConversations.length" description="暂无会话记录" />
    </div>
  </div>
</template>

<style scoped>
.history-view {
  max-width: 1200px;
}
.header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #1e293b;
}
.desc {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}
.kpi-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin: 24px 0;
}
.kpi-card {
  padding: 20px;
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.kpi-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.conv-list {
  display: grid;
  gap: 16px;
}
.conv-card {
  padding: 20px;
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;
}
.conv-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.conv-header h3 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}
.time {
  font-size: 13px;
  color: #6b7280;
}
.conv-meta {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #6b7280;
}
.conv-actions {
  display: flex;
  gap: 8px;
}
</style>
