<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as statsApi from '@/api/stats'
import type { HotQuestion } from '@/types/stats'

const loading = ref(false)
const hot = ref<HotQuestion[]>([])

const emit = defineEmits<{ pick: [question: string] }>()

onMounted(async () => {
  loading.value = true
  try {
    hot.value = await statsApi.getHotQuestions(10)
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

    <div v-if="hot.length" class="hot-list">
      <div
        v-for="(item, idx) in hot"
        :key="item.question"
        class="hot-item"
        @click="onPick(item.question)"
      >
        <span class="rank">{{ idx + 1 }}</span>
        <span class="q">{{ item.question }}</span>
        <el-tag type="warning" effect="plain" size="small">{{ item.hit_count }}</el-tag>
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
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.8);
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
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
