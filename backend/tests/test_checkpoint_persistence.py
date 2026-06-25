"""Agent Checkpoint 集成测试：多轮对话 + 重启恢复。"""

from __future__ import annotations

import logging
import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _make_state(query: str, conv_id: int = 1, user_id: int = 1) -> dict:
    """构造最小可用的 AgentState。"""
    return {
        "messages": [],
        "current_query": query,
        "conversation_id": conv_id,
        "user_id": user_id,
        "request_id": "test-req",
        "created_at": "2024-01-01T00:00:00",
        "retry_attempt": 0,
        "tool_call_count": 0,
        "regenerate_count": 0,
        "forced_exit": False,
        "is_low_confidence": False,
        "skipped_consistency_check": False,
        "is_error": False,
        "should_refuse": False,
        "refusal_reason": "",
        "content_safe": True,
        "search_results": [],
        "citations": [],
        "confidence": 0.0,
        "query_risk_level": "low",
        "route": "direct",
        "response": f"模拟回答：{query}",
        "consistency_issues": [],
        "fact_issues": [],
        "temporal_warnings": [],
        "history": [],
        "reasoning_chain": [{"step": "route", "decision": "direct", "reason": "测试"}],
        "error": {},
        "partial_effects": [],
        "last_search_query": "",
        "llm_tokens_in": 0,
        "llm_tokens_out": 0,
        "warnings": [],
    }


def test_checkpoint_persistence() -> bool:
    """测试 Checkpoint 持久化 + 重启恢复。"""
    from app.agent.sqlite_checkpoint import SqliteSaver
    from app.agent.graph import get_agent_graph

    tmpdir = tempfile.mkdtemp(prefix="agent_checkpoint_test_")
    db_path = os.path.join(tmpdir, "test_checkpoints.db")
    logger.info("测试数据库: %s", db_path)

    try:
        # ===== 第一步：创建 checkpointer =====
        saver1 = SqliteSaver(db_path=db_path)
        logger.info("✅ 第一步：SqliteSaver 创建成功")

        # ===== 第二步：编译工作流并执行第一轮对话 =====
        app1 = get_agent_graph().compile(db_path=db_path)
        thread_id = "test-thread-001"
        config = {"configurable": {"thread_id": thread_id}}

        result1 = app1.invoke(_make_state("你好"), config)
        logger.info("✅ 第二步：第一轮 invoke 完成，route=%s", result1.get("route"))

        # ===== 第三步：检查 SQLite 是否写入了 checkpoint =====
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT checkpoint_id, checkpoint FROM checkpoints WHERE thread_id = ?",
            (thread_id,),
        ).fetchall()
        conn.close()

        assert len(rows) > 0, "SQLite 中没有找到 checkpoint 数据"
        logger.info("✅ 第三步：SQLite 中找到 %d 条 checkpoint", len(rows))

        # ===== 第四步：模拟重启——新建 SqliteSaver 实例 =====
        saver2 = SqliteSaver(db_path=db_path)
        logger.info("✅ 第四步：模拟重启，新建 SqliteSaver 实例")

        # ===== 第五步：用同一 thread_id 读 checkpoint =====
        tuple1 = saver2.get_tuple(config)
        assert tuple1 is not None, "重启后无法读取 checkpoint"
        restored_id = tuple1.checkpoint.get("id") if hasattr(tuple1.checkpoint, "get") else getattr(tuple1.checkpoint, "id", "unknown")
        logger.info("✅ 第五步：checkpoint 恢复成功，checkpoint_id=%s", restored_id)

        channel_values = tuple1.checkpoint.get("channel_values", {}) if hasattr(tuple1.checkpoint, "get") else {}
        assert channel_values.get("route") == "direct", f"checkpoint route 不匹配: {channel_values.get('route')}"
        assert channel_values.get("response") == "模拟回答：你好", f"checkpoint response 不匹配: {channel_values.get('response')}"
        logger.info("✅ 第五步：checkpoint 内容验证通过")

        # ===== 第六步：基于恢复的 checkpoint 继续对话 =====
        app2 = get_agent_graph().compile(db_path=db_path)
        result2 = app2.invoke(_make_state("谢谢"), config)
        logger.info("✅ 第六步：基于恢复的 checkpoint 继续对话完成，route=%s", result2.get("route"))

        # ===== 第七步：清理 =====
        try:
            os.remove(db_path)
            os.rmdir(tmpdir)
            logger.info("✅ 第七步：测试数据已清理")
        except Exception:
            pass

        return True

    except Exception as e:
        logger.error("❌ 测试失败: %s", str(e), exc_info=True)
        try:
            os.remove(db_path)
            os.rmdir(tmpdir)
        except Exception:
            pass
        return False


if __name__ == "__main__":
    success = test_checkpoint_persistence()
    sys.exit(0 if success else 1)
