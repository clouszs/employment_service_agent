import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/api/request'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
    },
    {
      path: '/chat/favorites',
      name: 'chat-favorites',
      component: () => import('@/views/chat/FavoritesView.vue'),
      meta: { requireAuth: true },
    },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      meta: { requireAdmin: true },
      redirect: '/admin/dashboard',
      children: [
        { path: 'dashboard', name: 'admin-dashboard', component: () => import('@/views/admin/DashboardView.vue') },
        { path: 'documents', name: 'admin-documents', component: () => import('@/views/admin/DocumentsView.vue') },
        { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/CategoriesView.vue') },
        { path: 'faqs', name: 'admin-faqs', component: () => import('@/views/admin/FaqView.vue') },
        { path: 'synonyms', name: 'admin-synonyms', component: () => import('@/views/admin/SynonymsView.vue') },
        { path: 'logs', name: 'admin-logs', component: () => import('@/views/admin/LogsView.vue') },
        { path: 'feedback', name: 'admin-feedback', component: () => import('@/views/admin/FeedbackView.vue') },
        { path: 'unanswered', name: 'admin-unanswered', component: () => import('@/views/admin/UnansweredView.vue') },
        { path: 'eval', name: 'admin-eval', component: () => import('@/views/admin/EvalView.vue') },
        { path: 'users', name: 'admin-users', component: () => import('@/views/admin/UsersView.vue'), meta: { adminOnly: true } },
        { path: 'roles', name: 'admin-roles', component: () => import('@/views/admin/RolesView.vue'), meta: { adminOnly: true } },
        { path: 'sensitive-words', name: 'admin-sensitive', component: () => import('@/views/admin/SensitiveWordsView.vue'), meta: { adminOnly: true } },
        { path: 'monitor', name: 'admin-monitor', component: () => import('@/views/admin/MonitorView.vue'), meta: { adminOnly: false } },
        { path: 'stats', name: 'admin-stats', component: () => import('@/views/admin/StatsView.vue') },
        { path: 'students', name: 'admin-students', component: () => import('@/views/admin/StudentsView.vue') },
        { path: 'announcements', name: 'admin-announcements', component: () => import('@/views/admin/AnnouncementsView.vue') },
        { path: 'settings', name: 'admin-settings', component: () => import('@/views/admin/SettingsView.vue') },
        { path: 'qa-config', name: 'admin-qa-config', component: () => import('@/views/admin/QaConfigView.vue') },
      ],
    },
    { path: '/', redirect: '/chat' },
    { path: '/:pathMatch(.*)*', redirect: '/chat' },
  ],
})

// 全局守卫：登录校验 + 管理后台角色校验
router.beforeEach(async (to) => {
  const hasToken = !!getToken()
  if (!to.meta.public && !hasToken) {
    return { path: '/login' }
  }
  if (to.path === '/login' && hasToken) {
    return { path: '/chat' }
  }
  if (to.meta.requireAdmin) {
    const userStore = useUserStore()
    if (!userStore.user) {
      try {
        await userStore.loadMe()
      } catch {
        return { path: '/login' }
      }
    }
    if (!userStore.hasAdminAccess) {
      return { path: '/chat' }
    }
    if (to.meta.adminOnly && !userStore.isAdmin) {
      return { path: '/admin/dashboard' }
    }
  }
  return true
})

export default router
