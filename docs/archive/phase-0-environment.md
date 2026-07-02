# 项目进度追踪

> 项目：高校智慧就业服务平台 — RAG + Agent 融合开发
> 创建时间：2026-06-23
> 最后更新：2026-06-26
> 关联文档：[Agent模块融合实施方案](./Agent模块融合实施方案.md) · [功能模块实现文档](./功能模块实现文档.md) · [产品介绍文档](./产品介绍文档.md)

---

## 进度概览

| 阶段 | 状态 | 开始时间 | 完成时间 | 备注 |
|------|------|----------|----------|------|
| 阶段 0：环境准备 | ✅ 完成 | 2026-06-23 | 2026-06-23 | Alembic+3迁移(24表)/Embedding三级缓存/LangSmith全局，详见文末权威记录 |
| 阶段 1：Agent 核心构建 | ✅ 完成 | 2026-06-24 | 2026-06-24 | P0 骨架 + P1 持久化/缓存/跑通 + Docker 部署文件，默认 agent_enabled=true（测试环境） |
| 阶段 2：幻觉防御集成 | ✅ 完成 | 2026-06-25 | 2026-06-25 | 动态阈值/一致性/事实核验/拒答模板/引用追踪/时效感知检索集成到节点流程 |
| 阶段 3：监控告警模块 | ✅ 完成 | 2026-06-25 | 2026-06-25 | 知识库健康度监控 + LLM 成本监控 + 引用质量评估 + APScheduler 定时任务 |
| 阶段 4：问答服务升级 | ✅ 完成 | 2026-06-25 | 2026-06-25 | qa_service.agent_chat() 集成 Agent 工作流 + routers/qa.py 新增 /ask/agent 端点 |
| 阶段 5：路由 + Schema | ✅ 完成 | 2026-06-25 | 2026-06-25 | schemas 抽离 + 3 个监控路由（kb_health/llm_cost/refusal）+ qa.py 响应对齐 |
| 阶段 6：前端对接 | ✅ 完成 | 2026-06-25 | 2026-06-26 | 三栏布局 + Agent 组件 + 监控中心 + 样式升级 + bugfixes |
| 阶段 7：外部检索兜底 | ✅ 完成 | 2026-06-26 | 2026-06-26 | NewsAPI fallback + 引用溯源 + 前端 web 来源展示 |

---

## 操作日志

### Phase 0 — 环境准备（2026-06-23）

#### 操作 0-1：更新 requirements.txt

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-23 |
| **模块** | 阶段0 / 依赖管理 |
| **修改文件** | `backend/requirements.txt` |
| **操作** | 追加 4 个新依赖包 |

**新增依赖：**

| 包名 | 版本要求 | 作用 | 调试说明 |
|------|----------|------|----------|
| `langgraph` | `>=0.1.0` | Agent 状态机工作流核心框架 | 安装后在 Python 中 `import langgraph` 验证；工作流编译后可打印 `.graph.nodes` 查看节点拓扑 |
| `langgraph-checkpoint` | `>=0.1.0` | LangGraph Checkpoint 存储后端 | 与 `MemorySaver` 配合使用，支持对话暂停/恢复；调试时检查 checkpoint 文件是否写入 |
| `langsmith` | `>=0.1.0` | LLM 调用追踪 + Prompt 版本管理 | 配置 `LANGCHAIN_API_KEY` 后可在 LangSmith Dashboard 查看调用链；未配置则自动跳过（优雅降级） |
| `apscheduler` | `>=3.10.0` | 定时任务（健康检查、成本月报） | 启动后查看日志确认 `kb_health_check` 和 `kb_weekly_report` job 是否注册成功 |

**验证命令：**
```bash
cd backend
pip install -r requirements.txt
python -c "import langgraph; import langsmith; import apscheduler; print('OK')"
```

**后续可能的问题：**
- `langgraph` API 版本变化可能导致节点/边 API 不兼容 → 固定版本号 + 查看 changelog
- `langsmith` SDK 初始化可能依赖 `LANGCHAIN_API_KEY` 环境变量 → 未配置时需捕获异常降级
- `apscheduler` 在 Windows 上使用 `threading` 或 `asyncio` 调度器 → 避免使用 `fork` 调度器

---

#### 操作 0-2：创建数据库迁移脚本

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-23 |
| **模块** | 阶段0 / 数据库 |
| **新建文件** | `backend/migrations/add_agent_tables.py` |
| **操作** | 创建数据库迁移脚本，新增 6 张监控表 + 修改 qa_message 表 |

**新增表清单：**

| 表名 | 用途 | 关键字段 | 调试/验证方法 |
|------|------|----------|---------------|
| `agent_refusal_log` | 拒答记录 | query, refusal_reason, confidence, created_at | 插入测试数据，查询确认写入 |
| `citation_quality_log` | 引用质量评估日志 | message_id, quality_score, direct_count, indirect_count, none_count, created_at | 检查评分计算是否正确 |
| `kb_health_log` | 知识库健康度日志 | check_date, health_score, warning_docs, expired_docs, total_docs | 每日检查后查看是否写入 |
| `llm_cost_log` | LLM 成本消耗日志 | check_date, daily_cost, monthly_cost, token_count, created_at | 对比 LangSmith Dashboard 数据 |
| `consistency_issue_log` | 一致性问题日志 | message_id, issue_type, severity, description, created_at | 模拟一致性检查触发 |
| `fact_verification_log` | 事实核验日志 | message_id, fact_type, extracted_value, validation_result, created_at | 发送含政策编号的查询，确认日志 |

**修改表清单：**

| 表名 | 新增字段 | 字段类型 | 说明 |
|------|----------|----------|------|
| `qa_message` | `confidence` | DECIMAL(5,4) | 综合置信度 |
| `qa_message` | `query_risk_level` | VARCHAR(20) | 查询风险等级 (high/medium/low) |

**执行方式：**
```bash
cd backend
python -c "from migrations.add_agent_tables import migrate; migrate()"
```

**验证方法：**
- 执行后连接 MySQL，执行 `SHOW TABLES LIKE 'agent_%'` 确认 6 张新表存在
- 执行 `DESC qa_message` 确认 confidence 和 query_risk_level 字段已添加

---

## 后续阶段详细计划

> 每个阶段开始前，会在此文档中追加该阶段的具体操作日志。

### 阶段 1 预备信息：Agent 核心构建

| 顺序 | 新建文件 | 修改文件 | 核心内容 |
|------|----------|----------|----------|
| 1.1 | `agent/__init__.py` | — | 模块初始化 |
| 1.2 | `agent/state.py` | — | AgentState TypedDict 定义 |
| 1.3 | `agent/nodes.py` | — | route/search/check_confidence/generate/check_consistency/verify_facts/generate_refusal 节点 |
| 1.4 | `agent/tools.py` | — | knowledge_search 工具 |
| 1.5 | `agent/graph.py` | — | StateGraph 工作流构建 |
| 1.6 | `agent/hallucination_defense.py` | — | 五重防护（动态阈值/一致性/事实核验） |
| 1.7 | `agent/citation_tracker.py` | — | 句子级别引用追踪 |
| 1.8 | `agent/temporal_retriever.py` | — | 时效感知检索 |
| 1.9 | `agent/refusal_handler.py` | — | 拒答模板 |
| — | `routers/agent.py` | — | /agent/chat 接口 |
| — | — | `main.py` | 注册 agent 路由 |

### 阶段 2-7 规划

各阶段的详细文件清单和操作记录将在推进时逐阶段追加到本文件。

---

## 已知风险与待确认事项

| 风险/问题 | 状态 | 说明 |
|-----------|------|------|
| Redis 可用性 | ✅ 已处理 | 本机未装 Redis；代码 Redis-ready，自动降级到 内存+MySQL，不影响功能 |
| langgraph API 兼容性 | ⚠️ 注意 | 实际安装 1.2.6（已内置 checkpoint）；固定大版本，关注 changelog |
| LangSmith API Key | ✅ 已处理 | 从环境变量 `LANGSMITH_API_KEY` 读取，凭证校验通过，project=myproject |
| 迁移方式选择 | ✅ 已定 | 采用 **Alembic**，脚本输出到 `backend/migrations/` |

---

## 阶段 0 实际执行记录（权威版，2026-06-23）

> ⚠️ 本节为阶段 0 的**最终实际执行结果**，与上方"操作 0-1 / 0-2"的早期规划存在差异时，**以本节为准**。
> 主要差异：① 迁移改用 Alembic（非手写 add_agent_tables.py）；② `langgraph-checkpoint` 未单装（1.2 已内置）；
> ③ qa_message 一次加 5 个字段（非 2 个）；④ 新增 Embedding 三级缓存 + embedding_cache 表；⑤ LangSmith 已全局配置。

### 0.1 依赖（`backend/requirements.txt`）

实际安装版本：`langgraph 1.2.6`、`langsmith`、`apscheduler 3.11.2`、`alembic 1.18.4`、`redis 8.0.0`。
**`langgraph-checkpoint` 未单独安装**——LangGraph 1.2 已内置 checkpoint。

调试：`cd backend && .venv/Scripts/python.exe -c "import langgraph,apscheduler,alembic,redis,langsmith; print('OK')"`

### 0.2 Alembic 迁移环境

- 环境配置在 `backend/alembic/`；版本脚本输出到 `backend/migrations/`（由 `alembic.ini` 的 `version_locations` 指定）。
- `alembic/env.py`：用 `settings.database_url` 动态注入连接串（不在 ini 存密码），绑定 `Base.metadata`。
- **编码坑**：Windows 上 configparser 用 GBK 读 `alembic.ini`，含中文必崩 → `alembic.ini` 只保留纯英文，中文说明写进 `env.py`。
- **前置条件**：`MySQL84` 服务需启动（`net start MySQL84`）。

调试：`.venv/Scripts/python.exe -m alembic current` / `... history`

### 0.3 三个迁移版本（当前 head = `65a7e09c9884`）

| 版本 | 内容 |
|------|------|
| `83dc52f295f1` | 基线空迁移（stamp 现有 17 表为起点，不执行 DDL） |
| `be1122c3c9a7` | 6 张监控日志表 + qa_message 加 5 字段 |
| `65a7e09c9884` | embedding_cache 缓存表（embedding 列用 LONGTEXT 精确往返） |

**6 张监控表**（写多读少，最终决定存 MySQL 而非 MongoDB）：`kb_health_log`、`llm_cost_log`、`agent_refusal_log`、`citation_quality_log`、`consistency_issue_log`、`fact_verification_log`。

**qa_message 新增 5 字段**：`confidence`(DECIMAL5,4)、`query_risk_level`(VARCHAR20)、`consistency_issues`(JSON)、`fact_issues`(JSON)、`temporal_warnings`(JSON)。

调试：`.venv/Scripts/python.exe -m alembic upgrade head` / `downgrade -1`；当前共 24 张表。

### 0.4 Embedding 三级缓存（方案 B）

链路 `L1内存LRU → L2 Redis(24h) → L3 MySQL(embedding_cache) → DashScope API`，逐层回填，任意层不可用透传降级。**仅缓存 `embed_query`**（查询/FAQ 高复用），`embed_texts` 建索引不缓存。

| 文件 | 作用 |
|------|------|
| `app/core/redis_client.py` 【新增】 | Redis 懒连接 + 失败熔断降级（30s 冷却） |
| `app/core/embedding_cache.py` 【新增】 | 三级缓存 `get`/`put`，key=SHA256(text\|model\|dim) |
| `app/core/embedding.py` 【改】 | `embed_query` 接入缓存；全零兜底向量不缓存 |
| `app/core/config.py` / `.env` 【改】 | Redis + 缓存配置项 |

关键点：`embedding` 列用 **LONGTEXT**（非原生 JSON），避免 double 归一化的 1-ULP 偏差，bit 级精确往返。

调试：见 §0.4 自测脚本（无 Redis 也应 4 步全 True）。

### 0.5 LangSmith 全局追踪

| 文件 | 作用 |
|------|------|
| `app/core/langsmith_setup.py` 【新增】 | `setup_langsmith()` 导出 `LANGSMITH_*`/`LANGCHAIN_*` 环境变量 |
| `app/main.py` 【改】 | 启动时调用，全局生效 |
| `app/core/config.py` / `.env` 【改】 | `LANGSMITH_ENABLED/PROJECT(myproject)/ENDPOINT`；Key 走环境变量 |

凭证已校验通过（`list_projects` 成功）。阶段1 的 `@traceable` 节点将自动上报到 LangSmith `myproject`。

### 阶段 0 验收

- [x] 依赖安装成功　- [x] Alembic 就绪，迁移到 `65a7e09c9884`（24 表）　- [x] qa_message 5 字段
- [x] 三级缓存可用，无 Redis 正确降级，精确往返　- [x] LangSmith 全局生效，凭证有效　- [x] `app.main:app` 构建无报错

**遗留**：本机未装 Redis（降级运行，不影响功能）；MySQL84 为本次启动、非开机自启。

---
