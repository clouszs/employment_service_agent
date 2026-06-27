<script setup lang="ts">
import { InfoFilled } from '@element-plus/icons-vue'

defineProps<{
  isNoAnswer: boolean
  reason?: string | null
  route?: string
}>()
</script>

<template>
  <div v-if="isNoAnswer" class="refusal">
    <div class="refusal-head">
      <el-icon><InfoFilled /></el-icon>
      <span>未找到合适答案</span>
    </div>
    <div class="refusal-body">
      <p v-if="reason">{{ reason }}</p>
      <p v-else>当前知识库暂未覆盖该问题，请联系就业中心老师或换个问法试试。</p>
      <div v-if="route" class="route-tag">路由：{{ route }}</div>
    </div>
  </div>
</template>

<style scoped>
.refusal {
  margin-top: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(79, 172, 254, 0.12);
  border: 1px solid rgba(79, 172, 254, 0.35);
  color: var(--text-primary);
}
.refusal-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-cyan);
  margin-bottom: 6px;
}
.refusal-body {
  font-size: 13px;
  color: var(--text-secondary);
}
.refusal-body p {
  margin: 0 0 6px;
}
.route-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(79, 172, 254, 0.14);
  font-size: 12px;
  color: var(--accent-blue);
}
</style>
