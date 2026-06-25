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
  background: #fff7ed;
  border: 1px solid #fdba74;
}
.tw-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #c2410c;
  margin-bottom: 6px;
}
.tw-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #9a3412;
}
.tw-list li + li {
  margin-top: 2px;
}
</style>
