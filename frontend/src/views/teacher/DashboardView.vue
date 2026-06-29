<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  DataLine,
  ChatDotRound,
  Document,
  Star,
  CircleClose,
  ChatLineSquare,
  Monitor,
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import * as statsApi from '@/api/stats'
import type { StatsOverview } from '@/types/stats'

const router = useRouter()
const loading = ref(false)
const overview = ref<StatsOverview | null>(null)
const hot = ref<Array<{ faq_id: number; question: string; hit_count: number }>>([])
const cards = ref<{ label: string; value: string; icon: any; color: string }[]>([])

function buildCards(o: StatsOverview) {
  cards.value = [
    { label: '累计问答数', value: String(o.total_questions), icon: ChatDotRound, color: '#2563eb' },
    { label: '无答案率', value: (o.no_answer_rate * 100).toFixed(1) + '%', icon: CircleClose, color: '#f59e0b' },
    { label: '点赞率', value: (o.like_rate * 100).toFixed(1) + '%', icon: Star, color: '#10b981' },
    { label: '文档总数', value: String(o.total_documents), icon: Document, color: '#6366f1' },
    { label: '已索引文档', value: String(o.indexed_documents), icon: DataLine, color: '#06b6d4' },
  ]
}

async function load() {
  loading.value = true
  try {
    const [o, h] = await Promise.all([statsApi.getOverview(), statsApi.getHotQuestions(10)])
    overview.value = o
    buildCards(o)
    hot.value = h
  } finally {
    loading.value = false
  }
}

onMounted(load)

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <div v-loading="loading" class="dashboard">
    <div class="page-header">
      <h2>数据看板</h2>
      <p class="subtitle">平台运营数据概览</p>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-actions">
      <el-card shadow="hover" class="action-card" @click="go('/teacher/faqs')">
        <div class="action-icon" style="background:#7c3aed"><ChatLineSquare /></div>
        <div class="action-info">
          <div class="action-title">FAQ 管理</div>
          <div class="action-desc">维护问答知识库</div>
        </div>
      </el-card>
      <el-card shadow="hover" class="action-card" @click="go('/teacher/conversations')">
        <div class="action-icon" style="background:#0ea5e9"><Monitor /></div>
        <div class="action-info">
          <div class="action-title">对话监控</div>
          <div class="action-desc">查看学生对话记录</div>
        </div>
      </el-card>
    </div>

    <!-- 统计卡片 -->
    <div class="cards" style="margin-top:20px">
      <el-card v-for="c in cards" :key="c.label" class="stat-card" shadow="hover">
        <div class="stat-body">
          <div class="stat-icon" :style="{ background: c.color }">
            <el-icon :size="22"><component :is="c.icon" /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 高频问题 -->
    <el-card class="hot-card" shadow="never" style="margin-top:20px">
      <template #header>
        <span class="hot-title">🔥 高频问题排行（按 FAQ 命中）</span>
      </template>
      <el-table :data="hot" stripe>
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="question" label="问题" />
        <el-table-column prop="hit_count" label="命中次数" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="warning" effect="plain">{{ row.hit_count }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && hot.length === 0" description="暂无数据" :image-size="60" />
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0 0 4px;
  font-size: 22px;
}
.subtitle {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
}
.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.action-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 10px;
}
.action-card:hover {
  transform: translateY(-2px);
}
.action-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.action-title {
  font-weight: 600;
  font-size: 15px;
}
.action-desc {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.stat-card {
  border-radius: 12px;
}
.stat-body {
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #6b7280;
}
.hot-card {
  border-radius: 12px;
}
.hot-title {
  font-weight: 600;
}
@media (max-width: 900px) {
  .cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .quick-actions {
    grid-template-columns: 1fr;
  }
}
</style>
