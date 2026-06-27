<script setup lang="ts">
import { Clock } from '@element-plus/icons-vue'

defineProps<{
  warnings: string[]
}>()
</script>

<template>
  <div v-if="warnings.length" class="temporal-warning">
    <div class="tw-head">
      <el-icon><Clock /></el-icon>
      <span>时效性提示</span>
    </div>
    <ul class="tw-list">
      <li v-for="(w, i) in warnings" :key="i">{{ w }}</li>
    </ul>
  </div>
</template>

<style scoped>
.temporal-warning {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(251, 191, 36, 0.14);
  border: 1px solid rgba(251, 191, 36, 0.45);
  color: var(--text-primary);
}
.tw-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-cyan);
  margin-bottom: 6px;
}
.tw-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: var(--text-secondary);
}
.tw-list li + li {
  margin-top: 2px;
}
</style>
