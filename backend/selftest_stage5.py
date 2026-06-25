"""阶段5 + 前端接口全量验证脚本 v3（更健壮）。"""
import json
import urllib.request
import urllib.parse
import urllib.error

BASE = "http://127.0.0.1:8000/api/v1"
_results: list[tuple[str, bool, str]] = []


def call(method: str, path: str, token: str | None = None, body: dict | None = None, params: dict | None = None):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw}
    except Exception as e:
        return 0, {"_error": str(e)}


def check(name: str, cond: bool, detail: str = ""):
    _results.append((name, cond, detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name}  {detail}")


def safe_keys(r):
    if isinstance(r, dict):
        return list(r.keys())[:8]
    return str(type(r).__name__)


# 登录 admin
st, r = call("POST", "/auth/login", body={"username": "admin", "password": "admin123"})
admin_token = r.get("data", {}).get("access_token") if st == 200 else None
check("admin 登录", st == 200 and admin_token is not None)

# 找非 admin 用户
st, r = call("GET", "/users", token=admin_token, params={"page": 1, "size": 50})
other_user = None
other_token = None
if st == 200:
    items = r.get("data", {}).get("items", [])
    for u in items:
        if u.get("id") != 1 and u.get("status") == 1:
            other_user = u
            break
if other_user:
    st2, r2 = call("POST", "/auth/login", body={"username": other_user["username"], "password": "admin123"})
    other_token = r2.get("data", {}).get("access_token") if st2 == 200 else None
    print(f"  Other user: id={other_user['id']} username={other_user['username']} login={st2}")

print()
print("=== 阶段5 新端点验证 ===")

st, r = call("GET", "/kb-health/latest", token=admin_token)
check("kb-health/latest", st == 200 and "health_score" in r.get("data", {}), f"status={st} score={r.get('data', {}).get('health_score')}")

st, r = call("GET", "/kb-health/history", token=admin_token, params={"page": 1, "size": 10})
check("kb-health/history", st == 200 and "items" in r.get("data", {}), f"status={st} total={r.get('data', {}).get('total')}")

st, r = call("POST", "/kb-health/run", token=admin_token)
check("kb-health/run", st == 200 and "health_score" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/llm-cost/daily", token=admin_token)
check("llm-cost/daily", st == 200 and "models" in r.get("data", {}), f"status={st} total_cost={r.get('data', {}).get('total_cost_usd')}")

st, r = call("GET", "/llm-cost/monthly", token=admin_token, params={"year": 2026, "month": 6})
check("llm-cost/monthly", st == 200 and "models" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/llm-cost/history", token=admin_token, params={"page": 1, "size": 10})
check("llm-cost/history", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/refusal/list", token=admin_token, params={"page": 1, "size": 10})
check("refusal/list", st == 200 and "items" in r.get("data", {}), f"status={st} total={r.get('data', {}).get('total')}")

st, r = call("GET", "/refusal/stats", token=admin_token, params={"days": 7})
check("refusal/stats", st == 200 and "total_refusals" in r.get("data", {}), f"status={st}")

print()
print("=== 前端依赖接口验证 ===")

st, r = call("POST", "/search", token=admin_token, body={"query": "落户政策", "top_k": 3})
check("search", st == 200 and isinstance(r.get("data"), list), f"status={st} hits={len(r['data']) if isinstance(r.get('data'), list) else 0}")

st, r = call("POST", "/ask", token=admin_token, body={"question": "你好", "conversation_id": None})
check("ask (old RAG)", st == 200 and "answer" in r.get("data", {}), f"status={st}")

st, r = call("POST", "/ask/agent", token=admin_token, body={"question": "你好", "conversation_id": None})
d = r.get("data") if isinstance(r, dict) else None
check("ask/agent (qa.py)", st == 200 and d is not None and "response" in d, f"status={st} keys={safe_keys(d)}")

st, r = call("POST", "/chat", token=admin_token, body={"query": "你好", "conversation_id": None})
d = r.get("data") if isinstance(r, dict) else None
check("chat (agent.py)", st == 200 and d is not None and "response" in d, f"status={st} keys={safe_keys(d)} detail={r.get('message') if isinstance(r, dict) else str(r)[:200]}")

st, r = call("GET", "/conversations", token=admin_token, params={"page": 1, "size": 10})
check("conversations", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/stats/overview", token=admin_token)
check("stats/overview", st == 200 and "total_questions" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/stats/hot-questions", token=admin_token, params={"limit": 5})
check("stats/hot-questions", st == 200 and isinstance(r.get("data"), list), f"status={st} count={len(r['data']) if isinstance(r.get('data'), list) else 0}")

st, r = call("POST", "/messages/999999/feedback", token=admin_token, body={"rating": 1})
check("messages/feedback (404 ok)", st == 404, f"status={st}")

st, r = call("GET", "/messages/999999/references", token=admin_token)
check("messages/references (404 ok)", st == 404, f"status={st}")

st, r = call("GET", "/categories", token=admin_token)
check("categories", st == 200 and isinstance(r.get("data"), list), f"status={st}")

st, r = call("GET", "/documents", token=admin_token, params={"page": 1, "size": 5})
check("documents", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/faqs", token=admin_token, params={"page": 1, "size": 5})
check("faqs", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/feedback/stats", token=admin_token)
check("feedback/stats", st == 200 and "today" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/logs/queries", token=admin_token, params={"page": 1, "size": 5})
check("logs/queries", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/eval-cases", token=admin_token, params={"page": 1, "size": 5})
check("eval-cases", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/unanswered", token=admin_token, params={"page": 1, "size": 5})
check("unanswered", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/sensitive-words", token=admin_token, params={"page": 1, "size": 5})
check("sensitive-words", st == 200 and "items" in r.get("data", {}), f"status={st}")

st, r = call("GET", "/synonyms", token=admin_token, params={"page": 1, "size": 5})
check("synonyms", st == 200 and "items" in r.get("data", {}), f"status={st}")

print()
print("=== 权限控制验证 ===")

if other_token:
    st, r = call("GET", "/stats/overview", token=other_token)
    check(f"user_id={other_user['id']} -> /stats/overview", st == 403, f"status={st}")

    st, r = call("POST", "/ask/agent", token=other_token, body={"question": "你好", "conversation_id": None})
    check(f"user_id={other_user['id']} -> /ask/agent", st == 200, f"status={st}")

    st, r = call("GET", "/conversations", token=other_token, params={"page": 1, "size": 5})
    check(f"user_id={other_user['id']} -> /conversations", st == 200, f"status={st}")

    st, r = call("GET", "/stats/overview")
    check("no token -> 401", st == 401, f"status={st}")
else:
    print("  (skip: no other user token)")

print()
print("==== 汇总 ====")
passed = sum(1 for _, c, _ in _results if c)
print(f"通过 {passed}/{len(_results)}")
