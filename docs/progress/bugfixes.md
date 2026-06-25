### 修复 1：`qa_service.py` `estimate_tokens` 导入错误

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 4 / Bug 修复 |
| **修改文件** | `backend/app/services/qa_service.py` |
| **关联阶段** | 阶段 4（操作 4-1：`agent_chat` 集成 Agent 工作流） |

**问题**：`agent_chat` 函数第 278 行 `from app.core.llm import estimate_tokens`，但 `llm.py` 只导出 `chat` / `chat_stream`，`estimate_tokens` 实际定义在 `qa_service.py` 第 19 行。调用 `agent_chat` 时会触发 `ImportError`。

**原因**：阶段 4 编码时误以为 `estimate_tokens` 已提取到 `llm.py`，实际未提取。

**修复**：删除错误的跨模块导入，直接使用函数内已定义的 `_estimate_tokens()` 函数。

**验证**：`.venv/Scripts/python.exe -c "from app.services.qa_service import agent_chat; print('OK')"`

---

### 修复 2：`main.py` 生命周期管理混乱

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 1-P0 / Bug 修复 |
| **修改文件** | `backend/app/main.py` |
| **关联阶段** | 阶段 1（操作 1-10：`main.py` 注册 agent 路由） |

**问题**：
1. 使用已弃用的 `@app.on_event("startup")` / `@app.on_event("shutdown")` 装饰器
2. 文件后半段定义了 `lifespan` 异步上下文管理器，但**从未挂载到 `FastAPI` 实例**
3. `lifespan` 内引用了未定义的 `logger` 变量
4. 两套生命周期逻辑同时存在，`lifespan` 完全不生效

**原因**：阶段 1 编码时预留了 `lifespan` 位置但未完成集成，后续迭代也未清理。

**修复**：
- 统一使用 `lifespan` 模式，将启动/关闭逻辑迁移到 `lifespan` 函数内
- 将 `lifespan` 挂载到 `FastAPI` 实例（`lifespan=lifespan`）
- 删除 `@app.on_event` 装饰器和未挂载的 `lifespan` 死代码
- 模块顶层定义 `logger`，确保 `lifespan` 内可正常使用

**验证**：`.venv/Scripts/python.exe -c "from app.main import app; print('OK')"`

---

### 修复 3：`routers/qa.py` `/ask/agent` 忽略 `agent_enabled` 开关

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 4 / Bug 修复 |
| **修改文件** | `backend/app/routers/qa.py` |
| **关联阶段** | 阶段 4（操作 4-2：`routers/qa.py` 新增 Agent 端点） |

**问题**：`/ask/agent` 端点直接调用 `qa_service.agent_chat()`，**未检查** `agent_enabled` 配置。而 `routers/agent.py` 的 `/chat` 端点会检查该开关并回退到传统 RAG。

**影响**：当 `agent_enabled=False` 时，`/ask/agent` 仍然走 Agent 工作流，与渐进式迁移策略不一致。

**修复**：在 `/ask/agent` 端点内加入 `agent_enabled` 判断，关闭时回退到 `rag_service.ask()`。

**验证**：`.venv/Scripts/python.exe -c "from app.routers.qa import router; print('OK')"`

---

### 修复 4：`agent_timeout_seconds` 配置项未实际生效

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 1-P0 / 稳定性修复 |
| **修改文件** | `backend/app/routers/agent.py` |
| **关联阶段** | 阶段 1（操作 1-2：`config.py` 加 Agent 配置项） |

**问题**：`config.py` 定义了 `agent_timeout_seconds: int = 60`，但 `_run_agent` 中的 `app.invoke()` 调用**没有 timeout 包装**。单个慢查询可无限期阻塞 worker。

**原因**：阶段 1 编码时只定义了配置项，未在调用处实际使用。

**修复**：
- 使用 `asyncio.wait_for` + `run_in_executor` 包装 `app.invoke()`，超时后返回降级响应
- 超时日志记录 user_id / conv_id / 超时秒数
- 超时响应包含 `is_error=True`、`should_refuse=True`、友好提示

**验证**：`.venv/Scripts/python.exe -c "from app.routers.agent import _run_agent; print('OK')"`

---

### 修复 5：`sqlite_checkpoint.py` 重复 return 死代码

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 1-P1 / Bug 修复 |
| **修改文件** | `backend/app/agent/sqlite_checkpoint.py` |
| **关联阶段** | 阶段 1（操作 1-11：实现持久化 SqliteSaver） |

**问题**：`_row_to_tuple` 方法第 264 行已有 `return CheckpointTuple(...)`，第 271-276 行存在完全相同的重复 return 块（第 270 行空行），后半段永远不可达。

**原因**：疑似合并冲突残留或编辑时未清理。

**修复**：删除第 271-276 行的重复 return 块，保留唯一正确的 return 语句。

**验证**：`.venv/Scripts/python.exe -c "from app.agent.sqlite_checkpoint import SqliteSaver; print('OK')"`

---

### 修复 6：`monitor/scheduler.py` 补充缺失定时任务

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 3 / 功能补全 |
| **修改文件** | `backend/app/monitor/scheduler.py` |
| **关联阶段** | 阶段 3（操作 3-5：配置 APScheduler 定时任务） |

**问题**：仅配置了 `kb_health_check`（02:00）和 `llm_cost_check`（02:30），但方案要求 `citation_evaluator` 和一致性检查也应有定期评估任务。监控数据覆盖不完整。

**原因**：阶段 3 编码时只实现了基础 2 个任务，未完成全部监控项的定时评估。

**修复**：
- 新增 `citation_quality_check`（02:15）：批量评估近 24 小时内有引用的 AI 回答质量
- 新增 `consistency_check`（02:45）：批量检查近 24 小时内的 consistency_issues 并写入 `ConsistencyIssueLog`
- 新增 `_run_citation_quality_check()` 和 `_run_consistency_check()` 实现
- 更新模块 docstring 和启动日志

**验证**：`.venv/Scripts/python.exe -c "from app.monitor.scheduler import setup_scheduler; print('OK')"`

---

### 修复 7：`hallucination_defense.py` `min_results` 公式与方案不一致

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 2 / 正确性修复 |
| **修改文件** | `backend/app/agent/hallucination_defense.py` |
| **关联阶段** | 阶段 2（操作 2-1：确认 hallucination_defense 集成状态） |

**问题**：`should_accept_result` 方法中 `min_results` 计算公式为 `max(1, base_config["min_results"] - retry_attempt)`，与方案文档中的动态阈值表不一致。

**方案要求 vs 当前实现对比：**

| 重试次数 | 高风险(方案) | 高风险(实际) | 中风险(方案) | 中风险(实际) | 低风险(方案) | 低风险(实际) |
|----------|------------|------------|------------|------------|------------|------------|
| 0 | 3 | 3 | 2 | 2 | 1 | 1 |
| 1 | 2 | 1 | 2 | 1 | 1 | 1 |
| 2 | 2 | 2 | 1 | 1 | 1 | 1 |
| 3+ | 1 | 1 | 1 | 1 | 1 | 1 |

**影响**：重试 1 次时，高风险和中风险的 `min_results` 被错误地降低（高风险应为 2 而非 1，中风险应为 2 而非 1），可能导致置信度不足时过早接受结果。

**修复**：
- 将 `min_results` 计算改为查表方式，精确对齐方案文档
- 新增 `min_results_map` 字典，按重试次数和风险等级精确映射
- 在 docstring 中补充完整的阈值表

**验证**：`.venv/Scripts/python.exe -c "from app.agent.hallucination_defense import threshold_checker; ..."`

---

### 优化 8：Agent 工作流 LLM Token 真实追踪

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段 1-P0 / 优化（token 追踪精度） |
| **修改文件** | `backend/app/core/llm.py`、`backend/app/agent/nodes.py`、`backend/app/routers/agent.py`、`backend/app/services/qa_service.py` |
| **关联阶段** | 阶段 1（操作 1-25：修复 Token 统计） |

**问题**：
- `llm.py` 的 `chat()` 调用 DashScope 后丢弃 `resp.usage`，返回纯文本
- `nodes.py` 的 `generate_response` / `regenerate_with_hints` 用 `_estimate_tokens()` 估算 token 数（非真实值）
- `routers/agent.py` + `qa_service.py` 落库时 `prompt_tokens=0`，`completion_tokens` 为估算值
- `cost_monitor` 对 agent 查询的成本统计完全失真

**修复**：
- `llm.py`：新增 `chat_with_usage()` 返回 `(content, {prompt_tokens, completion_tokens})`，提取 `_chat_completion()` 共享底层调用，避免重复代码
- `nodes.py`：`generate_response` / `regenerate_with_hints` 改用 `chat_with_usage()`，真实 token 写入 state 的 `llm_tokens_in/out`
- `routers/agent.py`：`_run_agent` 输出增加 `llm_tokens_in/out`；`_save_agent_messages` 写入真实值
- `qa_service.py`：`agent_chat` 从 workflow result 读取真实 token，废弃 `_estimate_tokens()`
- 删除 `nodes.py` 和 `qa_service.py` 中的 `_estimate_tokens()` 死代码

**不变更**：`chat()` / `chat_stream()` 公共 API 保持向后兼容，`rag_service.py` 等非 agent 调用方不受影响。

---

## 修复后验证汇总

| 验证项 | 命令 | 结果 |
|--------|------|------|
| 应用构建 | `.venv/Scripts/python.exe -c "from app.main import app; print('OK')"` | ✅ |
| Agent 路由导入 | `from app.routers.agent import _run_agent` | ✅ |
| QA 路由导入 | `from app.routers.qa import router` | ✅ |
| QA Service 导入 | `from app.services.qa_service import agent_chat` | ✅ |
| SqliteSaver 导入 | `from app.agent.sqlite_checkpoint import SqliteSaver` | ✅ |
| Scheduler 导入 | `from app.monitor.scheduler import setup_scheduler` | ✅ |
| 配置项校验 | `agent_timeout_seconds=60, agent_enabled=True` | ✅ |
| Token 追踪验证 | `tests/test_token_tracking.py` | ✅ |

---
