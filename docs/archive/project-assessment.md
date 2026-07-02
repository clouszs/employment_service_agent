# 项目评估报告

> **评估日期**：2026-06-26
> **评估范围**：后端代码库 + 前端代码库 + 设计文档
> **评估目的**：V4.0 方案实施前的全面代码审查与优化建议

---

## 一、当前代码健康度总览

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | ⭐⭐⭐⭐ | LangGraph 11 节点图清晰，环路有防护 |
| 状态管理 | ⭐⭐⭐ | `AgentState` 字段齐全，但类型定义不规范 |
| 节点职责 | ⭐⭐⭐⭐ | 每个节点职责单一，符合 SRP |
| 错误处理 | ⭐⭐⭐ | 有 `error_handler` 兜底，但 `qa_service.agent_chat()` 无超时保护 |
| 可观测性 | ⭐⭐⭐ | LangSmith 已配置，`reasoning_chain` 已记录 |
| 测试覆盖 | ❌ | 未看到任何单元测试文件 |
| 代码整洁度 | ⭐⭐ | 死代码 + 重复文档 + 重复逻辑 |

---

## 二、核心问题深度分析

### 2.1 幻觉问题

**当前防护体系**：

```
第一重：动态置信度阈值 ✅
  ├─ 按风险等级（high/medium/low）使用不同阈值
  ├─ 重试时动态降级（每次 -0.15，保底 0.30）
  └─ 最大重试 3 次，耗尽后降级回答（带警告）

第二重：引用强制生成 ✅
  ├─ Prompt 中明确约束"只能从参考资料提取"
  ├─ 句末标注 [1][2] 来源编号
  └─ 检索无结果时直接返回"未找到答案"兜底语

第三重：自我一致性检查 ⚠️
  ├─ V1 简化版：只检查"否定词 + 历史关键词"的明显矛盾
  ├─ 不做多轮生成比对
  └─ 验证器降级（非阻塞）

第四重：事实核验 ⚠️
  ├─ 正则提取政策编号、日期、金额、数量
  ├─ 当前只标记存在的事实要素
  └─ 不做跨源校验（V2 再加）

第五重：内容审核 ⚠️
  ├─ 输出侧敏感词过滤（正则匹配）
  ├─ 不与输入侧形成真正闭环
  └─ 未调 LLM 做深度审核
```

**评估结论**：

| 防护层 | 有效性 | 说明 |
|--------|--------|------|
| 动态置信度阈值 | ✅ 有效 | 低分结果会被拦截或降级 |
| 引用强制生成 | ✅ 有效 | Prompt 约束严格，"不知道就说不知道" |
| 自我一致性检查 | ⚠️ 部分有效 | 只检测同一回答内部的明显矛盾，不检测跨轮矛盾 |
| 事实核验 | ⚠️ 标记但未验证 | 能提取政策编号/日期/金额，但不验证其正确性 |
| 内容审核 | ⚠️ 表面有效 | 只做关键词匹配，容易被绕过 |

**核心缺陷**：
1. **`verify_facts` 节点不验证**：`FactVerificationPostProcessor.verify()` 只做 regex 提取，标记为"待跨源校验"，但实际上从未校验。如果 LLM 编造了一个政策编号（如"国办发〔2024〕99号"），系统会原样输出。
2. **`check_consistency` 检测范围太窄**：只检查当前回答中是否同时包含"可以"和"不可以"，不检查与历史回答的矛盾。
3. **`content_moderation` 只做关键词匹配**：不调 LLM，容易绕过。

**建议优先级**：
- P0：保持现状（MVP1 不做额外 LLM 调用）
- P1：`verify_facts` 增加"事实是否被引用支持"的简单校验（用引用得分判断）
- P2：`check_consistency` 接入 LLM 做跨轮比对
- P2：`content_moderation` 接入 LLM 做深度审核

---

### 2.2 溯源问题

**当前溯源能力**：

```
引用构建（citation_tracker.py）
  ├─ build_citations(hits) → list[dict]
  │   ├─ rank: 引用序号 [1][2][3]
  │   ├─ document_id: 文档 ID
  │   ├─ document_title: 文档标题
  │   ├─ chunk_id: 分片 ID
  │   ├─ score: 检索得分
  │   ├─ page_no: 页码
  │   ├─ snippet: 内容片段（200 字符）
  │   ├─ source_type: "local" | "web"
  │   ├─ url: web 来源链接
  │   ├─ source: 新闻来源
  │   ├─ published_at: 发布日期
  │   └─ author: 作者
  │
  └─ evaluate_citation_quality(citations) → dict
      ├─ quality_score: 整体质量分
      ├─ direct_count: 强引用数（score >= 0.75）
      ├─ indirect_count: 弱引用数（0.40 <= score < 0.75）
      ├─ none_count: 无引用数
      └─ avg_score: 平均得分
```

**前端展示**：
- 本地来源：蓝色卡片，显示文档标题 + 页码 + 相似度 + 片段
- Web 来源：黄色卡片，显示来源名称 + 发布日期 + "查看原文"链接

**评估结论**：

| 溯源维度 | 状态 | 说明 |
|----------|------|------|
| 引用到具体文档 | ✅ | `document_id` + `document_title` |
| 引用到具体分片 | ✅ | `chunk_id` |
| 引用到具体页码 | ✅ | `page_no` |
| 引用置信度 | ✅ | `score` 字段 |
| 句子级引用 | ❌ | V2 才实现（`SentenceLevelCitationTracker` 未实现） |
| 引用支持度验证 | ❌ | 不做 LLM 级验证（direct/indirect/none） |

**核心缺陷**：
1. **粒度不够细**：只能引用到 chunk 级别，不能精确到句子。用户无法知道回答中哪句话来自哪个具体句子。
2. **引用准确性缺乏验证**：LLM 可能错误归因（引用了不相关的 chunk），系统不做校验。
3. **引用质量评估是统计性的**：`evaluate_citation_quality()` 只基于得分区间做统计映射，不做 LLM judge。

**建议优先级**：
- P0：保持 chunk 级引用（MVP1 不做句子级）
- P1：`evaluate_citation_quality()` 增加"引用是否被回答实际使用"的检查（对比回答文本和引用片段的文本重叠度）
- P2：V2 实现 `SentenceLevelCitationTracker`

---

### 2.3 时效性问题

**当前时效性处理**：

```
检索流程中的时效性处理：
  ├─ filter_expired_docs(db, doc_ids) → set[int]
  │   └─ 查询 MySQL，返回已过期文档 ID 集合
  │
  ├─ apply_temporal_adjustment(hits, expired_ids) → list[dict]
  │   └─ V1 简化：仅添加 is_expired 标记，不修改得分
  │
  └─ search_knowledge 节点
      ├─ 调用 filter_expired_docs 过滤过期文档
      ├─ 调用 apply_temporal_adjustment 标记剩余结果
      └─ 过期文档直接从检索结果中移除（不展示给用户）

监控层面的时效性处理：
  ├─ KnowledgeBaseHealthMonitor.run_daily_check()
  │   ├─ 计算健康度评分（指数衰减：exp(-0.693 × days / half_life)）
  │   ├─ 过期文档 freshness *= 0.1
  │   └─ 写入 kb_health_log 表
  │
  └─ get_expiring_soon_docs(db, warning_days=30)
      └─ 返回即将过期文档列表（供管理员预警）
```

**评估结论**：

| 时效性维度 | 状态 | 说明 |
|------------|------|------|
| 过期文档过滤 | ✅ | 检索时直接过滤已过期文档 |
| 即将过期预警 | ✅ | 监控模块每日检查，30 天预警 |
| 健康度评分 | ✅ | 指数衰减模型，过期惩罚 ×0.1 |
| 检索结果时效性排序 | ❌ | V1 不修改得分，V2 才做综合得分排序 |
| 用户侧时效性提示 | ⚠️ | `temporal_warnings` 字段存在，但 `search_knowledge` 节点未实际填充 |

**核心缺陷**：
1. **`temporal_warnings` 未填充**：`search_knowledge` 节点调用 `apply_temporal_adjustment` 后，没有把过期文档信息写入 `state["temporal_warnings"]`。前端永远看不到时效性警告。
2. **V1 不做时效性排序**：过期文档只是被移除，近过期文档（如 15 天后过期）和新鲜文档在排序上没有任何区别。
3. **外部检索结果无时效性处理**：`web_search` 返回的外部结果没有 `valid_until` 概念，无法判断是否过期。

**建议优先级**：
- P0：修复 `temporal_warnings` 填充（`search_knowledge` 节点中补充）
- P1：近过期文档降权（不是直接过滤，而是标记为"即将过期，建议核实"）
- P2：V2 实现综合得分排序（similarity × 0.7 + temporal × 0.3）

---

### 2.4 答案准确性问题

**当前准确性保障**：

```
准确性保障链条：
  ├─ 输入侧：ops_service.moderate() 敏感词过滤
  ├─ 检索侧：rag_service.search() 向量检索 + score_threshold 过滤
  ├─ 生成侧：Prompt 严格约束"只能从参考资料提取"
  ├─ 输出侧：nodes.content_moderation() 敏感词过滤
  └─ 兜底：检索无结果 / LLM 判定无法回答 → 返回标准兜底语
```

**评估结论**：

| 准确性维度 | 状态 | 说明 |
|------------|------|------|
| 输入侧安全过滤 | ✅ | 敏感词缓存 + 正则匹配，有拦截/替换/告警三级 |
| 检索侧置信度过滤 | ✅ | `retrieve_score_threshold` 过滤低分结果 |
| 生成侧 Prompt 约束 | ✅ | "绝对禁用常识和已知信息" |
| 无答案兜底 | ✅ | 标准兜底语 + `record_unanswered` 记录 |
| 事实要素验证 | ❌ | 只提取不验证 |
| 跨源一致性 | ❌ | 不做多源交叉验证 |
| 答案后置校验 | ❌ | 没有生成后的二次验证 |

**核心缺陷**：
1. **Prompt 约束不等于事实正确**：LLM 可能"自信地编造"——即使 Prompt 说"只能从参考资料提取"，LLM 仍可能在参考资料基础上做不正确的推断。
2. **检索分数不等于内容质量**：ChromaDB 余弦相似度高只代表语义相近，不代表内容准确。
3. **无外部验证机制**：当前没有"把生成的答案和参考资料做二次比对"的步骤。

**建议优先级**：
- P0：保持现状（MVP1 不做额外 LLM 调用）
- P1：`verify_facts` 增加"事实是否被引用内容支持"的校验（用引用片段的文本匹配）
- P2：新增 `groundedness_check` 节点（LLM 逐句验证）

---

## 三、其他优化发现

### 3.1 代码质量问题

| 问题 | 严重度 | 位置 | 说明 |
|------|--------|------|------|
| 死代码 | 🟡 中 | `prompts/router.py`、`prompts/refusal.py`、`prompts/moderation.py` | 定义了但从未被调用 |
| 重复文档 | 🟡 中 | `Agent模块融合实施方案.md` | 第 8 章出现两遍完全重复 |
| 类型定义不规范 | 🟢 低 | `state.py` | `class AgentState(Annotated[dict, ...])` 不是合法 TypedDict |
| Graph 重复编译 | 🟢 低 | `graph.py` + `qa_service.py` + `routers/agent.py` | 每次都重新 build + compile |
| 两个 Agent 端点重复逻辑 | 🟡 中 | `routers/agent.py` / `routers/qa.py` | 消息保存、图编译逻辑重复 |

### 3.2 架构问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| `qa_service.agent_chat()` 无超时保护 | 🔴 高 | `routers/agent.py` 有 `asyncio.wait_for`，但 `qa_service.py` 直接 `app.invoke()` 无超时 |
| `ToolCallTracker` 每次新建 | 🟡 中 | `search_knowledge` 中新建的 tracker 不会累积跨节点调用次数 |
| `semantic_cache` 只在 `/chat` 生效 | 🟢 低 | `/ask/agent` 不走缓存 |
| 无单元测试 | 🟡 中 | 任何改动都无法快速验证 |
| `ask_stream` 用 `time.sleep` | 🟢 低 | 阻塞 generator 线程 |

---

## 四、V4.0 方案与当前代码的差距

| V4.0 方案项 | 当前状态 | 差距 |
|-------------|---------|------|
| 五类意图分类 | 3 类关键词路由 | 需要新增 `job_query` 和 `web_query` |
| Bing 搜索 | NewsAPI | 需要替换 `web_search()` 实现 |
| Fetch 网页抓取 | ❌ 不存在 | 需要新增 `fetch_webpage()` |
| `safety_filter` 节点 | ❌ 不存在 | 需要新增（复用 `ops_service.moderate`） |
| `context_merge` 节点 | ❌ 不存在 | 需要新增（简单拼接历史消息） |
| `classify_intent` 节点 | ❌ 不存在 | 需要新建（或扩展现有 `route_query`） |
| 站点白名单路由 | ❌ 不存在 | 需要新增政务站/招聘站白名单 |
| `groundedness_check` 节点 | ❌ 不存在 | 需要新增 |
| 前端传消息历史 | ❌ 不存在 | 需要修改前端 `sendAgent()` |
| 死代码清理 | ❌ 未清理 | 3 个 prompt 文件 + 1 个重复文档章节 |

---

## 五、优化建议汇总

### 5.1 立即执行（P0）

| # | 优化项 | 文件 | 预期收益 |
|---|--------|------|---------|
| 1 | 修复 `temporal_warnings` 未填充 | `nodes.py` | 前端能显示时效性警告 |
| 2 | 修复 `qa_service.agent_chat()` 无超时 | `qa_service.py` | 防止单个请求阻塞 worker |
| 3 | 删除死代码 | `prompts/router.py` 等 | 消除混淆 |
| 4 | 删除文档重复章节 | `Agent模块融合实施方案.md` | 消除混淆 |

### 5.2 MVP1 执行（与 V4.0 方案对齐）

| # | 优化项 | 文件 | 说明 |
|---|--------|------|------|
| 5 | 新增配置项 | `config.py` | Bing/Fetch URL、站点白名单、 groundedness_check 开关 |
| 6 | 新增关键词常量 | `constants.py` | web_query / job_query 关键词列表 |
| 7 | 替换 `web_search()` | `tools.py` | 新增 `bing_search()` + `fetch_webpage()` |
| 8 | 扩展 `route_query` | `nodes.py` | 5 类意图分类 |
| 9 | 增强 `search_knowledge` | `nodes.py` | Bing → Fetch 分级 fallback |
| 10 | 新增 `safety_filter` 节点 | `nodes.py` | 输入侧安全审核 |
| 11 | 新增 `context_merge` 节点 | `nodes.py` | 简单拼接历史消息 |
| 12 | 前端传消息历史 | `chat.ts` / `chat.ts` | `sendAgent()` 传 `messages[]` |

### 5.3 MVP2 执行

| # | 优化项 | 文件 | 说明 |
|---|--------|------|------|
| 13 | 新增 `groundedness_check` 节点 | `nodes.py` + `graph.py` | LLM 逐句验证 |
| 14 | 新增 `rewrite_question` 节点 | `nodes.py` + `graph.py` | 指代消解 + 追问补全 |
| 15 | `check_consistency` 升级 | `hallucination_defense.py` | LLM 跨轮比对 |
| 16 | `content_moderation` 升级 | `nodes.py` | LLM 深度审核 |

### 5.4 长期优化

| # | 优化项 | 说明 |
|---|--------|------|
| 17 | 合并两个 Agent 端点 | 减少重复逻辑 |
| 18 | 缓存 compiled graph | 避免每次调用都重新 build |
| 19 | 标准化 AgentState | 改为合法 TypedDict |
| 20 | 添加单元测试 | 核心节点 + 工具函数 |
| 21 | 实现 Rerank | Cohere API 或本地 bge-reranker |
| 22 | 实现 SentenceLevelCitationTracker | 句子级引用追踪 |

---

## 六、幻觉/溯源/时效性/准确性 总结

| 维度 | 当前能力 | 缺口 | MVP1 后能力 | MVP2 后能力 |
|------|---------|------|------------|------------|
| **幻觉防护** | 动态阈值 + Prompt 约束 + regex 检查 | 事实不验证、一致性检测弱 | + Bing 外部检索（更多依据） | + groundedness_check + LLM 一致性 |
| **溯源** | chunk 级引用 + 本地蓝卡/外部黄卡 | 句子级缺失、引用准确性未验证 | + 外部来源展示 | + 句子级引用 + 支持度验证 |
| **时效性** | 过期文档过滤 + 健康度监控 | `temporal_warnings` 未展示、无时效性排序 | + 修复 warnings 展示 | + 综合得分排序 |
| **准确性** | 检索过滤 + Prompt 约束 + 无答案兜底 | 事实不验证、无跨源校验 | + 外部检索补充 | + groundedness_check |

---

## 七、结论

1. **当前代码的幻觉防护是"半闭环"**：能拦截低置信度结果、能做 regex 提取，但**不做真正的验证**。`verify_facts` 节点只标记"有政策编号/日期/金额"，不验证这些事实是否正确。这是当前最大的准确性风险。

2. **溯源能力够用但不精确**：chunk 级引用 + 得分展示对于 MVP 已经足够，但句子级引用和引用准确性验证是明显的体验缺口。

3. **时效性处理有框架但未落地**：`temporal_warnings` 字段存在但从未被填充，用户看不到任何时效性提示。这是**一个明显的 bug**，修复成本极低。

4. **准确性最大的保障是"不知道就说不知道"**：当前 Prompt 约束 + 兜底语 + FAQ 优先的机制，在"无答案"场景下的表现是可靠的。真正的风险在于"有依据但依据本身有问题"的场景。

5. **V4.0 方案整体可行**：MVP1 的核心增量是 Bing 搜索 + 5 类意图分类 + 前端传历史，技术风险可控。最大的不确定性是 Bing MCP 的接口格式。

---

*报告完毕。下一步：确认优化优先级后，开始 MVP1 编码。*
