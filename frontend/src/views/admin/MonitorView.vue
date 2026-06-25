<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { storeToRefs } from 'pinia'
import { useMonitorStore } from '@/stores/monitor'
import * as monitorApi from '@/api/monitor'
import type { KbHealthLogRead, LlmCostLogRead, AgentRefusalLogRead } from '@/types/monitor'
import type { PageResult } from '@/types/api'

const monitorStore = useMonitorStore()
const { kbHealth, llmCostDaily, refusalStats, loadingHealth, loadingCost, loadingRefusal } =
  storeToRefs(monitorStore)

const activeTab = ref('health')

// 列表页
const healthHistory = ref<PageResult<KbHealthLogRead>>({ total: 0, page: 1, size: 20, items: [] })
const costHistory = ref<PageResult<LlmCostLogRead>>({ total: 0, page: 1, size: 20, items: [] })
const refusalList = ref<PageResult<AgentRefusalLogRead>>({ total: 0, page: 1, size: 20, items: [] })

async function loadAll() {
  await monitorStore.refreshDashboardCards()
  await Promise.all([loadHealthHistory(), loadCostHistory(), loadRefusalList()])
}

async function loadHealthHistory() {
  try {
    healthHistory.value = await monitorApi.getKbHealthHistory({ page: 1, size: 20 })
  } catch {
    // ignore
  }
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

async function onRefresh() {
  await loadAll()
}

onMounted(loadAll)
</script>

<template>
  <div class="monitor-view">
    <div class="monitor-header">
      <h2 class="monitor-title">监控中心</h2>
      <el-button :icon="Refresh" @click="onRefresh">刷新</el-button>
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
            <el-table :data="healthHistory.items" stripe>
              <el-table-column prop="check_date" label="检查日期" width="140" />
              <el-table-column prop="total_docs" label="总文档" width="90" align="center" />
              <el-table-column prop="current_docs" label="生效文档" width="100" align="center" />
              <el-table-column prop="warning_docs" label="即将过期" width="110" align="center" />
              <el-table-column prop="expired_docs" label="已过期" width="100" align="center" />
              <el-table-column prop="avg_freshness" label="平均新鲜度" width="120" align="center">
                <template #default="{ row }">
                  {{ row.avg_freshness != null ? (row.avg_freshness * 100).toFixed(1) + '%' : '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="health_score" label="健康度" width="110" align="center">
                <template #default="{ row }">
                  <el-tag :type="(row.health_score ?? 0) >= 80 ? 'success' : (row.health_score ?? 0) >= 60 ? 'warning' : 'danger'" effect="plain">
                    {{ row.health_score != null ? Math.round(row.health_score) : '-' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
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
  grid-template-columns: repeat(3, 1fr);
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
.list-card {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
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
@media (max-width: 1200px) {
  .summary-row {
    grid-template-columns: 1fr;
  }
}
</style>
