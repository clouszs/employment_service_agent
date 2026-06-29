<template>
  <div class="conversations-view">
    <div class="page-header">
      <h2>对话监控</h2>
      <p class="subtitle">查看学生对话记录与质量分析</p>
    </div>

    <el-card class="list-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索对话/用户..." clearable style="width: 260px" @input="onSearch" />
        <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px" @change="onSearch">
          <el-option label="正常" :value="1" />
          <el-option label="已删除" :value="0" />
        </el-select>
      </div>

      <el-table :data="rows" stripe @row-click="openDetail" style="margin-top:16px">
        <el-table-column label="会话" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="conv-title">{{ row.title || '未命名会话' }}</div>
            <div class="conv-meta">用户：{{ row.username }}</div>
          </template>
        </el-table-column>
        <el-table-column label="最新消息" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">{{ row.last_message || '-' }}</template>
        </el-table-column>
        <el-table-column label="消息数" width="90" align="center">
          <template #default="{ row }">{{ row.message_count || '-' }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="load"
          @size-change="load"
        />
      </div>
    </el-card>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="会话详情" size="720px" direction="rtl">
      <div v-if="detail" class="detail">
        <div class="detail-header">
          <div>
            <div class="detail-title">{{ detail.title || '未命名会话' }}</div>
            <div class="detail-meta">用户：{{ detail.username }} | 消息数：{{ detail.message_count || '-' }}</div>
          </div>
        </div>
        <el-divider />
        <div class="messages">
          <div v-for="msg in detail.messages || []" :key="msg.id" class="msg" :class="msg.role === 1 ? 'msg-user' : 'msg-bot'">
            <div class="msg-role">{{ msg.role === 1 ? '学生' : '系统' }}</div>
            <div class="msg-content">{{ msg.content }}</div>
            <div class="msg-time">{{ formatDate(msg.created_at) }}</div>
          </div>
          <el-empty v-if="!detail.messages?.length" description="暂无消息" :image-size="60" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as conversationsApi from '@/api/conversations'
import type { AdminConversationItem } from '@/api/conversations'

const loading = ref(false)
const rows = ref<AdminConversationItem[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const keyword = ref('')
const statusFilter = ref<number | ''>('')

const drawerVisible = ref(false)
const detail = ref<any>(null)

async function load() {
  loading.value = true
  try {
    const res = await conversationsApi.adminListConversations({
      page: page.value,
      size: size.value,
      keyword: keyword.value || undefined,
      status: typeof statusFilter.value === 'number' ? statusFilter.value : undefined,
    })
    rows.value = res.items
    total.value = res.total
  } catch (err: any) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}
function onSearch() {
  page.value = 1
  load()
}

async function openDetail(row: AdminConversationItem) {
  try {
    const res = await conversationsApi.adminGetConversation(row.id)
    detail.value = res
    drawerVisible.value = true
  } catch (err: any) {
    ElMessage.error(err.message || '加载详情失败')
  }
}

function formatDate(iso: string | null) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

onMounted(load)
</script>

<style scoped>
.conversations-view {
  max-width: 1200px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 22px;
}
.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
}
.toolbar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
.conv-title {
  font-weight: 600;
  font-size: 14px;
}
.conv-meta {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detail-title {
  font-size: 18px;
  font-weight: 700;
}
.detail-meta {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}
.messages {
  display: grid;
  gap: 12px;
}
.msg {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.msg-user {
  background: #eff6ff;
  border-color: #bfdbfe;
}
.msg-bot {
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.msg-role {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}
.msg-content {
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.msg-time {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 6px;
}
</style>
