# 阶段 11 进度追踪：复杂业务域开发

> **目标**：补齐 P2 前端页面 + P3 新领域模型，完成"高校智慧就业服务平台"的核心业务闭环
> **前置条件**：阶段 9-10 完成（单智能体扩展 + 多智能体评估）
> **启动日期**：2026-06-27
> **架构决策**：单 Agent + REST API 层，不引入多智能体

---

## 进度概览

| 批次 | 内容 | 状态 | 计划时间 | 备注 |
|------|------|------|----------|------|
| Batch A | 我的收藏 + 公告管理 | ✅ 完成 | 2026-06-27 | Commit `ea020dd`，后端 CRUD 就绪，前端页面可用 |
| Batch B | 系统设置 + 智能问答配置 + 对话管理 | 🔄 进行中 | 下周 | QA 配置选方案 A（复用 AppConfig + qa_ 前缀）；对话管理 scope：列表 + 删除 + 摘要预览 |
| Batch C | 新领域模型（企业/职位/招聘会/简历/面试/就业数据） | ⏸️ 待规划 | 待排期 | 需新建数据库表 + 后端路由 |

---

## 关键决策

### 决策 1：智能问答配置后端方案

| 方案 | 说明 | 决策 |
|------|------|------|
| 方案 A | 复用 AppConfig 表，key 以 `qa_` 前缀区分 | ⭐ **已选** |
| 方案 B | 新建 `qa_config` 表 | 未选 |

**理由**：V1 配置项量级小、无复杂关联，方案 A 零后端改造、节省 ~1 天工作量。

### 决策 2：对话管理范围

| 功能 | 说明 | 决策 |
|------|------|------|
| 列表 + 删除 + 摘要预览 | 满足审计和清理 80% 场景 | ⭐ **已选** |
| 消息详情页 | 锦上添花，留待后续迭代 | 未选 |

**理由**：排期较紧，摘要预览（列表展示最近 1 条消息）几乎零额外工作量，满足快速预览需求。

---

## 批次详情

### Batch A（2026-06-27）：我的收藏 + 公告管理

| 页面 | 路由 | 后端 API | 工作量 | 状态 |
|------|------|----------|--------|------|
| 我的收藏 | `/chat/favorites` | UserFavorite CRUD ✅ | ~1 天 | ✅ 已完成 |
| 公告管理 | `/admin/announcements` | Announcement CRUD ✅ | ~1-2 天 | ✅ 已完成 |
| Phase 11 文档 | — | — | ~半天 | ✅ 已完成 |

**提交记录：** `ea020dd` (2026-06-27) `feat(phase-11/batch-a): 我的收藏 + 公告管理前后端实现`

**实现说明：**

| 功能 | 说明 |
|------|------|
| 我的收藏 | 分页列表 + 消息摘要反查(message_id→conversation_id) + 跳转原会话 + 备注弹窗(加/编辑) + 删除 |
| 公告 Banner | ChatView 折叠展示 + 优先级色标(高🔴/中🟡/低⚪) + 静默降级(接口异常不影响主功能) |
| 公告管理 | 完整 CRUD + 搜索过滤(标题/状态) + 优先级色标 + 发布/撤下/草稿状态管理 + 分页 |
| 路由注册 | `/chat/favorites`(requireAuth) + `/admin/announcements`(requireAdmin) |
| 类型定义 | `frontend/src/types/announcements.ts` (`AnnouncementItem` + `AnnouncementBanner`) |

**操作记录：**

| 操作 | 时间 | 文件 | 说明 |
|------|------|------|------|
| 11-1 | 2026-06-27 | `docs/progress/phase-11.md` | 创建阶段 11 专用文档 |
| 11-2 | 2026-06-27 | — | 确认 types/announcements.ts 已就位 + AnnouncementsView.vue CRUD 完整 |
| 11-3 | 2026-06-27 | — | 提交 Batch A 至 `ea020dd` |

### Batch B（2026-06-27 启动）：系统设置 + 智能问答配置 + 对话管理

| 页面 | 路由 | 后端 API | 工作量 | 状态 |
|------|------|----------|--------|------|
| 系统设置 | `/admin/settings` | AppConfig CRUD ✅ | ~1 天 | 🔄 进行中（Day 1 完成） |
| 智能问答配置 | `/admin/qa-config` | 复用 AppConfig（qa_ 前缀）✅ | ~1 天 | ✅ Day 2 完成 |
| 对话管理 | `/admin/conversations` | 需后端扩展 | ~2-4 天 | ⏸️ 待后端就绪 |

**Batch B 关键决策：**

| 决策 | 方案 |
|------|------|
| 前端 UI 模式 | 只读展示 + 关键项内联编辑（非敏感项双击进入编辑模式，统一保存按钮） |
| 后端端点 | 直接复用 `/app-configs`，零改动 |
| 保存方式 | 前端逐个 PUT（后端无 batch 端点） |
| 分组展示 | 前端按 group_name 动态分组：系统基础 / 智能问答 / 检索参数 / 其他 |
| 敏感配置 | 掩码展示（`******`），禁止编辑 |

**系统设置页实现说明：**

| 功能 | 实现 |
|------|------|
| 分组 Tab | 4 个预设分组（系统基础 / 智能问答 / 检索参数 / 其他） |
| 行内编辑 | 双击非敏感配置项进入编辑模式，Enter / 失焦提交 |
| 敏感配置 | 掩码展示 + 锁图标，不可编辑 |
| 统一保存 | "保存全部修改"按钮，收集 dirty 行逐个 PUT /app-configs/{id} |
| 放弃修改 | "放弃修改"按钮，回滚到加载时快照 |
| 操作提示 | 未保存项数量提示（dirtyCount） |

**前端文件：**

| 文件 | 说明 |
|------|------|
| `frontend/src/api/app-configs.ts` | 复用 `settings.ts` 接口，新增 `listAppConfigs` / `updateAppConfig` / `toggleAppConfigStatus` |
| `frontend/src/types/app-configs.ts` | `AppConfigItem` + `ConfigGroup` + `ConfigEditRow` |
| `frontend/src/views/admin/SettingsView.vue` | 分组 Tab + 行内编辑 + 统一保存 |
| `frontend/src/router/index.ts` | 注册 `/admin/settings` 路由 |
| `frontend/src/views/admin/AdminLayout.vue` | 侧边栏新增「系统设置」菜单（Setting 图标） |

**智能问答配置页（Day 2）实现说明：**

| 功能 | 实现 |
|------|------|
| 数据过滤 | 前端只展示 `config_key` 以 `qa_` 前缀开头的配置项 |
| 分组 Tab | 4 个 QA 专属分组：问答策略 / 检索参数 / 模型配置 / 其他 |
| 行内编辑 | 同系统设置页，双击非敏感配置项进入编辑模式 |
| 敏感配置 | 掩码展示 + 锁图标，禁止编辑 |
| 统一保存 | 同系统设置页，收集 dirty 行逐个 PUT /app-configs/{id} |
| 空状态提示 | 无 qa_ 配置时展示引导文字，提示在系统设置中新建 |

**新增前端文件：**

| 文件 | 说明 |
|------|------|
| `frontend/src/views/admin/QaConfigView.vue` | QA 专属设置页，复用 SettingsView 交互模式 |
| `frontend/src/router/index.ts` | 注册 `/admin/qa-config` 路由 |
| `frontend/src/views/admin/AdminLayout.vue` | 侧边栏新增「智能问答配置」菜单 |

**操作记录（续）：**

| 操作 | 时间 | 文件 | 说明 |
|------|------|------|------|
| 11-9 | 2026-06-27 | `frontend/src/views/admin/QaConfigView.vue` | 创建智能问答配置页 |
| 11-10 | 2026-06-27 | `frontend/src/router/index.ts` | 注册 qa-config 路由 |
| 11-11 | 2026-06-27 | `frontend/src/views/admin/AdminLayout.vue` | 添加「智能问答配置」侧边栏菜单 |

**操作记录：**

| 操作 | 时间 | 文件 | 说明 |
|------|------|------|------|
| 11-4 | 2026-06-27 | `frontend/src/api/app-configs.ts` | 创建 AppConfig API 模块 |
| 11-5 | 2026-06-27 | `frontend/src/types/app-configs.ts` | 创建类型定义 |
| 11-6 | 2026-06-27 | `frontend/src/views/admin/SettingsView.vue` | 创建系统设置页面 |
| 11-7 | 2026-06-27 | `frontend/src/router/index.ts` | 注册 settings 路由 |
| 11-8 | 2026-06-27 | `frontend/src/views/admin/AdminLayout.vue` | 添加「系统设置」侧边栏菜单 |

### Batch C（待排期）：新领域模型

| 模块 | 复杂度 | 说明 | 状态 |
|------|--------|------|------|
| 企业管理 + 职位推荐 | 高 | 需新建 companies + job_postings 表 | ⏸️ 待规划 |
| 招聘会管理 | 高 | 需新建 job_fairs + registrations 表 | ⏸️ 待规划 |
| 简历助手 | 高 | 需新建 resumes 表 + AI 生成逻辑 | ⏸️ 待规划 |
| 面试日程 | 中 | 需新建 interview_events 表 + 日历视图 | ⏸️ 待规划 |
| 就业数据 | 中 | 数据聚合 + 报表 | ⏸️ 待规划 |

---

## 验收标准

| 批次 | 验收项 |
|------|--------|
| Batch A | 我的收藏 / 公告管理页面可用，路由注册，API 对接完成 |
| Batch B | 系统设置 / QA 配置 / 对话管理页面可用 |
| Batch C | 新领域模型 CRUD 可用，前端页面可访问 |

---

## 踩坑记录

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| （待补充） | — | — |

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [phase-10.md](./phase-10.md) | 多智能体触发评估：5 项检查点 + 结论（无需引入） |
| [../implementation/missing-frontend-pages.md](../implementation/missing-frontend-pages.md) | 缺失页面完整清单 + 后端接口需求 |
| [../implementation/implementation-steps.md](../implementation/implementation-steps.md) | 实施步骤总览（含批次规划） |
