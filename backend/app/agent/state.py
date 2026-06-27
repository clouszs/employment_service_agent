"""Agent 状态定义：LangGraph 工作流的共享状态。"""

from __future__ import annotations

from typing import TypedDict, Annotated, Optional

from langgraph.graph import add_messages


class AgentState(TypedDict):
    """LangGraph Agent 工作流状态。

    使用 TypedDict 定义，支持 IDE 类型检查和 LangGraph 状态管理。
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

    # ===== 工具扩展结果（阶段 9 新增）=====
    resume_data: dict  # 简历生成结果
    job_recommendations: list[dict]  # 职位推荐结果
    calendar_events: list[dict]  # 面试日程数据
    announcements: list[dict]  # 公告列表

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

