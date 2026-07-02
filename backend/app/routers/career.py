"""学生生涯服务接口：简历生成 / 职位推荐 / 面试日历。

这些是用户主动触发的确定性业务功能，直接走 service 层，不经过 Agent 工作流。
鉴权仅要求登录（前端按角色控制入口；admin 作为超级用户亦可调用）。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.response import success
from app.models import SysUser
from app.schemas.career import CalendarIcsRequest, JobQuery, ResumeGenerateRequest, ResumeListResponse, ResumePDFResponse, ResumeRead, ResumeSaveRequest
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


@router.post("/resume/save", summary="保存简历", response_model=dict)
def save_resume(
    payload: ResumeSaveRequest,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    obj = resume_service.save_resume(
        db,
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        is_default=payload.is_default,
    )
    return success(ResumeRead.model_validate(obj).model_dump(), message="保存成功")


@router.get("/resume/list", summary="我的简历列表")
def list_resumes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    rows, total = resume_service.list_user_resumes(db, current_user.id, page=page, size=size)
    return success(
        {
            "total": total,
            "page": page,
            "size": size,
            "items": [ResumeRead.model_validate(r).model_dump() for r in rows],
        }
    )


@router.delete("/resume/{resume_id}", summary="删除简历")
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    ok = resume_service.delete_user_resume(db, resume_id, current_user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历不存在")
    return success(message="已删除")


@router.post("/resume/{resume_id}/default", summary="设为默认简历")
def set_default(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
) -> dict:
    obj = resume_service.set_default_resume(db, resume_id, current_user.id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="简历不存在")
    return success(ResumeRead.model_validate(obj).model_dump(), message="已设为默认")


@router.get("/resume/{resume_id}/pdf", summary="下载简历 PDF")
def download_resume_pdf(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: SysUser = Depends(get_current_user),
):
    try:
        abs_path, filename = resume_service.generate_resume_pdf(db, resume_id, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    from fastapi.responses import FileResponse
    return FileResponse(abs_path, filename=filename, media_type="application/pdf")


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
