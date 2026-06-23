"""敏感词前置过滤自测：拦截 / 替换 / 正常放行（同步+流式）。

用法：先启动服务(端口8000)，再 python selftest_moderation.py
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


def stream_done(path, token, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    full, done, ev = "", None, None
    with urllib.request.urlopen(req) as resp:
        for raw in resp:
            line = raw.decode("utf-8").rstrip("\n")
            if line.startswith("event: "):
                ev = line[7:]
            elif line.startswith("data: "):
                if ev == "delta":
                    full += line[6:]
                elif ev == "done":
                    done = json.loads(line[6:])
    return full, done


def check(name, cond, detail=""):
    results.append((name, cond))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def cleanup():
    from app.core.database import SessionLocal
    from app.models import OpSensitiveWord, QaConversation, QaMessage, QaMessageReference, OpQueryLog

    db = SessionLocal()
    for w in db.query(OpSensitiveWord).filter(OpSensitiveWord.word.in_(["赌博测试", "替换测试词"])).all():
        db.delete(w)
    for c in db.query(QaConversation).filter(QaConversation.title.like("%赌博测试%") | QaConversation.title.like("%***%")).all():
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

# 建敏感词：拦截词 + 替换词
st, r = call("POST", "/sensitive-words", token=token, body={"word": "赌博测试", "category": "测试", "action": 1})
check("建拦截敏感词(action=1)", st == 201)
st, r = call("POST", "/sensitive-words", token=token, body={"word": "替换测试词", "category": "测试", "action": 2})
check("建替换敏感词(action=2)", st == 201)

# 同步：拦截
st, r = call("POST", "/ask", token=token, body={"question": "我想了解赌博测试相关的信息"})
d = r["data"]
check("同步-拦截命中", st == 200 and d.get("blocked") and d["is_no_answer"] and len(d["references"]) == 0,
      f"blocked={d.get('blocked')} 答:{d['answer'][:20]}")

# 同步：替换后继续(替换词与知识库无关→会走兜底，但关键是没被拦截)
st, r = call("POST", "/ask", token=token, body={"question": "替换测试词是什么意思"})
d = r["data"]
check("同步-替换放行(未拦截)", st == 200 and not d.get("blocked"), f"blocked={d.get('blocked')}")

# 同步：正常问题不受影响
st, r = call("POST", "/ask", token=token, body={"question": "你好"})
check("同步-正常问题放行", st == 200 and not r["data"].get("blocked"))

# 流式：拦截
full, done = stream_done("/ask/stream", token, {"question": "赌博测试怎么参与"})
check("流式-拦截命中", done is not None and done.get("blocked") and "拦截" in full,
      f"blocked={done.get('blocked') if done else None}")

cleanup()
print("\n==== 汇总 ====")
passed = sum(1 for _, c in results if c)
print(f"通过 {passed}/{len(results)}  (测试数据已清理)")
