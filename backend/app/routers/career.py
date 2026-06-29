"""学生生涯服务接口：简历生成 / 职位推荐 / 面试日历。

这些是用户主动触发的确定性业务功能，直接走 service 层，不经过 Agent 工作流。
鉴权仅要求登录（前端按角色控制入口；admin 作为超级用户亦可调用）。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import SysUser
from app.schemas.career import CalendarIcsRequest, JobQuery, ResumeGenerateRequest
from app.services import calendar_service, job_service, resume_service

router = APIRouter(prefix="/career", tags=["学生-生涯服务"])


@router.post("/resume", summary="生成简历（结构化 JSON）")
def generate_resume(
    payload: ResumeGenerateRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    try:
        result = resume_service.generate_resume(
            db, current_user, target_job=payload.target_job, extra_profile=payload.extra_profile
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return success(result)


@router.post("/jobs", summary="职位推荐（基于知识库检索）")
def recommend_jobs(
    payload: JobQuery,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    jobs = job_service.recommend_jobs(
        db, query=payload.query, top_k=payload.top_k, location=payload.location
    )
    return success({"items": jobs, "count": len(jobs), "query": payload.query})


@router.post("/calendar/ics", summary="生成面试日程 ICS")
def create_calendar_ics(
    payload: CalendarIcsRequest,
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    try:
        result = calendar_service.build_ics(
            title=payload.title,
            start_time=payload.start_time,
            end_time=payload.end_time,
            location=payload.location,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return success(result)
