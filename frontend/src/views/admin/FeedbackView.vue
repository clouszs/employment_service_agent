<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ChatDotRound, CaretTop, CaretBottom, Warning } from '@element-plus/icons-vue'
import * as opsApi from '@/api/ops'
import type { FeedbackItem, FeedbackStats } from '@/types/ops'

const stats = ref<FeedbackStats | null>(null)
const loadingStats = ref(false)

const loading = ref(false)
const rows = ref<FeedbackItem[]>([])
const total = ref(0)
const query = reactive({ page: 1, size: 10, rating: undefined as number | undefined, date: '' })

async function loadStats() {
  loadingStats.value = true
  try {
    stats.value = await opsApi.getFeedbackStats()
  } finally {
    loadingStats.value = false
  }
}

async function load() {
  loading.value = true
  try {
    const res = await opsApi.listFeedback({
      page: query.page,
      size: query.size,
      rating: query.rating,
      date: query.date || undefined,
    })
    rows.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  query.page = 1
  load()
}

onMounted(() => {
  loadStats()
  load()
})

// 当日统计卡片
const cards = computed(() => {
  const t = stats.value?.today
  return [
    { label: '今日反馈数', value: t?.total ?? 0, icon: ChatDotRound, color: '#2563eb' },
    { label: '今日点赞', value: t?.like ?? 0, icon: CaretTop, color: '#10b981' },
    { label: '今日点踩', value: t?.dislike ?? 0, icon: CaretBottom, color: '#ef4444' },
    { label: '今日点踩率', value: ((t?.dislike_rate ?? 0) * 100).toFixed(1) + '%', icon: Warning, color: '#f59e0b' },
  ]
})

// 趋势图柱高（按最大值归一到 110px）
const trendMax = computed(() => {
  const t = stats.value?.trend || []
  return Math.max(1, ...t.map((d) => Math.max(d.like, d.dislike)))
})
function barHeight(v: number): string {
  return Math.round((v / trendMax.value) * 110) + 'px'
}
</script>

<template>
  <div>
    <!-- 当日统计卡片 -->
    <div v-loading="loadingStats" class="cards">
      <el-card v-for="c in cards" :key="c.label" class="stat-card" shadow="hover">
        <div class="stat-body">
          <div class="stat-icon" :style="{ background: c.color }">
            <el-icon :size="20"><component :is="c.icon" /></el-icon>
          </div>
          <div>
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 近7天趋势图（纯 CSS 柱状） -->
    <el-card class="trend-card" shadow="never">
      <template #header>
        <div class="trend-header">
          <span>近 7 天反馈趋势</span>
          <span class="legend">
            <i class="dot like"></i>点赞<i class="dot dislike"></i>点踩
          </span>
        </div>
      </template>
      <div v-if="stats" class="trend">
        <div v-for="d in stats.trend" :key="d.date" class="trend-day">
          <div class="bars">
            <div class="bar like" :style="{ height: barHeight(d.like) }" :title="`点赞 ${d.like}`"></div>
            <div class="bar dislike" :style="{ height: barHeight(d.dislike) }" :title="`点踩 ${d.dislike}`"></div>
          </div>
          <div class="trend-label">{{ d.date.slice(5) }}</div>
        </div>
      </div>
    </el-card>

    <!-- 反馈明细 -->
    <el-card class="list-card" shadow="never">
      <div class="toolbar">
        <el-select v-model="query.rating" placeholder="全部评价" clearable style="width: 130px" @change="onSearch">
          <el-option label="点赞" :value="1" />
          <el-option label="点踩" :value="-1" />
        </el-select>
        <el-date-picker
          v-model="query.date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="按日期筛选"
          clearable
          @change="onSearch"
        />
      </div>
      <el-table v-loading="loading" :data="rows" stripe border>
        <el-table-column label="时间" prop="created_at" width="170" />
        <el-table-column label="用户" prop="user_name" width="110" />
        <el-table-column label="评价" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="row.rating === 1 ? 'success' : 'danger'" size="small">
              {{ row.rating === 1 ? '点赞' : '点踩' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="问题" prop="question" min-width="180" show-overflow-tooltip />
        <el-table-column label="答案摘要" prop="answer" min-width="200" show-overflow-tooltip />
        <el-table-column label="反馈原因" prop="reason" min-width="180" show-overflow-tooltip />
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="load"
          @size-change="onSearch"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.stat-card {
  border-radius: 12px;
}
.stat-body {
  display: flex;
  align-items: center;
  gap: 12px;
}
.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #6b7280;
}
.trend-card,
.list-card {
  border-radius: 12px;
  margin-bottom: 16px;
}
.trend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
.legend {
  font-size: 12px;
  color: #6b7280;
  font-weight: 400;
}
.legend .dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  margin: 0 4px 0 12px;
  vertical-align: middle;
}
.dot.like,
.bar.like {
  background: #10b981;
}
.dot.dislike,
.bar.dislike {
  background: #ef4444;
}
.trend {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 150px;
  padding: 0 8px;
}
.trend-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.bars {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 110px;
}
.bar {
  width: 16px;
  border-radius: 3px 3px 0 0;
  min-height: 2px;
  transition: height 0.3s;
}
.trend-label {
  font-size: 12px;
  color: #94a3b8;
}
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
