"""P4(会话与反馈) + P5(运营统计) 接口端到端自测（UTF-8 请求体）。

用法：先启动服务(端口8002)，再 python selftest_p45.py
"""

import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
_results: list[tuple[str, bool, str]] = []


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
    _results.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def cleanup():
    from app.core.database import SessionLocal
    from app.models import OpEvalCase, OpSensitiveWord, QaConversation, QaFeedback, QaMessage

    db = SessionLocal()
    # 删自测会话及其消息/反馈
    for c in db.query(QaConversation).filter(QaConversation.title.like("自测会话%")).all():
        mids = [m.id for m in db.query(QaMessage).filter(QaMessage.conversation_id == c.id).all()]
        if mids:
            db.query(QaFeedback).filter(QaFeedback.message_id.in_(mids)).delete(synchronize_session=False)
            db.query(QaMessage).filter(QaMessage.conversation_id == c.id).delete(synchronize_session=False)
        db.delete(c)
    for w in db.query(OpSensitiveWord).filter(OpSensitiveWord.word.like("自测敏感词%")).all():
        db.delete(w)
    for e in db.query(OpEvalCase).filter(OpEvalCase.question.like("自测评测%")).all():
        db.delete(e)
    db.commit()
    db.close()


def seed_message(conversation_id: int) -> int:
    """直接在DB插入一条系统答案消息(P3未实现,手工造数据用于测反馈)。"""
    from app.core.database import SessionLocal
    from app.models import QaMessage

    db = SessionLocal()
    m = QaMessage(conversation_id=conversation_id, role=2, content="自测系统答案内容。", is_no_answer=0)
    db.add(m)
    db.commit()
    mid = m.id
    db.close()
    return mid


cleanup()

st, r = call("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
token = r["data"]["access_token"]
check("登录 admin", st == 200 and token)

# ============ P4 会话与反馈 ============
st, r = call("POST", "/conversations", token=token, body={"title": "自测会话-落户咨询"})
conv_id = r["data"]["id"] if st == 201 else None
check("新建会话", st == 201 and conv_id, f"id={conv_id}")

st, r = call("GET", "/conversations?size=5", token=token)
check("会话列表", st == 200 and r["data"]["total"] >= 1, f"total={r['data']['total']}")

st, r = call("PUT", f"/conversations/{conv_id}", token=token, body={"title": "自测会话-改名"})
check("重命名会话", st == 200 and r["data"]["title"] == "自测会话-改名")

# 造一条系统答案消息
msg_id = seed_message(conv_id)
check("准备答案消息(DB)", msg_id is not None, f"msg_id={msg_id}")

st, r = call("GET", f"/conversations/{conv_id}", token=token)
check("会话详情(含消息)", st == 200 and len(r["data"]["messages"]) == 1)

st, r = call("GET", f"/conversations/{conv_id}/messages", token=token)
check("会话消息列表", st == 200 and len(r["data"]) == 1)

# 反馈：点赞
st, r = call("POST", f"/messages/{msg_id}/feedback", token=token, body={"rating": 1, "reason": "有帮助"})
check("提交反馈(点赞)", st == 200 and r["data"]["rating"] == 1)
# 再次提交改为点踩(upsert)
st, r = call("POST", f"/messages/{msg_id}/feedback", token=token, body={"rating": -1, "reason": "不准确"})
check("反馈upsert(改点踩)", st == 200 and r["data"]["rating"] == -1)
# 非法 rating
st, r = call("POST", f"/messages/{msg_id}/feedback", token=token, body={"rating": 5})
check("非法rating -> 400", st == 400, f"http={st}")

# 引用来源(空)
st, r = call("GET", f"/messages/{msg_id}/references", token=token)
check("查看引用来源", st == 200 and isinstance(r["data"], list))

# 删除会话(软删)后列表不应再出现
st, r = call("DELETE", f"/conversations/{conv_id}", token=token)
check("删除会话(软删)", st == 200)
st, r = call("GET", f"/conversations/{conv_id}", token=token)
check("软删后访问 -> 404", st == 404, f"http={st}")

# ============ P5 运营统计 ============
st, r = call("POST", "/sensitive-words", token=token, body={"word": "自测敏感词X", "category": "测试", "action": 1})
sw_id = r["data"]["id"] if st == 201 else None
check("新建敏感词", st == 201 and sw_id)
st, r = call("POST", "/sensitive-words", token=token, body={"word": "自测敏感词X"})
check("重复敏感词 -> 400", st == 400, f"http={st}")
st, r = call("GET", "/sensitive-words?keyword=" + urllib.parse.quote("自测敏感词"), token=token)
check("敏感词列表", st == 200 and r["data"]["total"] >= 1)
st, r = call("PUT", f"/sensitive-words/{sw_id}", token=token, body={"action": 3})
check("修改敏感词", st == 200 and r["data"]["action"] == 3)

st, r = call("GET", "/logs/queries?size=5", token=token)
check("问答日志列表", st == 200 and "items" in r["data"], f"total={r['data']['total']}")

st, r = call("GET", "/stats/overview", token=token)
ok = st == 200 and "total_questions" in r["data"] and "no_answer_rate" in r["data"]
check("统计概览", ok, f"问答数={r['data'].get('total_questions')} 文档数={r['data'].get('total_documents')}")

st, r = call("GET", "/stats/hot-questions?limit=3", token=token)
check("高频问题排行", st == 200 and isinstance(r["data"], list), f"返回{len(r['data'])}条")

st, r = call("POST", "/eval-cases", token=token, body={"question": "自测评测问题？", "expected_answer": "标准答案", "category": "落户政策"})
ec_id = r["data"]["id"] if st == 201 else None
check("新建评测用例", st == 201 and ec_id)
st, r = call("GET", "/eval-cases?size=5", token=token)
check("评测集列表", st == 200 and r["data"]["total"] >= 1)
st, r = call("PUT", f"/eval-cases/{ec_id}", token=token, body={"expected_answer": "更新答案"})
check("修改评测用例", st == 200 and r["data"]["expected_answer"] == "更新答案")

# 权限：普通用户访问统计应 403
st, r = call("POST", "/auth/login", body={"username": "2021001001", "password": "admin123"})
# 该学生密码未知，尝试失败则跳过该项
if st == 200:
    t2 = r["data"]["access_token"]
    st2, _ = call("GET", "/stats/overview", token=t2)
    check("普通用户访问统计 -> 403", st2 == 403, f"http={st2}")

# 清理
call("DELETE", f"/sensitive-words/{sw_id}", token=token)
call("DELETE", f"/eval-cases/{ec_id}", token=token)
cleanup()

print("\n==== 汇总 ====")
passed = sum(1 for _, c, _ in _results if c)
print(f"通过 {passed}/{len(_results)}  (测试数据已清理)")
