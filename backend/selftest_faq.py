"""FAQ 命中优先自测：增改自动入库 / 语义命中直返 / 未命中走RAG / 删除清向量。

用法：先启动服务(端口8000)，再 python selftest_faq.py
"""

import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
results = []


def call(method, path, token=None, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, None


def check(name, cond, detail=""):
    results.append((name, cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def cleanup():
    from app.core.database import SessionLocal
    from app.models import KbFaq, OpQueryLog, QaConversation, QaMessage, QaMessageReference
    from app.services.knowledge_service import _remove_faq_vector

    db = SessionLocal()
    for f in db.query(KbFaq).filter(KbFaq.question.like("FAQ自测%")).all():
        _remove_faq_vector(f.id)
        db.delete(f)
    for c in db.query(QaConversation).filter(QaConversation.title.like("%三方协议%") | QaConversation.title.like("%违约%")).all():
        mids = [m.id for m in db.query(QaMessage).filter(QaMessage.conversation_id == c.id).all()]
        if mids:
            db.query(QaMessageReference).filter(QaMessageReference.message_id.in_(mids)).delete(synchronize_session=False)
            db.query(OpQueryLog).filter(OpQueryLog.message_id.in_(mids)).delete(synchronize_session=False)
            db.query(QaMessage).filter(QaMessage.conversation_id == c.id).delete(synchronize_session=False)
        db.delete(c)
    db.commit()
    db.close()


cleanup()
st, r = call("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
token = r["data"]["access_token"]
check("登录 admin", st == 200 and token)

# 建 FAQ（创建即自动向量化入库）
st, r = call("POST", "/faqs", token=token, body={
    "question": "FAQ自测：三方协议违约金最多是多少？",
    "answer": "三方协议违约金一般不超过五千元，具体以协议约定为准。",
})
fid = r["data"]["id"] if st == 201 else None
vec_id = r["data"].get("vector_id") if fid else None
check("新建FAQ", st == 201 and fid)
check("FAQ创建即自动入库(有vector_id)", bool(vec_id), f"vector_id={vec_id}")

# 换个问法提问 -> 应命中 FAQ，直接返回标准答案(不走LLM)
st, r = call("POST", "/ask", token=token, body={"question": "请问三方协议的违约金最高多少钱呀"})
d = r["data"]
check("换问法命中FAQ", st == 200 and d.get("from_faq") is True and "五千元" in d["answer"],
      f"from_faq={d.get('from_faq')} 答:{d['answer'][:25]}")
check("FAQ命中不带文档引用", len(d["references"]) == 0)

# 落库验证：该回答 answer_type 应为 2(FAQ命中)
from app.core.database import SessionLocal
from app.models import QaMessage
_db = SessionLocal()
msg = _db.get(QaMessage, d["message_id"])
check("FAQ答案 answer_type=2", msg is not None and msg.answer_type == 2, f"answer_type={msg.answer_type if msg else None}")
# hit_count 应+1
from app.models import KbFaq
faq_obj = _db.get(KbFaq, fid)
check("FAQ命中计数+1", faq_obj.hit_count >= 1, f"hit_count={faq_obj.hit_count}")
_db.close()

# 完全无关问题 -> 不命中FAQ，走RAG（知识库也没有→兜底）
st, r = call("POST", "/ask", token=token, body={"question": "今天天气怎么样"})
d = r["data"]
check("无关问题不命中FAQ", st == 200 and not d.get("from_faq"), f"from_faq={d.get('from_faq')}")

# 修改 FAQ 问题 -> 向量应更新（用新问法仍能命中）
st, r = call("PUT", f"/faqs/{fid}", token=token, body={"question": "FAQ自测：报到证丢了如何补办？"})
check("修改FAQ问题", st == 200)
st, r = call("POST", "/ask", token=token, body={"question": "报到证不见了怎么重新办理"})
check("改问法后新问题能命中", st == 200 and r["data"].get("from_faq") is True,
      f"from_faq={r['data'].get('from_faq')}")

cleanup()
print("\n==== 汇总 ====")
passed = sum(1 for _, c in results if c)
print(f"通过 {passed}/{len(results)}  (测试数据已清理)")
