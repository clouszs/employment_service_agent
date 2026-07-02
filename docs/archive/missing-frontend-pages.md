# 前端缺失页面待办清单

> **作用**：对照 `docs/前端实施方案.md` 和当前 `frontend/src/` Vue 3 SPA，列出仍缺失的前端页面、所需后端能力及实施优先级
> **前置阅读**：[前端实施方案](../前端实施方案.md) · [实施步骤总览](./implementation-steps.md)

---

## 目录

- [已实现页面（当前 frontend/src/）](#已实现页面当前-frontendsrc)
- [缺失页面总览](#缺失页面总览)
- [第一优先级：后端接口已就绪，只缺前端页面](#第一优先级后端接口已就绪只缺前端页面)
- [第二优先级：需新增后端能力，业务逻辑标准](#第二优先级需新增后端能力业务逻辑标准)
- [第三优先级：新领域模型，复杂度高](#第三优先级新领域模型复杂度高)
- [实施建议与依赖关系](#实施建议与依赖关系)

---

## 已实现页面（当前 `frontend/src/`）

根据对 `frontend/src/views/` 和 `frontend/src/router/` 的审查，以下页面已在 Vue 3 SPA 中实现：

| 页面 | 视图文件 | 路由 | 说明 |
|------|----------|------|------|
| 登录页 | `LoginView.vue` | `/login` | 含深蓝科技风、Token 存储、角色路由 |
| 智能问答 | `ChatView.vue` | `/chat` | 三栏布局、Agent 增强、纯检索模式 |
| 会话历史 | — | 集成在 ChatView 左侧栏 | `ConversationList` 组件 |
| 数据总览 | `DashboardView.vue` | `/admin/dashboard` | KPI 卡片、趋势图、HotQuestions |
| FAQ 管理 | `FaqView.vue` | `/admin/faq` | 表格 + CRUD + 批量操作 |
| 文档管理 | `DocumentsView.vue` | `/admin/documents` | 文档列表 + 上传 + 解析 + 索引 |
| 分类管理 | `CategoriesView.vue` | `/admin/categories` | 分类树 + CRUD |
| 同义词管理 | `SynonymsView.vue` | `/admin/synonyms` | 同义词 CRUD |
| 敏感词管理 | `SensitiveWordsView.vue` | `/admin/sensitive-words` | 敏感词 CRUD |
| 用户管理 | `UsersView.vue` | `/admin/users` | 用户列表 + 角色分配 |
| 角色管理 | `RolesView.vue` | `/admin/roles` | 角色 CRUD |
| 评测管理 | `EvalView.vue` | `/admin/eval` | 评测用例 + 执行 |
| 反馈管理 | `FeedbackView.vue` | `/admin/feedback` | 反馈统计 + 明细 |
| 无答案管理 | `UnansweredView.vue` | `/admin/unanswered` | 无答案列表 + 处理 |
| 问答日志 | `LogsView.vue` | `/admin/logs` | 查询日志 + 筛选 |
| 监控中心 | `MonitorView.vue` | `/admin/monitor` | KB 健康度 / LLM 成本 / 拒答记录 |
| **统计分析** | **`StatsView.vue`** | **`/admin/stats`** | **P1 已完成（4 tab：概览/反馈/日志/无答案）** |
| **学生管理** | **`StudentsView.vue`** | **`/admin/students`** | **P1 已完成（复用 users API，默认筛选 user_type=1）** |

> **总结**：18 个页面已完成，覆盖了后端 75+ 端点中的主要管理功能。P1 缺失页面补齐完成（2026-06-27）。P2 后端 API 层已完成（2026-06-27），前端页面待开发。

---

## 缺失页面总览

根据 `docs/前端实施方案.md` 的规划，以下页面仍**缺失**，按优先级分为三类：

```
┌─────────────────────────────────────────────────────────────┐
│  第一优先级（后端就绪，只缺前端）— 已完成 ✅                  │
│  统计分析页 / 学生管理页                                      │
├─────────────────────────────────────────────────────────────┤
│  第二优先级（需少量后端扩展）— 待开发 ⏸️                      │
│  系统设置 / 我的收藏 / 公告管理 / 智能问答配置 / 对话管理     │
├─────────────────────────────────────────────────────────────┤
│  第三优先级（新领域模型）— 待开发 ⏸️                          │
│  企业+职位 / 招聘会 / 简历助手 / 面试日程 / 就业数据          │
└─────────────────────────────────────────────────────────────┘
```

---

## 第一优先级：后端接口已就绪，只缺前端页面

> **特点**：后端接口和模型均已就绪，前端只需新建 Vue 页面 + 对接 API
> **预估工作量**：3-5 天

### 1.1 统计分析独立页

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/stats` |
| **角色权限** | admin / editor |
| **视图文件** | `frontend/src/views/admin/StatsView.vue` |
| **API 模块** | `frontend/src/api/stats.ts`（新建）或复用 `monitor.ts` |

**所需后端接口**（均已就绪）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/stats/overview` | 统计概览 |
| GET | `/api/v1/stats/hot-questions` | 高频问题 TOP10 |
| GET | `/api/v1/logs/queries` | 问答日志（用于趋势图） |
| GET | `/api/v1/feedback/stats` | 反馈统计 |
| GET | `/api/v1/unanswered` | 无答案列表 |
| GET | `/api/v1/kb-health/latest` | 知识库健康度 |
| GET | `/api/v1/llm-cost/daily` | 每日成本 |
| GET | `/api/v1/llm-cost/monthly` | 每月成本 |
| GET | `/api/v1/refusal/stats` | 拒答统计 |

**页面功能**：
- KPI 卡片：今日对话量 / 活跃用户 / FAQ 命中率 / 平均响应时间
- ECharts 趋势图：对话量趋势、成本趋势、满意度趋势
- 高频问题 TOP10 表格
- 知识库健康度指示器
- Token 消耗统计（日/月）
- 拒答统计饼图

**对接说明**：`DashboardView.vue` 已有的 `StatsOverview`、`HotQuestions`、`KbHealthCard`、`LlmCostCard`、`RefusalStatsCard` 组件可直接复用，提取为独立页面。

---

### 1.2 学生管理页

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/students` |
| **角色权限** | admin / editor |
| **视图文件** | `frontend/src/views/admin/StudentsView.vue` |
| **API 模块** | 复用 `user.ts` |

**所需后端接口**（均已就绪）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/users?user_type=1` | 学生列表 |
| GET | `/api/v1/users/{id}` | 学生详情 |
| POST | `/api/v1/users` | 新建学生 |
| PUT | `/api/v1/users/{id}` | 修改学生 |
| DELETE | `/api/v1/users/{id}` | 禁用学生 |
| POST | `/api/v1/users/{id}/reset-password` | 重置密码 |

**页面功能**：
- 学生列表表格（筛选 `user_type=student`）
- 搜索：学号、姓名、班级
- CRUD：新建 / 编辑 / 禁用
- 重置密码弹窗
- 查看学生对话历史（跳转会话列表并筛选）

**对接说明**：复用 `UsersView.vue` 的表格结构和 `user.ts` API，增加 `user_type=student` 默认筛选。

---

## 第二优先级：需新增后端能力，业务逻辑标准

> **特点**：需要新建数据库表 + 后端路由，业务逻辑相对标准
> **预估工作量**：1-2 周

### 2.1 系统设置页

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/settings` | 前端路由保持 `/admin/settings`，后端 API 使用 `/api/v1/app-configs` |
| **角色权限** | admin only |
| **视图文件** | `frontend/src/views/admin/SettingsView.vue` |
| **API 模块** | `frontend/src/api/settings.ts`（新建） |

**需新建后端能力**：

| 组件 | 说明 | 状态 |
|------|------|------|
| **数据模型** | `AppConfig` 表：`id`, `config_key`(unique), `config_value`, `description`, `group_name`, `updated_by`, `is_sensitive`, `status`, `created_at`, `updated_at` | ✅ 已完成 |
| **后端路由** | `routers/app_config.py`：GET `/api/v1/app-configs`（列表）、GET `/api/v1/app-configs/{id}`、POST `/api/v1/app-configs`、PUT `/api/v1/app-configs/{id}`、DELETE `/api/v1/app-configs/{id}` | ✅ 已完成 |
| **Schema** | `schemas/app_config.py`：`AppConfigBase` / `AppConfigCreate` / `AppConfigUpdate` / `AppConfigRead` | ✅ 已完成 |
| **Service** | `services/app_config_service.py`：list / get / create / update / delete / upsert | ✅ 已完成 |
| **迁移** | `migrations/fd8202321cd1_p2_add_appconfig_userfavorite_.py` | ✅ 已执行 |

**配置项建议**：

| Key | 默认值 | 说明 |
|-----|--------|------|
| `platform_name` | 智慧就业服务平台 | 平台名称 |
| `allow_register` | true | 是否允许自主注册 |
| `max_conversation_turns` | 50 | 单会话最大轮数 |
| `agent_timeout_seconds` | 30 | Agent 超时时间 |
| `kb_freshness_half_life` | 90 | 知识库半衰期（天） |
| `daily_cost_threshold` | 10 | 每日成本告警阈值（USD） |

**页面功能**：
- Key-Value 配置表格
- 分组：基础设置 / Agent 设置 / 监控设置
- 内联编辑 + 保存按钮
- 操作日志（谁改了什么）

---

### 2.2 我的收藏页

| 项目 | 内容 |
|------|------|
| **路由** | `/chat/favorites` |
| **角色权限** | 学生 / 老师 / 管理员 |
| **视图文件** | `frontend/src/views/chat/FavoritesView.vue` |
| **API 模块** | `frontend/src/api/favorites.ts`（新建） |

**需新建后端能力**：

| 组件 | 说明 | 状态 |
|------|------|------|
| **数据模型** | `UserFavorite` 表：`id`, `user_id`, `message_id`, `note`, `status`, `created_at` | ✅ 已完成 |
| **后端路由** | `routers/user_favorite.py`：GET `/api/v1/favorites`（列表）、POST `/api/v1/favorites`、PUT `/api/v1/favorites/{fav_id}`、DELETE `/api/v1/favorites/{fav_id}` | ✅ 已完成 |
| **Schema** | `schemas/user_favorite.py`：`UserFavoriteBase` / `UserFavoriteCreate` / `UserFavoriteUpdate` / `UserFavoriteRead` | ✅ 已完成 |
| **Service** | `services/user_favorite_service.py`：list / get / create / update / delete / batch_delete | ✅ 已完成 |
| **迁移** | `migrations/fd8202321cd1_p2_add_appconfig_userfavorite_.py` | ✅ 已执行 |

**页面功能**：
- 收藏消息列表（带引用卡片）
- 添加备注
- 删除收藏
- 跳转原会话

---

### 2.3 公告管理页

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/announcements` |
| **角色权限** | admin / editor |
| **视图文件** | `frontend/src/views/admin/AnnouncementsView.vue` |
| **API 模块** | `frontend/src/api/announcements.ts`（新建） |

**需新建后端能力**：

| 组件 | 说明 | 状态 |
|------|------|------|
| **数据模型** | `Announcement` 表：`id`, `title`, `content`, `priority`, `publish_at`, `expire_at`, `status`, `created_by`, `created_at`, `updated_at` | ✅ 已完成 |
| **后端路由** | `routers/announcements.py`：GET `/api/v1/announcements`（列表，公开）、GET `/api/v1/announcements/admin`（管理列表，带筛选）、POST `/api/v1/announcements`、PUT `/api/v1/announcements/{id}`、DELETE `/api/v1/announcements/{id}`、GET `/api/v1/announcements/list/active`（生效中公告） | ✅ 已完成 |
| **Schema** | `schemas/announcement.py`：`AnnouncementBase` / `AnnouncementCreate` / `AnnouncementUpdate` / `AnnouncementRead` | ✅ 已完成 |
| **Service** | `services/announcement_service.py`：list / get / create / update / delete / toggle_status | ✅ 已完成 |
| **迁移** | `migrations/fd8202321cd1_p2_add_appconfig_userfavorite_.py` | ✅ 已执行 |

**页面功能**：
- 公告列表（支持置顶、定时发布）
- 富文本编辑（建议集成简单 Markdown 或 Element Plus 的 `el-input` type="textarea"）
- 优先级标识（高/中/低）
- 发布状态切换
- 在前端 ChatView 首页展示最新公告条

---

### 2.4 智能问答配置页

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/qa-config` |
| **角色权限** | admin only |
| **视图文件** | `frontend/src/views/admin/QaConfigView.vue` |
| **API 模块** | 复用 `settings.ts` 或新建 |

**需新建后端能力**：

| 组件 | 说明 |
|------|------|
| **数据模型** | `QaConfig` 表 或复用 `SystemConfig` 表（前缀 `qa_`） |
| **后端路由** | `routers/qa_config.py` 或 `settings.py` 子模块 |
| **Schema** | `schemas/qa_config.py` |

**可配置项**（与 `config.py` 中的 Agent 配置对应）：

| Key | 默认值 | 说明 |
|-----|--------|------|
| `qa_welcome_message` | 您好，我是智能就业顾问... | 欢迎语 |
| `qa_confidence_threshold` | 0.5 | 最低置信度 |
| `qa_max_retries` | 3 | 最大重试次数 |
| `qa_show_citations` | true | 是否显示引用来源 |
| `qa_enable_web_fallback` | false | 是否启用外部检索 |
| `qa_enable_consistency_check` | true | 是否启用一致性检查 |

**页面功能**：
- 表单配置（滑块、开关、输入框）
- 保存后实时生效（无需重启）
- 配置变更日志

**简化方案**：直接读取/写入 `config.py` 中的配置，通过 `/api/v1/settings` 统一管理，无需单独建表。

---

### 2.5 对话管理页（管理端）

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/conversations` |
| **角色权限** | admin / editor |
| **视图文件** | `frontend/src/views/admin/ConversationsAdminView.vue` |
| **API 模块** | `frontend/src/api/conversations.ts`（新建） |

**需新建后端能力**：

| 组件 | 说明 |
|------|------|
| **后端路由** | `routers/admin_conversations.py`：管理员查看所有用户的会话 + 强制删除 |
| **Schema** | 复用 `schemas/qa.py` 中的 `ConversationRead` |

**注意**：现有 `routers/conversations.py` 中的接口只返回当前用户的会话，管理端需要全局查看能力。

**页面功能**：
- 全部用户会话列表（含用户名、消息数、最后活跃时间）
- 搜索：用户名、会话标题关键词
- 查看会话详情（消息列表）
- 强制删除/归档会话
- 标记异常会话

---

## 第三优先级：新领域模型，复杂度高

> **特点**：需要新建多张数据表、复杂业务逻辑、外部数据源集成
> **预估工作量**：4-8 周（按模块）

### 3.1 企业管理 + 职位推荐

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/companies` / `/jobs` |
| **角色权限** | admin（管理）/ 学生/老师（浏览） |
| **视图文件** | `CompaniesView.vue` / `JobsView.vue` |
| **API 模块** | `api/companies.ts` / `api/jobs.ts` |

**需新建后端能力**：

| 模型 | 表名 | 关键字段 |
|------|------|----------|
| `Company` | `companies` | `name`, `industry`, `scale`, `location`, `description`, `logo_url`, `website`, `status` |
| `JobPosting` | `job_postings` | `company_id`, `title`, `salary_min/max`, `requirements`, `description`, `publish_date`, `expire_date`, `status` |

**业务复杂度**：
- 企业 CRUD（含 Logo 上传）
- 职位发布（关联企业）
- 职位检索（全文搜索 + 筛选）
- AI 推荐引擎（基于用户画像 + 职位标签匹配）— V2

**页面功能**：
- 企业列表 / 详情 / 入驻申请审核
- 职位列表 / 详情 / 发布表单
- 学生端：职位推荐卡片 + 一键投递

---

### 3.2 招聘会管理

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/job-fairs` / `/job-fairs` |
| **角色权限** | admin / editor（管理）/ 学生（浏览报名） |
| **视图文件** | `JobFairsView.vue` / `JobFairDetailView.vue` |
| **API 模块** | `api/job-fairs.ts` |

**需新建后端能力**：

| 模型 | 表名 | 关键字段 |
|------|------|----------|
| `JobFair` | `job_fairs` | `name`, `description`, `start_time`, `end_time`, `location`, `online_url`, `status` |
| `JobFairRegistration` | `job_fair_registrations` | `job_fair_id`, `user_id`, `resume_url`, `status`, `checked_in` |

**业务复杂度**：
- 招聘会 CRUD
- 学生报名 + 签到（二维码/验证码）
- 企业摊位分配
- 报名统计

**页面功能**：
- 招聘会列表（进行中 / 即将开始 / 已结束）
- 详情页：企业参展列表 + 在线入口
- 报名/签到流程
- 管理端：报名统计 + 签到核销

---

### 3.3 简历助手

| 项目 | 内容 |
|------|------|
| **路由** | `/chat/resume` |
| **角色权限** | 学生 / 老师 / 管理员 |
| **视图文件** | `ResumeAssistantView.vue` |
| **API 模块** | `api/resumes.ts` |

**需新建后端能力**：

| 模型 | 表名 | 关键字段 |
|------|------|----------|
| `Resume` | `resumes` | `user_id`, `title`, `content`(JSON), `template_id`, `version`, `ai_generated` |

**业务复杂度**：
- 简历 CRUD + 版本管理
- AI 生成简历（调用 LLM 基于用户信息生成）
- 富文本编辑器（支持 Markdown 或所见即所得）
- 导出 PDF

**页面功能**：
- 简历编辑器（分区块：基本信息 / 教育背景 / 实习经历 / 项目经验 / 技能证书）
- AI 一键生成（输入目标岗位，自动填充内容）
- 模板切换
- 预览 + 导出

---

### 3.4 面试日程

| 项目 | 内容 |
|------|------|
| **路由** | `/chat/interviews` |
| **角色权限** | 学生 / 老师 / 管理员 |
| **视图文件** | `InterviewScheduleView.vue` |
| **API 模块** | `api/interviews.ts` |

**需新建后端能力**：

| 模型 | 表名 | 关键字段 |
|------|------|----------|
| `InterviewEvent` | `interview_events` | `user_id`, `company_id`, `job_posting_id`, `interview_time`, `location`, `type`, `status`, `notes` |

**业务复杂度**：
- 面试日程 CRUD
- 日历视图（月/周视图）
- 提醒通知（站内信 + 邮件）
- ICS 日历导出

**页面功能**：
- 日历视图（月/列表切换）
- 添加面试日程（关联职位/公司）
- 状态标记（待面试 / 已通过 / 已拒绝）
- 导出到日历

---

### 3.5 就业数据

| 项目 | 内容 |
|------|------|
| **路由** | `/admin/employment` |
| **角色权限** | admin / editor |
| **视图文件** | `EmploymentDataView.vue` |
| **API 模块** | `api/employment.ts` |

**需新建后端能力**：

| 组件 | 说明 |
|------|------|
| **数据源** | 新增就业上报表单 / 对接学校就业系统 / Excel 导入 |
| **后端路由** | `routers/employment.py`：统计分析接口 |

**业务复杂度**：
- 就业数据聚合（按学院/专业/年份）
- 就业率趋势图
- 薪资分布统计
- 企业招聘偏好分析

**页面功能**：
- 就业率仪表盘
- 专业就业对比图
- 薪资区间分布
- 导出报表

---

### 3.6 帮助中心

| 项目 | 内容 |
|------|------|
| **路由** | `/help` |
| **角色权限** | 全部 |
| **视图文件** | `HelpCenterView.vue` |
| **API 模块** | 复用 `faqs.ts` + `documents.ts` |

**后端需求**：无需新建，复用现有 `/faqs` 和 `/documents` 接口。

**页面功能**：
- FAQ 分类展示（学生端 / 管理员端 / 通用）
- 搜索 FAQ
- 联系管理员入口
- 最小版：直接复用 FaqView 的公开部分，去掉管理功能

---

## 实施建议与依赖关系

### 依赖关系图

```
系统设置  ──────────────────┐
                            ├──→ 无强制依赖，可并行
我的收藏  ──────────────────┘

公告管理  ──────────────────┐
                            ├──→ 无强制依赖，可并行
智能问答配置 ───────────────┘

统计分析  ───→ 依赖：系统配置完成（用于配置展示维度）

学生管理  ───→ 无强制依赖，可独立推进

企业管理  ───→ 依赖：系统设置（企业审核流程配置）
    │
    └──→ 职位推荐 ──→ 依赖：企业管理（企业数据源）

招聘会管理 ──→ 依赖：企业管理（参展企业）

简历助手  ───→ 依赖：企业管理（职位数据用于 AI 生成）

面试日程  ────→ 依赖：职位推荐（申请职位后生成面试）

就业数据  ────→ 依赖：简历助手 / 面试日程（就业数据来源）

帮助中心  ────→ 无依赖，可最后做（最小版只需复用 FAQ）
```

### 建议实施顺序

| 批次 | 页面 | 理由 |
|------|------|------|
| **Batch 1**（Week 1） | 统计分析 + 学生管理 | 后端就绪，纯前端工作量，快速交付 |
| **Batch 2**（Week 2-3） | 系统设置 + 我的收藏 + 公告管理 | 基础支撑模块，后续模块依赖系统设置 |
| **Batch 3**（Week 3-4） | 智能问答配置 + 对话管理 | 完善管理端能力 |
| **Batch 4**（Week 5-6） | 企业管理 + 职位推荐 | 新领域核心 |
| **Batch 5**（Week 7-8） | 招聘会 + 简历助手 | 高频使用场景 |
| **Batch 6**（Week 9-10） | 面试日程 + 就业数据 | 数据聚合类 |
| **Batch 7**（Week 11） | 帮助中心 | 最小版快速上线 |

---

## 后端待扩展接口清单

以下接口在 `docs/前端实施方案.md` 中标记为"需新增"，在实施上述页面时需要同步扩展：

| 接口 | 方法 | 路径 | 关联页面 | 复杂度 |
|------|------|------|----------|--------|
| 对话管理（全局） | GET | `/api/v1/admin/conversations` | 对话管理页 | 低 |
| 会话搜索扩展 | GET | `/api/v1/conversations?keyword=&start_date=&end_date=&sort=` | 会话历史页 | 低 |
| 系统配置 CRUD | GET/PUT | `/api/v1/settings` | 系统设置页 | 低 |
| 我的收藏 CRUD | GET/POST/DELETE | `/api/v1/favorites` | 我的收藏页 | 低 |
| 公告 CRUD | GET/POST/PUT/DELETE | `/api/v1/announcements` | 公告管理页 | 中 |
| QA 配置读写 | GET/PUT | `/api/v1/qa-config` | 智能问答配置页 | 中 |
| 企业 CRUD | GET/POST/PUT/DELETE | `/api/v1/admin/companies` | 企业管理页 | 高 |
| 职位 CRUD | GET/POST/PUT/DELETE | `/api/v1/admin/jobs` | 职位管理页 | 高 |
| 招聘会 CRUD | GET/POST/PUT/DELETE | `/api/v1/admin/job-fairs` | 招聘会管理页 | 高 |
| 招聘会报名 | POST | `/api/v1/job-fairs/{id}/register` | 招聘会页 | 中 |
| 简历 CRUD | GET/POST/PUT/DELETE | `/api/v1/resumes` | 简历助手页 | 高 |
| AI 生成简历 | POST | `/api/v1/resumes/generate` | 简历助手页 | 高 |
| 面试日程 CRUD | GET/POST/PUT/DELETE | `/api/v1/interviews` | 面试日程页 | 中 |
| 就业数据统计 | GET | `/api/v1/admin/employment/overview` | 就业数据页 | 中 |

---

## 附：前端实施方案原文阶段对照

| 实施方案阶段 | 对应内容 | 当前状态 |
|-------------|----------|----------|
| Phase 1：静态页面骨架 | login / chat / conversations / admin-dashboard / admin-faq 的静态页面 | ✅ 静态页面已有，接口在 Vue 3 SPA 中已对接 |
| Phase 2：接口打通 | 5 个页面调用后端 API | ✅ Vue 3 SPA 已全部打通 |
| Phase 3：缺失页面补齐 | 文档/分类/敏感词/用户/对话管理 | ✅ 文档/分类/敏感词/用户已完成，对话管理待做（管理端视图） |
| Phase 4：新业务模块 | 系统设置/收藏/公告/统计/QA 配置/学生管理 | ✅ 统计+学生已完成，其余待开发（见第二优先级） |
| Phase 5：复杂业务域 | 企业/职位/招聘会/简历/面试/就业/帮助中心 | ⏸️ 全部缺失（见第三优先级） |
