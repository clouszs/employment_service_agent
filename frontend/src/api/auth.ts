import request from './request'
import type { LoginResp, User } from '@/types/user'

export function login(username: string, password: string): Promise<LoginResp> {
  return request.post('/auth/login', { username, password })
}

export function getMe(): Promise<User> {
  return request.get('/auth/me')
}

export function changePassword(oldPassword: string, newPassword: string): Promise<unknown> {
  return request.post('/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
}
