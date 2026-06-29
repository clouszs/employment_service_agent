# 高校智慧就业服务平台

面向高校就业场景的智能问答与运营平台：学生侧提供带引用溯源的 AI 政策问答、简历助手、职位推荐与就业数据；教师/管理侧提供知识库运营、对话监控、数据看板与系统配置。

## 技术栈

**后端**：FastAPI + SQLAlchemy(MySQL) + LangGraph（单智能体固定流水线）+ 混合 RAG（ChromaDB 向量检索 + FAQ 命中 + 时效调整）+ Redis 语义缓存 + MCP 协议（外部 Bing 搜索 / 网页抓取）+ DashScope qwen。

**前端**：Vue 3 + TypeScript + Pinia + Vue Router + Vite + Element Plus + ECharts。按角色（管理员 / 教师 / 学生）拆分布局与权限路由。

## 架构要点

- **单智能体 + 固定流水线**（非多智能体、非 ReAct）：`route → search → confidence → generate → 五重防护 → END`。
- **五重幻觉防护**：动态置信阈值 / 引用强制 / 自我一致性 / 事实核验 / 内容审核。
- **三层能力定位**：对话推理→图节点；我方确定性业务→service+REST；外部第三方能力→MCP。

## 文档导航

| 目录 | 内容 |
|---|---|
| [docs/architecture/](docs/architecture/) | 架构决策记录（ADR）：检索/智能体/MCP/防护/监控/分层的「何时·为何」 |
| [docs/modules/](docs/modules/) | 当前能力清单：检索工具 / 管理端点 / 监控端点 / 生涯服务 |
| [docs/implementation/](docs/implementation/) | 实施指南、迁移说明、模块参考 |
| [docs/progress/](docs/progress/) | 历史阶段日志（phase-0 ~ phase-11，原始记录） |

新人建议阅读顺序：本文 → [架构决策](docs/architecture/ARCHITECTURE_DECISIONS.md) → [当前能力](docs/modules/CURRENT_CAPABILITIES.md)。

## 本地启动

```bash
# 后端（需 MySQL / Redis / DashScope Key，配置见 backend/app/core/config.py）
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# 前端
cd frontend && npm install && npm run dev
```
