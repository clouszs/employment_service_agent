<template>
  <div class="faqs-view">
    <div class="page-header">
      <h2>FAQ 管理</h2>
      <p class="subtitle">维护知识库问答对，支持新增、编辑、启禁和删除</p>
    </div>

    <el-card class="toolbar-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索问题..." clearable style="width: 260px" @input="onSearch" />
        <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px" @change="onSearch">
          <el-option label="已启用" :value="1" />
          <el-option label="已禁用" :value="0" />
        </el-select>
        <el-button type="primary" @click="openCreate">新增 FAQ</el-button>
        <el-button :disabled="!selected.length" @click="handleBatch('enable')">批量启用</el-button>
        <el-button :disabled="!selected.length" @click="handleBatch('disable')">批量禁用</el-button>
        <el-button :disabled="!selected.length" type="danger" plain @click="handleBatch('delete')">批量删除</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="rows" stripe @selection-change="onSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column label="问题" min-width="320" show-overflow-tooltip>
          <template #default="{ row }">{{ row.question }}</template>
        </el-table-column>
        <el-table-column label="答案" min-width="400" show-overflow-tooltip>
          <template #default="{ row }">{{ row.answer }}</template>
        </el-table-column>
        <el-table-column label="命中" width="90" align="center">
          <template #default="{ row }">
            <el-tag type="warning" effect="plain">{{ row.hit_count }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="170">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="success" plain @click="toggleStatus(row)">
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(row)">删除</el-button>
          </template>
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

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑 FAQ' : '新增 FAQ'" width="720px" @closed="resetForm">
      <el-form :model="form" label-width="90px">
        <el-form-item label="问题" required>
          <el-input v-model="form.question" placeholder="标准问题" clearable />
        </el-form-item>
        <el-form-item label="答案" required>
          <el-input v-model="form.answer" type="textarea" :rows="5" placeholder="标准答案" clearable />
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
import * as faqApi from '@/api/faqs'
import type { FaqItem } from '@/api/faqs'

const loading = ref(false)
const rows = ref<FaqItem[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)
const keyword = ref('')
const statusFilter = ref<number | ''>('')
const selected = ref<number[]>([])

const dialogVisible = ref(false)
const editing = ref(false)
const submitting = ref(false)
const form = reactive({ id: 0 as number | null, question: '', answer: '' })

async function load() {
  loading.value = true
  try {
    const res = await faqApi.listFaqs({
      page: page.value,
      size: size.value,
      keyword: keyword.value || undefined,
      status: typeof statusFilter.value === 'number' ? statusFilter.value : undefined,
    })
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}
function onSearch() {
  page.value = 1
  load()
}
function onSelectionChange(val: FaqItem[]) {
  selected.value = val.map((v) => v.id)
}

function openCreate() {
  editing.value = false
  form.id = null
  form.question = ''
  form.answer = ''
  dialogVisible.value = true
}
function openEdit(row: FaqItem) {
  editing.value = true
  form.id = row.id
  form.question = row.question
  form.answer = row.answer
  dialogVisible.value = true
}
function resetForm() {
  editing.value = false
  form.id = null
  form.question = ''
  form.answer = ''
}

async function submit() {
  if (!form.question.trim() || !form.answer.trim()) {
    ElMessage.warning('请填写完整')
    return
  }
  submitting.value = true
  try {
    if (editing.value && form.id) {
      await faqApi.updateFaq(form.id, { question: form.question, answer: form.answer })
      ElMessage.success('更新成功')
    } else {
      await faqApi.createFaq({ question: form.question, answer: form.answer })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    load()
  } catch (err: any) {
    ElMessage.error(err.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(row: FaqItem) {
  try {
    await faqApi.setFaqStatus(row.id, { status: row.status === 1 ? 0 : 1 })
    ElMessage.success('状态已更新')
    load()
  } catch (err: any) {
    ElMessage.error(err.message || '操作失败')
  }
}
async function handleDelete(row: FaqItem) {
  try {
    await ElMessageBox.confirm('删除该 FAQ？', '提示', { type: 'warning' })
    await faqApi.deleteFaq(row.id)
    ElMessage.success('已删除')
    load()
  } catch {
    /* cancelled */
  }
}
async function handleBatch(action: 'enable' | 'disable' | 'delete') {
  if (!selected.value.length) return
  const label = action === 'enable' ? '启用' : action === 'disable' ? '禁用' : '删除'
  try {
    await ElMessageBox.confirm(`确认${label}选中的 ${selected.value.length} 条 FAQ？`, '提示', { type: 'warning' })
    await faqApi.batchFaqs({ action, ids: selected.value })
    ElMessage.success('批量操作完成')
    selected.value = []
    load()
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
.faqs-view {
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
.toolbar-card {
  margin-bottom: 16px;
}
.toolbar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
