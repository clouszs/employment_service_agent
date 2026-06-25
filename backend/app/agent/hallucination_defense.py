"""幻觉防御：动态置信度阈值 + 一致性检查 + 事实核验。"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ==================== 动态置信度阈值 ====================


class DynamicConfidenceThreshold:
    """按查询风险等级使用不同阈值，并支持重试时动态降级。"""

    THRESHOLD_CONFIG = {
        "high":   {"min_confidence": 0.80, "min_results": 3, "require_citation": True},
        "medium": {"min_confidence": 0.65, "min_results": 2, "require_citation": True},
        "low":    {"min_confidence": 0.40, "min_results": 1, "require_citation": False},
    }

    # 每次重试降低的阈值幅度
    _THRESHOLD_STEP: float = 0.15
    # 保底阈值
    _MIN_THRESHOLD: float = 0.30
    # 最大重试次数
    _MAX_RETRY: int = 3

    def classify_query(self, query: str) -> str:
        """按关键词判断风险等级。"""
        high_keywords = [
            "落户", "补贴", "政策", "规定", "流程", "申请", "条件",
            "要求", "资格", "审批", "办理", "报到", "档案", "户口",
        ]
        low_keywords = ["你好", "谢谢", "再见", "辛苦", "在吗", "嗨"]

        if any(k in query for k in high_keywords):
            return "high"
        if any(k in query for k in low_keywords):
            return "low"
        return "medium"

    def should_accept_result(
        self,
        query: str,
        confidence: float,
        results_count: int,
        has_citation: bool,
        retry_attempt: int = 0,
    ) -> tuple[bool, str]:
        """判断是否接受检索结果，每次重试自动降低阈值。

        阈值表与方案对齐（按风险等级 + 重试次数）：

        | 重试次数 | 高风险阈值 | 中风险阈值 | 低风险阈值 | 最低结果数(高/中/低) |
        |----------|-----------|-----------|-----------|-------------------|
        | 0 | 0.80 | 0.65 | 0.40 | 3 / 2 / 1 |
        | 1 | 0.65 | 0.50 | 0.30 | 2 / 2 / 1 |
        | 2 | 0.50 | 0.35 | 0.30 | 2 / 1 / 1 |
        | 3+ | 0.30 | 0.30 | 0.30 | 1 / 1 / 1 |

        返回 (是否接受, 不通过原因字符串，通过则为空)。
        """
        risk_level = self.classify_query(query)
        base_config = self.THRESHOLD_CONFIG[risk_level]

        # 阈值：每次重试降低 0.15，保底不低于 _MIN_THRESHOLD
        threshold = max(self._MIN_THRESHOLD, base_config["min_confidence"] - retry_attempt * self._THRESHOLD_STEP)

        # 最低结果数：按方案精确对齐（与阈值不同步降低）
        min_results_map = {
            0: {"high": 3, "medium": 2, "low": 1},
            1: {"high": 2, "medium": 2, "low": 1},
            2: {"high": 2, "medium": 1, "low": 1},
        }
        min_results = min_results_map.get(min(retry_attempt, 2), {}).get(risk_level, 1)

        reasons: list[str] = []
        if confidence < threshold:
            reasons.append(f"置信度{confidence:.2f} < 当前阈值{threshold}")
        if results_count < min_results:
            reasons.append(f"检索结果数{results_count} < 最低要求{min_results}")
        if base_config["require_citation"] and not has_citation:
            reasons.append("该类查询必须有引用来源")

        return (len(reasons) == 0, "; ".join(reasons))

    def should_retry(self, retry_attempt: int) -> bool:
        """是否还有重试机会。"""
        return retry_attempt < self._MAX_RETRY


# 全局单例
threshold_checker = DynamicConfidenceThreshold()


# ==================== 事实核验 ====================


class FactVerificationPostProcessor:
    """事实核验：正则验证政策编号、日期、金额等。"""

    FACT_RULES = {
        "policy_no": (r"[一-龥]{2,4}〔\d{4}〕\d+号", "政策编号"),
        "date":      (r"\d{4}年\d{1,2}月\d{1,2}日", "日期"),
        "money":     (r"\d+(\.\d+)?(万|千|百)?元", "金额"),
        "count":     (r"\d+(个|项|种|类|份)", "数量"),
    }

    def verify(self, text: str) -> list[dict]:
        """核验文本中的事实要素，返回问题列表。"""
        issues: list[dict] = []
        for fact_type, (pattern, label) in self.FACT_RULES.items():
            matches = re.findall(pattern, text)
            if matches:
                # 当前版本只标记存在的事实要素，不做跨源校验（V2 再加）
                issues.append(
                    {
                        "fact_type": fact_type,
                        "label": label,
                        "values": matches,
                        "note": "已识别，待跨源校验",
                    }
                )
        return issues


fact_verifier = FactVerificationPostProcessor()


# ==================== 一致性检查（V1 简化版）====================


class SelfConsistencyChecker:
    """自我一致性检查：V1 只做轻量标记，不做多轮生成比对。"""

    def check(
        self,
        current_response: str,
        history: list[dict] | None = None,
    ) -> tuple[bool, list[dict]]:
        """检查当前回答是否与历史矛盾。

        V1 简化：只检查"否定词 + 历史关键词"的明显矛盾。
        """
        if not history:
            return True, []

        issues: list[dict] = []
        last_topic = (history[-1].get("last_topic") if history else None)
        if not last_topic:
            return True, []

        current_lower = current_response.lower()
        # 简单规则：历史说"可以"，当前说"不可以" → 标记
        contradiction_pairs = [
            (["可以", "能够", "允许"], ["不可以", "不能", "不允许", "不行"]),
            (["需要", "必须", "要求"], ["不需要", "不必", "不强制"]),
        ]
        for positive, negative in contradiction_pairs:
            has_positive = any(p in current_lower for p in positive)
            has_negative = any(n in current_lower for n in negative)
            if has_positive and has_negative:
                issues.append(
                    {
                        "severity": "medium",
                        "contradiction_type": f"同时包含{positive}和{negative}",
                        "description": "回答内部可能存在矛盾",
                    }
                )

        is_consistent = len(issues) == 0
        return is_consistent, issues


consistency_checker = SelfConsistencyChecker()
