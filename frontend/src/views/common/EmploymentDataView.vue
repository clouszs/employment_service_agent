<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import * as statsApi from '@/api/stats'

const userStore = useUserStore()
const loading = ref(false)
const errorMsg = ref('')
const departmentFilter = ref('')
const gradeFilter = ref('')

// 仅管理员/教师可筛选；学生端展示统一数据
const canFilter = userStore.hasAdminAccess

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params: Record<string, string> = {}
    if (canFilter) {
      if (departmentFilter.value) params.department = departmentFilter.value
      if (gradeFilter.value) params.grade = gradeFilter.value
    }
    const data = await statsApi.getEmployment(params)
    renderTrendChart(data.employment_trend)
    renderIndustryChart(data.industry_distribution)
    renderSalaryChart(data.salary_distribution)
    renderRegionChart(data.region_distribution)
  } catch (err: any) {
    const msg = err?.message || '加载失败'
    errorMsg.value = msg
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

function renderTrendChart(data: any[]) {
  const el = document.getElementById('trendChart')
  if (!el) return
  echarts.init(el).setOption({
    title: { text: '就业率趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { top: 50, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: data.map((d) => d.year) },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{ data: data.map((d) => d.rate), type: 'line', smooth: true, itemStyle: { color: '#3b82f6' }, areaStyle: { color: 'rgba(59,130,246,0.08)' } }],
  })
}
function renderIndustryChart(data: any[]) {
  const el = document.getElementById('industryChart')
  if (!el) return
  echarts.init(el).setOption({
    title: { text: '行业分布', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '60%', data: data.map((d) => ({ name: d.industry, value: d.count })), label: { formatter: '{b}: {d}%' }, emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.2)' } } }],
  })
}
function renderSalaryChart(data: any[]) {
  const el = document.getElementById('salaryChart')
  if (!el) return
  echarts.init(el).setOption({
    title: { text: '薪资分布', left: 'center' },
    tooltip: { trigger: 'axis' },
    grid: { top: 50, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: data.map((d) => d.range) },
    yAxis: { type: 'value' },
    series: [{ data: data.map((d) => d.count), type: 'bar', itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] } }],
  })
}
function renderRegionChart(data: any[]) {
  const el = document.getElementById('regionChart')
  if (!el) return
  echarts.init(el).setOption({
    title: { text: '地域分布', left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 50, right: 20, bottom: 30, left: 80 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: data.map((d) => d.region) },
    series: [{ data: data.map((d) => d.count), type: 'bar', itemStyle: { color: '#f59e0b', borderRadius: [0, 4, 4, 0] } }],
  })
}
</script>

<template>
  <div v-loading="loading" class="employment-view">
    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-banner">
      <el-result icon="warning" :title="errorMsg">
        <template #extra>
          <el-text type="info" size="small">请联系管理员确认该账号已分配「学生」角色后再试</el-text>
          <el-button type="primary" style="margin-top: 12px" @click="loadData">重新加载</el-button>
        </template>
      </el-result>
    </div>

    <!-- 图表展示 -->
    <div v-else class="charts-grid">
      <div id="trendChart" class="chart-box" />
      <div id="industryChart" class="chart-box" />
      <div id="salaryChart" class="chart-box" />
      <div id="regionChart" class="chart-box" />
    </div>

    <!-- 管理员/教师筛选栏 -->
    <div v-if="canFilter" class="filter-bar">
      <el-input v-model="departmentFilter" placeholder="院系筛选" style="width: 160px" clearable />
      <el-input v-model="gradeFilter" placeholder="年级筛选" style="width: 160px; margin-left: 12px" clearable />
      <el-button type="primary" style="margin-left: 12px" @click="loadData">查询</el-button>
    </div>
  </div>
</template>

<style scoped>
.employment-view {
  padding: 20px;
  color: #374151;
}
.filter-bar {
  margin-bottom: 20px;
}
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}
.chart-box {
  height: 360px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  padding: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.error-banner {
  padding: 24px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #fecaca;
}
.error-banner :deep(.el-result) {
  padding: 32px 0;
}
.error-banner :deep(.el-result__title) {
  font-size: 15px;
  color: #b45309;
}
.coming-soon {
  padding: 60px 20px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
}
.coming-icon {
  font-size: 64px;
  margin-bottom: 16px;
}
</style>
