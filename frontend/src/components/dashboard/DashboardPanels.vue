<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { ArrowRight } from '@element-plus/icons-vue'
import { useMonitorStore } from '@/stores/monitor'
import KbHealthCard from './KbHealthCard.vue'
import LlmCostCard from './LlmCostCard.vue'
import RefusalStatsCard from './RefusalStatsCard.vue'
import StatsOverview from './StatsOverview.vue'
import HotQuestions from './HotQuestions.vue'

const emit = defineEmits<{ pick: [question: string] }>()

const monitorStore = useMonitorStore()
const { kbHealth, llmCostDaily, refusalStats, loadingHealth, loadingCost, loadingRefusal } =
  storeToRefs(monitorStore)

function openMonitor() {
  window.open('/admin/monitor', '_blank')
}
</script>

<template>
  <div class="dashboard-panels">
    <StatsOverview />

    <div class="panels-row">
      <KbHealthCard :data="kbHealth" :loading="loadingHealth" class="panel" />
      <LlmCostCard :data="llmCostDaily" :loading="loadingCost" class="panel" />
      <RefusalStatsCard :data="refusalStats" :loading="loadingRefusal" class="panel" />
    </div>

    <el-card class="hot-card-wrap" shadow="never">
      <template #header>
        <div class="hot-header">
          <span class="hot-title">热门问题</span>
          <el-button text type="primary" :icon="ArrowRight" @click="openMonitor">监控中心</el-button>
        </div>
      </template>
      <HotQuestions @pick="emit('pick', $event)" />
    </el-card>
  </div>
</template>

<style scoped>
.dashboard-panels {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.panels-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.panel {
  min-height: 120px;
}
.hot-card-wrap {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(16px);
}
.hot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hot-title {
  font-weight: 600;
}
@media (max-width: 1200px) {
  .panels-row {
    grid-template-columns: 1fr;
  }
}
</style>
