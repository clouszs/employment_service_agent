"""简历生成服务（学生自助）。

由 REST 端点直接调用，不经过 Agent 工作流：简历生成是用户主动触发的确定性
业务功能，不需要 Agent 的意图路由/检索。LLM 调用走 chat_with_usage，并通过
llm_usage.log_feature_usage 记录用量（审计链路）。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.llm import chat_with_usage
from app.models import LlmUsageSource, SysUser
from app.services.llm_usage import log_feature_usage

logger = logging.getLogger(__name__)

_USER_TYPE_LABEL = {1: "学生", 2: "毕业生", 3: "辅导员", 4: "教师", 5: "管理员"}

_RESUME_PROMPT = (
    "你是专业的简历生成助手。请根据【用户档案】和【目标岗位】生成一份中文简历，"
    "只返回严格的 JSON，不要任何解释或 Markdown 代码块。\n"
    "JSON 结构：\n"
    '{{"basics":{{"name":"","title":"","email":"","phone":"","location":""}},'
    '"summary":"","education":[{{"school":"","major":"","degree":"","period":""}}],'
    '"experience":[{{"org":"","role":"","period":"","highlights":[""]}}],'
    '"skills":[""],"projects":[{{"name":"","desc":"","highlights":[""]}}]}}\n'
    "要求：内容真实合理、与目标岗位匹配；缺失信息可基于岗位做通用化补全但不得编造具体单位名。\n"
    "【用户档案】{profile}\n"
    "【目标岗位】{target_job}\n"
)


def _build_profile(user: SysUser, extra: Optional[dict[str, Any]]) -> dict[str, Any]:
    """从用户记录 + 前端补充信息组装档案。"""
    profile: dict[str, Any] = {
        "name": user.real_name or user.username,
        "identity": _USER_TYPE_LABEL.get(user.user_type, "学生"),
        "college": user.college,
        "email": user.email,
        "phone": user.phone,
    }
    if extra:
        # 前端可补充 major / skills / experience 等自由字段
        profile.update({k: v for k, v in extra.items() if v not in (None, "", [])})
    return {k: v for k, v in profile.items() if v not in (None, "")}


def generate_resume(
    db: Session,
    user: SysUser,
    target_job: str = "",
    extra_profile: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """生成简历（返回结构化 JSON + 用量）。

    Args:
        db: 数据库会话（用于 LLM 用量流水落库）
        user: 当前用户
        target_job: 目标岗位
        extra_profile: 前端补充档案
    Returns:
        {"resume": dict, "raw": str|None, "usage": dict, "target_job": str}
    Raises:
        RuntimeError: LLM 调用失败时抛出，由路由层转为 HTTP 错误。
    """
    profile = _build_profile(user, extra_profile)
    prompt = _RESUME_PROMPT.format(profile=json.dumps(profile, ensure_ascii=False), target_job=target_job or "未指定")

    try:
        text, usage = chat_with_usage([{"role": "user", "content": prompt}], temperature=0.3)
    except Exception as exc:  # noqa: BLE001
        logger.warning("generate_resume LLM 调用失败: user=%s err=%s", user.id, exc)
        raise RuntimeError("简历生成失败，请稍后重试") from exc

    usage_info = log_feature_usage(
        db, source=LlmUsageSource.RESUME_GENERATION.value, usage=usage, user_id=user.id
    )

    resume_obj = _safe_parse_json(text)
    return {
        "resume": resume_obj,
        "raw": None if resume_obj is not None else text,
        "usage": usage_info,
        "target_job": target_job,
    }


def _safe_parse_json(text: str) -> Optional[dict[str, Any]]:
    """尽力把 LLM 输出解析为 JSON 对象（容忍包裹的代码块）。失败返回 None。"""
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # 去掉 ```json ... ``` 包裹
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        obj = json.loads(cleaned)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None
