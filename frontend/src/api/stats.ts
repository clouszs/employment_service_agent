import request from './request'
import type { HotQuestion, StatsOverview } from '@/types/stats'

export function getOverview(): Promise<StatsOverview> {
  return request.get('/stats/overview')
}

export function getHotQuestions(limit = 10): Promise<HotQuestion[]> {
  return request.get('/stats/hot-questions', { params: { limit } })
}
