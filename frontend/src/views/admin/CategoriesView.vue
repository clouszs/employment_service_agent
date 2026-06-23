<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import * as kbApi from '@/api/knowledge'
import type { Category } from '@/types/knowledge'

const loading = ref(false)
const rows = ref<Category[]>([])
const selectedRows = ref<Category[]>([])

async function load() {
  loading.value = true
  try {
    rows.value = await kbApi.listCategories()
  } finally {
    loading.value = false
  }
}
onMounted(load)

function onSelectionChange(rows: Category[]) {
  selectedRows.value = rows
}
async function batchDelete() {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 个分类？`, '批量删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await Promise.all(selectedRows.value.map((r) => kbApi.deleteCategory(r.id).catch(() => null)))
  ElMessage.success('批量删除完成')
  load()
}

const dialogVisible = ref(false)
const editing = ref<Category | null>(null)
const form = reactive({ name: '', parent_id: 0, sort: 0 })

function openCreate() {
  editing.value = null
  form.name = ''
  form.parent_id = 0
  form.sort = 0
  dialogVisible.value = true
}
function openEdit(row: Category) {
  editing.value = row
  form.name = row.name
  form.parent_id = row.parent_id
  form.sort = row.sort
  dialogVisible.value = true
}
async function submit() {
  if (!form.name.trim()) return ElMessage.warning('请填写分类名称')
  if (editing.value) {
    await kbApi.updateCategory(editing.value.id, { ...form })
    ElMessage.success('已更新')
  } else {
    await kbApi.createCategory({ ...form })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: Category) {
  try {
    await ElMessageBox.confirm(`删除分类「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await kbApi.deleteCategory(row.id)
    ElMessage.success('已删除')
    load()
  } catch {
    /* 拦截器已提示（如存在关联文档不可删） */
  }
}
</script>

<template>
  <div>
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="openCreate">新建分类</el-button>
      <el-button type="danger" :icon="Delete" :disabled="!selectedRows.length" @click="batchDelete">
        批量删除{{ selectedRows.length ? `(${selectedRows.length})` : '' }}
      </el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe border @selection-change="onSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="分类名称" min-width="200" />
      <el-table-column prop="parent_id" label="父分类ID" width="120" align="center" />
      <el-table-column prop="sort" label="排序" width="100" align="center" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="remove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑分类' : '新建分类'" width="420px">
      <el-form label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="如：就业政策" />
        </el-form-item>
        <el-form-item label="父分类">
          <el-input-number v-model="form.parent_id" :min="0" />
          <span class="hint">0 为顶级</span>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
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
  margin-bottom: 16px;
}
.hint {
  margin-left: 10px;
  color: #9ca3af;
  font-size: 12px;
}
</style>
