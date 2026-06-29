<script setup lang="ts">
import { WarningFilled } from '@element-plus/icons-vue'
</script>

<template>
  <div class="not-found">
    <el-icon class="nf-icon"><WarningFilled /></el-icon>
    <h2 class="nf-title">404</h2>
    <p class="nf-desc">页面不存在或您没有访问权限</p>
  </div>
</template>

<style scoped>
.not-found {
  height: 100%;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
}
.nf-icon {
  font-size: 56px;
  color: #38bdf8;
  opacity: 0.7;
}
.nf-title {
  font-size: 48px;
  font-weight: 700;
  margin: 0;
  color: #475569;
}
.nf-desc {
  font-size: 14px;
  margin: 0;
}
</style>
