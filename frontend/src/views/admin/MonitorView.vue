<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Timer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { storeToRefs } from 'pinia'
import { useMonitorStore } from '@/stores/monitor'
import * as monitorApi from '@/api/monitor'
import type { KbHealthLogRead, LlmCostLogRead, AgentRefusalLogRead, LlmCostMonthlyRead } from '@/types/monitor'
import type { PageResult } from '@/types/api'

const monitorStore = useMonitorStore()
const { kbHealth, llmCostDaily, refusalStats, loadingHealth, loadingCost, loadingRefusal } =
  storeToRefs(monitorStore)

const activeTab = ref('health')

// 列表页
const healthHistory = ref<PageResult<KbHealthLogRead>>({ total: 0, page: 1, size: 20, items: [] })
const costHistory = ref<PageResult<LlmCostLogRead>>({ total: 0, page: 1, size: 20, items: [] })
const refusalList = ref<PageResult<AgentRefusalLogRead>>({ total: 0, page: 1, size: 20, items: [] })

// 月度成本
const monthlyCost = ref<LlmCostMonthlyRead | null>(null)
const loadingMonthly = ref(false)
const monthlyYear = ref(new Date().getFullYear())
const monthlyMonth = ref(new Date().getMonth() + 1)
const monthOptions = Array.from({ length: 12 }, (_, i) => ({ label: `${i + 1}月`, value: i + 1 }))
const yearOptions = Array.from({ length: 5 }, (_, i) => ({ label: `${new Date().getFullYear() - i}年`, value: new Date().getFullYear() - i }))

// 健康检查
const runningHealthCheck = ref(false)
const langsmithEnabled = ref(false)
const langsmithLoading = ref(false)
const trendChartEl = ref<HTMLElement | null>(null)

async function loadAll() {
  await monitorStore.refreshDashboardCards()
  await Promise.all([loadHealthHistory(), loadCostHistory(), loadRefusalList()])
  await nextTick()
  renderTrendChart()
}

async function loadHealthHistory() {
  try {
    healthHistory.value = await monitorApi.getKbHealthHistory({ page: 1, size: 20 })
  } catch {
    // ignore
  }
}

function renderTrendChart() {
  if (!trendChartEl.value) return
  const items = (healthHistory.value.items || []).slice().reverse()
  const labels = items.map((item) => item.check_date || '')
  const series = items.map((item) => item.health_score != null ? Number(Math.round(item.health_score)) : null)
  const xData = labels.length ? labels : ['']
  const sData = series.length ? series : [0]
  const chart = echarts.init(trendChartEl.value)
  chart.setOption({
    title: { text: '健康度趋势', left: 'center', textStyle: { fontSize: 14, color: '#334155' } },
    tooltip: { trigger: 'axis' },
    grid: { top: 40, right: 20, bottom: 24, left: 44 },
    xAxis: { type: 'category', data: xData, axisLabel: { color: '#64748b', fontSize: 11 } },
    yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}', color: '#64748b', fontSize: 11 } },
    series: [{ data: sData, type: 'line', smooth: true, symbol: 'circle', symbolSize: 6, itemStyle: { color: '#38bdf8' }, areaStyle: { color: 'rgba(56,189,248,0.12)' } }],
  })
}

async function loadCostHistory() {
  try {
    costHistory.value = await monitorApi.getLlmCostHistory({ page: 1, size: 20 })
  } catch {
    // ignore
  }
}

async function loadRefusalList() {
  try {
    refusalList.value = await monitorApi.getRefusalList({ page: 1, size: 20 })
  } catch {
    // ignore
  }
}

async function loadMonthlyCost() {
  loadingMonthly.value = true
  try {
    monthlyCost.value = await monitorApi.getLlmCostMonthly(monthlyYear.value, monthlyMonth.value)
  } catch {
    monthlyCost.value = null
  } finally {
    loadingMonthly.value = false
  }
}

async function onRunHealthCheck() {
  runningHealthCheck.value = true
  try {
    await monitorApi.runKbHealthCheck()
    // 刷新数据
    await Promise.all([monitorStore.loadKbHealthLatest(), loadHealthHistory()])
  } finally {
    runningHealthCheck.value = false
  }
}

async function onRefresh() {
  await loadAll()
  if (activeTab.value === 'cost') {
    await loadMonthlyCost()
  }
}

async function toggleLangSmith() {
  langsmithLoading.value = true
  try {
    await monitorApi.toggleLangSmith({ enabled: !langsmithEnabled.value })
    langsmithEnabled.value = !langsmithEnabled.value
    ElMessage.success(`LangSmith 已${langsmithEnabled.value ? '开启' : '关闭'}`)
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    langsmithLoading.value = false
  }
}

onMounted(() => {
  loadAll()
  loadMonthlyCost()
  langsmithEnabled.value = !!localStorage.getItem('langsmith_enabled')
})
</script>

<template>
  <div class="monitor-view">
    <div class="monitor-header">
      <h2 class="monitor-title">监控中心</h2>
      <div class="header-actions">
        <el-button v-if="activeTab === 'cost'" :icon="Timer" :loading="loadingMonthly" @click="loadMonthlyCost">
          查询月度
        </el-button>
        <el-button v-if="activeTab === 'health'" type="primary" :icon="Refresh" :loading="runningHealthCheck" @click="onRunHealthCheck">
          健康检查
        </el-button>
        <el-button :icon="Refresh" @click="onRefresh">刷新</el-button>
        <el-button :type="langsmithEnabled ? 'danger' : 'success'" :loading="langsmithLoading" @click="toggleLangSmith">
          {{ langsmithEnabled ? 'LangSmith 已开启，点击关闭' : 'LangSmith 已关闭，点击开启' }}
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="monitor-tabs">
      <el-tab-pane label="知识库健康度" name="health">
        <div class="monitor-section">
          <div class="summary-row">
            <el-card class="summary-card" shadow="never" v-loading="loadingHealth">
              <template #header>最新健康度</template>
              <div v-if="kbHealth" class="summary-grid">
                <div class="summary-item">
                  <div class="summary-label">检查日期</div>
                  <div class="summary-value">{{ kbHealth.check_date }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">健康度</div>
                  <div class="summary-value" :style="{ color: kbHealth.health_score >= 80 ? '#10b981' : kbHealth.health_score >= 60 ? '#f59e0b' : '#ef4444' }">
                    {{ Math.round(kbHealth.health_score) }}
                  </div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">即将过期</div>
                  <div class="summary-value warn">{{ kbHealth.warning_count }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">已过期</div>
                  <div class="summary-value danger">{{ kbHealth.expired_count }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">文档总数</div>
                  <div class="summary-value">{{ kbHealth.total_docs }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">生效文档</div>
                  <div class="summary-value">{{ kbHealth.current_docs }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" :image-size="40" />
            </el-card>
          </div>

          <el-card class="list-card" shadow="never">
            <template #header>
              <div class="list-head">
                <span class="list-title">历史记录</span>
              </div>
            </template>
            <div class="table-chart-row">
              <el-table :data="healthHistory.items" stripe table-layout="auto" class="health-table">
                <el-table-column prop="check_date" label="检查日期" min-width="120" />
                <el-table-column prop="total_docs" label="总文档" min-width="80" align="center" />
                <el-table-column prop="current_docs" label="生效文档" min-width="90" align="center" />
                <el-table-column prop="warning_docs" label="即将过期" min-width="100" align="center" />
                <el-table-column prop="expired_docs" label="已过期" min-width="90" align="center" />
                <el-table-column prop="avg_freshness" label="平均新鲜度" min-width="100" align="center">
                  <template #default="{ row }">
                    {{ row.avg_freshness != null ? (row.avg_freshness * 100).toFixed(1) + '%' : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="health_score" label="健康度" min-width="90" align="center">
                  <template #default="{ row }">
                    <el-tag :type="(row.health_score ?? 0) >= 80 ? 'success' : (row.health_score ?? 0) >= 60 ? 'warning' : 'danger'" effect="plain">
                      {{ row.health_score != null ? Math.round(row.health_score) : '-' }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
              <div ref="trendChartEl" class="trend-chart" />
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="LLM 成本" name="cost">
        <div class="monitor-section">
          <div class="summary-row">
            <el-card class="summary-card" shadow="never" v-loading="loadingCost">
              <template #header>今日成本</template>
              <div v-if="llmCostDaily" class="summary-grid">
                <div class="summary-item">
                  <div class="summary-label">统计日期</div>
                  <div class="summary-value">{{ llmCostDaily.stat_date }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">总成本</div>
                  <div class="summary-value">${{ llmCostDaily.total_cost_usd.toFixed(4) }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">总调用</div>
                  <div class="summary-value">{{ llmCostDaily.total_calls }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">总 Token</div>
                  <div class="summary-value">{{ (llmCostDaily.total_tokens_in + llmCostDaily.total_tokens_out).toLocaleString() }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" :image-size="40" />
            </el-card>

            <el-card class="summary-card" shadow="never" v-loading="loadingMonthly">
              <template #header>
                <div class="list-head">
                  <span class="list-title">月度成本</span>
                  <div class="month-picker">
                    <el-select v-model="monthlyYear" size="small" style="width: 100px">
                      <el-option v-for="y in yearOptions" :key="y.value" :label="y.label" :value="y.value" />
                    </el-select>
                    <el-select v-model="monthlyMonth" size="small" style="width: 80px">
                      <el-option v-for="m in monthOptions" :key="m.value" :label="m.label" :value="m.value" />
                    </el-select>
                  </div>
                </div>
              </template>
              <div v-if="monthlyCost" class="summary-grid">
                <div class="summary-item">
                  <div class="summary-label">统计月份</div>
                  <div class="summary-value">{{ monthlyCost.year }}-{{ String(monthlyCost.month).padStart(2, '0') }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">总成本</div>
                  <div class="summary-value">${{ monthlyCost.total_cost_usd.toFixed(4) }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">模型数</div>
                  <div class="summary-value">{{ monthlyCost.models?.length || 0 }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" :image-size="40" />
            </el-card>
          </div>

          <el-card class="list-card" shadow="never">
            <template #header>
              <div class="list-head">
                <span class="list-title">成本历史</span>
              </div>
            </template>
            <el-table :data="costHistory.items" stripe>
              <el-table-column prop="stat_date" label="日期" width="140" />
              <el-table-column prop="model" label="模型" />
              <el-table-column prop="call_count" label="调用次数" width="110" align="center" />
              <el-table-column prop="tokens_in" label="输入 Token" width="120" align="center" />
              <el-table-column prop="tokens_out" label="输出 Token" width="120" align="center" />
              <el-table-column prop="cost_usd" label="成本 (USD)" width="130" align="right">
                <template #default="{ row }">${{ row.cost_usd.toFixed(4) }}</template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="拒答记录" name="refusal">
        <div class="monitor-section">
          <div class="summary-row">
            <el-card class="summary-card" shadow="never" v-loading="loadingRefusal">
              <template #header>拒答统计</template>
              <div v-if="refusalStats" class="summary-grid">
                <div class="summary-item">
                  <div class="summary-label">累计拒答</div>
                  <div class="summary-value">{{ refusalStats.total_refusals }}</div>
                </div>
                <div class="summary-item">
                  <div class="summary-label">今日拒答</div>
                  <div class="summary-value warn">{{ refusalStats.today_refusals }}</div>
                </div>
                <div class="summary-item" v-if="refusalStats.by_reason.length">
                  <div class="summary-label">主要原因</div>
                  <div class="summary-value small">{{ refusalStats.by_reason[0].reason }}</div>
                </div>
              </div>
              <el-empty v-else description="暂无数据" :image-size="40" />
            </el-card>
          </div>

          <el-card class="list-card" shadow="never">
            <template #header>
              <div class="list-head">
                <span class="list-title">拒答列表</span>
              </div>
            </template>
            <el-table :data="refusalList.items" stripe>
              <el-table-column prop="query" label="问题" show-overflow-tooltip />
              <el-table-column prop="refusal_reason" label="拒答原因" show-overflow-tooltip />
              <el-table-column prop="confidence" label="置信度" width="110" align="center">
                <template #default="{ row }">{{ row.confidence != null ? row.confidence.toFixed(2) : '-' }}</template>
              </el-table-column>
              <el-table-column prop="query_risk_level" label="风险等级" width="110" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.query_risk_level === 'high' ? 'danger' : row.query_risk_level === 'medium' ? 'warning' : 'success'" effect="plain">
                    {{ row.query_risk_level }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="170" />
            </el-table>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.monitor-view {
  padding: 4px;
}
.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.monitor-title {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}
.monitor-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.summary-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.summary-card {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
}
.summary-card :deep(.el-card__header) {
  padding: 10px 14px;
  font-weight: 600;
  color: #334155;
}
.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.summary-item {
  padding: 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.8);
}
.summary-label {
  font-size: 12px;
  color: #475569;
}
.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin-top: 4px;
}
.summary-value.warn {
  color: #f59e0b;
}
.summary-value.danger {
  color: #ef4444;
}
.summary-value.small {
  font-size: 13px;
  font-weight: 600;
}
.month-picker {
  display: flex;
  gap: 6px;
}
.list-card {
  border-radius: 14px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.list-card :deep(.el-card__body) {
  background: #ffffff;
}
.list-card :deep(.el-table) {
  background: #ffffff;
}
.list-card :deep(.el-table__body-wrapper) {
  background: #ffffff;
}
.list-card :deep(.el-table__header-wrapper) {
  background: #f8fafc;
}
.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.list-title {
  font-weight: 600;
  color: #334155;
}
.table-chart-row {
  display: flex;
  gap: 16px;
  align-items: stretch;
}
.health-table {
  flex: 1 1 auto;
}
.trend-chart {
  width: 380px;
  min-width: 320px;
  height: 100%;
  min-height: 220px;
  background: #ffffff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  padding: 10px;
}
@media (max-width: 1200px) {
  .table-chart-row {
    flex-direction: column;
  }
  .trend-chart {
    width: 100%;
    min-width: unset;
  }
  .summary-row {
    grid-template-columns: 1fr;
  }
}
</style>
