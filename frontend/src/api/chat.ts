import request from './request'
import type { AgentAskResult, AskResult } from '@/types/chat'

// ---------------- 基础问答 ----------------
export function ask(question: string, conversationId?: number | null): Promise<AskResult> {
  return request.post('/ask', {
    question,
    conversation_id: conversationId ?? undefined,
  })
}

export interface SearchHit {
  chunk_id: number | null
  document_id: number | null
  document_title: string | null
  content: string
  score: number | null
  page_no: number | null
}

export function search(query: string, topK = 5): Promise<SearchHit[]> {
  return request.post('/search', { query, top_k: topK })
}

// ---------------- Agent 问答（P0 主流程） ----------------
export function askAgent(
  query: string,
  conversationId?: number | null,
): Promise<AgentAskResult> {
  return request.post('/ask/agent', {
    query,
    conversation_id: conversationId ?? undefined,
  })
}

// ---------------- 消息引用 ----------------
export function getMessageReferences(messageId: number) {
  return request.get(`/messages/${messageId}/references`)
}
