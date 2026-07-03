"""End-to-end test: admin changes top_k, ask question, verify references."""
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"

def login():
    req = urllib.request.Request(
        f"{BASE}/api/v1/auth/login",
        data=json.dumps({"username": "admin", "password": "admin123"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["data"]["access_token"]

def api_get(token, path):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def api_put(token, path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def api_post(token, path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def main():
    token = login()

    # Step 1: Check current top_k
    d = api_get(token, "/api/v1/app-configs?page=1&size=200")
    row = [i for i in d["data"]["items"] if i["config_key"] == "qa_retrieval.top_k"][0]
    print(f"[Step 1] Current qa_retrieval.top_k = {row['config_value']} (id={row['id']})")

    # Step 2: Admin changes top_k from 5 to 3
    print("\n[Step 2] Admin changes top_k: 5 -> 3")
    r = api_put(token, f'/api/v1/app-configs/{row["id"]}', {"config_value": "3"})
    print(f"  Update: code={r['code']} msg={r['message']}")

    # Step 3: Verify change
    d = api_get(token, "/api/v1/app-configs?page=1&size=200")
    row = [i for i in d["data"]["items"] if i["config_key"] == "qa_retrieval.top_k"][0]
    print(f"[Step 3] After update: qa_retrieval.top_k = {row['config_value']}")
    assert row["config_value"] == "3", f"FAIL: value is {row['config_value']}"

    # Step 4: Search with explicit top_k=3
    print("\n[Step 4] POST /search with top_k=3...")
    r = api_post(token, "/api/v1/search", {"query": "就业", "top_k": 3})
    if isinstance(r, list):
        print(f"  References returned: {len(r)}")
        for i, ref in enumerate(r[:6], 1):
            print(f"    [{i}] score={ref.get('score')} doc={ref.get('document_title', '?')[:40]}")
    else:
        print(f"  Unexpected response type: {type(r)}")
        print(f"  {json.dumps(r, ensure_ascii=False)[:300]}")

    # Step 5: Ask (uses DB config, no explicit top_k)
    print("\n[Step 5] POST /ask (uses DB config top_k=3)...")
    r = api_post(token, "/api/v1/ask", {"question": "什么是就业指导？"})
    if isinstance(r, dict) and r.get("conversation_id"):
        refs = r.get("references", [])
        print(f"  References returned: {len(refs)}")
        for i, ref in enumerate(refs[:6], 1):
            print(f"    [{i}] score={ref.get('score')} doc={ref.get('document_title', '?')[:40]}")
        if len(refs) == 3:
            print("  PASS: top_k=3 is working correctly!")
        else:
            print(f"  FAIL: expected 3 references, got {len(refs)}")
    else:
        print(f"  Unexpected response: {json.dumps(r, ensure_ascii=False)[:300]}")

    # Step 6: Reset to 5
    print("\n[Step 6] Resetting top_k back to 5...")
    r = api_put(token, f'/api/v1/app-configs/{row["id"]}', {"config_value": "5"})
    print(f"  Reset: code={r['code']} msg={r['message']}")

if __name__ == "__main__":
    main()
