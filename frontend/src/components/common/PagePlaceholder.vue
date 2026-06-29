<script setup lang="ts">
/**
 * 统一占位页：用于尚未实现（P2 待建）或后端数据源待接入的路由，
 * 保证骨架阶段导航端到端可点。
 */
import { Tools } from '@element-plus/icons-vue'

withDefaults(
  defineProps<{
    title?: string
    description?: string
  }>(),
  {
    title: '功能建设中',
    description: '该页面将在后续阶段实现。',
  },
)
</script>

<template>
  <div class="placeholder">
    <el-icon class="ph-icon"><Tools /></el-icon>
    <h2 class="ph-title">{{ title }}</h2>
    <p class="ph-desc">{{ description }}</p>
  </div>
</template>

<style scoped>
.placeholder {
  height: 100%;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
  text-align: center;
}
.ph-icon {
  font-size: 56px;
  color: #38bdf8;
  opacity: 0.7;
}
.ph-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #475569;
}
.ph-desc {
  font-size: 14px;
  margin: 0;
}
</style>
