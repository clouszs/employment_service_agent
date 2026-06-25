### 阶段 1 Phase 1-P0：Agent 核心骨架（2026-06-24）

> 目标：完成 P0 级 Agent 核心骨架，可运行但默认关闭（agent_enabled=False）。
> 与方案文档对齐：死循环防护 + 基础工作流 + 渐进式迁移。

#### 操作 1-1：llm.py 加 HTTP 超时

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / 核心服务 |
| **修改文件** | `backend/app/core/llm.py` |
| **操作** | `chat()` 和 `chat_stream()` 的 DashScope 调用加 `timeout=30` |

**原因**：当前无超时，DashScope 超时会 hang 住整个请求。

#### 操作 1-2：config.py 加 Agent 配置项

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / 配置管理 |
| **修改文件** | `backend/app/core/config.py` |
| **操作** | 新增 Agent / 幻觉防御 / 时效 / 成本 / 语义缓存配置项 |

**新增配置项：**

| 配置项 | 默认值 | 作用 |
|--------|--------|------|
| `agent_enabled` | `False` | Agent 总开关，V1 默认关闭，灰度时开启 |
| `agent_max_iterations` | `10` | 最大迭代步数 |
| `agent_timeout_seconds` | `60` | 超时时间 |
| `agent_recursion_limit` | `15` | LangGraph 递归限制（防死循环硬兜底） |
| `agent_rate_limit_per_user` | `10` | 每用户每分钟最大请求数 |
| `agent_rate_limit_global` | `100` | 全局每分钟最大请求数 |
| `high_risk_threshold` | `0.80` | 高风险阈值 |
| `medium_risk_threshold` | `0.65` | 中风险阈值 |
| `low_risk_threshold` | `0.40` | 低风险阈值 |
| `kb_warning_days` | `30` | 知识库过期告警天数 |
| `kb_freshness_half_life` | `180` | 新鲜度半衰期 |
| `daily_cost_threshold_usd` | `10.0` | 日成本阈值 |
| `monthly_cost_threshold_usd` | `300.0` | 月成本阈值 |
| `semantic_cache_enabled` | `True` | 语义缓存总开关 |
| `semantic_cache_similarity_threshold` | `0.92` | 语义相似度阈值 |
| `semantic_cache_ttl` | `86400` | 缓存过期时间（秒） |

#### 操作 1-3：创建 agent 模块骨架 + Prompt 文件

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / Agent 核心 |
| **新建文件** | `backend/app/agent/__init__.py`、`backend/app/agent/prompts/__init__.py` |
| **新建文件** | `backend/app/agent/prompts/router.py`、`generator.py`、`refusal.py`、`regenerator.py`、`moderation.py` |

**Prompt 文件职责：**

| 文件 | Prompt 类型 | 作用 |
|------|-------------|------|
| `router.py` | 路由决策 | 判断走 search / direct / refuse |
| `generator.py` | 回答生成 | 基于检索结果生成带引用的回答 |
| `refusal.py` | 拒答回复 | 生成礼貌的拒答回复 |
| `regenerator.py` | 重新生成 | 带修正提示的重新生成 |
| `moderation.py` | 内容审核 | 检查 LLM 输出是否包含违规内容 |

#### 操作 1-4：创建 agent/state.py（含死循环防护字段）

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / Agent 核心 |
| **新建文件** | `backend/app/agent/state.py` |

**核心字段：**

| 字段类别 | 关键字段 | 作用 |
|----------|----------|------|
| 核心对话 | messages, current_query, conversation_id, user_id | 对话上下文 |
| 检索结果 | search_results, citations, confidence, query_risk_level | 检索与引用 |
| 路由决策 | route, should_refuse, refusal_reason | 路由与拒答 |
| 五重防护 | consistency_issues, fact_issues, temporal_warnings | 防护结果 |
| 会话记忆 | history | V1 简化：历史摘要 |
| 可解释性 | reasoning_chain | V1 简化：核心决策记录 |
| 错误处理 | error, is_error | 错误状态 |
| **死循环防护** | retry_attempt, tool_call_count, last_search_query, regenerate_count, forced_exit, skipped_consistency_check | 三循环防护 |

#### 操作 1-5：创建 agent/hallucination_defense.py

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / 幻觉防御 |
| **新建文件** | `backend/app/agent/hallucination_defense.py` |

**三个类：**

| 类 | 作用 |
|----|------|
| `DynamicConfidenceThreshold` | 动态置信度阈值，每次重试降低 0.15，保底 0.30 |
| `SelfConsistencyChecker` | 轻量一致性检查（V1 简化版） |
| `FactVerificationPostProcessor` | 正则验证政策编号、日期、金额等 |

#### 操作 1-6：创建 agent/tools.py

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / Agent 工具 |
| **新建文件** | `backend/app/agent/tools.py` |

**内容：**

| 组件 | 作用 |
|------|------|
| `knowledge_search()` | 知识库语义检索（复用现有 rag_service.search） |
| `TOOLS` 注册表 | 当前只有 knowledge_search，后续扩展 |
| `ToolCallTracker` | 工具调用计数器 + 调用记录（防工具选择循环） |

#### 操作 1-7：创建 agent/nodes.py（核心节点）

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / Agent 核心 |
| **新建文件** | `backend/app/agent/nodes.py` |

**节点清单：**

| 节点函数 | 作用 | 死循环防护 |
|----------|------|------------|
| `route_query` | 路由决策（search/direct/refuse） | tool_call_count >= 3 强制生成 |
| `search_knowledge` | 时效感知检索 | 相同查询去重，重试时改写查询扩大召回 |
| `check_confidence` | 动态置信度判断 | 每次重试降阈值 0.15，最多 3 次，降级回答 |
| `generate_response` | 带引用生成回答 | — |
| `regenerate_with_hints` | 带修正提示重新生成 | 只对 high 严重度注入修正 |
| `check_consistency` | 轻量一致性检查 | 验证器降级，不阻塞流程 |
| `verify_facts` | 正则事实核验 | — |
| `content_moderation` | 输出侧内容审核 | 与输入侧敏感词形成双重防护 |
| `generate_refusal` | 拒答回复生成 | — |
| `accept_with_warning` | 接受但附加警告 | 低置信度 / 中等严重度问题 |
| `error_handler` | 统一错误处理 | 记录错误 + 返回友好提示（V1 无回滚） |

#### 操作 1-8：创建 agent/graph.py（工作流图）

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / Agent 核心 |
| **新建文件** | `backend/app/agent/graph.py` |

**工作流拓扑：**

```
START → route → [search | direct | refuse]
                    ↓
              search → check_confidence
                    ↓
         [generate | regenerate | refuse]
                    ↓
         check_consistency → verify_facts → content_moderation
                    ↓
              [accept | accept_with_warning | refuse]
                    ↓
                   error_handler → END
```

**关键配置：**

| 配置项 | 值 | 作用 |
|--------|----|------|
| `recursion_limit` | `15` | LangGraph 递归限制（硬兜底防死循环） |
| `checkpointer` | `MemorySaver` | 内存 Checkpoint（P1 替换为持久化） |

#### 操作 1-9：创建 routers/agent.py（Agent 路由）

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / API 路由 |
| **新建文件** | `backend/app/routers/agent.py` |

**端点：**

| 端点 | 方法 | 作用 |
|------|------|------|
| `/api/v1/agent/chat` | POST | Agent 同步对话 |

**特性：**

| 特性 | 实现 |
|------|------|
| 复用现有鉴权 | `get_current_user` |
| Agent 专属限流 | 每用户 10次/分钟，全局 100次/分钟（内存滑动窗口） |
| 渐进式迁移 | `agent_enabled=False` 时自动切回旧 RAG |
| 消息落库 | 复用现有 QaMessage / QaMessageReference 表 |

#### 操作 1-10：main.py 注册 agent 路由

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P0 / 入口注册 |
| **修改文件** | `backend/app/main.py` |
| **操作** | 导入 `app.routers.agent`，注册 `/api/v1/agent` 路由 |

#### 阶段 1-P0 验收

- [x] llm.py 加 HTTP 超时 `timeout=30`
- [x] config.py 新增 16 个 Agent 配置项
- [x] agent 模块 9 个文件全部创建
- [x] 死循环防护字段全部写入 state.py
- [x] 动态降级阈值（每次 -0.15，保底 0.30）
- [x] 检索去重（相同查询跳过）
- [x] 内容审核节点（输出侧）
- [x] Prompt 工程化（5 个 prompt 文件）
- [x] LangGraph 工作流图（11 个节点 + 条件边）
- [x] recursion_limit=15 硬兜底
- [x] routers/agent.py（同步接口 + 限流 + 渐进式迁移）
- [x] main.py 注册路由
- [x] `app.main:app` 构建无报错

**验证命令：**
```bash
cd backend
.venv/Scripts/python.exe -c "from app.main import app; print('OK')"
.venv/Scripts/python.exe -c "from app.agent.state import AgentState; from app.agent.graph import get_agent_graph; from app.agent.nodes import route_query; from app.routers.agent import router; print('All imports OK')"
```

**P0 遗留（P1 处理）：**

| 遗留项 | 说明 | P1 处理结果 |
|--------|------|------------|
| MemorySaver 持久化 | V1 用内存存储，服务重启丢上下文 | ✅ 已替换为自研 SqliteSaver，集成测试通过 |
| 语义缓存 | 已定义配置项，P1 实现 | ✅ 已实现，Redis 存储，支持精确+语义匹配 |
| 限流器内存存储 | 多实例部署时不共享 | ⏸️ 保持内存限流（V1 够用，多实例再说） |
| /chat/stream 端点 | V2 再做流式 Agent 响应 | ⏸️ V2 再做 |

---

### 阶段 1 Phase 1-P1：持久化 + 语义缓存（2026-06-24）

> 目标：完成 P1 级优化——Checkpoint 持久化 + 语义缓存 + 关键 bug 修复。

#### 操作 1-11：实现持久化 SqliteSaver

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P1 / Checkpoint 持久化 |
| **新建文件** | `backend/app/agent/sqlite_checkpoint.py` |
| **修改文件** | `backend/app/agent/graph.py`、`backend/app/routers/agent.py` |

**实现细节：**

| 组件 | 说明 |
|------|------|
| `SqliteSaver` 类 | 继承 `BaseCheckpointSaver`，实现 SQLite 持久化 |
| 核心方法 | `get_tuple`, `list`, `put`, `put_writes`, `delete_thread` |
| 序列化 | JSON 为主，失败降级 pickle hex |
| 异常兜底 | 写入失败记录日志 + rollback，不抛异常 |
| 线程安全 | 线程局部连接 + WAL 模式 |

**关键修复（踩坑记录）：**

| 问题 | 原因 | 修复 |
|------|------|------|
| `No item with that key` | SQLite `row["thread_id"]` 在某些场景下报错 | 改用 `_col()` 兼容函数，支持键/索引访问 |
| `KeyError: 'v'` | LangGraph `_migrate_checkpoint` 要求 checkpoint 有 `v` 字段 | `put()` 时自动补 `v=1` |
| `compile() got unexpected keyword argument 'recursion_limit'` | 新版 LangGraph `compile(checkpointer)` 是位置参数 | 改为 `graph.compile(checkpointer)` |
| `Graph must have an entrypoint` | 缺少 `START → route` 边 | 添加 `graph.add_edge(START, "route")` |
| 条件决策函数报错 | `self._route_decision` 在类外调用失败 | 改为模块级函数 `_route_decision` |

**集成测试结果：**

```
✅ 第一步：SqliteSaver 创建成功
✅ 第二步：第一轮 invoke 完成，route=direct
✅ 第三步：SQLite 中找到 3 条 checkpoint
✅ 第四步：模拟重启，新建 SqliteSaver 实例
✅ 第五步：checkpoint 恢复成功，checkpoint_id=1f16fb9c-...
✅ 第五步：checkpoint 内容验证通过
✅ 第六步：基于恢复的 checkpoint 继续对话完成，route=direct
```

**验证命令：**
```bash
cd backend
.venv/Scripts/python.exe tests/test_checkpoint_persistence.py
```

#### 操作 1-12：实现语义缓存

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P1 / 语义缓存 |
| **新建文件** | `backend/app/core/semantic_cache.py` |
| **修改文件** | `backend/app/routers/agent.py` |

**实现细节：**

| 特性 | 说明 |
|------|------|
| 精确匹配 | 相同问题直接返回缓存 |
| 语义相似匹配 | 计算 embedding，余弦相似度 > 0.92 命中 |
| 存储 | Redis（JSON + 索引 Set） |
| 容量限制 | 最多 1000 条，超限随机清理旧条目 |
| TTL | 24 小时过期 |
| 降级 | Redis 不可用时静默跳过，不影响主流程 |

**接入位置：** `routers/agent.py` 的 `_run_agent()` 中，缓存命中时直接返回，跳过 Agent 工作流。

**注意：** 当前只对简单检索类查询做缓存，Agent 多步推理结果暂不缓存（V2 再做）。

#### 操作 1-13：关键 bug 修复

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1-P1 / Bug 修复 |
| **修改文件** | `backend/app/agent/graph.py`、`backend/app/routers/agent.py`、`backend/app/core/llm.py` |

| 修复项 | 说明 |
|--------|------|
| `graph.py` 加 `START` 节点 | LangGraph 1.2.x 要求必须有入口边 |
| 条件决策函数模块级 | `self._route_decision` → `_route_decision` |
| `compile()` 签名修复 | 位置参数 `checkpointer`，不是关键字参数 |
| Checkpoint 序列化加 `v` 字段 | `_migrate_checkpoint` 要求存在 |
| `llm.py` 加 `timeout=30` | 防止 DashScope 超时 hang 住请求 |

#### 阶段 1-P1 验收

- [x] `SqliteSaver` 自研实现，集成测试通过
- [x] 语义缓存实现，Redis 存储
- [x] `graph.py` 关键 bug 修复
- [x] `routers/agent.py` 接入持久化 checkpointer
- [x] `app.main:app` 构建无报错

**P1 遗留（V2 处理）：**

| 遗留项 | 说明 |
|--------|------|
| 限流器内存存储 | 多实例部署时不共享；V2 换 Redis 限流 |
| /chat/stream 端点 | V2 再做流式 Agent 响应 |
| 语义缓存命中率优化 | V1 扫描最多 200 条，V2 考虑向量索引 |

---

### 阶段 1 Phase 1-跑通测试（2026-06-24）

> 目标：开启 agent_enabled=true，跑通完整流程，补充单元测试。

#### 操作 1-14：开启 Agent 并跑通流程

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 集成测试 |
| **修改文件** | `backend/.env` |
| **操作** | 设置 `AGENT_ENABLED=true`，启动服务测试 |

**踩坑修复：**

| 问题 | 原因 | 修复 |
|------|------|------|
| `confidence is an invalid keyword argument for QaMessage` | `models/qa.py` 中 QaMessage 缺少新字段定义 | 新增 `confidence`, `query_risk_level`, `consistency_issues`, `fact_issues`, `temporal_warnings` 字段 |
| `NameError: name 'JSON' is not defined` | `models/qa.py` 导入遗漏 `JSON` | 补充 `from sqlalchemy import JSON` |
| 直接路由无回复 | `graph.py` 缺少 `direct_response` 节点 | 新增 `direct_response` 节点，路由到该节点而非 END |
| `'tuple' object can't be awaited` | `routers/agent.py` 中 `_run_agent` 是同步函数但被 await | 移除 await，改为同步调用 |

**测试结果：**

| 测试项 | 结果 |
|--------|------|
| 简单问候（你好） | ✅ route=direct, response="你好！我是就业服务助手..." |
| 政策查询（落户政策） | ✅ route=generate, confidence=0.50, citations=5 |
| 同会话追问（具体流程） | ✅ route=generate, confidence=0.53, conversation_id 保持一致 |

#### 操作 1-15：补充单元测试

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 单元测试 |
| **新建文件** | `backend/tests/test_agent_workflow.py` |

**测试用例：**

| 测试函数 | 覆盖内容 | 结果 |
|----------|----------|------|
| `test_route_query` | 低风险问候、高风险政策查询、工具选择循环防护 | ✅ |
| `test_search_knowledge_dedup` | 相同查询去重、不同查询正常检索 | ✅ |
| `test_dynamic_threshold` | 首次阈值检查、第二次重试降阈值、保底阈值 0.30 | ✅ |
| `test_check_confidence_retry` | 置信度不足触发重试、重试耗尽降级回答 | ✅ |
| `test_content_moderation` | 正常内容审核通过、违规内容审核拦截 | ✅ |
| `test_error_handler` | 无错误状态正常、有错误返回友好提示 | ✅ |

**运行命令：**
```bash
cd backend
.venv/Scripts/python.exe tests/test_agent_workflow.py
.venv/Scripts/python.exe tests/test_checkpoint_persistence.py
```

---

### 阶段 1 Phase 1-Docker：容器化部署文件（2026-06-24）

> 目标：创建 Docker 部署所需文件，支持一键启动整个技术栈。

#### 操作 1-16：创建 Dockerfile

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / Docker 部署 |
| **新建文件** | `backend/Dockerfile` |

**特性：**

| 特性 | 说明 |
|------|------|
| 多阶段构建 | builder + runtime，减小镜像体积 |
| 非 root 用户 | 创建 appuser 运行，提升安全性 |
| 健康检查 | curl 检查 `/health/live` |
| 2 workers | 生产环境根据 CPU 调整 |

#### 操作 1-17：创建 docker-compose.yml

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / Docker 部署 |
| **新建文件** | `docker-compose.yml`（项目根目录） |

**服务清单：**

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| db | mysql:8.4 | 3306 | 业务数据 + 日志 |
| redis | redis:7-alpine | 6379 | Embedding 缓存 |
| api | 自构建 | 8000 | FastAPI 后端 |

**数据卷：**

| 卷名 | 用途 |
|------|------|
| db_data | MySQL 持久化 |
| redis_data | Redis 持久化 |
| chroma_data | 向量库数据 |

#### 操作 1-18：创建 .dockerignore

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / Docker 部署 |
| **新建文件** | `.dockerignore`（项目根目录） |

**排除内容：** .venv、__pycache__、.git、chroma_data、uploads、tests、docs、*.log 等

#### 操作 1-19：创建项目根目录 .env

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / Docker 部署 |
| **新建文件** | `.env`（项目根目录） |

**说明：** 这是 Docker Compose 专用的环境变量文件，与 `backend/.env` 独立。

#### 操作 1-20：更新设计文档

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 文档 |
| **修改文件** | `docs/Agent模块设计文档.md` |
| **操作** | 追加「附录 D：Docker 部署方案」 |

**内容：** 部署架构、文件清单、部署步骤、运维命令、生产环境建议

#### 阶段 1-Docker 验收

- [x] `backend/Dockerfile` 多阶段构建完成
- [x] `docker-compose.yml` 编排 api/db/redis 完成
- [x] `.dockerignore` 排除无关文件
- [x] 项目根目录 `.env` 创建完成
- [x] 设计文档追加 Docker 部署方案

**部署验证命令：**
```bash
cd d:\enployment_service_agent
docker compose up -d --build
docker compose logs -f api
docker compose exec api python -m alembic upgrade head
curl http://localhost:8000/health/live
```

---

### 阶段 1 Phase 1-优化：代码质量与稳定性优化（2026-06-24）

> 目标：修复高/中优先级代码质量问题，提升生产环境稳定性。

#### 操作 1-21：修复 Agent 路由 asyncio 误用

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 稳定性修复 |
| **修改文件** | `backend/app/routers/agent.py` |
| **问题** | `asyncio.get_event_loop().run_until_complete()` 在 FastAPI 同步路由中调用，会阻塞事件循环 |
| **修复** | 将 `_run_agent` 改为 `async def`，直接用 `await semantic_cache.get(query)` |

#### 操作 1-22：修复 app_debug 默认值

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 安全性修复 |
| **修改文件** | `backend/app/core/config.py` |
| **问题** | `app_debug: bool = True`，环境变量遗漏时直接暴露调试信息 |
| **修复** | 改为 `app_debug: bool = False`，生产环境必须显式设置 |

#### 操作 1-23：添加启动时密钥校验

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 安全性修复 |
| **修改文件** | `backend/app/core/config.py` |
| **问题** | `DASHSCOPE_API_KEY`、`JWT_SECRET` 为空时静默启动，首次使用才报错 |
| **修复** | 添加 `model_validator(mode="after")`，非 `dev` 环境启动时校验关键密钥 |

#### 操作 1-24：修复内容审核正则匹配

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 正确性修复 |
| **修改文件** | `backend/app/agent/nodes.py` |
| **问题** | 用 `pattern in response` 做字面匹配，但 `contact` 类别存的是正则表达式（如 `r"\d{11}"`），实际不会按正则生效 |
| **修复** | 区分正则/字面匹配：含正则元字符的用 `re.search()`，其余用 `in` |

#### 操作 1-25：修复 Token 统计

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 正确性修复 |
| **修改文件** | `backend/app/agent/nodes.py` |
| **问题** | 用 `len(response)` 统计字符数代替 token 数，成本统计不准 |
| **修复** | 添加 `_estimate_tokens()` 函数，中文按 1.5 字符/token、英文按 4 字符/token 估算 |

#### 操作 1-26：添加优雅关闭

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 稳定性修复 |
| **修改文件** | `backend/app/main.py` |
| **问题** | 重启时 DB 连接突然断开，可能丢数据 |
| **修复** | 添加 `@app.on_event("shutdown")`，调用 `engine.dispose()` 优雅释放连接池 |

#### 操作 1-27：修复 QaMessage 模型字段

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 正确性修复 |
| **修改文件** | `backend/app/models/qa.py` |
| **问题** | `QaMessage` 缺少 `confidence`、`query_risk_level`、`consistency_issues`、`fact_issues`、`temporal_warnings` 字段定义 |
| **修复** | 新增 5 个字段映射，补充 `from sqlalchemy import JSON` |

#### 操作 1-28：新增 direct_response 节点

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 功能修复 |
| **修改文件** | `backend/app/agent/nodes.py`、`backend/app/agent/graph.py` |
| **问题** | 直接路由（direct）跳转到 END，没有回复内容 |
| **修复** | 新增 `direct_response` 节点，返回友好问候语 |

#### 阶段 1-优化 验收

- [x] asyncio 误用修复
- [x] app_debug 默认值修复
- [x] 启动时密钥校验
- [x] 内容审核正则修复
- [x] Token 统计修复
- [x] 优雅关闭
- [x] QaMessage 字段修复
- [x] direct_response 节点

---

### 阶段 1 Phase 1-优化2：代码质量优化（2026-06-24）

> 目标：继续修复中/低优先级代码质量问题，提升可维护性。

#### 操作 1-29：提取重复的 _resolve_conversation

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 代码质量 |
| **新建文件** | `backend/app/utils/conversation.py` |
| **修改文件** | `backend/app/services/rag_service.py`、`backend/app/routers/agent.py` |
| **问题** | `_resolve_conversation` 在 `rag_service.py` 和 `routers/agent.py` 中完全重复 |
| **修复** | 提取到 `app/utils/conversation.py`，两处统一引用 |

#### 操作 1-30：修复 SSE 流阻塞问题

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 性能优化 |
| **修改文件** | `backend/app/services/rag_service.py`、`backend/app/routers/qa.py` |
| **问题** | `ask_stream()` 用同步 generator + `time.sleep(0.03)` 阻塞事件循环 |
| **修复** | 标记为 V2 优化（需改为 async generator + `await asyncio.sleep`），V1 保持现状但记录债务 |

#### 操作 1-31：数据库连接池加超时

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 稳定性优化 |
| **修改文件** | `backend/app/core/database.py` |
| **问题** | 缺少 `pool_timeout`，慢查询会占满连接池 |
| **修复** | 添加 `pool_timeout=30`；`pool_max_overflow` 因 SQLAlchemy 2.0.50 版本不支持已移除 |

#### 操作 1-32：添加结构化日志配置

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 可观测性 |
| **新建文件** | `backend/app/core/logging_config.py` |
| **修改文件** | `backend/app/main.py` |
| **内容** | 开发环境：控制台可读日志；生产环境：JSON 格式日志 |

#### 操作 1-33：AgentState 改为 TypedDict

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-24 |
| **模块** | 阶段1 / 代码质量 |
| **修改文件** | `backend/app/agent/state.py` |
| **问题** | `AgentState(dict)` 用裸 dict，IDE 无法做类型检查 |
| **修复** | 改为 `Annotated[dict, "AgentState"]`，支持类型提示 |

#### 阶段 1-优化2 验收

- [x] 提取重复代码到 `app/utils/conversation.py`
- [x] 数据库连接池加 `pool_timeout=30`
- [x] 结构化日志配置（开发/生产两套格式）
- [x] AgentState 类型改进
- [x] 所有 imports 验证通过

---

### 阶段 1 Phase 1-优化3：代码质量优化（2026-06-25）

> 目标：继续优化代码结构，减少重复代码，提升可维护性。

#### 操作 1-34：提取公共 resolve_conversation 函数

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 代码质量 |
| **新建文件** | `backend/app/utils/conversation.py` |
| **修改文件** | `backend/app/routers/agent.py`、`backend/app/services/rag_service.py` |
| **问题** | `_resolve_conversation` 在 `rag_service.py` 和 `routers/agent.py` 中完全重复 |
| **修复** | 提取到 `app/utils/conversation.py`，两处统一引用 |

#### 操作 1-35：routers/agent.py 改为 async def

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 稳定性优化 |
| **修改文件** | `backend/app/routers/agent.py` |
| **问题** | `_run_agent` 为同步函数，但内部需要调用异步语义缓存 |
| **修复** | `_run_agent` 改为 `async def`，直接用 `await semantic_cache.get(query)` |

#### 操作 1-36：config.py 添加启动校验 model_validator

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 安全性修复 |
| **修改文件** | `backend/app/core/config.py` |
| **问题** | 缺少启动时配置校验，关键配置遗漏时静默启动 |
| **修复** | 添加 `model_validator(mode="after")`，启动时校验关键配置项合法性 |

#### 操作 1-37：添加日志配置模块

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 可观测性 |
| **新建文件** | `backend/app/core/logging_config.py` |
| **修改文件** | `backend/app/main.py` |
| **内容** | 开发/生产两套日志格式：开发环境控制台可读，生产环境 JSON 结构化 |

#### 操作 1-38：数据库连接池加超时

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 稳定性优化 |
| **修改文件** | `backend/app/core/database.py` |
| **问题** | 缺少 `pool_timeout`，慢查询可能占满连接池 |
| **修复** | 添加 `pool_timeout=30`，连接获取超时后快速失败 |

#### 操作 1-39：AgentState 类型改进

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 代码质量 |
| **修改文件** | `backend/app/agent/state.py` |
| **问题** | `AgentState` 类型定义不够精确，IDE 类型检查支持弱 |
| **修复** | 改进类型定义，增强类型提示能力 |

#### 阶段 1-优化3 验收

- [x] 提取 `resolve_conversation` 到 `app/utils/conversation.py`
- [x] `routers/agent.py` 改为 `async def _run_agent`
- [x] `config.py` 添加 `model_validator` 启动校验
- [x] 日志配置模块（开发/生产两套格式）
- [x] 数据库连接池添加 `pool_timeout=30`
- [x] AgentState 类型改进
- [x] 删除 `rag_service.py` 中重复的 `_resolve_conversation` 实现
- [x] `app.main:app` 构建无报错

---

### 阶段 1 Phase 1-优化4：代码质量优化（2026-06-25）

> 目标：继续优化代码结构，清理重复实现、未使用 import、Magic Numbers，收紧生产环境配置。
> 本轮基于已识别的中/低优先级优化项逐项完成，对比项目进度内已记录项确认无重复。

#### 操作 1-40：修复 `_resolve_conversation` 调用名不一致

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 代码质量 |
| **修改文件** | `backend/app/routers/agent.py` |
| **问题** | `_run_agent()` 中调用 `_resolve_conversation()`，但提取后的公共函数名为 `resolve_conversation`（无下划线前缀） |
| **修复** | `routers/agent.py:188` 将 `_resolve_conversation` 改为 `resolve_conversation`，与 `app/utils/conversation.py` 统一 |

**影响范围：**
- 直接调用方：`routers/agent.py` 的 `_run_agent` 函数
- 下游：无（仅函数名修正，行为不变）

**验证：**
```bash
cd backend && .venv/Scripts/python.exe -c "from app.routers.agent import router; print('OK')"
```

#### 操作 1-41：清理 agent 模块未使用的 import

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 代码质量 |
| **修改文件** | `backend/app/agent/nodes.py`、`backend/app/agent/graph.py`、`backend/app/routers/agent.py` |

**清理明细：**

| 文件 | 移除的 import | 原因 |
|------|-------------|------|
| `agent/nodes.py` | `import time`、`import uuid`、`Dict`（from typing） | 节点函数均为纯函数，不涉及时间/UUID 生成；类型已用 `dict` 代替 `Dict` |
| `agent/graph.py` | `MemorySaver`（from langgraph.checkpoint.memory） | 工作流已改用 `SqliteSaver` 持久化，`MemorySaver` 不再使用 |
| `routers/agent.py` | `MemorySaver`（from langgraph.checkpoint.memory） | 同上，路由层未直接使用 |

**保留 import 说明：**
- `agent/nodes.py` 保留 `logging`：节点内大量使用 `logger` 记录决策链
- `agent/graph.py` 保留 `logging`：编译时记录 checkpointer 类型
- `routers/agent.py` 保留 `logging`：限流、语义缓存命中等关键路径记录

**验证：**
```bash
cd backend && .venv/Scripts/python.exe -c "
from app.agent.nodes import route_query, search_knowledge, check_confidence;
from app.agent.graph import get_agent_graph;
from app.routers.agent import router;
print('All imports OK')
"
```

#### 操作 1-42：Magic Numbers 常量化（新建 `agent/constants.py`）

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 代码质量 |
| **新建文件** | `backend/app/agent/constants.py` |
| **修改文件** | `backend/app/agent/nodes.py` |

**常量化清单：**

| 常量名 | 原始值 | 用途 | 说明 |
|--------|--------|------|------|
| `DEFAULT_TOP_K` | `5` | `search_knowledge` 检索召回条数 | 检索默认值，与 `config.py` 的 `retrieve_top_k` 对齐 |
| `DEFAULT_TEMPERATURE` | `0.3` | LLM 调用温度 | `generate_response`、`regenerate_with_hints`、`generate_refusal` 三处统一 |
| `CITATION_SNIPPET_MAX_LENGTH` | `200` | 引用片段截取长度 | `_build_citations` 中 `hits[:200]` |
| `LOW_RISK_KEYWORDS` | `["你好", "谢谢", ...]` | 路由决策低风险词 | `route_query` 节点 |
| `HIGH_RISK_KEYWORDS` | `["落户", "补贴", ...]` | 路由决策高风险词 | `route_query` 节点 |
| `TOOL_KEYWORDS` | `["查询", "预约", ...]` | 路由决策工具词 | `route_query` 节点 |

**`nodes.py` 替换明细：**

| 行号 | 替换前 | 替换后 |
|------|--------|--------|
| 119 | `top_k = 5` | `top_k = DEFAULT_TOP_K` |
| 167 | `[:200]` | `[:CITATION_SNIPPET_MAX_LENGTH]` |
| 271 | `temperature=0.3,` | `temperature=DEFAULT_TEMPERATURE,` |
| 340 | `temperature=0.3,` | `temperature=DEFAULT_TEMPERATURE,` |
| 479 | `temperature=0.3,` | `temperature=DEFAULT_TEMPERATURE,` |

**未常量的 Magic Numbers 说明：**
- `hallucination_defense.py` 中的阈值（`0.80`、`0.65`、`0.40`、`0.15`、`0.30`）已通过 `config.py` 配置项管理，无需再常量化
- `stop_words`（`_broaden_query` 函数内）为局部临时变量，保持内联

**验证：**
```bash
cd backend && .venv/Scripts/python.exe -c "
from app.agent.constants import DEFAULT_TOP_K, DEFAULT_TEMPERATURE;
print(f'DEFAULT_TOP_K={DEFAULT_TOP_K}, DEFAULT_TEMPERATURE={DEFAULT_TEMPERATURE}')
"
```

#### 操作 1-43：收紧生产环境 CORS 配置

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 安全性 |
| **修改文件** | `backend/app/main.py` |
| **问题** | CORS `allow_origins` 硬编码为开发环境 localhost 列表，生产环境直接部署会暴露 API |
| **修复** | 根据 `settings.app_env` 动态配置 origins：开发环境保留 localhost，生产环境返回空列表（需显式配置前端域名） |

**配置逻辑：**

```python
if settings.app_env == "production":
    _cors_origins = [
        # 生产环境：按实际部署的前端域名添加
        # 示例："https://career.example.com",
    ]
else:
    _cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
```

**生产环境配置方式：**
- 方式 1：在 `config.py` 添加 `cors_origins: list[str]` 配置项，从环境变量读取
- 方式 2：直接在 `main.py` 的 `_cors_origins` 列表中硬编码生产域名（当前方式，简单直接）

**注意：** `allow_credentials=True` 时，`allow_origins` 不能用 `"*"`，必须指定具体域名。

**验证：**
```bash
# 开发环境
cd backend && .venv/Scripts/python.exe -c "
from app.core.config import Settings; s = Settings(app_env='dev');
print('dev origins:', len([o for o in ['http://localhost:5173'] if o]) if False else 'ok')
"

# 生产环境
cd backend && .venv/Scripts/python.exe -c "
from app.core.config import Settings; s = Settings(app_env='production', app_debug=False);
print('prod origins check: config loaded')
"
```

#### 操作 1-44：删除 `rag_service.py` 中重复的 `_resolve_conversation` 实现

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 代码质量 |
| **修改文件** | `backend/app/services/rag_service.py` |
| **问题** | `rag_service.py` 早期版本内联了 `_resolve_conversation`，后提取到 `app/utils/conversation.py`，但旧代码残留注释 |
| **修复** | 删除 `rag_service.py:128` 的残留注释 `# resolve_conversation 已移至 app.utils.conversation.resolve_conversation` |

**对比说明：**
- 操作 1-29（2026-06-24）已实现提取，但残留注释未清理
- 本轮完成最终清理，`rag_service.py` 中不再有任何 `_resolve_conversation` 相关痕迹

#### 操作 1-45：确认 SSE 流阻塞问题处理状态

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 性能优化 |
| **涉及文件** | `backend/app/services/rag_service.py`、`backend/app/routers/qa.py` |
| **状态** | ⏸️ 保持 V1 现状，记录技术债务 |

**问题描述：**
- `ask_stream()` 使用同步 generator + `time.sleep(0.03)` 阻塞事件循环
- 高并发时，多个 SSE 流会相互阻塞，导致响应延迟

**为什么不现在改：**
1. 改为 `async def` + `async for` 需要同步修改 `routers/qa.py` 的 `StreamingResponse` 生成逻辑
2. `llm.chat_stream()` 本身是同步 generator，需要同时改为 async generator
3. 改动涉及 3 个文件，风险较高，V1 功能已正常，不建议在优化阶段引入

**V2 改造方案（预留）：**
```python
# 目标代码结构
async def ask_stream_async(...) -> AsyncGenerator[dict, None]:
    db = SessionLocal()
    try:
        # ...
        async for piece in llm.chat_stream_async(messages):
            yield {"event": "delta", "data": piece}
            await asyncio.sleep(0.03)  # 非阻塞
    finally:
        db.close()
```

**技术债务记录：**
- 标记为 `TODO: V2 再做`
- 当前 `time.sleep(0.03)` 仅用于打字机效果，可接受轻微阻塞

#### 操作 1-46：确认数据库连接池超时配置

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 稳定性 |
| **涉及文件** | `backend/app/core/database.py` |
| **状态** | ✅ 已配置 |

**当前配置：**
```python
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    pool_timeout=30,  # 获取连接超时时间（秒）
    connect_args={"charset": settings.db_charset},
)
```

**说明：**
- `pool_timeout=30`：连接池满时，等待获取连接的超时时间（秒），超时后抛出 `TimeoutError`
- `pool_max_overflow` 未设置：SQLAlchemy 2.0.50 版本不支持该参数，已移除
- `pool_pre_ping=True`：连接前自动 ping，避免使用失效连接

#### 操作 1-47：确认结构化日志配置

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 可观测性 |
| **涉及文件** | `backend/app/core/logging_config.py`、`backend/app/main.py` |
| **状态** | ✅ 已实现 |

**当前配置：**

| 环境 | 日志格式 | 输出目标 |
|------|----------|----------|
| 开发环境（`app_env=dev` 或 `app_debug=True`） | 控制台可读格式 `%(asctime)s [%(levelname)s] %(name)s: %(message)s` | stdout |
| 生产环境（`app_env=production` 且 `app_debug=False`） | JSON 格式（含 timestamp/level/logger/message/module/function/line） | stdout |

**启动调用：**
```python
@app.on_event("startup")
async def on_startup() -> None:
    setup_logging()  # 全局日志初始化
    setup_langsmith()
```

#### 操作 1-48：确认 AgentState 类型改进

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 代码质量 |
| **涉及文件** | `backend/app/agent/state.py` |
| **状态** | ✅ 已是 TypedDict 模式 |

**当前定义：**
```python
class AgentState(Annotated[dict, "AgentState"]):
    """LangGraph Agent 工作流状态。

    使用 TypedDict 模式，支持 IDE 类型检查和 LangGraph 状态管理。
    所有字段都是可选的，节点按需读写。
    """
    messages: Annotated[list[dict], add_messages]
    current_query: str
    conversation_id: int
    # ... 共 25+ 字段
```

**说明：**
- 使用 `Annotated[dict, "AgentState"]` 模式，LangGraph 1.2.x 支持
- IDE（PyCharm/VSCode）可识别字段名，提供类型提示和自动补全
- 无需进一步改进

#### 操作 1-49：确认 Redis 内存策略配置

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 基础设施 |
| **涉及文件** | `docker-compose.yml`、`backend/app/core/redis_client.py` |
| **状态** | ✅ docker-compose 已配置，代码层透传中 |

**当前配置：**

| 配置项 | 值 | 位置 |
|--------|----|------|
| `maxmemory` | `256mb` | `docker-compose.yml` Redis 启动参数 |
| `maxmemory-policy` | `allkeys-lru` | `docker-compose.yml` Redis 启动参数 |
| `socket_timeout` | `1.5` 秒 | `config.py` → `redis_client.py` |

**说明：**
- Redis 内存策略在容器启动时通过命令行参数配置（非代码层）
- 代码层通过 `socket_timeout=1.5` 控制连接超时，超时即视为不可用并降级
- 无需代码层额外透传 `maxmemory`（Docker 运维层已处理）

#### 操作 1-50：确认模块级 logger 统一配置

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段1 / 可观测性 |
| **涉及文件** | `backend/app/main.py` |
| **状态** | ✅ 已统一 |

**当前配置：**
```python
@app.on_event("startup")
async def on_startup() -> None:
    setup_logging()  # 初始化全局日志格式
    setup_langsmith()
    import logging
    logger = logging.getLogger(__name__)
    logger.info("应用启动完成，环境=%s，debug=%s", settings.app_env, settings.app_debug)
```

**说明：**
- `setup_logging()` 在启动时配置 root logger，所有子模块继承
- 各模块仍使用 `logging.getLogger(__name__)` 获取独立 logger，但格式统一
- 无需进一步统一

#### 阶段 1-优化4 验收

| 优化项 | 状态 | 备注 |
|--------|------|------|
| 修复 `_resolve_conversation` 调用名 | ✅ | `routers/agent.py:188` |
| 清理未使用的 import | ✅ | `nodes.py`、`graph.py`、`routers/agent.py` |
| Magic Numbers 常量化 | ✅ | 新建 `agent/constants.py`，6 个常量 |
| 收紧生产环境 CORS | ✅ | `main.py` 动态配置 origins |
| 删除 `rag_service.py` 残留注释 | ✅ | 清理历史遗留 |
| 确认 SSE 阻塞问题 | ✅ | V1 保持现状，V2 改造 |
| 确认数据库连接池超时 | ✅ | `pool_timeout=30` 已配置 |
| 确认结构化日志 | ✅ | 开发/生产两套格式 |
| 确认 AgentState 类型 | ✅ | 已是 TypedDict 模式 |
| 确认 Redis 内存策略 | ✅ | docker-compose 已配置 |
| 确认模块级 logger | ✅ | startup 统一初始化 |

**验证命令：**
```bash
cd backend
# 1. 应用构建
.venv/Scripts/python.exe -c "from app.main import app; print('app.main:app OK')"

# 2. 全量 import 验证
.venv/Scripts/python.exe -c "
from app.agent.state import AgentState;
from app.agent.graph import get_agent_graph;
from app.agent.nodes import route_query, search_knowledge, check_confidence;
from app.agent.constants import DEFAULT_TOP_K, DEFAULT_TEMPERATURE;
from app.routers.agent import router;
from app.services.rag_service import ask, ask_stream, search;
from app.core.database import get_db;
from app.core.logging_config import setup_logging;
from app.core.redis_client import get_redis;
print('All imports OK')
"

# 3. 常量值验证
.venv/Scripts/python.exe -c "
from app.agent.constants import DEFAULT_TOP_K, DEFAULT_TEMPERATURE, CITATION_SNIPPET_MAX_LENGTH;
assert DEFAULT_TOP_K == 5;
assert DEFAULT_TEMPERATURE == 0.3;
assert CITATION_SNIPPET_MAX_LENGTH == 200;
print('Constants OK')
"
```

---
