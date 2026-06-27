/** 收藏模块类型 */

/** 消息片段（收藏列表项扩展字段） */
export interface FavoriteItem {
  id: number
  message_id: number
  note: string | null
  status: number
  created_at: string | null
  message_snippet?: string
  conversation_id?: number | null
}
