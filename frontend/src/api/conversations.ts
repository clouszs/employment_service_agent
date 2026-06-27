import request from './request'
import type { PageResult } from '@/types/api'
import type { Conversation, Message } from '@/types/chat'

export interface AdminConversationItem extends Conversation {
  username: string
  last_message: string
}

/** 管理端会话列表 */
export function adminListConversations(params: {
  page?: number
  size?: number
  keyword?: string
  status?: number
}): Promise<PageResult<AdminConversationItem>> {
  return request.get('/admin/conversations', { params })
}

/** 管理端会话详情 */
export function adminGetConversation(id: number): Promise<Conversation & { messages: Message[] }> {
  return request.get(`/admin/conversations/${id}`)
}

/** 管理端强制删除 */
export function adminDeleteConversation(id: number): Promise<unknown> {
  return request.delete(`/admin/conversations/${id}`)
}
