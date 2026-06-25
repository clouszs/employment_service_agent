<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as statsApi from '@/api/stats'
import type { StatsOverview } from '@/types/stats'

const loading = ref(false)
const overview = ref<StatsOverview | null>(null)

onMounted(async () => {
  loading.value = true
  try {
    overview.value = await statsApi.getOverview()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="stats-overview" v-loading="loading">
    <div v-if="overview" class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ overview.total_questions }}</div>
        <div class="stat-label">累计问答</div>
      </div>
      <div class="stat-item">
        <div class="stat-value warn">{(overview.no_answer_rate * 100).toFixed(1)}%</div>
        <div class="stat-label">无答案率</div>
      </div>
      <div class="stat-item">
        <div class="stat-value success">{{ (overview.like_rate * 100).toFixed(1) }}%</div>
        <div class="stat-label">点赞率</div>
      </div>
      <div class="stat-item">
        <div class="stat-value info">{{ overview.indexed_documents }}/{{ overview.total_documents }}</div>
        <div class="stat-label">已索引/总文档</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-overview {
  padding: 4px 0;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.stat-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}
.stat-value.warn {
  color: #f59e0b;
}
.stat-value.success {
  color: #10b981;
}
.stat-value.info {
  color: #0ea5e9;
}
.stat-label {
  font-size: 12px;
  color: #475569;
  margin-top: 4px;
}
</style>
