"""Pydantic schema 包：按模块组织请求/响应模型。

模块划分（与 models 一致）：
  common    —— 通用：分页、ORM基类
  user      —— 用户与权限
  knowledge —— 知识库
  qa        —— 问答与会话
  agent     —— Agent 对话（路由决策、引用、置信度、五重防护）
  monitor   —— 监控告警（知识库健康度、LLM成本、拒答、引用质量）
  ops       —— 运营·安全·质量
"""
