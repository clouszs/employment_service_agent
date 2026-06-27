<script setup lang="ts">
import { computed } from 'vue'
import { CircleCheck, Warning, CircleClose } from '@element-plus/icons-vue'

const props = defineProps<{
  confidence: number
}>()

const level = computed(() => {
  const v = props.confidence
  if (v >= 0.8) return { text: '高置信度', type: 'success' as const, icon: CircleCheck }
  if (v >= 0.5) return { text: '中置信度', type: 'warning' as const, icon: Warning }
  return { text: '低置信度', type: 'danger' as const, icon: CircleClose }
})
</script>

<template>
  <el-tag :type="level.type" size="small" effect="plain" class="badge">
    <el-icon class="badge-icon"><component :is="level.icon" /></el-icon>
    {{ level.text }}
  </el-tag>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: 999px;
  border: 1px solid rgba(79, 172, 254, 0.35);
  color: var(--text-primary);
}
.badge-icon {
  font-size: 14px;
  color: var(--accent-cyan);
}
</style>
