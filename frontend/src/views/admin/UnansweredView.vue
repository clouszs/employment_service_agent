<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import * as opsApi from '@/api/ops'
import type { UnansweredQuestion } from '@/types/ops'

const loading = ref(false)
const rows = ref<UnansweredQuestion[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, status: undefined as number | undefined, keyword: '' })

async function load() {
  loading.value = true
  try {
    const res = await opsApi.listUnanswered({
      page: query.page,
      size: query.size,
      status: query.status,
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

// 标记处理
const dialogVisible = ref(false)
const editing = ref<UnansweredQuestion | null>(null)
const form = reactive({ status: 2, resolve_note: '' })

function openResolve(row: UnansweredQuestion) {
  editing.value = row
  form.status = 2 // 默认置为已解决
  form.resolve_note = row.resolve_note || ''
  dialogVisible.value = true
}
async function submit() {
  if (!editing.value) return
  await opsApi.resolveUnanswered(editing.value.id, form.status, form.resolve_note || undefined)
  ElMessage.success('已更新')
  dialogVisible.value = false
  load()
}

async function remove(row: UnansweredQuestion) {
  try {
    await ElMessageBox.confirm('删除该无答案问题记录？', '提示', { type: 'warning' })
  } catch {
    return
  }
  await opsApi.deleteUnanswered(row.id)
  ElMessage.success('已删除')
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
        style="width: 220px"
        @keyup.enter="onSearch"
        @clear="onSearch"
      />
      <el-select v-model="query.status" placeholder="处理状态" clearable style="width: 140px" @change="onSearch">
        <el-option label="未解决" :value="1" />
        <el-option label="已解决" :value="2" />
      </el-select>
      <el-button type="primary" :icon="Refresh" @click="onSearch">查询</el-button>
    </div>

    <el-alert
      class="tip"
      title="这里汇总用户提问但系统未找到答案的问题（相同问题已合并计数）。可据此往知识库补充文档或新增 FAQ，处理后标记“已解决”并说明。"
      type="info"
      :closable="false"
      show-icon
    />

    <el-table v-loading="loading" :data="rows" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="question" label="未答问题" min-width="240" show-overflow-tooltip />
      <el-table-column label="出现次数" width="100" align="center">
        <template #default="{ row }">
          <el-tag type="warning" effect="plain">{{ row.ask_count }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="最近提问" prop="last_asked_at" width="170" />
      <el-table-column label="状态" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.status === 2 ? 'success' : 'danger'" size="small">
            {{ row.status === 2 ? '已解决' : '未解决' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="处理说明" prop="resolve_note" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openResolve(row)">标记</el-button>
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

    <!-- 标记处理弹窗 -->
    <el-dialog v-model="dialogVisible" title="标记处理" width="460px">
      <div v-if="editing" class="q-text">问题：{{ editing.question }}</div>
      <el-form label-width="80px">
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="2">已解决</el-radio>
            <el-radio :value="1">未解决</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="说明">
          <el-input
            v-model="form.resolve_note"
            type="textarea"
            :rows="3"
            placeholder="如：已补充XX文档 / 已新增FAQ / 该问题超出服务范围"
          />
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
  gap: 12px;
  margin-bottom: 12px;
}
.tip {
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.q-text {
  margin-bottom: 14px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  color: #374151;
  font-size: 14px;
}
</style>
