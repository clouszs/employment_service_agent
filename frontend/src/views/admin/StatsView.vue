<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ChatDotRound, CircleClose, Star, Document, DataLine } from '@element-plus/icons-vue'
import * as statsApi from '@/api/stats'
import type { StatsOverview, HotQuestion } from '@/types/stats'
import type { FeedbackStats, FeedbackTrendPoint, QueryLog, FeedbackItem } from '@/types/ops'

// ===== tabs =====
const activeTab = ref('overview')

// ===== overview =====
const overviewLoading = ref(false)
const overview = ref<StatsOverview | null>(null)
const hotQuestions = ref<HotQuestion[]>([])

const overviewCards = computed<{ label: string; value: string; icon: any; color: string }[]>(() => {
  if (!overview.value) return []
  const o = overview.value
  return [
    { label: '累计问答数', value: String(o.total_questions), icon: ChatDotRound, color: '#2563eb' },
    { label: '无答案率', value: (o.no_answer_rate * 100).toFixed(1) + '%', icon: CircleClose, color: '#f59e0b' },
    { label: '点赞率', value: (o.like_rate * 100).toFixed(1) + '%', icon: Star, color: '#10b981' },
    { label: '文档总数', value: String(o.total_documents), icon: Document, color: '#6366f1' },
    { label: '已索引文档', value: String(o.indexed_documents), icon: DataLine, color: '#06b6d4' },
  ]
})

async function loadOverview() {
  overviewLoading.value = true
  try {
    const [o, h] = await Promise.all([statsApi.getOverview(), statsApi.getHotQuestions(10)])
    overview.value = o
    hotQuestions.value = h
  } finally {
    overviewLoading.value = false
  }
}

// ===== feedback =====
const feedbackLoading = ref(false)
const feedbackStatsData = ref<FeedbackStats | null>(null)
const trendData = ref<FeedbackTrendPoint[]>([])
const feedbackList = ref<{ total: number; items: FeedbackItem[] }>({ total: 0, items: [] })
const feedbackQuery = reactive({ page: 1, size: 10, rating: undefined as number | undefined, date: '' as string })

async function loadFeedbackStats() {
  feedbackLoading.value = true
  try {
    const [stats, list] = await Promise.all([
      statsApi.getFeedbackStats(),
      statsApi.listFeedback({ page: feedbackQuery.page, size: feedbackQuery.size, rating: feedbackQuery.rating || undefined, date: feedbackQuery.date || undefined }),
    ])
    feedbackStatsData.value = stats
    trendData.value = stats.trend || []
    feedbackList.value = list
  } finally {
    feedbackLoading.value = false
  }
}

function onFeedbackSearch() {
  feedbackQuery.page = 1
  loadFeedbackStats()
}

// ===== query logs =====
const logsLoading = ref(false)
const logsData = ref<{ total: number; items: QueryLog[] }>({ total: 0, items: [] })
const logsQuery = reactive({ page: 1, size: 15, keyword: '' as string, is_no_answer: undefined as number | undefined })

async function loadLogs() {
  logsLoading.value = true
  try {
    logsData.value = await statsApi.listQueryLogs({
      page: logsQuery.page,
      size: logsQuery.size,
      keyword: logsQuery.keyword || undefined,
      is_no_answer: logsQuery.is_no_answer,
    })
  } finally {
    logsLoading.value = false
  }
}

function onLogsSearch() {
  logsQuery.page = 1
  loadLogs()
}

// ===== unanswered =====
const unansweredLoading = ref(false)
const unansweredData = ref<{ total: number; items: { id: number; question: string; ask_count: number; status: number }[] }>({ total: 0, items: [] })
const unansweredQuery = reactive({ page: 1, size: 15, keyword: '' as string, status: undefined as number | undefined })

async function loadUnanswered() {
  unansweredLoading.value = true
  try {
    unansweredData.value = await statsApi.listUnanswered({
      page: unansweredQuery.page,
      size: unansweredQuery.size,
      keyword: unansweredQuery.keyword || undefined,
      status: unansweredQuery.status,
    })
  } finally {
    unansweredLoading.value = false
  }
}

function onUnansweredSearch() {
  unansweredQuery.page = 1
  loadUnanswered()
}

// ===== init =====
onMounted(() => {
  loadOverview()
  loadFeedbackStats()
  loadLogs()
  loadUnanswered()
})
</script>

<template>
  <div class="stats-view" v-loading="overviewLoading">
    <!-- 概览 -->
    <el-tabs v-model="activeTab" class="stats-tabs">
      <el-tab-pane label="📊 运营概览" name="overview">
        <div class="overview-section">
          <div class="cards-row">
            <el-card v-for="c in overviewCards" :key="c.label" class="stat-card" shadow="hover">
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

          <el-card class="hot-card" shadow="never" style="margin-top: 16px">
            <template #header>
              <span class="hot-title">🔥 高频问题排行（按 FAQ 命中）</span>
            </template>
            <el-table :data="hotQuestions" stripe>
              <el-table-column type="index" label="#" width="60" />
              <el-table-column prop="question" label="问题" show-overflow-tooltip />
              <el-table-column prop="hit_count" label="命中次数" width="140" align="center">
                <template #default="{ row }">
                  <el-tag type="warning" effect="plain">{{ row.hit_count }}</el-tag>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!overviewLoading && hotQuestions.length === 0" description="暂无数据" :image-size="60" />
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 反馈统计 -->
      <el-tab-pane label="👍 用户反馈" name="feedback">
        <div v-loading="feedbackLoading" class="feedback-section">
          <div v-if="feedbackStatsData" class="feedback-cards">
            <el-card class="fb-card" shadow="hover">
              <div class="fb-stat">
                <div class="fb-label">今日反馈</div>
                <div class="fb-value">{{ feedbackStatsData.today.total }}</div>
              </div>
              <div class="fb-sub">
                <span class="fb-like">👍 {{ feedbackStatsData.today.like }}</span>
                <span class="fb-dislike">👎 {{ feedbackStatsData.today.dislike }}</span>
                <span class="fb-rate">不满意率 {{ (feedbackStatsData.today.dislike_rate * 100).toFixed(1) }}%</span>
              </div>
            </el-card>
            <el-card class="fb-card" shadow="hover">
              <div class="fb-stat">
                <div class="fb-label">趋势（近7天）</div>
                <div class="fb-value small">{{ trendData.length }} 天</div>
              </div>
              <div class="trend-mini">
                <span v-for="t in trendData" :key="t.date" class="trend-dot" :title="`${t.date} 赞${t.like} 踩${t.dislike}`">
                  {{ t.date.slice(5) }}
                </span>
              </div>
            </el-card>
          </div>

          <el-card class="list-card" shadow="never" style="margin-top: 14px">
            <template #header>
              <div class="list-head">
                <span class="list-title">反馈明细</span>
                <div class="filter-row">
                  <el-select v-model="feedbackQuery.rating" placeholder="评分" clearable size="small" style="width: 100px" @change="onFeedbackSearch">
                    <el-option label="👍 赞" :value="1" />
                    <el-option label="👎 踩" :value="-1" />
                  </el-select>
                  <el-input v-model="feedbackQuery.date" placeholder="日期 YYYY-MM-DD" clearable size="small" style="width: 150px" @keyup.enter="onFeedbackSearch" @clear="onFeedbackSearch" />
                  <el-button type="primary" size="small" @click="onFeedbackSearch">查询</el-button>
                </div>
              </div>
            </template>
            <el-table :data="feedbackList.items" stripe>
              <el-table-column prop="user_name" label="用户" width="140" />
              <el-table-column prop="rating" label="评分" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.rating === 1 ? 'success' : 'danger'" effect="plain">{{ row.rating === 1 ? '👍' : '👎' }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="reason" label="原因" show-overflow-tooltip />
              <el-table-column prop="created_at" label="时间" width="170" />
            </el-table>
            <div class="pager">
              <el-pagination
                v-model:current-page="feedbackQuery.page"
                v-model:page-size="feedbackQuery.size"
                :total="feedbackList.total"
                :page-sizes="[10, 20, 50]"
                layout="total, sizes, prev, pager, next"
                @current-change="loadFeedbackStats"
                @size-change="onFeedbackSearch"
              />
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 问答日志 -->
      <el-tab-pane label="📋 问答日志" name="logs">
        <div v-loading="logsLoading">
          <div class="toolbar">
            <el-input v-model="logsQuery.keyword" placeholder="问题关键词" clearable style="width: 220px" @keyup.enter="onLogsSearch" @clear="onLogsSearch" />
            <el-select v-model="logsQuery.is_no_answer" placeholder="全部" clearable size="default" style="width: 130px" @change="onLogsSearch">
              <el-option label="全部" :value="undefined" />
              <el-option label="有答案" :value="0" />
              <el-option label="无答案" :value="1" />
            </el-select>
            <el-button type="primary" @click="onLogsSearch">查询</el-button>
          </div>
          <el-table :data="logsData.items" stripe>
            <el-table-column prop="question" label="问题" show-overflow-tooltip min-width="240" />
            <el-table-column prop="hit_doc_count" label="命中" width="80" align="center" />
            <el-table-column prop="latency_ms" label="耗时(ms)" width="110" align="center">
              <template #default="{ row }">{{ row.latency_ms ?? '-' }}</template>
            </el-table-column>
            <el-table-column prop="is_no_answer" label="无答案" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_no_answer ? 'warning' : 'success'" effect="plain" size="small">{{ row.is_no_answer ? '是' : '否' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
          <div class="pager">
            <el-pagination
              v-model:current-page="logsQuery.page"
              v-model:page-size="logsQuery.size"
              :total="logsData.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadLogs"
              @size-change="onLogsSearch"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 无答案问题 -->
      <el-tab-pane label="⚠️ 无答案问题" name="unanswered">
        <div v-loading="unansweredLoading">
          <div class="toolbar">
            <el-input v-model="unansweredQuery.keyword" placeholder="问题关键词" clearable style="width: 220px" @keyup.enter="onUnansweredSearch" @clear="onUnansweredSearch" />
            <el-select v-model="unansweredQuery.status" placeholder="全部状态" clearable size="default" style="width: 130px" @change="onUnansweredSearch">
              <el-option label="未解决" :value="1" />
              <el-option label="已解决" :value="2" />
            </el-select>
            <el-button type="primary" @click="onUnansweredSearch">查询</el-button>
          </div>
          <el-table :data="unansweredData.items" stripe>
            <el-table-column prop="question" label="问题" show-overflow-tooltip min-width="260" />
            <el-table-column prop="ask_count" label="询问次数" width="110" align="center">
              <template #default="{ row }">
                <el-tag type="warning" effect="plain">{{ row.ask_count }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 2 ? 'success' : 'danger'" effect="plain" size="small">{{ row.status === 2 ? '已解决' : '未解决' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="first_asked_at" label="首次出现" width="170" />
            <el-table-column prop="last_asked_at" label="最近出现" width="170" />
          </el-table>
          <div class="pager">
            <el-pagination
              v-model:current-page="unansweredQuery.page"
              v-model:page-size="unansweredQuery.size"
              :total="unansweredData.total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadUnanswered"
              @size-change="onUnansweredSearch"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.stats-view {
  padding: 4px;
}
.cards-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
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
.feedback-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 14px;
}
.fb-card {
  border-radius: 12px;
}
.fb-stat {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.fb-label {
  font-size: 13px;
  color: #475569;
}
.fb-value {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
}
.fb-value.small {
  font-size: 15px;
}
.fb-sub {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: #475569;
}
.fb-like { color: #10b981; }
.fb-dislike { color: #ef4444; }
.fb-rate { color: #f59e0b; }
.trend-mini {
  margin-top: 8px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.trend-dot {
  font-size: 12px;
  color: #475569;
  background: rgba(37, 99, 235, 0.08);
  padding: 2px 6px;
  border-radius: 6px;
}
.list-card {
  border-radius: 12px;
}
.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.list-title {
  font-weight: 600;
  color: #334155;
}
.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.pager {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
@media (max-width: 1200px) {
  .cards-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .feedback-cards {
    grid-template-columns: 1fr;
  }
}
</style>
