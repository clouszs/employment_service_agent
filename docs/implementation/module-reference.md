# 模块速查

> 快速查阅各模块的文件清单和职责。**不包含代码片段**（源码请直接阅读对应文件）。
> **最后更新**：2026-07-02

---

## 1. 核心基础设施 `backend/app/core/`

| 文件 | 职责 |
|------|------|
| `config.py` | pydantic-settings 配置（80+ 字段：DB/JWT/LLM/Redis/Agent/监控）|
| `database.py` | SQLAlchemy engine + SessionLocal + get_db 依赖 |
| `deps.py` | get_current_user（JWT 验证）+ require_roles 权限工厂 |
| `security.py` | PBKDF2 密码哈希 + JWT 创建/验证 |
| `llm.py` | DashScope OpenAI 兼容客户端（sync/async/stream + 重试）|
| `embedding.py` | Embedding 生成（batched 10条/批，L1 缓存优先）|
| `embedding_cache.py` | 三级缓存：L1 内存 LRU / L2 Redis / L3 MySQL |
| `vectorstore.py` | ChromaDB 持久化向量库（cosine 距离，kb_chunks）|
| `redis_client.py` | Redis 懒连接 + 30s cooldown 熔断降级 |
| `semantic_cache.py` | 语义缓存（Redis-backed，余弦>0.92 命中）|
| `document_parser.py` | 文件解析：.txt/.md/.pdf |
| `text_splitter.py` | 句子级切分（中英文 punctuation + overlap）|
| `semantic_chunker.py` | 语义切分（句子嵌入 + 百分位落差法）|
| `langsmith_setup.py` | LangSmith 全局追踪开关 + runtime 重配置 |
| `logging_config.py` | JSON 格式（生产）/ 控制台（开发）|
| `response.py` | 统一响应 envelope（code/message/data）+ 异常处理器 |

## 2. 数据模型 `backend/app/models/`

| 文件 | 表数 | 核心表 |
|------|------|--------|
| `base.py` | — | DeclarativeBase + TABLE_ARGS（utf8mb4/InnoDB）|
| `user.py` | 3 | sys_user / sys_role / sys_user_role |
| `qa.py` | 4 | qa_conversation / qa_message / qa_message_reference / qa_feedback |
| `knowledge.py` | 6 | kb_category / kb_document / kb_document_chunk / kb_faq / kb_synonym / kb_index_task |
| `app_config.py` | 1 | app_config（KV 配置表，qa_ 前缀区分 QA 配置）|
| `announcement.py` | 1 | announcement（标题/内容/优先级/发布状态/过期时间）|
| `resume.py` | 1 | user_resume（多版本 + is_default 标记）|
| `ops.py` | 4 | op_query_log / op_sensitive_word / op_unanswered_question / op_eval_case |
| `monitor.py` | 6 | kb_health_log / llm_cost_log / agent_refusal_log / citation_quality_log / consistency_issue_log / fact_verification_log |
| `llm_usage.py` | 1 | llm_usage（特性级 LLM 流水，source 区分 agent_chat / resume_generation）|
| `user_favorite.py` | 1 | user_favorite（消息收藏 + 备注）|

**总计：24 张表**

## 3. 业务服务 `backend/app/services/`

| 文件 | 职责 |
|------|------|
| `user_service.py` | 用户 CRUD / 认证 / 密码重置 / 硬删除 / 角色分配 |
| `knowledge_service.py` | KB 管理：文档上传（SHA-256 去重）/ 分类 / FAQ（自动向量化）/ 同义词 |
| `index_service.py` | 后台 parse→index 流水：chunk → embed → Chroma upsert |
| `rag_service.py` | 核心检索：ask（含重试）/ ask_stream（SSE）/ search（向量+FAQ+时效）|
| `qa_service.py` | 对话生命周期：agent_chat（LangGraph invoke）/ 反馈 CRUD / 管理员硬删除 |
| `announcement_service.py` | 双数据源： announcements.json（Agent 用）+ DB CRUD（管理端）|
| `app_config_service.py` | KV 配置：qa_ 前缀过滤 / seed_defaults / 缓存降级 |
| `resume_service.py` | 简历 LLM 生成 → JSON 持久化 → PDF 导出（reportlab）|
| `job_service.py` | 职位推荐：复用 rag_service.search + 地点过滤 |
| `calendar_service.py` | 面试日程 ICS 生成（纯计算）|
| `ops_service.py` | 内容审核（敏感词 cache+regex）/ 查询日志 / 评测集 / 未解决问题 / 统计聚合 |
| `llm_usage.py` | 特性级 LLM token 流水（llm_usage 表 + 审计日志）|
| `user_favorite_service.py` | 消息收藏 CRUD（幂等）+ 批量删除 |

## 4. Agent 引擎 `backend/app/agent/`

| 文件 | 职责 |
|------|------|
| `state.py` | AgentState TypedDict（25+ 字段，含死循环防护字段）|
| `graph.py` | 12 节点 StateGraph 编译 + SqliteSaver checkpoint 单例 |
| `nodes.py` | 12 个节点实现：route / search / check_confidence / generate / regenerate / check_consistency / verify_facts / content_moderation / accept_with_warning / refuse / direct_response / error_handler |
| `tools.py` | 3 个工具：knowledge_search（进程内 RAG）/ bing_search（MCP）/ fetch_webpage（MCP）+ MCPClient 封装 |
| `hallucination_defense.py` | 3 个防御组件：DynamicConfidenceThreshold / FactVerificationPostProcessor / SelfConsistencyChecker |
| `citation_tracker.py` | 引用构建（chunk 级）+ 质量评估（direct/indirect/none）|
| `temporal_retriever.py` | 时效过滤：过期文档剔除 + 即将过期警告 |
| `refusal_handler.py` | 6 个拒答模板（general / no_result / low_confidence / blocked / consistency / fact_verification）|
| `prompts/generator.py` | GENERATOR_SYSTEM_PROMPT + GENERATOR_USER_PROMPT |
| `prompts/regenerator.py` | REGENERATOR_SYSTEM_PROMPT + REGENERATOR_USER_PROMPT |
| `constants.py` | 意图关键词 / 阈值 / 12 类意图映射 / DEFAULT_TOP_K 等常量 |

## 5. 监控 `backend/app/monitor/`

| 文件 | 职责 |
|------|------|
| `scheduler.py` | APScheduler 单例：4 个 cron job（02:00/02:15/02:30/02:45）|
| `health_monitor.py` | KB 健康度：freshness 半衰期衰减 + 过期惩罚 → health_score 0-100 |
| `cost_monitor.py` | LLM 成本：按天+模型聚合 / 单价映射 / 阈值告警 / 月度汇总 |
| `citation_evaluator.py` | 引用质量：direct/indirect/none 计数 + quality_score 持久化 |

## 6. 路由层（28 个 router，前缀 /api/v1）

| 路由文件 | 前缀 | 核心端点 |
|----------|------|----------|
| `health.py` | /health | GET / — DB 存活探针 |
| `auth.py` | /auth | POST /login / GET /me / POST /change-password |
| `users.py` | /users | CRUD + 硬删除 + 重置密码 + 角色分配 |
| `roles.py` | /roles | List / Create / Update |
| `categories.py` | /categories | CRUD（删除需无子分类/文档）|
| `documents.py` | /documents | 上传/列表/详情/删除/分片查询/解析索引触发 |
| `index_tasks.py` | /index-tasks | 分页任务列表 |
| `faqs.py` | /faqs | Top（public）/ CRUD / 批量启用停用删除 / 状态切换 |
| `synonyms.py` | /synonyms | CRUD |
| `sensitive_words.py` | /sensitive-words | CRUD（admin）|
| `qa.py` | /search /ask /ask/stream /ask/agent | 向量检索 / 同步问答 / SSE 流式 / Agent |
| `agent.py` | /chat | Agent 对话（独立端点，含限流 + 语义缓存）|
| `conversations.py` | /conversations | CRUD + 历史消息 + 反馈 + 引用 |
| `messages.py` | /messages | 反馈提交 / 引用查询 |
| `admin_conversations.py` | /admin/conversations | 跨用户列表 + 详情 + 强制删除 + LangSmith toggle |
| `feedback.py` | /feedback | 统计摘要 + 分页列表 |
| `query_logs.py` | /logs/queries | 分页查询日志 |
| `stats.py` | /stats | 总览 / 热门问题 / 日趋势 / 活动统计 / 就业数据 |
| `eval_cases.py` | /eval-cases | 评测集 CRUD + 批量执行 |
| `unanswered.py` | /unanswered | 无答案列表 + 解决 + 删除 + SHA-256 去重 |
| `app_config.py` | /app-configs | KV 配置 CRUD + seed_defaults + upsert |
| `user_favorite.py` | /favorites | 收藏 CRUD（幂等）+ 批量删除 |
| `announcements.py` | /announcements | 公开列表 / active 列表 / 管理端 CRUD |
| `career.py` | /career | 简历生成/保存/列表/删除/默认/PDF；职位推荐；ICS 日历 |
| `kb_health.py` | /kb-health | Latest / History / manual run |
| `llm_cost.py` | /llm-cost | Daily / Monthly / Monthly-by-source / History |
| `refusal.py` | /refusal | 拒答记录列表 + 统计摘要 |
| `kb_health.py` | /kb-health | Latest / History / manual run |

## 7. 前端结构 `frontend/src/`

### 路由结构（3 个门户 + 1 个共享）

| 门户 | 布局 | 核心页面 |
|------|------|----------|
| 学生 (`/student`) | StudentLayout | Chat / 会话历史 / 简历 / 职位 / 日历 / 就业数据 / 收藏 / 个人中心 |
| 教师 (`/teacher`) | TeacherLayout | 数据看板 / FAQ 管理 / 对话监控 / 就业数据 / 个人中心 |
| 管理员 (`/admin`) | AdminLayout | 概览 / 文档 / 分类 / FAQ / 同义词 / 日志 / 反馈 / 无答案 / 评测 / 用户 / 角色 / 敏感词 / 监控 / 统计 / 学生 / 公告 / 设置 / QA 配置 / 对话管理 |

### 核心文件

| 目录 | 关键文件 | 职责 |
|------|----------|------|
| `api/` | 15 个 .ts 文件 | Axios 封装，统一 token 注入 + 响应解包 |
| `stores/` | user.ts / chat.ts / monitor.ts | Pinia：用户态 / 对话态 / 监控态 |
| `types/` | 10 个 .ts 文件 | TypeScript 类型定义（chat/user/knowledge/monitor/ops 等）|
| `components/chat/` | 11 个 .vue 文件 | 聊天核心组件（SearchBox / MessageList / ReferenceCard 等）|
| `components/dashboard/` | 6 个 .vue 文件 | 看板卡片（StatsOverview / KbHealth / LlmCost / HotQuestions）|
| `views/admin/` | 18 个 .vue 文件 | 管理端页面 |
| `views/chat/` | 3 个 .vue 文件 | 学生端聊天 / 收藏 / 历史 |
| `views/student/` | 5 个 .vue 文件 | 简历 / 职位 / 日历 / 就业数据 / 个人中心 |
