import request from './request'
import type { PageResult } from '@/types/api'
import type { AppConfig } from './settings'

/** 系统配置条目（系统设置视图使用，含 group_name） */
export interface AppConfigItem extends AppConfig {
  group_name: string | null
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

/** 获取配置列表（兼容 settings 视图导入） */
export function listConfigs(params: { group_name?: string; keyword?: string; page?: number; size?: number }): Promise<PageResult<AppConfig>> {
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

/** 创建新配置项（供系统设置和问答策略视图复用） */
export function createConfig(payload: Partial<AppConfigItem>): Promise<AppConfigItem> {
  return request.post('/app-configs', payload)
}

/** 创建或更新配置（upsert） */
export function upsertConfig(payload: Partial<AppConfigItem>): Promise<AppConfigItem> {
  return request.post('/app-configs/upsert', payload)
}

/** 删除配置项 */
export function deleteConfig(id: number): Promise<unknown> {
  return request.delete(`/app-configs/${id}`)
}

/** 初始化默认问答配置 */
export function seedDefaults(): Promise<{ seeded: number }> {
  return request.post('/app-configs/seed-defaults', {})
}
