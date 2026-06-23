<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Delete } from '@element-plus/icons-vue'
import * as kbApi from '@/api/knowledge'
import type { Faq } from '@/types/knowledge'

const loading = ref(false)
const rows = ref<Faq[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, keyword: '' })
const selectedRows = ref<Faq[]>([])

async function load() {
  loading.value = true
  try {
    const res = await kbApi.listFaqs({ page: query.page, size: query.size, keyword: query.keyword || undefined })
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
onMounted(load)

const dialogVisible = ref(false)
const editing = ref<Faq | null>(null)
const form = reactive({ question: '', answer: '' })

function openCreate() {
  editing.value = null
  form.question = ''
  form.answer = ''
  dialogVisible.value = true
}
function openEdit(row: Faq) {
  editing.value = row
  form.question = row.question
  form.answer = row.answer
  dialogVisible.value = true
}
async function submit() {
  if (!form.question.trim() || !form.answer.trim()) return ElMessage.warning('问题和答案必填')
  if (editing.value) {
    await kbApi.updateFaq(editing.value.id, { question: form.question, answer: form.answer })
    ElMessage.success('已更新（已自动重建向量）')
  } else {
    await kbApi.createFaq({ question: form.question, answer: form.answer })
    ElMessage.success('已创建（已自动向量化入库）')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: Faq) {
  try {
    await ElMessageBox.confirm('删除该 FAQ？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await kbApi.deleteFaq(row.id)
  ElMessage.success('已删除')
  load()
}

function onSelectionChange(rows: Faq[]) {
  selectedRows.value = rows
}
async function batchDelete() {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 条 FAQ？`, '批量删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await Promise.all(selectedRows.value.map((r) => kbApi.deleteFaq(r.id).catch(() => null)))
  ElMessage.success('批量删除完成')
  load()
}
</script>

<template>
  <div>
    <div class="toolbar">
      <el-input
        v-model="query.keyword"
        placeholder="按问题搜索"
        clearable
        style="width: 240px"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-button type="primary" :icon="Refresh" @click="onSearch">查询</el-button>
      <div class="spacer" />
      <el-button type="danger" :icon="Delete" :disabled="!selectedRows.length" @click="batchDelete">
        批量删除{{ selectedRows.length ? `(${selectedRows.length})` : '' }}
      </el-button>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建 FAQ</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe border @selection-change="onSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="question" label="问题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="answer" label="答案" min-width="240" show-overflow-tooltip />
      <el-table-column prop="hit_count" label="命中" width="90" align="center">
        <template #default="{ row }">
          <el-tag type="warning" effect="plain">{{ row.hit_count }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pager">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="load"
        @size-change="onSearch"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑 FAQ' : '新建 FAQ'" width="560px">
      <el-form label-width="60px">
        <el-form-item label="问题" required>
          <el-input v-model="form.question" placeholder="标准问题" />
        </el-form-item>
        <el-form-item label="答案" required>
          <el-input v-model="form.answer" type="textarea" :rows="4" placeholder="标准答案" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.spacer {
  flex: 1;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
