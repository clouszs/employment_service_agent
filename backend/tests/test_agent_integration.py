"""阶段2 幻觉防御集成验证脚本（无 pytest 依赖）。"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.citation_tracker import build_citations, evaluate_citation_quality
from app.agent.hallucination_defense import (
    consistency_checker,
    fact_verifier,
    threshold_checker,
)
from app.agent.refusal_handler import get_refusal_by_type, get_refusal_response
from app.agent.nodes import (
    accept_with_warning,
    check_confidence,
    check_consistency,
    content_moderation,
    direct_response,
    error_handler,
    generate_refusal,
    generate_response,
    regenerate_with_hints,
    route_query,
    search_knowledge,
    verify_facts,
)


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


def assert_in(name, needle, haystack):
    global passed, failed
    if needle in haystack:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: {needle!r} not in {haystack!r}")


# ==================== 动态置信度阈值 ====================
print("测试组：动态置信度阈值")
accepted, reason = threshold_checker.should_accept_result(
    query="落户政策", confidence=0.85, results_count=3, has_citation=True, retry_attempt=0
)
assert_true("high_risk_accept", accepted)

accepted, reason = threshold_checker.should_accept_result(
    query="落户政策", confidence=0.70, results_count=3, has_citation=True, retry_attempt=0
)
assert_false("high_risk_reject", accepted)
assert_in("reason_contains_threshold", "当前阈值", reason)

accepted, _ = threshold_checker.should_accept_result(
    query="落户", confidence=0.69, results_count=2, has_citation=True, retry_attempt=1
)
assert_true("retry_lower_threshold", accepted)

assert_true("should_retry_0", threshold_checker.should_retry(0))
assert_true("should_retry_2", threshold_checker.should_retry(2))
assert_false("should_retry_3", threshold_checker.should_retry(3))


# ==================== 一致性检查 ====================
print("测试组：一致性检查")
ok, issues = consistency_checker.check("回答内容", [])
assert_true("no_history_consistent", ok)
assert_eq("no_history_issues", issues, [])


# ==================== 事实核验 ====================
print("测试组：事实核验")
issues = fact_verifier.verify("根据国办发〔2024〕5号文件")
types = [i["fact_type"] for i in issues]
assert_in("policy_no_detected", "policy_no", types)

issues = fact_verifier.verify("2024年6月30日生效")
types = [i["fact_type"] for i in issues]
assert_in("date_detected", "date", types)

issues = fact_verifier.verify("补贴金额5000元")
types = [i["fact_type"] for i in issues]
assert_in("money_detected", "money", types)


# ==================== 拒答模板 ====================
print("测试组：拒答模板")
resp = get_refusal_response(reason="资料不足", question="落户政策")
assert_in("refusal_has_question", "落户政策", resp)
assert_in("refusal_has_reason", "资料不足", resp)

resp = get_refusal_by_type("no_result")
assert_in("no_result_template", "就业资料", resp)

resp = get_refusal_by_type("blocked")
assert_in("blocked_template", "拦截", resp)


# ==================== 引用追踪 ====================
print("测试组：引用追踪")
hits = [
    {
        "document_id": 1,
        "document_title": "测试文档",
        "chunk_id": "c1",
        "score": 0.9,
        "page_no": 1,
        "content": "测试内容" * 50,
    }
]
citations = build_citations(hits)
assert_eq("citation_count", len(citations), 1)
assert_eq("citation_rank", citations[0]["rank"], 1)
assert_eq("citation_title", citations[0]["document_title"], "测试文档")

result = evaluate_citation_quality([])
assert_eq("empty_quality_score", result["quality_score"], 0.0)
assert_in("empty_quality_issues", "无引用", result["issues"])

citations = [{"score": 0.9}, {"score": 0.85}, {"score": 0.80}]
result = evaluate_citation_quality(citations)
assert_eq("high_quality_direct", result["direct_count"], 3)
assert_eq("high_quality_score", result["quality_score"], 1.0)


# ==================== 节点集成 ====================
print("测试组：节点集成")

# route_query
state = {"current_query": "你好", "tool_call_count": 0}
result = route_query(state)
assert_eq("route_direct", result["route"], "direct")
assert_eq("route_direct_level", result["query_risk_level"], "low")

state = {"current_query": "落户政策", "tool_call_count": 0}
result = route_query(state)
assert_eq("route_search_high", result["route"], "search")
assert_eq("route_high_level", result["query_risk_level"], "high")

# check_confidence
state = {
    "current_query": "落户",
    "confidence": 0.85,
    "search_results": [{"score": 0.85}, {"score": 0.82}, {"score": 0.80}],
    "citations": [{"rank": 1}],
    "retry_attempt": 0,
}
result = check_confidence(state)
assert_false("confidence_accept_retry", result.get("should_retry", True))
assert_false("confidence_accept_refuse", result.get("should_refuse", True))

state = {
    "current_query": "落户",
    "confidence": 0.70,
    "search_results": [{"score": 0.70}, {"score": 0.65}, {"score": 0.60}],
    "citations": [{"rank": 1}],
    "retry_attempt": 0,
}
result = check_confidence(state)
assert_true("confidence_retry", result.get("should_retry", False))
assert_eq("retry_count", result.get("retry_attempt"), 1)

# generate_refusal (V1 简化：不调 LLM)
state = {"current_query": "测试问题", "refusal_reason": "资料不足"}
result = generate_refusal(state)
assert_true("refuse_flag", result.get("should_refuse", False))
assert_in("refusal_text", "测试问题", result.get("response", ""))
assert_in("refusal_reason", "资料不足", result.get("response", ""))

# direct_response
state = {"current_query": "你好"}
result = direct_response(state)
assert_eq("direct_route", result["route"], "direct")
assert_eq("direct_confidence", result["confidence"], 1.0)

# content_moderation
state = {"response": "这是一个正常的回答。"}
result = content_moderation(state)
assert_true("moderation_safe", result.get("content_safe", False))

state = {"response": "加我微信，私信我，代做枪手。"}
result = content_moderation(state)
assert_false("moderation_unsafe", result.get("content_safe", True))
assert_true("moderation_refuse", result.get("should_refuse", False))

# error_handler
state = {}
result = error_handler(state)
assert_eq("error_handler_empty", result, state)

state = {"error": {"type": "test", "message": "test error"}, "request_id": "123"}
result = error_handler(state)
assert_true("error_handler_error", result.get("is_error", False))
assert_in("error_response", "抱歉", result.get("response", ""))


# ==================== 汇总 ====================
print(f"\n结果：passed={passed}, failed={failed}")
if failed:
    sys.exit(1)
print("全部验证通过")
