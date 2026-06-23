# 高校智慧就业服务平台 - Agent 智能体模块设计方案

> 文档版本：v3.0
> 创建时间：2026-06
> 最后更新：2026-06-23
> 项目定位：面向市场的高校智慧就业服务 SaaS 平台
> 技术栈：LangGraph + LangSmith + LlamaIndex + 通义千问

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
| 检索引擎 | ChromaDB 简单检索 | **LlamaIndex + 混合检索** | 多路召回、Rerank，检索质量大幅提升 |
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
| **LlamaIndex** | 展示RAG深度理解 | "混合检索怎么做？Rerank原理是什么？" |
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

#### 为什么选择 LlamaIndex？

| 维度 | 自研检索 | LlamaIndex | 结论 |
|------|---------|------------|------|
| 混合检索 | 需要自己实现 | 内置支持 | ✅ LlamaIndex 更成熟 |
| Rerank | 需要集成第三方 | 内置支持 | ✅ LlamaIndex 更方便 |
| Query 改写 | 需要自己实现 | 内置支持 | ✅ LlamaIndex 更智能 |
| 多路召回 | 需要自己实现 | 内置支持 | ✅ LlamaIndex 更强大 |
| 引用追踪 | 需要自己实现 | 内置 Citation | ✅ LlamaIndex 更完善 |

**LlamaIndex 面试价值**：
- 展示对 RAG 检索优化的理解（不是简单的向量相似度搜索）
- 体现对搜索系统（ES/Lucene）的理解（混合检索底层原理）
- 表明关注检索质量而非仅仅"能用"

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
│                              检索层 (LlamaIndex)                                │
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
| **检索层** | LlamaIndex | 混合检索、Rerank、引用追踪 |
| **数据层** | MySQL + Redis + OSS | 持久化、缓存、文件存储 |
| **LLM 层** | 通义千问 / GPT-4 | 核心推理能力 |

---

## 三、大模型问题解决方案

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

#### 三重防护机制

```python
# ================================================================
# 第一重：置信度过滤
# ================================================================

class ConfidenceFilter:
    """
    置信度过滤：只接受高置信度的检索结果
    """

    def __init__(self, min_score: float = 0.7):
        self.min_score = min_score

    def filter(self, results: list[SearchResult]) -> list[SearchResult]:
        """过滤低置信度结果"""
        filtered = [r for r in results if r.score >= self.min_score]

        if not filtered:
            # 低置信度 → 触发拒答机制
            raise LowConfidenceError(
                "检索结果置信度不足，无法生成可靠回答"
            )

        return filtered


# ================================================================
# 第二重：引用强制（Grounded Generation）
# ================================================================

class GroundedGeneration:
    """
    引用强制生成：要求每句话都必须有引用
    """

    SYSTEM_PROMPT = """
你是一个严谨的就业政策助手。

回答规则：
1. 每说一个事实，必须在句尾用 [来源: XXX] 标注来源
2. 如果检索结果中没有支持某个观点，直接说"这个信息我不确定"
3. 不要编造政策编号、日期、数字
4. 不确定时，宁可不说，不要说错

示例回答格式：
"根据《关于做好2024年毕业生就业工作的意见》[来源: 国办发〔2024〕5号]，
应届毕业生落户上海需要满足以下条件... [来源: 上海市人社局官网]"
"""

    def generate(self, query: str, context: list[Citation]) -> str:
        """生成带引用的回答"""
        # 在 Prompt 中强制要求引用
        prompt = f"""
问题：{query}

参考资料：
{self._format_citations(context)}

请基于以上参考资料回答问题，每句话都要标注来源。
"""

        response = llm.chat(prompt, system_prompt=self.SYSTEM_PROMPT)

        # 后处理：验证引用完整性
        return self._validate_citations(response, context)


# ================================================================
# 第三重：拒答机制
# ================================================================

class RefusalGenerator:
    """
    拒答机制：超出知识边界时直接拒绝
    """

    REFUSAL_TEMPLATE = """
抱歉，关于"{question}"这个问题：

1. 我的知识库中没有收录相关信息
2. 这个问题可能涉及较新的政策，建议您：
   - 联系学校就业中心老师咨询
   - 查看相关政府部门的官方网站
   - 拨打官方咨询热线

如果您还有其他就业相关问题，我很乐意帮助您。
"""

    def should_refuse(
        self,
        query: str,
        context: list[SearchResult],
        confidence: float
    ) -> tuple[bool, str]:
        """判断是否应该拒答"""

        # 拒答条件
        reasons = []

        if not context:
            reasons.append("知识库中没有相关内容")

        if confidence < 0.5:
            reasons.append("检索置信度过低")

        if self._is_out_of_scope(query):
            reasons.append("问题超出服务范围")

        if reasons:
            return True, self.REFUSAL_TEMPLATE.format(
                question=query,
                reasons=reasons
            )

        return False, None
```

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
# LlamaIndex Citation 实现
# ================================================================

from llama_index.core import VectorStoreIndex, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.core.response.notebook_utils import (
    display_source_node
)

class CitationAwareIndex:
    """
    支持精确引用的索引
    """

    def __init__(self):
        self.node_parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separator="。！？\n"
        )

    def build_index(self, documents: list[Document]):
        """构建带引用信息的索引"""

        # 1. 解析文档为节点
        nodes = self.node_parser.get_nodes_from_documents(documents)

        # 2. 为每个节点添加元数据
        for i, node in enumerate(nodes):
            node.metadata = {
                "chunk_id": i,
                "doc_title": node.metadata.get("doc_title"),
                "page_num": node.metadata.get("page_num"),
                "created_at": node.metadata.get("created_at"),
                "valid_until": node.metadata.get("valid_until"),  # 时效性
                "category": node.metadata.get("category"),  # policy/process/faq
            }

        # 3. 构建向量索引
        self.index = VectorStoreIndex(nodes)

        # 4. 配置重排序
        self.reranker = CohereRerank(
            api_key=COHERE_API_KEY,
            top_n=5
        )

    def query_with_citations(self, query: str):
        """查询并返回带引用的结果"""

        # 构建查询引擎
        query_engine = self.index.as_query_engine(
            similarity_top_k=10,
            node_postprocessors=[self.reranker]
        )

        # 执行查询
        response = query_engine.query(query)

        # 提取引用信息
        citations = []
        for source_node in response.source_nodes:
            citation = {
                "text": source_node.text,
                "doc_id": source_node.node_id,
                "doc_title": source_node.metadata.get("doc_title"),
                "page_num": source_node.metadata.get("page_num"),
                "score": source_node.score,
                "valid_until": source_node.metadata.get("valid_until"),
                # 生成引用 ID
                "ref_id": f"[{len(citations) + 1}]"
            }
            citations.append(citation)

        return {
            "answer": response.response,
            "citations": citations,
            "confidence": self._calculate_confidence(citations)
        }


# ================================================================
# 可视化引用展示
# ================================================================

def format_citations_for_display(citations: list[dict]) -> str:
    """格式化引用用于前端展示"""

    lines = []
    for i, cite in enumerate(citations, 1):
        # 检查时效性
        is_expired = _check_expiry(cite.get("valid_until"))

        status = "⚠️ 已过期" if is_expired else "✅ 有效"

        lines.append(f"""
📄 [{i}] {cite['doc_title']}
   📍 第{cite.get('page_num', 'N/A')}页
   📋 {cite['text'][:100]}...
   🎯 匹配度: {cite['score']:.2%}
   ⏰ {status}
   {cite.get('ref_id', '')}
""")

    return "\n".join(lines)
```

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

#### 解决方案：知识库版本管理 + 实时数据通道

```python
# ================================================================
# 知识库版本管理
# ================================================================

from datetime import datetime, timedelta

class KnowledgeBaseVersion:
    """
    知识库版本管理
    """

    def __init__(self):
        self.versions = {}  # version_id -> VersionInfo
        self.current_version = None

    def add_version(
        self,
        version_id: str,
        doc_count: int,
        valid_from: datetime,
        changelog: str
    ):
        """添加知识库版本"""

        self.versions[version_id] = {
            "version_id": version_id,
            "doc_count": doc_count,
            "valid_from": valid_from,
            "valid_until": None,  # 下一个版本发布前有效
            "changelog": changelog,
            "status": "active" if self.current_version is None else "superseded"
        }

        if self.current_version is None:
            self.current_version = version_id
        else:
            # 更新上一版本的截止日期
            self.versions[self.current_version]["valid_until"] = valid_from
            self.current_version = version_id

    def get_version_info(self) -> dict:
        """获取当前版本信息"""
        if not self.current_version:
            return None

        v = self.versions[self.current_version]
        return {
            "version": v["version_id"],
            "doc_count": v["doc_count"],
            "valid_from": v["valid_from"].isoformat(),
            "age_days": (datetime.now() - v["valid_from"]).days,
            "status": v["status"]
        }

    def check_expiry(self, valid_until: datetime) -> bool:
        """检查内容是否过期"""
        return datetime.now() > valid_until


# ================================================================
# 回答中添加时效性提示
# ================================================================

class TemporalAwareResponse:
    """
    带时效性提示的回答生成
    """

    TEMPORAL_WARNING = """
⚠️ 重要提示：
以上信息基于 {version} 版本（{date} 更新），距今已 {days} 天。
政策可能已有调整，建议您：

1. 登录 {official_website} 核实最新政策
2. 拨打官方咨询热线确认
3. 联系学校就业中心老师获取准确信息
"""

    def add_temporal_warning(
        self,
        answer: str,
        version_info: dict
    ) -> str:
        """为回答添加时效性警告"""

        # 检查是否超过警戒阈值（如 90 天）
        if version_info["age_days"] > 90:
            warning = self.TEMPORAL_WARNING.format(
                version=version_info["version"],
                date=version_info["valid_from"],
                days=version_info["age_days"],
                official_website="国家人社部官网"
            )
            return answer + "\n\n" + warning

        return answer


# ================================================================
# 实时数据通道（对于需要最新数据的查询）
# ================================================================

class RealTimeDataChannel:
    """
    实时数据通道：对于时效性要求高的查询，调用实时 API
    """

    # 需要实时数据的查询类型
    REALTIME_QUERIES = {
        "今天/本周/本月": ["招聘会", "宣讲会", "双选会"],
        "最新": ["补贴", "政策", "通知"],
        "当前": ["岗位", "职位", "招聘"]
    }

    def should_use_realtime(self, query: str) -> bool:
        """判断是否需要实时数据"""

        query_lower = query.lower()

        for time_keywords, topic_keywords in self.REALTIME_QUERIES.items():
            if any(k in query_lower for k in topic_keywords):
                if any(t in query_lower for t in time_keywords.split("/")):
                    return True

        return False

    async def fetch_realtime_data(self, query: str) -> dict:
        """获取实时数据"""

        # 调用招聘会/岗位实时 API
        if "招聘" in query:
            return await self._fetch_job_listings()
        elif "宣讲" in query:
            return await self._fetch_career_talks()

        return None
```

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

#### 第四重：动态置信度阈值

```python
# ================================================================
# 动态置信度阈值：根据查询类型调整
# ================================================================

from enum import Enum
from typing import Optional

class QueryRiskLevel(Enum):
    """查询风险等级"""
    HIGH = "high"      # 政策查询、流程指导
    MEDIUM = "medium"  # 通用咨询、FAQ
    LOW = "low"        # 闲聊、寒暄

class DynamicConfidenceThreshold:
    """
    动态置信度阈值策略
    
    面试要点：
    - 展示对业务场景的理解（不同查询风险不同）
    - 展示精细化调优能力（不是一刀切）
    """

    # 风险等级对应的阈值配置
    THRESHOLD_CONFIG = {
        QueryRiskLevel.HIGH: {
            "min_confidence": 0.80,    # 高风险查询，阈值更高
            "min_results": 3,          # 至少需要3个相关结果
            "require_citation": True,  # 必须有引用
            "description": "政策查询、流程指导等高风险场景"
        },
        QueryRiskLevel.MEDIUM: {
            "min_confidence": 0.65,
            "min_results": 2,
            "require_citation": True,
            "description": "通用咨询、常见问题"
        },
        QueryRiskLevel.LOW: {
            "min_confidence": 0.40,
            "min_results": 1,
            "require_citation": False,
            "description": "闲聊、寒暄、简单问候"
        }
    }

    # 查询类型识别规则
    QUERY_TYPE_RULES = {
        "high": [
            "落户", "补贴", "政策", "规定", "流程", "申请",
            "条件", "要求", "资格", "审批", "办理"
        ],
        "medium": [
            "如何", "怎么", "什么", "哪些", "能否", "是否",
            "区别", "比较", "选择"
        ],
        "low": [
            "你好", "谢谢", "再见", "辛苦", "帮忙",
            "在吗", "可以吗"
        ]
    }

    def classify_query(self, query: str) -> QueryRiskLevel:
        """分类查询风险等级"""
        
        query_lower = query.lower()
        
        # 检查高风险关键词
        for keyword in self.QUERY_TYPE_RULES["high"]:
            if keyword in query_lower:
                return QueryRiskLevel.HIGH
        
        # 检查低风险关键词
        for keyword in self.QUERY_TYPE_RULES["low"]:
            if keyword in query_lower:
                return QueryRiskLevel.LOW
        
        # 默认中等风险
        return QueryRiskLevel.MEDIUM

    def get_threshold(self, query: str) -> dict:
        """获取查询对应的阈值配置"""
        
        risk_level = self.classify_query(query)
        return self.THRESHOLD_CONFIG[risk_level]

    def should_accept_result(
        self,
        query: str,
        confidence: float,
        results_count: int,
        has_citation: bool
    ) -> tuple[bool, str]:
        """判断检索结果是否可接受"""
        
        config = self.get_threshold(query)
        
        reasons = []
        
        if confidence < config["min_confidence"]:
            reasons.append(
                f"置信度{confidence:.2f}低于阈值{config['min_confidence']}"
            )
        
        if results_count < config["min_results"]:
            reasons.append(
                f"检索结果数{results_count}低于最小要求{config['min_results']}"
            )
        
        if config["require_citation"] and not has_citation:
            reasons.append("该类查询必须有引用来源")
        
        if reasons:
            return False, "; ".join(reasons)
        
        return True, None


# ================================================================
# 使用示例
# ================================================================

def process_query_with_dynamic_threshold(query: str, search_results: list):
    """使用动态置信度阈值处理查询"""
    
    threshold_checker = DynamicConfidenceThreshold()
    
    # 获取阈值配置
    config = threshold_checker.get_threshold(query)
    print(f"查询类型: {config['description']}")
    print(f"置信度阈值: {config['min_confidence']}")
    
    # 计算检索结果置信度
    avg_confidence = sum(r.score for r in search_results) / len(search_results)
    has_citation = any(r.metadata.get("doc_title") for r in search_results)
    
    # 判断是否可接受
    accepted, reason = threshold_checker.should_accept_result(
        query=query,
        confidence=avg_confidence,
        results_count=len(search_results),
        has_citation=has_citation
    )
    
    if not accepted:
        # 触发拒答机制
        return generate_refusal_response(query, reason)
    
    # 继续生成回答
    return generate_grounded_response(query, search_results)
```

#### 第五重：自我一致性检查

```python
# ================================================================
# 自我一致性检查：同一对话中同类问题回答应一致
# ================================================================

from dataclasses import dataclass
from datetime import datetime

@dataclass
class ConsistencyIssue:
    """一致性问题记录"""
    current_query: str
    previous_query: str
    current_answer: str
    previous_answer: str
    contradiction_type: str  # "fact" / "policy" / "process"
    severity: str  # "high" / "medium" / "low"

class SelfConsistencyChecker:
    """
    自我一致性检查器
    
    面试要点：
    - 展示对LLM"记忆不一致"问题的理解
    - 展示系统性思维（不只是单次回答质量，还要关注整体一致性）
    """
    
    # 同类问题的相似度阈值
    SIMILARITY_THRESHOLD = 0.75
    
    # 矛盾检测的关键维度
    CONTRADICTION_DIMENSIONS = [
        "政策条件",    # 如落户条件前后不一致
        "办理流程",    # 如申请步骤前后不一致
        "时间节点",    # 如截止日期前后不一致
        "金额数量",    # 如补贴金额前后不一致
        "材料清单",    # 如所需材料前后不一致
    ]

    def __init__(self, llm_client):
        self.llm = llm_client

    def find_similar_queries(
        self,
        current_query: str,
        history: list[dict],
        top_k: int = 3
    ) -> list[dict]:
        """从对话历史中找到相似的查询"""
        
        similar = []
        
        for msg in history:
            if msg["role"] != "user":
                continue
            
            # 计算查询相似度
            similarity = self._calculate_query_similarity(
                current_query,
                msg["content"]
            )
            
            if similarity >= self.SIMILARITY_THRESHOLD:
                similar.append({
                    "query": msg["content"],
                    "answer": self._find_answer_for_query(history, msg),
                    "similarity": similarity
                })
        
        return sorted(similar, key=lambda x: x["similarity"], reverse=True)[:top_k]

    def check_consistency(
        self,
        current_query: str,
        current_answer: str,
        history: list[dict]
    ) -> tuple[bool, list[ConsistencyIssue]]:
        """检查当前回答与历史回答的一致性"""
        
        similar_queries = self.find_similar_queries(current_query, history)
        
        if not similar_queries:
            return True, []
        
        issues = []
        
        for sq in similar_queries:
            # 使用LLM判断两个回答是否存在矛盾
            contradiction = self._detect_contradiction(
                current_answer,
                sq["answer"],
                current_query
            )
            
            if contradiction:
                issues.append(ConsistencyIssue(
                    current_query=current_query,
                    previous_query=sq["query"],
                    current_answer=current_answer,
                    previous_answer=sq["answer"],
                    contradiction_type=contradiction["type"],
                    severity=contradiction["severity"]
                ))
        
        return len(issues) == 0, issues

    def _detect_contradiction(
        self,
        answer1: str,
        answer2: str,
        context_query: str
    ) -> Optional[dict]:
        """使用LLM检测两个回答是否存在矛盾"""
        
        prompt = f"""
你是事实一致性检查专家。请判断以下两个回答是否存在矛盾。

用户问题背景：{context_query}

回答A（历史回答）：
{answer1}

回答B（当前回答）：
{answer2}

请检查以下维度是否存在矛盾：
1. 政策条件
2. 办理流程
3. 时间节点
4. 金额数量
5. 材料清单

如果存在矛盾，请输出：
- 矛盾维度：xxx
- 矛盾描述：xxx
- 严重程度：high/medium/low

如果不存在矛盾，输出：无矛盾
"""
        
        response = self.llm.chat(prompt)
        
        if "无矛盾" in response:
            return None
        
        # 解析矛盾信息
        return self._parse_contradiction(response)

    def _calculate_query_similarity(self, q1: str, q2: str) -> float:
        """计算两个查询的语义相似度"""
        
        # 简化实现：关键词重叠度
        # 实际项目中应使用向量相似度
        
        keywords1 = set(self._extract_keywords(q1))
        keywords2 = set(self._extract_keywords(q2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1 & keywords2
        union = keywords1 | keywords2
        
        return len(intersection) / len(union)

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        
        # 简化实现
        # 实际项目中应使用NLP工具
        
        keywords = []
        important_words = [
            "落户", "补贴", "政策", "流程", "申请", "条件",
            "材料", "时间", "金额", "资格", "办理", "审批"
        ]
        
        for word in important_words:
            if word in text:
                keywords.append(word)
        
        return keywords


# ================================================================
# 一致性问题处理策略
# ================================================================

class ConsistencyHandler:
    """一致性问题处理器"""
    
    def handle_inconsistency(
        self,
        issues: list[ConsistencyIssue],
        current_answer: str
    ) -> str:
        """处理一致性问题"""
        
        if not issues:
            return current_answer
        
        # 高严重度问题：需要重新生成回答
        high_severity = [i for i in issues if i.severity == "high"]
        
        if high_severity:
            # 添加一致性警告
            warning = self._generate_consistency_warning(high_severity)
            return f"{current_answer}\n\n{warning}"
        
        # 中低严重度：添加提示但不阻断
        return current_answer

    def _generate_consistency_warning(
        self,
        issues: list[ConsistencyIssue]
    ) -> str:
        """生成一致性警告"""
        
        warnings = []
        for issue in issues:
            warnings.append(f"""
⚠️ 注意：本次回答与之前的回答在"{issue.contradiction_type}"方面可能存在差异。
- 之前回答：{issue.previous_answer[:100]}...
- 当前回答：{issue.current_answer[:100]}...

建议您核实最新政策，或联系就业中心老师确认准确信息。
""")
        
        return "\n".join(warnings)
```

#### 第六重：具体事实核验

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

#### 五重防护机制整合

```python
# ================================================================
# 五重防护机制整合使用
# ================================================================

class HallucinationDefenseSystem:
    """
    幻觉防御系统：整合五重防护机制
    
    面试要点：
    - 展示系统性架构能力
    - 展示对LLM幻觉问题的深度理解
    """
    
    def __init__(self, llm_client, config: dict = None):
        self.llm = llm_client
        
        # 初始化各防护层
        self.confidence_filter = ConfidenceFilter()
        self.dynamic_threshold = DynamicConfidenceThreshold()
        self.grounded_generator = GroundedGeneration()
        self.refusal_generator = RefusalGenerator()
        self.consistency_checker = SelfConsistencyChecker(llm_client)
        self.fact_verifier = FactVerificationPostProcessor()
        self.fact_handler = FactIssueHandler()
        
        self.config = config or {}

    async def process_query(
        self,
        query: str,
        search_results: list,
        history: list[dict]
    ) -> dict:
        """
        五重防护处理流程
        
        流程：
        1. 动态置信度阈值判断
        2. 置信度过滤
        3. 引用强制生成
        4. 自我一致性检查
        5. 具体事实核验
        """
        
        result = {
            "query": query,
            "accepted": True,
            "response": None,
            "refusal_reason": None,
            "consistency_issues": [],
            "fact_issues": [],
            "confidence": None,
            "citations": []
        }
        
        # 第一重：动态置信度阈值
        threshold_config = self.dynamic_threshold.get_threshold(query)
        avg_confidence = sum(r.score for r in search_results) / len(search_results) if search_results else 0
        
        accepted, reason = self.dynamic_threshold.should_accept_result(
            query=query,
            confidence=avg_confidence,
            results_count=len(search_results),
            has_citation=True
        )
        
        if not accepted:
            result["accepted"] = False
            result["refusal_reason"] = reason
            result["response"] = self.refusal_generator.generate(query, reason)
            return result
        
        # 第二重：置信度过滤
        try:
            filtered_results = self.confidence_filter.filter(
                search_results,
                min_score=threshold_config["min_confidence"]
            )
        except LowConfidenceError as e:
            result["accepted"] = False
            result["refusal_reason"] = str(e)
            result["response"] = self.refusal_generator.generate(query, str(e))
            return result
        
        # 第三重：引用强制生成
        response = self.grounded_generator.generate(query, filtered_results)
        result["citations"] = self._extract_citations(filtered_results)
        
        # 第四重：自我一致性检查
        is_consistent, consistency_issues = self.consistency_checker.check_consistency(
            query, response, history
        )
        
        if not is_consistent:
            result["consistency_issues"] = consistency_issues
            response = ConsistencyHandler().handle_inconsistency(
                consistency_issues, response
            )
        
        # 第五重：具体事实核验
        fact_issues = self.fact_verifier.verify(response, {"query": query})
        
        if fact_issues:
            result["fact_issues"] = fact_issues
            response = self.fact_handler.handle_issues(response, fact_issues)
        
        result["response"] = response
        result["confidence"] = avg_confidence
        
        return result

    def _extract_citations(self, results: list) -> list[dict]:
        """提取引用信息"""
        
        citations = []
        for i, r in enumerate(results, 1):
            citations.append({
                "ref_id": f"[{i}]",
                "doc_title": r.metadata.get("doc_title", "未知来源"),
                "text": r.text[:200],
                "score": r.score
            })
        
        return citations
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
# 语义感知的文档切分（Semantic Chunking）
# ================================================================

from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from typing import List
import numpy as np

class SemanticAwareChunker:
    """
    语义感知的文档切分器
    
    核心思想：
    - 不使用固定的chunk_size切分
    - 不单纯依赖句子边界切分
    - 计算句子之间的语义相似度
    - 在语义"断点"处进行切分
    
    面试要点：
    - 展示对传统切分方式局限性的理解
    - 展示对语义完整性的重视
    - 展示对Embedding模型的深度应用
    """
    
    def __init__(
        self,
        embed_model,
        similarity_threshold: float = 0.7,
        min_chunk_size: int = 100,
        max_chunk_size: int = 500
    ):
        """
        Args:
            embed_model: Embedding模型
            similarity_threshold: 语义相似度阈值，低于此值则切分
            min_chunk_size: 最小chunk大小（字符数）
            max_chunk_size: 最大chunk大小（字符数）
        """
        self.embed_model = embed_model
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk_document(self, document: str) -> List[str]:
        """
        语义感知切分
        
        流程：
        1. 先按句子切分（保持句子完整性）
        2. 计算相邻句子的语义相似度
        3. 在相似度"断点"处合并/切分
        4. 确保每个chunk语义完整
        """
        
        # 1. 按句子切分
        sentences = self._split_into_sentences(document)
        
        if len(sentences) <= 1:
            return [document]
        
        # 2. 计算句子Embedding
        sentence_embeddings = self._get_embeddings(sentences)
        
        # 3. 计算相邻句子相似度
        similarities = self._calculate_adjacent_similarity(sentence_embeddings)
        
        # 4. 找到语义断点
        breakpoints = self._find_semantic_breakpoints(similarities)
        
        # 5. 根据断点生成chunks
        chunks = self._create_chunks(sentences, breakpoints)
        
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """按句子切分"""
        
        # 中文句子分隔符
        separators = ["。", "！", "？", "；", "\n"]
        
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            if char in separators:
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # 处理最后未结束的句子
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences

    def _get_embeddings(self, sentences: List[str]) -> np.ndarray:
        """计算句子Embedding"""
        
        embeddings = []
        
        for sentence in sentences:
            emb = self.embed_model.get_text_embedding(sentence)
            embeddings.append(emb)
        
        return np.array(embeddings)

    def _calculate_adjacent_similarity(self, embeddings: np.ndarray) -> List[float]:
        """计算相邻句子相似度"""
        
        similarities = []
        
        for i in range(len(embeddings) - 1):
            # Cosine相似度
            sim = self._cosine_similarity(embeddings[i], embeddings[i + 1])
            similarities.append(sim)
        
        return similarities

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算Cosine相似度"""
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot_product / (norm1 * norm2 + 1e-8)

    def _find_semantic_breakpoints(self, similarities: List[float]) -> List[int]:
        """
        找到语义断点
        
        断点定义：相邻句子相似度低于阈值的位置
        """
        
        breakpoints = []
        
        for i, sim in enumerate(similarities):
            if sim < self.similarity_threshold:
                # 相似度低，说明语义发生变化，此处是断点
                breakpoints.append(i + 1)  # 断点位置（句子索引）
        
        return breakpoints

    def _create_chunks(
        self,
        sentences: List[str],
        breakpoints: List[int]
    ) -> List[str]:
        """根据断点创建chunks"""
        
        chunks = []
        
        # 添加首尾边界
        boundaries = [0] + breakpoints + [len(sentences)]
        
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            
            # 合并句子
            chunk_sentences = sentences[start:end]
            chunk_text = "".join(chunk_sentences)
            
            # 检查chunk大小
            if len(chunk_text) < self.min_chunk_size:
                # 太小：尝试合并到下一个chunk
                continue
            elif len(chunk_text) > self.max_chunk_size:
                # 太大：需要进一步切分
                sub_chunks = self._split_large_chunk(chunk_text)
                chunks.extend(sub_chunks)
            else:
                chunks.append(chunk_text)
        
        return chunks

    def _split_large_chunk(self, text: str) -> List[str]:
        """切分过大的chunk"""
        
        # 按最大大小切分，但保持句子完整性
        chunks = []
        current_chunk = ""
        
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


# ================================================================
# 使用LlamaIndex内置的SemanticSplitterNodeParser
# ================================================================

from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.dashscope import DashScopeEmbedding

def create_semantic_chunker():
    """
    使用LlamaIndex内置的语义切分器
    
    面试要点：
    - LlamaIndex提供了SemanticSplitterNodeParser
    - 基于Embedding相似度自动切分
    - 比自研更稳定，推荐使用
    """
    
    # 使用通义千问Embedding
    embed_model = DashScopeEmbedding(
        model_name="text-embedding-v2",
        api_key="your-dashscope-api-key"
    )
    
    # 创建语义切分器
    semantic_splitter = SemanticSplitterNodeParser(
        embed_model=embed_model,
        breakpoint_percentile_threshold=95,  # 断点阈值（百分位）
        buffer_size=1,  # 缓冲区大小（句子数）
    )
    
    return semantic_splitter


# ================================================================
# 完整的语义切分流程示例
# ================================================================

async def process_document_with_semantic_chunking(document: Document):
    """使用语义切分处理文档"""
    
    # 1. 创建语义切分器
    semantic_splitter = create_semantic_chunker()
    
    # 2. 切分文档
    nodes = semantic_splitter.get_nodes_from_documents([document])
    
    # 3. 为每个节点添加元数据
    for i, node in enumerate(nodes):
        node.metadata = {
            "chunk_id": i,
            "doc_title": document.metadata.get("title"),
            "doc_source": document.metadata.get("source"),
            "valid_from": document.metadata.get("valid_from"),
            "valid_until": document.metadata.get("valid_until"),
            "chunk_type": "semantic",  # 标记为语义切分
            "sentence_count": len(node.text.split("。")),
        }
    
    # 4. 构建向量索引
    index = VectorStoreIndex(nodes)
    
    return index, nodes
```

#### 句子级别引用追踪

```python
# ================================================================
# 句子级别引用追踪
# ================================================================

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SentenceCitation:
    """句子级别引用"""
    sentence: str           # 回答中的句子
    sentence_index: int     # 句子在回答中的位置
    source_chunk_id: str    # 来源chunk ID
    source_text: str        # 来源chunk原文
    source_sentence: str    # 来源中的具体句子（如果可定位）
    confidence: float       # 引用置信度
    support_type: str       # 支持类型：direct/indirect/none


class SentenceLevelCitationTracker:
    """
    句子级别引用追踪器
    
    面试要点：
    - 展示对引用精度的追求
    - 展示对LLM归因准确性的把控
    """
    
    def __init__(self, llm_client, embed_model):
        self.llm = llm_client
        self.embed_model = embed_model

    def track_citations(
        self,
        response: str,
        source_chunks: List[dict]
    ) -> List[SentenceCitation]:
        """
        追踪回答中每个句子的引用
        
        流程：
        1. 将回答切分为句子
        2. 对每个句子，找到最相关的来源chunk
        3. 验证引用是否真的支持该句子
        4. 返回带置信度的引用列表
        """
        
        # 1. 切分回答为句子
        response_sentences = self._split_into_sentences(response)
        
        # 2. 为每个句子追踪引用
        citations = []
        
        for i, sentence in enumerate(response_sentences):
            # 找到最相关的来源
            best_match = self._find_best_source(sentence, source_chunks)
            
            # 验证引用支持度
            support_info = self._verify_support(sentence, best_match)
            
            citation = SentenceCitation(
                sentence=sentence,
                sentence_index=i,
                source_chunk_id=best_match["chunk_id"],
                source_text=best_match["text"],
                source_sentence=best_match.get("matched_sentence", ""),
                confidence=support_info["confidence"],
                support_type=support_info["type"]
            )
            
            citations.append(citation)
        
        return citations

    def _find_best_source(
        self,
        sentence: str,
        source_chunks: List[dict]
    ) -> dict:
        """找到最相关的来源chunk"""
        
        # 计算句子与各chunk的相似度
        sentence_embedding = self.embed_model.get_text_embedding(sentence)
        
        best_match = None
        best_similarity = -1
        
        for chunk in source_chunks:
            chunk_embedding = self.embed_model.get_text_embedding(chunk["text"])
            
            similarity = self._cosine_similarity(sentence_embedding, chunk_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "similarity": similarity
                }
        
        # 尝试定位到chunk中的具体句子
        if best_match:
            best_match["matched_sentence"] = self._locate_source_sentence(
                sentence,
                best_match["text"]
            )
        
        return best_match

    def _locate_source_sentence(
        self,
        query_sentence: str,
        source_text: str
    ) -> str:
        """定位来源中的具体句子"""
        
        source_sentences = self._split_into_sentences(source_text)
        
        query_embedding = self.embed_model.get_text_embedding(query_sentence)
        
        best_sentence = ""
        best_similarity = -1
        
        for s in source_sentences:
            s_embedding = self.embed_model.get_text_embedding(s)
            similarity = self._cosine_similarity(query_embedding, s_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_sentence = s
        
        return best_sentence

    def _verify_support(
        self,
        sentence: str,
        source: dict
    ) -> dict:
        """
        验证来源是否真的支持该句子
        
        使用LLM判断：
        - direct: 来源直接支持该句子
        - indirect: 来源间接相关
        - none: 来源不支持该句子
        """
        
        if not source:
            return {"confidence": 0, "type": "none"}
        
        prompt = f"""
判断以下来源文本是否支持目标句子。

目标句子：{sentence}

来源文本：{source["text"]}

请判断支持类型：
- direct: 来源直接包含目标句子的信息，可以直接推导出目标句子
- indirect: 来源与目标句子相关，但不能直接推导
- none: 来源与目标句子无关

只输出一个类型：direct/indirect/none
"""
        
        response = self.llm.chat(prompt)
        
        support_type = response.strip().lower()
        
        if support_type == "direct":
            confidence = 0.9
        elif support_type == "indirect":
            confidence = 0.6
        else:
            confidence = 0.2
        
        return {"confidence": confidence, "type": support_type}

    def _cosine_similarity(self, vec1, vec2) -> float:
        """计算Cosine相似度"""
        
        import numpy as np
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        return dot_product / (norm1 * norm2 + 1e-8)

    def _split_into_sentences(self, text: str) -> List[str]:
        """切分为句子"""
        
        separators = ["。", "！", "？", "；", "\n"]
        
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in separators:
                if current.strip():
                    sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        return sentences


# ================================================================
# 引用质量评估
# ================================================================

class CitationQualityEvaluator:
    """引用质量评估器"""
    
    def evaluate(
        self,
        citations: List[SentenceCitation]
    ) -> dict:
        """评估引用整体质量"""
        
        total = len(citations)
        
        if total == 0:
            return {"score": 0, "issues": ["无引用"]}
        
        # 统计各类型引用数量
        direct_count = sum(1 for c in citations if c.support_type == "direct")
        indirect_count = sum(1 for c in citations if c.support_type == "indirect")
        none_count = sum(1 for c in citations if c.support_type == "none")
        
        # 计算平均置信度
        avg_confidence = sum(c.confidence for c in citations) / total
        
        # 计算质量分数
        quality_score = (
            direct_count * 1.0 +
            indirect_count * 0.5 +
            none_count * 0.0
        ) / total
        
        # 识别问题
        issues = []
        
        if none_count > 0:
            issues.append(f"{none_count}个句子无有效引用")
        
        if avg_confidence < 0.5:
            issues.append(f"平均引用置信度过低({avg_confidence:.2f})")
        
        return {
            "score": quality_score,
            "avg_confidence": avg_confidence,
            "direct_count": direct_count,
            "indirect_count": indirect_count,
            "none_count": none_count,
            "issues": issues
        }
```

### 3.6 时效性问题增强方案（健康监控 + 时效性感知检索）

#### 知识库健康度监控

```python
# ================================================================
# 知识库健康度监控系统
# ================================================================

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio

@dataclass
class HealthAlert:
    """健康度告警"""
    alert_type: str       # warning / critical
    document_id: int
    document_title: str
    issue_description: str
    days_until_expiry: Optional[int]
    created_at: datetime

class KnowledgeBaseHealthMonitor:
    """
    知识库健康度监控器
    
    面试要点：
    - 展示可观测性思维
    - 展示对知识库质量的持续关注
    - 展示主动运维能力
    """
    
    # 健康度评估配置
    HEALTH_CONFIG = {
        "warning_days": 30,      # 30天内过期 → warning
        "critical_days": 0,      # 已过期 → critical
        "freshness_half_life": 180,  # 新鲜度半衰期（天）
        "min_health_score": 60,  # 最低健康度阈值
    }

    def __init__(self, db_session, notification_service):
        self.db = db_session
        self.notification = notification_service

    async def run_daily_health_check(self) -> dict:
        """
        每日健康检查
        
        自动化任务，每日凌晨执行
        """
        
        today = datetime.now()
        
        # 1. 检查即将过期的文档
        warning_docs = await self._check_upcoming_expiry(today)
        
        # 2. 检查已过期文档
        expired_docs = await self._check_expired_docs(today)
        
        # 3. 计算整体健康度
        health_score = await self._calculate_health_score(today)
        
        # 4. 生成报告
        report = {
            "check_date": today.strftime("%Y-%m-%d"),
            "health_score": health_score,
            "warning_count": len(warning_docs),
            "expired_count": len(expired_docs),
            "warning_docs": warning_docs,
            "expired_docs": expired_docs,
            "recommendations": self._generate_recommendations(
                warning_docs, expired_docs, health_score
            )
        }
        
        # 5. 发送告警
        await self._send_alerts(warning_docs, expired_docs)
        
        # 6. 记录健康度日志
        await self._log_health_report(report)
        
        return report

    async def _check_upcoming_expiry(self, today: datetime) -> List[dict]:
        """检查即将过期的文档"""
        
        warning_date = today + timedelta(days=self.HEALTH_CONFIG["warning_days"])
        
        # 查询即将过期的文档
        query = """
            SELECT id, title, valid_until, category, source
            FROM kb_document
            WHERE valid_until BETWEEN :today AND :warning_date
            AND is_current = 1
            AND status = 1
            ORDER BY valid_until ASC
        """
        
        results = await self.db.execute(query, {
            "today": today,
            "warning_date": warning_date
        })
        
        warning_docs = []
        for row in results:
            days_until_expiry = (row.valid_until - today).days
            warning_docs.append({
                "id": row.id,
                "title": row.title,
                "valid_until": row.valid_until.strftime("%Y-%m-%d"),
                "days_until_expiry": days_until_expiry,
                "category": row.category,
                "source": row.source
            })
        
        return warning_docs

    async def _check_expired_docs(self, today: datetime) -> List[dict]:
        """检查已过期文档"""
        
        query = """
            SELECT id, title, valid_until, category, source
            FROM kb_document
            WHERE valid_until < :today
            AND is_current = 1
            AND status = 1
            ORDER BY valid_until DESC
        """
        
        results = await self.db.execute(query, {"today": today})
        
        expired_docs = []
        for row in results:
            expired_docs.append({
                "id": row.id,
                "title": row.title,
                "valid_until": row.valid_until.strftime("%Y-%m-%d"),
                "days_expired": (today - row.valid_until).days,
                "category": row.category,
                "source": row.source
            })
        
        return expired_docs

    async def _calculate_health_score(self, today: datetime) -> float:
        """
        计算知识库整体健康度
        
        健康度 = Σ(文档新鲜度 × 文档权重) / 文档总数
        
        新鲜度 = exp(-0.693 × 天数 / 半衰期)
        """
        
        query = """
            SELECT id, valid_from, valid_until, category
            FROM kb_document
            WHERE is_current = 1
            AND status = 1
        """
        
        results = await self.db.execute(query)
        
        if not results:
            return 100.0
        
        total_score = 0
        total_weight = 0
        
        # 文档权重配置（政策类权重更高）
        category_weights = {
            "policy": 2.0,
            "process": 1.5,
            "regulation": 2.0,
            "faq": 1.0,
        }
        
        for row in results:
            # 计算新鲜度
            days_since_valid = (today - row.valid_from).days if row.valid_from else 365
            half_life = self.HEALTH_CONFIG["freshness_half_life"]
            freshness = math.exp(-0.693 * days_since_valid / half_life)
            
            # 过期惩罚
            if row.valid_until and row.valid_until < today:
                freshness *= 0.1  # 过期文档大幅降权
            
            # 文档权重
            weight = category_weights.get(row.category, 1.0)
            
            total_score += freshness * weight
            total_weight += weight
        
        health_score = (total_score / total_weight) * 100
        
        return round(health_score, 2)

    def _generate_recommendations(
        self,
        warning_docs: List[dict],
        expired_docs: List[dict],
        health_score: float
    ) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        
        if expired_docs:
            recommendations.append(
                f"紧急：{len(expired_docs)}个文档已过期，请立即更新或标记为历史版本"
            )
        
        if warning_docs:
            recommendations.append(
                f"预警：{len(warning_docs)}个文档将在30天内过期，请提前准备更新"
            )
        
        if health_score < self.HEALTH_CONFIG["min_health_score"]:
            recommendations.append(
                f"健康度过低({health_score})，建议批量更新知识库内容"
            )
        
        if not recommendations:
            recommendations.append("知识库状态良好，继续保持定期更新")
        
        return recommendations

    async def _send_alerts(
        self,
        warning_docs: List[dict],
        expired_docs: List[dict]
    ):
        """发送告警通知"""
        
        # 发送过期告警（critical）
        for doc in expired_docs:
            await self.notification.send_alert(
                level="critical",
                title=f"文档已过期：{doc['title']}",
                content=f"""
文档《{doc['title']}》已于{doc['valid_until']}过期，已过期{doc['days_expired']}天。

文档信息：
- 分类：{doc['category']}
- 来源：{doc['source']}

建议操作：
1. 获取最新版本文档并上传
2. 或将当前文档标记为"历史版本"
3. 更新相关引用的时效性标记
""",
                recipients=["admin", "knowledge_manager"]
            )
        
        # 发送预警（warning）
        for doc in warning_docs:
            await self.notification.send_alert(
                level="warning",
                title=f"文档即将过期：{doc['title']}",
                content=f"""
文档《{doc['title']}》将在{doc['days_until_expiry']}天后过期。

过期日期：{doc['valid_until']}
分类：{doc['category']}
来源：{doc['source']}

建议提前准备更新。
""",
                recipients=["admin", "knowledge_manager"]
            )

    async def _log_health_report(self, report: dict):
        """记录健康度日志"""
        
        await self.db.execute("""
            INSERT INTO kb_health_log (
                check_date, total_docs, current_docs,
                warning_docs, expired_docs, avg_freshness, health_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            report["check_date"],
            report.get("total_docs", 0),
            report.get("current_docs", 0),
            report["warning_count"],
            report["expired_count"],
            report.get("avg_freshness", 0),
            report["health_score"]
        ])


# ================================================================
# 定时任务配置
# ================================================================

async def setup_health_monitoring():
    """配置健康度监控定时任务"""
    
    monitor = KnowledgeBaseHealthMonitor(db, notification)
    
    # 每日凌晨2点执行健康检查
    scheduler.add_job(
        monitor.run_daily_health_check,
        trigger="cron",
        hour=2,
        minute=0,
        id="kb_health_check",
        replace_existing=True
    )
    
    # 每周一上午9点发送健康度周报
    scheduler.add_job(
        monitor.send_weekly_report,
        trigger="cron",
        day_of_week="mon",
        hour=9,
        minute=0,
        id="kb_weekly_report",
        replace_existing=True
    )
```

#### 时效性感知的检索

```python
# ================================================================
# 时效性感知的检索器
# ================================================================

import math
from datetime import datetime, timedelta
from typing import List, Optional

@dataclass
class TemporalSearchResult:
    """带时效性信息的检索结果"""
    chunk_id: str
    text: str
    score: float              # 原始相似度得分
    temporal_score: float     # 时效性得分
    combined_score: float     # 综合得分
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    days_until_expiry: Optional[int]
    is_expired: bool
    freshness_level: str      # fresh / aging / expired

class TemporalAwareRetriever:
    """
    时效性感知的检索器
    
    核心思想：
    - 检索时考虑文档的时效性
    - 新文档权重更高
    - 过期文档降低权重或排除
    
    面试要点：
    - 展示对知识时效性的重视
    - 展示算法优化能力（不只是相似度，还要考虑时间维度）
    """
    
    # 时效性权重配置
    TEMPORAL_CONFIG = {
        # 时间衰减配置
        "half_life_days": 180,       # 180天后权重减半
        "grace_period_days": 30,     # 过期30天内仍可用但降权
        
        # 权重配置
        "similarity_weight": 0.7,    # 相似度权重
        "temporal_weight": 0.3,      # 时效性权重
        
        # 分类特定配置
        "policy_decay_factor": 0.5,  # 政策类文档衰减更快
        "faq_decay_factor": 0.8,     # FAQ类文档衰减较慢
        
        # 过期处理策略
        "expired_penalty": 0.1,      # 过期文档惩罚系数
        "exclude_expired": False,    # 是否完全排除过期文档
    }

    def __init__(self, base_retriever, config: dict = None):
        self.base_retriever = base_retriever
        self.config = config or self.TEMPORAL_CONFIG

    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        exclude_expired: bool = None
    ) -> List[TemporalSearchResult]:
        """
        时效性感知检索
        
        流程：
        1. 基础检索（获取候选集）
        2. 计算时效性得分
        3. 计算综合得分
        4. 过滤/降权过期内容
        5. 返回排序后的结果
        """
        
        # 1. 基础检索（多取一些候选）
        base_results = await self.base_retriever.retrieve(
            query,
            top_k=top_k * 2
        )
        
        # 2. 计算时效性得分
        temporal_results = []
        today = datetime.now()
        
        for result in base_results:
            temporal_score = self._calculate_temporal_score(
                result.metadata,
                today
            )
            
            combined_score = (
                result.score * self.config["similarity_weight"] +
                temporal_score * self.config["temporal_weight"]
            )
            
            # 判断过期状态
            valid_until = result.metadata.get("valid_until")
            is_expired = valid_until and valid_until < today
            
            days_until_expiry = None
            if valid_until:
                days_until_expiry = (valid_until - today).days
            
            # 判断新鲜度级别
            freshness_level = self._classify_freshness(
                days_until_expiry,
                is_expired
            )
            
            temporal_results.append(TemporalSearchResult(
                chunk_id=result.chunk_id,
                text=result.text,
                score=result.score,
                temporal_score=temporal_score,
                combined_score=combined_score,
                valid_from=result.metadata.get("valid_from"),
                valid_until=valid_until,
                days_until_expiry=days_until_expiry,
                is_expired=is_expired,
                freshness_level=freshness_level
            ))
        
        # 3. 过滤过期文档（可选）
        if exclude_expired or self.config["exclude_expired"]:
            temporal_results = [
                r for r in temporal_results if not r.is_expired
            ]
        else:
            # 过期文档降权
            for r in temporal_results:
                if r.is_expired:
                    r.combined_score *= self.config["expired_penalty"]
        
        # 4. 按综合得分排序
        temporal_results.sort(
            key=lambda x: x.combined_score,
            reverse=True
        )
        
        return temporal_results[:top_k]

    def _calculate_temporal_score(
        self,
        metadata: dict,
        today: datetime
    ) -> float:
        """
        计算时效性得分
        
        新鲜度 = exp(-0.693 × 天数 / 半衰期)
        
        考虑因素：
        1. 文档生效时间（越新越好）
        2. 文档过期时间（即将过期降权）
        3. 文档分类（政策类衰减更快）
        """
        
        valid_from = metadata.get("valid_from")
        valid_until = metadata.get("valid_until")
        category = metadata.get("category", "faq")
        
        # 计算新鲜度
        if valid_from:
            days_since_valid = (today - valid_from).days
        else:
            days_since_valid = 0  # 不知道时间，默认新鲜
        
        half_life = self.config["half_life_days"]
        
        # 分类特定衰减
        decay_factor = self.config.get(
            f"{category}_decay_factor",
            1.0
        )
        
        adjusted_half_life = half_life * decay_factor
        
        freshness = math.exp(-0.693 * days_since_valid / adjusted_half_life)
        
        # 过期惩罚
        if valid_until and valid_until < today:
            # 已过期
            days_expired = (today - valid_until).days
            
            # 过期越久，惩罚越重
            if days_expired <= self.config["grace_period_days"]:
                # 宽限期：轻微惩罚
                freshness *= 0.5
            else:
                # 超过宽限期：大幅惩罚
                freshness *= self.config["expired_penalty"]
        
        elif valid_until:
            # 未过期但即将过期
            days_until_expiry = (valid_until - today).days
            
            if days_until_expiry <= self.config["grace_period_days"]:
                # 即将过期：轻微降权
                freshness *= 0.8
        
        return freshness

    def _classify_freshness(
        self,
        days_until_expiry: Optional[int],
        is_expired: bool
    ) -> str:
        """分类新鲜度级别"""
        
        if is_expired:
            return "expired"
        
        if days_until_expiry is None:
            return "unknown"
        
        if days_until_expiry > 90:
            return "fresh"
        elif days_until_expiry > 30:
            return "aging"
        else:
            return "expiring_soon"


# ================================================================
# 时效性提示生成
# ================================================================

class TemporalHintGenerator:
    """时效性提示生成器"""
    
    def generate_hint(
        self,
        results: List[TemporalSearchResult],
        query: str
    ) -> str:
        """为回答生成时效性提示"""
        
        # 检查是否有过期或即将过期的内容
        expired = [r for r in results if r.is_expired]
        expiring_soon = [r for r in results if r.freshness_level == "expiring_soon"]
        
        if not expired and not expiring_soon:
            return ""
        
        hints = []
        
        if expired:
            hints.append(f"""
⚠️ 重要提示：以下信息包含已过期的内容

本次回答参考了以下已过期的文档：
{self._format_expired_docs(expired)}

这些政策可能已有更新，请务必：
1. 登录相关政府部门官网核实最新政策
2. 拨打官方咨询热线确认
3. 联系学校就业中心老师获取准确信息
""")
        
        if expiring_soon:
            hints.append(f"""
⏰ 时效性提醒：以下信息即将过期

本次回答参考了以下即将过期的文档（30天内）：
{self._format_expiring_docs(expiring_soon)}

建议您及时核实最新政策，避免信息滞后。
""")
        
        return "\n".join(hints)

    def _format_expired_docs(self, docs: List[TemporalSearchResult]) -> str:
        """格式化过期文档列表"""
        
        lines = []
        for doc in docs[:3]:  # 只显示前3个
            lines.append(f"- {doc.text[:50]}...（已过期）")
        
        return "\n".join(lines)

    def _format_expiring_docs(self, docs: List[TemporalSearchResult]) -> str:
        """格式化即将过期文档列表"""
        
        lines = []
        for doc in docs[:3]:
            days = doc.days_until_expiry or 0
            lines.append(f"- {doc.text[:50]}...（{days}天后过期）")
        
        return "\n".join(lines)
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
│          # 1. 判断下一步                                                 │
│          next_step = decide_next_step(user_input, history)              │
│                                                                          │
│          if next_step == "search":                                       │
│              result = search_tool(user_input)                           │
│          elif next_step == "ask_llm":                                    │
│              result = llm.generate(user_input, context)                 │
│          elif next_step == "end":                                        │
│              return final_answer                                         │
│                                                                          │
│          history.append(result)                                         │
│                                                                          │
│  问题：                                                                   │
│  ❌ 状态分散在全局变量                                                   │
│  ❌ 难以追踪执行链路                                                     │
│  ❌ 循环/分支逻辑复杂                                                   │
│  ❌ 无法暂停/恢复                                                       │
│  ❌ 调试困难                                                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         LangGraph 实现                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  from langgraph.graph import StateGraph, END                            │
│                                                                          │
│  # 1. 定义状态                                                          │
│  class AgentState(TypedDict):                                            │
│      messages: list[BaseMessage]                                        │
│      current_query: str                                                  │
│      tools_used: list[str]                                              │
│      confidence: float                                                   │
│      response: str                                                      │
│                                                                          │
│  # 2. 定义节点                                                          │
│  def router(state) -> str:                                              │
│      return "search" if needs_tool(state) else "respond"                │
│                                                                          │
│  def search_node(state) -> dict:                                         │
│      result = search_tool(state["current_query"])                        │
│      return {"messages": [result], "confidence": result.score}          │
│                                                                          │
│  def respond_node(state) -> dict:                                        │
│      return {"response": llm.generate(state)}                            │
│                                                                          │
│  # 3. 构建图                                                            │
│  graph = StateGraph(AgentState)                                          │
│  graph.add_node("router", router)                                        │
│  graph.add_node("search", search_node)                                   │
│  graph.add_node("respond", respond_node)                                 │
│  graph.add_edge("router", "search", label="needs_tool")                 │
│  graph.add_edge("router", "respond", label="direct")                    │
│  graph.add_edge("search", "respond")                                     │
│                                                                          │
│  # 4. 编译 + 执行                                                        │
│  app = graph.compile()                                                   │
│  result = app.invoke({"query": user_input})                             │
│                                                                          │
│  优势：                                                                   │
│  ✅ 状态显式管理                                                          │
│  ✅ 执行链路清晰                                                          │
│  ✅ 支持循环/分支/条件                                                    │
│  ✅ 支持 Checkpoint (暂停/恢复)                                          │
│  ✅ 内置可视化调试                                                        │
│  ✅ 易于扩展                                                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 LangGraph 工作流详解

```python
# ================================================================
# LangGraph Agent 完整实现
# ================================================================

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
import json

# ================================================================
# 1. Agent 状态定义
# ================================================================

class AgentState(TypedDict):
    """Agent 状态定义"""

    # 对话历史
    messages: Annotated[list, add_messages]

    # 当前用户查询
    current_query: str

    # 检索结果
    search_results: list[dict]

    # 引文信息
    citations: list[dict]

    # 置信度
    confidence: float

    # 已使用的工具
    tools_used: list[str]

    # 工具执行结果
    tool_outputs: dict

    # 最终回答
    response: str

    # 执行路由
    route: str

    # 是否应该拒答
    should_refuse: bool

    # 拒答原因
    refusal_reason: str

    # 版本信息（时效性）
    version_info: dict


# ================================================================
# 2. 节点定义
# ================================================================

class AgentNodes:
    """Agent 节点集合"""

    def __init__(self, llm, tools, retriever):
        self.llm = llm
        self.tools = tools
        self.retriever = retriever

    # -------------------- 路由节点 --------------------

    def route_query(self, state: AgentState) -> AgentState:
        """
        路由节点：判断查询类型，决定下一步

        返回路由结果：
        - "search": 需要检索
        - "tool_call": 需要调用工具
        - "direct": 直接回答
        - "refuse": 拒答
        """

        query = state["current_query"]
        messages = state["messages"]

        # 构建路由 Prompt
        router_prompt = f"""
你是查询路由专家。根据用户问题，决定下一步操作。

当前问题：{query}

选项：
1. search: 需要检索知识库才能回答
2. tool_call: 需要调用外部工具（如查档案、预约等）
3. direct: 可以直接从对话历史回答，不需要额外操作
4. refuse: 问题超出服务范围或无法回答

判断依据：
- 如果问题涉及政策、流程、规定 → search
- 如果问题涉及个人数据查询、预约、生成 → tool_call
- 如果是简单寒暄或跟进 → direct
- 如果涉及违法、政治敏感、无法核实的内容 → refuse

只输出一个选项：search/tool_call/direct/refuse
"""

        # 调用 LLM 路由
        response = self.llm.chat([{"role": "user", "content": router_prompt}])

        route = response.strip().lower()

        # 验证路由结果
        valid_routes = ["search", "tool_call", "direct", "refuse"]
        if route not in valid_routes:
            route = "search"  # 默认走检索

        return {"route": route}

    # -------------------- 检索节点 --------------------

    def search_knowledge(self, state: AgentState) -> AgentState:
        """
        检索节点：使用 LlamaIndex 检索知识库
        """

        query = state["current_query"]

        # 使用 LlamaIndex 检索
        search_result = self.retriever.query_with_citations(query)

        return {
            "search_results": search_result["results"],
            "citations": search_result["citations"],
            "confidence": search_result["confidence"]
        }

    # -------------------- 置信度检查节点 --------------------

    def check_confidence(self, state: AgentState) -> AgentState:
        """
        置信度检查：判断检索结果是否足够可靠
        """

        confidence = state["confidence"]
        search_results = state["search_results"]

        # 拒答条件
        should_refuse = False
        refusal_reason = None

        if not search_results:
            should_refuse = True
            refusal_reason = "知识库中没有相关内容"
        elif confidence < 0.5:
            should_refuse = True
            refusal_reason = "检索结果置信度过低"
        elif len(search_results) == 0:
            should_refuse = True
            refusal_reason = "未找到匹配的知识"

        return {
            "should_refuse": should_refuse,
            "refusal_reason": refusal_reason
        }

    # -------------------- 拒答节点 --------------------

    def generate_refusal(self, state: AgentState) -> AgentState:
        """
        拒答节点：生成友好的拒答内容
        """

        refusal_reason = state.get("refusal_reason", "无法回答此问题")

        refusal_response = f"""
抱歉，关于您的问题，我无法提供准确回答。

原因：{refusal_reason}

建议您：
1. 联系学校就业中心老师获取准确信息
2. 登录相关政府部门官网查询最新政策
3. 拨打官方咨询热线

如果您有其他就业相关问题，我很乐意帮助您。
"""

        return {"response": refusal_response}

    # -------------------- 工具调用节点 --------------------

    def execute_tool(self, state: AgentState) -> AgentState:
        """
        工具执行节点：调用相应的工具
        """

        # 解析需要调用的工具
        # 这里需要从 messages 中提取工具调用信息

        tool_outputs = {}
        for tool_name, tool_args in state.get("pending_tool_calls", []).items():
            tool_func = self.tools.get(tool_name)
            if tool_func:
                result = tool_func(**tool_args)
                tool_outputs[tool_name] = result

        return {"tool_outputs": tool_outputs}

    # -------------------- 生成回答节点 --------------------

    def generate_response(self, state: AgentState) -> AgentState:
        """
        生成回答节点：结合检索结果生成最终回答
        """

        query = state["current_query"]
        search_results = state["search_results"]
        citations = state["citations"]
        confidence = state["confidence"]
        tool_outputs = state.get("tool_outputs", {})

        # 构建生成 Prompt
        context = self._build_context(search_results, tool_outputs)

        generation_prompt = f"""
你是高校就业服务平台的 AI 助手。请基于以下参考资料回答问题。

参考资料：
{context}

回答要求：
1. 每说一个事实，必须在句尾标注来源 [来源: XXX]
2. 如果某些信息参考资料中没有，直接说"这个我不确定"
3. 不要编造政策编号、日期、数字
4. 如果参考资料较少，表达要更保守
5. 语气友好，给出具体建议

当前问题：{query}
"""

        response = self.llm.chat([
            {"role": "system", "content": generation_prompt}
        ])

        # 添加引用格式化
        formatted_response = self._format_with_citations(
            response,
            citations
        )

        return {"response": formatted_response}

    def _build_context(self, search_results: list, tool_outputs: dict) -> str:
        """构建上下文"""

        context_parts = []

        # 添加检索结果
        for i, result in enumerate(search_results[:5], 1):
            context_parts.append(
                f"[{i}] {result['content']}\n来源: {result.get('source', '未知')}"
            )

        #添加工具输出
        for tool_name, output in tool_outputs.items():
            context_parts.append(f"[工具: {tool_name}]\n{output}")

        return "\n\n".join(context_parts)

    def _format_with_citations(self, response: str, citations: list) -> str:
        """格式化带引用的回答"""
        # 添加引用列表
        if citations:
            citation_section = "\n\n---\n**参考来源：**\n"
            for i, cite in enumerate(citations, 1):
                citation_section += f"{i}. {cite['doc_title']} - {cite.get('page', 'N/A')}页\n"

            response += citation_section

        return response


# ================================================================
# 3. 边定义
# ================================================================

def should_search(state: AgentState) -> str:
    """条件边：是否需要检索"""

    route = state.get("route", "search")

    if route == "search":
        return "do_search"
    elif route == "tool_call":
        return "do_tool"
    elif route == "direct":
        return "do_direct"
    elif route == "refuse":
        return "do_refuse"

    return "do_search"


def should_retry(state: AgentState) -> str:
    """条件边：是否需要重试"""

    if state.get("should_refuse"):
        return "do_refuse"

    return "generate"


# ================================================================
# 4. 构建 StateGraph
# ================================================================

def build_agent_graph(llm, tools, retriever) -> StateGraph:
    """构建 Agent 图"""

    # 创建节点实例
    nodes = AgentNodes(llm, tools, retriever)

    # 创建图
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("route", nodes.route_query)
    graph.add_node("search", nodes.search_knowledge)
    graph.add_node("check_confidence", nodes.check_confidence)
    graph.add_node("execute_tool", nodes.execute_tool)
    graph.add_node("generate_response", nodes.generate_response)
    graph.add_node("generate_refusal", nodes.generate_refusal)

    # 添加边
    graph.add_edge(START, "route")

    # 路由边
    graph.add_conditional_edges(
        "route",
        should_search,
        {
            "do_search": "search",
            "do_tool": "execute_tool",
            "do_direct": "generate_response",
            "do_refuse": "generate_refusal"
        }
    )

    # 检索后的检查
    graph.add_edge("search", "check_confidence")

    # 置信度检查后的分支
    graph.add_conditional_edges(
        "check_confidence",
        should_retry,
        {
            "generate": "generate_response",
            "do_refuse": "generate_refusal"
        }
    )

    # 工具执行后生成回答
    graph.add_edge("execute_tool", "generate_response")

    # 结束
    graph.add_edge("generate_response", END)
    graph.add_edge("generate_refusal", END)

    return graph


# ================================================================
# 5. 编译和执行
# ================================================================

def compile_agent(llm, tools, retriever):
    """编译 Agent"""

    graph = build_agent_graph(llm, tools, retriever)

    # 添加 Checkpoint（支持暂停/恢复）
    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


# ================================================================
# 6. 执行示例
# ================================================================

async def run_agent(agent, user_query: str):
    """运行 Agent"""

    # 初始状态
    initial_state = {
        "messages": [],
        "current_query": user_query,
        "search_results": [],
        "citations": [],
        "confidence": 1.0,
        "tools_used": [],
        "tool_outputs": {},
        "response": "",
        "route": "",
        "should_refuse": False,
        "refusal_reason": "",
        "version_info": {}
    }

    # 执行
    result = await agent.ainvoke(initial_state)

    return result["response"]
```

### 4.3 Checkpoint 功能（对话暂停/恢复）

```python
# ================================================================
# Checkpoint 功能：支持对话暂停和恢复
# ================================================================

from langgraph.checkpoint.sqlite import SqliteSaver

# 使用 SQLite 作为持久化 Checkpoint
checkpoint_saver = SqliteSaver.from_conn_string(":memory:")

# 编译时添加 Checkpointer
agent = graph.compile(checkpointer=checkpoint_saver)


# ================================================================
# 对话恢复
# ================================================================

async def resume_conversation(agent, thread_id: str, new_input: str):
    """
    恢复历史对话继续执行

    thread_id: 对话线程 ID（用于区分不同用户/会话）
    new_input: 用户新的输入
    """

    config = {
        "configurable": {
            "thread_id": thread_id  # 关键：指定对话线程
        }
    }

    # 获取历史状态
    current_state = agent.get_state(config)

    # 更新状态继续执行
    updated_state = {
        **current_state.values,
        "current_query": new_input
    }

    # 继续执行
    result = await agent.ainvoke(updated_state, config)

    return result["response"]


# ================================================================
# 对话回溯
# ================================================================

async def get_conversation_history(agent, thread_id: str, limit: int = 10):
    """获取对话历史"""

    config = {"configurable": {"thread_id": thread_id}}

    # 获取所有历史状态
    history = []

    async for state in agent.astream(None, config, limit=limit):
        history.append(state)

    return history
```

---

## 五、LangSmith 监控方案

### 5.1 LangSmith 集成

```python
# ================================================================
# LangSmith 配置
# ================================================================

import os
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree
from langsmith.evaluation import evaluate

# 环境变量配置
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-api-key"
os.environ["LANGCHAIN_PROJECT"] = "aiqa-agent"  # 项目名称
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# ================================================================
# 追踪装饰器
# ================================================================

@traceable(
    name="llm.generate",
    tags=["llm", "generation"],
    metadata={"model": "qwen-max"}
)
def tracked_llm_generate(prompt: str, system_prompt: str = None) -> str:
    """
    带追踪的 LLM 生成
    LangSmith 会自动记录：
    - 输入 prompt
    - 输出 response
    - 执行时间
    - Token 消耗
    - 错误信息
    """
    response = llm.chat(prompt, system_prompt=system_prompt)
    return response


@traceable(
    name="retriever.search",
    tags=["retriever", "rag"],
    metadata={"retriever_type": "llamaindex"}
)
def tracked_search(query: str, top_k: int = 5) -> list[dict]:
    """
    带追踪的检索
    LangSmith 会记录：
    - 检索耗时
    - 返回结果数
    - 置信度分数
    """
    results = retriever.search(query, top_k=top_k)
    return results


@traceable(
    name="agent.route",
    tags=["agent", "routing"],
    metadata={"agent_version": "v2.0"}
)
def tracked_route(query: str, context: dict) -> str:
    """
    带追踪的路由决策
    """
    route = route_decision(query, context)
    return route


# ================================================================
# 自动追踪 LangGraph
# ================================================================

from langgraph.checkpoint.langchain import LangChainCheckpointSaver

# LangGraph 自动集成 LangSmith
# 只需要在编译时指定 LangSmith 相关环境变量
# 所有节点执行都会自动追踪

agent = graph.compile(
    checkpointer=LangChainCheckpointSaver(),  # 使用 LangChain 的 Checkpoint
    debug=True  # 开启调试模式，记录更多细节
)

# ================================================================
# 手动添加追踪事件
# ================================================================

from langsmith import trace

def agent_with_custom_tracing(user_query: str):
    """带自定义追踪的 Agent"""

    with trace("agent.full_pipeline", tags=["agent"]) as parent_run:
        # 添加自定义属性
        parent_run.log(
            {"user_query": user_query, "timestamp": datetime.now().isoformat()}
        )

        # 执行各阶段
        with trace("route_decision") as route_run:
            route = route_decision(user_query)
            route_run.log({"route": route})

        if route == "search":
            with trace("knowledge_retrieval") as search_run:
                results = retriever.search(user_query)
                search_run.log({
                    "result_count": len(results),
                    "avg_confidence": sum(r.score for r in results) / len(results)
                })

        with trace("response_generation") as gen_run:
            response = llm.generate(user_query)
            gen_run.log({"response_length": len(response)})

        return response
```

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
│  │  Status: ✅ Success                                                         │   │
│  │  Duration: 2.34s                                                           │   │
│  │                                                                              │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐     │   │
│  │  │  🟢 route_decision (0.12s)                                        │     │   │
│  │  │     Input: "毕业生落户需要准备什么材料"                              │     │   │
│  │  │     Output: "search"                                               │     │   │
│  │  └──────────────────────────────────────────────────────────────────┘     │   │
│  │                              ↓                                              │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐     │   │
│  │  │  🟢 knowledge_retrieval (0.45s)                                   │     │   │
│  │  │     Query: "毕业生落户 材料"                                        │     │   │
│  │  │     Results: 5 docs, Avg score: 0.82                              │     │   │
│  │  └──────────────────────────────────────────────────────────────────┘     │   │
│  │                              ↓                                              │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐     │   │
│  │  │  🟢 response_generation (1.77s)                                   │     │   │
│  │  │     Tokens: 342 in, 156 out                                       │     │   │
│  │  │     Model: qwen-max                                               │     │   │
│  │  └──────────────────────────────────────────────────────────────────┘     │   │
│  │                                                                              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  Prompt 版本管理                                                         │   │
│  │                                                                              │   │
│  │  版本    创建时间        使用次数    状态                                 │   │
│  │  v1.2    2024-01-15     3,421        ✅ 当前                            │   │
│  │  v1.1    2024-01-10     8,234        ❌ 已废弃                          │   │
│  │  v1.0    2024-01-05     1,192        ❌ 已废弃                          │   │
│  │                                                                              │   │
│  │  [+ 新建版本]  [📊 对比]  [📈 趋势分析]                                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 性能评估和回归测试

```python
# ================================================================
# 使用 LangSmith 进行自动化评估
# ================================================================

from langsmith.schemas import Example, Run
from langsmith.evaluation import evaluate, Comparison

# ================================================================
# 评估数据集
# ================================================================

EVAL_DATASET = [
    {
        "query": "应届毕业生落户上海需要准备哪些材料？",
        "expected_topics": ["落户", "材料", "上海"],
        "expected_response_type": "policy_answer"
    },
    {
        "query": "三方协议丢了怎么办？",
        "expected_topics": ["三方协议", "补办"],
        "expected_response_type": "process_guide"
    },
    {
        "query": "你好",
        "expected_topics": [],
        "expected_response_type": "greeting"
    },
    # ... 更多测试用例
]


# ================================================================
# 评估器定义
# ================================================================

def response_quality_evaluator(run: Run, example: Example) -> dict:
    """评估回答质量"""

    # 获取输入输出
    predicted = run.outputs.get("response", "")
    expected = example.outputs

    # 检查是否包含关键信息
    topics = expected.get("expected_topics", [])
    missing_topics = [t for t in topics if t not in predicted]

    # 检查是否有引用
    has_citation = "[来源:" in predicted or "来源:" in predicted

    return {
        "score": 1.0 if len(missing_topics) == 0 else 0.5,
        "reason": f"Missing topics: {missing_topics}" if missing_topics else "All topics covered",
        "metrics": {
            "has_citation": has_citation,
            "missing_topics_count": len(missing_topics),
            "response_length": len(predicted)
        }
    }


def citation_accuracy_evaluator(run: Run, example: Example) -> dict:
    """评估引用准确性"""

    citations = run.outputs.get("citations", [])

    # 检查引用是否有效
    valid_citations = sum(1 for c in citations if c.get("source"))

    return {
        "score": valid_citations / max(len(citations), 1),
        "metrics": {
            "total_citations": len(citations),
            "valid_citations": valid_citations
        }
    }


# ================================================================
# 执行评估
# ================================================================

# 注册评估器
evaluation = evaluate(
    my_agent,
    data=EVAL_DATASET,
    evaluators={
        "response_quality": response_quality_evaluator,
        "citation_accuracy": citation_accuracy_evaluator
    },
    experiment_prefix="aiqa-agent-v2"
)

# 输出结果
print(f"评估完成！")
print(f"平均回答质量: {evaluation.metrics['response_quality']:.2%}")
print(f"平均引用准确率: {evaluation.metrics['citation_accuracy']:.2%}")
```

---

## 六、LlamaIndex 检索优化

### 6.1 为什么需要 LlamaIndex？

```
当前简单检索 vs LlamaIndex 高级检索：

┌─────────────────────────────────────────────────────────────────────────┐
│                        当前实现（简单向量检索）                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  user_query → embedding → ChromaDB → top_k → response                  │
│                                                                          │
│  问题：                                                                   │
│  ❌ 只用语义相似度，忽略关键词匹配                                         │
│  ❌ 检索结果不一定是用户真正想要的                                         │
│  ❌ 无法处理复杂查询（如多义词、同义词）                                   │
│  ❌ 检索结果没有重排序                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        LlamaIndex（混合检索）                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  user_query                                                              │
│      │                                                                   │
│      ├─→ Query Rewriting (改写查询)                                      │
│      │      • HyDE: 生成假设性答案 → 检索                                 │
│      │      • 子问题: 拆分成多个子查询                                     │
│      │      • 同义词扩展: 扩展查询词                                       │
│      │                                                                   │
│      ↓                                                                   │
│      │                                                                   │
│      ├─→ Vector Search (语义) ──┐                                        │
│      │                          │                                        │
│      ├─→ BM25 (关键词) ────────┼──→ Fusion (RRF) → Rerank → response   │
│      │                          │                                        │
│      ├─→ Knowledge Graph ──────┘                                        │
│      │                                                                   │
│      ↓                                                                   │
│  Citation (引用追踪)                                                      │
│                                                                          │
│  优势：                                                                   │
│  ✅ 语义 + 关键词双重匹配                                                 │
│  ✅ 多种检索策略融合                                                      │
│  ✅ Rerank 提升相关性                                                     │
│  ✅ 内置引用追踪                                                          │
│  ✅ 支持复杂查询优化                                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 LlamaIndex 配置

```python
# ================================================================
# LlamaIndex 检索配置
# ================================================================

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Document
)
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser
)
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.postprocessor import SimilarityPostprocessor
from llama_index.core.retrievers import (
    VectorIndexRetriever,
    BM25Retriever,
    QueryFusionRetriever
)
from llama_index.core.query_engine import QueryEngine
from llama_index.llms.openai import OpenAI

# ================================================================
# 1. 文档解析器配置
# ================================================================

class DocumentProcessor:
    """
    文档处理配置
    """

    def __init__(self):
        # 语义分块器（基于句子相似度）
        self.semantic_splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            sentence_splitter=self._sentence_splitter,
            embed_model=OpenAIEmbedding("text-embedding-3-small"),
            percentile_threshold=95  # 相似度低于 95% 分位点时断开
        )

        # 备选：简单分块器
        self.sentence_splitter = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separator=["。", "！", "？", "\n"]
        )

    @staticmethod
    def _sentence_splitter(text: str) -> list[str]:
        """句子分割"""
        import re
        sentences = re.split(r'[。！？\n]+', text)
        return [s.strip() for s in sentences if s.strip()]


# ================================================================
# 2. 混合检索器配置
# ================================================================

class HybridRetriever:
    """
    混合检索器：向量 + BM25 + 知识图谱
    """

    def __init__(self, index: VectorStoreIndex, bm25_store):
        self.index = index
        self.bm25_store = bm25_store

    def build_fusion_retriever(
        self,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        top_k: int = 10
    ) -> QueryFusionRetriever:
        """
        构建融合检索器

        Args:
            vector_weight: 向量检索权重
            bm25_weight: BM25 权重
            top_k: 最终返回数量
        """

        # 向量检索器
        vector_retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=20,  # 初步检索更多
            filters=None
        )

        # BM25 检索器
        bm25_retriever = BM25Retriever.from_defaults(
            index=self.bm25_store,
            similarity_top_k=20,
            verbose=False
        )

        # 融合检索器
        fusion_retriever = QueryFusionRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            mode=QueryFusionMode.RECIPROCAL_RANK,  # RRF 融合
            # mode=QueryFusionMode.SIMPLE_AVERAGE,  # 加权平均
            similarity_top_k=top_k,
            weights=[vector_weight, bm25_weight]
        )

        return fusion_retriever


# ================================================================
# 3. Rerank 配置
# ================================================================

class RerankerConfig:
    """
    重排序配置
    """

    def __init__(self):
        # Cohere Rerank
        self.cohere_reranker = CohereRerank(
            api_key=os.environ["COHERE_API_KEY"],
            top_n=5,  # Rerank 后保留 5 个
            model="rerank-multilingual-v2.0"
        )

        # 或者使用 BGE-Reranker
        # self.bge_reranker = BGEReranker(
        #     model="BAAI/bge-reranker-large",
        #     top_n=5
        # )


# ================================================================
# 4. Query Engine 配置
# ================================================================

class QueryEngineConfig:
    """
    查询引擎配置
    """

    def __init__(
        self,
        fusion_retriever: QueryFusionRetriever,
        reranker,
        llm
    ):
        self.retriever = fusion_retriever
        self.reranker = reranker
        self.llm = llm

    def build_query_engine(self) -> QueryEngine:
        """
        构建查询引擎
        """

        # 配置后处理器
        postprocessors = [
            SimilarityPostprocessor(
                similarity_cutoff=0.7  # 低于 0.7 相似度过滤
            ),
            self.reranker  # Rerank
        ]

        # 构建查询引擎
        query_engine = self.index.as_query_engine(
            retriever=self.retriever,
            node_postprocessors=postprocessors,
            response_mode="compact",  # compact/summarize/tree_summarize
            verbose=True
        )

        return query_engine


# ================================================================
# 5. HyDE 查询改写配置
# ================================================================

from llama_index.core.prompts import PromptTemplate

class HyDEConfig:
    """
    HyDE (Hypothetical Document Embeddings) 配置

    原理：
    1. 先让 LLM 生成一个"假设性答案"
    2. 用这个假设性答案去检索
    3. 因为假设性答案包含答案的结构，检索更准确
    """

    hyde_prompt_template = PromptTemplate(
        input_variables=["query"],
        template="""
请为以下问题生成一个假设性的高质量答案。
这个答案可以是略微不准确的，但结构应该是正确的。

问题：{query}

假设性答案：
"""
    )

    def __init__(self, llm):
        self.llm = llm

    def get_hyde_retriever(self, index: VectorStoreIndex) -> Any:
        """获取 HyDE 检索器"""

        from llama_index.core.query_engine import RetrieverQueryEngine
        from llama_index.retrievers.bm25 import BM25Retriever

        # HyDE 检索流程
        hyde_retriever = HyDEQueryTransform(
            llm=self.llm,
            hyde_prompt=self.hyde_prompt_template,
            include_original=True  # 同时检索原始查询
        )

        return hyde_retriever
```

### 6.3 完整检索流程

```python
# ================================================================
# 完整检索流程实现
# ================================================================

class EnhancedRetriever:
    """
    增强检索器：集成 LlamaIndex 高级功能
    """

    def __init__(self, config: dict):
        # 初始化各组件
        self.doc_processor = DocumentProcessor()
        self.hybrid_retriever = HybridRetriever(...)
        self.reranker = RerankerConfig().cohere_reranker
        self.query_engine = QueryEngineConfig(...).build_query_engine()

    def query_with_citations(self, user_query: str) -> dict:
        """
        带引用的查询

        返回：
        {
            "answer": "...",
            "citations": [...],
            "metadata": {...}
        }
        """

        # 1. Query Rewriting (可选)
        rewritten_query = self._rewrite_query(user_query)

        # 2. 执行查询
        response = self.query_engine.query(rewritten_query)

        # 3. 提取引用信息
        citations = self._extract_citations(response)

        # 4. 计算置信度
        confidence = self._calculate_confidence(response, citations)

        return {
            "answer": response.response,
            "citations": citations,
            "confidence": confidence,
            "metadata": {
                "query": user_query,
                "rewritten_query": rewritten_query,
                "retrieval_time": response.metadata.get("retrieval_time"),
                "total_nodes": len(response.source_nodes)
            }
        }

    def _rewrite_query(self, query: str) -> str:
        """
        查询改写：使用 LlamaIndex 的查询改写功能
        """

        # 子问题查询改写
        sub_questions = self.llm.predict(
            "请将这个问题拆分成多个可以独立检索的子问题。\n"
            f"问题：{query}\n\n"
            "子问题（用 | 分隔）："
        )

        # 如果拆分成功，用子问题替代
        if "|" in sub_questions:
            return sub_questions.replace("|", " ")

        return query

    def _extract_citations(self, response) -> list[dict]:
        """
        提取引用信息
        """

        citations = []

        for i, source_node in enumerate(response.source_nodes, 1):
            citation = {
                "ref_id": f"[{i}]",
                "text": source_node.text,
                "doc_title": source_node.metadata.get("doc_title", "未知来源"),
                "page": source_node.metadata.get("page_num", "N/A"),
                "score": source_node.score,
                "valid_until": source_node.metadata.get("valid_until"),
                "category": source_node.metadata.get("category", "general")
            }
            citations.append(citation)

        return citations

    def _calculate_confidence(
        self,
        response,
        citations: list[dict]
    ) -> float:
        """
        计算置信度
        """

        if not citations:
            return 0.0

        # 综合评分
        score_factors = []

        # 1. 平均相似度分数
        avg_similarity = sum(c["score"] for c in citations) / len(citations)
        score_factors.append(avg_similarity * 0.4)

        # 2. 引用数量（越多越可信，但不能太多）
        citation_count_bonus = min(len(citations) / 5, 1.0) * 0.2
        score_factors.append(citation_count_bonus)

        # 3. 来源权威性
        authority_score = self._calculate_authority(citations)
        score_factors.append(authority_score * 0.2)

        # 4. 时效性
        recency_score = self._calculate_recency(citations)
        score_factors.append(recency_score * 0.2)

        return min(sum(score_factors), 1.0)

    def _calculate_authority(self, citations: list[dict]) -> float:
        """计算来源权威性"""

        authority_map = {
            "国办发": 1.0,      # 国务院文件
            "人社部": 0.95,    # 人力资源部
            "教育部": 0.95,
            "省": 0.8,
            "市": 0.7,
            "学校": 0.6,
            "general": 0.5
        }

        scores = []
        for cite in citations:
            title = cite.get("doc_title", "")
            score = 0.5
            for key, val in authority_map.items():
                if key in title:
                    score = val
                    break
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.5

    def _calculate_recency(self, citations: list[dict]) -> float:
        """计算时效性"""

        from datetime import datetime, timedelta

        now = datetime.now()
        recency_scores = []

        for cite in citations:
            valid_until = cite.get("valid_until")

            if not valid_until:
                recency_scores.append(0.5)
                continue

            if isinstance(valid_until, str):
                valid_until = datetime.fromisoformat(valid_until)

            days_until_expire = (valid_until - now).days

            if days_until_expire < 0:
                recency_scores.append(0.0)  # 已过期
            elif days_until_expire < 30:
                recency_scores.append(0.5)  # 即将过期
            else:
                recency_scores.append(1.0)  # 有效

        return sum(recency_scores) / len(recency_scores) if recency_scores else 0.5
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
│                              │ • role (user/ai) │                                │
│                              │ • content        │                                │
│                              │ • confidence     │  ←--- 新增：置信度             │
│                              │ • is_no_answer   │  ←--- 新增：无法回答标记       │
│                              │ • tool_used      │  ←--- 新增：使用的工具         │
│                              │ • created_at     │                                 │
│                              └────────┬─────────┘                                 │
│                                       │ 1:N                                        │
│                                       ▼                                           │
│                              ┌─────────────────┐                                 │
│                              │ qa_message_ref  │                                 │
│                              │ (消息引用)       │                                 │
│                              │                  │                                 │
│                              │ • id (PK)        │                                 │
│                              │ • message_id(FK) │                                 │
│                              │ • document_id(FK)│────────┐                       │
│                              │ • chunk_id       │        │                       │
│                              │ • ref_text       │        │ N:1                   │
│                              │ • page_no        │        ▼                       │
│                              │ • valid_until    │  ┌──────────────┐              │
│                              │ • score          │  │ kb_document   │              │
│                              │ • rank_no        │  │ (文档)        │              │
│                              │ • citation_text  │  │              │              │
│                              │ • source_url     │  │ • id (PK)     │              │
│                              └─────────────────┘  │ • title       │              │
│                                                  │ • category    │              │
│                                                  │ • version      │              │
│                                                  │ • valid_from   │              │
│                                                  │ • valid_until  │              │
│                                                  └──────────────┘              │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │ kb_chunk        │         │ kb_faq          │         │ kb_category     │   │
│  │ (文档块)        │         │ (FAQ)           │         │ (文档分类)      │   │
│  │                 │         │                 │         │                 │   │
│  │ • id (PK)       │         │ • id (PK)       │         │ • id (PK)       │   │
│  │ • document_id(FK)│       │ • question      │         │ • name          │   │
│  │ • content        │         │ • answer        │         │ • parent_id(FK) │   │
│  │ • chunk_index    │         │ • keywords      │         │ • level        │   │
│  │ • char_count     │         │ • hit_count     │         │ • sort_order   │   │
│  │ • embedding      │         │ • status        │         └─────────────────┘   │
│  │ • vector_id      │         │ • created_by(FK)│                               │
│  └─────────────────┘         │ • created_at    │                               │
│                              └─────────────────┘                               │
│                                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐   │
│  │ op_sensitive_word│       │ op_query_log    │         │ agent_tool_call│   │
│  │ (敏感词)        │         │ (查询日志)       │         │ (工具调用日志)  │   │
│  │                 │         │                 │         │                 │   │
│  │ • id (PK)       │         │ • id (PK)       │         │ • id (PK)       │   │
│  │ • word          │         │ • user_id (FK)  │         │ • message_id(FK)│        │
│  │ • category      │         │ • query         │         │ • tool_name    │       │
│  │ • action        │         │ • route         │         │ • tool_input    │       │
│  │ • status        │         │ • confidence    │         │ • tool_output   │       │
│  │ • created_by(FK)│         │ • response_time │         │ • status       │       │
│  │ • created_at    │         │ • created_at     │         │ • created_at   │       │
│  └─────────────────┘         └─────────────────┘         └─────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

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

#### 7.3.1 系统参数

```python
# ================================================================
# 系统配置参数
# ================================================================

class SystemConfig:
    """系统级配置"""

    # ===== Agent 配置 =====
    AGENT_MAX_ITERATIONS = 10  # Agent 最大迭代次数
    AGENT_MAX_TOKENS = 4000    # Agent 输出最大 Token 数
    AGENT_TEMPERATURE = 0.7    # Agent 生成温度

    # ===== 检索配置 =====
    RETRIEVAL_TOP_K = 10       # 初步检索数量
    RETRIEVAL_FINAL_K = 5     # 最终返回数量
    SIMILARITY_THRESHOLD = 0.7  # 相似度阈值
    RERANK_TOP_N = 5          # Rerank 后保留数量

    # ===== 置信度配置 =====
    CONFIDENCE_HIGH = 0.8     # 高置信度
    CONFIDENCE_MEDIUM = 0.5    # 中置信度
    CONFIDENCE_LOW = 0.3       # 低置信度
    REFUSE_THRESHOLD = 0.5     # 拒答阈值

    # ===== 版本管理 =====
    VERSION_STALE_DAYS = 90    # 知识库过期天数
    VERSION_CHECK_INTERVAL = 24  # 版本检查间隔（小时）

    # ===== 限流配置 =====
    RATE_LIMIT_FREE = 100      # 免费版日调用限制
    RATE_LIMIT_PRO = 500      # 专业版日调用限制
    RATE_LIMIT_ENTERPRISE = -1 # 企业版不限


class RetrievalConfig:
    """检索配置"""

    # ===== 向量检索 =====
    VECTOR_WEIGHT = 0.6        # 向量检索权重
    BM25_WEIGHT = 0.4          # BM25 权重
    EMBEDDING_MODEL = "text-embedding-v4"
    EMBEDDING_DIM = 1024

    # ===== Query Rewriting =====
    ENABLE_HYDE = True        # 是否启用 HyDE
    ENABLE_SUBQUESTION = True  # 是否启用子问题拆分
    ENABLE_SYONYMY = True      # 是否启用同义词扩展

    # ===== Rerank =====
    RERANKER_MODEL = "cohere/rerank-multilingual-v2.0"
    RERANK_API_KEY = ""       # Cohere API Key

    # ===== Fusion =====
    FUSION_MODE = "reciprocal_rank"  # RRF / simple_average / dist_based_score


class LLMRouterConfig:
    """LLM 路由配置"""

    # 主模型
    PRIMARY_MODEL = "qwen-max"
    PRIMARY_API_KEY = ""

    # 备用模型
    FALLBACK_MODEL = "qwen-plus"
    FALLBACK_RETRIES = 2

    # 模型参数
    TEMPERATURE_MAP = {
        "qwen-max": 0.7,
        "qwen-plus": 0.5,
        "gpt-4-turbo": 0.7
    }

    MAX_TOKENS_MAP = {
        "qwen-max": 2000,
        "qwen-plus": 1500,
        "gpt-4-turbo": 2000
    }

    # 成本配置
    COST_PER_1K_INPUT = {
        "qwen-max": 0.02,
        "qwen-plus": 0.005,
        "gpt-4-turbo": 0.03
    }

    COST_PER_1K_OUTPUT = {
        "qwen-max": 0.02,
        "qwen-plus": 0.01,
        "gpt-4-turbo": 0.06
    }
```

---

## 八、部署架构（完整版）

### 8.1 Kubernetes 部署配置

```yaml
# k8s/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiqa-agent
  namespace: aiqa-prod
  labels:
    app: aiqa-agent
    version: v2.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aiqa-agent
  template:
    metadata:
      labels:
        app: aiqa-agent
        version: v2.0
      annotations:
        langsmith.project: "aiqa-agent"
        langsmith.run.name: "{{ pod.name }}"
    spec:
      containers:
        - name: agent
          image: ${REGISTRY}/aiqa-agent:v2.0
          ports:
            - containerPort: 8000
          env:
            # LLM 配置
            - name: DASHSCOPE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: aiqa-secrets
                  key: dashscope-key
            - name: LANGCHAIN_API_KEY
              valueFrom:
                secretKeyRef:
                  name: aiqa-secrets
                  key: langsmith-key
            - name: LANGCHAIN_TRACING_V2
              value: "true"
            - name: LANGCHAIN_PROJECT
              value: "aiqa-agent-prod"

            # 数据库配置
            - name: DB_HOST
              value: "mysql-headless"
            - name: DB_PORT
              value: "3306"
            - name: REDIS_HOST
              value: "redis-headless"
            - name: REDIS_PORT
              value: "6379"

            # 检索配置
            - name: VECTOR_WEIGHT
              value: "0.6"
            - name: BM25_WEIGHT
              value: "0.4"
            - name: RERANK_TOP_N
              value: "5"

            # 资源限制
            - name: MAX_WORKERS
              value: "10"
            - name: TIMEOUT_SECONDS
              value: "60"
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: aiqa-agent-service
  namespace: aiqa-prod
spec:
  selector:
    app: aiqa-agent
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: aiqa-agent-hpa
  namespace: aiqa-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: aiqa-agent
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
```

### 8.2 Helm Chart Values

```yaml
# helm/values.yaml

replicaCount: 3

image:
  repository: aiqa-agent
  tag: v2.0
  pullPolicy: IfNotPresent

env:
  LANGCHAIN_TRACING_V2: "true"
  LANGCHAIN_PROJECT: "aiqa-agent-{{ .Release.Namespace }}"
  VECTOR_WEIGHT: "0.6"
  BM25_WEIGHT: "0.4"
  RERANK_TOP_N: "5"
  CONFIDENCE_THRESHOLD: "0.7"

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
  hosts:
    - host: api.aiqa.example.com
      paths:
        - path: /
          pathType: Prefix

dependencies:
  mysql:
    enabled: true
    image: mysql:8.0
    persistence:
      enabled: true
      size: 50Gi

  redis:
    enabled: true
    image: redis:7-alpine
    persistence:
      enabled: true
      size: 10Gi

  chromadb:
    enabled: true
    image: chromadb/chroma:latest
    persistence:
      enabled: true
      size: 100Gi
```

---

## 九、技术栈完整清单 (v2.0)

| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **Agent 框架** | LangGraph | 0.1+ | 状态机工作流 |
| **LLM 监控** | LangSmith | - | 调用追踪、Prompt 管理 |
| **检索框架** | LlamaIndex | 0.10+ | 混合检索、Rerank |
| **向量数据库** | ChromaDB | 0.5+ | 向量存储 |
| **全文检索** | Elasticsearch | 8.x | BM25 检索 |
| **Rerank 模型** | Cohere | - | 重排序 |
| **后端框架** | FastAPI | 0.115+ | 异步 API |
| **数据库** | MySQL | 8.0 | 主业务数据 |
| **缓存** | Redis | 7.0 | 会话、工具缓存 |
| **LLM API** | DashScope | - | 通义千问 |
| **前端** | Vue3 + TS | 3.4+ | 用户界面 |
| **容器化** | Docker | 24+ | 容器化 |
| **编排** | Kubernetes | 1.28+ | 容器编排 |
| **监控** | Prometheus + Grafana | - | 指标监控 |
| **日志** | ELK Stack | - | 日志聚合 |

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

### 10.3 LlamaIndex 面试价值

| 面试点 | 回答要点 |
|--------|---------|
| **简单向量检索的问题？** | 只用语义相似度，忽略关键词；无法处理多义词、同义词 |
| **混合检索原理？** | 向量检索 + BM25 关键词检索，用 RRF 算法融合结果 |
| **Rerank 为什么必要？** | 向量检索 Top-K 不一定是最相关的，Rerank 用更强大的模型重新排序 |
| **HyDE 是什么？** | 让 LLM 先生成假设性答案，再检索，提高检索准确率 |
| **Citation 如何实现？** | LlamaIndex 内置节点级引用追踪，自动记录来源 |

### 10.4 大模型问题解决方案

| 问题 | 解决方案 | 面试亮点 |
|------|---------|---------|
| **幻觉** | 三重防护：置信度过滤 + 引用强制 + 拒答机制 | 不是简单加 Prompt，而是系统性工程 |
| **不可溯源** | LlamaIndex Citation + 句子级引用 + 引用验证 | 精确到句子级别的溯源体系 |
| **时效性低** | 知识库版本管理 + 时效性标记 + 实时数据通道 | 完整的版本生命周期管理 |

---

## 附录

### A. 环境变量清单

```bash
# .env 配置

# ===== LangSmith =====
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=aiqa-agent-prod
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# ===== LLM =====
DASHSCOPE_API_KEY=your-dashscope-key
OPENAI_API_KEY=your-openai-key

# ===== Cohere Rerank =====
COHERE_API_KEY=your-cohere-key

# ===== Database =====
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=xxx
DB_NAME=aiqa_db

# ===== Redis =====
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=xxx

# ===== Retrieval =====
VECTOR_WEIGHT=0.6
BM25_WEIGHT=0.4
RERANK_TOP_N=5
SIMILARITY_THRESHOLD=0.7

# ===== Agent =====
AGENT_MAX_ITERATIONS=10
CONF_INTERVAL=0.7
REFUSE_THRESHOLD=0.5
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

# LlamaIndex
pip install llama-index llama-index-core llama-index-postprocessor-cohere-rerank

# 向量库
pip install chromadb

# 全文检索
pip install elasticsearch

# 工具库
pip install httpx tiktoken
```

---

*文档版本：v2.0*
*最后更新：2026-06*
