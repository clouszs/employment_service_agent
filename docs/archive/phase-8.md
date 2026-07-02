# 阶段 8 进度追踪：单智能体稳固期

> **目标**：修复已知 bug、清理技术债务、建立测试基础
> **前置条件**：阶段 0-7 全部完成
> **开始时间**：2026-06-27

---

## 操作记录

### 操作 8-5：清理文档重复章节

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **修改文件** | `docs/Agent模块融合实施方案.md` |
| **操作** | 第 8 章「Agent 死循环防护」顶部增加说明：本章为各阶段死循环防护内容的汇总参考，详细实现见阶段 0-7 实施文档。避免读者误以为需要重新实现。 |

---

### 操作 8-7：标准化 AgentState TypedDict

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **修改文件** | `backend/app/agent/state.py` |
| **修改前** | `class AgentState(Annotated[dict, "AgentState"]):` — 不是合法 TypedDict |
| **修改后** | `class AgentState(TypedDict):` — 标准 TypedDict 定义，IDE 类型检查生效 |
| **验证** | `from app.agent.state import AgentState; print(type(AgentState).__name__)` 输出 `_TypedDictMeta` |

---

### 操作 8-9：verify_facts 增加基础验证

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **修改文件** | `backend/app/agent/hallucination_defense.py` |
| **修改内容** | `FactVerificationPostProcessor.verify()` V1 增强：对提取到的事实要素，检查是否被引用内容支持 |
| **验证逻辑** | policy_no/date 做精确匹配；money/count 做核心数字匹配 |
| **测试覆盖** | 3 个新测试：有引用支持 / 无引用支持 / 无引用 |

---

### 操作 8-6：建立单元测试框架

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-27 |
| **新建文件** | `backend/pytest.ini` — pytest 配置文件 |
| **新建文件** | `backend/tests/conftest.py` — 公共 fixtures（SQLite 内存数据库、TestClient） |
| **新建文件** | `backend/tests/test_agent_workflow_supplement.py` — 7 个补充测试 |
| **测试结果** | 14 passed, 2 warnings in 30.00s |

**测试覆盖矩阵**：

| 测试文件 | 测试数 | 覆盖内容 |
|----------|--------|----------|
| `test_agent_workflow.py` | 6 | 路由、检索去重、动态阈值、置信度重试、内容审核、错误处理 |
| `test_agent_workflow_supplement.py` | 7 | verify_facts(3)、accept_with_warning(3)、direct_response(1) |
| `test_checkpoint_persistence.py` | 1 | Checkpoint 持久化 |
| **合计** | **14** | **通过率 100%** |

---

## 阶段 8 验收清单

| 验收项 | 状态 | 说明 |
|--------|------|------|
| temporal_warnings 前端可见 | ✅ | 阶段 7 已完成 |
| agent_chat() 超时保护 | ✅ | 阶段 7 已完成 |
| 死代码文件已删除 | ✅ | 阶段 7 已完成 |
| Graph 编译仅执行 1 次 | ✅ | 阶段 7 已完成 |
| 单元测试通过率 ≥ 80% | ✅ | **14 passed, 100% 通过率** |
| AgentState 为合法 TypedDict | ✅ | 已标准化 |
| 两个 Agent 端点已合并 | ⏸️ 待评估 | 见下方评估报告 |

---

## 8-8 端点合并评估报告

### 现状分析

| 端点 | 位置 | 功能 | 调用方式 |
|------|------|------|----------|
| `POST /api/v1/agent/chat` | `routers/agent.py` | Agent 同步对话 | 前端 ChatView 调用 |
| `POST /api/v1/qa/ask/agent` | `routers/qa.py` | Agent 问答(同步) | 内部调用 / 渐进式迁移 |

**重复逻辑对比**：

| 逻辑 | routers/agent.py | routers/qa.py |
|------|------------------|---------------|
| Agent 开关判断 | ✅ `agent_enabled` 判断 | ✅ `agent_enabled` 判断 |
| 调用 `qa_service.agent_chat()` | ❌ 直接调用 `_run_agent()` | ✅ 调用 `qa_service.agent_chat()` |
| 消息保存 | ✅ `_save_agent_messages()` | ✅ `qa_service.agent_chat()` 内部保存 |
| 语义缓存 | ✅ 有 | ❌ 无 |
| 限流 | ✅ 有 (`_RateLimiter`) | ❌ 无 |
| 响应格式 | `AgentChatResponse` | `success(result)` |

### 合并利弊分析

#### 合并的收益

1. **消除重复逻辑**：`agent_enabled` 判断、消息保存逻辑只需维护一份
2. **统一限流**：`routers/agent.py` 的 `_RateLimiter` 可覆盖所有 Agent 端点
3. **统一语义缓存**：缓存命中率可提升
4. **减少维护成本**：后续修改只需改一处

#### 合并的风险

1. **破坏渐进式迁移**：`routers/qa.py` 的 `/ask/agent` 设计为"渐进式迁移"开关，合并后无法独立开关
2. **破坏现有前端调用**：前端 ChatView 已对接 `/api/v1/agent/chat`，合并后需要改前端
3. **破坏 API 兼容性**：`/ask/agent` 已有调用方，合并后路径变化需要协调
4. **增加单文件复杂度**：`routers/qa.py` 会变得更长，违反单一职责

### 结论

**建议：暂不合并，保持现状**。

**理由**：
1. 两个端点的定位不同：`/agent/chat` 是 Agent 专属入口，`/ask/agent` 是渐进式迁移入口
2. 合并收益有限（主要是消除重复的 `agent_enabled` 判断），但风险较高（破坏渐进式迁移、需要协调前端）
3. 当前重复逻辑简单，维护成本低
4. 后续如果引入多智能体（Supervisor），两个端点会有不同的路由逻辑，分开更清晰

**替代方案（低成本）**：
- 将 `agent_enabled` 判断抽取为装饰器 `require_agent_enabled()`，两个端点复用
- 将 `_save_agent_messages()` 抽取为 `utils/agent.py`，两个端点复用

---

## 下一步

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 8 | 单智能体稳固期 | 🔄 进行中（8-1~8-7 已完成，8-8 评估完成，待用户决定） |
| 阶段 9 | 单智能体扩展期 | ⏸️ 待阶段 8 完成后启动 |

**请确认**：
1. 是否接受 8-8 的评估结论（暂不合并端点）？
2. 是否进入阶段 9（单智能体扩展期）？
