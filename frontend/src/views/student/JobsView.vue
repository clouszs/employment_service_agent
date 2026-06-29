<template>
  <div class="jobs-view">
    <div class="page-header">
      <h2>职位推荐</h2>
      <p class="subtitle">基于知识库为你推荐匹配岗位</p>
    </div>

    <el-card class="search-card">
      <el-form :model="form" inline>
        <el-form-item label="关键词">
          <el-input v-model="form.query" placeholder="如：Python、产品经理、后端开发" clearable />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="form.location" placeholder="如：北京、上海（可选）" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleSearch">搜索</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <div v-loading="loading" class="results">
      <el-empty v-if="!loading && !jobs.length" description="暂无推荐结果，请先搜索" />

      <div v-for="item in jobs" :key="item.document_id || item.title" class="job-card">
        <div class="job-header">
          <h3>{{ item.title }}</h3>
          <el-tag type="info" size="small">匹配度 {{ Math.round((item.score || 0) * 100) }}%</el-tag>
        </div>
        <p class="job-snippet">{{ item.snippet }}</p>
        <div class="job-footer">
          <span class="job-source">来源：知识库</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as careerApi from '@/api/career'

const loading = ref(false)
const jobs = ref<Array<{ title: string; score: number; source: string; snippet: string; document_id?: number }>>([])

const form = reactive({
  query: '',
  top_k: 8,
  location: '',
})

async function handleSearch() {
  if (!form.query) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  loading.value = true
  try {
    const res = await careerApi.recommendJobs({
      query: form.query,
      top_k: form.top_k,
      location: form.location || undefined,
    })
    jobs.value = res.items || []
  } catch (err: any) {
    ElMessage.error(err.message || '搜索失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.jobs-view {
  max-width: 900px;
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
.search-card {
  margin-bottom: 20px;
}
.results {
  display: grid;
  gap: 16px;
}
.job-card {
  padding: 18px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}
.job-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.job-header h3 {
  margin: 0;
  font-size: 16px;
}
.job-snippet {
  margin: 0;
  color: #374151;
  line-height: 1.6;
  font-size: 14px;
}
.job-footer {
  margin-top: 12px;
  font-size: 12px;
  color: #6b7280;
}
</style>
