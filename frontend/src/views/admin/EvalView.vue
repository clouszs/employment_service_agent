<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, VideoPlay, Delete } from '@element-plus/icons-vue'
import * as opsApi from '@/api/ops'
import type { EvalCase, EvalRunResult } from '@/types/ops'

const loading = ref(false)
const rows = ref<EvalCase[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10 })
const selectedRows = ref<EvalCase[]>([])

async function load() {
  loading.value = true
  try {
    const res = await opsApi.listEvalCases({ page: query.page, size: query.size })
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}
onMounted(load)

// 新建/编辑
const dialogVisible = ref(false)
const editing = ref<EvalCase | null>(null)
const form = reactive({ question: '', expected_answer: '', expected_doc_id: undefined as number | undefined, category: '' })
function openCreate() {
  editing.value = null
  Object.assign(form, { question: '', expected_answer: '', expected_doc_id: undefined, category: '' })
  dialogVisible.value = true
}
function openEdit(row: EvalCase) {
  editing.value = row
  Object.assign(form, {
    question: row.question,
    expected_answer: row.expected_answer || '',
    expected_doc_id: row.expected_doc_id ?? undefined,
    category: row.category || '',
  })
  dialogVisible.value = true
}
async function submit() {
  if (!form.question.trim()) return ElMessage.warning('请填写评测问题')
  if (editing.value) {
    await opsApi.updateEvalCase(editing.value.id, { ...form })
    ElMessage.success('已更新')
  } else {
    await opsApi.createEvalCase({ ...form })
    ElMessage.success('已创建')
  }
  dialogVisible.value = false
  load()
}
async function remove(row: EvalCase) {
  try {
    await ElMessageBox.confirm('删除该评测用例？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await opsApi.deleteEvalCase(row.id)
  ElMessage.success('已删除')
  load()
}

function onSelectionChange(rows: EvalCase[]) {
  selectedRows.value = rows
}
async function batchDelete() {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedRows.value.length} 个评测用例？`, '批量删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  await Promise.all(selectedRows.value.map((r) => opsApi.deleteEvalCase(r.id).catch(() => null)))
  ElMessage.success('批量删除完成')
  load()
}

// 执行评测
const running = ref(false)
const result = ref<EvalRunResult | null>(null)
const resultVisible = ref(false)
async function run() {
  running.value = true
  try {
    result.value = await opsApi.runEval({ top_k: 5 })
    resultVisible.value = true
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div>
    <div class="toolbar">
      <el-button type="success" :icon="VideoPlay" :loading="running" @click="run">一键评测</el-button>
      <el-button :icon="Refresh" @click="load">刷新</el-button>
      <div class="spacer" />
      <el-button type="danger" :icon="Delete" :disabled="!selectedRows.length" @click="batchDelete">
        批量删除{{ selectedRows.length ? `(${selectedRows.length})` : '' }}
      </el-button>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建用例</el-button>
    </div>

    <el-alert
      v-if="result"
      class="result-bar"
      :title="`最近评测：命中率 ${(result.hit_rate * 100).toFixed(1)}%（命中 ${result.hit_count}/${result.evaluated}，跳过 ${result.skipped}）`"
      type="success"
      :closable="false"
      show-icon
    />

    <el-table v-loading="loading" :data="rows" stripe border @selection-change="onSelectionChange">
      <el-table-column type="selection" width="50" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="question" label="评测问题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="expected_answer" label="参考答案" min-width="200" show-overflow-tooltip />
      <el-table-column prop="expected_doc_id" label="期望文档ID" width="110" align="center" />
      <el-table-column prop="category" label="类别" width="120" />
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
        @size-change="load"
      />
    </div>

    <!-- 新建/编辑 -->
    <el-dialog v-model="dialogVisible" :title="editing ? '编辑用例' : '新建用例'" width="520px">
      <el-form label-width="90px">
        <el-form-item label="评测问题" required>
          <el-input v-model="form.question" placeholder="问题" />
        </el-form-item>
        <el-form-item label="参考答案">
          <el-input v-model="form.expected_answer" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="期望文档ID">
          <el-input-number v-model="form.expected_doc_id" :min="1" />
          <span class="hint">检索命中此文档算命中</span>
        </el-form-item>
        <el-form-item label="类别">
          <el-input v-model="form.category" placeholder="如：落户政策" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 评测结果明细 -->
    <el-dialog v-model="resultVisible" title="评测结果明细" width="640px">
      <div v-if="result" class="result-summary">
        命中率 <b>{{ (result.hit_rate * 100).toFixed(1) }}%</b> ｜ 命中 {{ result.hit_count }}/{{ result.evaluated }} ｜
        跳过 {{ result.skipped }} ｜ 总数 {{ result.total }}
      </div>
      <el-table :data="result?.details || []" stripe max-height="420">
        <el-table-column prop="question" label="问题" min-width="200" show-overflow-tooltip />
        <el-table-column label="命中" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.hit ? 'success' : 'danger'" size="small">{{ row.hit ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hit_rank" label="命中排名" width="90" align="center" />
        <el-table-column prop="top_score" label="最高分" width="90" align="center" />
      </el-table>
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
.result-bar {
  margin-bottom: 16px;
}
.result-summary {
  margin-bottom: 12px;
  font-size: 14px;
  color: #374151;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.hint {
  margin-left: 10px;
  color: #9ca3af;
  font-size: 12px;
}
</style>
