export interface Conversation {
  id: number
  user_id: number | null
  title: string | null
  status: number
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  conversation_id: number
  role: number // 1用户 2助手
  content: string
  answer_type: number | null // 1知识库生成 2FAQ命中 3兜底
  is_no_answer: number
  llm_model: string | null
  latency_ms: number | null
  created_at: string
}

export interface Reference {
  document_id: number | null
  document_title: string | null
  chunk_id: number | null
  score: number | null
  rank_no: number | null
  page_no: number | null
  snippet?: string | null
  source_type?: 'local' | 'web'
  url?: string | null
  source?: string | null
  published_at?: string | null
  author?: string | null
}

export interface AskResult {
  conversation_id: number
  message_id: number
  answer: string
  is_no_answer: boolean
  blocked?: boolean
  from_faq?: boolean
  references: Reference[]
}

// Agent 问答增强响应字段
export interface AgentAskResult extends AskResult {
  response: string
  confidence: number
  route: string
  query_risk_level: string
  is_low_confidence: boolean
  is_error: boolean
  citations: Reference[]
  consistency_issues: Array<{ type?: string; severity?: string; detail?: string }>
  fact_issues: Array<{
    fact_type?: string
    label?: string
    values?: string[]
    unsupported_values?: string[]
    note?: string
    supported_count?: number
  }>
  temporal_warnings: string[]
  warnings: string[]
  request_id: string
  llm_tokens_in: number
  llm_tokens_out: number
}

// 前端展示用的统一消息结构（兼容历史消息与 Agent 新消息）
export interface ChatMessage {
  id?: number // 后端消息ID，流式生成中可能暂无
  role: 'user' | 'assistant'
  content: string
  isNoAnswer?: boolean
  blocked?: boolean
  fromFaq?: boolean
  references?: Reference[]
  citations?: Reference[]
  streaming?: boolean // 是否正在流式输出中
  confidence?: number
  route?: string
  queryRiskLevel?: string
  isLowConfidence?: boolean
  isError?: boolean
  consistencyIssues?: AgentAskResult['consistency_issues']
  factIssues?: AgentAskResult['fact_issues']
  temporalWarnings?: string[]
  warnings?: string[]
  requestId?: string
  llmTokensIn?: number
  llmTokensOut?: number
}
