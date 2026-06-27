import request from './request'
import type { HotQuestion, StatsOverview } from '@/types/stats'
import type { PageResult } from '@/types/api'
import type { QueryLog, FeedbackItem, FeedbackStats } from '@/types/ops'

// ===== 基础统计 =====
export function getOverview(): Promise<StatsOverview> {
  return request.get('/stats/overview')
}

export function getHotQuestions(limit = 10): Promise<HotQuestion[]> {
  return request.get('/stats/hot-questions', { params: { limit } })
}

// ===== 用户反馈 =====
export interface FeedbackQuery {
  page?: number
  size?: number
  rating?: number
  date?: string
}
export function listFeedback(params: FeedbackQuery): Promise<PageResult<FeedbackItem>> {
  return request.get('/feedback', { params })
}

export function getFeedbackStats(): Promise<FeedbackStats> {
  return request.get('/feedback/stats')
}

// ===== 问答日志 =====
export interface QueryLogQuery {
  page?: number
  size?: number
  keyword?: string
  is_no_answer?: number
  user_id?: number
}
export function listQueryLogs(params: QueryLogQuery): Promise<PageResult<QueryLog>> {
  return request.get('/logs/queries', { params })
}

// ===== 无答案问题 =====
export interface UnansweredQuery {
  page?: number
  size?: number
  keyword?: string
  status?: number
}
export function listUnanswered(params: UnansweredQuery): Promise<PageResult<{ id: number; question: string; ask_count: number; status: number }>> {
  return request.get('/unanswered', { params })
}
