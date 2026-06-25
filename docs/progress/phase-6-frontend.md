# 阶段 6 进度追踪：前端对接（2026-06-25 启动）

> 目标：按照 `frontend-implementation-plan.md` 完成阶段 6 全量实施，让前端能够调用后端 75 个端点并呈现 Agent 增强响应。
> 前置条件：阶段 0-5 全部完成（环境 / Agent 核心 / 幻觉防御 / 监控 / QA 升级 / 路由 Schema）。

---

## 阶段 6 前置条件确认

| 前置 | 状态 | 说明 |
|------|------|------|
| 阶段 0-5 完成 | ✅ | 环境 / Agent / 幻觉防御 / 监控 / QA / 路由 Schema 全部完成 |
| 后端 75 个端点可用 | ✅ | `main.py` 已注册 22 组路由 |
| `schemas/agent.py` | ✅ | `AgentChatRequest` / `AgentChatResponse` 已定义 |
| `schemas/monitor.py` | ✅ | 10 个 Schema（6 Read + 4 DTO） |
| 前端基础框架 | ✅ | Vue 3 + Pinia + Element Plus + Vue Router + Axios |
| 前端现有页面 | ✅ | 登录页 / 聊天主页 / 管理后台 12 个页面 |

---

## 操作 6-1：扩展前端类型定义

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 类型 |
| **修改文件** | `frontend/src/types/chat.ts` |

**变更：**
- 新增 `AgentAskResult` 接口（含 confidence / route / citations / warnings 等 17 个字段）
- 扩展 `ChatMessage` 接口，增加 Agent 增强字段（confidence / route / isError / temporalWarnings 等）

---

## 操作 6-2：新增/更新前端 API 模块

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / API |
| **新建文件** | `frontend/src/api/monitor.ts` |
| **修改文件** | `frontend/src/api/chat.ts` |

**`chat.ts` 变更：**
- 新增 `askAgent(query, conversationId)` → `POST /ask/agent`
- 新增 `getMessageReferences(messageId)` → `GET /messages/{id}/references`
- 保留原有 `ask()` / `search()` 兼容旧流程

**`monitor.ts` 新建：**
- 知识库健康度：`getKbHealthLatest()` / `getKbHealthHistory()` / `runKbHealthCheck()`
- LLM 成本：`getLlmCostDaily()` / `getLlmCostMonthly()` / `getLlmCostHistory()`
- 拒答记录：`getRefusalList()` / `getRefusalStats()`

---

## 操作 6-3：新增前端 Store

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 状态管理 |
| **新建文件** | `frontend/src/stores/monitor.ts` |

**功能：**
- `kbHealth` / `llmCostDaily` / `refusalStats` 三个响应式状态
- `loadKbHealthLatest()` / `loadLlmCostDaily()` / `loadRefusalStats()`
- `refreshDashboardCards()` 并行刷新三个摘要

---

## 操作 6-4：新增聊天增强组件

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 组件 |
| **新建文件** | 见下方 |

| 组件 | 路径 | 用途 |
|------|------|------|
| `SearchBox.vue` | `frontend/src/components/chat/SearchBox.vue` | AI 问答 / 纯检索切换 + 磨砂玻璃搜索框 |
| `ConfidenceBadge.vue` | `frontend/src/components/chat/ConfidenceBadge.vue` | 置信度标签（高/中/低） |
| `TemporalWarning.vue` | `frontend/src/components/chat/TemporalWarning.vue` | 时效性警告横幅 |
| `RefusalMessage.vue` | `frontend/src/components/chat/RefusalMessage.vue` | 拒答提示 + 建议操作 |

---

## 操作 6-5：新增仪表板卡片组件

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 组件 |
| **新建文件** | 见下方 |

| 组件 | 路径 | 用途 |
|------|------|------|
| `StatsOverview.vue` | `frontend/src/components/dashboard/StatsOverview.vue` | 问答统计概览（累计问答 / 无答案率 / 点赞率 / 索引文档） |
| `HotQuestions.vue` | `frontend/src/components/dashboard/HotQuestions.vue` | 热门问题排行榜 |
| `KbHealthCard.vue` | `frontend/src/components/dashboard/KbHealthCard.vue` | 知识库健康度卡片 |
| `LlmCostCard.vue` | `frontend/src/components/dashboard/LlmCostCard.vue` | LLM 成本卡片（按模型拆分进度条） |
| `RefusalStatsCard.vue` | `frontend/src/components/dashboard/RefusalStatsCard.vue` | 拒答统计卡片（按风险等级进度条） |
| `DashboardPanels.vue` | `frontend/src/components/dashboard/DashboardPanels.vue` | 左侧面板容器，聚合上述卡片 |

---

## 操作 6-6：重构 ChatView 为三栏深空蓝布局

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 视图 |
| **修改文件** | `frontend/src/views/ChatView.vue` |

**变更：**
- 左侧面板（300px）：会话列表 + DashboardPanels（仅 admin/editor 可见）
- 中央面板：SearchBox + MessageList + ChatInput，深空蓝渐变背景
- 右侧面板（340px，仅 admin/editor 可见）：HotQuestions
- 搜索框采用磨砂玻璃 + 霓虹发光效果

---

## 操作 6-7：更新 ChatStore 对接 askAgent

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 状态管理 |
| **修改文件** | `frontend/src/stores/chat.ts` |

**变更：**
- 新增 `sendAgent(question)` 方法，调用 `askAgent()` 同步接口
- 将 `AgentAskResult` 映射为 `ChatMessage`，包含 confidence / route / citations / warnings 等字段
- 错误处理：捕获异常后设置 `isNoAnswer=true` / `isError=true`

---

## 操作 6-8：更新 MessageItem 渲染 Agent 增强字段

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 组件 |
| **修改文件** | `frontend/src/components/chat/MessageItem.vue` |

**变更：**
- 引入 `ConfidenceBadge` / `TemporalWarning` / `RefusalMessage`
- 助手消息元信息区展示：置信度标签 / 路由标签 / 风险等级 / 低置信度标签
- 引用来源兼容 `references` 和 `citations` 字段
- 状态标签增加 `isError` → "系统错误"

---

## 操作 6-9：注册 MonitorView 路由

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 路由 |
| **修改文件** | `frontend/src/router/index.ts` |
| **新建文件** | `frontend/src/views/admin/MonitorView.vue` |

**路由变更：**
- 新增 `/admin/monitor` → `MonitorView.vue`
- 权限：`requireAdmin`（admin/editor 可访问）

**MonitorView 功能：**
- Tab 1：知识库健康度（最新快照 + 历史表格）
- Tab 2：LLM 成本（今日汇总 + 成本历史表格）
- Tab 3：拒答记录（统计摘要 + 拒答列表表格）
- 顶部刷新按钮调用 `refreshDashboardCards()`

---

## 操作 6-10：更新 AdminLayout 菜单

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 布局 |
| **修改文件** | `frontend/src/views/admin/AdminLayout.vue` |

**变更：**
- 引入 `Monitor` 图标
- 侧边栏新增「监控」菜单组，包含「监控中心」入口
- `TITLES` 映射表新增 `'admin-monitor': '监控中心'`

---

## 操作 6-11：新增 monitor 类型定义

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 6 / 类型 |
| **新建文件** | `frontend/src/types/monitor.ts` |

**内容：**
- `KbHealthLatest` / `KbHealthLogRead`
- `LlmCostDailyRead` / `LlmCostMonthlyRead` / `LlmCostLogRead` / `LlmCostModelBreakdown`
- `RefusalStats` / `AgentRefusalLogRead`
- `CitationQualityLogRead` / `ConsistencyIssueLogRead` / `FactVerificationLogRead`

---

## 操作 6-12：新增前端状态管理（已在上文 6-3 覆盖）

---

## 阶段 6 自测

| 测试项 | 结果 | 说明 |
|--------|------|------|
| `vue-tsc` 类型检查 | ⏸️ 待执行 | 验证所有新增组件/API/Store 类型正确 |
| `vite build` 构建 | ⏸️ 待执行 | 验证无编译错误 |
| 全量 import 验证 | ⏸️ 待执行 | 验证所有新增文件可正常导入 |
| ChatView 三栏布局渲染 | ⏸️ 待执行 | 启动 dev server 人工验证 |
| askAgent 接口调用 | ⏸️ 待执行 | 需后端运行，输入问题验证完整响应渲染 |
| MonitorView 三 Tab 切换 | ⏸️ 待执行 | 需后端运行，验证监控数据展示 |
| AdminLayout 菜单 | ⏸️ 待执行 | 验证「监控中心」入口正确 |

**自测命令：**
```bash
cd frontend
# 1. 类型检查
npx vue-tsc -b --noEmit

# 2. 构建
npm run build

# 3. 启动 dev server（需后端同时运行）
npm run dev
```

---

## 阶段 6 验收

| 优化项 | 状态 | 备注 |
|--------|------|------|
| 扩展 `types/chat.ts` | ✅ | AgentAskResult + ChatMessage 增强字段 |
| 新增 `api/monitor.ts` | ✅ | 8 个 API 函数 |
| 更新 `api/chat.ts` | ✅ | askAgent + getMessageReferences |
| 新增 `stores/monitor.ts` | ✅ | 3 个摘要状态 + refreshDashboardCards |
| 新增 `SearchBox.vue` | ✅ | AI 问答 / 纯检索切换 |
| 新增 `ConfidenceBadge.vue` | ✅ | 高/中/低置信度标签 |
| 新增 `TemporalWarning.vue` | ✅ | 时效性警告横幅 |
| 新增 `RefusalMessage.vue` | ✅ | 拒答提示 |
| 新增 `StatsOverview.vue` | ✅ | 统计概览卡片 |
| 新增 `HotQuestions.vue` | ✅ | 热门问题排行榜 |
| 新增 `KbHealthCard.vue` | ✅ | 知识库健康度卡片 |
| 新增 `LlmCostCard.vue` | ✅ | LLM 成本卡片 |
| 新增 `RefusalStatsCard.vue` | ✅ | 拒答统计卡片 |
| 新增 `DashboardPanels.vue` | ✅ | 左侧面板容器 |
| 重构 `ChatView.vue` | ✅ | 三栏深空蓝科技风布局 |
| 更新 `stores/chat.ts` | ✅ | sendAgent 对接 askAgent |
| 更新 `MessageItem.vue` | ✅ | 渲染 Agent 增强字段 |
| 新建 `MonitorView.vue` | ✅ | 三 Tab 监控中心 |
| 注册 monitor 路由 | ✅ | `/admin/monitor` |
| 更新 `AdminLayout.vue` | ✅ | 监控菜单入口 |
| 新建 `types/monitor.ts` | ✅ | 监控模块类型定义 |
| 自测 | ⏸️ | 待执行 |

---

## 下一阶段预告

| 阶段 | 内容 | 依赖 |
|------|------|------|
| **阶段 7** | 集成测试 + 灰度 | 阶段 6 完成（当前阶段） |

---

## 踩坑记录

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| `LlmCostCard.vue` v-for key | `:key="{m.model}"` 语法错误（对象字面量） | 改为 `:key="m.model"` |
| `RefusalStatsCard.vue` v-for key | 同上 | 改为 `:key="item.risk_level"` |
| `chat.ts` 类型导出 | `AskResult` / `AgentAskResult` 未导出给 store 使用 | 补充 `export` 关键字 |
| `chat.ts` import 类型 | 新增 `Reference` 类型导入 | `import type { AgentAskResult, ChatMessage, Message, Reference }` |
| `docs/README.md` 编码问题 | 文件含 BOM/中文特殊字符导致 sed 无法匹配 | 使用 Write 完整重写文件 |
| `monitor.ts` import 顺序 | `PageResult` 需从 `@/types/api` 导入 | 拆分 import 语句 |
| `ChatView.vue` 右侧面板条件 | 非 admin/editor 用户不应看到右侧面板 | 用 `v-if="isAdminOrEditor"` 控制 |
| `ChatView.vue` 搜索框双份 | welcome 和 messages 两个区域都需要 SearchBox | 用 `v-if="showSearch"` 控制显示 |
