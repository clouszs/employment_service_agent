"""P2 知识库管理接口端到端自测（UTF-8 请求体，含文件上传）。

用法：先启动服务(端口8001)，再 python selftest_p2.py
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


def upload(path, token, fields: dict, filename: str, file_bytes: bytes):
    """构造 multipart/form-data 请求（避免终端编码问题）。"""
    boundary = "----selftestboundary1234567890"
    parts = []
    for k, v in fields.items():
        if v is None:
            continue
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n")
    body = "".join(parts).encode("utf-8")
    body += (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def check(name, cond, detail=""):
    _results.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def cleanup():
    """删除自测产生的数据(直接操作DB)。"""
    from app.core.database import SessionLocal
    from app.models import KbCategory, KbDocument, KbDocumentChunk, KbFaq, KbSynonym

    db = SessionLocal()
    for d in db.query(KbDocument).filter(KbDocument.title.like("自测文档%")).all():
        db.query(KbDocumentChunk).filter(KbDocumentChunk.document_id == d.id).delete()
        db.delete(d)
    for c in db.query(KbCategory).filter(KbCategory.name.like("自测分类%")).all():
        db.delete(c)
    for f in db.query(KbFaq).filter(KbFaq.question.like("自测FAQ%")).all():
        db.delete(f)
    for s in db.query(KbSynonym).filter(KbSynonym.term.like("自测词%")).all():
        db.delete(s)
    db.commit()
    db.close()


cleanup()

# 登录拿 admin token
st, r = call("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
token = r["data"]["access_token"]
check("登录 admin", st == 200 and token is not None)

# ---- 分类 ----
st, r = call("POST", "/categories", token=token, body={"name": "自测分类A", "sort": 99})
cid = r["data"]["id"] if st == 201 else None
check("新建分类", st == 201 and cid, f"id={cid}")
st, r = call("GET", "/categories", token=token)
check("分类列表", st == 200 and any(c["name"] == "自测分类A" for c in r["data"]))
st, r = call("PUT", f"/categories/{cid}", token=token, body={"name": "自测分类A改"})
check("修改分类", st == 200 and r["data"]["name"] == "自测分类A改")

# ---- 文档(文件上传) ----
st, r = upload(
    "/documents", token,
    {"title": "自测文档-就业政策", "category_id": cid, "source": "校就业中心",
     "confidential_level": 1, "remark": "自测上传"},
    "policy.txt", "这是一份就业政策测试文档的内容。".encode("utf-8"),
)
did = r["data"]["id"] if st == 201 else None
check("上传文档(中文+文件)", st == 201 and did,
      f"id={did} hash={r['data'].get('file_hash','')[:8] if did else r}")
st, r = call("GET", f"/documents?keyword=" + urllib.parse.quote("自测文档"), token=token)
check("文档列表(关键词)", st == 200 and r["data"]["total"] >= 1, f"total={r['data']['total']}")
st, r = call("GET", f"/documents/{did}", token=token)
check("文档详情", st == 200 and r["data"]["title"] == "自测文档-就业政策",
      f"file_name={r['data']['file_name']} size={r['data']['file_size']}")
st, r = call("PUT", f"/documents/{did}", token=token, body={"status": 0, "remark": "已下架"})
check("修改文档(下架)", st == 200 and r["data"]["status"] == 0)
st, r = call("GET", f"/documents/{did}/chunks", token=token)
check("查看文档分片(空)", st == 200 and isinstance(r["data"], list))

# ---- 索引任务列表 ----
st, r = call("GET", "/index-tasks?size=5", token=token)
check("索引任务列表", st == 200 and "items" in r["data"], f"total={r['data']['total']}")

# ---- FAQ ----
st, r = call("POST", "/faqs", token=token, body={"question": "自测FAQ问题？", "answer": "自测答案内容。"})
fid = r["data"]["id"] if st == 201 else None
check("新建FAQ", st == 201 and fid)
st, r = call("GET", "/faqs?keyword=" + urllib.parse.quote("自测FAQ"), token=token)
check("FAQ列表(关键词)", st == 200 and r["data"]["total"] >= 1, f"total={r['data']['total']}")
st, r = call("PUT", f"/faqs/{fid}", token=token, body={"answer": "更新后的答案"})
check("修改FAQ", st == 200 and r["data"]["answer"] == "更新后的答案")

# ---- 同义词 ----
st, r = call("POST", "/synonyms", token=token, body={"term": "自测词三方", "synonyms": "三方协议,就业协议"})
sid = r["data"]["id"] if st == 201 else None
check("新建同义词", st == 201 and sid)
st, r = call("GET", "/synonyms?keyword=" + urllib.parse.quote("自测词"), token=token)
check("同义词列表", st == 200 and r["data"]["total"] >= 1)

# ---- 权限：无 token 403/401 ----
st, r = call("POST", "/categories", body={"name": "x"})
check("无token建分类 -> 401/403", st in (401, 403), f"http={st}")

# ---- 删除 ----
st, r = call("DELETE", f"/documents/{did}", token=token)
check("删除文档", st == 200)
st, r = call("DELETE", f"/faqs/{fid}", token=token)
check("删除FAQ", st == 200)
st, r = call("DELETE", f"/synonyms/{sid}", token=token)
check("删除同义词", st == 200)
st, r = call("DELETE", f"/categories/{cid}", token=token)
check("删除分类", st == 200)

cleanup()
print("\n==== 汇总 ====")
passed = sum(1 for _, c, _ in _results if c)
print(f"通过 {passed}/{len(_results)}  (测试数据已清理)")
