<script setup lang="ts">
import { computed } from 'vue'
import type { RefusalStats } from '@/types/monitor'

const props = defineProps<{
  data?: RefusalStats | null
  loading?: boolean
}>()

const data = computed(() => props.data)
const total = computed(() => data.value?.total_refusals ?? 0)
const today = computed(() => data.value?.today_refusals ?? 0)
</script>

<template>
  <el-card class="refusal-card" shadow="never" v-loading="loading">
    <template #header>
      <div class="card-head">
        <span class="card-title">拒答统计</span>
        <el-tag type="warning" effect="plain">最近</el-tag>
      </div>
    </template>

    <div v-if="data" class="refusal-body">
      <div class="refusal-hero">
        <div class="refusal-total">{{ total }}</div>
        <div class="refusal-sub">累计拒答</div>
        <div class="refusal-today">今日 {{ today }}</div>
      </div>

      <div v-if="data.by_risk_level.length" class="risk-bars">
        <div v-for="item in data.by_risk_level" :key="item.risk_level" class="risk-row">
          <span class="risk-label">{{ item.risk_level }}</span>
          <el-progress
            :percentage="total ? Math.round((item.count / total) * 100) : 0"
            :stroke-width="10"
            :show-text="false"
            :color="item.risk_level === 'high' ? '#ef4444' : item.risk_level === 'medium' ? '#f59e0b' : '#10b981'"
          />
          <span class="risk-count">{{ item.count }}</span>
        </div>
      </div>
    </div>
    <el-empty v-else description="暂无拒答数据" :image-size="40" />
  </el-card>
</template>

<style scoped>
.refusal-card {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(14px);
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-weight: 600;
}
.refusal-body {
  margin-top: 6px;
}
.refusal-hero {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 10px;
}
.refusal-total {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}
.refusal-sub {
  font-size: 12px;
  color: #475569;
}
.refusal-today {
  margin-left: auto;
  font-size: 12px;
  color: #f59e0b;
}
.risk-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.risk-row {
  display: grid;
  grid-template-columns: 60px 1fr 40px;
  align-items: center;
  gap: 10px;
}
.risk-label {
  font-size: 12px;
  color: #334155;
  text-transform: capitalize;
}
.risk-count {
  font-size: 12px;
  color: #475569;
  text-align: right;
}
</style>
