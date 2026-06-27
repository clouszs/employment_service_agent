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

    def verify(self, text: str, citations: list[dict] | None = None) -> list[dict]:
        """核验文本中的事实要素，返回问题列表。

        V1 增强：对提取到的事实要素，检查是否被引用内容支持。
        - 被引用支持 → 标记为"已核验"
        - 未被引用支持 → 标记为"未找到依据"，需用户关注
        """
        issues: list[dict] = []
        citation_text = ""
        if citations:
            citation_text = " ".join(
                (c.get("snippet") or c.get("document_title") or "") for c in citations
            ).lower()

        for fact_type, (pattern, label) in self.FACT_RULES.items():
            matches = re.findall(pattern, text)
            if not matches:
                continue

            unsupported: list[str] = []
            for value in matches:
                # 对 policy_no / date 做精确匹配；money / count 做宽松匹配
                if fact_type in ("policy_no", "date"):
                    if value not in citation_text:
                        unsupported.append(value)
                else:
                    # 金额/数量：检查核心数字是否出现在引用中
                    core = re.sub(r"[^\d.]", "", str(value))
                    if core and core not in citation_text:
                        unsupported.append(value)

            if unsupported:
                issues.append(
                    {
                        "fact_type": fact_type,
                        "label": label,
                        "values": matches,
                        "unsupported_values": unsupported,
                        "note": f"以下{label}在引用中未找到依据：{', '.join(unsupported)}",
                        "supported_count": len(matches) - len(unsupported),
                    }
                )
            else:
                issues.append(
                    {
                        "fact_type": fact_type,
                        "label": label,
                        "values": matches,
                        "unsupported_values": [],
                        "note": f"以下{label}已在引用中找到依据",
                        "supported_count": len(matches),
                    }
                )
        return issues


fact_verifier = FactVerificationPostProcessor()


# ==================== 一致性检查（V1 简化版）====================


class SelfConsistencyChecker:
    """自我一致性检查：V1 轻量版 + 跨轮矛盾检测。"""

    def check(
        self,
        current_response: str,
        history: list[dict] | None = None,
    ) -> tuple[bool, list[dict]]:
        """检查当前回答是否与历史矛盾。

        V1 实现：
        1. 检查当前回答内部是否存在明显矛盾（同时包含正反义词）
        2. 检查当前回答与最后一轮助手回答是否存在跨轮矛盾
        """
        issues: list[dict] = []
        current_lower = current_response.lower()

        # ===== 检查 1：当前回答内部矛盾 =====
        contradiction_pairs = [
            (["可以", "能够", "允许"], ["不可以", "不能", "不允许", "不行"]),
            (["需要", "必须", "要求"], ["不需要", "不必", "不强制"]),
            (["是", "属于", "包含"], ["不是", "不属于", "不包含"]),
            (["有效", "有用", "可行"], ["无效", "没用", "不可行"]),
        ]
        for positive, negative in contradiction_pairs:
            has_positive = any(p in current_lower for p in positive)
            has_negative = any(n in current_lower for n in negative)
            if has_positive and has_negative:
                issues.append(
                    {
                        "severity": "medium",
                        "contradiction_type": f"回答内部同时包含{positive}和{negative}",
                        "description": "回答内部可能存在矛盾",
                        "scope": "internal",
                    }
                )

        # ===== 检查 2：跨轮矛盾（与最后一轮助手回答对比）=====
        if history:
            # 查找最后一轮助手回答
            last_assistant_response = None
            for entry in reversed(history):
                if entry.get("role") == "assistant" or entry.get("type") == "assistant":
                    last_assistant_response = entry.get("content", "")
                    break

            if last_assistant_response:
                last_lower = last_assistant_response.lower()

                # 跨轮矛盾检测：正反义词在不同轮次中出现
                for positive, negative in contradiction_pairs:
                    current_has_positive = any(p in current_lower for p in positive)
                    current_has_negative = any(n in current_lower for n in negative)
                    last_has_positive = any(p in last_lower for p in positive)
                    last_has_negative = any(n in last_lower for n in negative)

                    # 上一轮说"可以"，这一轮说"不可以" → 矛盾
                    if last_has_positive and current_has_negative:
                        issues.append(
                            {
                                "severity": "high",
                                "contradiction_type": f"与上一轮回答矛盾：上一轮包含{positive}，当前轮包含{negative}",
                                "description": f"当前回答与上一轮回答存在矛盾",
                                "scope": "cross_turn",
                                "last_response_excerpt": last_assistant_response[:100],
                            }
                        )
                    elif last_has_negative and current_has_positive:
                        issues.append(
                            {
                                "severity": "high",
                                "contradiction_type": f"与上一轮回答矛盾：上一轮包含{negative}，当前轮包含{positive}",
                                "description": f"当前回答与上一轮回答存在矛盾",
                                "scope": "cross_turn",
                                "last_response_excerpt": last_assistant_response[:100],
                            }
                        )

        is_consistent = len(issues) == 0
        return is_consistent, issues


consistency_checker = SelfConsistencyChecker()
