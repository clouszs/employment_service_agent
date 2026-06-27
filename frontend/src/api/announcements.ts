import request from './request'
import type { PageResult } from '@/types/api'

/** 公告条目 */
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

export interface AnnouncementQuery {
  page?: number
  size?: number
  keyword?: string
  status?: number
}

export interface AnnouncementCreatePayload {
  title: string
  content: string
  priority?: number
  status?: number
  expire_at?: string | null
}

export interface AnnouncementUpdatePayload {
  title?: string | null
  content?: string | null
  priority?: number | null
  status?: number | null
  expire_at?: string | null
}

/** 列表（公开/公开筛选） */
export function listAnnouncements(params: {
  page?: number
  size?: number
  status?: number
}): Promise<PageResult<AnnouncementItem>> {
  return request.get('/announcements', { params })
}

/** 管理列表（含 keyword 筛选） */
export function adminListAnnouncements(params: AnnouncementQuery): Promise<PageResult<AnnouncementItem>> {
  return request.get('/announcements/admin', { params })
}

/** 获取生效中公告 */
export function listActiveAnnouncements(): Promise<AnnouncementItem[]> {
  return request.get('/announcements/list/active')
}

/** 新建公告 */
export function createAnnouncement(payload: AnnouncementCreatePayload): Promise<AnnouncementItem> {
  return request.post('/announcements', payload)
}

/** 更新公告 */
export function updateAnnouncement(
  id: number,
  payload: AnnouncementUpdatePayload,
): Promise<AnnouncementItem> {
  return request.put(`/announcements/${id}`, payload)
}

/** 删除公告 */
export function deleteAnnouncement(id: number): Promise<unknown> {
  return request.delete(`/announcements/${id}`)
}
