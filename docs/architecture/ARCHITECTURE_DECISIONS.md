# 架构决策记录（ADR）

> 本文提炼项目关键架构决策的「何时 / 为何」，按主题组织。来源标注到 `docs/progress/phase-*.md` 等原始文档；冲突处以 `[待确认]` 标记。原始阶段日志原位保留在 [docs/progress/](../progress/)。
> **最后更新**：2026-07-02（阶段 11 完成，确认多智能体评估结论）

---

## 决策总览

| 决策 | 结论 | 引入/冻结 |
|---|---|---|
| 检索架构 | 单路向量检索（ChromaDB）+ 时效性调整，**不引入** BM25/Neo4j/ES/Cohere Rerank | 设计期选型变更 |
| 智能体形态 | **单智能体 + 固定流水线 LangGraph**，非多智能体 | Phase 1 落地 → Phase 10 正式评估（已确认无需多智能体） |
| 外部检索 | 通过 **MCP 调用外部托管服务**（Bing 搜索、网页抓取） | Phase 7 |
| 幻觉防御 | 五重防护（动态阈值 / 引用强制 / 一致性 / 事实核验 / 内容审核） | Phase 1 构建 → Phase 2 集成 |
| 监控 | 定时聚合（KB 健康 / LLM 成本 / 引用质量 / 拒答统计），日志告警 | Phase 3 → Phase 5 暴露 HTTP |
| 工具/业务分层 | **三层定位法**：对话推理→graph 节点；我方确定性业务→service+REST；外部能力→MCP | 2026-06-28 冻结 |

---

## 1. 检索：为何是「ChromaDB 单路向量 + 时效调整」

设计文档最初规划完整混合检索（Vector + BM25 + 知识图谱 + RRF 融合 + Rerank，底层 ChromaDB+ES+Neo4j），但**实际选型变更**为 ChromaDB 本地嵌入式向量检索 + 自定义时效性调整，明确不使用 LlamaIndex / BM25 / Cohere Rerank / Elasticsearch。

**理由**：复用既有 ChromaDB 基础设施；就业政策问答数据量适中；减少外部依赖与运维；语义缓存（Redis）已覆盖性能；时效性调整可直接叠加在检索结果上。

实际链路：FAQ 快速命中（cosine≥0.75）→ 语义缓存（Redis，余弦>0.92）→ ChromaDB `kb_chunks` 向量检索（top_k=5，score_threshold=0.4）→ 时效性调整 → chunk 级引用构建。

来源：`Agent模块设计文档.md`(§六、§6)、`phase-1-agent-core.md`、`phase-0-environment.md`。

> `[待确认]` 综合得分排序 `similarity×0.7+temporal×0.3` 与「句子级引用」在设计文档中描述为已实现，但 `phase-2` 与 `project-assessment.md` 明确实际为 V1 简化版（仅过滤/标记过期、chunk 级、基于检索得分统计）。设计文档=目标态。
>
> `[待确认]` Rerank：设计文档称以时效调整替代、不实现；`project-assessment.md` 仍将其列为长期待办。当前未实现。

---

## 2. 智能体：为何保持「单智能体 + 固定流水线」

这是贯穿 Phase 8/9/10 的显式决策，并建立了量化触发条件。

**多智能体触发阈值**（任一触发才考虑）：①3+ 个独立子流程；②Agent 间需状态隔离；③不同 Agent 需不同模型；④工具数 > 8；⑤单 Prompt > 4k tokens。

**Phase 10 正式评估**：5 项检查点全部未触发 → 结论「无需引入多智能体，继续单 Agent」。Phase 11 据此定调「单 Agent + REST API 层」，复杂业务域通过工具扩展或纯 REST 实现。

**实现形态**：单图固定流水线（见 [graph.py](../../backend/app/agent/graph.py)）：
`route → search → check_confidence → generate → check_consistency → verify_facts → [content_moderation | accept | accept_with_warning | refuse] → error_handler → END`。

其中 `verify_facts` 后已改为三阶段自校正闭环：
- `accept` → `content_moderation` → 最终输出
- `regenerate` → `regenerate_with_hints` → 未超限回到 `verify_facts`，超限熔断到 `content_moderation`
- `refuse` → `refuse` → `error_handler` → END

注意：这不是 ReAct 工具调用智能体——LLM 不自主选工具，流程由边写死，意图分类仅用于站点白名单等分支。

来源：`implementation/multi-agent-architecture.md`、`phase-10.md`、`phase-8.md`、`phase-11.md`。

> 设计文档 §2.1 画有 `Supervisor→Router→Executor→Responder` 多智能体拓扑，属设计愿景，非实现态。

---

## 3. MCP：为何引入、用在何处

- **时机**：Phase 7（外部检索兜底）——本地知识库无结果/置信不足时 fallback 到外部检索。
- **为何 MCP**：原计划用 NewsAPI，但免费版限制大（仅近 30 天、每小时 100 次）→ 迁移到 **Bing MCP**，无此限制。
- **用在两项能力**，均指向**外部托管 MCP 服务**（URL 配置 `bing_search_url` / `fetch_url`，当前指向 `mcp.api-inference.modelscope.net`）：
  - `bing_search` —— 外部 Bing 搜索 MCP，支持按意图走站点白名单（政务站 / 招聘站）。
  - `fetch_webpage` —— 外部 Fetch MCP，抓取网页正文。
- 工程化：MCP 工具名跨提供方不一致，用 `find_tool()` 多候选匹配；fetch 超时降级用 snippet。

来源：`phase-7-web-search-fallback.md`、`phase-9.md`。

---

## 4. 幻觉防御 / 引用评估 / 拒答

| 能力 | 引入 | 解决的问题 |
|---|---|---|
| 五重防护 | Phase 1 构建 → Phase 2 集成 | 抑制 LLM 幻觉 |
| ①动态置信阈值 | Phase 1 | 按风险分级阈值，重试每次 −0.15、保底 0.30、最多 3 次后降级 |
| ③自我一致性 | Phase 1（V1 关键词矛盾） | 检测回答内部明显矛盾 |
| ④事实核验 | Phase 1（regex）→ Phase 8 增强 | 政策编号/日期/金额提取；校验是否被引用支持 |
| ⑤内容审核 | Phase 1 | 输出侧违规过滤 |
| 引用追踪 CitationEvaluator | Phase 2（V1）→ Phase 3 落库 | chunk 级引用 + 质量统计（direct/indirect/none），写 `citation_quality_log` |
| 拒答 refusal_handler | Phase 2（6 模板，V1 不调 LLM） | 无结果/低置信/违规/冲突时返回结构化拒答 |

来源：`phase-1`、`phase-2`、`phase-3`、`phase-8`、`project-assessment.md`。

> `[已解决]` 拒答落库：`AgentRefusalLog` 模型已定义，`routers/refusal.py` 提供 `/refusal/list` 和 `/refusal/stats` 查询接口。当前工作流通过 `generate_refusal` 节点返回结构化拒答（含 reason/route/confidence），前端 `RefusalMessage` 组件展示；如需持久化拒绝记录，可在 `nodes.py` 的 `generate_refusal` 节点增加 `db.add(AgentRefusalLog(...))`。

---

## 5. 监控

引入于 Phase 3（APScheduler 定时聚合），Phase 5 补 HTTP 路由暴露。

| 监控项 | 口径 | 落库表 |
|---|---|---|
| KB 健康度 | `freshness=exp(−0.693×days/half_life)`，过期×0.1，`health_score=均值×100`（半衰期默认 180 天） | `kb_health_log` |
| LLM 成本 | 从 `QaMessage.prompt/completion_tokens` 按天+模型聚合 + 参考单价；日阈值 $10、月 $300，日志告警（V1 不接 LangSmith API） | `llm_cost_log` |
| 引用质量 | direct/indirect/none 计数 + quality_score | `citation_quality_log` |
| 拒答统计 | 总数/今日/按原因/按风险 | `agent_refusal_log` |

来源：`phase-3-monitoring.md`、`phase-5-routing-schema.md`、`bugfixes.md`。

> `[已解决]` 定时任务数：4 个 cron job（`monitor/scheduler.py`）：
> - 02:00 KB 健康度（`health_monitor.run_daily_check`）
> - 02:15 引用质量（`citation_evaluator.evaluate_and_log`）
> - 02:30 LLM 成本（`cost_monitor.run_daily_check`）
> - 02:45 一致性检查（`consistency_checker`，代码不存在但 scheduler 已注册 cron，需确认实现）

---

## 6. 工具与业务分层：三层定位法（2026-06-28 冻结）

### 背景
Phase 9 在 `tools.py` 的 `TOOLS` 注册表中新增了 5 个「业务工具」（`generate_resume` / `recommend_jobs` / `toggle_faq_status` / `add_calendar_event` / `fetch_announcement`）。代码审查发现：
- `TOOLS` 注册表**无任何代码消费**；nodes.py 仅 import `knowledge_search / bing_search / fetch_webpage`。
- 其中 4 个工具是**完全未接线的死代码**；`generate_resume` 直接调 LLM、`recommend_jobs` 直接调 RAG，绕过监控/引用链路。
- 原计划（拆 3 个本地 MCP server 8101/8102/8103）属反向过度工程：把我方 DB/文件上的确定性操作经 HTTP/JSON-RPC 跳到另一本地进程再 import 同一 service，MCP 的隔离/复用/伸缩价值均不适用。

### 决策：按能力性质三层定位
| 能力性质 | 归位 | 示例 |
|---|---|---|
| 对话式推理 | `app/agent/nodes.py` 图节点 | route / search / generate / verify |
| 我方 DB/文件上的确定性业务操作 | `app/services/*_service.py` + REST 端点 | 简历生成、职位推荐、面试日历 |
| 真·外部第三方能力且需隔离 | `tools.py` 经 `_MCPClient` 调**外部** MCP server | bing_search、fetch_webpage |

### 落地
- `tools.py` 瘦身：删 `TOOLS` 注册表 + 4 个死函数；`fetch_announcement` 收编进 `announcement_service.get_active_config_announcements`；文件头加架构约束注释。agent 工具回归为 `knowledge_search`（进程内 RAG）+ `bing_search` / `fetch_webpage`（外部 MCP）。
- resume / jobs / calendar 改为 service + REST（`/career/resume`、`/career/jobs`、`/career/calendar/ics`），前端 `/student/resume`、`/student/jobs` 直接调用。LLM 用量经 `llm_usage.log_feature_usage` 审计。
- **放弃**自建本地 MCP server；MCP 仅用于外部能力。

### 黄金法则（取代「新功能必先做成 MCP server」）
新增能力先判性质：**对话推理→graph 节点；我方确定性业务→service+REST；外部第三方且需隔离→外部 MCP**。严禁在 `tools.py` 写业务逻辑，或在 nodes.py 硬编码新的一次性 LLM 调用。

> `[已解决]` 特性级 LLM 用量：`services/llm_usage.py` 的 `log_feature_usage()` 已在简历生成等非对话调用中落地，写入 `llm_usage` 流水表。`cost_monitor.run_daily_check` 在每日聚合时按 (model, source) 汇总进 `llm_cost_log`，与 Agent 对话成本（source=agent_chat）在同一看板融合。 
