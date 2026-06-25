### 阶段 2 Phase 2：幻觉防御集成（2026-06-25）

> 目标：将动态阈值、一致性检查、事实核验、拒答模板、引用追踪、时效感知检索集成到节点流程，实现五重防护能力。

#### 阶段 2 前置状态确认

| 组件 | 状态 | 说明 |
|------|------|------|
| `hallucination_defense.py` | ✅ 已完成 | 动态阈值 + 一致性检查 + 事实核验 |
| `nodes.py` 五重防护节点 | ✅ 已完成 | route/search/check_confidence/generate/check_consistency/verify_facts/content_moderation/regenerate/accept_with_warning/error_handler |
| `graph.py` 工作流图 | ✅ 已完成 | 11 节点 + 条件边 + recursion_limit=15 |
| `refusal_handler.py` | ✅ 已完成 | 拒答模板（V1 简化版，不调 LLM） |
| `citation_tracker.py` | ✅ 已完成 | V1 chunk 级别引用 + 质量评估 |
| `temporal_retriever.py` | ✅ 已完成 | V1 过期文档过滤 + 降权标记 |

#### 操作 2-1：确认 hallucination_defense 集成状态

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段2 / 幻觉防御 |
| **涉及文件** | `backend/app/agent/hallucination_defense.py` |
| **状态** | ✅ 已完成，阶段1 已集成 |

**当前实现：**

| 类 | 状态 | 说明 |
|----|------|------|
| `DynamicConfidenceThreshold` | ✅ 已实现 | 按风险等级使用不同阈值，重试时动态降级（每次 -0.15，保底 0.30） |
| `SelfConsistencyChecker` | ✅ 已实现 | V1 简化版，关键词矛盾检测 |
| `FactVerificationPostProcessor` | ✅ 已实现 | 正则验证政策编号、日期、金额、数量 |

**接入位置：**
- `nodes.py` 的 `check_confidence` 节点调用 `threshold_checker.should_accept_result()`
- `nodes.py` 的 `check_consistency` 节点调用 `consistency_checker.check()`
- `nodes.py` 的 `verify_facts` 节点调用 `fact_verifier.verify()`

#### 操作 2-2：确认 graph.py 工作流图完整

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段2 / 工作流 |
| **涉及文件** | `backend/app/agent/graph.py` |
| **状态** | ✅ 已完成，阶段1 已集成 |

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

**关键防护配置：**

| 防护类型 | 实现 | 位置 |
|----------|------|------|
| 递归限制 | `recursion_limit=15` | `graph.py` compile |
| 语义去重 | 相同查询跳过 | `search_knowledge` 节点 |
| 工具计数 | ≥3 强制生成 | `route_query` 节点 |
| 动态阈值 | 每次 -0.15，保底 0.30 | `check_confidence` 节点 |
| 最大重试 | 3 次后降级 | `check_confidence` 节点 |
| 严重度分级 | high 重试，medium 警告 | `check_consistency` 节点 |
| 重生成限制 | 最多 2 次 | `regenerate_with_hints` 节点 |
| 内容审核 | 输出侧关键词匹配 | `content_moderation` 节点 |

#### 操作 2-3：创建 refusal_handler.py

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段2 / 拒答模板 |
| **新建文件** | `backend/app/agent/refusal_handler.py` |

**模板清单：**

| 模板 | 用途 |
|------|------|
| `REFUSAL_TEMPLATE` | 通用拒答模板（含问题 + 原因 + 建议） |
| `NO_RESULT_REFUSAL` | 检索无结果拒答 |
| `LOW_CONFIDENCE_REFUSAL` | 低置信度拒答 |
| `BLOCKED_REFUSAL` | 违规内容拒答 |
| `CONSISTENCY_REFUSAL` | 一致性冲突拒答 |
| `FACT_VERIFICATION_REFUSAL` | 事实核验问题拒答 |

**接口：**

| 函数 | 说明 |
|------|------|
| `get_refusal_response(reason, question)` | 生成通用拒答回复 |
| `get_refusal_by_type(refusal_type, question)` | 根据类型获取拒答回复 |

**V1 简化说明：**
- 不调 LLM 生成拒答回复，直接返回模板
- 节省成本 + 降低延迟
- V2 可改为 LLM 生成个性化拒答

#### 操作 2-4：创建 citation_tracker.py V1 简化版

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段2 / 引用追踪 |
| **新建文件** | `backend/app/agent/citation_tracker.py` |

**V1 实现：**

| 组件 | 说明 |
|------|------|
| `build_citations(hits)` | 从检索结果构建 chunk 级别引用列表 |
| `evaluate_citation_quality(citations)` | 基于检索得分评估引用质量 |

**V2 预留接口：**

| 组件 | 说明 |
|------|------|
| `SentenceLevelCitationTracker` | 句子级别引用追踪（V2 实现） |
| `track(response, source_chunks)` | 逐句验证引用支持度 |

**V1 简化说明：**
- 不做句子级别切分
- 不做 LLM 验证支持度
- 仅基于检索得分做质量统计

#### 操作 2-5：创建 temporal_retriever.py V1 简化版

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段2 / 时效感知 |
| **新建文件** | `backend/app/agent/temporal_retriever.py` |

**V1 实现：**

| 函数 | 说明 |
|------|------|
| `filter_expired_docs(db, doc_ids)` | 过滤已过期文档 ID |
| `get_expiring_soon_docs(db, warning_days)` | 获取即将过期文档 |
| `apply_temporal_adjustment(hits, expired_ids)` | 对检索结果标记过期状态 |

**V2 预留接口：**

| 组件 | 说明 |
|------|------|
| `TemporalAwareRetriever` | 完整时效感知检索（V2 实现） |

**V1 简化说明：**
- 不做时效性得分计算
- 不做综合得分排序
- 仅过滤/标记过期文档

#### 操作 2-6：nodes.py 集成新增组件

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-25 |
| **模块** | 阶段2 / 节点集成 |
| **修改文件** | `backend/app/agent/nodes.py` |

**集成明细：**

| 节点 | 集成内容 | 说明 |
|------|----------|------|
| `search_knowledge` | 引用 `filter_expired_docs` + `apply_temporal_adjustment` | 过期文档过滤 + 标记 |
| `search_knowledge` | 引用 `build_citations`（从 `citation_tracker`） | 统一引用构建 |
| `generate_refusal` | 引用 `get_refusal_response`（从 `refusal_handler`） | V1 不调 LLM |

**新增 import：**

| import | 来源 | 用途 |
|--------|------|------|
| `filter_expired_docs, apply_temporal_adjustment` | `temporal_retriever` | 时效性调整 |
| `build_citations` | `citation_tracker` | 引用构建 |
| `get_refusal_response` | `refusal_handler` | 拒答模板 |
| `SessionLocal` | `core.database` | 检索节点内建 DB 会话 |

**清理内容：**
- 移除 `REFUSAL_SYSTEM_PROMPT`、`REFUSAL_USER_PROMPT` import（不再使用）
- 移除 `_build_citations` 本地函数（统一引用 `citation_tracker.build_citations`）

#### 阶段 2 验收

| 优化项 | 状态 | 备注 |
|--------|------|------|
| 确认 hallucination_defense 集成 | ✅ | `nodes.py` 三处调用 |
| 确认 graph.py 工作流完整 | ✅ | 11 节点 + 条件边 |
| 创建 refusal_handler.py | ✅ | 6 个模板 + 2 个接口 |
| 创建 citation_tracker.py V1 | ✅ | chunk 级别引用 + 质量评估 |
| 创建 temporal_retriever.py V1 | ✅ | 过期过滤 + 标记 |
| nodes.py 集成新组件 | ✅ | 4 处集成 |
| 清理旧 import / 函数 | ✅ | 移除 refusal prompt import + _build_citations |
| 集成测试 42 项 | ✅ | 全部通过 |
| `app.main:app` 构建无报错 | ✅ | 验证通过 |

**验证命令：**
```bash
cd backend
# 1. 应用构建
.venv/Scripts/python.exe -c "from app.main import app; print('OK')"

# 2. 全量 import 验证
.venv/Scripts/python.exe -c "
from app.agent.nodes import (
    route_query, search_knowledge, check_confidence,
    generate_response, check_consistency, verify_facts,
    content_moderation, generate_refusal, direct_response,
    accept_with_warning, error_handler, regenerate_with_hints,
);
from app.agent.hallucination_defense import threshold_checker, consistency_checker, fact_verifier;
from app.agent.citation_tracker import build_citations, evaluate_citation_quality;
from app.agent.refusal_handler import get_refusal_response;
from app.agent.temporal_retriever import filter_expired_docs, apply_temporal_adjustment;
from app.agent.graph import get_agent_graph;
print('All imports OK')
"

# 3. 集成测试
.venv/Scripts/python.exe tests/test_agent_integration.py
```

---
