import request from './request'
import type { PageResult } from '@/types/api'
import type {
  KbHealthLatest,
  KbHealthLogRead,
  LlmCostDailyRead,
  LlmCostLogRead,
  LlmCostMonthlyRead,
  RefusalStats,
  AgentRefusalLogRead,
} from '@/types/monitor'

// ==================== 知识库健康度 ====================
export function getKbHealthLatest(): Promise<KbHealthLatest> {
  return request.get('/kb-health/latest')
}

export interface KbHealthHistoryQuery {
  page?: number
  size?: number
  start_date?: string
  end_date?: string
}
export function getKbHealthHistory(params: KbHealthHistoryQuery): Promise<PageResult<KbHealthLogRead>> {
  return request.get('/kb-health/history', { params })
}

export function runKbHealthCheck(): Promise<KbHealthLatest> {
  return request.post('/kb-health/run')
}

// ==================== LLM 成本 ====================
export function getLlmCostDaily(): Promise<LlmCostDailyRead> {
  return request.get('/llm-cost/daily')
}

export function getLlmCostMonthly(year: number, month: number): Promise<LlmCostMonthlyRead> {
  return request.get('/llm-cost/monthly', { params: { year, month } })
}

export interface LlmCostHistoryQuery {
  page?: number
  size?: number
  model?: string
  start_date?: string
  end_date?: string
}
export function getLlmCostHistory(params: LlmCostHistoryQuery): Promise<PageResult<LlmCostLogRead>> {
  return request.get('/llm-cost/history', { params })
}

// ==================== 拒答记录 ====================
export interface RefusalListQuery {
  page?: number
  size?: number
  risk_level?: string
  reason?: string
  start_date?: string
  end_date?: string
}
export function getRefusalList(params: RefusalListQuery): Promise<PageResult<AgentRefusalLogRead>> {
  return request.get('/refusal/list', { params })
}

export function getRefusalStats(): Promise<RefusalStats> {
  return request.get('/refusal/stats')
}
