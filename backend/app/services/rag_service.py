"""RAG 核心服务：检索 / 组装提示 / 问答(同步+流式) / 落库。

策略：纯向量检索 Top-K；最高分低于阈值走"无法回答"兜底，不调 LLM 编造。
落库：写入 qa_message(问与答) + qa_message_reference(引用溯源) + op_query_log。
支持从系统配置读取检索参数，未配置时回退到 settings 默认值。

FAQ 命中链路（分两步）：
  1. 语义匹配：向量检索 FAQ 集合，相似度达标 → 直接返回标准答案，并累加 hit_count。
  2. 模糊匹配：语义未命中时，用 rapidfuzz 对所有启用的 FAQ 问题做模糊匹配，
     达到阈值 → 视为"有效问题命中"，累加 ask_count（不直接返回答案，仍走检索/LLM）。
"""

import logging
import time
from datetime import datetime
from typing import Iterator, Optional

from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core import llm, vectorstore
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.embedding import embed_query
from app.models import (
    KbDocument,
    KbFaq,
    OpQueryLog,
    QaConversation,
    QaMessage,
    QaMessageReference,
)
from app.services import app_config_service, ops_service
from app.utils.conversation import resolve_conversation

logger = logging.getLogger(__name__)

# LLM 调用重试配置
_LLM_RETRY_ATTEMPTS = 3
_LLM_RETRY_MIN_WAIT = 2  # 秒
_LLM_RETRY_MAX_WAIT = 10  # 秒

# 统一的温柔拒答文案（检索未召回 / 资料不足 两条路径共用）
_NO_ANSWER_TEXT = (
    "很抱歉呀，目前的就业资料里暂时没有找到能回答这个问题的内容～"
    "您可以换个说法再问我，或者咨询就业指导中心的老师，他们会很乐意帮您解答的。"
)
_BLOCKED_TEXT = "您的提问包含不当或违规内容，已被系统拦截，请调整后重新提问。"

_SYSTEM_PROMPT = (
    "## 角色\n"
    "你是一个严格、友好的就业信息检索助手。你**没有**任何关于就业政策的自有知识，"
    "你的全部知识仅来源于【参考资料】中的文本片段。\n"
    "## 规则（必须严格遵守）\n"
    "1. **绝对禁用自己的常识和已知信息**。即使你知道某个政策，只要参考资料里没写，就视为你不知道。\n"
    "2. 回答问题时，**只能**从【参考资料】中提取相关信息，并用参考资料中的原话或最小改述来组织答案，"
    "语气亲切自然。\n"
    "3. 如果【参考资料】中没有提供足以回答问题的信息，或者只有部分信息但无法完全覆盖，"
    f"你必须温柔地回答：“{_NO_ANSWER_TEXT}” 不得进行任何推测、补充或扩展。\n"
    "4. 不要添加任何解释背景、延伸建议或“另外需要注意”等内容——除非参考资料里明确写了这些。\n"
    "5. 回答中若涉及事实陈述，可以（但非必须）指出其来自参考资料的第几条，以确保可溯源。"
)


# ==================== 配置读取 ====================
def _get_int_config(db: Session, key: str, default: int) -> int:
    """读取整数配置，失败时返回默认值。"""
    try:
        val = app_config_service.get_qa_config_value(db, key)
        if val is not None:
            return int(val)
    except Exception as e:  # pragma: no cover - 防御性降级
        logger.warning("读取配置失败 key=%s: %s", key, e)
    return default


def _get_float_config(db: Session, key: str, default: float) -> float:
    """读取浮点配置，失败时返回默认值。"""
    try:
        val = app_config_service.get_qa_config_value(db, key)
        if val is not None:
            return float(val)
    except Exception as e:  # pragma: no cover - 防御性降级
        logger.warning("读取配置失败 key=%s: %s", key, e)
    return default


# ==================== 检索 ====================
def search(db: Session, query: str, top_k: Optional[int] = None) -> list[dict]:
    """向量检索，返回命中片段(含文档标题，用于展示与溯源)。"""
    if top_k is None:
        top_k = _get_int_config(db, "qa_retrieval.top_k", settings.retrieve_top_k)
    k = int(top_k)
    qvec = embed_query(query)
    hits = vectorstore.query(qvec, top_k=k)

    # 回查文档标题
    doc_ids = {h["metadata"].get("document_id") for h in hits if h.get("metadata")}
    title_map = {}
    if doc_ids:
        for d in db.query(KbDocument).filter(KbDocument.id.in_(doc_ids)).all():
            title_map[d.id] = d.title

    results = []
    for h in hits:
        meta = h.get("metadata") or {}
        did = meta.get("document_id")
        page = meta.get("page_no")
        results.append(
            {
                "chunk_id": meta.get("chunk_id"),
                "document_id": did,
                "document_title": title_map.get(did),
                "content": h.get("document") or "",
                "score": h.get("score"),
                "page_no": page if page not in (None, -1) else None,
            }
        )
    return results


def faq_match(db: Session, query: str) -> Optional[tuple[KbFaq, float]]:
    """FAQ 语义匹配：相似度达阈值则返回 (FAQ, score)，否则 None。"""
    qvec = embed_query(query)
    top_k = _get_int_config(db, "qa_retrieval.faq_top_k", 1)
    hits = vectorstore.query(qvec, top_k=max(1, top_k), collection=settings.faq_collection)
    if not hits:
        return None
    top = hits[0]
    score = top.get("score")
    threshold = _get_float_config(db, "qa_retrieval.faq_score_threshold", settings.faq_score_threshold)
    if score is None or score < threshold:
        return None
    faq_id = (top.get("metadata") or {}).get("faq_id")
    faq = db.get(KbFaq, faq_id) if faq_id else None
    if faq and faq.status == 1:
        return faq, score
    return None


def _faq_fuzzy_match(db: Session, query: str, threshold: int = 70) -> Optional[tuple[int, str]]:
    """FAQ 模糊匹配：对全部启用 FAQ 做 rapidfuzz 相似度计算，达标则返回 (id, question)。

    用于语义匹配未命中时，补录"有效问题"统计。
    采用缓存全量 FAQ 问题到内存的方案，避免 N+1 查询。
    """
    from rapidfuzz import fuzz

    rows = db.execute(select(KbFaq.id, KbFaq.question).where(KbFaq.status == 1)).all()
    if not rows:
        return None

    q = (query or "").strip()
    best_id: Optional[int] = None
    best_question: Optional[str] = None
    best_score = threshold
    for row_id, row_question in rows:
        score = fuzz.ratio(q, row_question)
        if score > best_score:
            best_score = score
            best_id = row_id
            best_question = row_question
    if best_id is not None:
        return best_id, best_question  # type: ignore[return-value]
    return None


def _build_messages(query: str, hits: list[dict]) -> list[dict]:
    """组装 LLM 提示：系统约束 + 编号参考资料 + 用户问题。"""
    blocks = []
    for i, h in enumerate(hits, start=1):
        src = h.get("document_title") or "未知来源"
        page = f" 第{h['page_no']}页" if h.get("page_no") else ""
        blocks.append(f"[{i}] 来源：《{src}》{page}\n{h['content']}")
    context = "\n\n".join(blocks)
    user_content = (
        f"## 参考资料\n{context}\n\n"
        f"## 用户问题\n{query}\n\n"
        f"## 你的回答（严格遵守上述规则）"
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


# ==================== 会话与落库辅助 ====================
# resolve_conversation 已移至 app.utils.conversation.resolve_conversation


def _save_qa(
    db: Session,
    conv: QaConversation,
    question: str,
    answer: str,
    hits: list[dict],
    is_no_answer: bool,
    latency_ms: int,
    user_id: int,
    client_ip: Optional[str] = None,
    answer_type: Optional[int] = None,
    llm_model: Optional[str] = None,
) -> QaMessage:
    """写入 用户提问消息 + 系统回答消息 + 引用 + 日志，返回回答消息。

    answer_type: 1知识库生成 2FAQ命中 3无答案兜底；为空则按 is_no_answer 推断。
    """
    if answer_type is None:
        answer_type = 3 if is_no_answer else 1
    db.add(QaMessage(conversation_id=conv.id, role=1, content=question))
    answer_msg = QaMessage(
        conversation_id=conv.id,
        role=2,
        content=answer,
        answer_type=answer_type,
        is_no_answer=1 if is_no_answer else 0,
        llm_model=llm_model,
        latency_ms=latency_ms,
    )
    db.add(answer_msg)
    db.commit()
    db.refresh(answer_msg)

    if not is_no_answer:
        for rank, h in enumerate(hits, start=1):
            db.add(
                QaMessageReference(
                    message_id=answer_msg.id,
                    document_id=h.get("document_id"),
                    chunk_id=h.get("chunk_id"),
                    score=h.get("score"),
                    rank_no=rank,
                    snippet=(h.get("content") or "")[:300],
                )
            )
    db.add(
        OpQueryLog(
            user_id=user_id,
            conversation_id=conv.id,
            message_id=answer_msg.id,
            question=question[:1024],
            answer_brief=answer[:2048],
            hit_doc_count=len(hits),
            is_no_answer=1 if is_no_answer else 0,
            latency_ms=latency_ms,
            client_ip=client_ip,
            channel="web",
        )
    )
    db.commit()
    db.refresh(answer_msg)
    return answer_msg


def _is_no_answer(db: Session, hits: list[dict]) -> bool:
    if not hits:
        return True
    top = hits[0].get("score")
    threshold = _get_float_config(db, "qa_retrieval.score_threshold", settings.retrieve_score_threshold)
    return top is None or top < threshold


def _is_llm_no_answer(answer: str) -> bool:
    """LLM 看了资料后判定无法回答，输出了兜底语（检索没兜底但 LLM 说不知道）。"""
    a = (answer or "").strip()
    return a == _NO_ANSWER_TEXT or _NO_ANSWER_TEXT[:12] in a


# ==================== 同步问答 ====================
def ask(
    db: Session, user_id: int, question: str, conversation_id: Optional[int] = None, client_ip: Optional[str] = None
) -> dict:
    """一次性问答：敏感词过滤→检索→(兜底或生成)→落库，返回结果。"""
    start = datetime.now()

    # 敏感词前置过滤
    mod = ops_service.moderate(db, question)
    if mod["action"] == 1:  # 拦截
        conv = resolve_conversation(db, user_id, conversation_id, question)
        latency = int((datetime.now() - start).total_seconds() * 1000)
        answer_msg = _save_qa(db, conv, question, _BLOCKED_TEXT, [], True, latency, user_id, client_ip)
        return {
            "conversation_id": conv.id,
            "message_id": answer_msg.id,
            "answer": _BLOCKED_TEXT,
            "is_no_answer": True,
            "blocked": True,
            "references": [],
        }
    if mod["action"] == 2:  # 替换后继续
        question = mod["masked"]

    # FAQ 命中优先：问法相似度达阈值，直接返回标准答案，不走 LLM
    faq_hit = faq_match(db, question)
    if faq_hit is not None:
        faq, _score = faq_hit
        conv = resolve_conversation(db, user_id, conversation_id, question)
        faq.hit_count = (faq.hit_count or 0) + 1
        latency = int((datetime.now() - start).total_seconds() * 1000)
        answer_msg = _save_qa(
            db, conv, question, faq.answer, [], False, latency, user_id, client_ip, answer_type=2
        )
        return {
            "conversation_id": conv.id,
            "message_id": answer_msg.id,
            "answer": faq.answer,
            "is_no_answer": False,
            "blocked": False,
            "from_faq": True,
            "references": [],
        }

    # FAQ 模糊命中（语义未达标但问法相近）：补录 ask_count，继续走检索/LLM
    _FAQ_FUZZY_THRESHOLD = _get_int_config(db, "qa_retrieval.faq_fuzzy_threshold", 70)
    faq_fuzzy = _faq_fuzzy_match(db, question, threshold=_FAQ_FUZZY_THRESHOLD)
    if faq_fuzzy is not None:
        fuzzy_id, _ = faq_fuzzy
        db_faq = db.get(KbFaq, fuzzy_id)
        if db_faq and db_faq.status == 1:
            db_faq.ask_count = (db_faq.ask_count or 0) + 1
            db.commit()

    hits = search(db, question)
    conv = resolve_conversation(db, user_id, conversation_id, question)

    if _is_no_answer(db, hits):
        answer, no_answer, used_hits = _NO_ANSWER_TEXT, True, []
        llm_used = None
        ops_service.record_unanswered(db, question, user_id)  # 专项记录无答案问题
    else:
        # 带重试的 LLM 调用
        try:
            answer = _chat_with_retry(_build_messages(question, hits))
            no_answer, used_hits, llm_used = False, hits, _get_model(db)
            if _is_llm_no_answer(answer):  # 检索有内容但 LLM 判定资料不足 → 也算无答案
                no_answer, used_hits = True, []
                ops_service.record_unanswered(db, question, user_id)
        except Exception as e:
            # LLM 服务不可用时的降级策略
            logger.error("LLM调用失败，降级返回无答案: %s", str(e))
            answer, no_answer, used_hits = _NO_ANSWER_TEXT, True, []
            llm_used = None
            ops_service.record_unanswered(db, question, user_id)

    latency = int((datetime.now() - start).total_seconds() * 1000)
    answer_msg = _save_qa(
        db, conv, question, answer, used_hits, no_answer, latency, user_id, client_ip, llm_model=llm_used
    )

    refs = []
    if not no_answer:
        for rank, h in enumerate(used_hits, start=1):
            refs.append(
                {
                    "document_id": h.get("document_id"),
                    "document_title": h.get("document_title"),
                    "chunk_id": h.get("chunk_id"),
                    "score": h.get("score"),
                    "rank_no": rank,
                    "page_no": h.get("page_no"),
                    "snippet": (h.get("content") or "")[:300],
                }
            )
    return {
        "conversation_id": conv.id,
        "message_id": answer_msg.id,
        "answer": answer,
        "is_no_answer": no_answer,
        "blocked": False,
        "from_faq": False,
        "references": refs,
    }


# ==================== 流式问答 ====================
def ask_stream(
    user_id: int, question: str, conversation_id: Optional[int] = None, client_ip: Optional[str] = None
) -> Iterator[dict]:
    """流式问答：先产出 token 增量，最后产出 done 事件(含会话/消息/引用)。

    自带独立 DB 会话(流式响应期间需持续可用)。产出 dict 事件，由路由序列化为 SSE。
    """
    db = SessionLocal()
    try:
        start = datetime.now()

        # 敏感词前置过滤
        mod = ops_service.moderate(db, question)
        if mod["action"] == 1:  # 拦截
            conv = resolve_conversation(db, user_id, conversation_id, question)
            yield {"event": "delta", "data": _BLOCKED_TEXT}
            latency = int((datetime.now() - start).total_seconds() * 1000)
            answer_msg = _save_qa(db, conv, question, _BLOCKED_TEXT, [], True, latency, user_id, client_ip)
            yield {
                "event": "done",
                "data": {
                    "conversation_id": conv.id,
                    "message_id": answer_msg.id,
                    "is_no_answer": True,
                    "blocked": True,
                    "references": [],
                },
            }
            return
        if mod["action"] == 2:  # 替换后继续
            question = mod["masked"]

        # FAQ 命中优先：直接整段返回标准答案
        faq_hit = faq_match(db, question)
        if faq_hit is not None:
            faq, _score = faq_hit
            conv = resolve_conversation(db, user_id, conversation_id, question)
            faq.hit_count = (faq.hit_count or 0) + 1
            yield {"event": "delta", "data": faq.answer}
            latency = int((datetime.now() - start).total_seconds() * 1000)
            answer_msg = _save_qa(
                db, conv, question, faq.answer, [], False, latency, user_id, client_ip, answer_type=2
            )
            yield {
                "event": "done",
                "data": {
                    "conversation_id": conv.id,
                    "message_id": answer_msg.id,
                    "is_no_answer": False,
                    "blocked": False,
                    "from_faq": True,
                    "references": [],
                },
            }
            return

        # FAQ 模糊命中（语义未达标但问法相近）：补录 ask_count，继续走检索/LLM
        _FAQ_FUZZY_THRESHOLD = _get_int_config(db, "qa_retrieval.faq_fuzzy_threshold", 70)
        faq_fuzzy = _faq_fuzzy_match(db, question, threshold=_FAQ_FUZZY_THRESHOLD)
        if faq_fuzzy is not None:
            fuzzy_id, _ = faq_fuzzy
            db_faq = db.get(KbFaq, fuzzy_id)
            if db_faq and db_faq.status == 1:
                db_faq.ask_count = (db_faq.ask_count or 0) + 1
                db.commit()

        hits = search(db, question)
        conv = resolve_conversation(db, user_id, conversation_id, question)

        if _is_no_answer(db, hits):
            answer, no_answer, used_hits, llm_used = _NO_ANSWER_TEXT, True, [], None
            ops_service.record_unanswered(db, question, user_id)  # 专项记录无答案问题
            # 逐字、有节奏地输出兜底语，呈现打字机效果
            for ch in answer:
                yield {"event": "delta", "data": ch}
                time.sleep(0.03)
        else:
            no_answer, used_hits, llm_used = False, hits, _get_model(db)
            buf = []
            try:
                for piece in _chat_stream_with_retry(_build_messages(question, hits)):
                    buf.append(piece)
                    yield {"event": "delta", "data": piece}
                answer = "".join(buf)
                if _is_llm_no_answer(answer):  # 检索有内容但 LLM 判定资料不足 → 也算无答案
                    no_answer, used_hits = True, []
                    ops_service.record_unanswered(db, question, user_id)
            except Exception as e:
                # LLM 服务不可用时的降级策略
                logger.error("流式LLM调用失败，降级返回无答案: %s", str(e))
                answer = _NO_ANSWER_TEXT
                no_answer, used_hits, llm_used = True, [], None
                ops_service.record_unanswered(db, question, user_id)
                # 输出降级提示
                for ch in answer:
                    yield {"event": "delta", "data": ch}
                    time.sleep(0.03)

        latency = int((datetime.now() - start).total_seconds() * 1000)
        answer_msg = _save_qa(
            db, conv, question, answer, used_hits, no_answer, latency, user_id, client_ip, llm_model=llm_used
        )

        refs = []
        if not no_answer:
            for rank, h in enumerate(used_hits, start=1):
                refs.append(
                    {
                        "document_id": h.get("document_id"),
                        "document_title": h.get("document_title"),
                        "chunk_id": h.get("chunk_id"),
                        "score": h.get("score"),
                        "rank_no": rank,
                        "page_no": h.get("page_no"),
                        "snippet": (h.get("content") or "")[:300],
                    }
                )
        yield {
            "event": "done",
            "data": {
                "conversation_id": conv.id,
                "message_id": answer_msg.id,
                "is_no_answer": no_answer,
                "blocked": False,
                "from_faq": False,
                "references": refs,
            },
        }
    finally:
        db.close()


# ==================== LLM 调用辅助函数（带重试）====================
def _get_model(db: Session) -> str | None:
    """读取模型配置，失败时返回 settings 默认值。"""
    val = app_config_service.get_qa_config_value(db, "qa_model.model", settings.llm_model)
    return val or settings.llm_model


def _chat_with_retry(messages: list[dict]) -> str:
    """带重试的同步 LLM 调用。"""
    db = SessionLocal()
    try:
        temperature = _get_float_config(db, "qa_model.temperature", 0.3)
        max_tokens = _get_int_config(db, "qa_model.max_tokens", 0)
        model = _get_model(db)
    finally:
        db.close()

    kwargs: dict[str, Any] = {}
    if max_tokens > 0:
        kwargs["max_tokens"] = max_tokens

    @retry(
        stop=stop_after_attempt(_LLM_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=_LLM_RETRY_MIN_WAIT, max=_LLM_RETRY_MAX_WAIT),
        reraise=True,
        before_sleep=lambda retry_state: logger.warning(
            "LLM调用失败，第%d次重试中... (等待%d秒)",
            retry_state.attempt_number,
            _LLM_RETRY_MIN_WAIT * (2 ** (retry_state.attempt_number - 1)),
        ),
    )
    def _call():
        return llm.chat(messages, temperature=temperature, model=model, **kwargs)

    return _call()


def _chat_stream_with_retry(messages: list[dict]) -> Iterator[str]:
    """带重试的流式 LLM 调用。"""
    db = SessionLocal()
    try:
        temperature = _get_float_config(db, "qa_model.temperature", 0.3)
        max_tokens = _get_int_config(db, "qa_model.max_tokens", 0)
        model = _get_model(db)
    finally:
        db.close()

    kwargs: dict[str, Any] = {}
    if max_tokens > 0:
        kwargs["max_tokens"] = max_tokens

    attempt = 0

    while attempt < _LLM_RETRY_ATTEMPTS:
        attempt += 1
        try:
            yield from llm.chat_stream(messages, temperature=temperature, model=model, **kwargs)
            return
        except Exception as e:
            if attempt >= _LLM_RETRY_ATTEMPTS:
                logger.error("流式LLM调用最终失败，已达最大重试次数: %s", str(e))
                raise
            wait_time = _LLM_RETRY_MIN_WAIT * (2 ** (attempt - 1))
            logger.warning(
                "流式LLM调用失败，第%d次重试中... (等待%d秒): %s",
                attempt,
                wait_time,
                str(e),
            )
            time.sleep(wait_time)
