"""P1 接口端到端自测（独立脚本，UTF-8 请求体，避免终端编码问题）。

用法：先启动服务，再 python selftest_p1.py
"""

import json
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"
_results: list[tuple[str, bool, str]] = []


def pre_cleanup():
    """删除上次自测残留(直接操作DB)，保证可重复运行。"""
    from app.core.database import SessionLocal
    from app.models import SysRole, SysUser, SysUserRole

    db = SessionLocal()
    for u in db.query(SysUser).filter(SysUser.username == "test_p1_user").all():
        db.query(SysUserRole).filter(SysUserRole.user_id == u.id).delete()
        db.delete(u)
    for r in db.query(SysRole).filter(SysRole.role_code == "test_role").all():
        db.delete(r)
    db.commit()
    db.close()


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
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


def check(name: str, cond: bool, detail: str = ""):
    _results.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


pre_cleanup()

# 1. 登录
st, r = call("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
token = r["data"]["access_token"] if st == 200 else None
check("登录 admin", st == 200 and token is not None, f"user={r['data']['user']['real_name']}" if token else str(r))

# 2. /auth/me
st, r = call("GET", "/auth/me", token=token)
check("获取当前用户 /auth/me", st == 200 and "admin" in r["data"]["roles"], f"roles={r['data']['roles']}")

# 3. 无 token -> 401
st, r = call("GET", "/auth/me")
check("无token访问 -> 401", st == 401)

# 4. 创建用户(含中文)
st, r = call("POST", "/users", token=token, body={
    "username": "test_p1_user", "password": "test123",
    "real_name": "接口测试用户", "user_type": 1, "college": "测试学院",
})
uid = r["data"]["id"] if st == 201 else None
check("创建用户(中文)", st == 201 and uid, f"id={uid} name={r['data']['real_name']}" if uid else str(r))

# 5. 列表分页+关键词
st, r = call("GET", "/users?page=1&size=3&keyword=" + urllib.parse.quote("接口测试"), token=token)
check("用户列表分页", st == 200 and r["data"]["total"] >= 1, f"total={r['data']['total']}")

# 6. 详情
st, r = call("GET", f"/users/{uid}", token=token)
check("用户详情", st == 200 and r["data"]["real_name"] == "接口测试用户", f"name={r['data']['real_name']}")

# 7. 修改
st, r = call("PUT", f"/users/{uid}", token=token, body={"real_name": "改名后的用户", "college": "计算机学院"})
check("修改用户", st == 200 and r["data"]["real_name"] == "改名后的用户", f"name={r['data']['real_name']} college={r['data']['college']}")

# 8. 创建角色
st, r = call("POST", "/roles", token=token, body={"role_code": "test_role", "role_name": "测试角色", "description": "自测用"})
rid = r["data"]["id"] if st == 201 else None
check("创建角色", st == 201 and rid, f"id={rid}" if rid else str(r))

# 9. 分配角色
st, r = call("PUT", f"/users/{uid}/roles", token=token, body={"role_ids": [rid]})
codes = [x["role_code"] for x in r["data"]] if st == 200 else []
check("分配角色", st == 200 and "test_role" in codes, f"roles={codes}")

# 10. 查看用户角色
st, r = call("GET", f"/users/{uid}/roles", token=token)
check("查看用户角色", st == 200 and any(x["role_code"] == "test_role" for x in r["data"]))

# 11. 普通用户登录 -> 越权创建用户应 403
st, r = call("POST", "/auth/login", body={"username": "test_p1_user", "password": "test123"})
t2 = r["data"]["access_token"] if st == 200 else None
check("普通用户登录", st == 200 and t2 is not None)
st, r = call("POST", "/users", token=t2, body={"username": "x_should_fail", "password": "123456"})
check("非admin建用户 -> 403", st == 403, f"http={st}")

# 12. 禁用用户(软删除)
st, r = call("DELETE", f"/users/{uid}", token=token)
check("禁用用户", st == 200)
st, r = call("GET", f"/users/{uid}", token=token)
check("禁用后 status=0", st == 200 and r["data"]["status"] == 0, f"status={r['data']['status']}")

# 清理测试数据
pre_cleanup()

# 汇总
print("\n==== 汇总 ====")
passed = sum(1 for _, c, _ in _results if c)
print(f"通过 {passed}/{len(_results)}  (测试数据已清理)")
