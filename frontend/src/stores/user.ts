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
  // 教师（editor）/ 学生（student）角色判定
  const isEditor = computed(() => (user.value?.roles || []).includes('editor'))
  const isStudent = computed(() => (user.value?.roles || []).includes('student'))
  // 是否可进入教师端（editor 或 admin）
  const hasTeacherAccess = computed(() => isEditor.value || isAdmin.value)

  // 登录后/越权回退的角色落地页：admin → 管理端，editor → 教师端，其余 → 学生聊天
  const homeRoute = computed(() => {
    if (isAdmin.value) return '/admin'
    if (isEditor.value) return '/teacher/dashboard'
    return '/student/chat'
  })

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

  return {
    token,
    user,
    hasAdminAccess,
    isAdmin,
    isEditor,
    isStudent,
    hasTeacherAccess,
    homeRoute,
    login,
    loadMe,
    logout,
  }
})
