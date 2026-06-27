/** 系统配置模块类型 */

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

/** 配置分组定义 */
export interface ConfigGroup {
  key: string
  label: string
  icon?: string
}

/** 编辑状态的行数据 */
export interface ConfigEditRow {
  id: number
  config_key: string
  description: string | null
  config_value: string
  is_sensitive: number
  status: number
  dirty: boolean
}
