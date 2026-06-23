// 运营·安全·质量类型（对齐后端 schemas/ops.py）

export interface SensitiveWord {
  id: number
  word: string
  category: string | null
  action: number // 1拦截 2替换 3告警
  status: number
  created_at: string
}

export interface QueryLog {
  id: number
  user_id: number | null
  conversation_id: number | null
  message_id: number | null
  question: string
  answer_brief: string | null
  hit_doc_count: number | null
  is_no_answer: number
  latency_ms: number | null
  client_ip: string | null
  channel: string | null
  created_at: string
}

export interface EvalCase {
  id: number
  question: string
  expected_answer: string | null
  expected_doc_id: number | null
  category: string | null
  status: number
  created_at: string
}

export interface EvalCaseResult {
  case_id: number
  question: string
  expected_doc_id: number | null
  hit: boolean
  hit_rank: number | null
  top_doc_ids: number[]
  top_score: number | null
}

export interface EvalRunResult {
  total: number
  evaluated: number
  skipped: number
  hit_count: number
  hit_rate: number
  details: EvalCaseResult[]
}

export interface FeedbackItem {
  id: number
  rating: number // 1赞 -1踩
  reason: string | null
  created_at: string
  user_name: string | null
  question: string | null
  answer: string | null
}

export interface FeedbackTrendPoint {
  date: string
  like: number
  dislike: number
}

export interface FeedbackStats {
  today: { total: number; like: number; dislike: number; dislike_rate: number }
  trend: FeedbackTrendPoint[]
}

export interface UnansweredQuestion {
  id: number
  question: string
  ask_count: number
  last_user_id: number | null
  status: number // 1未解决 2已解决
  resolve_note: string | null
  first_asked_at: string
  last_asked_at: string
}
