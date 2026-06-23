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
      path: '/admin',
      component: () => import('@/views/admin/AdminLayout.vue'),
      meta: { requireAdmin: true },
      redirect: '/admin/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/DashboardView.vue'),
        },
        {
          path: 'documents',
          name: 'admin-documents',
          component: () => import('@/views/admin/DocumentsView.vue'),
        },
        {
          path: 'categories',
          name: 'admin-categories',
          component: () => import('@/views/admin/CategoriesView.vue'),
        },
        {
          path: 'faqs',
          name: 'admin-faqs',
          component: () => import('@/views/admin/FaqView.vue'),
        },
        {
          path: 'synonyms',
          name: 'admin-synonyms',
          component: () => import('@/views/admin/SynonymsView.vue'),
        },
        {
          path: 'logs',
          name: 'admin-logs',
          component: () => import('@/views/admin/LogsView.vue'),
        },
        {
          path: 'feedback',
          name: 'admin-feedback',
          component: () => import('@/views/admin/FeedbackView.vue'),
        },
        {
          path: 'unanswered',
          name: 'admin-unanswered',
          component: () => import('@/views/admin/UnansweredView.vue'),
        },
        {
          path: 'eval',
          name: 'admin-eval',
          component: () => import('@/views/admin/EvalView.vue'),
        },
        {
          path: 'users',
          name: 'admin-users',
          component: () => import('@/views/admin/UsersView.vue'),
          meta: { adminOnly: true },
        },
        {
          path: 'roles',
          name: 'admin-roles',
          component: () => import('@/views/admin/RolesView.vue'),
          meta: { adminOnly: true },
        },
        {
          path: 'sensitive-words',
          name: 'admin-sensitive',
          component: () => import('@/views/admin/SensitiveWordsView.vue'),
          meta: { adminOnly: true },
        },
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
  // 进入管理后台需 admin/editor 角色
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
      return { path: '/chat' } // 无权限退回问答端
    }
    // 部分页面仅 admin 可访问
    if (to.meta.adminOnly && !userStore.isAdmin) {
      return { path: '/admin/dashboard' }
    }
  }
  return true
})

export default router
