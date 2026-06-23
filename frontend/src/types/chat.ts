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

// 前端展示用的统一消息结构（兼容历史消息与流式新消息）
export interface ChatMessage {
  id?: number // 后端消息ID，流式生成中可能暂无
  role: 'user' | 'assistant'
  content: string
  isNoAnswer?: boolean
  blocked?: boolean
  fromFaq?: boolean
  references?: Reference[]
  streaming?: boolean // 是否正在流式输出中
}
