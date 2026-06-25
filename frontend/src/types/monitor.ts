// 监控模块统一类型定义

// ==================== 知识库健康度 ====================
export interface KbHealthLatest {
  check_date: string
  health_score: number
  warning_count: number
  expired_count: number
  total_docs: number
  current_docs: number
  avg_freshness?: number | null
  created_at: string
}

export interface KbHealthLogRead {
  id: number
  check_date: string
  total_docs: number
  current_docs: number
  warning_docs: number
  expired_docs: number
  avg_freshness?: number | null
  health_score?: number | null
  created_at: string
}

// ==================== LLM 成本 ====================
export interface LlmCostModelBreakdown {
  model: string
  cost_usd: number
  call_count: number
  tokens_in: number
  tokens_out: number
}

export interface LlmCostDailyRead {
  stat_date: string
  total_cost_usd: number
  total_calls: number
  total_tokens_in: number
  total_tokens_out: number
  models: LlmCostModelBreakdown[]
}

export interface LlmCostMonthlyRead {
  year: number
  month: number
  total_cost_usd: number
  models: LlmCostModelBreakdown[]
}

export interface LlmCostLogRead {
  id: number
  stat_date: string
  model: string
  call_count: number
  tokens_in: number
  tokens_out: number
  cost_usd: number
  created_at: string
  updated_at: string
}

// ==================== 拒答记录 ====================
export interface AgentRefusalLogRead {
  id: number
  query: string
  refusal_reason: string
  confidence?: number | null
  query_risk_level?: string | null
  conversation_id?: number | null
  user_id?: number | null
  created_at: string
}

export interface RefusalStats {
  total_refusals: number
  today_refusals: number
  by_reason: Array<{ reason: string; count: number }>
  by_risk_level: Array<{ risk_level: string; count: number }>
}

// ==================== 引用质量 ====================
export interface CitationQualityLogRead {
  id: number
  message_id: number
  total_sentences: number
  direct_count: number
  indirect_count: number
  none_count: number
  avg_confidence?: number | null
  quality_score?: number | null
  created_at: string
}

// ==================== 一致性问题 ====================
export interface ConsistencyIssueLogRead {
  id: number
  message_id: number
  current_query?: string | null
  previous_query?: string | null
  contradiction_type?: string | null
  severity?: string | null
  created_at: string
}

// ==================== 事实核验 ====================
export interface FactVerificationLogRead {
  id: number
  message_id: number
  fact_type: string
  extracted_value?: string | null
  validation_result?: string | null
  suggestion?: string | null
  created_at: string
}
