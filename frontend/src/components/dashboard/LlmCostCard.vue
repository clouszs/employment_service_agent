<script setup lang="ts">
import { computed } from 'vue'
import type { LlmCostDailyRead } from '@/types/monitor'

const props = defineProps<{
  data?: LlmCostDailyRead | null
  loading?: boolean
}>()

const data = computed(() => props.data)
const total = computed(() => data.value?.total_cost_usd ?? 0)
const calls = computed(() => data.value?.total_calls ?? 0)
</script>

<template>
  <el-card class="cost-card" shadow="never" v-loading="loading">
    <template #header>
      <div class="card-head">
        <span class="card-title">LLM 成本</span>
        <el-tag type="info" effect="plain">今日</el-tag>
      </div>
    </template>

    <div v-if="data" class="cost-body">
      <div class="cost-hero">
        <div class="cost-amount">$ {{ total.toFixed(4) }}</div>
        <div class="cost-calls">调用 {{ calls }} 次</div>
      </div>

      <div v-if="data.models.length" class="model-bars">
        <div v-for="m in data.models" :key="m.model" class="model-row">
          <div class="model-name">{{ m.model }}</div>
          <el-progress
            :percentage="total ? Math.round((m.cost_usd / total) * 100) : 0"
            :stroke-width="10"
            :show-text="false"
          />
          <div class="model-meta">
            <span>${{ m.cost_usd.toFixed(4) }}</span>
            <span class="muted">{{ m.call_count }} 次</span>
          </div>
        </div>
      </div>
    </div>
    <el-empty v-else description="暂无成本数据" :image-size="40" />
  </el-card>
</template>

<style scoped>
.cost-card {
  border-radius: 14px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border-solid);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: var(--text-primary);
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-weight: 600;
  color: var(--accent-cyan);
}
.cost-body {
  margin-top: 6px;
}
.cost-hero {
  margin-bottom: 10px;
}
.cost-amount {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
}
.cost-calls {
  font-size: 12px;
  color: var(--text-muted);
}
.model-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.model-row {
  display: grid;
  grid-template-columns: 110px 1fr auto;
  align-items: center;
  gap: 10px;
}
.model-name {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.model-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 12px;
  color: var(--text-muted);
  min-width: 80px;
}
.muted {
  color: var(--text-muted);
}
</style>
