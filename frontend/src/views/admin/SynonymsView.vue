<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Delete } from '@element-plus/icons-vue'
import * as kbApi from '@/api/knowledge'
import type { Synonym } from '@/types/knowledge'

const loading = ref(false)
const rows = ref<Synonym[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, keyword: '' })
const selectedRows = ref<Synonym[]>([])

async function load() {
  loading.value = true
  try {
    const res = await kbApi.listSynonyms({ page: query.page, size: query.size, keyword: query.keyword || undefined })
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
const editing = ref<Synonym | null>(null)
const form = reactive({ term: '', synonyms: '' })

function openCreate() {
  editing.value = null
  form.term = ''
  form.synonyms = ''
  dialogVisible.value = true
}
function openEdit(row: Synonym) {
  editing.value = row
  form.term = row.term
  form.synonyms = row.synonyms
  dialogVisible.value = true
}
async function submit() {
  if (!form.term.trim() || !form.synonyms.trim()) return ElMessage.warning('标准词和同义词必填')
  if (editing.value) {
    await kbApi.updateSynonym(editing.value.id, { term: form.term, synonyms: form.synonyms })
    ElMessage.success('已更新')
  } else {
    await kbApi.createSynonym({ term: form.term, synonyms: form.synonyms })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: Synonym) {
  try {
    await ElMessageBox.confirm(`删除同义词「${row.term}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await kbApi.deleteSynonym(row.id)
  ElMessage.success('已删除')
  load()
}

function onSelectionChange(rows: Synonym[]) {
  selectedRows.value = rows
}
async function batchDelete() {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 个同义词？`, '批量删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await Promise.all(selectedRows.value.map((r) => kbApi.deleteSynonym(r.id).catch(() => null)))
  ElMessage.success('批量删除完成')
  load()
}
</script>

<template>
  <div>
    <div class="toolbar">
      <el-input
        v-model="query.keyword"
        placeholder="按标准词搜索"
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
      <el-button type="primary" :icon="Plus" @click="openCreate">新建同义词</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe border @selection-change="onSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="term" label="标准词" width="180" />
      <el-table-column prop="synonyms" label="同义词(逗号分隔)" min-width="260" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑同义词' : '新建同义词'" width="480px">
      <el-form label-width="80px">
        <el-form-item label="标准词" required>
          <el-input v-model="form.term" placeholder="如：三方协议" />
        </el-form-item>
        <el-form-item label="同义词" required>
          <el-input v-model="form.synonyms" placeholder="逗号分隔，如：三方,就业协议书" />
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
