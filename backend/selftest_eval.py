"""评测执行自测：构造文档+评测集，跑 /eval-cases/run 验证命中率与明细。

用法：先启动服务(端口8000)，再 python selftest_eval.py
"""

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
results = []

DOC_TEXT = (
    "应届毕业生申请落户需要准备以下材料：报到证、毕业证、学位证、身份证、户口迁移证，"
    "以及用人单位接收证明。办理流程为先到就业指导中心领取报到证，再到落户地公安机关申请。"
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


def upload(path, token, fields, filename, file_bytes):
    boundary = "----evalboundary"
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
    results.append((name, cond))
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
    from app.models import KbDocument, KbDocumentChunk, OpEvalCase
    from app.services.index_service import remove_document_vectors

    db = SessionLocal()
    for d in db.query(KbDocument).filter(KbDocument.title.like("评测自测%")).all():
        remove_document_vectors(d.id)
        db.query(KbDocumentChunk).filter(KbDocumentChunk.document_id == d.id).delete()
        db.delete(d)
    for e in db.query(OpEvalCase).filter(OpEvalCase.question.like("评测自测%")).all():
        db.delete(e)
    db.commit()
    db.close()


cleanup()
st, r = call("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
token = r["data"]["access_token"]
check("登录 admin", st == 200 and token)

# 准备文档并入库
st, r = upload("/documents", token, {"title": "评测自测-落户材料", "confidential_level": 1},
               "eval.txt", DOC_TEXT.encode("utf-8"))
did = r["data"]["id"]
check("上传文档", st == 201 and did, f"id={did}")
call("POST", f"/documents/{did}/parse", token=token)
check("解析完成", wait_status(did, token, "parse_status") == 2)
call("POST", f"/documents/{did}/index", token=token)
check("入库完成", wait_status(did, token, "index_status") == 2)

# 评测集：1条应命中(指向该doc) / 1条必不命中(指向不存在doc) / 1条跳过(无expected_doc_id)
st, r = call("POST", "/eval-cases", token=token, body={
    "question": "评测自测：应届生落户要准备哪些材料？", "expected_doc_id": did, "category": "评测自测"})
check("建用例-应命中", st == 201)
st, r = call("POST", "/eval-cases", token=token, body={
    "question": "评测自测：落户流程是什么", "expected_doc_id": 99999999, "category": "评测自测"})
check("建用例-必不命中", st == 201)
st, r = call("POST", "/eval-cases", token=token, body={
    "question": "评测自测：无期望文档的问题", "category": "评测自测"})
check("建用例-无期望文档", st == 201)

# 执行评测(限定本次类别)
st, r = call("POST", "/eval-cases/run", token=token, body={"top_k": 5, "category": "评测自测"})
d = r["data"]
check("评测执行返回", st == 200 and "hit_rate" in d, f"total={d.get('total')}")
check("总数=3", d["total"] == 3, f"total={d['total']}")
check("跳过=1(无期望文档)", d["skipped"] == 1, f"skipped={d['skipped']}")
check("计入=2", d["evaluated"] == 2, f"evaluated={d['evaluated']}")
check("命中=1", d["hit_count"] == 1, f"hit_count={d['hit_count']}")
check("命中率=0.5", abs(d["hit_rate"] - 0.5) < 0.001, f"hit_rate={d['hit_rate']}")
# 明细：应命中的那条 hit=True 且 hit_rank>=1
hit_case = next((x for x in d["details"] if x["expected_doc_id"] == did), None)
check("应命中用例 hit=True", hit_case and hit_case["hit"] and hit_case["hit_rank"] >= 1,
      f"hit_rank={hit_case['hit_rank'] if hit_case else None}")

# 权限：普通查看接口登录可访问，但 run 需 admin/editor —— 用 admin 已覆盖
cleanup()
print("\n==== 汇总 ====")
passed = sum(1 for _, c in results if c)
print(f"通过 {passed}/{len(results)}  (测试数据已清理)")
