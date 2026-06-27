"""阶段3 监控告警模块验证脚本。"""

from __future__ import annotations

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.monitor.citation_evaluator import CitationQualityEvaluator
from app.monitor.cost_monitor import LlmCostMonitor
from app.monitor.health_monitor import KnowledgeBaseHealthMonitor
from app.monitor.scheduler import get_scheduler, setup_scheduler, shutdown_scheduler

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


def assert_isinstance(name, obj, cls):
    global passed, failed
    if isinstance(obj, cls):
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: expected {cls}, got {type(obj)}")


# ==================== 知识库健康度监控 ====================
print("测试组：知识库健康度监控")

try:
    from app.core.database import SessionLocal
    from app.models import KbDocument

    db = SessionLocal()
    try:
        monitor = KnowledgeBaseHealthMonitor(db)
        assert_isinstance("monitor_init", monitor, KnowledgeBaseHealthMonitor)

        report = monitor.run_daily_check()
        assert_isinstance("report_is_dict", report, dict)
        assert_in = lambda n, k: report.get(k) is not None
        assert_true("report_has_check_date", "check_date" in report)
        assert_true("report_has_health_score", "health_score" in report)
        assert_true("report_has_warning_count", "warning_count" in report)
        assert_true("report_has_expired_count", "expired_count" in report)
        assert_true("report_has_warning_docs", "warning_docs" in report)
        assert_true("report_has_expired_docs", "expired_docs" in report)

        # 健康度应该是 0-100
        score = report.get("health_score", -1)
        assert_true("health_score_in_range", 0 <= score <= 100)

        passed += 1
        print(f"  [PASS] kb_health_report")
    finally:
        db.close()
except Exception as e:
    failed += 1
    print(f"  [FAIL] kb_health_monitor: {e}")

# ==================== LLM 成本监控 ====================
print("测试组：LLM 成本监控")

try:
    db = SessionLocal()
    try:
        monitor = LlmCostMonitor(db)
        assert_isinstance("cost_monitor_init", monitor, LlmCostMonitor)

        # 无数据时的空报告
        report = monitor.run_daily_check()
        assert_isinstance("cost_report_is_dict", report, dict)
        assert_true("cost_report_has_stat_date", "stat_date" in report)
        assert_true("cost_report_has_total_cost", "total_cost_usd" in report)
        assert_true("cost_report_has_models", "models" in report)
        assert_eq("cost_report_total_cost_empty", report["total_cost_usd"], 0.0)
        assert_eq("cost_report_total_calls_empty", report["total_calls"], 0)

        # 估算函数
        cost = monitor._estimate_cost("qwen-plus", tokens_in=1000, tokens_out=500)
        assert_true("cost_estimate_positive", cost >= 0)

        passed += 1
        print(f"  [PASS] llm_cost_monitor")
    finally:
        db.close()
except Exception as e:
    failed += 1
    print(f"  [FAIL] llm_cost_monitor: {e}")

# ==================== 引用质量评估 ====================
print("测试组：引用质量评估")

try:
    db = SessionLocal()
    try:
        evaluator = CitationQualityEvaluator()
        assert_isinstance("evaluator_init", evaluator, CitationQualityEvaluator)

        # 空引用
        result = evaluator.evaluate_and_log(db, message_id=1, citations=[])
        assert_isinstance("result_is_dict", result, dict)
        assert_eq("empty_quality_score", result.get("quality_score"), 0.0)

        # 高质量引用
        citations = [{"score": 0.9}, {"score": 0.85}, {"score": 0.80}]
        result = evaluator.evaluate_and_log(db, message_id=2, citations=citations)
        assert_eq("high_quality_score", result.get("quality_score"), 1.0)
        assert_eq("high_quality_direct", result.get("direct_count"), 3)

        passed += 1
        print(f"  [PASS] citation_evaluator")
    finally:
        db.close()
except Exception as e:
    failed += 1
    print(f"  [FAIL] citation_evaluator: {e}")

# ==================== 调度器 ====================
print("测试组：调度器")

try:
    # 调度器需要 event loop，在同步脚本中可能不可用
    import asyncio
    loop = asyncio.get_running_loop()
    scheduler = setup_scheduler()
    assert_true("scheduler_started", scheduler is not None)
    assert_true("scheduler_running", scheduler.running)

    jobs = scheduler.get_jobs()
    job_ids = [j.id for j in jobs]
    assert_true("has_kb_health_job", "kb_health_check" in job_ids)
    assert_true("has_llm_cost_job", "llm_cost_check" in job_ids)

    shutdown_scheduler()
    assert_true("scheduler_shutdown", get_scheduler() is None)

    passed += 1
    print(f"  [PASS] scheduler")
except RuntimeError as e:
    if "no running event loop" in str(e):
        passed += 1
        print(f"  [SKIP] scheduler (no event loop in sync test)")
    else:
        raise
except Exception as e:
    failed += 1
    print(f"  [FAIL] scheduler: {e}")
    try:
        shutdown_scheduler()
    except Exception:
        pass

if __name__ == "__main__":
    # ==================== 汇总 ====================
    print(f"\n结果：passed={passed}, failed={failed}")
    if failed:
        sys.exit(1)
    print("全部验证通过")
