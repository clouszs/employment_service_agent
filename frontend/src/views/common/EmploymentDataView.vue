<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import * as statsApi from '@/api/stats'

const userStore = useUserStore()
const loading = ref(false)
const departmentFilter = ref('')
const gradeFilter = ref('')

// 判断是否为教师/管理员(可用筛选)
const canFilter = userStore.hasAdminAccess

onMounted(() => {
  loadData()
})

async function loadData() {
  loading.value = true
  try {
    const params: any = {}
    if (canFilter && departmentFilter.value) params.department = departmentFilter.value
    if (canFilter && gradeFilter.value) params.grade = gradeFilter.value

    const data = await statsApi.getEmployment(params)

    renderTrendChart(data.employment_trend)
    renderIndustryChart(data.industry_distribution)
    renderSalaryChart(data.salary_distribution)
    renderRegionChart(data.region_distribution)
  } catch (err: any) {
    ElMessage.error(err.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function renderTrendChart(data: any[]) {
  const chart = echarts.init(document.getElementById('trendChart')!)
  chart.setOption({
    title: { text: '就业率趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.year) },
    yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    series: [{ data: data.map((d) => d.rate), type: 'line', smooth: true, itemStyle: { color: '#38bdf8' } }],
  })
}

function renderIndustryChart(data: any[]) {
  const chart = echarts.init(document.getElementById('industryChart')!)
  chart.setOption({
    title: { text: '行业分布', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: '60%',
        data: data.map((d) => ({ name: d.industry, value: d.count })),
        label: { formatter: '{b}: {d}%' },
      },
    ],
  })
}

function renderSalaryChart(data: any[]) {
  const chart = echarts.init(document.getElementById('salaryChart')!)
  chart.setOption({
    title: { text: '薪资分布', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.range) },
    yAxis: { type: 'value' },
    series: [{ data: data.map((d) => d.count), type: 'bar', itemStyle: { color: '#10b981' } }],
  })
}

function renderRegionChart(data: any[]) {
  const chart = echarts.init(document.getElementById('regionChart')!)
  chart.setOption({
    title: { text: '地域分布', left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: data.map((d) => d.region) },
    series: [{ data: data.map((d) => d.count), type: 'bar', itemStyle: { color: '#f59e0b' } }],
  })
}
</script>

<template>
  <div v-loading="loading" class="employment-view">
    <div v-if="canFilter" class="filter-bar">
      <el-input v-model="departmentFilter" placeholder="院系筛选" style="width: 160px" clearable />
      <el-input v-model="gradeFilter" placeholder="年级筛选" style="width: 160px; margin-left: 12px" clearable />
      <el-button type="primary" style="margin-left: 12px" @click="loadData">查询</el-button>
    </div>

    <div class="charts-grid">
      <div id="trendChart" class="chart-box"></div>
      <div id="industryChart" class="chart-box"></div>
      <div id="salaryChart" class="chart-box"></div>
      <div id="regionChart" class="chart-box"></div>
    </div>
  </div>
</template>

<style scoped>
.employment-view {
  padding: 20px;
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
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}
</style>
