<script setup lang="ts">
import { computed } from 'vue'
import type { KbHealthLatest } from '@/types/monitor'

const props = defineProps<{
  data?: KbHealthLatest | null
  loading?: boolean
}>()

const data = computed(() => props.data)
const isLoading = computed(() => props.loading ?? false)

const score = computed(() => data.value?.health_score ?? 0)
const color = computed(() => {
  const v = score.value
  if (v >= 80) return '#10b981'
  if (v >= 60) return '#f59e0b'
  return '#ef4444'
})
</script>

<template>
  <el-card class="kb-card" shadow="never" v-loading="isLoading">
    <template #header>
      <div class="card-head">
        <span class="card-title">知识库健康度</span>
        <el-tag :color="color" class="score-pill">{{ Math.round(score) }}</el-tag>
      </div>
    </template>

    <div v-if="data" class="kb-body">
      <div class="kb-row">
        <div class="kb-item">
          <div class="kb-label">检查日期</div>
          <div class="kb-value">{{ data.check_date }}</div>
        </div>
        <div class="kb-item">
          <div class="kb-label">即将过期</div>
          <div class="kb-value warn">{{ data.warning_count }}</div>
        </div>
        <div class="kb-item">
          <div class="kb-label">已过期</div>
          <div class="kb-value danger">{{ data.expired_count }}</div>
        </div>
        <div class="kb-item">
          <div class="kb-label">文档总数</div>
          <div class="kb-value">{{ data.total_docs }}</div>
        </div>
      </div>
    </div>
    <el-empty v-else description="暂无健康度数据" :image-size="40" />
  </el-card>
</template>

<style scoped>
.kb-card {
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
.score-pill {
  color: #0a0e27;
  border-radius: 999px;
  padding: 0 12px;
  font-weight: 700;
}
.kb-body {
  margin-top: 6px;
}
.kb-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.kb-item {
  padding: 10px;
  border-radius: 10px;
  background: rgba(79, 172, 254, 0.12);
  border: 1px solid rgba(79, 172, 254, 0.25);
}
.kb-label {
  font-size: 12px;
  color: var(--text-muted);
}
.kb-value {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  margin-top: 4px;
}
.kb-value.warn {
  color: #fbbf24;
}
.kb-value.danger {
  color: #f87171;
}
</style>
