"""简历生成服务（学生自助）。

由 REST 端点直接调用，不经过 Agent 工作流：简历生成是用户主动触发的确定性
业务功能，不需要 Agent 的意图路由/检索。LLM 调用走 chat_with_usage，并通过
llm_usage.log_feature_usage 记录用量（审计链路）。

新增：保存/列表/删除/默认设置 + PDF 生成（reportlab）。
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.llm import chat_with_usage
from app.models import LlmUsageSource, SysUser, UserResume
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


# ==================== 简历持久化 ====================

_RESUME_STORAGE_DIR = getattr(settings, "resume_storage_dir", "storage/resumes")


def save_resume(
    db: Session,
    user_id: int,
    title: str,
    content: dict[str, Any],
    is_default: bool = False,
) -> UserResume:
    """保存一份简历（JSON 入库）。"""
    if is_default:
        # 取消同用户其他默认
        db.execute(
            UserResume.__table__.update().where(UserResume.user_id == user_id).values(is_default=0)
        )
    obj = UserResume(
        user_id=user_id,
        title=title,
        content=json.dumps(content, ensure_ascii=False),
        is_default=1 if is_default else 0,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_user_resumes(db: Session, user_id: int, page: int = 1, size: int = 20) -> tuple[list[UserResume], int]:
    """列出用户所有简历（按更新时间倒序）。"""
    stmt = select(UserResume).where(UserResume.user_id == user_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        db.execute(stmt.order_by(UserResume.updated_at.desc()).offset((page - 1) * size).limit(size))
        .scalars()
        .all()
    )
    return list(rows), total


def get_user_resume(db: Session, resume_id: int, user_id: int) -> Optional[UserResume]:
    """获取单份简历（校验归属）。"""
    return db.scalar(select(UserResume).where(UserResume.id == resume_id, UserResume.user_id == user_id))


def delete_user_resume(db: Session, resume_id: int, user_id: int) -> bool:
    """删除简历（校验归属）。"""
    obj = db.scalar(select(UserResume).where(UserResume.id == resume_id, UserResume.user_id == user_id))
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


def set_default_resume(db: Session, resume_id: int, user_id: int) -> Optional[UserResume]:
    """设为默认简历（取消其他默认）。"""
    obj = db.scalar(select(UserResume).where(UserResume.id == resume_id, UserResume.user_id == user_id))
    if obj is None:
        return None
    db.execute(
        UserResume.__table__.update().where(UserResume.user_id == user_id).values(is_default=0)
    )
    obj.is_default = 1
    db.commit()
    db.refresh(obj)
    return obj


# ==================== PDF 生成 ====================

def generate_resume_pdf(db: Session, resume_id: int, user_id: int) -> tuple[str, str]:
    """根据已保存的简历 JSON 生成 PDF 文件，返回 (文件绝对路径, 下载文件名)。

    使用 reportlab 生成 A4 排版 PDF，存储到 storage/resumes/ 目录。
    返回路径供路由层做 FileResponse 下载。
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    obj = db.scalar(select(UserResume).where(UserResume.id == resume_id, UserResume.user_id == user_id))
    if obj is None:
        raise ValueError("简历不存在")

    try:
        content = json.loads(obj.content) if isinstance(obj.content, str) else obj.content
    except json.JSONDecodeError:
        content = {}

    # 确保存储目录存在
    os.makedirs(_RESUME_STORAGE_DIR, exist_ok=True)
    filename = f"resume_{user_id}_{resume_id}_{uuid.uuid4().hex[:8]}.pdf"
    abs_path = os.path.join(_RESUME_STORAGE_DIR, filename)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ResumeTitle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1e293b"), spaceAfter=6
    )
    heading_style = ParagraphStyle(
        "ResumeHeading", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#334155"), spaceAfter=4, spaceBefore=10
    )
    body_style = ParagraphStyle(
        "ResumeBody", parent=styles["BodyText"], fontSize=10, textColor=colors.HexColor("#374151"), leading=16
    )
    small_style = ParagraphStyle(
        "ResumeSmall", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#6b7280"), leading=14
    )

    story = []

    # 姓名 + 联系方式
    basics = content.get("basics", {})
    name = basics.get("name", "姓名")
    story.append(Paragraph(f"<b>{name}</b>", title_style))
    contact_parts = [v for v in [basics.get("title"), basics.get("email"), basics.get("phone"), basics.get("location")] if v]
    if contact_parts:
        story.append(Paragraph(" | ".join(contact_parts), small_style))
    story.append(Spacer(1, 4 * mm))

    # 个人简介
    if content.get("summary"):
        story.append(Paragraph("个人简介", heading_style))
        story.append(Paragraph(content["summary"], body_style))
        story.append(Spacer(1, 2 * mm))

    # 教育经历
    if content.get("education"):
        story.append(Paragraph("教育经历", heading_style))
        for edu in content["education"]:
            school = edu.get("school", "")
            major = edu.get("major", "")
            degree = edu.get("degree", "")
            period = edu.get("period", "")
            header = f"<b>{school}</b> - {major} | {degree}"
            if period:
                header += f" | {period}"
            story.append(Paragraph(header, body_style))
        story.append(Spacer(1, 2 * mm))

    # 工作/实习经历
    if content.get("experience"):
        story.append(Paragraph("工作经历", heading_style))
        for exp in content["experience"]:
            org = exp.get("org", "")
            role = exp.get("role", "")
            period = exp.get("period", "")
            header = f"<b>{org}</b> - {role}"
            if period:
                header += f" | {period}"
            story.append(Paragraph(header, body_style))
            highlights = exp.get("highlights", [])
            if highlights:
                for h in highlights:
                    story.append(Paragraph(f"• {h}", body_style))
        story.append(Spacer(1, 2 * mm))

    # 技能
    if content.get("skills"):
        story.append(Paragraph("技能", heading_style))
        skills = content["skills"]
        if isinstance(skills, list):
            story.append(Paragraph("、".join(str(s) for s in skills), body_style))
        else:
            story.append(Paragraph(str(skills), body_style))
        story.append(Spacer(1, 2 * mm))

    # 项目经历
    if content.get("projects"):
        story.append(Paragraph("项目经历", heading_style))
        for proj in content["projects"]:
            name = proj.get("name", "")
            desc = proj.get("desc", "")
            header = f"<b>{name}</b>"
            story.append(Paragraph(header, body_style))
            if desc:
                story.append(Paragraph(desc, body_style))
            highlights = proj.get("highlights", [])
            if highlights:
                for h in highlights:
                    story.append(Paragraph(f"• {h}", body_style))

    # 生成 PDF
    doc = SimpleDocTemplate(abs_path, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=20 * mm, bottomMargin=20 * mm)
    doc.build(story)

    # 更新数据库中的 pdf_path（相对路径）
    rel_path = os.path.relpath(abs_path, ".")
    obj.pdf_path = rel_path
    db.commit()

    download_name = f"{obj.title or name}.pdf"
    return abs_path, download_name
