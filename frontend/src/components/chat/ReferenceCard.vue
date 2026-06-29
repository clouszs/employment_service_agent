<script setup lang="ts">
import { ref, computed } from 'vue'
import { Document, Link, ArrowDown, ArrowRight } from '@element-plus/icons-vue'
import type { Reference } from '@/types/chat'

const props = defineProps<{ references: Reference[] }>()

const expanded = ref(false)

const hasWeb = computed(() => props.references.some((r) => r.source_type === 'web'))
const localRefs = computed(() => props.references.filter((r) => r.source_type !== 'web'))
const webRefs = computed(() => props.references.filter((r) => r.source_type === 'web'))
const hasMore = computed(() => props.references.length > 3)

function toggle() {
  expanded.value = !expanded.value
}

function formatDate(iso: string | null | undefined) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return ''
  }
}
</script>

<template>
  <div v-if="references.length" class="ref-card">
    <div class="ref-head" @click="toggle">
      <el-icon><Document /></el-icon>
      <span>参考来源（{{ references.length }}）</span>
      <el-tag v-if="hasWeb" type="warning" size="small" effect="plain">含外部检索</el-tag>
      <el-icon v-if="hasMore" class="toggle-icon" :class="{ expanded }">
        <ArrowDown v-if="!expanded" />
        <ArrowRight v-else />
      </el-icon>
    </div>

    <template v-if="expanded || !hasMore">
      <!-- 本地知识库来源 -->
      <template v-if="localRefs.length">
        <div v-for="(r, i) in localRefs" :key="'local-' + i" class="ref-item">
          <div class="ref-title">
            <span class="rank">[{{ r.rank_no || i + 1 }}]</span>
            <span class="doc">《{{ r.document_title || '未知文档' }}》</span>
            <span v-if="r.page_no" class="meta">第{{ r.page_no }}页</span>
            <span v-if="r.score != null" class="meta">相似度 {{ r.score }}</span>
          </div>
          <div v-if="r.snippet" class="ref-snippet">{{ r.snippet }}</div>
        </div>
      </template>

      <!-- 外部检索来源 -->
      <template v-if="webRefs.length">
        <div v-for="(r, i) in webRefs" :key="'web-' + i" class="ref-item ref-item-web">
          <div class="ref-title">
            <span class="rank web-rank">[{{ r.rank_no || i + 1 }}]</span>
            <span class="doc">{{ r.document_title || '外部文章' }}</span>
            <el-tag v-if="r.source" size="small" effect="plain" type="info">{{ r.source }}</el-tag>
            <span v-if="r.published_at" class="meta">{{ formatDate(r.published_at) }}</span>
          </div>
          <div v-if="r.snippet" class="ref-snippet">{{ r.snippet }}</div>
          <a
            v-if="r.url"
            :href="r.url"
            target="_blank"
            rel="noopener noreferrer"
            class="ref-link"
          >
            <el-icon><Link /></el-icon>
            <span>查看原文</span>
          </a>
        </div>
      </template>
    </template>

    <div v-if="hasMore && !expanded" class="ref-more" @click="toggle">
      还有 {{ references.length - 3 }} 条参考来源，点击展开
    </div>
  </div>
</template>

<style scoped>
.ref-card {
  margin-top: 8px;
  border: 1px solid var(--glass-border-solid);
  border-radius: 8px;
  background: var(--glass-bg);
  overflow: hidden;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: var(--text-primary);
}
.ref-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-cyan);
  background: rgba(79, 172, 254, 0.12);
}
.ref-item {
  padding: 8px 12px;
  border-top: 1px solid rgba(79, 172, 254, 0.18);
}
.ref-item-web {
  background: rgba(79, 172, 254, 0.08);
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
  color: var(--accent-blue);
  font-weight: 600;
}
.web-rank {
  color: #fbbf24;
}
.doc {
  color: #ffffff;
  font-weight: 500;
}
.meta {
  font-size: 12px;
  color: var(--text-muted);
}
.ref-snippet {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(79, 172, 254, 0.25);
  border-radius: 6px;
  padding: 6px 8px;
}
.ref-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--accent-cyan);
  text-decoration: none;
  transition: color 0.2s;
}
.ref-link:hover {
  color: var(--accent-blue);
}
.toggle-icon {
  margin-left: auto;
  font-size: 14px;
  color: var(--text-muted);
  transition: transform 0.2s;
}
.toggle-icon.expanded {
  transform: rotate(90deg);
}
.ref-more {
  padding: 8px 12px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  border-top: 1px solid rgba(79, 172, 254, 0.18);
  transition: color 0.2s;
}
.ref-more:hover {
  color: var(--accent-cyan);
}
</style>
