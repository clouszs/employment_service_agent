import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getToken } from '@/api/request'
import { useUserStore } from '@/stores/user'
import StudentLayout from '@/layouts/StudentLayout.vue'
import TeacherLayout from '@/layouts/TeacherLayout.vue'
import AdminLayout from '@/views/admin/AdminLayout.vue'
import ChatView from '@/views/ChatView.vue'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 登录页（公开）
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },

    // 独立全屏问答窗口（不套布局，需登录）
    {
      path: '/student/chat',
      name: 'student-chat',
      component: ChatView,
      meta: { requireAuth: true },
    },

    // 学生工作台（StudentLayout 包裹）
    {
      path: '/student',
      component: StudentLayout,
      meta: { requireAuth: true },
      redirect: '/student/chat',
      children: [
        { path: 'conversations', name: 'student-conversations', component: () => import('@/views/chat/HistoryView.vue') },
        { path: 'resume', name: 'student-resume', component: () => import('@/views/student/ResumeView.vue') },
        { path: 'jobs', name: 'student-jobs', component: () => import('@/views/student/JobsView.vue') },
        { path: 'calendar', name: 'student-calendar', component: () => import('@/views/student/CalendarView.vue') },
        { path: 'employment', name: 'student-employment', component: () => import('@/views/common/EmploymentDataView.vue') },
        { path: 'favorites', name: 'student-favorites', component: () => import('@/views/chat/FavoritesView.vue') },
        { path: 'profile', name: 'student-profile', component: () => import('@/views/common/ProfileView.vue') },
      ],
    },

    // 教师工作台（TeacherLayout 包裹）
    {
      path: '/teacher',
      component: TeacherLayout,
      meta: { requireTeacher: true },
      redirect: '/teacher/dashboard',
      children: [
        { path: 'dashboard', name: 'teacher-dashboard', component: () => import('@/views/teacher/DashboardView.vue') },
        { path: 'faqs', name: 'teacher-faqs', component: () => import('@/views/teacher/FaqsView.vue') },
        { path: 'conversations', name: 'teacher-conversations', component: () => import('@/views/teacher/ConversationsView.vue') },
        { path: 'employment', name: 'teacher-employment', component: () => import('@/views/common/EmploymentDataView.vue') },
        { path: 'profile', name: 'teacher-profile', component: () => import('@/views/teacher/ProfileView.vue') },
      ],
    },

    // 管理后台（AdminLayout 包裹，保留原有子路由）
    {
      path: '/admin',
      component: AdminLayout,
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
        { path: 'monitor', name: 'admin-monitor', component: () => import('@/views/admin/MonitorView.vue') },
        { path: 'stats', name: 'admin-stats', component: () => import('@/views/admin/StatsView.vue') },
        { path: 'students', name: 'admin-students', component: () => import('@/views/admin/StudentsView.vue') },
        { path: 'announcements', name: 'admin-announcements', component: () => import('@/views/admin/AnnouncementsView.vue') },
        { path: 'settings', name: 'admin-settings', component: () => import('@/views/admin/SettingsView.vue') },
        { path: 'qa-config', name: 'admin-qa-config', component: () => import('@/views/admin/QaConfigView.vue') },
        { path: 'conversations', name: 'admin-conversations', component: () => import('@/views/admin/ConversationsView.vue') },
      ],
    },

    // 旧路径兼容（重定向）
    { path: '/chat', redirect: '/student/chat' },
    { path: '/chat/favorites', redirect: '/student/favorites' },

    // 根路由
    { path: '/', redirect: '/student/chat' },

    // 404 兜底
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFoundView.vue') },
  ],
})

// ===== 全局守卫 =====
router.beforeEach(async (to) => {
  const hasToken = !!getToken()

  // 公开页放行
  if (to.meta.public) return true

  // 未登录 → 登录页
  if (!hasToken) return { path: '/login', query: { redirect: to.fullPath } }

  // 需要登录的页面，确保用户信息已加载
  const userStore = useUserStore()
  if (!userStore.user) {
    try {
      await userStore.loadMe()
    } catch {
      return { path: '/login' }
    }
  }

  // 教师端权限（editor 或 admin）
  if (to.meta.requireTeacher && !userStore.hasTeacherAccess) {
    ElMessage.warning('您无权访问该页面')
    return { path: userStore.homeRoute }
  }

  // 管理端权限（admin 或 editor）
  if (to.meta.requireAdmin) {
    if (!userStore.hasAdminAccess) {
      ElMessage.warning('您无权访问该页面')
      return { path: userStore.homeRoute }
    }
    // adminOnly 页面仅 admin 可访问
    if (to.meta.adminOnly && !userStore.isAdmin) {
      ElMessage.warning('该功能仅限管理员访问')
      return { path: '/admin/dashboard' }
    }
  }

  return true
})

export default router
