<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as faqApi from '@/api/faqs'
import type { FaqItem } from '@/api/faqs'

const loading = ref(false)
const list = ref<FaqItem[]>([])

const emit = defineEmits<{ pick: [question: string] }>()

onMounted(async () => {
  loading.value = true
  try {
    list.value = await faqApi.getTopFaqs(20)
  } finally {
    loading.value = false
  }
})

function onPick(q: string) {
  emit('pick', q)
}
</script>

<template>
  <el-card class="hot-card" shadow="never" v-loading="loading">
    <template #header>
      <div class="hot-head">
        <span class="hot-title">🔥 热门问题</span>
      </div>
    </template>

    <div v-if="list.length" class="hot-list">
      <div
        v-for="(item, idx) in list"
        :key="item.id"
        class="hot-item"
        @click="onPick(item.question)"
      >
        <span class="rank">{{ idx + 1 }}</span>
        <span class="q">{{ item.question }}</span>
        <el-tag v-if="item.ask_count > 0" type="warning" effect="plain" size="small">{{ item.ask_count }}</el-tag>
        <span v-else class="zero">0</span>
      </div>
    </div>
    <el-empty v-else description="暂无数据" :image-size="48" />
  </el-card>
</template>

<style scoped>
.hot-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hot-title {
  font-weight: 600;
  color: var(--text-secondary);
}
.hot-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.hot-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--glass-border-solid);
  cursor: pointer;
  transition: all 0.2s;
}
.hot-item:hover {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.35);
}
.rank {
  width: 22px;
  font-weight: 700;
  color: #38bdf8;
}
.q {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.zero {
  font-size: 12px;
  color: var(--text-muted);
  padding: 0 6px;
}
:deep(.hot-card) {
  background: transparent;
  border: 1px solid var(--glass-border-solid);
}
:deep(.hot-card .el-card__header) {
  border-bottom: 1px solid var(--glass-border-solid);
  padding: 12px 16px;
}
:deep(.hot-card .el-card__body) {
  padding: 12px;
}
:deep(.el-tag--warning) {
  background: rgba(245, 158, 11, 0.15);
  border-color: rgba(245, 158, 11, 0.35);
  color: #fbbf24;
}
</style>
