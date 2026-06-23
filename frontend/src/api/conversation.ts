import request from './request'
import type { PageResult } from '@/types/api'
import type { Conversation, Message, Reference } from '@/types/chat'

export function listConversations(page = 1, size = 50): Promise<PageResult<Conversation>> {
  return request.get('/conversations', { params: { page, size } })
}

export function getConversation(
  id: number,
): Promise<Conversation & { messages: Message[] }> {
  return request.get(`/conversations/${id}`)
}

export function createConversation(title?: string): Promise<Conversation> {
  return request.post('/conversations', { title })
}

export function renameConversation(id: number, title: string): Promise<Conversation> {
  return request.put(`/conversations/${id}`, { title })
}

export function deleteConversation(id: number): Promise<unknown> {
  return request.delete(`/conversations/${id}`)
}

export function listMessages(id: number): Promise<Message[]> {
  return request.get(`/conversations/${id}/messages`)
}

export function submitFeedback(
  messageId: number,
  rating: number,
  reason?: string,
): Promise<unknown> {
  return request.post(`/messages/${messageId}/feedback`, { rating, reason })
}

export function getReferences(messageId: number): Promise<Reference[]> {
  return request.get(`/messages/${messageId}/references`)
}
