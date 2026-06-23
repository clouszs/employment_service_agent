<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as opsApi from '@/api/ops'
import type { QueryLog } from '@/types/ops'

const loading = ref(false)
const rows = ref<QueryLog[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, keyword: '', is_no_answer: undefined as number | undefined })

async function load() {
  loading.value = true
  try {
    const res = await opsApi.listQueryLogs({
      page: query.page,
      size: query.size,
      keyword: query.keyword || undefined,
      is_no_answer: query.is_no_answer,
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
      <el-select v-model="query.is_no_answer" placeholder="是否无答案" clearable style="width: 140px" @change="onSearch">
        <el-option label="有答案" :value="0" />
        <el-option label="无答案" :value="1" />
      </el-select>
      <el-button type="primary" :icon="Refresh" @click="onSearch">查询</el-button>
    </div>
    <el-table v-loading="loading" :data="rows" stripe border>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="question" label="问题" min-width="220" show-overflow-tooltip />
      <el-table-column prop="answer_brief" label="答案摘要" min-width="240" show-overflow-tooltip />
      <el-table-column label="命中数" prop="hit_doc_count" width="90" align="center" />
      <el-table-column label="无答案" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_no_answer === 1 ? 'info' : 'success'" size="small" effect="plain">
            {{ row.is_no_answer === 1 ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="耗时(ms)" prop="latency_ms" width="100" align="center" />
      <el-table-column label="渠道" prop="channel" width="90" align="center" />
      <el-table-column label="时间" prop="created_at" width="170" />
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
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
