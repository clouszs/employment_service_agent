"""P3 检索问答端到端自测：上传→解析→入库→检索→问答(溯源/落库)→流式→兜底。

用法：先启动服务(端口8000)，再 python selftest_p3.py
"""

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
results: list[tuple[str, bool, str]] = []

DOC_TEXT = (
    "应届毕业生申请落户需要准备以下材料：报到证、毕业证、学位证、身份证、户口迁移证，"
    "以及用人单位接收证明。办理流程为：先到就业指导中心领取报到证，再到落户地公安机关申请，"
    "最后办理户口迁入手续，一般五个工作日内办结。"
    "三方协议是毕业生、用人单位与学校三方签订的就业协议，签订后如需违约须经用人单位同意并出具书面解约函，"
    "违约金一般不超过五千元。"
)


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


def stream_call(path, token, body):
    """读取 SSE 流，返回 (delta拼接文本, done事件data)。"""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {token}")
    full, done, cur_event = "", None, None
    with urllib.request.urlopen(req) as resp:
        for raw in resp:
            line = raw.decode("utf-8").rstrip("\n")
            if line.startswith("event: "):
                cur_event = line[7:]
            elif line.startswith("data: "):
                payload = line[6:]
                if cur_event == "delta":
                    full += payload
                elif cur_event == "done":
                    done = json.loads(payload)
    return full, done


def upload(path, token, fields, filename, file_bytes):
    boundary = "----p3boundary"
    body = b""
    for k, v in fields.items():
        if v is None:
            continue
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8")
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def check(name, cond, detail=""):
    results.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def wait_status(did, token, field, timeout=60):
    for _ in range(timeout):
        st, r = call("GET", f"/documents/{did}", token=token)
        if r["data"][field] in (2, 3):
            return r["data"][field]
        time.sleep(1)
    return -1


def cleanup():
    from app.core.database import SessionLocal
    from app.models import KbDocument, KbDocumentChunk, OpQueryLog, QaConversation, QaMessage, QaMessageReference
    from app.services.index_service import remove_document_vectors

    db = SessionLocal()
    for d in db.query(KbDocument).filter(KbDocument.title.like("P3自测%")).all():
        remove_document_vectors(d.id)
        db.query(KbDocumentChunk).filter(KbDocumentChunk.document_id == d.id).delete()
        db.delete(d)
    for c in db.query(QaConversation).filter(QaConversation.title.like("应届%") | QaConversation.title.like("火星%")).all():
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

# 准备知识：上传→解析→入库
st, r = upload("/documents", token, {"title": "P3自测-落户与三方", "confidential_level": 1},
               "p3.txt", DOC_TEXT.encode("utf-8"))
did = r["data"]["id"]
check("上传文档", st == 201 and did, f"id={did}")
call("POST", f"/documents/{did}/parse", token=token)
check("解析完成", wait_status(did, token, "parse_status") == 2)
call("POST", f"/documents/{did}/index", token=token)
check("入库完成", wait_status(did, token, "index_status") == 2)

# 1. 纯检索
st, r = call("POST", "/search", token=token, body={"query": "落户需要哪些材料", "top_k": 3})
hits = r["data"] if st == 200 else []
check("纯检索 /search", st == 200 and len(hits) >= 1 and hits[0]["document_id"] == did,
      f"命中{len(hits)}条 top分={hits[0]['score'] if hits else None}")

# 2. 同步问答(命中)
st, r = call("POST", "/ask", token=token, body={"question": "应届生落户需要准备哪些材料？"})
d = r["data"]
ok = st == 200 and not d["is_no_answer"] and len(d["answer"]) > 0 and len(d["references"]) >= 1
check("同步问答 /ask", ok, f"答案:{d['answer'][:40]}...")
check("问答带引用溯源", len(d["references"]) >= 1 and d["references"][0]["document_title"],
      f"来源:《{d['references'][0]['document_title']}》" if d["references"] else "")
conv_id = d["conversation_id"]
msg_id = d["message_id"]

# 3. 落库验证：会话详情应有 问+答 两条消息
st, r = call("GET", f"/conversations/{conv_id}", token=token)
check("问答已落库(会话+消息)", st == 200 and len(r["data"]["messages"]) == 2,
      f"消息数={len(r['data']['messages'])}")

# 4. 溯源接口
st, r = call("GET", f"/messages/{msg_id}/references", token=token)
check("答案溯源 /messages/{id}/references", st == 200 and len(r["data"]) >= 1)

# 5. 多轮：在同一会话追问
st, r = call("POST", "/ask", token=token, body={"question": "三方协议违约金最多多少？", "conversation_id": conv_id})
check("同会话多轮追问", st == 200 and not r["data"]["is_no_answer"] and r["data"]["conversation_id"] == conv_id,
      f"答案:{r['data']['answer'][:30]}...")

# 6. 兜底：问与知识库无关的问题
st, r = call("POST", "/ask", token=token, body={"question": "火星上的房价是多少？"})
check("无关问题走兜底", st == 200 and r["data"]["is_no_answer"] and len(r["data"]["references"]) == 0,
      f"兜底答:{r['data']['answer'][:20]}...")

# 7. 流式问答
full, done = stream_call("/ask/stream", token, {"question": "落户办理流程是怎样的？"})
check("流式问答 /ask/stream", len(full) > 0 and done is not None and not done["is_no_answer"],
      f"流式文本:{full[:30]}... 引用{len(done['references']) if done else 0}条")

cleanup()
print("\n==== 汇总 ====")
passed = sum(1 for _, c, _ in results if c)
print(f"通过 {passed}/{len(results)}  (测试数据已清理)")
