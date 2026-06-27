# 高校智慧就业服务平台 — 文档中心

> **主索引**：所有设计、实施、进度文档的统一入口
> 更新时间：2026-06-26

---

## 快速导航

| 文档 | 用途 | 适合人群 |
|------|------|----------|
| [设计文档](Agent模块设计文档.md) | Agent 模块 v3.0 权威设计规范、架构决策、面试要点 | 架构师 / 面试 / 方案评审 |
| [实施步骤总览](./implementation/implementation-steps.md) | 各阶段实施步骤结构化清单、工程化模块化整理 | 开发工程师 / 项目经理 |
| [实施指南 — 总览](./implementation/README.md) | 分阶段实施步骤、代码示例、执行检查清单 | 开发工程师 |
| [模块速查](./implementation/module-reference.md) | 全模块文件清单、职责、代码片段 | 日常开发参考 |
| [数据库迁移](./implementation/migration.md) | 表结构变更、迁移脚本、执行验证 | DBA / 后端开发 |
| [进度追踪](./progress/README.md) | 各阶段完成状态、操作日志、风险登记 | 项目经理 / 测试 |
| [项目评估报告](./progress/project-assessment.md) | V4.0 实施前的全面评估与优化建议 | 架构师 / 开发工程师 |
| [工程化框架](./project-framework.md) | 从需求到部署的完整工程流程模板 | 所有角色 / 新项目参考 |

---

## 已完成的增量优化（2026-06-26 之后）

| 优化项 | 说明 | 状态 |
|--------|------|------|
| Bing 分级 fallback 接入 | `search_knowledge` 按 intent 选择站点白名单，top 1-2 条同步抓取正文 | ✅ 已完成 |
| 前端传历史消息 | `sendAgent()` 传最近 6 轮历史，`check_consistency` 跨轮矛盾检测生效 | ✅ 已完成 |
| 前端展示 fact_issues | `MessageItem.vue` 增加事实核验提示区，标红未找到依据的事实 | ✅ 已完成 |
| Graph 编译缓存 | `AgentGraph.compile()` 缓存 compiled graph，避免重复构建 | ✅ 已完成 |
| ChatInput 终止按钮 | 请求进行中显示红色"终止"按钮，Enter 在 sending 时触发 cancel | ✅ 已完成 |
| ChatStore AbortController | `sendAgent()` 创建 AbortController，`cancelSend()` 中断 pending 请求 | ✅ 已完成 |
| SearchBox 纯检索模式 | 点击"纯检索"调用 `POST /search`，将命中片段以助手消息展示 | ✅ 已完成 |
| MonitorView 扩展 | 月度成本选择器 + 手动健康检查按钮 | ✅ 已完成 |

---

## 文档关系

```
docs/README.md                          ← 总索引（本文件）
├── Agent模块设计文档.md                 ← 设计权威参考（v3.0）
│
├── implementation/                      ← 实施指南（工程实现）
│   ├── README.md                        ← 实施总览 + 阶段入口
│   ├── module-reference.md              ← 模块速查（从功能模块文档提取）
│   └── migration.md                     ← 数据库迁移（从功能模块文档提取）
│
├── progress/                            ← 项目进度追踪
│   ├── README.md                        ← 阶段完成状态总览
│   ├── phase-0-environment.md
│   ├── phase-1-agent-core.md
│   ├── phase-2-hallucination-defense.md
│   ├── phase-3-monitoring.md
│   ├── phase-4-qa-upgrade.md
│   ├── phase-5-routing-schema.md
│   ├── phase-6-frontend.md
│   └── bugfixes.md
│
└── 产品介绍文档.md                        ← 产品介绍
```

---

## 按角色阅读

### 我是开发工程师
1. 从 [实施指南总览](./implementation/README.md) 进入
2. 按阶段阅读 [phase-0 ~ phase-6](./progress/)
3. 需要了解某个模块的具体实现 → [模块速查](./implementation/module-reference.md)

### 我是架构师 / 需要评审方案
1. 阅读 [设计文档](Agent模块设计文档.md) 理解设计决策
2. 对照 [实施指南](./implementation/README.md) 确认可落地性

### 我是 DBA / 负责数据库
1. 阅读 [数据库迁移](./implementation/migration.md)
2. 对照 [进度追踪](./progress/README.md) 确认迁移已执行

### 我是测试工程师
1. 阅读 [进度追踪](./progress/README.md) 了解各阶段完成状态
2. 从 [实施指南](./implementation/README.md) 了解各阶段的验收标准

---

## 变更说明

- 原 `Agent模块融合实施方案.md` 和 `功能模块实现文档.md` 已按方案 A 重组
- 设计文档 `Agent模块设计文档.md` 保留不动，作为 v3.0 权威参考
- 实施相关内容已迁入 `docs/implementation/`，按阶段拆分
- 模块速查和迁移脚本已提取为独立文档
