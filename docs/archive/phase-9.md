# 阶段 9 进度追踪：单智能体扩展期

> **目标**：在不改变单智能体架构的前提下，通过新增工具扩展能力
> **前置条件**：阶段 8 完成
> **开始时间**：2026-06-27

---

## 操作记录

### 操作 9-1：创建 announcements.json 配置文件

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **新建文件** | `backend/data/announcements.json` |
| **说明** | 公告数据以 JSON 配置文件形式存放，包含 title/content/priority/effective_time/expire_time/status 字段 |
| **降级策略** | `fetch_announcement` 工具读取 JSON，文件损坏/不存在时降级返回空列表，不阻塞 Agent 流程 |
| **过滤逻辑** | 自动过滤当前时间不在 [effective_time, expire_time] 区间内的公告 |

**初始公告数据**：
- 2026 届毕业生就业手续办理指南（2026-06-01 至 2026-07-31）
- 校园双选会时间安排（2026-09-01 至 2026-10-31）
- 就业指导中心暑假值班安排（2026-07-01 至 2026-08-31）

---

### 操作 9-2：新增 5 个 Agent 工具

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **修改文件** | `backend/app/agent/tools.py` |
| **新增工具** | `toggle_faq_status` / `generate_resume` / `recommend_jobs` / `add_calendar_event` / `fetch_announcement` |
| **注册方式** | 统一注册到 `TOOLS` 字典，`TOOLS` 从 3 个扩展到 8 个 |

**各工具实现方式**：

| 工具 | 实现方式 | 数据依赖 | 说明 |
|------|---------|---------|------|
| `toggle_faq_status(faq_id, enabled)` | 调用 `ops_service.update_faq_status()` | FAQ 模型（已有） | 切换 FAQ 启用状态 |
| `generate_resume(user_profile, target_job)` | 调用 LLM 生成简历 JSON | 无（纯 LLM） | V1 返回结构化 JSON，不做模板渲染 |
| `recommend_jobs(query, top_k)` | 复用 RAG 检索 `rag_service.search()` | 知识库职位文档 | V1 基于本地知识库，不做外部 API |
| `add_calendar_event(title, start_time, end_time, location, description)` | 生成 ICS 格式字符串 | 无（纯计算） | V1 返回 ICS 内容，前端负责下载 |
| `fetch_announcement(query, max_results)` | 读取 `data/announcements.json` | JSON 配置文件 | 过滤当前生效公告，支持关键词搜索 |

---

### 操作 9-3：意图分类扩展为 9 类

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **修改文件** | `backend/app/agent/constants.py` + `backend/app/agent/nodes.py` |
| **修改前** | 5 类意图：chat / unrelated / kb_query / web_query / job_query |
| **修改后** | 9 类意图：chat / unrelated / policy_query / faq_query / document_query / news_query / resume_query / interview_query / salary_query + 3 个兜底（kb_query / web_query / job_query） |

**意图分类表**：

| 意图 | 关键词示例 | 路由目标 | 风险等级 |
|------|----------|---------|---------|
| chat | 你好、谢谢、再见 | direct_response | low |
| unrelated | 天气、NBA、电影 | generate_refusal | low |
| policy_query | 政策、规定、落户、补贴 | search_knowledge（Bing 政务站） | high |
| faq_query | 常见问题、怎么办理、如何申请 | search_knowledge（FAQ 优先） | medium |
| document_query | 文件、文档、资料、表格 | search_knowledge（文档检索） | medium |
| news_query | 新闻、公告、双选会、宣讲会 | search_knowledge（Bing 新闻）/ fetch_announcement | medium |
| resume_query | 简历、CV、实习经历、技能证书 | search_knowledge + generate_resume 工具 | medium |
| interview_query | 面试、面经、笔试、自我介绍 | search_knowledge + add_calendar_event 工具 | medium |
| salary_query | 薪资、待遇、工资、五险一金 | search_knowledge（薪资类 KB） | medium |
| kb_query | 兜底就业知识 | search_knowledge（本地优先） | medium |

**站点白名单路由更新**：

| intent 组 | 站点白名单 |
|----------|-----------|
| policy_query / web_query / news_query | 政务站点白名单 |
| job_query / resume_query / interview_query / salary_query | 招聘站点白名单 |
| faq_query / document_query / kb_query / chat / unrelated | 无限制 |

---

### 操作 9-4：AgentState 新增字段

| 字段 | 类型 | 用途 |
|------|------|------|
| `resume_data` | `dict` | 简历生成结果（generate_resume 工具输出） |
| `job_recommendations` | `list[dict]` | 职位推荐结果（recommend_jobs 工具输出） |
| `calendar_events` | `list[dict]` | 面试日程数据（add_calendar_event 工具输出） |
| `announcements` | `list[dict]` | 公告列表（fetch_announcement 工具输出） |

---

### 操作 9-5：nodes.py 扩展 direct_response 节点

| 修改内容 | 说明 |
|----------|------|
| `direct_response` 节点增加 intent 判断 | 当 intent == news_query 时，调用 `fetch_announcement` 工具获取当前生效公告 |
| 公告展示格式 | 📢 最新公告：• 标题：内容 |
| 降级处理 | 无公告时返回"暂无相关公告" |

---

### 操作 9-6：前端传历史轮数可配置

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **说明** | 前端传历史轮数保持当前实现（最近 6 轮），后续可通过配置项 `AGENT_HISTORY_TURNS` 调整 |
| **后端变动** | 无（本次阶段完成后端不做改动） |

---

## 阶段 9 验收清单

| 验收项 | 状态 | 说明 |
|--------|------|------|
| 5 个新工具全部注册并可调用 | ✅ | TOOLS 字典 3→8 个，smoke test 通过 |
| 意图分类扩展为 9 类 | ✅ | 9 类意图 + 3 个兜底，route_query 测试通过 |
| AgentState 新增字段不影响现有流程 | ✅ | 新增 4 个可选字段，现有测试全部通过 |
| 前端传历史可配置轮数 | ⏸️ | 前端任务，本次后端不动 |
| 工具调用记录在 reasoning_chain 中 | ✅ | ToolCallTracker 记录在 search_knowledge 节点 |

---

## 测试结果

| 测试文件 | 测试数 | 结果 |
|----------|--------|------|
| `test_agent_workflow.py` | 6 | ✅ 全部通过 |
| `test_agent_workflow_supplement.py` | 7 | ✅ 全部通过 |
| `test_checkpoint_persistence.py` | 1 | ✅ 通过 |
| **合计** | **14** | **14 passed, 100% 通过率** |

---

## 下一步

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 9 | 单智能体扩展期 | ✅ 完成 |
| 阶段 10 | 多智能体触发评估 | ⏸️ 待阶段 9 完成后评估 |
| 阶段 11 | 复杂业务域开发 | ⏸️ 待阶段 10 决策后启动 |

**触发条件检查**：
1. 工具数量：当前 8 个（`knowledge_search` / `bing_search` / `fetch_webpage` / `toggle_faq_status` / `generate_resume` / `recommend_jobs` / `add_calendar_event` / `fetch_announcement`），未超过 8 个阈值
2. Prompt 长度：当前提示词精简，未超过 4k tokens
3. 业务流程差异：各工具仍复用同一工作流，差异不大

**建议**：继续单智能体架构，进入阶段 11 开发复杂业务域。
