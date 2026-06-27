import request from './request'
import type { PageResult } from '@/types/api'

/** 收藏条目 */
export interface FavoriteItem {
  id: number
  message_id: number
  note: string | null
  status: number
  created_at: string | null
  /** 消息摘要（用于列表展示） */
  message_snippet?: string
  /** 关联会话 ID（反查后回填） */
  conversation_id?: number | null
}

export interface FavoriteQuery {
  page?: number
  size?: number
}

export interface FavoriteCreatePayload {
  message_id: number
  note?: string | null
}

export interface FavoriteUpdatePayload {
  note?: string | null
}

/** 获取我的收藏列表 */
export function listFavorites(params: FavoriteQuery): Promise<PageResult<FavoriteItem>> {
  return request.get('/favorites', { params })
}

/** 添加收藏 */
export function createFavorite(payload: FavoriteCreatePayload): Promise<FavoriteItem> {
  return request.post('/favorites', payload)
}

/** 修改备注 */
export function updateFavorite(favId: number, payload: FavoriteUpdatePayload): Promise<FavoriteItem> {
  return request.put(`/favorites/${favId}`, payload)
}

/** 取消收藏 */
export function deleteFavorite(favId: number): Promise<unknown> {
  return request.delete(`/favorites/${favId}`)
}

/** 获取消息详情（用于反查 conversation_id 和摘要） */
export function getMessageDetail(messageId: number) {
  return request.get(`/messages/${messageId}`)
}
