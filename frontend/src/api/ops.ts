import request from './request'
import type { PageResult } from '@/types/api'
import type {
  EvalCase,
  EvalRunResult,
  FeedbackItem,
  FeedbackStats,
  QueryLog,
  SensitiveWord,
  UnansweredQuestion,
} from '@/types/ops'

// ---------------- 敏感词 ----------------
export interface SensitiveWordQuery {
  page?: number
  size?: number
  keyword?: string
  status?: number
}
export function listSensitiveWords(params: SensitiveWordQuery): Promise<PageResult<SensitiveWord>> {
  return request.get('/sensitive-words', { params })
}
export function createSensitiveWord(payload: {
  word: string
  category?: string
  action?: number
}): Promise<SensitiveWord> {
  return request.post('/sensitive-words', payload)
}
export function updateSensitiveWord(id: number, payload: Partial<SensitiveWord>): Promise<SensitiveWord> {
  return request.put(`/sensitive-words/${id}`, payload)
}
export function deleteSensitiveWord(id: number): Promise<unknown> {
  return request.delete(`/sensitive-words/${id}`)
}

// ---------------- 问答日志 ----------------
export interface QueryLogQuery {
  page?: number
  size?: number
  keyword?: string
  is_no_answer?: number
}
export function listQueryLogs(params: QueryLogQuery): Promise<PageResult<QueryLog>> {
  return request.get('/logs/queries', { params })
}

// ---------------- 评测集 ----------------
export interface EvalCaseQuery {
  page?: number
  size?: number
  category?: string
  status?: number
}
export function listEvalCases(params: EvalCaseQuery): Promise<PageResult<EvalCase>> {
  return request.get('/eval-cases', { params })
}
export function createEvalCase(payload: {
  question: string
  expected_answer?: string
  expected_doc_id?: number
  category?: string
}): Promise<EvalCase> {
  return request.post('/eval-cases', payload)
}
export function updateEvalCase(id: number, payload: Partial<EvalCase>): Promise<EvalCase> {
  return request.put(`/eval-cases/${id}`, payload)
}
export function deleteEvalCase(id: number): Promise<unknown> {
  return request.delete(`/eval-cases/${id}`)
}
export function runEval(payload: { top_k?: number; category?: string; limit?: number }): Promise<EvalRunResult> {
  return request.post('/eval-cases/run', payload)
}

// ---------------- 用户反馈（管理端）----------------
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

// ---------------- 无答案问题（管理端）----------------
export interface UnansweredQuery {
  page?: number
  size?: number
  status?: number
  keyword?: string
}
export function listUnanswered(params: UnansweredQuery): Promise<PageResult<UnansweredQuestion>> {
  return request.get('/unanswered', { params })
}
export function resolveUnanswered(id: number, status: number, note?: string): Promise<UnansweredQuestion> {
  return request.put(`/unanswered/${id}`, { status, resolve_note: note })
}
export function deleteUnanswered(id: number): Promise<unknown> {
  return request.delete(`/unanswered/${id}`)
}
