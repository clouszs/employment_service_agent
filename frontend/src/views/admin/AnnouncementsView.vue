<template>
  <div class="announcements-page">
    <div class="page-header">
      <h2>公告管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate()">新建公告</el-button>
    </div>

    <el-card class="filter-card" shadow="never">
      <el-form :inline="true" :model="query" class="filter-form">
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="标题搜索" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 130px">
            <el-option label="草稿" :value="0" />
            <el-option label="发布" :value="1" />
            <el-option label="撤下" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="onSearch">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="rows" :loading="loading" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="优先级" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)" size="small">
            {{ priorityLabel(row.priority) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="过期时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.expire_at) }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            v-if="row.status !== 1"
            size="small"
            text
            type="success"
            @click="toggleStatus(row, 1)"
          >
            发布
          </el-button>
          <el-button v-if="row.status === 1" size="small" text type="warning" @click="toggleStatus(row, 2)">
            撤下
          </el-button>
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

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑公告' : '新建公告'" width="580px">
      <el-form :model="form" label-width="80px" :rules="rules" ref="formRef">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="公告标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="6" placeholder="公告内容（支持纯文本）" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio :label="1">高</el-radio>
            <el-radio :label="2">中</el-radio>
            <el-radio :label="3">低</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="form.expire_at"
            type="datetime"
            placeholder="可选"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item v-if="editing" label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :label="0">草稿</el-radio>
            <el-radio :label="1">发布</el-radio>
            <el-radio :label="2">撤下</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import * as annApi from '@/api/announcements'
import type { AnnouncementItem } from '@/types/announcements'

const loading = ref(false)
const rows = ref<AnnouncementItem[]>([])
const total = ref(0)
const dialogVisible = ref(false)
const editing = ref<AnnouncementItem | null>(null)
const submitting = ref(false)
const formRef = ref()
const query = reactive({ page: 1, size: 10, keyword: '', status: undefined as number | undefined })
const form = reactive({
  title: '',
  content: '',
  priority: 2,
  expire_at: '',
  status: 0,
})

const rules = {
  title: [{ required: true, message: '标题必填', trigger: 'blur' }],
  content: [{ required: true, message: '内容必填', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: query.page, size: query.size }
    if (query.keyword) params.keyword = query.keyword
    if (query.status !== undefined) params.status = query.status
    const res = await annApi.adminListAnnouncements(params)
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

function openCreate() {
  editing.value = null
  Object.assign(form, { title: '', content: '', priority: 2, expire_at: '', status: 0 })
  dialogVisible.value = true
}
function openEdit(row: AnnouncementItem) {
  editing.value = row
  Object.assign(form, {
    title: row.title,
    content: row.content,
    priority: row.priority,
    expire_at: row.expire_at || '',
    status: row.status,
  })
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const payload = {
      title: form.title,
      content: form.content,
      priority: form.priority,
      expire_at: form.expire_at || null,
      status: editing.value ? form.status : undefined,
    }
    if (editing.value) {
      await annApi.updateAnnouncement(editing.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await annApi.createAnnouncement(payload)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(row: AnnouncementItem, newStatus: number) {
  try {
    await annApi.updateAnnouncement(row.id, { status: newStatus })
    row.status = newStatus
    ElMessage.success(newStatus === 1 ? '已发布' : '已撤下')
  } catch {
    ElMessage.error('操作失败')
  }
}

async function onRemove(row: AnnouncementItem) {
  try {
    await ElMessageBox.confirm(`删除公告「${row.title}」？`, '提示', { type: 'warning' })
    await annApi.deleteAnnouncement(row.id)
    rows.value = rows.value.filter((r) => r.id !== row.id)
    ElMessage.success('已删除')
  } catch {
    /* cancelled */
  }
}

function priorityType(p: number) {
  return p === 1 ? 'danger' : p === 2 ? 'warning' : 'info'
}
function priorityLabel(p: number) {
  return p === 1 ? '高' : p === 2 ? '中' : '低'
}
function statusType(s: number) {
  return s === 1 ? 'success' : s === 0 ? 'info' : 'danger'
}
function statusLabel(s: number) {
  return s === 1 ? '发布' : s === 0 ? '草稿' : '撤下'
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
.announcements-page {
  max-width: 960px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #1f2937;
}
.filter-card {
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}
.filter-form :deep(.el-form-item__label) {
  color: #374151;
}
.filter-form :deep(.el-input__wrapper) {
  background: #ffffff;
  box-shadow: none;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
