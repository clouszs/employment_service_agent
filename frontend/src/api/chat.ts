import request from './request'
import type { AskResult } from '@/types/chat'

export interface SearchHit {
  chunk_id: number | null
  document_id: number | null
  document_title: string | null
  content: string
  score: number | null
  page_no: number | null
}

export function ask(question: string, conversationId?: number | null): Promise<AskResult> {
  return request.post('/ask', {
    question,
    conversation_id: conversationId ?? undefined,
  })
}

export function search(query: string, topK = 5): Promise<SearchHit[]> {
  return request.post('/search', { query, top_k: topK })
}
