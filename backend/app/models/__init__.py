"""ORM 模型包：统一导出 Base 与四大模块的全部模型。

模块划分：
  user      —— 用户与权限 (sys_*)
  knowledge —— 知识库     (kb_*)
  qa        —— 问答与会话 (qa_*)
  ops       —— 运营·安全·质量 (op_*)
"""

from app.models.base import Base
from app.models.knowledge import (
    KbCategory,
    KbDocument,
    KbDocumentChunk,
    KbFaq,
    KbIndexTask,
    KbSynonym,
)
from app.models.ops import OpEvalCase, OpQueryLog, OpSensitiveWord, OpUnansweredQuestion
from app.models.qa import QaConversation, QaFeedback, QaMessage, QaMessageReference
from app.models.user import SysRole, SysUser, SysUserRole

__all__ = [
    "Base",
    # user
    "SysUser",
    "SysRole",
    "SysUserRole",
    # knowledge
    "KbCategory",
    "KbDocument",
    "KbDocumentChunk",
    "KbSynonym",
    "KbFaq",
    "KbIndexTask",
    # qa
    "QaConversation",
    "QaMessage",
    "QaMessageReference",
    "QaFeedback",
    # ops
    "OpQueryLog",
    "OpSensitiveWord",
    "OpEvalCase",
    "OpUnansweredQuestion",
]
