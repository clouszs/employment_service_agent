/** 公告模块类型 */

export interface AnnouncementItem {
  id: number
  title: string
  content: string
  priority: number
  status: number
  expire_at: string | null
  created_by: number | null
  created_at: string | null
  updated_at: string | null
}

/** 公告 banner（首页轻量展示用） */
export interface AnnouncementBanner {
  id: number
  title: string
  content: string
  priority: number
  created_at: string | null
}
