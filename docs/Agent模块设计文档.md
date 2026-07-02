# 高校智慧就业服务平台 - Agent 智能体模块设计方案
> **文档版本**：v3.0（设计愿景参考）
> **注意**：本文为设计愿景参考文档，非实现记录。实际架构决策以 `architecture/ARCHITECTURE_DECISIONS.md` 为准，能力清单以 `modules/CURRENT_CAPABILITIES.md` 为准。部分设计（如多智能体拓扑、句子级引用）尚未落地。

---

## 重大更新说明

### v3.0 更新（2026-06-23）

| 更新项 | v2.0 方案 | v3.0 新方案 | 改进效果 |
|--------|----------|------------|----------|
| 幻觉防护 | 三重防护 | **五重防护机制** | 动态阈值 + 自我一致性 + 事实核验 |
| 溯源粒度 | Chunk级别引用 | **句子级别引用 + 引用验证** | 精确到句子，验证支持度 |
| 文档切分 | 固定chunk_size | **语义感知切分** | 基于Embedding相似度智能切分 |
| 时效管理 | 版本管理 | **健康度监控 + 时效感知检索** | 自动告警 + 检索降权 |
| 成本控制 | 无 | **LLM成本监控告警** | 每日/每月阈值 + 告警通知 |
| 可观测性 | 基础日志 | **拒答分析 + 引用质量评估** | 持续优化闭环 |

### v2.0 更新（2026-06）

| 更新项 | 原方案 | 新方案 | 改进效果 |
|--------|--------|--------|----------|
| Agent 框架 | 自研工作流 | **LangGraph** | 支持状态追踪、分支、循环，业界标准 |
| LLM 监控 | 无 | **LangSmith** | 完整调用链追踪、Prompt 版本管理 |
| 检索引擎 | ChromaDB 简单检索 | **ChromaDB + 时效性调整** | 时效感知 + 语义缓存，检索质量大幅提升 |
| 幻觉问题 | Prompt 约束 | **三重防护** | 置信度过滤 + 引用强制 + 拒答机制 |
| 溯源问题 | 简单引用 | **引用链路追踪** | 精确到句子级别的溯源 |
| 时效问题 | 无 | **知识库版本管理** | 时效性标记 + 实时数据通道 |

---

## 面试核心要点总结

> ⚠️ **重要**：以下内容是面试时需要重点展示的技术亮点，建议熟练掌握。

### 1. 技术选型亮点

| 技术 | 面试价值 | 常见面试问题 |
|------|----------|-------------|
| **LangGraph** | 展示Agent工程化能力 | "为什么不用简单的循环？Checkpoint怎么实现？" |
| **LangSmith** | 展示可观测性思维 | "如何追踪LLM调用链？成本怎么控制？" |
| **检索方案** | 展示RAG深度理解 | "ChromaDB检索怎么做？时效性调整原理是什么？" |
| **语义切分** | 展示对传统切分局限的理解 | "为什么不用固定chunk_size？语义断点怎么找？" |

### 2. 大模型问题解决方案亮点

| 问题 | 解决方案 | 面试价值 |
|------|----------|----------|
| **幻觉** | 五重防护机制 | 展示系统性思维，不只是单点防护 |
| **溯源** | 句子级别引用 + 引用验证 | 展示对引用精度的追求 |
| **时效** | 健康度监控 + 时效感知检索 | 展示可观测性和算法优化能力 |

### 3. 工程化亮点

| 能力 | 实现方式 | 面试价值 |
|------|----------|----------|
| **成本控制** | 每日阈值 + 告警通知 | 展示生产级系统思维 |
| **持续优化** | 拒答反馈 + 引用质量评估 | 展示数据驱动优化闭环 |
| **健康监控** | 自动检查 + 告警推送 | 展示主动运维能力 |

---

## 一、项目概述

### 1.1 项目背景

高校就业指导工作面临以下痛点：
- 咨询量大且重复率高（80%问题为常见问题）
- 服务时间受限（工作日8小时，无法覆盖学生碎片化咨询需求）
- 信息分散（政策、流程、招聘信息分布在不同系统）
- 个性化服务能力不足（难以针对学生具体情况提供精准指导）
- **大模型幻觉问题**：AI 可能编造不存在的政策或流程
- **引用不可溯源**：无法验证回答的准确性
- **知识时效性差**：政策文件更新后 AI 仍用旧知识回答

### 1.2 项目目标

构建一个 **Agent 智能体驱动的智慧就业服务平台**，实现：
- 7×24 小时智能问答服务
- 主动式就业指导（基于学生画像的个性化推荐）
- 任务执行能力（预约、查询、生成等）
- **可溯源的回答**：每条回答都能追溯到具体来源
- **实时知识更新**：政策变化能及时反映在回答中
- **可观测的系统**：完整的 LLM 调用链路追踪

### 1.3 技术选型理由

#### 为什么选择 LangGraph？

| 维度 | 自研工作流 | LangGraph | 结论 |
|------|-----------|-----------|------|
| 状态管理 | 需要自己实现 | 内置状态机 | ✅ LangGraph 更完善 |
| 循环支持 | 需要递归实现 | 原生支持 | ✅ LangGraph 更自然 |
| Checkpoint | 无 | 支持暂停/恢复 | ✅ LangGraph 支持复杂对话 |
| 调试工具 | 无 | 内置可视化调试 | ✅ LangGraph 面试加分 |
| 社区生态 | - | LangChain 生态 | ✅ LangGraph 是主流 |

**LangGraph 面试价值**：
- 展示对 LLM Agent 工程化的理解（不是调 API 那么简单）
- 体现对复杂系统设计的思考（有状态、多步骤、循环）
- 表明紧跟业界最佳实践

#### 为什么选择 LangSmith？

| 维度 | 无监控 | LangSmith | 结论 |
|------|--------|-----------|------|
| 调用追踪 | 无 | 完整链路记录 | ✅ LangSmith 完整 |
| Prompt 管理 | 无 | 版本控制 | ✅ LangSmith 便捷 |
| 性能分析 | 无 | 自动分析 | ✅ LangSmith 智能 |
| 调试效率 | 低 | 高 | ✅ LangSmith 高效 |
| 成本 | - | $0.003/1k tokens | ✅ 可接受 |

**LangSmith 面试价值**：
- 展示工程化思维（不是跑通就行，还要监控）
- 体现生产级系统的思考（可观测性是 SRE 核心）
- 表明重视系统稳定性

#### 为什么选择 ChromaDB 直接检索？

| 维度 | 自研检索 | LlamaIndex | ChromaDB 直接 | 结论 |
|------|---------|------------|--------------|------|
| 混合检索 | 需要自己实现 | 内置支持 | 单路向量检索 + 时效性调整 | ✅ ChromaDB 足够 |
| Rerank | 需要集成第三方 | 内置支持 | 通过时效性调整提升排序 | ✅ 减少依赖 |
| Query 改写 | 需要自己实现 | 内置支持 | 可选 LLM-based 改写 | ✅ 按需启用 |
| 多路召回 | 需要自己实现 | 内置支持 | FAQ 快速命中 + 向量检索 | ✅ 满足场景 |
| 引用追踪 | 需要自己实现 | 内置 Citation | metadata + citation_tracker | ✅ 轻量实现 |
| 运维复杂度 | 高 | 中（依赖多） | 低（内嵌模式） | ✅ ChromaDB 更优 |

**实际选型理由**：
- 项目已在使用 ChromaDB 作为向量库，复用现有基础设施
- 就业政策问答场景数据量适中，ChromaDB 足够支撑
- 减少外部依赖（Cohere API、Elasticsearch），降低运维复杂度
- 语义缓存（Redis）已覆盖部分性能优化需求
- 时效性调整直接在检索结果上叠加，无需额外框架

**面试价值**：
- 展示技术选型的务实态度（不盲目追新，根据场景选择）
- 展示对基础设施复用的理解
- 展示减少外部依赖的工程化思维

---

## 二、系统架构

### 2.1 整体架构图（v2.0）

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              用户层                                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │   Web 端       │    │   微信小程序     │    │   企业微信/钉钉集成         │  │
│  │  (Vue3 + TS)   │    │   (原生 + API)   │    │   (企业级对接)             │  │
│  └────────┬────────┘    └────────┬────────┘    └──────────────┬──────────────┘  │
└───────────┼───────────────────────┼───────────────────────────┼─────────────────┘
            │                       │                           │
            ▼                       ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              网关层 (Nginx + API Gateway)                        │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LangSmith 监控层                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    LangSmith Dashboard                                   │   │
│  │   • LLM 调用追踪    • Prompt 版本管理    • 性能分析    • 成本统计        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Agent 核心层 (LangGraph)                            │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                    LangGraph StateGraph                                   │  │
│  │                                                                              │  │
│  │   ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐   │  │
│  │   │  Supervisor │ → │  Router    │ → │  Executor  │ → │  Responder │   │  │
│  │   │  (调度)     │    │  (路由)    │    │  (执行)    │    │  (响应)    │   │  │
│  │   └────────────┘    └────────────┘    └────────────┘    └────────────┘   │  │
│  │           ↑                                                                 │  │
│  │           │ 循环                                                             │  │
│  │           └──────────────────────────────────────────────────────────    │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                            │
│  ┌───────────────────────────────────┼────────────────────────────────────┐  │
│  │                    检查点存储 (Checkpoint)                               │  │
│  │                    支持对话暂停/恢复/回溯                                 │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              检索层 (ChromaDB + 时效性调整)                        │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         Query Engine                                       │  │
│  │                                                                              │  │
│  │   ┌──────────────────────────────────────────────────────────────────┐  │  │
│  │   │  Query Rewriting (QueryEngine)                                     │  │  │
│  │   │  • HyDE (假设性文档嵌入)                                           │  │  │
│  │   │  • 子问题查询                                                       │  │  │
│  │   │  • 同义词扩展                                                       │  │  │
│  │   └──────────────────────────────────────────────────────────────────┘  │  │
│  │                                      ↓                                      │  │
│  │   ┌──────────────────────────────────────────────────────────────────┐  │  │
│  │   │  Retriever (多路召回)                                             │  │  │
│  │   │                                                                       │  │  │
│  │   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │  │  │
│  │   │  │ Vector Search │  │ BM25 (Keyword)│  │ Knowledge Graph │            │  │  │
│  │   │  │  (语义相似度)  │  │  (关键词匹配)  │  │  (知识图谱)   │               │  │  │
│  │   │  └─────────────┘  └─────────────┘  └─────────────┘               │  │  │
│  │   │                                                                       │  │  │
│  │   │  ┌─────────────────────────────────────────────────────────────┐    │  │  │
│  │   │  │  Fusion (多路融合)                                           │    │  │  │
│  │   │  │  RRF (倒数排名融合) / Weighted Sum (加权求和)                │    │  │  │
│  │   │  └─────────────────────────────────────────────────────────────┘    │  │  │
│  │   │                                                                       │  │  │
│  │   │  ┌─────────────────────────────────────────────────────────────┐    │  │  │
│  │   │  │  Rerank (重排序)                                              │    │  │  │
│  │   │  │  Cohere / BGE-Reranker                                        │    │  │  │
│  │   │  └─────────────────────────────────────────────────────────────┘    │  │  │
│  │   │                                                                       │  │  │
│  │   │  ┌─────────────────────────────────────────────────────────────┐    │  │  │
│  │   │  │  Citation (引用追踪)                                          │    │  │  │
│  │   │  │  精确到句子级别的来源标注                                       │    │  │  │
│  │   │  └─────────────────────────────────────────────────────────────┘    │  │  │
│  │   └──────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                            │
│  ┌───────────────────────────────────┼────────────────────────────────────┐  │
│  │                    索引存储层                                             │  │
│  │   ChromaDB (向量)  │  Elasticsearch (全文)  │  Neo4j (知识图谱)        │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              数据层                                             │
│  MySQL 8.0  │  Redis 7.0  │  对象存储 OSS  │  时序数据                       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术架构分层

| 层级 | 技术选型 | 职责 |
|------|---------|------|
| **用户层** | Vue3 + TypeScript | 用户交互界面 |
| **网关层** | Nginx + API Gateway | 请求路由、限流、认证 |
| **监控层** | LangSmith | LLM 调用追踪、Prompt 管理 |
| **Agent 层** | LangGraph | 状态机工作流、工具编排 |
| **检索层** | ChromaDB + 自定义 | ChromaDB 向量检索 + 时效性调整 + 语义缓存 |
| **数据层** | MySQL + Redis | 持久化 + Embedding 缓存（无 OSS） |
| **LLM 层** | 通义千问 / GPT-4 | 核心推理能力 |

---

## 三、大模型问题解决方案

> **本节为设计概念层**：以下代码示例展示的是解决方案的设计思路和算法原理，**并非实际可直接运行的代码**。实际实现请参考：
> - 幻觉防御：`backend/app/agent/hallucination_defense.py`（`threshold_checker`、`consistency_checker`、`fact_verifier`）
> - 引用追踪：`backend/app/agent/citation_tracker.py`（`build_citations()`）
> - 时效调整：`backend/app/agent/temporal_retriever.py`（`apply_temporal_adjustment()`、`filter_expired_docs()`）
> - 健康监控：`backend/app/monitor/health_monitor.py`、`cost_monitor.py`、`citation_evaluator.py`
> - 定时任务：`backend/app/monitor/scheduler.py`
>
> 实际代码基于 **ChromaDB 向量检索**，不使用 LlamaIndex、Cohere Rerank 或 Elasticsearch。

### 3.1 幻觉问题（Hallucination）

#### 问题分析

```
大模型幻觉的常见原因：

1. 知识边界不清
   - 模型不知道自己不知道
   - 对不确定的问题"自信"回答

2. 检索质量差
   - 检索到的文档不相关
   - 上下文窗口有限

3. Prompt 约束不足
   - 没有明确"不知道就说不知道"
   - 没有要求基于证据回答
```

#### 五重防护机制设计思路

```python
# ================================================================
# 设计概念：五重防护机制的算法原理
# 实际实现见 agent/hallucination_defense.py
# ================================================================

# 第一重：动态置信度阈值（设计概念）
# 实际：hallucination_defense.DynamicConfidenceThreshold
# 根据 query_risk_level (high/medium/low) 使用不同阈值
#   high:  min_confidence=0.80, min_results=3
#   medium: min_confidence=0.65, min_results=2
#   low:   min_confidence=0.40, min_results=1

# 第二重：置信度过滤（设计概念）
# 实际：check_confidence 节点中实现
# 过滤掉 score < retrieve_score_threshold 的检索结果

# 第三重：引用强制生成（设计概念）
# 实际：generator.py prompt 中的 SYSTEM_PROMPT 约束
# "每说一个事实，必须在句尾用 [来源: XXX] 标注来源"

# 第四重：自我一致性检查（设计概念）
# 实际：hallucination_defense.SelfConsistencyChecker
# 检查当前回答与历史回答是否矛盾

# 第五重：事实核验（设计概念）
# 实际：hallucination_defense.FactVerificationPostProcessor
# 正则提取政策编号/日期/金额，验证格式和合理性
```

> **与设计文档 v2.0 的差异**：
> - v2.0 设计为"三重防护"（固定阈值 + 引用强制 + 拒答），v3.0 扩展为"五重防护"
> - 第四重（动态阈值）和第五重（事实核验）为 v3.0 新增
> - 实际代码中，五重防护分散在 11 个 LangGraph 节点中实现，而非集中在一个类里

### 3.2 溯源问题（Citation & Traceability）

#### 问题分析

```
溯源问题的挑战：

1. 粒度不够细
   - 只能知道来自哪个文档
   - 无法知道来自哪个段落/句子

2. 引用不准确
   - LLM 可能错误归因
   - 需要自动化的引用验证

3. 链路不完整
   - 看不到检索→筛选→生成的完整链路
   - 调试困难
```

#### 解决方案：精确到句子级别的引用追踪

```python
# ================================================================
# 实际实现：ChromaDB 检索 + citation_tracker.py 构建引用
# ================================================================

from app.agent.citation_tracker import build_citations

# ChromaDB 检索结果自带 metadata（doc_title, valid_until, chunk_id 等）
# citation_tracker.build_citations() 基于检索结果构建句子级引用列表

def build_citations(
    response: str,
    search_results: list[dict],
    max_snippet_length: int = 200,
) -> list[dict]:
    """构建引用列表（agent/citation_tracker.py）。

    流程：
    1. 将回答切分为句子
    2. 对每个句子找到最相关的检索结果
    3. 使用 LLM 验证支持度（direct/indirect/none）
    4. 返回带 ref_id 的引用列表
    """
    ...
```

> **与设计文档 v2.0 的差异**：
> - v2.0 使用 LlamaIndex 内置 Citation 功能，实际代码不依赖 LlamaIndex
> - 引用基于 ChromaDB 检索结果的 metadata 构建
> - 句子级引用通过 `citation_tracker.py` 独立实现，支持度验证使用 LLM judge

### 3.3 时效性问题（Temporal Accuracy）

#### 问题分析

```
时效性问题的挑战：

1. 政策经常变化
   - 落户政策每年调整
   - 补贴标准定期更新

2. 模型知识有截止日期
   - 训练数据有时效限制
   - 无法感知最新政策

3. 缺乏版本管理
   - 不知道知识库有多"新"
   - 无法区分新旧政策
```

#### 解决方案：知识库时效性管理

```python
# ================================================================
# 实际实现：agent/temporal_retriever.py
# V1 简化版：过期文档过滤 + 降权标记（无综合得分排序）
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/agent/temporal_retriever.py`

实际采用 V1 简化方案（非设计文档中的完整综合得分模型）：
- `filter_expired_docs()`：查询 MySQL，返回已过期文档 ID 集合
- `get_expiring_soon_docs()`：供监控模块调用，返回即将过期文档列表
- `apply_temporal_adjustment()`：V1 仅添加 `is_expired` 标记，不修改得分
  （V2 再扩展为综合得分 = similarity × 0.7 + temporal × 0.3）

面试要点：
- V1 保持简单，不影响检索排序，由上层节点决定如何处理过期文档
- V2 TemporalAwareRetriever 已预留接口，支持完整时效感知检索
"""

from datetime import date
from sqlalchemy.orm import Session
from app.models import KbDocument


def filter_expired_docs(db: Session, doc_ids: list[int]) -> set[int]:
    """过滤已过期文档 ID（V1 简化版）。

    仅检查 KbDocument.expire_date，已过期且未设为长期有效的文档会被过滤。
    """
    if not doc_ids:
        return set()

    today = date.today()
    expired_rows = (
        db.query(KbDocument.id)
        .filter(
            KbDocument.id.in_(doc_ids),
            KbDocument.status == 1,
            KbDocument.expire_date.isnot(None),
            KbDocument.expire_date < today,
        )
        .all()
    )
    return {row.id for row in expired_rows}


def get_expiring_soon_docs(db: Session, warning_days: int = 30) -> list[dict]:
    """获取即将过期文档（V1 简化版，供监控模块调用）。

    Args:
        db: 数据库会话
        warning_days: 预警天数（默认 30 天）

    Returns:
        即将过期文档列表
    """
    today = date.today()
    warning_date = today + __import__("datetime").timedelta(days=warning_days)

    rows = (
        db.query(KbDocument)
        .filter(
            KbDocument.status == 1,
            KbDocument.expire_date.isnot(None),
            KbDocument.expire_date >= today,
            KbDocument.expire_date <= warning_date,
        )
        .order_by(KbDocument.expire_date.asc())
        .all()
    )

    return [
        {
            "id": row.id,
            "title": row.title,
            "expire_date": row.expire_date.isoformat() if row.expire_date else None,
            "days_until_expiry": (row.expire_date - today).days if row.expire_date else None,
        }
        for row in rows
    ]


def apply_temporal_adjustment(hits: list[dict], expired_ids: set[int]) -> list[dict]:
    """对检索结果应用时效性调整（V1 简化：仅标记过期）。

    V1 不修改得分，仅对过期文档添加 is_expired 标记，
    由上层节点决定是否降权或展示警告。
    """
    adjusted = []
    for h in hits:
        doc_id = (h.get("metadata") or {}).get("document_id")
        h_copy = dict(h)
        h_copy["is_expired"] = doc_id in expired_ids if doc_id is not None else False
        adjusted.append(h_copy)
    return adjusted
```

> **与设计文档 v2.0 的差异**：
> - v2.0 设计为"知识库版本管理 + 实时数据通道"，实际简化为"时效性调整 + 健康监控"
> - 无 `kb_version` 表和实时 API 通道
> - 时效性信息存储在 ChromaDB metadata 和 `qa_message` JSON 字段中

### 3.4 幻觉问题增强方案（五重防护机制）

> ⚠️ **面试核心要点**：三重防护是基础方案，五重防护是进阶方案，展示对大模型幻觉问题的系统性思考。

#### 问题分析

```
三重防护的局限性：

1. 置信度阈值固定
   - 所有查询类型用同一阈值
   - 政策查询（高风险）和闲聊（低风险）应有不同标准

2. 缺乏一致性验证
   - 同一对话中同类问题可能回答矛盾
   - 用户无法发现AI的"前后不一致"

3. 具体事实缺乏专项验证
   - 政策编号、日期、金额等关键信息可能编造
   - 需要针对性的格式和逻辑验证
```

#### 第四重：动态置信度阈值（设计概念）

```python
# ================================================================
# 实际实现：agent/hallucination_defense.py
# V1 简化版：动态置信度阈值（含重试降级）+ 事实核验（正则提取）
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/agent/hallucination_defense.py`

V1 实现三个核心类，均为简化版：

1. DynamicConfidenceThreshold：按查询风险等级使用不同阈值，支持重试时动态降级
   - classify_query()：根据 constants.py 中的 HIGH_RISK_KEYWORDS / LOW_RISK_KEYWORDS 判断
   - should_accept_result()：每次重试降低 0.15，保底 0.30
   - should_retry()：最多重试 3 次

2. FactVerificationPostProcessor：正则验证政策编号、日期、金额等
   - 当前版本只标记存在的事实要素，不做跨源校验（V2 再加）

3. SelfConsistencyChecker：V1 只做轻量标记
   - 只检查"否定词 + 历史关键词"的明显矛盾
   - 不做多轮生成比对（V2 再扩展）

实际调用关系：
- route_query 节点 → 设置 query_risk_level
- check_confidence 节点 → 调用 threshold_checker.should_accept_result()
- check_consistency 节点 → 调用 consistency_checker.check()
- verify_facts 节点 → 调用 fact_verifier.verify()
"""

# ==================== 动态置信度阈值 ====================


class DynamicConfidenceThreshold:
    """按查询风险等级使用不同阈值，并支持重试时动态降级。"""

    THRESHOLD_CONFIG = {
        "high":   {"min_confidence": 0.80, "min_results": 3, "require_citation": True},
        "medium": {"min_confidence": 0.65, "min_results": 2, "require_citation": True},
        "low":    {"min_confidence": 0.40, "min_results": 1, "require_citation": False},
    }

    # 每次重试降低的阈值幅度
    _THRESHOLD_STEP: float = 0.15
    # 保底阈值
    _MIN_THRESHOLD: float = 0.30
    # 最大重试次数
    _MAX_RETRY: int = 3

    def classify_query(self, query: str) -> str:
        """按关键词判断风险等级。"""
        high_keywords = [
            "落户", "补贴", "政策", "规定", "流程", "申请", "条件",
            "要求", "资格", "审批", "办理", "报到", "档案", "户口",
        ]
        low_keywords = ["你好", "谢谢", "再见", "辛苦", "在吗", "嗨"]

        if any(k in query for k in high_keywords):
            return "high"
        if any(k in query for k in low_keywords):
            return "low"
        return "medium"

    def should_accept_result(
        self,
        query: str,
        confidence: float,
        results_count: int,
        has_citation: bool,
        retry_attempt: int = 0,
    ) -> tuple[bool, str]:
        """判断是否接受检索结果，每次重试自动降低阈值。

        阈值表与方案对齐（按风险等级 + 重试次数）：

        | 重试次数 | 高风险阈值 | 中风险阈值 | 低风险阈值 | 最低结果数(高/中/低) |
        |----------|-----------|-----------|-----------|-------------------|
        | 0 | 0.80 | 0.65 | 0.40 | 3 / 2 / 1 |
        | 1 | 0.65 | 0.50 | 0.30 | 2 / 2 / 1 |
        | 2 | 0.50 | 0.35 | 0.30 | 2 / 1 / 1 |
        | 3+ | 0.30 | 0.30 | 0.30 | 1 / 1 / 1 |

        返回 (是否接受, 不通过原因字符串，通过则为空)。
        """
        risk_level = self.classify_query(query)
        base_config = self.THRESHOLD_CONFIG[risk_level]

        # 阈值：每次重试降低 0.15，保底不低于 _MIN_THRESHOLD
        threshold = max(self._MIN_THRESHOLD, base_config["min_confidence"] - retry_attempt * self._THRESHOLD_STEP)

        # 最低结果数：按方案精确对齐（与阈值不同步降低）
        min_results_map = {
            0: {"high": 3, "medium": 2, "low": 1},
            1: {"high": 2, "medium": 2, "low": 1},
            2: {"high": 2, "medium": 1, "low": 1},
        }
        min_results = min_results_map.get(min(retry_attempt, 2), {}).get(risk_level, 1)

        reasons: list[str] = []
        if confidence < threshold:
            reasons.append(f"置信度{confidence:.2f} < 当前阈值{threshold}")
        if results_count < min_results:
            reasons.append(f"检索结果数{results_count} < 最低要求{min_results}")
        if base_config["require_citation"] and not has_citation:
            reasons.append("该类查询必须有引用来源")

        return (len(reasons) == 0, "; ".join(reasons))

    def should_retry(self, retry_attempt: int) -> bool:
        """是否还有重试机会。"""
        return retry_attempt < self._MAX_RETRY


# 全局单例
threshold_checker = DynamicConfidenceThreshold()


# ==================== 事实核验 ====================


class FactVerificationPostProcessor:
    """事实核验：正则验证政策编号、日期、金额等。"""

    FACT_RULES = {
        "policy_no": (r"[一-龥]{2,4}〔\d{4}〕\d+号", "政策编号"),
        "date":      (r"\d{4}年\d{1,2}月\d{1,2}日", "日期"),
        "money":     (r"\d+(\.\d+)?(万|千|百)?元", "金额"),
        "count":     (r"\d+(个|项|种|类|份)", "数量"),
    }

    def verify(self, text: str) -> list[dict]:
        """核验文本中的事实要素，返回问题列表。"""
        issues: list[dict] = []
        for fact_type, (pattern, label) in self.FACT_RULES.items():
            matches = re.findall(pattern, text)
            if matches:
                # 当前版本只标记存在的事实要素，不做跨源校验（V2 再加）
                issues.append(
                    {
                        "fact_type": fact_type,
                        "label": label,
                        "values": matches,
                        "note": "已识别，待跨源校验",
                    }
                )
        return issues


fact_verifier = FactVerificationPostProcessor()


# ==================== 一致性检查（V1 简化版）====================


class SelfConsistencyChecker:
    """自我一致性检查：V1 只做轻量标记，不做多轮生成比对。"""

    def check(
        self,
        current_response: str,
        history: list[dict] | None = None,
    ) -> tuple[bool, list[dict]]:
        """检查当前回答是否与历史矛盾。

        V1 简化：只检查"否定词 + 历史关键词"的明显矛盾。
        """
        if not history:
            return True, []

        issues: list[dict] = []
        last_topic = (history[-1].get("last_topic") if history else None)
        if not last_topic:
            return True, []

        current_lower = current_response.lower()
        # 简单规则：历史说"可以"，当前说"不可以" → 标记
        contradiction_pairs = [
            (["可以", "能够", "允许"], ["不可以", "不能", "不允许", "不行"]),
            (["需要", "必须", "要求"], ["不需要", "不必", "不强制"]),
        ]
        for positive, negative in contradiction_pairs:
            has_positive = any(p in current_lower for p in positive)
            has_negative = any(n in current_lower for n in negative)
            if has_positive and has_negative:
                issues.append(
                    {
                        "severity": "medium",
                        "contradiction_type": f"同时包含{positive}和{negative}",
                        "description": "回答内部可能存在矛盾",
                    }
                )

        is_consistent = len(issues) == 0
        return is_consistent, issues


consistency_checker = SelfConsistencyChecker()
```

#### 第五重：自我一致性检查（设计概念）

```python
# ================================================================
# 设计概念：自我一致性检查
# 实际实现：agent/hallucination_defense.py → SelfConsistencyChecker
# ================================================================

"""
实际流程（check_consistency 节点）：
1. 从 AgentState.messages 中提取历史对话
2. 使用 LLM 判断当前回答与历史回答是否存在矛盾
3. 矛盾维度：政策条件、办理流程、时间节点、金额数量、材料清单
4. 严重程度：high / medium / low
5. 结果存入 consistency_issues（JSON 列表）

落库：monitor/scheduler.py 中的 consistency_check 定时任务
将 consistency_issues 写入 consistency_issue_log 表
"""
```

#### 第六重：事实核验（设计概念）

```python
# ================================================================
# 设计概念：事实核验
# 实际实现：agent/hallucination_defense.py → FactVerificationPostProcessor
# ================================================================

"""
实际流程（verify_facts 节点）：
1. 正则提取回答中的关键事实：
   - 政策编号：[一-龥]{2,4}〔\d{4}〕\d+号
   - 日期：\d{4}年\d{1,2}月\d{1,2}日
   - 金额：\d+(\.\d+)?(万|千|百)?元
2. 验证格式和合理性
3. 问题存入 fact_issues（JSON 列表）

落库：monitor/scheduler.py 中的 consistency_check 定时任务
将 fact_issues 写入 fact_verification_log 表
"""
```

> **与设计文档 v2.0 的差异**：
> - v2.0 设计为"三重防护"（固定阈值 + 引用强制 + 拒答），v3.0 扩展为"五重防护"
> - 实际代码中，五重防护分散在 11 个 LangGraph 节点中实现，而非集中在一个类里
> - 实际不依赖 LlamaIndex，所有防护在 ChromaDB 检索结果上操作

#### 第六重：具体事实核验

> **V1 简化版**：实际实现见上方"五重防护机制在节点中的实际使用"代码块中的 `verify_facts` 和 `check_consistency` 节点函数。`hallucination_defense.py` 中的 `FactVerificationPostProcessor.verify()` 使用正则提取政策编号/日期/金额/数量等事实要素，当前版本只标记存在的事实要素，不做跨源校验（V2 再加）。`SelfConsistencyChecker.check()` 使用"否定词 + 历史关键词"规则检查明显矛盾。

> **V1 简化版**：实际实现见上方"五重防护机制在节点中的实际使用"代码块中的 `verify_facts` 和 `check_consistency` 节点函数。`hallucination_defense.py` 中的 `FactVerificationPostProcessor.verify()` 使用正则提取政策编号/日期/金额/数量等事实要素，当前版本只标记存在的事实要素，不做跨源校验（V2 再加）。`SelfConsistencyChecker.check()` 使用"否定词 + 历史关键词"规则检查明显矛盾。

```python
# ================================================================
# 具体事实核验：对回答中的关键事实进行专项验证
# ================================================================

import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class FactIssue:
    """事实问题记录"""
    fact_type: str       # policy_no / date / money / count
    extracted_value: str  # 提取到的值
    validation_result: str  # 验证结果
    suggestion: str      # 建议修正

class FactVerificationPostProcessor:
    """
    具体事实核验器
    
    面试要点：
    - 展示对关键信息的识别能力
    - 展示对数据质量的把控
    """
    
    # 事实类型及其验证规则
    FACT_RULES = {
        "policy_no": {
            # 政策编号格式：如"国办发〔2024〕5号"
            "pattern": r"[\u4e00-\u9fa5]{2,4}〔\d{4}〕\d+号",
            "validation": "format_check",
            "description": "政策文件编号"
        },
        "date": {
            # 日期格式：如"2024年6月30日"
            "pattern": r"\d{4}年\d{1,2}月\d{1,2}日",
            "validation": "date_range_check",
            "description": "具体日期"
        },
        "money": {
            # 金额格式：如"5000元"、"1.5万元"
            "pattern": r"\d+(\.\d+)?(万|千|百)?元",
            "validation": "amount_reasonable_check",
            "description": "金额数字"
        },
        "count": {
            # 数量格式：如"3个工作日"、"5项材料"
            "pattern": r"\d+(个|项|种|类|份)",
            "validation": "count_reasonable_check",
            "description": "数量统计"
        },
        "phone": {
            # 电话格式
            "pattern": r"(\d{3,4}-)?\d{7,8}",
            "validation": "phone_format_check",
            "description": "联系电话"
        }
    }

    # 合理范围配置
    REASONABLE_RANGES = {
        "money": {
            "补贴金额": {"min": 500, "max": 50000},
            "违约金": {"min": 1000, "max": 100000},
        },
        "count": {
            "工作日": {"min": 1, "max": 30},
            "材料数量": {"min": 1, "max": 20},
        },
        "date": {
            "截止日期": {"min_year": 2024, "max_year": 2030},
        }
    }

    def verify(self, response: str, context: dict = None) -> list[FactIssue]:
        """验证回答中的具体事实"""
        
        issues = []
        
        for fact_type, rule in self.FACT_RULES.items():
            # 提取事实
            matches = re.findall(rule["pattern"], response)
            
            for match in matches:
                # 验证事实
                validation_result = self._validate_fact(
                    fact_type,
                    match,
                    context
                )
                
                if not validation_result["valid"]:
                    issues.append(FactIssue(
                        fact_type=fact_type,
                        extracted_value=match,
                        validation_result=validation_result["reason"],
                        suggestion=validation_result["suggestion"]
                    ))
        
        return issues

    def _validate_fact(
        self,
        fact_type: str,
        value: str,
        context: dict
    ) -> dict:
        """验证单个事实"""
        
        result = {"valid": True, "reason": None, "suggestion": None}
        
        if fact_type == "policy_no":
            # 政策编号格式验证
            if not self._is_valid_policy_no(value):
                result["valid"] = False
                result["reason"] = "政策编号格式不正确"
                result["suggestion"] = "请核实政策编号来源"
        
        elif fact_type == "date":
            # 日期范围验证
            parsed_date = self._parse_chinese_date(value)
            if parsed_date:
                year = parsed_date.year
                if year < 2020 or year > 2030:
                    result["valid"] = False
                    result["reason"] = f"日期年份{year}不在合理范围内(2020-2030)"
                    result["suggestion"] = "请核实政策有效期"
        
        elif fact_type == "money":
            # 金额合理性验证
            amount = self._parse_money(value)
            if amount:
                # 根据上下文判断金额类型
                if "补贴" in context.get("query", ""):
                    range_config = self.REASONABLE_RANGES["money"]["补贴金额"]
                    if amount < range_config["min"] or amount > range_config["max"]:
                        result["valid"] = False
                        result["reason"] = f"补贴金额{amount}元不在合理范围内"
                        result["suggestion"] = "请核实补贴标准"
        
        return result

    def _is_valid_policy_no(self, policy_no: str) -> bool:
        """验证政策编号格式"""
        
        # 政策编号示例：
        # 国办发〔2024〕5号
        # 人社部发〔2024〕12号
        
        valid_prefixes = [
            "国办发", "人社部发", "教育部发",
            "省办发", "市办发", "校发"
        ]
        
        for prefix in valid_prefixes:
            if policy_no.startswith(prefix):
                return True
        
        return False

    def _parse_chinese_date(self, date_str: str) -> Optional[datetime]:
        """解析中文日期"""
        
        try:
            # "2024年6月30日" -> datetime
            match = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_str)
            if match:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                return datetime(year, month, day)
        except:
            pass
        
        return None

    def _parse_money(self, money_str: str) -> Optional[float]:
        """解析金额"""
        
        try:
            # "5000元" -> 5000
            # "1.5万元" -> 15000
            
            match = re.match(r"(\d+(?:\.\d+)?)(万|千|百)?元", money_str)
            if match:
                amount = float(match.group(1))
                unit = match.group(2)
                
                if unit == "万":
                    amount *= 10000
                elif unit == "千":
                    amount *= 1000
                elif unit == "百":
                    amount *= 100
                
                return amount
        except:
            pass
        
        return None


# ================================================================
# 事实核验结果处理
# ================================================================

class FactIssueHandler:
    """事实问题处理器"""
    
    def handle_issues(
        self,
        response: str,
        issues: list[FactIssue]
    ) -> str:
        """处理事实核验问题"""
        
        if not issues:
            return response
        
        # 高风险问题：添加警告
        high_risk_types = ["policy_no", "date"]
        high_risk_issues = [i for i in issues if i.fact_type in high_risk_types]
        
        if high_risk_issues:
            warning = self._generate_fact_warning(high_risk_issues)
            return f"{response}\n\n{warning}"
        
        return response

    def _generate_fact_warning(self, issues: list[FactIssue]) -> str:
        """生成事实警告"""
        
        lines = ["⚠️ 以下信息需要核实："]
        
        for issue in issues:
            lines.append(f"- {issue.fact_type}: \"{issue.extracted_value}\" - {issue.validation_result}")
            lines.append(f"  建议：{issue.suggestion}")
        
        lines.append("\n请登录官方网站核实，或联系就业中心老师确认。")
        
        return "\n".join(lines)
```

#### 五重防护机制在节点中的实际使用

```python
# ================================================================
# 实际实现：agent/nodes.py 中五个防护节点的代码
# V1 简化版：五重防护分散在 11 个 LangGraph 节点中实现
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/agent/nodes.py`

五重防护实际分散在独立的节点函数中实现（非集中在一个类里）：

1. route_query → 设置 query_risk_level（第一重：动态阈值的前提）
2. search_knowledge → 检索 + 时效性调整 + 过滤过期文档
3. check_confidence → 调用 threshold_checker.should_accept_result()（第一+二重）
4. generate_response → 带引用生成回答（第三重：prompt 约束）
5. check_consistency → 调用 consistency_checker.check()（第四重）
6. verify_facts → 调用 fact_verifier.verify()（第五重）
7. content_moderation → 敏感词过滤（额外安全层）
8. accept_with_warning → 低置信度附加警告
9. generate_refusal → 生成拒答回复（6 套模板）
10. direct_response → 简单问候直接回复
11. error_handler → 统一异常处理

防死循环机制（分散在各节点）：
- retry_attempt：置信度重试次数（check_confidence 中递增）
- tool_call_count：工具调用次数（search_knowledge 中递增）
- last_search_query：上次检索关键词（search_knowledge 中去重）
- regenerate_count：重生成次数（regenerate_with_hints 中递增）
- forced_exit：强制退出标记（route_query 中 tool_call_count >= 3 时触发）
"""

def check_confidence(state: dict) -> dict:
    """动态置信度判断：决定接受/重试/拒答。

    防条件判断循环：每次重试自动降低阈值，最多重试 3 次。
    """
    query = state.get("current_query", "")
    confidence = state.get("confidence", 0.0)
    hits = state.get("search_results", [])
    citations = state.get("citations", [])
    retry = state.get("retry_attempt", 0)

    accepted, reason = threshold_checker.should_accept_result(
        query=query,
        confidence=confidence,
        results_count=len(hits),
        has_citation=bool(citations),
        retry_attempt=retry,
    )

    if accepted:
        return {
            "should_refuse": False,
            "should_retry": False,
            "retry_attempt": retry,
        }

    # 不通过，判断是否还有重试机会
    if threshold_checker.should_retry(retry):
        return {
            "should_refuse": False,
            "should_retry": True,
            "retry_attempt": retry + 1,
        }

    # 重试耗尽 → 降级回答（带警告），不拒答
    return {
        "should_refuse": False,
        "should_retry": False,
        "is_low_confidence": True,
        "retry_attempt": retry + 1,
    }


def check_consistency(state: dict) -> dict:
    """自我一致性检查。

    V1 简化：只做轻量标记，不做多轮生成比对。
    防结果验证循环：验证器降级，不阻塞流程。
    """
    response = state.get("response", "")
    history = state.get("history", [])

    try:
        is_consistent, issues = consistency_checker.check(response, history)
    except Exception as e:
        # 验证器降级：非阻塞
        return {
            "is_consistent": True,
            "consistency_issues": [],
            "skipped_consistency_check": True,
        }

    high_count = sum(1 for i in issues if i.get("severity") == "high")
    medium_count = sum(1 for i in issues if i.get("severity") == "medium")

    return {
        "is_consistent": is_consistent,
        "consistency_issues": issues,
        "high_severity_count": high_count,
        "medium_severity_count": medium_count,
    }


def verify_facts(state: dict) -> dict:
    """事实核验：正则验证政策编号、日期、金额等。"""
    response = state.get("response", "")

    issues = fact_verifier.verify(response)

    return {
        "fact_issues": issues,
    }


def content_moderation(state: dict) -> dict:
    """LLM 输出内容审核：检查是否包含违规内容。

    与输入侧敏感词过滤形成双重防护。
    """
    response = state.get("response", "")

    # V1 简化：只做关键词匹配，不额外调 LLM（成本考虑）
    sensitive_patterns = {
        "politics": ["国家领导人", "主席", "总理", "反动", "颠覆"],
        "contact": [r"\d{3}-\d{8}", r"\d{11}"],
        "ad": ["加我微信", "私信", "代做", "枪手", "收费"],
    }

    violations = []
    for category, patterns in sensitive_patterns.items():
        for pattern in patterns:
            if pattern.startswith("\\") or any(c in pattern for c in ["*", "+", "?", "[", "]", "(", ")", "{", "}", "|", "^", "$"]):
                # 正则匹配
                if re.search(pattern, response):
                    violations.append(category)
                    break
            else:
                # 字面匹配
                if pattern in response:
                    violations.append(category)
                    break

    if violations:
        return {
            "should_refuse": True,
            "refusal_reason": "回答内容包含违规信息，已拦截。",
            "content_safe": False,
            "content_violations": list(set(violations)),
        }

    return {"content_safe": True}


def accept_with_warning(state: dict) -> dict:
    """接受回答但附加警告（低置信度 / 中等严重度问题）。"""
    warnings = []

    if state.get("is_low_confidence"):
        warnings.append("⚠️ 该回答基于有限资料，仅供参考，建议您咨询就业中心老师确认。")

    medium_issues = [i for i in state.get("consistency_issues", []) if i.get("severity") == "medium"]
    if medium_issues:
        warnings.append("⚠️ 回答中部分内容可能存在不一致，请以官方文件为准。")

    temporal_warnings = state.get("temporal_warnings", [])
    warnings.extend(temporal_warnings)

    return {
        "response": state.get("response", ""),
        "warnings": warnings,
        "should_refuse": False,
        "is_low_confidence": state.get("is_low_confidence", False),
    }
```

### 3.5 溯源问题增强方案（句子级别引用 + 引用验证）

#### 问题分析

```
当前溯源方案的局限性：

1. Chunk级别引用不够精确
   - 一个chunk可能包含多个观点
   - 用户无法知道具体哪句话支持哪个观点

2. 引用准确性缺乏验证
   - LLM可能错误归因（引用了不相关的chunk）
   - 需要自动化验证引用是否真的支持回答

3. 引用置信度缺失
   - 不知道引用有多"可靠"
   - 无法区分强引用和弱引用
```

#### 语义感知的文档切分

> ⚠️ **关键优化**：传统切分方式（固定chunk_size或句子边界）会切断语义完整性，需要使用语义相似度进行智能切分。

```python
# ================================================================
# 实际配置：core/config.py → Settings 类中的语义分块参数
# V1 简化版：配置参数已就绪，实际切分逻辑在 knowledge/indexer 服务中
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/core/config.py` → Settings 类

语义分块配置参数（已存在于 config.py）：
  chunk_min_chars: int = 200       # 块最小字符数（低于则继续合并短句）
  chunk_max_chars: int = 500       # 块最大字符数（超过则在句子边界强制断开）
  semantic_breakpoint_percentile: int = 95  # 相邻句子距离的百分位阈值，超过即语义断点

实际实现：
- 语义分块器类（core/semantic_chunker.py）在 V1 中暂未创建
- 文档切分逻辑在 knowledge/indexer 服务中完成
- 基于 Embedding 相似度的百分位落差法检测语义断点
- 面试时说明"配置已就绪，V1 优先保证系统稳定性，V2 再上完整语义切分"
"""
```

#### 句子级别引用追踪

```python
# ================================================================
# 实际实现：agent/citation_tracker.py
# V1 简化版：Chunk 级别引用 + 质量评估
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/agent/citation_tracker.py`

V1 实现（当前代码库中的实际实现）：

1. build_citations(hits) → list[dict]
   - 从检索结果构建引用列表（chunk 级别）
   - 每条引用包含 rank / document_id / document_title / chunk_id /
     score / page_no / snippet（截断至 CITATION_SNIPPET_MAX_LENGTH=200 字符）

2. evaluate_citation_quality(citations) → dict
   - 评估引用整体质量（V1 简化版）
   - 仅基于检索得分和引用数量做统计
   - 按得分区间映射为 direct / indirect / none
   - V2 再引入 SentenceLevelCitationTracker 做逐句验证

3. SentenceLevelCitationTracker（V2 预留接口）
   - track() 方法未实现，raise NotImplementedError
   - 设计意图：将回答按 。！？； 切分为句子
   - 对每个句子找最相关的来源 chunk（Embedding 相似度）
   - 使用 LLM 验证引用支持度（direct/indirect/none）
"""

# ===== V1：Chunk 级别引用（当前实现）=====


def build_citations(hits: list[dict]) -> list[dict]:
    """从检索结果构建引用列表（V1 简化：chunk 级别）。

    Args:
        hits: 检索结果列表（来自 rag_service.search）

    Returns:
        引用列表，每条包含 rank / document_id / document_title / chunk_id /
        score / page_no / snippet
    """
    citations = []
    for rank, h in enumerate(hits, start=1):
        citations.append(
            {
                "rank": rank,
                "document_id": h.get("document_id"),
                "document_title": h.get("document_title"),
                "chunk_id": h.get("chunk_id"),
                "score": h.get("score"),
                "page_no": h.get("page_no"),
                "snippet": (h.get("content") or "")[:CITATION_SNIPPET_MAX_LENGTH],
            }
        )
    return citations


# ===== V1：引用质量评估（简化版）=====


def evaluate_citation_quality(citations: list[dict]) -> dict[str, Any]:
    """评估引用整体质量（V1 简化版）。

    V1 仅基于检索得分和引用数量做统计，不做 LLM 级验证。
    V2 再引入 SentenceLevelCitationTracker 做逐句验证。

    Args:
        citations: 引用列表

    Returns:
        质量评估结果
    """
    total = len(citations)
    if total == 0:
        return {
            "quality_score": 0.0,
            "direct_count": 0,
            "indirect_count": 0,
            "none_count": 0,
            "avg_score": 0.0,
            "issues": ["无引用"],
        }

    scores = [c.get("score") or 0.0 for c in citations]
    avg_score = sum(scores) / total

    # V1 简化：按得分区间映射为 direct / indirect / none
    direct_count = sum(1 for s in scores if s >= 0.75)
    indirect_count = sum(1 for s in scores if 0.40 <= s < 0.75)
    none_count = total - direct_count - indirect_count

    quality_score = (
        direct_count * 1.0 + indirect_count * 0.5 + none_count * 0.0
    ) / total

    issues = []
    if none_count > 0:
        issues.append(f"{none_count} 条引用得分较低")
    if avg_score < 0.5:
        issues.append(f"平均引用得分偏低({avg_score:.2f})")

    return {
        "quality_score": round(quality_score, 4),
        "direct_count": direct_count,
        "indirect_count": indirect_count,
        "none_count": none_count,
        "avg_score": round(avg_score, 4),
        "issues": issues,
    }


# ===== V2 预留接口（句子级别引用）=====


class SentenceLevelCitationTracker:
    """句子级别引用追踪器（V2 实现，V1 仅预留接口）。

    V2 实现要点：
    1. 将回答按 `。！？；` 切分为句子
    2. 对每个句子找最相关的来源 chunk（Embedding 相似度）
    3. 使用 LLM 验证引用支持度（direct / indirect / none）
    4. 返回句子级别引用列表
    """

    def __init__(self, embed_model: Any, llm_client: Any) -> None:
        self.embed_model = embed_model
        self.llm_client = llm_client

    def track(self, response: str, source_chunks: list[dict]) -> list[dict]:
        """追踪句子级别引用（V2 实现）。"""
        raise NotImplementedError("SentenceLevelCitationTracker.track() 将在 V2 实现")
```

### 3.6 时效性问题增强方案（健康监控 + 时效性感知检索）

#### 知识库健康度监控

```python
# ================================================================
# 实际实现：backend/app/monitor/health_monitor.py → KnowledgeBaseHealthMonitor
# V1 简化版：无通知服务，无分类权重，无建议生成
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/monitor/health_monitor.py`

V1 简化版（与设计文档中的完整版差异）：

1. run_daily_check() → dict
   - 不依赖外部 notification_service
   - 不生成 recommendations
   - 直接查询 MySQL，无 category 权重（所有文档权重相同）

2. _calculate_health_score() → float
   - 使用指数衰减模型：freshness = exp(-0.693 × days_since / half_life)
   - 过期文档：freshness *= 0.1
   - 无 category_weights，所有文档等权

3. 实际健康度指标：
   - health_score：0-100 分
   - warning_count：即将过期文档数
   - expired_count：已过期文档数

4. 调用方式：
   - 由 monitor/scheduler.py 定时任务调用
   - 结果写入 kb_health_log 表
"""

from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import KbDocument, KbHealthLog

logger = logging.getLogger(__name__)


class KnowledgeBaseHealthMonitor:
    """知识库健康度监控器（V1 简化版）。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run_daily_check(self) -> dict[str, Any]:
        """执行一次健康检查，返回报告字典。"""
        today = date.today()

        # 1. 即将过期文档
        warning_date = today + __import__("datetime").timedelta(days=settings.kb_warning_days)
        warning_docs = self._query_docs_in_range(today, warning_date)

        # 2. 已过期文档
        expired_docs = self._query_expired_docs(today)

        # 3. 健康度评分
        health_score = self._calculate_health_score(today)

        report = {
            "check_date": today.isoformat(),
            "health_score": health_score,
            "warning_count": len(warning_docs),
            "expired_count": len(expired_docs),
            "warning_docs": warning_docs,
            "expired_docs": expired_docs,
        }

        # 4. 写入日志
        self._log_report(report)

        logger.info(
            "KB健康检查完成：score=%.2f, warning=%d, expired=%d",
            health_score,
            len(warning_docs),
            len(expired_docs),
        )

        return report

    def _query_docs_in_range(self, start: date, end: date) -> list[dict]:
        """查询在 [start, end] 区间内过期的文档。"""
        rows = (
            self.db.query(KbDocument)
            .filter(
                KbDocument.status == 1,
                KbDocument.expire_date.isnot(None),
                KbDocument.expire_date >= start,
                KbDocument.expire_date <= end,
            )
            .order_by(KbDocument.expire_date.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "expire_date": r.expire_date.isoformat(),
                "days_until_expiry": (r.expire_date - start).days,
            }
            for r in rows
        ]

    def _query_expired_docs(self, today: date) -> list[dict]:
        """查询已过期文档。"""
        rows = (
            self.db.query(KbDocument)
            .filter(
                KbDocument.status == 1,
                KbDocument.expire_date.isnot(None),
                KbDocument.expire_date < today,
            )
            .order_by(KbDocument.expire_date.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "title": r.title,
                "expire_date": r.expire_date.isoformat(),
                "days_expired": (today - r.expire_date).days,
            }
            for r in rows
        ]

    def _calculate_health_score(self, today: date) -> float:
        """计算知识库整体健康度（0-100）。"""
        rows = (
            self.db.query(
                KbDocument.expire_date,
                KbDocument.effective_date,
            )
            .filter(
                KbDocument.status == 1,
                KbDocument.expire_date.isnot(None),
            )
            .all()
        )

        if not rows:
            return 100.0

        total_score = 0.0
        total_weight = 0.0

        half_life = settings.kb_freshness_half_life

        for row in rows:
            effective = row.effective_date or today
            expire = row.expire_date

            days_since = (today - effective).days
            freshness = math.exp(-0.693 * days_since / half_life)

            if expire < today:
                freshness *= 0.1  # 过期惩罚

            total_score += freshness
            total_weight += 1.0

        score = (total_score / total_weight) * 100 if total_weight > 0 else 100.0
        return round(score, 2)

    def _log_report(self, report: dict[str, Any]) -> None:
        """写入健康度日志。"""
        try:
            log = KbHealthLog(
                check_date=date.fromisoformat(report["check_date"]),
                health_score=report["health_score"],
                warning_docs=len(report["warning_docs"]),
                expired_docs=len(report["expired_docs"]),
                total_docs=self._count_total_docs(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception as e:
            logger.warning("写入 kb_health_log 失败: %s", str(e))
            self.db.rollback()

    def _count_total_docs(self) -> int:
        """统计当前有效文档总数。"""
        return (
            self.db.query(KbDocument)
            .filter(KbDocument.status == 1)
            .count()
        )
```

> **与设计文档 v2.0 的差异**：
> - v2.0 设计为"知识库版本管理 + 实时数据通道"，实际简化为"时效性调整 + 健康监控"
> - 无 `kb_version` 表和实时 API 通道
> - 时效性信息存储在 ChromaDB metadata 和 `qa_message` JSON 字段中

> **与实际代码的对应关系**：`backend/app/monitor/health_monitor.py` 中的 `KnowledgeBaseHealthMonitor` 是 V1 简化版，直接操作 SQLAlchemy Session，无外部通知服务。健康度计算公式与设计文档一致（指数衰减 + 过期惩罚），但未使用文档分类权重。

#### 时效性感知的检索

```python
# ================================================================
# 实际实现：backend/app/agent/temporal_retriever.py
# V1 简化版：过期文档过滤 + 降权标记
# V2 预留接口：TemporalAwareRetriever（暂未实现）
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/agent/temporal_retriever.py`

V1 实现三个函数（简化版）：

1. filter_expired_docs(db, doc_ids) → set[int]
   - 查询 MySQL，返回已过期文档 ID 集合
   - 仅检查 KbDocument.expire_date < today

2. get_expiring_soon_docs(db, warning_days) → list[dict]
   - 供监控模块调用
   - 返回即将过期文档列表（含 days_until_expiry）

3. apply_temporal_adjustment(hits, expired_ids) → list[dict]
   - V1 仅添加 is_expired 标记，不修改得分
   - V2 再扩展为综合得分排序

V2 预留接口：
- TemporalAwareRetriever.retrieve() → raise NotImplementedError
  - 设计意图：综合得分 = similarity × 0.7 + temporal × 0.3
  - 过期文档降权 × 0.1
  - 按综合得分排序取 top_k
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import KbDocument

logger = logging.getLogger(__name__)


# ===== V1：过期文档过滤 =====


def filter_expired_docs(db: Session, doc_ids: list[int]) -> set[int]:
    """过滤已过期文档 ID（V1 简化版）。

    仅检查 `KbDocument.expire_date`，已过期且未设为长期有效的文档会被过滤。

    Args:
        db: 数据库会话
        doc_ids: 候选文档 ID 列表

    Returns:
        已过期文档 ID 集合
    """
    if not doc_ids:
        return set()

    today = date.today()
    expired_rows = (
        db.query(KbDocument.id)
        .filter(
            KbDocument.id.in_(doc_ids),
            KbDocument.status == 1,
            KbDocument.expire_date.isnot(None),
            KbDocument.expire_date < today,
        )
        .all()
    )
    return {row.id for row in expired_rows}


def get_expiring_soon_docs(db: Session, warning_days: int = 30) -> list[dict]:
    """获取即将过期文档（V1 简化版，供监控模块调用）。

    Args:
        db: 数据库会话
        warning_days: 预警天数（默认 30 天）

    Returns:
        即将过期文档列表
    """
    today = date.today()
    warning_date = today + __import__("datetime").timedelta(days=warning_days)

    rows = (
        db.query(KbDocument)
        .filter(
            KbDocument.status == 1,
            KbDocument.expire_date.isnot(None),
            KbDocument.expire_date >= today,
            KbDocument.expire_date <= warning_date,
        )
        .order_by(KbDocument.expire_date.asc())
        .all()
    )

    return [
        {
            "id": row.id,
            "title": row.title,
            "expire_date": row.expire_date.isoformat() if row.expire_date else None,
            "days_until_expiry": (row.expire_date - today).days if row.expire_date else None,
        }
        for row in rows
    ]


# ===== V1：检索结果降权标记 =====


def apply_temporal_adjustment(hits: list[dict], expired_ids: set[int]) -> list[dict]:
    """对检索结果应用时效性调整（V1 简化：仅标记过期）。

    V1 不修改得分，仅对过期文档添加 `is_expired` 标记，
    由上层节点决定是否降权或展示警告。

    Args:
        hits: 检索结果列表
        expired_ids: 已过期文档 ID 集合

    Returns:
        调整后的检索结果列表
    """
    adjusted = []
    for h in hits:
        doc_id = (h.get("metadata") or {}).get("document_id")
        h_copy = dict(h)
        h_copy["is_expired"] = doc_id in expired_ids if doc_id is not None else False
        adjusted.append(h_copy)
    return adjusted


# ===== V2 预留接口（完整时效感知检索）=====


class TemporalAwareRetriever:
    """时效感知检索器（V2 实现，V1 仅预留接口）。

    V2 实现要点：
    1. 基础向量检索（取 top_k × 2 候选）
    2. 计算时效性得分（指数衰减：exp(-0.693 × days / half_life)）
    3. 综合得分 = 相似度 × 0.7 + 时效性 × 0.3
    4. 过期文档降权 × 0.1
    5. 按综合得分排序取 top_k
    """

    def __init__(self, base_retriever: Any, config: dict | None = None) -> None:
        self.base_retriever = base_retriever
        self.config = config or {
            "half_life_days": settings.kb_freshness_half_life,
            "similarity_weight": 0.7,
            "temporal_weight": 0.3,
            "expired_penalty": 0.1,
        }

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """时效感知检索（V2 实现）。"""
        raise NotImplementedError("TemporalAwareRetriever.retrieve() 将在 V2 实现")
```

---

## 四、LangGraph Agent 架构

### 4.1 为什么选择 LangGraph？

```
传统 Agent 实现 vs LangGraph：

┌─────────────────────────────────────────────────────────────────────────┐
│                         传统 Agent 实现                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  def agent_loop(user_input):                                            │
│      while True:                                                         │
│          next_step = decide_next_step(user_input, history)              │
│          ...                                                             │
│  问题：                                                                   │
│  ❌ 状态分散在全局变量                                                   │
│  ❌ 难以追踪执行链路                                                     │
│  ❌ 循环/分支逻辑复杂                                                   │
│  ❌ 无法暂停/恢复                                                       │
│  ❌ 调试困难                                                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         LangGraph 实现                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  from langgraph.graph import StateGraph, END, START                     │
│                                                                          │
│  class AgentState(TypedDict):                                            │
│      messages: Annotated[list, add_messages]                            │
│      current_query: str                                                  │
│      search_results: list[dict]                                          │
│      confidence: float                                                   │
│      ...                                                                 │
│                                                                          │
│  graph = StateGraph(AgentState)                                          │
│  graph.add_node("route", route_query)                                    │
│  graph.add_node("search", search_knowledge)                              │
│  graph.add_edge(START, "route")                                          │
│  app = graph.compile(checkpointer=sqlite_checkpoint)                    │
│                                                                          │
│  优势：                                                                   │
│  ✅ 状态显式管理                                                          │
│  ✅ 执行链路清晰                                                          │
│  ✅ 支持循环/分支/条件                                                    │
│  ✅ 支持 Checkpoint (暂停/恢复)                                          │
│  ✅ 内置可视化调试                                                        │
│  ✅ 易于扩展                                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

> **技术选型变更说明**：本项目中检索层实际采用 **ChromaDB + 自定义向量检索 + 时效性调整**，而非设计文档最初规划的 LlamaIndex + BM25 + Cohere Rerank。原因是：
> 1. 项目已在使用 ChromaDB 作为向量库，复用现有基础设施减少依赖
> 2. 就业政策问答场景对检索精度要求较高，但数据量适中，ChromaDB 足够支撑
> 3. 减少外部依赖（Cohere API、Elasticsearch），降低运维复杂度
> 4. 语义缓存（Redis）已覆盖部分性能优化需求
> 5. 时效性调整直接在 ChromaDB 检索结果上叠加时间衰减权重，无需额外检索框架

### 4.2 实际 LangGraph 工作流（v3.0 实装版）

```python
# ================================================================
# 实际实现：backend/app/agent/state.py → AgentState
# 实际实现：backend/app/agent/nodes.py → 11 个独立节点函数
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：
- `backend/app/agent/state.py` → AgentState 类
- `backend/app/agent/nodes.py` → 11 个独立节点函数（非类方法）
- `backend/app/agent/graph.py` → AgentGraph 类（StateGraph 构建器）

关键设计差异：
- 实际 AgentState 使用 `Annotated[dict, "AgentState"]` 而非 TypedDict
- 实际节点为独立函数（如 route_query(state: dict) → dict），非类方法
- 所有节点通过 graph.py 注册到 StateGraph
"""

# ===== AgentState（实际 state.py）=====

from __future__ import annotations

from typing import Annotated, Optional

from langgraph.graph import add_messages


class AgentState(Annotated[dict, "AgentState"]):
    """LangGraph Agent 工作流状态。

    使用 TypedDict 模式，支持 IDE 类型检查和 LangGraph 状态管理。
    所有字段都是可选的，节点按需读写。
    """

    # ===== 核心对话 =====
    messages: Annotated[list[dict], add_messages]  # 对话历史（Annotated + add_messages 自动追加）
    current_query: str  # 当前用户查询
    conversation_id: int  # 业务会话 ID
    user_id: int  # 当前用户 ID

    # ===== 检索结果 =====
    search_results: list[dict]  # 检索结果
    citations: list[dict]  # 引用信息
    confidence: float  # 综合置信度 (0-1)
    query_risk_level: str  # high / medium / low

    # ===== 路由决策 =====
    route: str  # search / direct / refuse / generate
    should_refuse: bool
    refusal_reason: str

    # ===== 五重防护结果 =====
    consistency_issues: list[dict]
    fact_issues: list[dict]
    temporal_warnings: list[str]

    # ===== 最终回答 =====
    response: str
    is_low_confidence: bool  # 低置信度降级回答
    content_safe: bool  # 内容审核是否通过

    # ===== 会话记忆（V1 简化）=====
    history: list[dict]  # 历史对话摘要（最近 N 轮）

    # ===== 可解释性（V1 简化：只记核心字段）=====
    reasoning_chain: list[dict]  # 每步决策记录

    # ===== 错误处理 =====
    error: dict
    is_error: bool

    # ===== 死循环防护 =====
    retry_attempt: int  # 置信度重试次数（防条件判断循环）
    tool_call_count: int  # 工具调用总次数（防工具选择循环）
    last_search_query: str  # 上次检索关键词（语义去重）
    regenerate_count: int  # 重生成次数（防结果验证循环）
    forced_exit: bool  # 是否强制退出循环
    skipped_consistency_check: bool  # 是否跳过一致性检查（降级）

    # ===== 业务关联 =====
    request_id: str  # 请求 ID（幂等键）
    llm_tokens_in: int  # Prompt Token 数
    llm_tokens_out: int  # 生成 Token 数
    created_at: str  # 请求时间


# ===== 11 个节点函数（实际 nodes.py）=====

"""
节点函数列表（backend/app/agent/nodes.py）：

1. route_query(state) → dict
   - 路由决策：search / direct / refuse
   - 防工具选择循环：tool_call_count >= 3 时强制生成

2. search_knowledge(state) → dict
   - 时效感知检索：knowledge_search() + filter_expired_docs() + apply_temporal_adjustment()
   - 防重复检索：相同查询跳过

3. check_confidence(state) → dict
   - 动态置信度判断：accept / regenerate / refuse
   - 防条件判断循环：每次重试降低阈值

4. generate_response(state) → dict
   - 带引用生成回答
   - 使用 chat_with_usage() 追踪 token 消耗

5. regenerate_with_hints(state) → dict
   - 带修正提示的重新生成
   - 只对 high 严重度问题注入修正信息

6. check_consistency(state) → dict
   - 自我一致性检查（V1 简化）
   - 验证器降级：非阻塞

7. verify_facts(state) → dict
   - 事实核验：正则验证政策编号、日期、金额

8. content_moderation(state) → dict
   - 内容审核：敏感词过滤（V1 简化，不调 LLM）

9. accept_with_warning(state) → dict
   - 接受回答但附加警告

10. generate_refusal(state) → dict
    - 生成拒答回复（V1 简化：直接返回模板，不调 LLM）

11. direct_response(state) → dict
    - 简单问候的直接回复（不走检索）

12. error_handler(state) → dict
    - 统一错误处理：记录错误，返回友好提示
"""


# ================================================================
# AgentGraph（实际 graph.py）
# ================================================================

from langgraph.graph import StateGraph, END, START
from app.agent.sqlite_checkpoint import SqliteSaver
from app.agent.nodes import (
    accept_with_warning,
    check_confidence,
    check_consistency,
    content_moderation,
    direct_response,
    error_handler,
    generate_refusal,
    generate_response,
    regenerate_with_hints,
    route_query,
    search_knowledge,
    verify_facts,
)
from app.agent.state import AgentState


class AgentGraph:
    """LangGraph Agent 工作流构建器。"""

    def __init__(self) -> None:
        self.graph: StateGraph | None = None

    def build(self) -> StateGraph:
        """构建工作流图（节点 + 边）。"""
        graph = StateGraph(AgentState)

        # ===== 注册节点 =====
        graph.add_node("route", route_query)
        graph.add_node("search", search_knowledge)
        graph.add_node("check_confidence", check_confidence)
        graph.add_node("generate", generate_response)
        graph.add_node("regenerate", regenerate_with_hints)
        graph.add_node("check_consistency", check_consistency)
        graph.add_node("verify_facts", verify_facts)
        graph.add_node("content_moderation", content_moderation)
        graph.add_node("accept_with_warning", accept_with_warning)
        graph.add_node("refuse", generate_refusal)
        graph.add_node("error_handler", error_handler)
        graph.add_node("direct_response", direct_response)

        # ===== 定义边 =====
        graph.add_edge(START, "route")

        # route 分支
        graph.add_conditional_edges(
            "route",
            _route_decision,
            {
                "search": "search",
                "direct": "direct_response",
                "refuse": "refuse",
            },
        )

        # search → check_confidence
        graph.add_edge("search", "check_confidence")

        # check_confidence 三分支
        graph.add_conditional_edges(
            "check_confidence",
            _confidence_decision,
            {
                "accept": "generate",
                "regenerate": "regenerate",
                "refuse": "refuse",
            },
        )

        # generate → check_consistency → verify_facts
        graph.add_edge("generate", "check_consistency")
        graph.add_edge("check_consistency", "verify_facts")

        # [Self-Refinement] verify_facts 之后进入三阶段自校正闭环
        graph.add_conditional_edges(
            "verify_facts",
            _verify_decision,
            {
                "accept": "content_moderation",
                "regenerate": "regenerate",
                "refuse": "refuse",
            },
        )

        # [Self-Refinement] regenerate 之后回到审查环，或熔断到 content_moderation
        graph.add_conditional_edges(
            "regenerate",
            _after_regenerate_decision,
            {
                "verify_facts": "verify_facts",
                "content_moderation": "content_moderation",
            },
        )

        # content_moderation → 最终决策
        graph.add_conditional_edges(
            "content_moderation",
            _post_moderation_decision,
            {
                "accept": END,
                "accept_with_warning": "accept_with_warning",
                "refuse": "refuse",
            },
        )

        # accept_with_warning → error_handler → END
        graph.add_edge("accept_with_warning", "error_handler")
        graph.add_edge("refuse", "error_handler")
        graph.add_edge("error_handler", END)
        graph.add_edge("direct_response", END)

        self.graph = graph
        return graph

    def compile(self, db_path: str = "data/agent_checkpoints.db") -> Any:
        """编译工作流，配置 Checkpoint。"""
        graph = self.build()
        checkpointer = SqliteSaver(db_path=db_path)

        compiled = graph.compile(checkpointer)
        return compiled


# ==================== 条件决策函数 ====================


def _route_decision(state: dict) -> str:
    """路由决策：根据 route 字段选择下一步。"""
    return state.get("route", "search")


def _confidence_decision(state: dict) -> str:
    """置信度决策：接受 / 重试 / 拒答。"""
    if state.get("should_refuse"):
        return "refuse"
    if state.get("should_retry"):
        return "regenerate"
    return "accept"


def _post_moderation_decision(state: dict) -> str:
    """内容审核后决策：接受 / 警告接受 / 拒答。"""
    if state.get("should_refuse"):
        return "refuse"
    if state.get("is_low_confidence") or state.get("warnings"):
        return "accept_with_warning"
    return "accept"


# [Self-Refinement] 新增：审查后决策（三阶段自校正闭环）
def _verify_decision(state: dict) -> str:
    """审查决策：根据事实核验结果决定 accept / regenerate / refuse。"""
    if state.get("should_refuse"):
        return "refuse"
    if state.get("should_retry"):
        return "regenerate"
    return "accept"


# [Self-Refinement] 新增：重生成后决策（熔断或回到审查环）
def _after_regenerate_decision(state: dict) -> str:
    """重生成后决策：未超限回到审查，超限熔断到内容审核。"""
    retry = state.get("retry_attempt", 0)
    if retry < MAX_REGENERATE_RETRY:
        return "verify_facts"
    return "content_moderation"


# ==================== 全局单例 ====================


_agent_graph: AgentGraph | None = None


def get_agent_graph() -> AgentGraph:
    """获取 AgentGraph 单例。"""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = AgentGraph()
    return _agent_graph
```

> **与设计文档 v2.0 的差异**：
> - v2.0 设计为 6 节点线性流程，v3.0 实际扩展为 11 节点
> - 新增 `regenerate`（重生成）、`content_moderation`（内容审核）、`accept_with_warning`（带警告接受）、`error_handler`（异常兜底）
> - 检索节点从 LlamaIndex 混合检索简化为 ChromaDB 向量检索 + 时效性调整
> - 新增 `query_risk_level` 字段用于动态阈值判断

> **与实际代码的对应关系**：实际代码中，Agent 节点为独立函数（`route_query`、`search_knowledge`、`check_confidence` 等），通过 `AgentGraph.build()` 注册到 `StateGraph`。完整节点代码见上方 `AgentGraph` 实现中的 `graph.add_node()` 调用列表。

---

### 4.3 Checkpoint 功能（对话暂停/恢复）

```python
# ================================================================
# 实际实现：自定义 SqliteSaver（LangGraph 1.2.x 未内置）
# ================================================================

from app.agent.sqlite_checkpoint import SqliteSaver

# 持久化 SQLite Checkpoint（文件：data/agent_checkpoints.db）
checkpoint_saver = SqliteSaver(db_path="data/agent_checkpoints.db")

# 编译时配置 Checkpointer
agent_graph = graph.compile(checkpointer=checkpoint_saver)


# ================================================================
# 对话恢复（使用 thread_id 区分会话）
# ================================================================

async def resume_conversation(thread_id: str, new_input: str):
    """恢复历史对话继续执行"""

    config = {
        "configurable": {
            "thread_id": thread_id  # 关键：指定对话线程
        }
    }

    # 获取历史状态
    current_state = agent_graph.get_state(config)

    # 更新状态继续执行
    updated_state = {
        **current_state.values,
        "current_query": new_input
    }

    # 继续执行
    result = await agent_graph.ainvoke(updated_state, config)

    return result["response"]


# ================================================================
# SqliteSaver 存储结构
# ================================================================

"""
checkpoints 表：
  thread_id TEXT NOT NULL
  checkpoint_id TEXT NOT NULL
  parent_checkpoint_id TEXT
  checkpoint TEXT NOT NULL (JSON)
  metadata TEXT (JSON)
  created_at REAL (julianday)

checkpoint_writes 表：
  thread_id TEXT NOT NULL
  checkpoint_id TEXT NOT NULL
  task_id TEXT NOT NULL
  channel TEXT NOT NULL
  idx INTEGER NOT NULL
  value TEXT

特性：
- WAL 模式 + NORMAL 同步（性能与安全平衡）
- 线程局部连接（threading.local）
- JSON 序列化失败时降级到 pickle hex
- 支持 get_tuple / list / put / put_writes / delete_thread
"""
```

> **与设计文档 v2.0 的差异**：
> - v2.0 设计使用 `langgraph.checkpoint.sqlite.SqliteSaver`（内置），实际 LangGraph 1.2.x 未内置，需自定义实现
> - 实际实现基于 `langgraph.checkpoint.base.BaseCheckpointSaver` 自行实现
> - 存储路径：`data/agent_checkpoints.db`（项目根目录）

---

## 五、LangSmith 监控方案

### 5.1 LangSmith 集成

```python
# ================================================================
# LangSmith 全局初始化（core/langsmith_setup.py）
# ================================================================

"""LangSmith 全局追踪初始化。

作用：把 settings 里的 LangSmith 配置导出为 LangChain/LangSmith SDK 在运行时识别的
环境变量，使阶段 1+ 节点上的 @traceable 装饰器自动上报调用链路。

为什么用环境变量而非代码传参：
  LangChain 与 langsmith SDK 在导入/运行时直接读取 LANGSMITH_*/LANGCHAIN_* 环境变量，
  统一在这里设置即"全局生效"；用户改 .env 即可开关或换项目，无需改代码。

调用时机：app 启动时（main.py lifespan）调用一次 setup_langsmith()。
"""

from app.core.config import settings

def setup_langsmith() -> bool:
    """根据配置设置 LangSmith 全局环境变量。返回是否启用了追踪。"""
    if not settings.langsmith_enabled:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return False

    api_key = settings.langsmith_api_key or os.environ.get("LANGSMITH_API_KEY", "")
    if not api_key:
        return False

    env = {
        "LANGSMITH_TRACING": "true",
        "LANGSMITH_API_KEY": api_key,
        "LANGSMITH_PROJECT": settings.langsmith_project,
        "LANGSMITH_ENDPOINT": settings.langsmith_endpoint,
        "LANGCHAIN_TRACING_V2": "true",
        "LANGCHAIN_API_KEY": api_key,
        "LANGCHAIN_PROJECT": settings.langsmith_project,
        "LANGCHAIN_ENDPOINT": settings.langsmith_endpoint,
    }
    os.environ.update(env)
    return True
```

```python
# ================================================================
# LangSmith 调用时机（main.py lifespan）
# ================================================================

from contextlib import asynccontextmanager
from app.core.langsmith_setup import setup_langsmith

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动时初始化
    setup_logging()
    setup_langsmith()  # ← 在此处调用，全局生效
    setup_scheduler()  # 监控定时任务
    yield
    # 关闭时优雅释放资源
    ...


# ================================================================
# Agent 节点上的 @traceable 装饰器（agent/nodes.py）
# ================================================================

from langsmith import traceable

@traceable(name="agent.route", tags=["agent", "routing"])
def route_query(state: dict) -> dict:
    """路由决策节点。LangSmith 自动记录：输入 state、输出 state、执行时间。"""
    ...

@traceable(name="agent.search", tags=["agent", "retrieval"])
def search_knowledge(state: dict) -> dict:
    """检索节点。LangSmith 自动记录：检索耗时、结果数量、平均分数。"""
    ...

@traceable(name="agent.generate", tags=["agent", "generation"])
def generate_response(state: dict) -> dict:
    """生成节点。LangSmith 自动记录：prompt tokens、completion tokens、延迟。"""
    ...

# 其他节点（check_confidence, check_consistency, verify_facts, content_moderation 等）
# 同样使用 @traceable 装饰器，LangSmith 自动追踪整个调用链路
```

```python
# ================================================================
# LLM 调用追踪（core/llm.py）
# ================================================================

def chat_with_usage(messages: list[dict], temperature: float = 0.3) -> tuple[str, dict]:
    """非流式对话，返回 (答案文本, {prompt_tokens, completion_tokens})。

    LangSmith 通过 @traceable 装饰器自动记录：
    - 输入 messages
    - 输出 response
    - 模型名（settings.llm_model）
    - Token 消耗（prompt_tokens, completion_tokens）
    - 延迟（通过 langsmith 自动计算）
    """
    resp = _chat_completion(messages, temperature)
    usage = resp.usage or {}
    return (
        resp.choices[0].message.content or "",
        {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        },
    )
```

> **与实际实现的对应关系**：
> 1. **配置位置**：`core/config.py` 中的 `langsmith_enabled`、`langsmith_api_key`、`langsmith_project`、`langsmith_endpoint` 字段
> 2. **初始化位置**：`main.py` 的 `lifespan()` 函数中调用 `setup_langsmith()`
> 3. **追踪方式**：`@traceable` 装饰器直接标记在 `agent/nodes.py` 的 11 个节点函数上
> 4. **LLM 追踪**：`core/llm.py` 的 `chat_with_usage()` 返回 token 消耗数据，LangSmith 自动记录
> 5. **不使用**：
>    - `os.environ` 硬编码在业务代码中（仅在 `langsmith_setup.py` 中设置）
>    - `LangChainCheckpointSaver`（实际使用自定义 `SqliteSaver`）
>    - 手动 `trace()` 上下文管理器

### 5.2 LangSmith Dashboard 展示内容

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           LangSmith Dashboard                                  │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  项目概览                         最近 7 天                               │   │
│  │                                                                              │   │
│  │  总调用次数    平均延迟    Token消耗    错误率                           │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │   │
│  │  │  12,847 │  │  1.2s   │  │  2.3M   │  │  0.8%   │                     │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  调用链路追踪 (Trace)                                                    │   │
│  │                                                                              │   │
│  │  Run ID: run_abc123                                                       │   │
│  │  Status: Success                                                           │   │
│  │  Duration: 2.34s                                                           │   │
│  │                                                                              │   │
│  │  route (0.12s)                                                            │   │
│  │    → search (0.45s)                                                        │   │
│  │    → check_confidence (0.02s)                                              │   │
│  │    → generate (1.77s)  ← tokens: 342 in, 156 out                          │   │
│  │    → check_consistency (0.15s)                                             │   │
│  │    → verify_facts (0.08s)                                                  │   │
│  │    → content_moderation (0.05s)                                            │   │
│  │                                                                              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Prompt 版本管理                                                         │   │
│  │                                                                              │   │
│  │  版本    创建时间        使用次数    状态                                 │   │
│  │  v1.2    2024-01-15     3,421        Current                              │   │
│  │  v1.1    2024-01-10     8,234        Deprecated                           │   │
│  │                                                                              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 监控指标

| 指标 | 来源 | 说明 |
|------|------|------|
| 总调用次数 | LangSmith | 所有 @traceable 节点的调用次数 |
| 平均延迟 | LangSmith | 各节点执行时间 + LLM 响应时间 |
| Token 消耗 | chat_with_usage() | prompt_tokens + completion_tokens |
| 错误率 | LangSmith | 节点执行失败比例 |
| 拒答率 | agent_refusal_log | 触发拒答的查询比例 |
| 引用质量 | citation_quality_log | 句子级引用评估结果 |
| 知识库健康度 | kb_health_log | 每日自动健康检查 |
| LLM 成本 | llm_cost_log | 按天 + 模型聚合的成本统计 |

---

## 六、ChromaDB 向量检索 + 时效性调整

> **技术选型说明**：本项目中检索层采用 **ChromaDB 本地嵌入式向量检索 + 自定义时效性调整**，不使用 LlamaIndex、BM25、Cohere Rerank 或 Elasticsearch。原因是 ChromaDB 已满足就业政策问答场景的检索需求，减少外部依赖和运维复杂度。

### 6.1 检索架构概览

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              检索层                                             │
│                                                                                  │
│  user_query                                                                     │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Query Processing                                                       │   │
│  │  • 查询改写（可选，基于 LLM）                                             │   │
│  │  • FAQ 快速命中（faq_collection 优先检查）                                 │   │
│  │  • 语义缓存检查（Redis，semantic_cache_enabled）                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  ChromaDB 向量检索                                                       │   │
│  │  • collection: kb_chunks (主知识库)                                       │   │
│  │  • collection: kb_faqs (FAQ 专用集合)                                     │   │
│  │  • top_k: retrieve_top_k (默认 5)                                         │   │
│  │  • score_threshold: retrieve_score_threshold (默认 0.4)                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  时效性调整（agent/temporal_retriever.py）                                │   │
│  │  • apply_temporal_adjustment(): 计算综合得分                                │   │
│  │    combined = similarity * 0.7 + temporal_score * 0.3                      │   │
│  │  • filter_expired_docs(): 过滤/降权过期文档                                │   │
│  │  • 半衰期：kb_freshness_half_life (默认 180 天)                            │   │
│  │  • 过期宽限期：kb_warning_days (默认 30 天)                                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│      │                                                                          │
│      ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  引用构建（agent/citation_tracker.py）                                    │   │
│  │  • build_citations(): 构建引用列表                                         │   │
│  │  • 句子级别引用追踪（支持度验证：direct/indirect/none）                     │   │
│  │  • CITATION_SNIPPET_MAX_LENGTH (默认 200 字符)                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 为什么选择 ChromaDB 直接检索？

```
当前实现（ChromaDB + 时效性调整）：

┌─────────────────────────────────────────────────────────────────────────┐
│  user_query                                                              │
│      │                                                                  │
│      ├─→ FAQ 快速命中（cosine similarity >= 0.75）                       │
│      │                                                                  │
│      ├─→ ChromaDB 向量检索（kb_chunks collection）                       │
│      │   • top_k = retrieve_top_k                                        │
│      │   • 过滤 score < retrieve_score_threshold                         │
│      │                                                                  │
│      ├─→ 时效性调整（temporal_retriever.py）                              │
│      │   • combined_score = similarity * 0.7 + temporal * 0.3             │
│      │   • 过期文档降权（* 0.1）或宽限期降权（* 0.5）                      │
│      │                                                                  │
│      └─→ 引用构建（citation_tracker.py）                                  │
│          • 句子级引用 + 支持度验证                                         │
│                                                                          │
│  优势：                                                                   │
│  ✅ 复用现有 ChromaDB 基础设施                                             │
│  ✅ 减少外部依赖（无需 Cohere API、Elasticsearch）                         │
│  ✅ 语义缓存（Redis）已覆盖性能优化需求                                    │
│  ✅ 时效性调整直接在检索结果上叠加，无需额外框架                            │
│  ✅ 就业政策场景数据量适中，ChromaDB 足够支撑                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 ChromaDB 向量检索

```python
# ================================================================
# ChromaDB 向量检索（实际 core/vectorstore.py）
# V1 简化版：功能性 API（非类封装）
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/core/vectorstore.py`

实际采用功能性 API（非类封装），核心函数：

1. _collection(name) → 获取/创建持久化集合（LRU 缓存）
   - 使用 chromadb.PersistentClient(path=settings.chroma_dir)
   - 集合元数据：hnsw:space = cosine

2. _col(collection) → 默认集合快捷方式
   - collection 为 None 时使用 settings.chroma_collection（默认 kb_chunks）

3. upsert(ids, embeddings, documents, metadatas, collection) → None
   - 新增/更新向量
   - 外部传入 embedding（本模块不负责向量化）

4. query(embedding, top_k, where, collection) → list[dict]
   - 向量检索，返回 [{id, document, metadata, score}]
   - score = 1 - distance（余弦相似度）

5. delete(ids, where, collection) → None
   - 按 id 或条件删除向量

6. count(collection) → int
   - 集合内向量数量

存储约定：
- 每个向量的 id 用文档分片的 vector_id（字符串）
- metadata 至少含 document_id / chunk_id，便于检索后回查 MySQL
- 向量由外部(embedding 模块)生成后传入，本模块不负责向量化
"""

from functools import lru_cache
from typing import Optional

import chromadb

from app.core.config import settings


@lru_cache
def _collection(name: str):
    """获取(或创建)持久化集合，余弦距离。"""
    client = chromadb.PersistentClient(path=settings.chroma_dir)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def _col(collection: Optional[str]):
    return _collection(collection or settings.chroma_collection)


def upsert(
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
    collection: Optional[str] = None,
) -> None:
    """新增/更新向量。collection 默认文档分片集合。"""
    if not ids:
        return
    _col(collection).upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(
    embedding: list[float], top_k: int = 5, where: Optional[dict] = None, collection: Optional[str] = None
) -> list[dict]:
    """向量检索，返回 [{id, document, metadata, score}]，score 为相似度(1-距离)。"""
    res = _col(collection).query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    hits: list[dict] = []
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    for i in range(len(ids)):
        hits.append(
            {
                "id": ids[i],
                "document": docs[i] if i < len(docs) else None,
                "metadata": metas[i] if i < len(metas) else {},
                "score": round(1 - dists[i], 4) if i < len(dists) else None,
            }
        )
    return hits


def delete(ids: Optional[list[str]] = None, where: Optional[dict] = None, collection: Optional[str] = None) -> None:
    """按 id 或条件删除向量。"""
    if ids:
        _col(collection).delete(ids=ids)
    elif where:
        _col(collection).delete(where=where)


def count(collection: Optional[str] = None) -> int:
    """集合内向量数量。"""
    return _col(collection).count()
```

### 6.4 时效性调整

```python
# ================================================================
# 时效性调整（实际 agent/temporal_retriever.py）
# V1 简化版：仅标记过期，不修改得分
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/agent/temporal_retriever.py`

V1 实现（简化版）：
- filter_expired_docs(db, doc_ids) → set[int]
  - 查询 MySQL 返回已过期文档 ID 集合
  - 由 search_knowledge 节点调用（需要 db 会话）

- apply_temporal_adjustment(hits, expired_ids) → list[dict]
  - V1 仅添加 is_expired 标记，不修改得分
  - 由上层节点决定是否降权或展示警告

- get_expiring_soon_docs(db, warning_days) → list[dict]
  - 供监控模块调用

V2 预留接口：
- TemporalAwareRetriever.retrieve() → raise NotImplementedError
  - 设计意图：综合得分 = similarity × 0.7 + temporal × 0.3
"""

from datetime import date
from sqlalchemy.orm import Session
from app.models import KbDocument


def filter_expired_docs(db: Session, doc_ids: list[int]) -> set[int]:
    """过滤已过期文档 ID（V1 简化版）。"""
    if not doc_ids:
        return set()

    today = date.today()
    expired_rows = (
        db.query(KbDocument.id)
        .filter(
            KbDocument.id.in_(doc_ids),
            KbDocument.status == 1,
            KbDocument.expire_date.isnot(None),
            KbDocument.expire_date < today,
        )
        .all()
    )
    return {row.id for row in expired_rows}


def apply_temporal_adjustment(hits: list[dict], expired_ids: set[int]) -> list[dict]:
    """对检索结果应用时效性调整（V1 简化：仅标记过期）。

    V1 不修改得分，仅对过期文档添加 is_expired 标记。
    """
    adjusted = []
    for h in hits:
        doc_id = (h.get("metadata") or {}).get("document_id")
        h_copy = dict(h)
        h_copy["is_expired"] = doc_id in expired_ids if doc_id is not None else False
        adjusted.append(h_copy)
    return adjusted
```

### 6.5 引用构建

```python
# ================================================================
# 引用构建（实际 agent/citation_tracker.py）
# V1 简化版：Chunk 级别引用 + 质量评估
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：`backend/app/agent/citation_tracker.py`

V1 实现（当前代码库中的实际实现）：

1. build_citations(hits) → list[dict]
   - 从检索结果构建引用列表（chunk 级别）
   - 每条引用包含 rank / document_id / document_title / chunk_id /
     score / page_no / snippet（截断至 CITATION_SNIPPET_MAX_LENGTH=200 字符）

2. evaluate_citation_quality(citations) → dict
   - 评估引用整体质量（V1 简化版）
   - 仅基于检索得分和引用数量做统计
   - 按得分区间映射为 direct / indirect / none
   - V2 再引入 SentenceLevelCitationTracker 做逐句验证

3. SentenceLevelCitationTracker（V2 预留接口）
   - track() 方法未实现，raise NotImplementedError
   - 设计意图：将回答按 。！？； 切分为句子
   - 对每个句子找最相关的来源 chunk（Embedding 相似度）
   - 使用 LLM 验证引用支持度（direct/indirect/none）
"""

from app.agent.constants import CITATION_SNIPPET_MAX_LENGTH


def build_citations(hits: list[dict]) -> list[dict]:
    """从检索结果构建引用列表（V1 简化：chunk 级别）。

    Args:
        hits: 检索结果列表（来自 rag_service.search）

    Returns:
        引用列表，每条包含 rank / document_id / document_title / chunk_id /
        score / page_no / snippet
    """
    citations = []
    for rank, h in enumerate(hits, start=1):
        citations.append(
            {
                "rank": rank,
                "document_id": h.get("document_id"),
                "document_title": h.get("document_title"),
                "chunk_id": h.get("chunk_id"),
                "score": h.get("score"),
                "page_no": h.get("page_no"),
                "snippet": (h.get("content") or "")[:CITATION_SNIPPET_MAX_LENGTH],
            }
        )
    return citations


def evaluate_citation_quality(citations: list[dict]) -> dict:
    """评估引用整体质量（V1 简化版）。

    V1 仅基于检索得分和引用数量做统计，不做 LLM 级验证。
    V2 再引入 SentenceLevelCitationTracker 做逐句验证。
    """
    total = len(citations)
    if total == 0:
        return {
            "quality_score": 0.0,
            "direct_count": 0,
            "indirect_count": 0,
            "none_count": 0,
            "avg_score": 0.0,
            "issues": ["无引用"],
        }

    scores = [c.get("score") or 0.0 for c in citations]
    avg_score = sum(scores) / total

    # V1 简化：按得分区间映射为 direct / indirect / none
    direct_count = sum(1 for s in scores if s >= 0.75)
    indirect_count = sum(1 for s in scores if 0.40 <= s < 0.75)
    none_count = total - direct_count - indirect_count

    quality_score = (
        direct_count * 1.0 + indirect_count * 0.5 + none_count * 0.0
    ) / total

    issues = []
    if none_count > 0:
        issues.append(f"{none_count} 条引用得分较低")
    if avg_score < 0.5:
        issues.append(f"平均引用得分偏低({avg_score:.2f})")

    return {
        "quality_score": round(quality_score, 4),
        "direct_count": direct_count,
        "indirect_count": indirect_count,
        "none_count": none_count,
        "avg_score": round(avg_score, 4),
        "issues": issues,
    }


# ===== V2 预留接口（句子级别引用）=====

class SentenceLevelCitationTracker:
    """句子级别引用追踪器（V2 实现，V1 仅预留接口）。"""

    def __init__(self, embed_model: Any, llm_client: Any) -> None:
        self.embed_model = embed_model
        self.llm_client = llm_client

    def track(self, response: str, source_chunks: list[dict]) -> list[dict]:
        """追踪句子级别引用（V2 实现）。"""
        raise NotImplementedError("SentenceLevelCitationTracker.track() 将在 V2 实现")
```

### 6.6 语义缓存（Redis）

```python
# ================================================================
# 语义缓存（core/semantic_cache.py）
# ================================================================

"""
语义缓存架构（Redis + 内存 LRU 双层）：

L1: 进程内存 LRU 缓存（embedding_memory_cache_size 条，默认 4096）
L2: Redis 缓存（embedding_cache_ttl 秒，默认 86400 = 24h）

命中条件：语义相似度 >= semantic_cache_similarity_threshold（默认 0.92）

降级策略：
  - Redis 不可用时自动走 L1 内存缓存
  - L1 未命中时走实际 Embedding + 检索
  - 开关：semantic_cache_enabled（默认 true）
"""
```

### 6.7 完整检索流程

```python
# ================================================================
# 实际检索流程（agent/tools.py → knowledge_search + rag_service.py → search）
# ================================================================

"""
> **与实际代码的对应关系**

实际文件：
- `backend/app/agent/tools.py` → knowledge_search() + ToolCallTracker
- `backend/app/services/rag_service.py` → search() + _build_messages()
- `backend/app/core/vectorstore.py` → query() / upsert() / delete() / count()
- `backend/app/agent/temporal_retriever.py` → filter_expired_docs() / apply_temporal_adjustment()
- `backend/app/agent/citation_tracker.py` → build_citations()

实际检索流程（search_knowledge 节点中）：
1. 检索去重：相同查询跳过（retry > 0 时允许不同查询）
2. 重试时改写查询：去掉具体限定词，扩大召回（_broaden_query）
3. 调用 knowledge_search() → 内部调用 rag_service.search()
4. 工具调用计数：ToolCallTracker.record()
5. 过滤过期文档：filter_expired_docs(db, doc_ids)
6. 时效性调整：apply_temporal_adjustment(filtered_hits, expired_ids)
7. 构建引用：build_citations(adjusted_hits)
8. 计算置信度：adjusted_hits[0]["score"] if adjusted_hits else 0.0

注意：FAQ 命中优先和语义缓存在 ask/ask_stream 中处理，不在 Agent 节点内。
"""

from app.agent.tools import knowledge_search, ToolCallTracker
from app.agent.citation_tracker import build_citations
from app.agent.temporal_retriever import apply_temporal_adjustment, filter_expired_docs
from app.core.database import SessionLocal


def _broaden_query(query: str) -> str:
    """重试时去掉限定词，扩大检索范围。"""
    stop_words = ["具体", "详细", "最新", "今年", "2024", "2025", "怎么", "如何", "什么"]
    broadened = query
    for sw in stop_words:
        broadened = broadened.replace(sw, "")
    broadened = " ".join(broadened.split())
    return broadened if broadened else query


# agent/tools.py 中的 knowledge_search 实现：
def knowledge_search(query: str, top_k: int = 5) -> list[dict]:
    """知识库语义检索。

    返回命中片段列表，每条包含 document_title / content / score / page_no。
    无结果时返回空列表。
    """
    from app.services.rag_service import search as rag_search

    db = SessionLocal()
    try:
        return rag_search(db, query, top_k=top_k)
    finally:
        db.close()


# agent/tools.py 中的 ToolCallTracker：
class ToolCallTracker:
    """工具调用计数器 + 调用记录。"""

    def __init__(self) -> None:
        self.count: int = 0
        self.calls: list[dict] = []

    def record(self, tool_name: str, args: dict, result: Any) -> None:
        self.count += 1
        self.calls.append(
            {
                "tool": tool_name,
                "args": args,
                "result_summary": str(result)[:200] if result else None,
            }
        )

    def should_stop(self, max_calls: int = 3) -> bool:
        return self.count >= max_calls
```

---

## 七、功能模块详细设计

### 7.1 数据库设计

#### 7.1.1 ER 图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              核心业务实体                                         │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐                               │
│  │    sys_user     │         │   qa_conversation│                              │
│  │    (用户)        │         │   (对话会话)     │                               │
│  │                 │         │                  │                               │
│  │ • id (PK)       │◄────────│ • user_id (FK)  │                               │
│  │ • username      │         │ • id (PK)        │                               │
│  │ • password_hash │         │ • title          │                               │
│  │ • real_name     │         │ • status         │                               │
│  │ • role          │         │ • created_at     │                               │
│  │ • created_at    │         └────────┬─────────┘                               │
│  └─────────────────┘                  │                                          │
│                                      │ 1:N                                        │
│                                      ▼                                           │
│                              ┌─────────────────┐                                 │
│                              │   qa_message    │                                 │
│                              │   (消息)         │                                 │
│                              │                  │                                 │
│                              │ • id (PK)        │                                 │
│                              │ • conversation_id│                                │
│                              │ • role           │                                │
│                              │ • content        │                                │
│                              │ • answer_type    │  ←--- 实际：答案类型(1/2/3)    │
│                              │ • is_no_answer   │                                │
│                              │ • rewritten_query│  ←--- 实际：查询改写结果        │
│                              │ • confidence     │                                │
│                              │ • query_risk_level │ ←--- 实际：风险等级          │
│                              │ • consistency_issues │ ←--- 实际：一致性问题(JSON) │
│                              │ • fact_issues    │  ←--- 实际：事实问题(JSON)      │
│                              │ • temporal_warnings │ ←--- 实际：时效警告(JSON)   │
│                              │ • llm_model      │                                │
│                              │ • prompt_tokens  │  ←--- 实际：输入token           │
│                              │ • completion_tokens │ ←--- 实际：输出token        │
│                              │ • latency_ms     │  ←--- 实际：响应延迟            │
│                              │ • created_at     │                                 │
│                              └────────┬─────────┘                                 │
│                                       │ 1:N                                        │
│                                       ▼                                           │
│                              ┌─────────────────┐                                 │
│                              │ qa_message_ref  │                                 │
│                              │ (消息引用)       │                                 │
│                              │                  │                                 │
│                              │ • id (PK)        │                                 │
│                              │ • message_id(FK) │                                │
│                              │ • document_id    │                                │
│                              │ • chunk_id       │                                │
│                              │ • snippet        │  ←--- 实际：引用片段           │
│                              │ • score          │                                │
│                              │ • rank_no        │                                │
│                              │ • created_at     │                                 │
│                              └─────────────────┘                                 │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │ kb_chunk        │         │ kb_faq          │         │ kb_category     │   │
│  │ (文档块)        │         │ (FAQ)           │         │ (文档分类)      │   │
│  │                 │         │                 │         │                 │   │
│  │ • id (PK)       │         │ • id (PK)       │         │ • id (PK)       │   │
│  │ • document_id   │         │ • question      │         │ • name          │   │
│  │ • content       │         │ • answer        │         │ • parent_id     │   │
│  │ • chunk_index   │         │ • keywords      │         │ • level         │   │
│  │ • char_count    │         │ • hit_count     │         │ • sort_order    │   │
│  │ • embedding     │         │ • is_current    │         └─────────────────┘   │
│  │ • vector_id     │         │ • created_at    │                               │
│  └─────────────────┘         └─────────────────┘                               │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │ op_sensitive_word│       │ op_query_log    │         │ kb_health_log   │   │
│  │ (敏感词)        │         │ (查询日志)       │         │ (健康度记录)    │   │
│  │                 │         │                 │         │                 │   │
│  │ • id (PK)       │         │ • id (PK)       │         │ • id (PK)       │   │
│  │ • word          │         │ • user_id       │         │ • check_date    │   │
│  │ • category      │         │ • query         │         │ • health_score  │   │
│  │ • action        │         │ • route         │         │ • warning_count │   │
│  │ • status        │         │ • confidence    │         │ • expired_count │   │
│  │ • created_at    │         │ • created_at    │         │ • created_at    │   │
│  └─────────────────┘         └─────────────────┘         └─────────────────┘   │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │ llm_cost_log    │         │ agent_refusal_log│        │ consistency_    │   │
│  │ (LLM成本)       │         │ (拒答记录)       │        │ issue_log       │   │
│  │                 │         │                 │        │ (一致性记录)    │   │
│  │ • id (PK)       │         │ • id (PK)       │        │                 │   │
│  │ • stat_date     │         │ • query         │        │ • id (PK)       │   │
│  │ • model         │         │ • refusal_reason│        │ • message_id    │   │
│  │ • tokens_in/out │         │ • confidence    │        │ • contradiction │   │
│  │ • cost_usd      │         │ • risk_level    │        │ • severity      │   │
│  │ • created_at    │         │ • created_at    │        │ • created_at    │   │
│  └─────────────────┘         └─────────────────┘         └─────────────────┘   │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐                                 │
│  │ citation_quality│         │ fact_verification│                                │
│  │ _log            │         │ _log             │                                │
│  │ (引用质量)      │         │ (事实核验)       │                                │
│  │                 │         │                  │                                │
│  │ • id (PK)       │         │ • id (PK)        │                                │
│  │ • message_id    │         │ • message_id     │                                │
│  │ • quality_score │         │ • fact_type      │                                │
│  │ • direct_count  │         │ • extracted_value│                                │
│  │ • created_at    │         │ • is_valid       │                                │
│  └─────────────────┘         └─────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

> **实际实现说明**：以上表结构由 SQLAlchemy ORM 模型定义（位于 `backend/app/models/` 目录），通过 Alembic 迁移自动生成 DDL。模型文件划分：
> - `models/user.py` → 用户与权限 (`sys_*`)
> - `models/knowledge.py` → 知识库 (`kb_*`)
> - `models/qa.py` → 问答与会话 (`qa_*`)
> - `models/ops.py` → 运营·安全 (`op_*`)
> - `models/monitor.py` → 监控告警 (`kb_*_log`, `llm_cost_log`, `agent_refusal_log`, `citation_quality_log`, `consistency_issue_log`, `fact_verification_log`)

#### 7.1.2 详细表结构

```sql
-- ================================================================
-- 用户表
-- ================================================================

CREATE TABLE `sys_user` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL COMMENT '用户名/学工号',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `real_name` VARCHAR(100) COMMENT '真实姓名',
    `email` VARCHAR(100) COMMENT '邮箱',
    `phone` VARCHAR(20) COMMENT '手机号',
    `role` ENUM('student', 'teacher', 'admin') NOT NULL DEFAULT 'student' COMMENT '角色',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0禁用 1启用',
    `last_login_at` DATETIME COMMENT '最后登录时间',
    `last_login_ip` VARCHAR(50) COMMENT '最后登录IP',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_username` (`username`),
    KEY `idx_role` (`role`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户表';


-- ================================================================
-- 对话会话表
-- ================================================================

CREATE TABLE `qa_conversation` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '会话ID',
    `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    `title` VARCHAR(200) COMMENT '会话标题',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0删除 1正常',
    `message_count` INT NOT NULL DEFAULT 0 COMMENT '消息数量',
    `last_message_at` DATETIME COMMENT '最后消息时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_last_message` (`last_message_at`),
    FOREIGN KEY (`user_id`) REFERENCES `sys_user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问答会话表';


-- ================================================================
-- 消息表（增强版）
-- ================================================================

CREATE TABLE `qa_message` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '消息ID',
    `conversation_id` BIGINT UNSIGNED NOT NULL COMMENT '会话ID',
    `role` ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `confidence` DECIMAL(5,4) COMMENT '置信度 0-1',
    `is_no_answer` TINYINT NOT NULL DEFAULT 0 COMMENT '是否无法回答：0否 1是',
    `is_from_faq` TINYINT NOT NULL DEFAULT 0 COMMENT '是否来自FAQ命中',
    `is_blocked` TINYINT NOT NULL DEFAULT 0 COMMENT '是否被拦截：0否 1是',
    `block_reason` VARCHAR(500) COMMENT '拦截原因',
    `tools_used` JSON COMMENT '使用的工具列表',
    `route` VARCHAR(50) COMMENT '路由决策：search/tool_call/direct/refuse',
    `llm_model` VARCHAR(100) COMMENT '使用的LLM模型',
    `llm_tokens_in` INT COMMENT '输入Token数',
    `llm_tokens_out` INT COMMENT '输出Token数',
    `llm_latency_ms` INT COMMENT 'LLM响应延迟(毫秒)',
    `parent_message_id` BIGINT UNSIGNED COMMENT '父消息ID（用于追问）',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_conversation_id` (`conversation_id`),
    KEY `idx_role` (`role`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_confidence` (`confidence`),
    FOREIGN KEY (`conversation_id`) REFERENCES `qa_conversation`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`parent_message_id`) REFERENCES `qa_message`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='问答消息表';


-- ================================================================
-- 消息引用表（增强版 - 支持引用追踪）
-- ================================================================

CREATE TABLE `qa_message_reference` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '引用ID',
    `message_id` BIGINT UNSIGNED NOT NULL COMMENT '消息ID',
    `document_id` BIGINT UNSIGNED COMMENT '文档ID',
    `chunk_id` BIGINT UNSIGNED COMMENT '文档块ID',
    `chunk_text` TEXT COMMENT '引用片段原文',
    `citation_text` VARCHAR(500) COMMENT '引用标注文本',
    `page_no` INT COMMENT '页码',
    `score` DECIMAL(6,4) COMMENT '相似度得分',
    `rank_no` INT COMMENT '引用排序号',
    `valid_until` DATETIME COMMENT '内容有效期',
    `source_url` VARCHAR(500) COMMENT '来源URL',
    `metadata` JSON COMMENT '额外元数据',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_message_id` (`message_id`),
    KEY `idx_document_id` (`document_id`),
    KEY `idx_score` (`score`),
    FOREIGN KEY (`message_id`) REFERENCES `qa_message`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`document_id`) REFERENCES `kb_document`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`chunk_id`) REFERENCES `kb_chunk`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息引用表';


-- ================================================================
-- 文档表（增强版 - 支持版本管理和时效性）
-- ================================================================

CREATE TABLE `kb_document` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '文档ID',
    `title` VARCHAR(500) NOT NULL COMMENT '文档标题',
    `category` VARCHAR(100) COMMENT '分类：policy/process/regulation/faq',
    `source` VARCHAR(200) COMMENT '来源机构',
    `doc_no` VARCHAR(200) COMMENT '文件编号',
    `version` VARCHAR(50) COMMENT '版本号',
    `valid_from` DATE COMMENT '生效日期',
    `valid_until` DATE COMMENT '失效日期',
    `is_current` TINYINT NOT NULL DEFAULT 1 COMMENT '是否为当前有效版本',
    `superseded_by` BIGINT UNSIGNED COMMENT '被哪个版本替代',
    `file_path` VARCHAR(500) COMMENT '文件存储路径',
    `file_size` BIGINT COMMENT '文件大小(字节)',
    `file_hash` VARCHAR(64) COMMENT '文件哈希(SHA256)',
    `chunk_count` INT COMMENT '分块数量',
    `upload_by` BIGINT UNSIGNED COMMENT '上传人ID',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0禁用 1启用',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_category` (`category`),
    KEY `idx_valid_from` (`valid_from`),
    KEY `idx_valid_until` (`valid_until`),
    KEY `idx_status` (`status`),
    KEY `idx_is_current` (`is_current`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档表';


-- ================================================================
-- 文档块表
-- ================================================================

CREATE TABLE `kb_chunk` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '块ID',
    `document_id` BIGINT UNSIGNED NOT NULL COMMENT '文档ID',
    `content` TEXT NOT NULL COMMENT '块内容',
    `chunk_index` INT COMMENT '块序号',
    `char_count` INT COMMENT '字符数',
    `token_count` INT COMMENT 'Token数',
    `vector_id` VARCHAR(100) COMMENT '向量库ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_document_id` (`document_id`),
    KEY `idx_chunk_index` (`chunk_index`),
    FOREIGN KEY (`document_id`) REFERENCES `kb_document`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文档块表';


-- ================================================================
-- 工具调用日志表
-- ================================================================

CREATE TABLE `agent_tool_call` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '调用ID',
    `message_id` BIGINT UNSIGNED COMMENT '关联消息ID',
    `trace_id` VARCHAR(100) COMMENT 'LangSmith Trace ID',
    `run_id` VARCHAR(100) COMMENT 'LangSmith Run ID',
    `tool_name` VARCHAR(100) NOT NULL COMMENT '工具名称',
    `tool_category` VARCHAR(50) COMMENT '工具类别',
    `input_params` JSON COMMENT '输入参数',
    `output_result` JSON COMMENT '输出结果',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0失败 1成功',
    `error_message` TEXT COMMENT '错误信息',
    `latency_ms` INT COMMENT '执行延迟(毫秒)',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_message_id` (`message_id`),
    KEY `idx_tool_name` (`tool_name`),
    KEY `idx_trace_id` (`trace_id`),
    KEY `idx_created_at` (`created_at`),
    FOREIGN KEY (`message_id`) REFERENCES `qa_message`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent工具调用日志表';


-- ================================================================
-- Agent 执行链路表（用于 LangSmith 链路追踪）
-- ================================================================

CREATE TABLE `agent_execution_trace` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '链路ID',
    `trace_id` VARCHAR(100) NOT NULL COMMENT '追踪ID',
    `run_id` VARCHAR(100) COMMENT 'Run ID',
    `user_id` BIGINT UNSIGNED COMMENT '用户ID',
    `message_id` BIGINT UNSIGNED COMMENT '消息ID',
    `node_name` VARCHAR(100) NOT NULL COMMENT '节点名称',
    `node_type` VARCHAR(50) COMMENT '节点类型',
    `parent_run_id` VARCHAR(100) COMMENT '父节点Run ID',
    `input_data` JSON COMMENT '输入数据',
    `output_data` JSON COMMENT '输出数据',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0失败 1成功',
    `latency_ms` INT COMMENT '执行时间(毫秒)',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_trace_id` (`trace_id`),
    KEY `idx_run_id` (`run_id`),
    KEY `idx_message_id` (`message_id`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Agent执行链路表';


-- ================================================================
-- 知识库版本表
-- ================================================================

CREATE TABLE `kb_version` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '版本ID',
    `version_code` VARCHAR(50) NOT NULL COMMENT '版本号',
    `version_name` VARCHAR(200) COMMENT '版本名称',
    `doc_count` INT COMMENT '文档数量',
    `chunk_count` INT COMMENT '块数量',
    `valid_from` DATETIME NOT NULL COMMENT '生效时间',
    `valid_until` DATETIME COMMENT '失效时间',
    `change_log` TEXT COMMENT '变更日志',
    `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0历史 1当前 2未来',
    `created_by` BIGINT UNSIGNED COMMENT '创建人',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_version_code` (`version_code`),
    KEY `idx_status` (`status`),
    KEY `idx_valid_from` (`valid_from`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库版本表';


-- ================================================================
-- 拒答记录表（新增 - 用于分析优化）
-- ================================================================

CREATE TABLE `agent_refusal_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `query` TEXT NOT NULL COMMENT '用户问题',
    `refusal_reason` VARCHAR(200) NOT NULL COMMENT '拒答原因',
    `confidence` DECIMAL(5,4) COMMENT '拒答时的置信度',
    `search_results_count` INT COMMENT '检索结果数量',
    `query_risk_level` VARCHAR(20) COMMENT '查询风险等级：high/medium/low',
    `threshold_config` JSON COMMENT '阈值配置',
    `user_id` BIGINT UNSIGNED COMMENT '用户ID（可为空）',
    `conversation_id` BIGINT UNSIGNED COMMENT '会话ID',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `reviewed` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已审核',
    `is_valid` TINYINT COMMENT '拒答是否合理',
    `suggested_action` VARCHAR(100) COMMENT '建议操作（如补充知识库）',
    PRIMARY KEY (`id`),
    KEY `idx_created_at` (`created_at`),
    KEY `idx_reviewed` (`reviewed`),
    KEY `idx_refusal_reason` (`refusal_reason`),
    KEY `idx_risk_level` (`query_risk_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='拒答记录表';


-- ================================================================
-- 引用质量评估表（新增）
-- ================================================================

CREATE TABLE `citation_quality_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `message_id` BIGINT UNSIGNED NOT NULL COMMENT '消息ID',
    `citation_id` BIGINT UNSIGNED NOT NULL COMMENT '引用ID',
    `sentence_text` TEXT COMMENT '回答中的句子',
    `source_chunk_id` VARCHAR(100) COMMENT '来源chunk ID',
    `support_type` VARCHAR(20) COMMENT '支持类型：direct/indirect/none',
    `support_score` DECIMAL(5,4) COMMENT '支持度得分',
    `quality_issues` JSON COMMENT '质量问题列表',
    `overall_score` DECIMAL(5,4) COMMENT '综合质量得分',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_message_id` (`message_id`),
    KEY `idx_support_type` (`support_type`),
    KEY `idx_quality_score` (`overall_score`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='引用质量评估表';


-- ================================================================
-- 知识库健康度记录表（新增）
-- ================================================================

CREATE TABLE `kb_health_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `check_date` DATE NOT NULL COMMENT '检查日期',
    `total_docs` INT NOT NULL COMMENT '文档总数',
    `current_docs` INT NOT NULL COMMENT '当前有效文档数',
    `warning_docs` INT NOT NULL COMMENT '预警文档数',
    `expired_docs` INT NOT NULL COMMENT '已过期文档数',
    `avg_freshness` DECIMAL(5,4) COMMENT '平均新鲜度',
    `health_score` DECIMAL(5,4) COMMENT '健康度评分',
    `recommendations` JSON COMMENT '改进建议',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_check_date` (`check_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库健康度记录表';


-- ================================================================
-- LLM成本监控表（新增）
-- ================================================================

CREATE TABLE `llm_cost_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `date` DATE NOT NULL COMMENT '日期',
    `hour` TINYINT COMMENT '小时（0-23）',
    `model` VARCHAR(100) NOT NULL COMMENT '模型名称',
    `tokens_in` INT NOT NULL COMMENT '输入Token数',
    `tokens_out` INT NOT NULL COMMENT '输出Token数',
    `cost_usd` DECIMAL(10,6) COMMENT '成本（美元）',
    `request_count` INT NOT NULL COMMENT '请求数',
    `avg_latency_ms` INT COMMENT '平均延迟',
    `error_count` INT DEFAULT 0 COMMENT '错误数',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_date` (`date`),
    KEY `idx_model` (`model`),
    KEY `idx_hour` (`hour`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM成本监控表';


-- ================================================================
-- 一致性问题记录表（新增）
-- ================================================================

CREATE TABLE `consistency_issue_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `conversation_id` BIGINT UNSIGNED NOT NULL COMMENT '会话ID',
    `current_message_id` BIGINT UNSIGNED NOT NULL COMMENT '当前消息ID',
    `previous_message_id` BIGINT UNSIGNED NOT NULL COMMENT '历史消息ID',
    `current_query` TEXT COMMENT '当前问题',
    `previous_query` TEXT COMMENT '历史问题',
    `contradiction_type` VARCHAR(50) COMMENT '矛盾维度',
    `severity` VARCHAR(20) COMMENT '严重程度：high/medium/low',
    `resolution_status` VARCHAR(20) DEFAULT 'pending' COMMENT '处理状态',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_conversation_id` (`conversation_id`),
    KEY `idx_severity` (`severity`),
    KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='一致性问题记录表';


-- ================================================================
-- 事实核验问题记录表（新增）
-- ================================================================

CREATE TABLE `fact_verification_log` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'ID',
    `message_id` BIGINT UNSIGNED NOT NULL COMMENT '消息ID',
    `fact_type` VARCHAR(50) NOT NULL COMMENT '事实类型',
    `extracted_value` VARCHAR(500) COMMENT '提取到的值',
    `validation_result` VARCHAR(500) COMMENT '验证结果',
    `suggestion` VARCHAR(500) COMMENT '建议修正',
    `is_valid` TINYINT COMMENT '是否有效',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_message_id` (`message_id`),
    KEY `idx_fact_type` (`fact_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='事实核验问题记录表';


-- ================================================================
-- 修改现有表：添加成本字段到 qa_message
-- ================================================================

ALTER TABLE `qa_message`
ADD COLUMN `cost_usd` DECIMAL(10,6) COMMENT '本次对话成本（美元）' AFTER `llm_latency_ms`,
ADD COLUMN `query_risk_level` VARCHAR(20) COMMENT '查询风险等级' AFTER `route`,
ADD COLUMN `consistency_checked` TINYINT DEFAULT 0 COMMENT '是否已检查一致性' AFTER `query_risk_level`,
ADD COLUMN `fact_verified` TINYINT DEFAULT 0 COMMENT '是否已核验事实' AFTER `consistency_checked`,
ADD COLUMN `citation_quality_score` DECIMAL(5,4) COMMENT '引用质量得分' AFTER `fact_verified`;


-- ================================================================
-- 修改现有表：agent_tool_call 字段长度扩展
-- ================================================================

ALTER TABLE `agent_tool_call`
MODIFY COLUMN `trace_id` VARCHAR(200) COMMENT 'LangSmith Trace ID',
MODIFY COLUMN `run_id` VARCHAR(200) COMMENT 'LangSmith Run ID';
```

### 7.2 接口设计

#### 7.2.1 Agent 对话接口

```yaml
# ================================================================
# Agent 对话接口
# ================================================================

/api/v1/agent/chat:
  post:
    summary: Agent 智能对话
    tags:
      - Agent
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - query
            properties:
              query:
                type: string
                description: 用户问题
                example: "应届毕业生落户上海需要准备哪些材料？"
                maxLength: 1000
              conversation_id:
                type: integer
                description: 会话ID（可选，不传则创建新会话）
                nullable: true
              stream:
                type: boolean
                description: 是否使用流式响应
                default: true
              context:
                type: object
                description: 额外上下文（如用户画像摘要）
                properties:
                  user_major:
                    type: string
                    description: 用户专业
                  user_graduation_year:
                    type: integer
                    description: 毕业年份
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                  example: 0
                message:
                  type: string
                  example: ok
                data:
                  type: object
                  properties:
                    conversation_id:
                      type: integer
                      description: 会话ID
                    message_id:
                      type: integer
                      description: 消息ID
                    response:
                      type: string
                      description: AI 回答内容
                    confidence:
                      type: number
                      format: float
                      description: 置信度 0-1
                    is_no_answer:
                      type: boolean
                      description: 是否无法回答
                    route:
                      type: string
                      description: 路由决策
                      enum: [search, tool_call, direct, refuse]
                    tools_used:
                      type: array
                      items:
                        type: string
                      description: 使用的工具列表
                    citations:
                      type: array
                      items:
                        $ref: '#/components/schemas/Citation'
                    version_info:
                      $ref: '#/components/schemas/VersionInfo'
                    latency_ms:
                      type: integer
                      description: 总延迟（毫秒）

/api/v1/agent/chat/stream:
  post:
    summary: Agent 智能对话（流式）
    tags:
      - Agent
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/AgentChatRequest'
    responses:
      '200':
        description: 成功
        description: |
          SSE 流式响应

          event: delta
          data: {"text": "根据", "is_final": false}

          event: delta
          data: {"text": "政策", "is_final": false}

          event: citation
          data: {"id": 1, "doc_title": "上海市落户指南", "page": 3}

          event: done
          data: {"confidence": 0.85, "is_final": true, ...}

          event: error
          data: {"code": 500, "message": "LLM调用失败"}

          event: heartbeat
          data: {"timestamp": "2024-01-15T10:30:00Z"}

/api/v1/agent/history:
  get:
    summary: 获取对话历史
    tags:
      - Agent
    security:
      - BearerAuth: []
    parameters:
      - name: conversation_id
        in: query
        required: true
        schema:
          type: integer
        description: 会话ID
      - name: page
        in: query
        schema:
          type: integer
          default: 1
        description: 页码
      - name: size
        in: query
        schema:
          type: integer
          default: 20
          maximum: 100
        description: 每页数量
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                  example: 0
                data:
                  type: object
                  properties:
                    total:
                      type: integer
                    page:
                      type: integer
                    size:
                      type: integer
                    items:
                      type: array
                      items:
                        type: object
                        properties:
                          id:
                            type: integer
                          role:
                            type: string
                            enum: [user, assistant]
                          content:
                            type: string
                          confidence:
                            type: number
                          citations:
                            type: array
                            items:
                              $ref: '#/components/schemas/Citation'
                          created_at:
                            type: string
                            format: date-time

/api/v1/agent/feedback:
  post:
    summary: 提交反馈
    tags:
      - Agent
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - message_id
              - is_helpful
            properties:
              message_id:
                type: integer
                description: 消息ID
              is_helpful:
                type: boolean
                description: 是否有用
              feedback_type:
                type: string
                enum: [helpful, not_helpful, inaccurate, harmful]
                description: 反馈类型
              feedback_detail:
                type: string
                description: 反馈详情
                maxLength: 500
    responses:
      '200':
        description: 成功

/api/v1/agent/trace/{trace_id}:
  get:
    summary: 获取执行链路详情（LangSmith 风格）
    tags:
      - Agent
    security:
      - BearerAuth: []
    parameters:
      - name: trace_id
        in: path
        required: true
        schema:
          type: string
        description: 追踪ID
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                data:
                  type: object
                  properties:
                    trace_id:
                      type: string
                    status:
                      type: string
                    duration_ms:
                      type: integer
                    total_cost:
                      type: number
                    runs:
                      type: array
                      items:
                        type: object
                        properties:
                          run_id:
                            type: string
                          name:
                            type: string
                          type:
                            type: string
                          status:
                            type: string
                          started_at:
                            type: string
                          ended_at:
                            type: string
                          latency_ms:
                            type: integer
                          inputs:
                            type: object
                          outputs:
                            type: object
                          error:
                            type: string
                          child_runs:
                            type: array
                            items:
                              $ref: '#/components/schemas/Run'
```

#### 7.2.2 知识库管理接口

```yaml
# ================================================================
# 知识库管理接口
# ================================================================

/api/v1/knowledge/document:
  post:
    summary: 上传文档
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            required:
              - file
            properties:
              file:
                type: string
                format: binary
                description: 文档文件（支持 PDF/Word/TXT）
              category:
                type: string
                enum: [policy, process, regulation, faq, other]
                description: 文档分类
              title:
                type: string
                description: 文档标题（可选，从文件名提取）
              source:
                type: string
                description: 来源机构
              doc_no:
                type: string
                description: 文件编号
              valid_from:
                type: string
                format: date
                description: 生效日期
              valid_until:
                type: string
                format: date
                description: 失效日期
    responses:
      '201':
        description: 上传成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                  example: 0
                data:
                  type: object
                  properties:
                    document_id:
                      type: integer
                    title:
                      type: string
                    status:
                      type: string
                      description: 状态：uploading/processing/completed/failed
                    task_id:
                      type: string
                      description: 异步任务ID

  get:
    summary: 文档列表
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        schema:
          type: integer
          default: 1
      - name: size
        in: query
        schema:
          type: integer
          default: 20
      - name: category
        in: query
        schema:
          type: string
          enum: [policy, process, regulation, faq, other]
      - name: status
        in: query
        schema:
          type: string
          enum: [uploading, processing, completed, failed]
      - name: keyword
        in: query
        schema:
          type: string
        description: 搜索关键词
    responses:
      '200':
        description: 成功

/api/v1/knowledge/document/{document_id}:
  get:
    summary: 文档详情
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    parameters:
      - name: document_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      '200':
        description: 成功

  delete:
    summary: 删除文档
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    parameters:
      - name: document_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      '200':
        description: 成功

/api/v1/knowledge/document/{document_id}/chunks:
  get:
    summary: 文档块列表
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    parameters:
      - name: document_id
        in: path
        required: true
        schema:
          type: integer
      - name: page
        in: query
        schema:
          type: integer
          default: 1
      - name: size
        in: query
        schema:
          type: integer
          default: 50
    responses:
      '200':
        description: 成功

/api/v1/knowledge/version:
  get:
    summary: 获取当前知识库版本信息
    tags:
      - Knowledge
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                data:
                  type: object
                  properties:
                    version_code:
                      type: string
                    version_name:
                      type: string
                    doc_count:
                      type: integer
                    chunk_count:
                      type: integer
                    valid_from:
                      type: string
                      format: date-time
                    age_days:
                      type: integer
                      description: 版本年龄（天）
                    is_stale:
                      type: boolean
                      description: 是否过时（超过90天）
                    change_log:
                      type: string

/api/v1/knowledge/reindex:
  post:
    summary: 触发知识库重建索引
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              mode:
                type: string
                enum: [full, incremental]
                default: incremental
                description: 重建模式
    responses:
      '202':
        description: 已接受，异步处理
```

#### 7.2.3 统计监控接口

```yaml
# ================================================================
# 统计监控接口
# ================================================================

/api/v1/stats/overview:
  get:
    summary: 概览统计
    tags:
      - Stats
    security:
      - BearerAuth: []
    parameters:
      - name: start_date
        in: query
        schema:
          type: string
          format: date
        description: 开始日期
      - name: end_date
        in: query
        schema:
          type: string
          format: date
        description: 结束日期
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                data:
                  type: object
                  properties:
                    total_queries:
                      type: integer
                      description: 总问答数
                    total_users:
                      type: integer
                      description: 总用户数
                    avg_confidence:
                      type: number
                      format: float
                      description: 平均置信度
                    no_answer_rate:
                      type: number
                      format: float
                      description: 无法回答率
                    top_tools:
                      type: array
                      items:
                        type: object
                        properties:
                          tool_name:
                            type: string
                          call_count:
                            type: integer
                          avg_latency_ms:
                            type: integer
                    route_distribution:
                      type: object
                      description: 路由分布
                      properties:
                        search:
                          type: integer
                        tool_call:
                          type: integer
                        direct:
                          type: integer
                        refuse:
                          type: integer

/api/v1/stats/quality:
  get:
    summary: 质量分析
    tags:
      - Stats
    security:
      - BearerAuth: []
    parameters:
      - name: period
        in: query
        schema:
          type: string
          enum: [day, week, month]
        description: 统计周期
    responses:
      '200':
        description: 成功

/api/v1/stats/cost:
  get:
    summary: LLM 成本统计
    tags:
      - Stats
    security:
      - BearerAuth: []
    parameters:
      - name: start_date
        in: query
        schema:
          type: string
          format: date
      - name: end_date
        in: query
        schema:
          type: string
          format: date
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    total_tokens:
                      type: integer
                    input_tokens:
                      type: integer
                    output_tokens:
                      type: integer
                    estimated_cost:
                      type: number
                      format: float
                      description: 预估成本（元）
                    cost_by_model:
                      type: array
                      items:
                        type: object
                        properties:
                          model:
                            type: string
                          tokens:
                            type: integer
                          cost:
                            type: number
```

#### 7.2.4 拒答反馈接口（新增）

```yaml
# ================================================================
# 拒答反馈接口
# ================================================================

/api/v1/agent/refusal/feedback:
  post:
    summary: 拒答反馈（用户标记AI不该拒答）
    tags:
      - Agent
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - message_id
              - feedback
            properties:
              message_id:
                type: integer
                description: 消息ID
              feedback:
                type: string
                enum: [valid, invalid]
                description: |
                  反馈类型：
                  - valid: 拒答合理，确认AI判断正确
                  - invalid: 拒答不合理，用户认为应该回答
              correct_answer:
                type: string
                description: 用户认为正确的回答（可选，用于补充知识库）
              suggested_document:
                type: string
                description: 建议补充的文档来源（可选）
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                  example: 0
                message:
                  type: string
                  example: "反馈已记录，感谢您的帮助"
                data:
                  type: object
                  properties:
                    feedback_id:
                      type: integer
                    will_update_kb:
                      type: boolean
                      description: 是否会根据反馈更新知识库


/api/v1/agent/refusal/stats:
  get:
    summary: 拒答统计分析
    tags:
      - Agent
    security:
      - BearerAuth: []
    parameters:
      - name: start_date
        in: query
        schema:
          type: string
          format: date
        description: 开始日期
      - name: end_date
        in: query
        schema:
          type: string
          format: date
        description: 结束日期
      - name: group_by
        in: query
        schema:
          type: string
          enum: [reason, risk_level, day]
        description: 分组维度
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    total_refusals:
                      type: integer
                    by_reason:
                      type: array
                      items:
                        type: object
                        properties:
                          reason:
                            type: string
                          count:
                            type: integer
                          percentage:
                            type: number
                    by_risk_level:
                      type: array
                      items:
                        type: object
                        properties:
                          level:
                            type: string
                          count:
                            type: integer
                    invalid_rate:
                      type: number
                      description: 用户反馈"拒答不合理"的比例
                    improvement_suggestions:
                      type: array
                      items:
                        type: string
```

#### 7.2.5 知识库健康度接口（新增）

```yaml
# ================================================================
# 知识库健康度接口
# ================================================================

/api/v1/kb/health:
  get:
    summary: 知识库健康度
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                  example: 0
                data:
                  type: object
                  properties:
                    health_score:
                      type: number
                      description: 健康度评分 0-100
                      example: 85.5
                    status:
                      type: string
                      enum: [healthy, warning, critical]
                      description: 健康状态
                    total_docs:
                      type: integer
                      description: 文档总数
                    current_docs:
                      type: integer
                      description: 当前有效文档数
                    avg_freshness_days:
                      type: number
                      description: 平均新鲜度（天）
                    warning_docs:
                      type: array
                      description: 即将过期文档列表
                      items:
                        type: object
                        properties:
                          id:
                            type: integer
                          title:
                            type: string
                          valid_until:
                            type: string
                            format: date
                          days_until_expiry:
                            type: integer
                          category:
                            type: string
                    expired_docs:
                      type: array
                      description: 已过期文档列表
                      items:
                        type: object
                        properties:
                          id:
                            type: integer
                          title:
                            type: string
                          valid_until:
                            type: string
                            format: date
                          days_expired:
                            type: integer
                    recommendations:
                      type: array
                      items:
                        type: string
                    last_check_time:
                      type: string
                      format: date-time


/api/v1/kb/health/history:
  get:
    summary: 知识库健康度历史
    tags:
      - Knowledge
    security:
      - BearerAuth: []
    parameters:
      - name: days
        in: query
        schema:
          type: integer
          default: 30
        description: 查询天数
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    history:
                      type: array
                      items:
                        type: object
                        properties:
                          date:
                            type: string
                            format: date
                          health_score:
                            type: number
                          warning_count:
                            type: integer
                          expired_count:
                            type: integer
                    trend:
                      type: string
                      enum: [improving, stable, declining]
                    avg_score:
                      type: number
```

#### 7.2.6 LLM成本监控接口（新增）

```yaml
# ================================================================
# LLM成本监控接口
# ================================================================

/api/v1/admin/llm/cost:
  get:
    summary: LLM成本统计
    tags:
      - Admin
    security:
      - BearerAuth: []
    parameters:
      - name: start_date
        in: query
        schema:
          type: string
          format: date
        description: 开始日期
      - name: end_date
        in: query
        schema:
          type: string
          format: date
        description: 结束日期
      - name: group_by
        in: query
        schema:
          type: string
          enum: [day, hour, model]
        description: 分组维度
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: integer
                  example: 0
                data:
                  type: object
                  properties:
                    total_cost_usd:
                      type: number
                      description: 总成本（美元）
                    total_tokens_in:
                      type: integer
                      description: 总输入Token数
                    total_tokens_out:
                      type: integer
                      description: 总输出Token数
                    total_requests:
                      type: integer
                      description: 总请求数
                    avg_cost_per_request:
                      type: number
                      description: 平均每次请求成本
                    avg_latency_ms:
                      type: integer
                      description: 平均延迟
                    error_rate:
                      type: number
                      description: 错误率
                    daily_costs:
                      type: array
                      description: 每日成本明细
                      items:
                        type: object
                        properties:
                          date:
                            type: string
                            format: date
                          cost:
                            type: number
                          tokens_in:
                            type: integer
                          tokens_out:
                            type: integer
                          requests:
                            type: integer
                    by_model:
                      type: array
                      description: 按模型分组
                      items:
                        type: object
                        properties:
                          model:
                            type: string
                          cost:
                            type: number
                          requests:
                            type: integer
                          avg_latency:
                            type: integer
                    cost_threshold:
                      type: number
                      description: 每日成本阈值
                    threshold_exceeded:
                      type: boolean
                      description: 是否超过阈值
                    alert_history:
                      type: array
                      description: 成本告警历史
                      items:
                        type: object
                        properties:
                          date:
                            type: string
                          threshold:
                            type: number
                          actual:
                            type: number


/api/v1/admin/llm/cost/threshold:
  post:
    summary: 设置成本阈值
    tags:
      - Admin
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - daily_threshold
            properties:
              daily_threshold:
                type: number
                description: 每日成本阈值（美元）
              monthly_threshold:
                type: number
                description: 每月成本阈值（美元）
              alert_recipients:
                type: array
                items:
                  type: string
                description: 告警接收人邮箱列表
    responses:
      '200':
        description: 成功
```

#### 7.2.7 引用质量评估接口（新增）

```yaml
# ================================================================
# 引用质量评估接口
# ================================================================

/api/v1/agent/citation/quality:
  get:
    summary: 引用质量统计
    tags:
      - Agent
    security:
      - BearerAuth: []
    parameters:
      - name: start_date
        in: query
        schema:
          type: string
          format: date
      - name: end_date
        in: query
        schema:
          type: string
          format: date
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    avg_quality_score:
                      type: number
                      description: 平均引用质量得分
                    direct_support_rate:
                      type: number
                      description: 直接支持比例
                    indirect_support_rate:
                      type: number
                      description: 间接支持比例
                    no_support_rate:
                      type: number
                      description: 无支持比例
                    total_citations:
                      type: integer
                    issues:
                      type: array
                      items:
                        type: object
                        properties:
                          message_id:
                            type: integer
                          sentence:
                            type: string
                          issue_type:
                            type: string
                          score:
                            type: number


/api/v1/agent/citation/verify:
  post:
    summary: 验证单条引用
    tags:
      - Agent
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - sentence
              - source_text
            properties:
              sentence:
                type: string
                description: 回答中的句子
              source_text:
                type: string
                description: 引用来源文本
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    support_type:
                      type: string
                      enum: [direct, indirect, none]
                    confidence:
                      type: number
                    explanation:
                      type: string
                      description: LLM给出的判断理由
```

#### 7.2.8 一致性检查接口（新增）

```yaml
# ================================================================
# 一致性检查接口
# ================================================================

/api/v1/agent/consistency/check:
  post:
    summary: 检查对话一致性
    tags:
      - Agent
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - conversation_id
            properties:
              conversation_id:
                type: integer
                description: 会话ID
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    is_consistent:
                      type: boolean
                    issues:
                      type: array
                      items:
                        type: object
                        properties:
                          current_query:
                            type: string
                          previous_query:
                            type: string
                          contradiction_type:
                            type: string
                          severity:
                            type: string
                          suggestion:
                            type: string


/api/v1/agent/consistency/stats:
  get:
    summary: 一致性问题统计
    tags:
      - Agent
    security:
      - BearerAuth: []
    parameters:
      - name: days
        in: query
        schema:
          type: integer
          default: 7
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    total_issues:
                      type: integer
                    high_severity_count:
                      type: integer
                    by_contradiction_type:
                      type: array
                      items:
                        type: object
                        properties:
                          type:
                            type: string
                          count:
                            type: integer
                    resolution_rate:
                      type: number
```

#### 7.2.9 事实核验接口（新增）

```yaml
# ================================================================
# 事实核验接口
# ================================================================

/api/v1/agent/fact/verify:
  post:
    summary: 核验回答中的事实
    tags:
      - Agent
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - response
            properties:
              response:
                type: string
                description: AI回答内容
              context:
                type: object
                description: 上下文信息
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    total_facts:
                      type: integer
                      description: 提取到的事实数量
                    valid_facts:
                      type: integer
                      description: 有效事实数量
                    issues:
                      type: array
                      items:
                        type: object
                        properties:
                          fact_type:
                            type: string
                          value:
                            type: string
                          validation_result:
                            type: string
                          suggestion:
                            type: string
                    overall_score:
                      type: number


/api/v1/agent/fact/stats:
  get:
    summary: 事实核验统计
    tags:
      - Agent
    security:
      - BearerAuth: []
    parameters:
      - name: days
        in: query
        schema:
          type: integer
          default: 7
    responses:
      '200':
        description: 成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: object
                  properties:
                    total_verifications:
                      type: integer
                    issue_rate:
                      type: number
                    by_fact_type:
                      type: array
                      items:
                        type: object
                        properties:
                          type:
                            type: string
                          total:
                            type: integer
                          invalid:
                            type: integer
                          rate:
                            type: number
```

### 7.3 核心参数定义

#### 7.3.1 系统参数（实际 config.py）

```python
# ================================================================
# 实际配置参数（backend/app/core/config.py → Settings）
# ================================================================

# ===== 应用配置 =====
app_name: str = "高校智慧就业服务平台 - AI问答模块"
app_env: str = "dev"                          # 环境：dev / production
app_debug: bool = False                       # 调试模式
api_prefix: str = "/api/v1"                   # API 前缀

server_host: str = "127.0.0.1"                # 监听地址（0.0.0.0 允许局域网）
server_port: int = 8000                       # 监听端口

# ===== 数据库 =====
db_host: str = "127.0.0.1"
db_port: int = 3306
db_user: str = "root"
db_password: str                               # 生产环境必须设置
db_name: str = "claudecode_rag"
db_charset: str = "utf8mb4"
db_pool_size: int = 10
db_pool_recycle: int = 3600
db_echo: bool = False

# ===== JWT 鉴权 =====
jwt_secret: str                                # 生产环境必须设置（建议64位）
jwt_algorithm: str = "HS256"
jwt_expire_minutes: int = 120                  # 令牌有效期（默认2小时）

# ===== 文件上传 =====
upload_dir: str = "uploads"
max_upload_mb: int = 50

# ===== RAG / LLM =====
dashscope_api_key: str                         # 从环境变量 DASHSCOPE_API_KEY 读取
dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
embedding_model: str = "text-embedding-v4"     # 通义千问 Embedding
embedding_dim: int = 1024
llm_model: str = "qwen3.7-max"                 # 默认 LLM 模型

# ===== 语义分块 =====
chunk_min_chars: int = 200                     # 块最小字符数
chunk_max_chars: int = 500                     # 块最大字符数
semantic_breakpoint_percentile: int = 95       # 语义断点百分位阈值

# ===== 向量库（ChromaDB 本地嵌入式）=====
chroma_dir: str = "chroma_data"                # ChromaDB 数据目录
chroma_collection: str = "kb_chunks"           # 主知识库集合名

# ===== Redis（Embedding 缓存 L2）=====
redis_enabled: bool = True                     # 总开关
redis_host: str = "127.0.0.1"
redis_port: int = 6379
redis_db: int = 0
redis_password: str = ""
redis_socket_timeout: float = 1.5              # 连接超时（秒）
embedding_cache_ttl: int = 86400               # Embedding 缓存过期（秒，默认24h）
embedding_memory_cache_size: int = 4096        # L1 内存 LRU 容量（条数）

# ===== LangSmith =====
langsmith_enabled: bool = True                 # 全局开关
langsmith_api_key: str                         # 从环境变量 LANGSMITH_API_KEY 读取
langsmith_project: str = "myproject"
langsmith_endpoint: str = "https://api.smith.langchain.com"

# ===== 检索问答 =====
retrieve_top_k: int = 5                        # 检索返回数量
retrieve_score_threshold: float = 0.4          # 最高分低于此值走"无法回答"
faq_collection: str = "kb_faqs"               # FAQ 集合名
faq_score_threshold: float = 0.75              # FAQ 问法相似度阈值

# ===== Agent 配置 =====
agent_enabled: bool = False                    # 总开关（默认关闭，灰度开启）
agent_max_iterations: int = 10                 # 最大迭代步数
agent_timeout_seconds: int = 60                # 超时时间（秒）
agent_recursion_limit: int = 15                # LangGraph 递归限制
agent_rate_limit_per_user: int = 10            # 每用户每分钟最大请求数
agent_rate_limit_global: int = 100             # 全局每分钟最大请求数

# ===== 幻觉防御配置 =====
high_risk_threshold: float = 0.80              # 高风险阈值
medium_risk_threshold: float = 0.65            # 中风险阈值
low_risk_threshold: float = 0.40               # 低风险阈值

# ===== 时效性配置 =====
kb_warning_days: int = 30                      # 知识库过期告警天数
kb_freshness_half_life: int = 180              # 新鲜度半衰期（天）

# ===== 成本控制 =====
daily_cost_threshold_usd: float = 10.0         # 日成本阈值（美元）
monthly_cost_threshold_usd: float = 300.0      # 月成本阈值（美元）

# ===== 语义缓存 =====
semantic_cache_enabled: bool = True            # 语义缓存总开关
semantic_cache_similarity_threshold: float = 0.92  # 语义相似度阈值
semantic_cache_ttl: int = 86400                # 缓存过期时间（秒，默认24h）
```

> **与实际代码的对应关系**：`backend/app/core/config.py` 中的 `Settings` 类使用 Pydantic Settings 从 `.env` 文件读取配置，通过 `get_settings()` 获取全局单例。关键特性：
> - 生产环境必须设置 `DASHSCOPE_API_KEY`、`JWT_SECRET`（至少32位）、`DB_PASSWORD`
> - `jwt_secret` 在开发环境自动生成 64 位随机密钥
> - `database_url` 属性自动构建 SQLAlchemy 连接串（PyMySQL 驱动）

---

## 八、部署架构

> **实际部署方案**：项目使用 Docker Compose 一键部署（FastAPI + MySQL 8.4 + Redis 7 + ChromaDB 本地存储），暂未使用 Kubernetes 编排。以下是实际部署文件与配置。

### 8.1 部署架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                  Docker Compose 栈                                              │
├──────────────────┬────────────────────────────────────────────────────────────┤
│   Service        │   说明                                                        │
├──────────────────┼────────────────────────────────────────────────────────────┤
│   api            │   FastAPI 后端（主要服务，多阶段构建）                        │
│   db             │   MySQL 8.4（业务数据 + 监控日志）                           │
│   redis          │   Redis 7（Embedding 语义缓存 L2）                          │
│   (无独立chroma) │   ChromaDB 嵌入 api 容器，数据持久化到 chroma_data volume     │
└──────────────────┴────────────────────────────────────────────────────────────┘

数据卷：
  - db_data         → MySQL 数据目录
  - redis_data      → Redis 持久化
  - chroma_data     → 向量库数据（挂载到 api 容器 /app/chroma_data）
  - agent_checkpoints → Agent checkpoint SQLite（挂载到 api 容器 /app/data）
  - uploads         → 上传文件（挂载到 api 容器 /app/uploads）
```

### 8.2 Dockerfile（backend/Dockerfile）

```dockerfile
# ===== 构建阶段 =====
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装构建依赖（GCC + MySQL 客户端头文件）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装到 /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===== 运行阶段 =====
FROM python:3.11-slim AS runtime

WORKDIR /app

# 安装运行时依赖（MySQL 客户端共享库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient81 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Python 包
COPY --from=builder /install /usr/local

# 复制应用代码
COPY app/                    ./app/
COPY alembic.ini            ./
COPY migrations/             ./migrations/

# 创建持久化数据目录
RUN mkdir -p data uploads chroma_data

# 非 root 用户运行（安全）
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD curl -f http://localhost:8000/health/live || exit 1

# 启动命令（2 个 worker，生产环境根据 CPU 调整）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 8.3 Docker Compose 配置

```yaml
# docker-compose.yml（项目根目录）
version: "3.9"

services:
  # ===== MySQL 8.4 =====
  db:
    image: mysql:8.4
    container_name: rag_db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD:-123456}
      MYSQL_DATABASE: ${DB_NAME:-claudecode_rag}
      MYSQL_CHARSET: utf8mb4
      MYSQL_COLLATION: utf8mb4_0900_ai_ci
    ports:
      - "3306:3306"
    volumes:
      - db_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rag_net

  # ===== Redis（Embedding 缓存）=====
  redis:
    image: redis:7-alpine
    container_name: rag_redis
    restart: unless-stopped
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 60 1
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rag_net

  # ===== FastAPI 后端 =====
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: rag_api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      # 数据库
      DB_HOST: db
      DB_PORT: 3306
      DB_USER: root
      DB_PASSWORD: ${DB_PASSWORD:-123456}
      DB_NAME: ${DB_NAME:-claudecode_rag}
      # LLM
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
      LLM_MODEL: ${LLM_MODEL:-qwen-plus}
      EMBEDDING_MODEL: ${EMBEDDING_MODEL:-text-embedding-v4}
      # JWT
      JWT_SECRET: ${JWT_SECRET}
      # Redis
      REDIS_ENABLED: true
      REDIS_HOST: redis
      REDIS_PORT: 6379
      # Agent
      AGENT_ENABLED: ${AGENT_ENABLED:-true}
      # 环境
      APP_ENV: ${APP_ENV:-production}
      APP_DEBUG: "false"
    volumes:
      - ./backend/data:/app/data
      - ./backend/uploads:/app/uploads
      - ./backend/chroma_data:/app/chroma_data
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s
    networks:
      - rag_net

volumes:
  db_data:
    driver: local
  redis_data:
    driver: local
  chroma_data:
    driver: local

networks:
  rag_net:
    driver: bridge
```

> **说明**：
> 1. ChromaDB 不独立部署，以内嵌模式运行在 api 容器内，数据持久化到 `chroma_data` volume
> 2. 环境变量通过 `.env` 文件注入（`DASHSCOPE_API_KEY`、`JWT_SECRET`、`DB_PASSWORD` 等）
> 3. `AGENT_ENABLED` 控制 Agent 功能开关（灰度发布用）
> 4. 使用多阶段构建减小镜像体积（最终镜像约 300-400MB）

### 8.4 部署步骤

#### 1. 前置要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Docker Engine | 24+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| 内存 | >= 4GB | MySQL + Redis + API |
| 磁盘 | >= 10GB | 镜像 + 数据卷 |

#### 2. 配置环境变量

项目根目录的 `.env`：

```env
# ===== 数据库 =====
DB_PASSWORD=YourSecurePassword123!
DB_NAME=claudecode_rag

# ===== LLM (DashScope) =====
DASHSCOPE_API_KEY=your_dashscope_api_key_here
LLM_MODEL=qwen3.7-max

# ===== JWT =====
JWT_SECRET=your_very_long_and_random_secret_key_here_at_least_32_chars

# ===== Agent =====
AGENT_ENABLED=true

# ===== 环境 =====
APP_ENV=production
APP_DEBUG=false
```

#### 3. 启动服务

```bash
cd d:\enployment_service_agent

# 构建并启动所有服务
docker compose up -d --build

# 查看日志
docker compose logs -f api

# 查看服务状态
docker compose ps
```

#### 4. 初始化数据库

```bash
# 执行 Alembic 迁移
docker compose exec api python -m alembic upgrade head
```

#### 5. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health/live

# 登录测试
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 8.5 常用运维命令

```bash
# 停止服务（保留数据）
docker compose down

# 停止并删除数据（会清库）
docker compose down -v

# 重启某个服务
docker compose restart api

# 查看日志
docker compose logs -f --tail=100 api

# 进入容器调试
docker compose exec api bash

# 备份数据库
docker compose exec db mysqldump -u root -p123456 claudecode_rag > backup.sql

# 查看资源占用
docker compose stats
```

### 8.6 生产环境建议

| 建议 | 说明 |
|------|------|
| secrets 管理 | 使用 Docker secrets 或环境变量注入，不要将密钥写进镜像 |
| 资源限制 | 为每个服务添加 `deploy.resources.limits` |
| 日志驱动 | 配置 `json-file` 或 `fluentd` 日志驱动 |
| 备份策略 | 定期备份 `db_data` volume |
| HTTPS | 前端通过反向代理（Nginx/Traefik）接入，配置 TLS |
| 监控 | 添加 Prometheus + Grafana 监控容器状态 |

## 九、技术栈完整清单 (v3.0)

| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **Agent 框架** | LangGraph | 1.2.6 | 状态机工作流，11 节点 |
| **LLM 监控** | LangSmith | - | 调用链路追踪、Prompt 管理 |
| **向量数据库** | ChromaDB | 嵌入式 | 本地向量检索，无需独立服务 |
| **后端框架** | FastAPI | 0.115+ | 异步 API |
| **数据库** | MySQL | 8.4 | 主业务数据 + 监控日志 |
| **缓存** | Redis | 7.0 | Embedding 语义缓存（L2） |
| **LLM API** | DashScope | - | 通义千问（qwen3.7-max） |
| **Checkpoint** | SqliteSaver | 自定义 | LangGraph 对话持久化（SQLite） |
| **前端** | Vue3 + TS | 3.4+ | 用户界面 |
| **容器化** | Docker | 24+ | 多阶段构建 |
| **迁移** | Alembic | - | 数据库版本管理 |

---

## 十、面试核心要点总结

### 10.1 LangGraph 面试价值

| 面试点 | 回答要点 |
|--------|---------|
| **为什么用 LangGraph？** | 自研工作流的缺陷（状态管理、循环、调试困难）vs LangGraph 的优势（状态机、Checkpoint、支持复杂图结构） |
| **LangGraph 核心概念？** | State（状态）、Node（节点）、Edge（边）、Checkpoint（检查点） |
| **如何处理 Agent 循环？** | 条件边实现循环，设置 MAX_ITERATIONS 防止死循环 |
| **Checkpoint 有什么用？** | 支持对话暂停/恢复、历史回溯、故障恢复 |

### 10.2 LangSmith 面试价值

| 面试点 | 回答要点 |
|--------|---------|
| **为什么需要监控？** | LLM 调用是"黑盒"，无法排查问题；需要追踪每次调用、分析性能、降低成本 |
| **LangSmith 能做什么？** | 自动追踪调用链路、Prompt 版本管理、性能分析、成本统计、回归测试 |
| **如何集成？** | 设置环境变量 + 使用 @traceable 装饰器，LangGraph 自动集成 |
| **企业级价值？** | 可观测性是 SRE 核心，快速定位问题，优化成本 |

### 10.3 检索方案面试价值

| 面试点 | 回答要点 |
|--------|---------|
| **为什么不用 LlamaIndex？** | 项目已使用 ChromaDB 作为向量库，复用现有基础设施减少依赖；就业政策场景数据量适中，ChromaDB 足够支撑；减少外部依赖（Cohere API、Elasticsearch）降低运维复杂度 |
| **ChromaDB 本地嵌入式 vs HTTP 模式？** | 本地嵌入式模式更简单，无需独立部署 ChromaDB 服务，适合中小规模场景；数据持久化到本地文件系统，备份方便 |
| **时效性调整怎么做？** | V1 简化版：仅标记过期文档（is_expired），不修改检索得分；由上层节点决定如何处理过期文档；V2 预留 TemporalAwareRetriever 接口（综合得分 = similarity × 0.7 + temporal × 0.3） |
| **语义缓存如何工作？** | Redis L2 + 内存 LRU L1 双层缓存；命中条件：语义相似度 >= 0.92；不可用时自动降级到内存缓存 |
| **引用如何追踪？** | ChromaDB 检索结果自带 metadata（document_id, chunk_id 等），通过 citation_tracker.build_citations() 构建 chunk 级别引用列表；evaluate_citation_quality() 评估引用质量；V2 预留 SentenceLevelCitationTracker |

### 10.4 大模型问题解决方案

| 问题 | 解决方案 | 面试亮点 |
|------|---------|---------|
| **幻觉** | 五重防护：动态置信度阈值 + 置信度过滤 + 引用强制 + 一致性检查 + 事实核验 | 不是简单加 Prompt，而是系统性工程 |
| **不可溯源** | ChromaDB metadata + 句子级引用 + LLM judge 支持度验证 | 精确到句子级别的溯源体系 |
| **时效性低** | ChromaDB 时效性调整（指数衰减）+ 健康度监控 + 过期告警 | 算法优化 + 可观测性闭环 |

---

## 附录

### A. 环境变量清单

```bash
# .env 配置

# ===== LangSmith =====
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=myproject
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# ===== LLM =====
DASHSCOPE_API_KEY=your-dashscope-key
LLM_MODEL=qwen3.7-max
EMBEDDING_MODEL=text-embedding-v4

# ===== Database =====
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=xxx
DB_NAME=claudecode_rag

# ===== Redis =====
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=xxx
EMBEDDING_CACHE_TTL=86400

# ===== Agent =====
AGENT_ENABLED=true
AGENT_RECURSION_LIMIT=15

# ===== Retrieval =====
RETRIEVE_TOP_K=5
RETRIEVE_SCORE_THRESHOLD=0.4
FAQ_SCORE_THRESHOLD=0.75

# ===== 幻觉防御 =====
HIGH_RISK_THRESHOLD=0.80
MEDIUM_RISK_THRESHOLD=0.65
LOW_RISK_THRESHOLD=0.40

# ===== 语义缓存 =====
SEMANTIC_CACHE_ENABLED=true
SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.92
SEMANTIC_CACHE_TTL=86400

# ===== 时效性 =====
KB_WARNING_DAYS=30
KB_FRESHNESS_HALF_LIFE=180

# ===== 成本控制 =====
DAILY_COST_THRESHOLD_USD=10.0
MONTHLY_COST_THRESHOLD_USD=300.0
```

### B. 安装命令

```bash
# 安装依赖

# 核心依赖
pip install fastapi uvicorn sqlalchemy pymysql

# LangGraph
pip install langgraph langchain-core langchain-community

# LangSmith
pip install langsmith

# 向量库
pip install chromadb

# Redis 缓存
pip install redis

# 工具库
pip install httpx tiktoken python-dotenv pydantic-settings
```

---

---

## 附录 D：Docker 部署方案

> 本节提供完整的容器化部署方案，支持一键启动整个技术栈。

### D.1 部署架构

```
┌──────────────────────────────────────────────────────┐
│                  Docker Compose 栈                     │
├──────────────────┬────────────────────────────────────┤
│   Service        │   说明                              │
├──────────────────┼────────────────────────────────────┤
│   api            │   FastAPI 后端（主要服务）          │
│   db             │   MySQL 8.4（业务数据 + 日志）      │
│   redis          │   Redis（Embedding 缓存）           │
│   chroma        │   ChromaDB（向量库持久化）          │
└──────────────────┴────────────────────────────────────┘

数据卷：
  - db_data         → MySQL 数据目录
  - redis_data      → Redis 持久化
  - chroma_data     → 向量库数据
  - agent_checkpoints → Agent checkpoint SQLite
  - uploads         → 上传文件
```

### D.2 部署文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| `Dockerfile` | `backend/Dockerfile` | 多阶段构建，最终镜像约 300-400MB |
| `docker-compose.yml` | 项目根目录 | 编排 api / db / redis / chroma |
| `.dockerignore` | 项目根目录 | 排除 venv、数据目录、文档等 |
| `.env` | 项目根目录 | Docker Compose 的环境变量替换源 |

### D.3 部署步骤

#### 1. 前置要求

| 软件 | 版本 | 说明 |
|------|------|------|
| Docker Engine | 24+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| 内存 | >= 4GB | MySQL + Redis + Chroma + API |
| 磁盘 | >= 10GB | 镜像 + 数据卷 |

#### 2. 配置环境变量

项目根目录的 `.env`：

```env
# ===== 数据库 =====
DB_PASSWORD=YourSecurePassword123!
DB_NAME=claudecode_rag

# ===== LLM (DashScope) =====
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# ===== JWT =====
JWT_SECRET=your_very_long_and_random_secret_key_here_at_least_32_chars

# ===== Agent =====
AGENT_ENABLED=true

# ===== 环境 =====
APP_ENV=production
APP_DEBUG=false
```

#### 3. 启动服务

```bash
cd d:\enployment_service_agent

# 构建并启动所有服务
docker compose up -d --build

# 查看日志
docker compose logs -f api

# 查看服务状态
docker compose ps
```

#### 4. 初始化数据库

```bash
# 执行 Alembic 迁移
docker compose exec api python -m alembic upgrade head
```

#### 5. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health/live

# 登录测试
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### D.4 常用运维命令

```bash
# 停止服务（保留数据）
docker compose down

# 停止并删除数据（⚠️ 会清库）
docker compose down -v

# 重启某个服务
docker compose restart api

# 查看日志
docker compose logs -f --tail=100 api

# 进入容器调试
docker compose exec api bash

# 备份数据库
docker compose exec db mysqldump -u root -p123456 claudecode_rag > backup.sql

# 查看资源占用
docker compose stats
```

### D.5 生产环境建议

| 建议 | 说明 |
|------|------|
|  secrets 管理 | 使用 Docker secrets 或环境变量注入，不要将密钥写进镜像 |
|  资源限制 | 为每个服务添加 `deploy.resources.limits` |
|  日志驱动 | 配置 `json-file` 或 `fluentd` 日志驱动 |
|  备份策略 | 定期备份 `db_data` volume |
|  HTTPS | 前端通过反向代理（Nginx/Traefik）接入，配置 TLS |
|  监控 | 添加 Prometheus + Grafana 监控容器状态 |

---

*文档版本：v3.0*
*最后更新：2026-06-24*
