### 阶段 4 Phase 4：问答服务升级（2026-06-25）

> 目标：将现有 `qa_service.py` 从纯 RAG 升级为集成 Agent 工作流，新增 `/ask/agent` 端点。

#### 操作 4-1：扩展 qa_service.py 集成 Agent 工作流

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段4 / 问答服务 |
| **修改文件** | `backend/app/services/qa_service.py` |

**新增方法：**

| 方法 | 说明 |
|------|------|
| `agent_chat(db, user_id, query, conversation_id, client_ip)` | Agent 问答入口，返回 enriched result |

**流程：**
1. `resolve_conversation()` → 创建/获取会话
2. `get_agent_graph().compile().invoke()` → 执行 Agent 工作流
3. 保存用户消息 + AI 回答 → `QaMessage`
4. 保存引用 → `QaMessageReference`
5. 记录查询日志 → `OpQueryLog`
6. 返回 enriched result → 包含 `citations` / `confidence` / `warnings` 等

**返回字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `conversation_id` | int | 会话 ID |
| `message_id` | int | 回答消息 ID |
| `response` | str | 回答内容 |
| `is_no_answer` | bool | 是否无答案 |
| `blocked` | bool | 是否被拦截 |
| `from_faq` | bool | 是否 FAQ 命中 |
| `references` | list | 引用列表 |
| `confidence` | float | 置信度 |
| `route` | str | 路由决策 |
| `query_risk_level` | str | 风险等级 |
| `is_low_confidence` | bool | 是否低置信度 |
| `consistency_issues` | list | 一致性问题 |
| `fact_issues` | list | 事实核验问题 |
| `temporal_warnings` | list | 时效性警告 |
| `warnings` | list | 警告列表 |

#### 操作 4-2：routers/qa.py 新增 Agent 端点

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段4 / API 路由 |
| **修改文件** | `backend/app/routers/qa.py` |

**新增端点：**

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/ask/agent` | POST | Agent 问答（同步，集成 Agent 工作流） |

**渐进式迁移：**
- `agent_enabled=False` 时，前端仍可显式调用 `/api/v1/ask/agent`
- 旧 `/ask` 和 `/ask/stream` 端点保持不变，向后兼容

#### 操作 4-3：阶段4 自测

| 测试项 | 结果 | 问题 |
|--------|------|------|
| `qa_service.agent_chat()` import | ✅ 通过 | 初始缺少 `estimate_tokens`，已在 `qa_service.py` 内定义 `_estimate_tokens()` |
| `routers/qa.py` 路由注册 | ✅ 通过 | 初始路径匹配错误，已修正为短路径 |
| `app.main:app` 构建 | ✅ 通过 | — |

**自测命令：**
```bash
cd backend
.venv/Scripts/python.exe tests/test_qa_service.py
```

**踩坑记录：**

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| `cannot import name 'estimate_tokens' from 'app.core.llm'` | `estimate_tokens` 定义在 `agent/nodes.py` 中，不在 `core/llm.py` | 在 `qa_service.py` 内定义本地 `_estimate_tokens()` |
| 路由路径匹配失败 | `router.routes` 返回的是 `/search`、`/ask` 等，不是完整前缀 `/api/v1/...` | 测试脚本中改用短路径匹配 |

#### 阶段 4 验收

| 优化项 | 状态 | 备注 |
|--------|------|------|
| 扩展 `qa_service.py` | ✅ | 新增 `agent_chat()` 方法 |
| 新增 `/ask/agent` 端点 | ✅ | `routers/qa.py` |
| 自测通过 | ✅ | `tests/test_qa_service.py` |
| `app.main:app` 构建无报错 | ✅ | 验证通过 |

**验证命令：**
```bash
cd backend
# 1. 应用构建
.venv/Scripts/python.exe -c "from app.main import app; print('OK')"

# 2. import 验证
.venv/Scripts/python.exe -c "
from app.services.qa_service import agent_chat;
from app.routers.qa import router;
print('Stage 4 imports OK')
"

# 3. QA 服务测试
.venv/Scripts/python.exe tests/test_qa_service.py
```

---

## Bug 修复记录（2026-06-25）

> 本批修复覆盖阶段 1-P0/P1 遗留问题、阶段 3 缺失项、阶段 4 接口一致性问题，共 6 项。
