<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import * as opsApi from '@/api/ops'
import type { SensitiveWord } from '@/types/ops'

const ACTION: Record<number, { text: string; type: 'danger' | 'warning' | 'info' }> = {
  1: { text: '拦截', type: 'danger' },
  2: { text: '替换', type: 'warning' },
  3: { text: '告警', type: 'info' },
}

const loading = ref(false)
const rows = ref<SensitiveWord[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, keyword: '' })

async function load() {
  loading.value = true
  try {
    const res = await opsApi.listSensitiveWords({
      page: query.page,
      size: query.size,
      keyword: query.keyword || undefined,
    })
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
const editing = ref<SensitiveWord | null>(null)
const form = reactive({ word: '', category: '', action: 1 })

function openCreate() {
  editing.value = null
  form.word = ''
  form.category = ''
  form.action = 1
  dialogVisible.value = true
}
function openEdit(row: SensitiveWord) {
  editing.value = row
  form.word = row.word
  form.category = row.category || ''
  form.action = row.action
  dialogVisible.value = true
}
async function submit() {
  if (!form.word.trim()) return ElMessage.warning('请填写敏感词')
  try {
    if (editing.value) {
      await opsApi.updateSensitiveWord(editing.value.id, { category: form.category, action: form.action })
      ElMessage.success('已更新')
    } else {
      await opsApi.createSensitiveWord({ word: form.word, category: form.category, action: form.action })
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    load()
  } catch {
    /* 拦截器已提示（如重复词） */
  }
}
async function remove(row: SensitiveWord) {
  try {
    await ElMessageBox.confirm(`删除敏感词「${row.word}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await opsApi.deleteSensitiveWord(row.id)
  ElMessage.success('已删除')
  load()
}
</script>

<template>
  <div>
    <div class="toolbar">
      <el-input
        v-model="query.keyword"
        placeholder="搜索敏感词"
        clearable
        style="width: 220px"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-button type="primary" :icon="Refresh" @click="onSearch">查询</el-button>
      <div class="spacer" />
      <el-button type="primary" :icon="Plus" @click="openCreate">新建敏感词</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="word" label="敏感词" min-width="160" />
      <el-table-column prop="category" label="分类" width="140" />
      <el-table-column label="处理方式" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="ACTION[row.action].type" size="small">{{ ACTION[row.action].text }}</el-tag>
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

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑敏感词' : '新建敏感词'" width="420px">
      <el-form label-width="90px">
        <el-form-item label="敏感词" required>
          <el-input v-model="form.word" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="如：违规" />
        </el-form-item>
        <el-form-item label="处理方式">
          <el-select v-model="form.action" style="width: 100%">
            <el-option label="拦截" :value="1" />
            <el-option label="替换" :value="2" />
            <el-option label="告警" :value="3" />
          </el-select>
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
