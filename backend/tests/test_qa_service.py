"""阶段4 问答服务升级验证脚本。"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.qa_service import agent_chat
from app.routers.qa import router

passed = 0
failed = 0


def assert_eq(name, actual, expected):
    global passed, failed
    if actual == expected:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: expected {expected!r}, got {actual!r}")


def assert_true(name, value):
    global passed, failed
    if value:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: expected truthy, got {value!r}")


def assert_false(name, value):
    global passed, failed
    if not value:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: expected falsy, got {value!r}")


# ==================== qa_service.agent_chat ====================
print("测试组：qa_service.agent_chat")

try:
    from app.core.database import SessionLocal
    from app.models import SysUser

    db = SessionLocal()
    try:
        # 找一个测试用户（user_id=1 通常存在）
        user = db.get(SysUser, 1)
        if user is None:
            print("  [SKIP] agent_chat (no test user)")
        else:
            result = agent_chat(db, user_id=user.id, query="你好")
            assert_isinstance = lambda n, o, c: assert_true(n, isinstance(o, c))
            assert_isinstance("result_is_dict", result, dict)
            assert_true("has_conversation_id", "conversation_id" in result)
            assert_true("has_message_id", "message_id" in result)
            assert_true("has_response", "response" in result)
            assert_true("has_route", "route" in result)
            assert_true("has_citations", "citations" in result)
            assert_true("has_confidence", "confidence" in result)

            passed += 1
            print(f"  [PASS] agent_chat")
    finally:
        db.close()
except Exception as e:
    failed += 1
    print(f"  [FAIL] agent_chat: {e}")


# ==================== routers/qa.py 路由注册 ====================
print("测试组：routers/qa.py 路由注册")

try:
    routes = [r.path for r in router.routes]
    assert_true("has_search", "/search" in routes)
    assert_true("has_ask", "/ask" in routes)
    assert_true("has_stream", "/ask/stream" in routes)
    assert_true("has_agent", "/ask/agent" in routes)

    passed += 1
    print(f"  [PASS] qa_routes")
except Exception as e:
    failed += 1
    print(f"  [FAIL] qa_routes: {e}")


# ==================== 汇总 ====================
print(f"\n结果：passed={passed}, failed={failed}")
if failed:
    sys.exit(1)
print("全部验证通过")
