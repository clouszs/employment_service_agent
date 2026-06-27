import request from './request'
import type { PageResult } from '@/types/api'

export interface AppConfig {
  id: number
  config_key: string
  config_value: string
  description: string | null
  group_name: string | null
  is_sensitive: number
  status: number
  updated_by?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export interface AppConfigQuery {
  page?: number
  size?: number
  keyword?: string
  group_name?: string
  status?: number
}

export interface AppConfigCreatePayload {
  config_key: string
  config_value: string
  description?: string | null
  group_name?: string | null
  is_sensitive?: number
  status?: number
}

export interface AppConfigUpdatePayload {
  config_value?: string
  description?: string | null
  group_name?: string | null
  is_sensitive?: number
  status?: number
}

export function listConfigs(params: AppConfigQuery): Promise<PageResult<AppConfig>> {
  return request.get('/app-configs', { params })
}

export function createConfig(payload: AppConfigCreatePayload): Promise<AppConfig> {
  return request.post('/app-configs', payload)
}

export function updateConfig(id: number, payload: AppConfigUpdatePayload): Promise<AppConfig> {
  return request.put(`/app-configs/${id}`, payload)
}

export function deleteConfig(id: number): Promise<unknown> {
  return request.delete(`/app-configs/${id}`)
}
