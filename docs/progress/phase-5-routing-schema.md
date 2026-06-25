### 阶段 5 Phase 5：路由 + Schema 补齐（2026-06-25）

> 目标：将阶段 0-4 的后端能力通过 HTTP 接口暴露，补齐 Agent Schema 和监控路由，为阶段 6 前端对接铺平道路。
> 前置条件：阶段 0-4 全部完成（Agent 工作流 + 幻觉防御 + 监控告警 + QA 服务升级）。

---

## 阶段 5 前置条件确认

| 前置 | 状态 | 说明 |
|------|------|------|
| 阶段 0-4 完成 | ✅ | 环境/Agent 核心/幻觉防御/监控/QA 升级全部完成 |
| `models/monitor.py` | ✅ | 6 个监控模型已定义（KbHealthLog/LlmCostLog/AgentRefusalLog/CitationQualityLog/ConsistencyIssueLog/FactVerificationLog） |
| `monitor/` 业务逻辑 | ✅ | health_monitor.py / cost_monitor.py / citation_evaluator.py / scheduler.py 已实现 |
| `qa_service.agent_chat()` | ✅ | 阶段 4 已完成，返回 enriched result dict |
| `routers/qa.py` /ask/agent | ✅ | 阶段 4 已完成，但返回结构体缺少 Agent 专属字段 |

---

## 操作 5-1：创建 `schemas/agent.py`

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 5 / Schema |
| **新建文件** | `backend/app/schemas/agent.py` |

**内容：**

| Schema | 类型 | 用途 |
|--------|------|------|
| `AgentChatRequest` | BaseModel | Agent 问答请求（query + conversation_id） |
| `AgentChatResponse` | BaseModel | Agent 问答响应（17 个字段，含 confidence/citations/warnings 等） |

**原因：** `routers/agent.py` 原本内联定义了这两个 Schema，不符合项目"Schema 独立模块"的组织规范，且 `routers/qa.py` 的 `/ask/agent` 端点也需要引用统一的结构体。

**迁移明细：**

| 项目 | 变更 |
|------|------|
| 删除 `routers/agent.py` 内联 Schema | `AgentChatRequest` / `AgentChatResponse` 类定义移除 |
| 新增 `from app.schemas.agent import AgentChatRequest, AgentChatResponse` | `routers/agent.py` |
| 新增 `from app.schemas.agent import AgentChatResponse` | `routers/qa.py` |

#### 操作 5-2：创建 `schemas/monitor.py`

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 5 / Schema |
| **新建文件** | `backend/app/schemas/monitor.py` |

**内容：**

| Schema | 用途 |
|--------|------|
| `KbHealthLogRead` | 知识库健康度日志单条（ORM 映射） |
| `KbHealthLatest` | 知识库健康度最新快照（管理端卡片用） |
| `LlmCostLogRead` | LLM 成本日志单条（ORM 映射） |
| `LlmCostDailyRead` | 单日成本汇总（按模型拆分） |
| `LlmCostMonthlyRead` | 月度成本汇总（按模型拆分） |
| `AgentRefusalLogRead` | 拒答记录单条（ORM 映射） |
| `RefusalStats` | 拒答统计摘要（总数/今日/按原因/按风险等级） |
| `CitationQualityLogRead` | 引用质量日志单条（ORM 映射） |
| `ConsistencyIssueLogRead` | 一致性问题日志单条（ORM 映射） |
| `FactVerificationLogRead` | 事实核验日志单条（ORM 映射） |

**设计说明：**
- `*Read` 类继承 `ORMModel`，支持 `model_validate(orm_obj).model_dump()` 直接序列化
- `KbHealthLatest` / `LlmCostDailyRead` / `LlmCostMonthlyRead` / `RefusalStats` 为纯 DTO，用于管理端聚合接口

#### 操作 5-3：创建 `routers/kb_health.py`

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 5 / 路由 |
| **新建文件** | `backend/app/routers/kb_health.py` |

**端点：**

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/v1/kb-health/latest` | GET | 最新一次健康检查快照 | admin / editor |
| `/api/v1/kb-health/history` | GET | 历史记录（分页 + 日期筛选） | admin / editor |
| `/api/v1/kb-health/run` | POST | 手动触发健康检查 | admin |

**实现逻辑：**
- `latest`：查询 `KbHealthLog` 最新一条，映射为 `KbHealthLatest`
- `history`：支持 `start_date` / `end_date` 筛选，分页返回 `KbHealthLogRead`
- `run`：调用 `KnowledgeBaseHealthMonitor.run_daily_check()` 手动执行，返回完整报告

**接入位置：** `main.py` 注册 `kb_health.router`，前缀 `/api/v1`

#### 操作 5-4：创建 `routers/llm_cost.py`

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 5 / 路由 |
| **新建文件** | `backend/app/routers/llm_cost.py` |

**端点：**

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/v1/llm-cost/daily` | GET | 单日成本汇总（按模型拆分） | admin / editor |
| `/api/v1/llm-cost/monthly` | GET | 月度成本汇总 | admin / editor |
| `/api/v1/llm-cost/history` | GET | 成本日志列表（分页 + 筛选） | admin / editor |

**实现逻辑：**
- `daily`：如果当天无数据，自动调用 `LlmCostMonitor.run_daily_check()` 生成；返回 `LlmCostDailyRead`
- `monthly`：调用 `LlmCostMonitor.get_monthly_cost()`；返回 `LlmCostMonthlyRead`
- `history`：支持 `model` / `start_date` / `end_date` 筛选，分页返回 `LlmCostLogRead`

**接入位置：** `main.py` 注册 `llm_cost.router`，前缀 `/api/v1`

#### 操作 5-5：创建 `routers/refusal.py`

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 5 / 路由 |
| **新建文件** | `backend/app/routers/refusal.py` |

**端点：**

| 端点 | 方法 | 说明 | 权限 |
|------|------|------|------|
| `/api/v1/refusal/list` | GET | 拒答记录列表（分页 + 筛选） | admin / editor |
| `/api/v1/refusal/stats` | GET | 拒答统计摘要 | admin / editor |

**实现逻辑：**
- `list`：支持 `risk_level` / `reason` / `start_date` / `end_date` 筛选，分页返回 `AgentRefusalLogRead`
- `stats`：统计最近 N 天拒 answering 总数、今日数、按原因分组、按风险等级分组；返回 `RefusalStats`

**注意：** 当前 `AgentRefusalLog` 模型仅定义，尚未在 Agent 工作流中实际写入记录。V1 阶段先暴露接口，V2 在 nodes.py 拒答节点中补充落库逻辑。

**接入位置：** `main.py` 注册 `refusal.router`，前缀 `/api/v1`

#### 操作 5-6：`schemas/__init__.py` 更新

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 5 / 文档 |
| **修改文件** | `backend/app/schemas/__init__.py` |
| **操作** | 补充 `agent` 和 `monitor` 模块说明 |

#### 操作 5-7：对齐 `routers/qa.py` 的 `/ask/agent` 响应结构

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 5 / 路由对齐 |
| **修改文件** | `backend/app/routers/qa.py`、`backend/app/services/qa_service.py` |

**问题：** `routers/qa.py` 的 `/ask/agent` 调用 `qa_service.agent_chat()` 后直接 `success(result)`，但 `qa_service.agent_chat()` 返回的 dict 缺少前端需要的关键字段（`citations`、`is_error`、`request_id`、`llm_tokens_in/out`）。

**修复：**
1. `qa_service.py` 的 `agent_chat()` return dict 增加 `citations`、`is_error`、`request_id`、`llm_tokens_in`、`llm_tokens_out` 字段
2. `routers/qa.py` 引入 `AgentChatResponse` Schema（准备后续直接序列化）

#### 操作 5-8：阶段 5 自测

| 测试项 | 结果 | 说明 |
|--------|------|------|
| `app.main:app` 构建 | ✅ | 无报错 |
| 全量 import 验证 | ✅ | schemas + routers + services |
| `AgentChatResponse` 字段完整性 | ✅ | 17 个字段与 `routers/agent.py` 一致 |
| `qa_service.agent_chat()` return dict | ✅ | 包含所有 Schema 字段 |
| `tests/test_qa_service.py` | ✅ | passed=13, failed=0 |

**自测命令：**
```bash
cd backend
# 1. 应用构建
.venv/Scripts/python.exe -c "from app.main import app; print('OK')"

# 2. 全量 import 验证
.venv/Scripts/python.exe -c "
from app.schemas.agent import AgentChatRequest, AgentChatResponse;
from app.schemas.monitor import KbHealthLogRead, LlmCostLogRead, AgentRefusalLogRead;
from app.routers.kb_health import router;
from app.routers.llm_cost import router;
from app.routers.refusal import router;
from app.routers.agent import router;
from app.routers.qa import router;
from app.services.qa_service import agent_chat;
print('All imports OK')
"

# 3. Schema 字段验证
.venv/Scripts/python.exe -c "
from app.schemas.agent import AgentChatResponse;
expected = ['conversation_id','message_id','response','confidence','is_no_answer','route','query_risk_level','is_low_confidence','is_error','citations','consistency_issues','fact_issues','temporal_warnings','warnings','request_id','llm_tokens_in','llm_tokens_out'];
actual = list(AgentChatResponse.model_fields.keys());
assert actual == expected, f'Mismatch: {actual}';
print('AgentChatResponse fields OK')
"

# 4. QA 服务测试
.venv/Scripts/python.exe tests/test_qa_service.py
```

**踩坑记录：**

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| `routers/qa.py` import 顺序混乱 | Edit 工具匹配失败（文件内容与预期不一致） | 改用精确匹配替换，确保 import 顺序正确 |
| `tests/test_qa_service.py` `has_citations` 失败 | `qa_service.agent_chat()` return dict 缺少 `citations` 字段 | 在 return dict 中增加 `"citations": citations` |
| `tests/test_qa_service.py` `name 'OpQueryLog' is not defined` | `qa_service.py` import 列表缺少 `OpQueryLog` | 补充 `from app.models import ... OpQueryLog` |
| `tests/test_qa_service.py` `name 'datetime' is not defined` | `qa_service.py` `from datetime import` 缺少 `datetime` | 补充 `from datetime import date, datetime, timedelta` |

---

## 阶段 5 验收

| 优化项 | 状态 | 备注 |
|--------|------|------|
| 创建 `schemas/agent.py` | ✅ | 2 个 Schema，从 `routers/agent.py` 抽离 |
| 创建 `schemas/monitor.py` | ✅ | 10 个 Schema（6 Read + 4 DTO） |
| 创建 `routers/kb_health.py` | ✅ | 3 个端点（latest/history/run） |
| 创建 `routers/llm_cost.py` | ✅ | 3 个端点（daily/monthly/history） |
| 创建 `routers/refusal.py` | ✅ | 2 个端点（list/stats） |
| 注册 3 个新路由到 `main.py` | ✅ | `kb_health` / `llm_cost` / `refusal` |
| 对齐 `routers/qa.py` /ask/agent | ✅ | `AgentChatResponse` import + return dict 字段补齐 |
| `qa_service.agent_chat()` 字段补齐 | ✅ | `citations` / `is_error` / `request_id` / `llm_tokens_in/out` |
| `schemas/__init__.py` 更新 | ✅ | 补充 agent/monitor 模块说明 |
| 自测 13 项 | ✅ | 全部通过 |

**验证后的路由清单：**

| 路由前缀 | 来源 | 端点数 |
|----------|------|--------|
| `/api/v1/health` | `health` | 1 |
| `/api/v1/auth` | `auth` | 3 |
| `/api/v1/users` | `users` | 6 |
| `/api/v1/roles` | `roles` | 6 |
| `/api/v1/categories` | `categories` | 6 |
| `/api/v1/documents` | `documents` | 8 |
| `/api/v1/index-tasks` | `index_tasks` | 4 |
| `/api/v1/faqs` | `faqs` | 6 |
| `/api/v1/synonyms` | `synonyms` | 6 |
| `/api/v1/search` | `qa` | 1 |
| `/api/v1/ask` | `qa` | 3（含 `/ask/agent`） |
| `/api/v1/agent` | `agent` | 1（`/chat`） |
| `/api/v1/kb-health` | `kb_health` | **3（新增）** |
| `/api/v1/llm-cost` | `llm_cost` | **3（新增）** |
| `/api/v1/refusal` | `refusal` | **2（新增）** |
| `/api/v1/conversations` | `conversations` | 7 |
| `/api/v1/messages` | `messages` | 6 |
| `/api/v1/sensitive-words` | `sensitive_words` | 6 |
| `/api/v1/logs` | `query_logs` | 1 |
| `/api/v1/stats` | `stats` | 2 |
| `/api/v1/eval-cases` | `eval_cases` | 6 |
| `/api/v1/feedback` | `feedback` | 5 |
| `/api/v1/unanswered` | `unanswered` | 4 |

---

## 下一阶段预告

| 阶段 | 内容 | 依赖 |
|------|------|------|
| **阶段 6** | 前端对接 | 阶段 5 完成（当前阶段） |
| **阶段 7** | 集成测试 + 灰度 | 阶段 6 完成 |

---
