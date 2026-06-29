/**
 * 三端导航菜单常量（单一数据源）
 *
 * 各 Layout（StudentLayout / TeacherLayout / AdminLayout）渲染菜单、
 * 路由守卫做权限判断时统一引用此处定义，避免菜单散落各文件。
 *
 * 后端角色码：admin / editor / student（“教师”= editor）。
 */
import type { Component } from 'vue'
import {
  DataLine,
  Document,
  Collection,
  ChatLineSquare,
  Connection,
  Tickets,
  ChatRound,
  QuestionFilled,
  Histogram,
  ChatDotRound,
  Monitor,
  UserFilled,
  Key,
  Warning,
  Bell,
  Setting,
  Star,
  User,
  Calendar,
  Suitcase,
} from '@element-plus/icons-vue'

/** 单个菜单项 */
export interface MenuItem {
  /** 显示名称 */
  label: string
  /** 路由 path */
  path: string
  /** Element Plus 图标组件 */
  icon: Component
}

/** 菜单分组（title 为空串表示不显示分组标题，直接平铺） */
export interface MenuGroup {
  title: string
  /** 该组是否仅 admin 可见（管理端“系统”组用） */
  adminOnly?: boolean
  items: MenuItem[]
}

/**
 * 学生端菜单（左侧栏 3 分组：对话 / 工具 / 设置）。
 * 参考设计稿 conversations.html 侧栏结构。
 */
export const STUDENT_MENU: MenuGroup[] = [
  {
    title: '对话',
    items: [
      { label: 'AI 问答', path: '/student/chat', icon: ChatDotRound },
      { label: '简历助手', path: '/student/resume', icon: Document },
      { label: '会话历史', path: '/student/conversations', icon: ChatLineSquare },
      { label: '我的收藏', path: '/student/favorites', icon: Star },
    ],
  },
  {
    title: '工具',
    items: [
      { label: '职位推荐', path: '/student/jobs', icon: Suitcase },
      { label: '面试日程', path: '/student/calendar', icon: Calendar },
      { label: '就业数据', path: '/student/employment', icon: DataLine },
    ],
  },
  {
    title: '设置',
    items: [
      { label: '个人中心', path: '/student/profile', icon: User },
    ],
  },
]

/** 教师端菜单（左侧分组侧边栏）。教师 = editor，能力聚焦内容维护。 */
export const TEACHER_MENU: MenuGroup[] = [
  {
    title: '',
    items: [{ label: '数据看板', path: '/teacher/dashboard', icon: DataLine }],
  },
  {
    title: '内容运营',
    items: [
      { label: 'FAQ 管理', path: '/teacher/faqs', icon: ChatLineSquare },
      { label: '对话监控', path: '/teacher/conversations', icon: ChatDotRound },
    ],
  },
  {
    title: '数据',
    items: [{ label: '就业数据', path: '/teacher/employment', icon: Histogram }],
  },
  {
    title: '个人',
    items: [{ label: '个人资料', path: '/teacher/profile', icon: User }],
  },
]

/** 管理员端菜单（左侧分组侧边栏，5 组）。“系统”组仅 admin 可见。 */
export const ADMIN_MENU: MenuGroup[] = [
  {
    title: '',
    items: [{ label: '概览', path: '/admin/dashboard', icon: DataLine }],
  },
  {
    title: '知识库',
    items: [
      { label: '文档管理', path: '/admin/documents', icon: Document },
      { label: '分类管理', path: '/admin/categories', icon: Collection },
      { label: 'FAQ 管理', path: '/admin/faqs', icon: ChatLineSquare },
      { label: '同义词', path: '/admin/synonyms', icon: Connection },
    ],
  },
  {
    title: '运营',
    items: [
      { label: '问答日志', path: '/admin/logs', icon: Tickets },
      { label: '用户反馈', path: '/admin/feedback', icon: ChatRound },
      { label: '无答案问题', path: '/admin/unanswered', icon: QuestionFilled },
      { label: '评测集', path: '/admin/eval', icon: Histogram },
      { label: '对话管理', path: '/admin/conversations', icon: ChatDotRound },
    ],
  },
  {
    title: '监控',
    items: [
      { label: '监控中心', path: '/admin/monitor', icon: Monitor },
      { label: '数据统计', path: '/admin/stats', icon: Histogram },
    ],
  },
  {
    title: '系统',
    adminOnly: true,
    items: [
      { label: '用户管理', path: '/admin/users', icon: UserFilled },
      { label: '角色管理', path: '/admin/roles', icon: Key },
      { label: '敏感词', path: '/admin/sensitive-words', icon: Warning },
      { label: '公告管理', path: '/admin/announcements', icon: Bell },
      { label: '系统设置', path: '/admin/settings', icon: Setting },
      { label: '智能问答配置', path: '/admin/qa-config', icon: ChatLineSquare },
    ],
  },
]
