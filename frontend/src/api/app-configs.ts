import request from './request'
import type { PageResult } from '@/types/api'

/** 系统配置条目 */
export interface AppConfigItem {
  id: number
  config_key: string
  config_value: string
  description: string | null
  group_name: string | null
  is_sensitive: number
  status: number
  updated_by: number | null
  created_at: string | null
  updated_at: string | null
}

export interface AppConfigQuery {
  group_name?: string
  keyword?: string
}

/** 获取配置列表（支持按分组/关键词筛选） */
export function listAppConfigs(
  params?: AppConfigQuery,
): Promise<PageResult<AppConfigItem>> {
  return request.get('/app-configs', { params })
}

/** 获取单条配置详情 */
export function getAppConfig(id: number): Promise<AppConfigItem> {
  return request.get(`/app-configs/${id}`)
}

/** 更新配置值/描述 */
export function updateAppConfig(
  id: number,
  payload: { config_value?: string | null; description?: string | null },
): Promise<AppConfigItem> {
  return request.put(`/app-configs/${id}`, payload)
}

/** 启用/禁用配置 */
export function toggleAppConfigStatus(
  id: number,
  status: number,
): Promise<AppConfigItem> {
  return request.put(`/app-configs/${id}`, { status })
}
