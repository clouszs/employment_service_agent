"""运营·安全·质量业务逻辑：敏感词 / 问答日志 / 统计 / 评测集。"""

import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

import hashlib

logger = logging.getLogger(__name__)

from app.models import (
    Announcement,
    KbDocument,
    KbFaq,
    OpEvalCase,
    OpQueryLog,
    OpSensitiveWord,
    OpUnansweredQuestion,
    QaConversation,
    QaFeedback,
    QaMessage,
)
from app.schemas.ops import (
    EvalCaseCreate,
    EvalCaseUpdate,
    SensitiveWordCreate,
    SensitiveWordUpdate,
)


# ==================== 敏感词缓存 ====================
# 敏感词列表缓存（避免每次请求都查库）
# 注意：只缓存简单数据（word, action），不缓存 ORM 对象，避免 session 绑定问题
_sensitive_words_cache: list[str] = []
_sensitive_word_actions_cache: dict[str, int] = {}  # word -> action
_cache_timestamp: float = 0
_CACHE_TTL: int = 300  # 缓存有效期（秒）
_word_patterns: re.Pattern | None = None  # 预编译的正则表达式


def _get_sensitive_words(db: Session) -> tuple[list[str], dict[str, int]]:
    """获取敏感词列表（带缓存）。

    返回 (words, word_actions) 元组，其中 word_actions 是 {word: action} 字典。
    """
    global _sensitive_words_cache, _sensitive_word_actions_cache, _cache_timestamp, _word_patterns

    now = time.time()
    # 检查缓存是否过期
    if not _sensitive_words_cache or (now - _cache_timestamp) > _CACHE_TTL:
        words = db.execute(select(OpSensitiveWord).where(OpSensitiveWord.status == 1)).scalars().all()
        _sensitive_words_cache = [w.word for w in words if w.word]
        _sensitive_word_actions_cache = {w.word: w.action for w in words if w.word}
        _cache_timestamp = now

        # 预编译正则表达式（用于快速匹配）
        if _sensitive_words_cache:
            pattern = "|".join(re.escape(w) for w in _sensitive_words_cache)
            _word_patterns = re.compile(pattern)
        else:
            _word_patterns = None

    return _sensitive_words_cache, _sensitive_word_actions_cache


def invalidate_sensitive_words_cache() -> None:
    """清除敏感词缓存（在增删改敏感词时调用）。"""
    global _sensitive_words_cache, _sensitive_word_actions_cache, _cache_timestamp, _word_patterns
    _sensitive_words_cache = []
    _sensitive_word_actions_cache = {}
    _cache_timestamp = 0
    _word_patterns = None


# ==================== 敏感词 ====================
def list_sensitive_words(
    db: Session, offset: int, limit: int, keyword: Optional[str] = None, status: Optional[int] = None
) -> tuple[list[OpSensitiveWord], int]:
    stmt = select(OpSensitiveWord)
    if keyword:
        stmt = stmt.where(OpSensitiveWord.word.like(f"%{keyword}%"))
    if status is not None:
        stmt = stmt.where(OpSensitiveWord.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(OpSensitiveWord.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


def get_sensitive_word(db: Session, word_id: int) -> Optional[OpSensitiveWord]:
    return db.get(OpSensitiveWord, word_id)


def get_sensitive_word_by_text(db: Session, word: str) -> Optional[OpSensitiveWord]:
    return db.scalar(select(OpSensitiveWord).where(OpSensitiveWord.word == word))


def moderate(db: Session, text: str) -> dict:
    """敏感词前置检查。

    返回 {action, masked, hits}：
      action: 0无命中 1拦截 2替换 3告警（取命中词中最严处理）
      masked: 命中词替换为 *** 后的文本（用于 action=2）
      hits:   命中的敏感词列表
    """
    # 使用缓存获取敏感词列表
    words, word_actions = _get_sensitive_words(db)

    if not words:
        return {"action": 0, "masked": text, "hits": []}

    # 使用预编译正则快速匹配
    if _word_patterns:
        matches = _word_patterns.findall(text)
        hits = list(set(matches))  # 去重
    else:
        hits = [w for w in words if w in text]

    if not hits:
        return {"action": 0, "masked": text, "hits": []}

    # 替换敏感词
    masked = text
    for w in hits:
        masked = masked.replace(w, "***")

    # 获取最严处理动作（从缓存的字典中读取 action）
    actions = {word_actions.get(w, 3) for w in hits}
    action = 1 if 1 in actions else (2 if 2 in actions else 3)

    return {"action": action, "masked": masked, "hits": list(hits)}


def create_sensitive_word(db: Session, data: SensitiveWordCreate) -> OpSensitiveWord:
    obj = OpSensitiveWord(word=data.word, category=data.category, action=data.action, status=data.status)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # 清除缓存，使新添加的敏感词立即生效
    invalidate_sensitive_words_cache()
    return obj


def update_sensitive_word(db: Session, obj: OpSensitiveWord, data: SensitiveWordUpdate) -> OpSensitiveWord:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    # 清除缓存，使修改立即生效
    invalidate_sensitive_words_cache()
    return obj


def delete_sensitive_word(db: Session, obj: OpSensitiveWord) -> None:
    db.delete(obj)
    db.commit()
    # 清除缓存，使删除立即生效
    invalidate_sensitive_words_cache()


# ==================== 问答日志 ====================
def list_query_logs(
    db: Session,
    offset: int,
    limit: int,
    user_id: Optional[int] = None,
    is_no_answer: Optional[int] = None,
    keyword: Optional[str] = None,
) -> tuple[list[OpQueryLog], int]:
    stmt = select(OpQueryLog)
    if user_id is not None:
        stmt = stmt.where(OpQueryLog.user_id == user_id)
    if is_no_answer is not None:
        stmt = stmt.where(OpQueryLog.is_no_answer == is_no_answer)
    if keyword:
        stmt = stmt.where(OpQueryLog.question.like(f"%{keyword}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(OpQueryLog.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


# ==================== 统计 ====================
def stats_overview(db: Session) -> dict:
    total_questions = db.scalar(select(func.count()).select_from(OpQueryLog)) or 0
    no_answer = db.scalar(
        select(func.count()).select_from(OpQueryLog).where(OpQueryLog.is_no_answer == 1)
    ) or 0
    total_feedback = db.scalar(select(func.count()).select_from(QaFeedback)) or 0
    like_feedback = db.scalar(
        select(func.count()).select_from(QaFeedback).where(QaFeedback.rating == 1)
    ) or 0
    total_documents = db.scalar(select(func.count()).select_from(KbDocument)) or 0
    indexed_documents = db.scalar(
        select(func.count()).select_from(KbDocument).where(KbDocument.index_status == 2)
    ) or 0
    return {
        "total_questions": total_questions,
        "no_answer_rate": round(no_answer / total_questions, 4) if total_questions else 0.0,
        "like_rate": round(like_feedback / total_feedback, 4) if total_feedback else 0.0,
        "total_documents": total_documents,
        "indexed_documents": indexed_documents,
    }


def hot_questions(db: Session, limit: int = 10) -> list[dict]:
    """高频问题：按 OpQueryLog 中实际提问次数排行（模糊去重）。

    出错时返回空列表，绝不抛异常。
    """
    try:
        from rapidfuzz import fuzz
        has_fuzz = True
    except ImportError:
        has_fuzz = False

    # 第一步：精确分组计数，只取干净数据
    try:
        rows = db.execute(
            select(
                OpQueryLog.question,
                func.count().label("cnt"),
            )
            .where(OpQueryLog.question.isnot(None))
            .where(func.length(OpQueryLog.question) > 0)
            .group_by(OpQueryLog.question)
            .order_by(func.count().desc())
            .limit(200)
        ).all()
    except Exception as exc:  # noqa: BLE001
        logger.error("hot_questions 查询失败: %s", exc)
        return []

    if not rows:
        return []

    items = [{"question": str(r[0]), "ask_count": int(r[1])} for r in rows]

    # 第二步：rapidfuzz 模糊合并
    if not has_fuzz:
        return [{"question": i["question"], "ask_count": i["ask_count"]} for i in items[:limit]]

    try:
        merged: list[dict] = []
        for item in items:
            placed = False
            for m in merged:
                try:
                    score = fuzz.ratio(item["question"], m["question"])
                except Exception:  # noqa: BLE001
                    score = 0
                if score > 82:
                    m["ask_count"] += item["ask_count"]
                    placed = True
                    break
            if not placed:
                merged.append({"question": item["question"], "ask_count": item["ask_count"]})
        merged.sort(key=lambda x: x["ask_count"], reverse=True)
        return merged[:limit]
    except Exception as exc:  # noqa: BLE001
        logger.error("hot_questions 模糊合并失败: %s", exc)
        return [{"question": i["question"], "ask_count": i["ask_count"]} for i in items[:limit]]


def recent_activity(db: Session, limit: int = 8) -> list[dict]:
    """最近活动时间线：聚合现有表的近期事件（FAQ新增/文档/公告/反馈），不新建表。"""
    events: list[dict] = []

    for f in db.query(KbFaq).order_by(KbFaq.created_at.desc()).limit(limit).all():
        events.append({"type": "faq", "level": "success", "desc": f"新增 FAQ「{(f.question or '')[:24]}」", "time": f.created_at})
    for d in db.query(KbDocument).order_by(KbDocument.created_at.desc()).limit(limit).all():
        events.append({"type": "document", "level": "info", "desc": f"知识库文档「{(d.title or '')[:24]}」", "time": d.created_at})
    for a in db.query(Announcement).order_by(Announcement.created_at.desc()).limit(limit).all():
        events.append({"type": "announcement", "level": "warning", "desc": f"发布公告「{(a.title or '')[:24]}」", "time": a.created_at})
    for fb in db.query(QaFeedback).order_by(QaFeedback.created_at.desc()).limit(limit).all():
        liked = fb.rating == 1
        events.append({"type": "feedback", "level": "success" if liked else "error",
                       "desc": "用户对回答点赞" if liked else "用户对回答点踩", "time": fb.created_at})

    events = [e for e in events if e["time"] is not None]
    events.sort(key=lambda e: e["time"], reverse=True)
    return [
        {"type": e["type"], "level": e["level"], "desc": e["desc"], "created_at": e["time"].isoformat()}
        for e in events[:limit]
    ]


def stats_daily(db: Session) -> dict:
    """仪表盘日维度 KPI（只读聚合）：今日提问数 / 今日活跃用户 / 今日平均响应时延 / FAQ命中率。"""
    today_start = datetime(date.today().year, date.today().month, date.today().day)

    today_questions = db.scalar(
        select(func.count())
        .select_from(QaMessage)
        .where(QaMessage.role == 1, QaMessage.created_at >= today_start)
    ) or 0

    # 今日活跃用户：今日有提问的会话所属用户去重
    active_users = db.scalar(
        select(func.count(func.distinct(QaConversation.user_id)))
        .select_from(QaMessage)
        .join(QaConversation, QaConversation.id == QaMessage.conversation_id)
        .where(QaMessage.role == 1, QaMessage.created_at >= today_start)
    ) or 0

    avg_latency = db.scalar(
        select(func.avg(QaMessage.latency_ms)).where(
            QaMessage.role == 2,
            QaMessage.created_at >= today_start,
            QaMessage.latency_ms.isnot(None),
        )
    )

    total_answers = db.scalar(
        select(func.count()).select_from(QaMessage).where(QaMessage.role == 2)
    ) or 0
    faq_answers = db.scalar(
        select(func.count())
        .select_from(QaMessage)
        .where(QaMessage.role == 2, QaMessage.answer_type == 2)
    ) or 0

    return {
        "today_questions": int(today_questions),
        "active_users": int(active_users),
        "avg_latency_ms": round(float(avg_latency)) if avg_latency is not None else None,
        "faq_hit_rate": round(faq_answers / total_answers, 4) if total_answers else 0.0,
    }


def stats_trend(db: Session, days: int = 14) -> list[dict]:
    """对话趋势（只读聚合）：最近 N 天每日提问数，缺失日期补 0。"""
    start_day = date.today() - timedelta(days=days - 1)
    start_dt = datetime(start_day.year, start_day.month, start_day.day)

    rows = db.execute(
        select(func.date(QaMessage.created_at), func.count())
        .where(QaMessage.role == 1, QaMessage.created_at >= start_dt)
        .group_by(func.date(QaMessage.created_at))
    ).all()
    counts: dict[str, int] = {str(r[0]): int(r[1]) for r in rows}

    result: list[dict] = []
    for i in range(days):
        d = start_day + timedelta(days=i)
        key = d.isoformat()
        result.append({"date": key, "count": counts.get(key, 0)})
    return result


# ==================== 评测集 ====================
def list_eval_cases(
    db: Session, offset: int, limit: int, category: Optional[str] = None, status: Optional[int] = None
) -> tuple[list[OpEvalCase], int]:
    stmt = select(OpEvalCase)
    if category:
        stmt = stmt.where(OpEvalCase.category == category)
    if status is not None:
        stmt = stmt.where(OpEvalCase.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(OpEvalCase.id.desc()).offset(offset).limit(limit)).scalars().all()
    return list(rows), total


def get_eval_case(db: Session, case_id: int) -> Optional[OpEvalCase]:
    return db.get(OpEvalCase, case_id)


def create_eval_case(db: Session, data: EvalCaseCreate) -> OpEvalCase:
    obj = OpEvalCase(
        question=data.question,
        expected_answer=data.expected_answer,
        expected_doc_id=data.expected_doc_id,
        category=data.category,
        status=data.status,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_eval_case(db: Session, obj: OpEvalCase, data: EvalCaseUpdate) -> OpEvalCase:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_eval_case(db: Session, obj: OpEvalCase) -> None:
    db.delete(obj)
    db.commit()


def run_eval(
    db: Session, top_k: int = 5, category: Optional[str] = None, limit: Optional[int] = None
) -> dict:
    """执行评测：以检索命中率为指标。

    对每条用例用其 question 走向量检索 top_k，若 expected_doc_id 在命中文档中记为命中。
    无 expected_doc_id 的用例跳过不计入指标。
    """
    from app.services import rag_service  # 局部导入避免循环依赖

    stmt = select(OpEvalCase).where(OpEvalCase.status == 1)
    if category:
        stmt = stmt.where(OpEvalCase.category == category)
    stmt = stmt.order_by(OpEvalCase.id)
    if limit:
        stmt = stmt.limit(limit)
    cases = list(db.execute(stmt).scalars().all())

    details = []
    evaluated = 0
    hit_count = 0
    for case in cases:
        hits = rag_service.search(db, case.question, top_k=top_k)
        top_doc_ids = [h["document_id"] for h in hits if h.get("document_id") is not None]
        top_score = hits[0]["score"] if hits else None

        if case.expected_doc_id is None:
            details.append(
                {
                    "case_id": case.id,
                    "question": case.question,
                    "expected_doc_id": None,
                    "hit": False,
                    "hit_rank": None,
                    "top_doc_ids": top_doc_ids,
                    "top_score": top_score,
                }
            )
            continue

        evaluated += 1
        hit_rank = None
        for idx, did in enumerate(top_doc_ids, start=1):
            if did == case.expected_doc_id:
                hit_rank = idx
                break
        is_hit = hit_rank is not None
        if is_hit:
            hit_count += 1
        details.append(
            {
                "case_id": case.id,
                "question": case.question,
                "expected_doc_id": case.expected_doc_id,
                "hit": is_hit,
                "hit_rank": hit_rank,
                "top_doc_ids": top_doc_ids,
                "top_score": top_score,
            }
        )

    skipped = len(cases) - evaluated
    return {
        "total": len(cases),
        "evaluated": evaluated,
        "skipped": skipped,
        "hit_count": hit_count,
        "hit_rate": round(hit_count / evaluated, 4) if evaluated else 0.0,
        "details": details,
    }


# ==================== 无答案问题（专项记录）====================
def record_unanswered(db: Session, question: str, user_id: Optional[int] = None) -> None:
    """记录一条未找到答案的问题；相同问题文本合并并累加出现次数。"""
    q = (question or "").strip()[:1024]
    if not q:
        return
    h = hashlib.sha256(q.encode("utf-8")).hexdigest()
    obj = db.scalar(select(OpUnansweredQuestion).where(OpUnansweredQuestion.question_hash == h))
    if obj is not None:
        obj.ask_count += 1
        obj.last_user_id = user_id
        obj.last_asked_at = datetime.now()
    else:
        db.add(
            OpUnansweredQuestion(
                question=q, question_hash=h, ask_count=1, last_user_id=user_id, status=1
            )
        )
    db.commit()


def list_unanswered(
    db: Session, offset: int, limit: int, status: Optional[int] = None, keyword: Optional[str] = None
) -> tuple[list[OpUnansweredQuestion], int]:
    stmt = select(OpUnansweredQuestion)
    if status is not None:
        stmt = stmt.where(OpUnansweredQuestion.status == status)
    if keyword:
        stmt = stmt.where(OpUnansweredQuestion.question.like(f"%{keyword}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    # 未解决优先 + 出现次数多优先
    rows = (
        db.execute(
            stmt.order_by(OpUnansweredQuestion.status, OpUnansweredQuestion.ask_count.desc())
            .offset(offset)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return list(rows), total


def get_unanswered(db: Session, item_id: int) -> Optional[OpUnansweredQuestion]:
    return db.get(OpUnansweredQuestion, item_id)


def resolve_unanswered(db: Session, obj: OpUnansweredQuestion, status: int, note: Optional[str]) -> OpUnansweredQuestion:
    """标记处理状态(1未解决 2已解决)并写说明。"""
    obj.status = status
    obj.resolve_note = note
    db.commit()
    db.refresh(obj)
    return obj


def delete_unanswered(db: Session, obj: OpUnansweredQuestion) -> None:
    db.delete(obj)
    db.commit()


# ==================== 就业数据统计 ====================


def stats_employment(department: str | None = None, grade: str | None = None) -> dict:
    """就业数据统计(Mock数据) - 学生看全局,教师可按院系/年级筛选。

    返回维度: 就业率趋势 + 行业分布 + 薪资分布 + 地域分布
    """
    # 基础全局数据
    base_data = {
        "employment_trend": [
            {"year": "2021", "rate": 92.3},
            {"year": "2022", "rate": 93.8},
            {"year": "2023", "rate": 94.5},
            {"year": "2024", "rate": 95.2},
        ],
        "industry_distribution": [
            {"industry": "互联网", "count": 350, "percentage": 35.0},
            {"industry": "金融", "count": 200, "percentage": 20.0},
            {"industry": "制造业", "count": 150, "percentage": 15.0},
            {"industry": "教育", "count": 120, "percentage": 12.0},
            {"industry": "其他", "count": 180, "percentage": 18.0},
        ],
        "salary_distribution": [
            {"range": "5-8k", "count": 180},
            {"range": "8-12k", "count": 350},
            {"range": "12-20k", "count": 280},
            {"range": "20-30k", "count": 120},
            {"range": "30k+", "count": 70},
        ],
        "region_distribution": [
            {"region": "北京", "count": 220},
            {"region": "上海", "count": 200},
            {"region": "深圳", "count": 180},
            {"region": "杭州", "count": 150},
            {"region": "广州", "count": 120},
            {"region": "其他", "count": 130},
        ],
    }

    # 教师筛选时调整数据(示例:按比例缩放)
    if department or grade:
        scale = 0.3 if department == "计算机学院" else 0.5
        for item in base_data["industry_distribution"]:
            item["count"] = int(item["count"] * scale)
        for item in base_data["salary_distribution"]:
            item["count"] = int(item["count"] * scale)
        for item in base_data["region_distribution"]:
            item["count"] = int(item["count"] * scale)

    return base_data
