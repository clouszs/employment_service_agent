<script setup lang="ts">
import { Document } from '@element-plus/icons-vue'
import type { Reference } from '@/types/chat'

defineProps<{ references: Reference[] }>()
</script>

<template>
  <div v-if="references.length" class="ref-card">
    <div class="ref-head">
      <el-icon><Document /></el-icon>
      <span>参考来源（{{ references.length }}）</span>
    </div>
    <div v-for="(r, i) in references" :key="i" class="ref-item">
      <div class="ref-title">
        <span class="rank">[{{ r.rank_no || i + 1 }}]</span>
        <span class="doc">《{{ r.document_title || '未知文档' }}》</span>
        <span v-if="r.page_no" class="meta">第{{ r.page_no }}页</span>
        <span v-if="r.score != null" class="meta">相似度 {{ r.score }}</span>
      </div>
      <div v-if="r.snippet" class="ref-snippet">{{ r.snippet }}</div>
    </div>
  </div>
</template>

<style scoped>
.ref-card {
  margin-top: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
  overflow: hidden;
}
.ref-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  background: #f1f5f9;
}
.ref-item {
  padding: 8px 12px;
  border-top: 1px solid #eef2f7;
}
.ref-title {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 13px;
  margin-bottom: 4px;
}
.rank {
  color: #2563eb;
  font-weight: 600;
}
.doc {
  color: #334155;
  font-weight: 500;
}
.meta {
  font-size: 12px;
  color: #94a3b8;
}
.ref-snippet {
  font-size: 12px;
  line-height: 1.6;
  color: #64748b;
  white-space: pre-wrap;
  background: #fff;
  border: 1px solid #eef2f7;
  border-radius: 6px;
  padding: 6px 8px;
}
</style>
