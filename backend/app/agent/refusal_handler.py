"""拒答回复模板：V1 简化版，统一管理拒答文案。"""


# ===== 拒答模板 =====

# 通用拒答模板
REFUSAL_TEMPLATE = """抱歉，关于"{question}"这个问题：

{reason}

建议您：
1. 联系学校就业中心老师咨询
2. 查看相关政府部门的官方网站
3. 拨打官方咨询热线

如果您还有其他就业相关问题，我很乐意帮助您。"""

# 检索无结果拒答
NO_RESULT_REFUSAL = (
    "很抱歉呀，目前的就业资料里暂时没有找到能回答这个问题的内容～"
    "您可以换个说法再问我，或者咨询就业指导中心的老师，他们会很乐意帮您解答的。"
)

# 低置信度拒答
LOW_CONFIDENCE_REFUSAL = (
    "抱歉，当前资料不足以准确回答您的问题。"
    "建议您联系就业中心老师获取更准确的信息。"
)

# 违规内容拒答
BLOCKED_REFUSAL = "您的提问包含不当或违规内容，已被系统拦截，请调整后重新提问。"

# 一致性冲突拒答
CONSISTENCY_REFUSAL = (
    "抱歉，系统检测到回答可能存在不一致，已拦截。"
    "建议您联系就业中心老师咨询准确信息。"
)

# 事实核验问题拒答
FACT_VERIFICATION_REFUSAL = (
    "抱歉，回答中包含需要核实的关键信息。"
    "建议您登录官方网站核实，或联系就业中心老师确认。"
)


def get_refusal_response(reason: str, question: str = "") -> str:
    """生成拒答回复。

    Args:
        reason: 拒答原因
        question: 用户问题（可选）

    Returns:
        拒答回复文本
    """
    if question:
        return REFUSAL_TEMPLATE.format(question=question, reason=reason)
    return f"抱歉，{reason}。建议您联系就业中心老师咨询，或查看相关政府部门的官方网站。"


def get_refusal_by_type(refusal_type: str, question: str = "") -> str:
    """根据类型获取拒答回复。

    Args:
        refusal_type: 拒答类型（no_result / low_confidence / blocked / consistency / fact）
        question: 用户问题（可选）

    Returns:
        拒答回复文本
    """
    templates = {
        "no_result": NO_RESULT_REFUSAL,
        "low_confidence": LOW_CONFIDENCE_REFUSAL,
        "blocked": BLOCKED_REFUSAL,
        "consistency": CONSISTENCY_REFUSAL,
        "fact": FACT_VERIFICATION_REFUSAL,
    }
    template = templates.get(refusal_type, NO_RESULT_REFUSAL)
    if question and refusal_type == "no_result":
        return REFUSAL_TEMPLATE.format(question=question, reason="资料不足")
    return template
