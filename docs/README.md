# 高校智慧就业服务平台 — 文档中心

> **最后更新**：2026-07-02
> **当前阶段**：阶段 11 完成（Batch A/B），Batch C 待规划

---

## 架构师快速阅读路径（70 分钟全貌）

```
30 分钟：本索引 → CURRENT_CAPABILITIES → ARCHITECTURE_DECISIONS
30 分钟：phase-11（最新工作）→ phase-10（多智能体结论）→ phase-9（工具/意图分类）
10 分钟：implementation/README 阶段总览表（技术栈 + 时间线）
```

### 三视角理解项目

| 视角 | 文档 | 回答的问题 |
|------|------|-----------|
| **设计决策** | [architecture/ARCHITECTURE_DECISIONS.md](./architecture/ARCHITECTURE_DECISIONS.md) | 为什么用 ChromaDB？为什么是单 Agent？三层定位法是什么？ |
| **当前能力** | [modules/CURRENT_CAPABILITIES.md](./modules/CURRENT_CAPABILITIES.md) | 系统现在能做什么？有哪些 API 端点？前端页面有哪些？ |
| **实施进度** | [progress/phase-11.md](./progress/phase-11.md) | 最新做了什么？Batch C 规划是什么？ |

---

## 文档导航

### 核心文档（必读）

| 文档 | 用途 | 适合场景 |
|------|------|----------|
| [README.md](./README.md) | 本文件：总索引 + 阅读指南 | 入口 |
| [architecture/ARCHITECTURE_DECISIONS.md](./architecture/ARCHITECTURE_DECISIONS.md) | 关键 ADR：检索选型、单 Agent 决策、三层定位法 | 架构评审、技术选型 |
| [modules/CURRENT_CAPABILITIES.md](./modules/CURRENT_CAPABILITIES.md) | 当前系统真实能力清单（端点、页面、组件） | 开发接入、能力核实 |
| [implementation/README.md](./implementation/README.md) | 阶段总览 + 技术栈实际状态 | 了解项目演进 |
| [progress/README.md](./progress/README.md) | 12 个阶段的完成状态总览 | 进度跟踪 |
| [progress/phase-10.md](./progress/phase-10.md) | 多智能体触发评估（5 检查点 + 触发信号清单） | 未来扩展决策 |
| [progress/phase-11.md](./progress/phase-11.md) | 复杂业务域开发（Batch A/B 完成，Batch C 待规划） | 最新进展 |

### 开发参考

| 文档 | 用途 |
|------|------|
| [implementation/module-reference.md](./implementation/module-reference.md) | 模块文件清单 + 职责（开发时查阅） |
| [implementation/migration.md](./implementation/migration.md) | 数据库迁移脚本（DBA / 部署需要） |

### 产品层

| 文档 | 用途 |
|------|------|
| [产品介绍文档.md](./产品介绍文档.md) | 非技术读者理解系统功能与价值 |

### 归档区（历史参考，不再更新）

> `docs/archive/` 包含已被取代或过时的文档，Git history 可追溯。

| 归档文档 | 原位置 | 归档原因 |
|----------|--------|----------|
| Agent模块融合实施方案.md | docs/ | 原始大文档，内容已分散到 implementation/ + progress/ |
| 功能模块实现文档.md | docs/ | 原始大文档，内容已提取为 module-reference.md + migration.md |
| 前端实施方案.md | docs/ | 前端规划，已被 phase-6-frontend.md + 实际代码覆盖 |
| implementation-steps.md | implementation/ | 与 progress/ 高度重复，已精简为 Batch C 规划 |
| missing-frontend-pages.md | implementation/ | 2026-06-26 快照，大部分页面已补齐 |
| multi-agent-architecture.md | implementation/ | 设计愿景，核心结论已沉淀到 ADR |
| bugfixes.md | progress/ | 历史 bug 修复记录，已融入各 phase 文档 |
| project-assessment.md | progress/ | 2026-06-26 评估，大部分问题已在后续阶段修复 |
| phase-0-environment.md ~ phase-9.md | progress/ | 历史阶段记录，phase-10/11 是最新的 |

---

## 增量优化与阶段里程碑

| 优化/阶段 | 说明 | 时间 |
|-----------|------|------|
| Bing 分级 fallback | 按意图切换站点白名单，Bing + fetch 抓取正文 | 阶段 7 |
| 前端传历史消息 | ChatStore 传最近 6 轮，check_consistency 跨轮矛盾检测 | 阶段 6/7 |
| 前端展示 fact_issues / warnings | MessageItem 事实核验/时效警告提示区 | 阶段 6/7 |
| Graph 编译缓存 | AgentGraph.compile() 单例 | 阶段 6 |
| ChatInput 终止按钮 + AbortController | 请求中显示终止，Enter 触发 cancel | 阶段 6 |
| SearchBox 纯检索模式 | 切换调用 POST /search，命中片段以助手消息展示 | 阶段 6 |
| MonitorView 扩展 | 月度成本选择器 + 手动 KB 健康检查 | 阶段 6 |
| AgentState TypedDict 标准化 | 修复 Annotated[dict] 误用 | 阶段 8 |
| verify_facts 基础验证 | 提取事实要素检查是否被引用内容支持 | 阶段 8 |
| 14 个单元测试 | pytest + SQLite 内存 DB，100% 通过率 | 阶段 8 |
| 5→3 个 Agent 工具（去债务） | 删 toggle_faq_status / generate_resume / recommend_jobs / add_calendar_event 死代码 | 阶段 9 |
| 9 类意图分类 | policy/faq/document/news/resume/interview/salary + 兜底 | 阶段 9 |
| 多智能体评估 | 5 检查点全未触发 → 无需多 Agent | 阶段 10 |
| Batch A 收藏 + 公告 | UserFavorite / Announcement 前后端 CRUD | 阶段 11 |
| Batch B 系统设置 + QA 配置 + 对话管理 | SettingsView / QaConfigView / ConversationsView | 阶段 11 |

---

## 按角色阅读

### 我是架构师
1. 阅读 [架构决策](./architecture/ARCHITECTURE_DECISIONS.md)（30 分钟）
2. 浏览 [能力清单](./modules/CURRENT_CAPABILITIES.md)（15 分钟）
3. 阅读 [phase-11](./progress/phase-11.md) + [phase-10](./progress/phase-10.md)（30 分钟）

### 我是开发工程师（新加入）
1. 阅读 [实施总览](./implementation/README.md) 阶段总览表（10 分钟）
2. 查阅 [模块速查](./implementation/module-reference.md)（按需）
3. 按需阅读对应 [progress/phase-*.md](./progress/)

### 我是 DBA
1. 阅读 [迁移文档](./implementation/migration.md)
2. 查阅 [progress/README.md](./progress/README.md) 确认迁移已执行

### 我是产品经理
1. 阅读 [产品介绍文档.md](./产品介绍文档.md)
2. 浏览 [CURRENT_CAPABILITIES.md](./modules/CURRENT_CAPABILITIES.md) 了解系统边界

---

## 文档维护规范

- **活跃文档**：README.md、ARCHITECTURE_DECISIONS.md、CURRENT_CAPABILITIES.md、progress/phase-10.md、progress/phase-11.md
- **只读参考**：implementation/module-reference.md、implementation/migration.md、progress/README.md
- **归档文档**：`docs/archive/` 下所有文件，不再维护但保留可追溯
- **新增文档**：如需新增 phase 文档，放在 `progress/` 下；如为设计决策，追加到 `architecture/ARCHITECTURE_DECISIONS.md`
