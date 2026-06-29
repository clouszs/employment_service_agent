"""特性级 LLM 用量记账。

为「非对话类」的 LLM 调用（如简历生成）提供统一记账落点，避免它们绕过成本监控：
  1. 写入 llm_usage 流水表（原始 token，不存成本）；
  2. 结构化日志审计（feature/model/tokens/user）；
  3. 把规整后的 usage 回传给调用方写入 API 响应。

流水由 cost_monitor.run_daily_check 在每日聚合时按 (model, source) 汇总进 llm_cost_log，
从而与 Agent 对话成本（source=agent_chat）在同一看板融合。
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import LlmUsage

logger = logging.getLogger("llm_usage")


def log_feature_usage(
    db: Session,
    source: str,
    usage: dict[str, int],
    user_id: Optional[int] = None,
    model: Optional[str] = None,
) -> dict[str, int]:
    """记录一次特性级 LLM 调用的 token 用量（流水落库 + 审计日志）。

    Args:
        db: 数据库会话
        source: 来源标识（用 LlmUsageSource 的取值，如 "resume_generation"）
        usage: chat_with_usage 返回的 {prompt_tokens, completion_tokens}
        user_id: 触发用户 ID（可空）
        model: 模型名（默认取 settings.llm_model）

    Returns:
        规整后的 usage（含 model/total_tokens），供写入 API 响应。
    """
    prompt = int(usage.get("prompt_tokens", 0) or 0)
    completion = int(usage.get("completion_tokens", 0) or 0)
    used_model = model or settings.llm_model

    # 落流水：失败不阻断主流程（审计日志仍保留）
    try:
        db.add(
            LlmUsage(
                source=source,
                model=used_model,
                prompt_tokens=prompt,
                completion_tokens=completion,
                user_id=user_id,
            )
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        logger.warning("写入 llm_usage 流水失败: source=%s err=%s", source, exc)

    logger.info(
        "feature_llm_usage feature=%s user_id=%s model=%s prompt_tokens=%d completion_tokens=%d",
        source,
        user_id,
        used_model,
        prompt,
        completion,
    )
    return {
        "model": used_model,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
    }
