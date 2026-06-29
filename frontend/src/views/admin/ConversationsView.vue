<template>
  <div class="conversations-page">
    <div class="page-header">
      <h2>对话管理</h2>
      <p class="subtitle">查看和管理全站用户对话（仅展示最近消息摘要）</p>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="query" class="filter-form">
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="标题 / 用户名" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 130px">
            <el-option label="正常" :value="1" />
            <el-option label="已删除" :value="0" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="onSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="rows" :loading="loading" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="用户" width="140">
        <template #default="{ row }">
          {{ row.username || '匿名' }}
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="最近消息摘要" min-width="260" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="snippet-text">{{ row.last_message || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? '正常' : '已删除' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openDetail(row)">详情</el-button>
          <el-button size="small" text type="danger" @click="onRemove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrap">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="load"
        @size-change="load"
      />
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="detailTitle" width="720px">
      <div v-if="detailMessages.length === 0" class="empty-detail">暂无消息</div>
      <div v-else class="message-list">
        <div v-for="msg in detailMessages" :key="msg.id" class="message-item">
          <div class="message-meta">
            <el-tag :type="msg.role === 1 ? 'primary' : 'success'" size="small">
              {{ msg.role === 1 ? '用户' : '助手' }}
            </el-tag>
            <span class="message-time">{{ formatDate(msg.created_at) }}</span>
          </div>
          <div class="message-content">{{ msg.content }}</div>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import * as convApi from '@/api/conversations'
import type { AdminConversationItem } from '@/api/conversations'
import type { Message } from '@/types/chat'

const loading = ref(false)
const rows = ref<AdminConversationItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, keyword: '', status: undefined as number | undefined })

const detailVisible = ref(false)
const detailTitle = ref('')
const detailMessages = ref<Message[]>([])

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, size: query.size }
    if (query.keyword) params.keyword = query.keyword
    if (query.status !== undefined) params.status = query.status
    const res = await convApi.adminListConversations(params)
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}
function onSearch() {
  query.page = 1
  load()
}
function resetQuery() {
  query.keyword = ''
  query.status = undefined
  query.page = 1
  load()
}

async function openDetail(row: AdminConversationItem) {
  detailTitle.value = `会话 #${row.id} — ${row.username || '匿名'}`
  try {
    const res = await convApi.adminGetConversation(row.id)
    detailMessages.value = res.messages || []
  } catch {
    ElMessage.error('加载会话详情失败')
  }
  detailVisible.value = true
}

async function onRemove(row: AdminConversationItem) {
  try {
    await ElMessageBox.confirm(`强制删除会话 #${row.id}？该操作不可恢复。`, '警告', { type: 'warning' })
    await convApi.adminDeleteConversation(row.id)
    rows.value = rows.value.filter((r) => r.id !== row.id)
    total.value = Math.max(0, total.value - 1)
    ElMessage.success('已删除')
  } catch {
    /* cancelled */
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
.conversations-page {
  max-width: 1100px;
}
.page-header {
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
  color: #1f2937;
}
.subtitle {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}
.filter-card {
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}
.filter-form :deep(.el-form-item__label) {
  color: #6b7280;
}
.filter-form :deep(.el-input__wrapper) {
  background: #f9fafb;
  box-shadow: none;
}
.snippet-text {
  color: #6b7280;
  font-size: 13px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.empty-detail {
  text-align: center;
  color: #6b7280;
  padding: 40px 0;
}
.message-list {
  max-height: 500px;
  overflow-y: auto;
}
.message-item {
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}
.message-item:last-child {
  border-bottom: none;
}
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.message-time {
  font-size: 12px;
  color: #6b7280;
}
.message-content {
  color: #1f2937;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
