// 后端统一响应结构
export interface ApiResp<T = unknown> {
  code: number
  message: string
  data: T
}

// 分页结果
export interface PageResult<T> {
  total: number
  page: number
  size: number
  items: T[]
}
