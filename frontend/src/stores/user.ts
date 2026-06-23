import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '@/api/auth'
import { clearToken, getToken, setToken } from '@/api/request'
import type { User } from '@/types/user'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(getToken())
  const user = ref<User | null>(null)

  // 是否有管理后台权限（admin 或 editor 角色）
  const hasAdminAccess = computed(() => {
    const roles = user.value?.roles || []
    return roles.includes('admin') || roles.includes('editor')
  })
  const isAdmin = computed(() => (user.value?.roles || []).includes('admin'))

  async function login(username: string, password: string) {
    const resp = await authApi.login(username, password)
    setToken(resp.access_token)
    token.value = resp.access_token
    user.value = resp.user
    // 登录接口不返回角色，补拉一次 /auth/me 获取 roles
    await loadMe()
    return user.value
  }

  async function loadMe() {
    user.value = await authApi.getMe()
    return user.value
  }

  function logout() {
    clearToken()
    token.value = null
    user.value = null
  }

  return { token, user, hasAdminAccess, isAdmin, login, loadMe, logout }
})
