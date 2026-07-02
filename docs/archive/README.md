# 归档区（Archive）

> 本目录存放已被取代或不再维护的历史文档，供追溯参考。
> **最后整理**：2026-07-02

---

## 归档文档清单

### 原始大文档（已拆分为 implementation/ + progress/）

| 文档 | 归档原因 |
|------|----------|
| `Agent模块融合实施方案.md` | 原始实施指南（1699行），内容已分散到 `implementation/` + `progress/` |
| `功能模块实现文档.md` | 原始模块文档（3700行），模块速查→`module-reference.md`，迁移→`migration.md` |
| `前端实施方案.md` | 前端规划文档（755行），已被 `phase-6-frontend.md` + 实际代码覆盖 |

### implementation/ 归档

| 文档 | 归档原因 |
|------|----------|
| `implementation-steps.md` | 旧版（1654行），已被精简版（300行）取代 |
| `missing-frontend-pages.md` | 2026-06-26 快照，大部分缺失页面已补齐 |
| `multi-agent-architecture.md` | 多智能体设计愿景，核心结论已沉淀到 `architecture/ADR` |

### progress/ 归档（历史阶段记录）

| 文档 | 归档原因 |
|------|----------|
| `phase-0-environment.md` | 环境配置细节，仅首次部署需查阅 |
| `phase-1-agent-core.md` | 历史阶段记录，核心设计在 ADR |
| `phase-2-hallucination-defense.md` ~ `phase-9.md` | 同上 |
| `bugfixes.md` | 历史 bug 修复，已融入各 phase 文档 |
| `project-assessment.md` | 2026-06-26 评估，大部分问题已在后续阶段修复 |

---

## 归档原则

1. **只归档，不删除**：Git history 可追溯完整变更
2. **活跃文档不归档**：当前活跃文档在 `docs/` 根目录及各子目录
3. **如需查阅历史细节**：直接在本目录找到对应文件

---

## 活跃文档索引

当前活跃文档请参考 [docs/README.md](../README.md)。
