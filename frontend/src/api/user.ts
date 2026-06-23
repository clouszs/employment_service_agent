import request from './request'
import type { PageResult } from '@/types/api'
import type { Role, User } from '@/types/user'

// ---------------- 用户 ----------------
export interface UserQuery {
  page?: number
  size?: number
  keyword?: string
  user_type?: number
  status?: number
}
export function listUsers(params: UserQuery): Promise<PageResult<User>> {
  return request.get('/users', { params })
}
export interface UserCreatePayload {
  username: string
  password: string
  real_name?: string
  user_type?: number
  college?: string
  email?: string
  phone?: string
  status?: number
}
export function createUser(payload: UserCreatePayload): Promise<User> {
  return request.post('/users', payload)
}
export function updateUser(id: number, payload: Partial<User>): Promise<User> {
  return request.put(`/users/${id}`, payload)
}
export function deleteUser(id: number): Promise<unknown> {
  return request.delete(`/users/${id}`)
}
export function hardDeleteUser(id: number): Promise<unknown> {
  return request.delete(`/users/${id}/permanent`)
}
export function resetPassword(id: number, newPassword: string): Promise<unknown> {
  return request.post(`/users/${id}/reset-password`, { new_password: newPassword })
}
export function getUserRoles(id: number): Promise<Role[]> {
  return request.get(`/users/${id}/roles`)
}
export function assignRoles(id: number, roleIds: number[]): Promise<Role[]> {
  return request.put(`/users/${id}/roles`, { role_ids: roleIds })
}

// ---------------- 角色 ----------------
export function listRoles(): Promise<Role[]> {
  return request.get('/roles')
}
export function createRole(payload: { role_code: string; role_name: string; description?: string }): Promise<Role> {
  return request.post('/roles', payload)
}
export function updateRole(id: number, payload: Partial<Role>): Promise<Role> {
  return request.put(`/roles/${id}`, payload)
}
