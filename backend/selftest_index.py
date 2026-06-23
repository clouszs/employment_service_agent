"""文档 解析(parse) + 入库(index) 端到端自测。

流程：上传txt文档 → 解析(后台) → 入库向量化(后台) → 语义检索验证 → 清理
用法：先启动服务(端口8000)，再 python selftest_index.py
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
    "三方协议是毕业生、用人单位与学校三方签订的就业协议，签订后如需违约须经用人单位同意并出具书面解约函。"
    "毕业生档案默认转递至生源地人才服务中心，如已落实工作单位且单位具备档案管理权限，可转至单位。"
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
    boundary = "----idxboundary999"
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


def wait_status(did, token, field, target=2, timeout=60):
    """轮询文档某状态字段直到达到 target 或失败(3)。"""
    for _ in range(timeout):
        st, r = call("GET", f"/documents/{did}", token=token)
        val = r["data"][field]
        if val in (2, 3):
            return val
        time.sleep(1)
    return -1


def cleanup():
    from app.core.database import SessionLocal
    from app.models import KbDocument, KbDocumentChunk
    from app.services.index_service import remove_document_vectors

    db = SessionLocal()
    for d in db.query(KbDocument).filter(KbDocument.title.like("解析自测%")).all():
        remove_document_vectors(d.id)
        db.query(KbDocumentChunk).filter(KbDocumentChunk.document_id == d.id).delete()
        db.delete(d)
    db.commit()
    db.close()


cleanup()
st, r = call("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
token = r["data"]["access_token"]
check("登录 admin", st == 200 and token)

# 上传文档
st, r = upload("/documents", token, {"title": "解析自测-就业政策", "confidential_level": 1},
               "policy.txt", DOC_TEXT.encode("utf-8"))
did = r["data"]["id"] if st == 201 else None
check("上传txt文档", st == 201 and did, f"id={did}")

# 解析
st, r = call("POST", f"/documents/{did}/parse", token=token)
check("提交解析任务", st == 200, f"task={r['data'].get('id')}")
ps = wait_status(did, token, "parse_status")
check("解析完成(parse_status=2)", ps == 2, f"status={ps}")

st, r = call("GET", f"/documents/{did}/chunks", token=token)
nchunks = len(r["data"]) if st == 200 else 0
check("生成分片", nchunks >= 1, f"分片数={nchunks}")

# 入库
st, r = call("POST", f"/documents/{did}/index", token=token)
check("提交入库任务", st == 200)
ixs = wait_status(did, token, "index_status")
check("入库完成(index_status=2)", ixs == 2, f"status={ixs}")

# 分片应有 vector_id
st, r = call("GET", f"/documents/{did}/chunks", token=token)
has_vec = all(c["vector_id"] for c in r["data"]) if r["data"] else False
check("分片均已写入向量ID", has_vec, f"示例={r['data'][0]['vector_id'] if r['data'] else None}")

# 语义检索验证(直接查 Chroma)
from app.core.embedding import embed_query
from app.core import vectorstore

hits = vectorstore.query(embed_query("落户要准备哪些证件材料"), top_k=3, where={"document_id": did})
top = hits[0] if hits else {}
check("语义检索命中本文档", len(hits) >= 1 and top.get("metadata", {}).get("document_id") == did,
      f"命中{len(hits)}条 top分数={top.get('score')}")
print("    top片段:", (top.get("document") or "")[:50])

# 删除文档应清理向量
st, r = call("DELETE", f"/documents/{did}", token=token)
check("删除文档", st == 200)
hits2 = vectorstore.query(embed_query("落户材料"), top_k=3, where={"document_id": did})
check("删除后向量已清理", len(hits2) == 0, f"残留={len(hits2)}")

cleanup()
print("\n==== 汇总 ====")
passed = sum(1 for _, c, _ in results if c)
print(f"通过 {passed}/{len(results)}  (测试数据已清理)")
