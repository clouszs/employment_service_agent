"""Agent 工作流补充测试：verify_facts 引用支持校验、temporal_warnings 填充、accept_with_warning。"""

from __future__ import annotations

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def test_verify_facts_with_citations():
    """测试 verify_facts：事实被引用支持时标记为已核验。"""
    from app.agent.hallucination_defense import fact_verifier

    # 引用与响应中包含相同的政策编号，且响应中政策号前无额外汉字干扰
    response = "国办发〔2024〕5号文件规定了相关政策，补贴为 5000 元。"
    citations = [
        {
            "snippet": "根据国办发〔2024〕5号文件，相关人员可申请补贴。",
            "document_title": "就业政策汇编",
        }
    ]
    issues = fact_verifier.verify(response, citations=citations)
    issue_types = [i.get("fact_type") for i in issues]

    assert "policy_no" in issue_types, "应检测到政策编号"
    policy_issue = next(i for i in issues if i["fact_type"] == "policy_no")
    assert policy_issue["unsupported_values"] == [], f"政策编号应被引用支持，实际未支持: {policy_issue['unsupported_values']}"
    assert policy_issue["supported_count"] >= 1
    logger.info("✅ verify_facts: 政策编号被引用支持，标记为已核验")


def test_verify_facts_unsupported():
    """测试 verify_facts：引用中未找到对应事实时标记为未核验。"""
    from app.agent.hallucination_defense import fact_verifier

    response = "根据国办发〔2024〕99号文件，补贴金额为 5000 元。"
    citations = [
        {
            "snippet": " unrelated content without the policy number or amount",
            "document_title": "其他文档",
        }
    ]
    issues = fact_verifier.verify(response, citations=citations)

    # 至少应检测到 policy_no 或 money 未支持
    unsupported_found = any(i.get("unsupported_values") for i in issues)
    assert unsupported_found, "应检测到未支持的事实要素"
    logger.info(f"✅ verify_facts: 发现未支持事实要素 {[i['fact_type'] for i in issues if i.get('unsupported_values')]}")


def test_verify_facts_no_citations():
    """测试 verify_facts：无引用时，所有事实都标记为未核验。"""
    from app.agent.hallucination_defense import fact_verifier

    response = "补贴金额为 5000 元，政策编号国办发〔2024〕5号。"
    issues = fact_verifier.verify(response, citations=[])
    unsupported_found = any(i.get("unsupported_values") for i in issues)
    assert unsupported_found, "无引用时应标记所有事实为未支持"
    logger.info("✅ verify_facts: 无引用时所有事实标记为未支持")


def test_accept_with_warning_temporal():
    """测试 accept_with_warning：temporal_warnings 被附加到回答中。"""
    from app.agent.nodes import accept_with_warning

    state = {
        "response": "这是回答内容。",
        "is_low_confidence": False,
        "consistency_issues": [],
        "temporal_warnings": [
            "《就业政策A》将于 10 天后过期，建议及时更新。",
        ],
    }
    result = accept_with_warning(state)
    assert result["should_refuse"] is False
    assert any("过期" in w for w in result["warnings"]), "应包含时效性警告"
    logger.info("✅ accept_with_warning: temporal_warnings 被附加到回答")


def test_accept_with_warning_low_confidence():
    """测试 accept_with_warning：低置信度时附加降级提示。"""
    from app.agent.nodes import accept_with_warning

    state = {
        "response": "回答内容。",
        "is_low_confidence": True,
        "consistency_issues": [],
        "temporal_warnings": [],
    }
    result = accept_with_warning(state)
    assert result["is_low_confidence"] is True
    assert any("仅供参考" in w for w in result["warnings"]), "应包含低置信度警告"
    logger.info("✅ accept_with_warning: 低置信度警告正确")


def test_accept_with_warning_medium_consistency():
    """测试 accept_with_warning：中等严重度一致性问题附加警告。"""
    from app.agent.nodes import accept_with_warning

    state = {
        "response": "回答内容。",
        "is_low_confidence": False,
        "consistency_issues": [
            {"severity": "medium", "description": "部分内容可能不一致"}
        ],
        "temporal_warnings": [],
    }
    result = accept_with_warning(state)
    assert any("不一致" in w for w in result["warnings"]), "应包含一致性警告"
    logger.info("✅ accept_with_warning: 中等严重度一致性问题附加警告")


def test_direct_response():
    """测试 direct_response：简单问候的固定回复。"""
    from app.agent.nodes import direct_response

    state = {"current_query": "你好"}
    result = direct_response(state)
    assert result["route"] == "direct"
    assert result["confidence"] == 1.0
    assert "你好" in result["response"]
    logger.info("✅ direct_response: 简单问候返回固定回复")


if __name__ == "__main__":
    test_verify_facts_with_citations()
    test_verify_facts_unsupported()
    test_verify_facts_no_citations()
    test_accept_with_warning_temporal()
    test_accept_with_warning_low_confidence()
    test_accept_with_warning_medium_consistency()
    test_direct_response()
    logger.info("所有补充单元测试通过！")
