# 阶段 7 进度追踪：外部检索兜底 + 引用溯源（2026-06-26，2026-06-26 优化）

> 目标：当本地知识库无结果或置信度不足时，自动 fallback 到外部检索（Bing MCP），按意图选择站点白名单，并完整溯源到外部来源链接。
> 前置条件：阶段 0-6 全部完成（环境 / Agent 核心 / 幻觉防御 / 监控 / QA 升级 / 路由 Schema / 前端对接）。

---

## 阶段 7 前置条件确认

| 前置 | 状态 | 说明 |
|------|------|------|
| 阶段 0-6 完成 | ✅ | 环境 / Agent / 幻觉防御 / 监控 / QA / 路由 Schema / 前端对接全部完成 |
| Bing MCP | ✅ | 已配置 `bing_search_url` / `fetch_url` |
| `agent_web_search_enabled` | ✅ | 配置项已添加到 `config.py` |

---

## 操作 7-1：安装 `newsapi-python` 依赖（已废弃）

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-26 |
| **模块** | 阶段 7 / 依赖 |
| **修改文件** | `backend/requirements.txt` |
| **操作** | 原计划安装 `newsapi-python>=0.2.0`，后续已迁移到 Bing MCP |

---

## 操作 7-2：新增外部检索配置项

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-26 |
| **模块** | 阶段 7 / 配置 |
| **修改文件** | `backend/app/core/config.py`、`backend/.env` |

**新增配置项：**

| 配置项 | 默认值 | 作用 |
|--------|--------|------|
| `agent_web_search_enabled` | `False` | 是否启用外部检索兜底 |
| `newsapi_page_size` | `5` | 外部检索返回条数（复用此参数控制 Bing 返回条数） |
| `bing_search_url` | MCP 地址 | Bing 搜索 MCP 服务地址 |
| `fetch_url` | MCP 地址 | 网页抓取 MCP 服务地址 |
| `fetch_max_length` | `8000` | 抓取内容最大长度 |
| `government_sites` | `.gov.cn,.edu.cn,...` | 政务站点白名单 |
| `job_sites` | `lagou.com,zhipin.com,...` | 招聘站点白名单 |

---

## 操作 7-3：Bing 搜索工具

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-26 |
| **模块** | 阶段 7 / Agent 工具 |
| **修改文件** | `backend/app/agent/tools.py` |

**实现细节：**

| 组件 | 说明 |
|------|------|
| `bing_search(query, page_size, site_filter)` | 通过 Bing MCP 服务搜索，返回标准化引用片段 |
| 站点过滤 | 支持 `site_filter` 参数，按意图传入站点白名单 |
| 返回格式 | 标准化为 `hits` 列表，包含 `document_title` / `content` / `score` / `metadata` |
| `metadata` | 包含 `source_type=web`、`url`、`source`、`published_at`、`author` |
| 异常处理 | 失败时返回空列表，记录 warning 日志，不影响主流程 |

---

## 操作 7-4：Fetch 网页正文

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-26 |
| **模块** | 阶段 7 / Agent 工具 |
| **修改文件** | `backend/app/agent/tools.py` |

**实现细节：**
- `fetch_webpage(url, max_length)` 通过 Fetch MCP 服务抓取网页正文
- 超时降级：抓取失败不影响主流程，返回 None

---

## 操作 7-5：改造 `search_knowledge` 节点（Bing 分级 fallback）

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-26 + 2026-06-26 优化 |
| **模块** | 阶段 7 / Agent 节点 |
| **修改文件** | `backend/app/agent/nodes.py` |

**改造内容：**

| 场景 | 行为 |
|------|------|
| 本地有结果且置信度足够 | 正常生成回答，不触发 fallback |
| 本地无结果 | fallback 到 bing_search |
| 本地有结果但最高分 < 阈值 | fallback 到 bing_search |
| bing_search 也无结果 | 走拒答/兜底流程 |
| bing_search 有结果 | 对 top 1-2 条同步抓取正文，替换 snippet，用增强后结果生成回答 |

**分级策略：**

| intent | 站点白名单 | 说明 |
|--------|-----------|------|
| web_query | 政务站点白名单 | 政策时效类查询 |
| job_query | 招聘站点白名单 + 本地检索 | 求职招聘类，合并本地结果 |
| kb_query | 无限制 | 兜底知识查询 |

**新增字段：**
- `reasoning_chain` 中记录 `web_fallback: true/false`
- `tool_call_count` 累加 bing_search 调用次数

---

## 操作 7-6：扩展引用追踪支持 web 来源

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-26 |
| **模块** | 阶段 7 / 引用追踪 |
| **修改文件** | `backend/app/agent/citation_tracker.py` |

**扩展内容：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `source_type` | `str` | `local` 或 `web` |
| `url` | `str` | web 来源链接 |
| `source` | `str` | 新闻来源（如 `36氪`） |
| `published_at` | `str` | 发布日期 ISO 格式 |
| `author` | `str` | 作者 |

**兼容性：**
- 本地引用保持原有字段，`source_type` 默认为 `local`
- Web 引用自动附加 `url` / `source` / `published_at` / `author`

---

## 操作 7-7：前端展示 web 来源 + 事实核验提示

| 字段 | 内容 |
|------|------|
| **时间** | 2026-06-26 + 2026-06-26 优化 |
| **模块** | 阶段 7 / 前端展示 |
| **修改文件** | `frontend/src/types/chat.ts`、`frontend/src/components/chat/ReferenceCard.vue`、`frontend/src/components/chat/MessageItem.vue` |

**前端变更：**

| 组件 | 变更 |
|------|------|
| `Reference` 类型 | 新增 `source_type` / `url` / `source` / `published_at` / `author` |
| `ReferenceCard.vue` | 分两区展示：本地来源（蓝色）+ web 来源（黄色，带"查看原文"链接） |
| `MessageItem.vue` | 增加事实核验提示区：展示 `unsupported_values`，标红未找到依据的事实 |
| `AgentAskResult` | `fact_issues` 类型扩展，支持 `label` / `values` / `unsupported_values` 等字段 |
| web 来源标签 | 显示来源名称和发布日期 |
| 外部链接 | 点击可跳转到原始文章 |

---

## 阶段 7 自测

| 测试项 | 结果 | 说明 |
|--------|------|------|
| `bing_search()` 工具 | ✅ | 返回标准化 hits，含 metadata |
| `fetch_webpage()` 工具 | ✅ | 抓取正文，失败降级 |
| `/ask/agent` 接口 | ✅ | HTTP 200 |
| 本地无结果时 fallback | ✅ | 触发 bing_search |
| 前端 ReferenceCard 展示 | ✅ | 本地/web 分色展示 |
| 配置开关 `AGENT_WEB_SEARCH_ENABLED` | ✅ | false 时跳过外部检索 |

**自测命令：**
```bash
# 1. 后端构建
cd backend
.venv/Scripts/python.exe -c "from app.main import app; print('OK')"

# 2. bing_search 工具测试
.venv/Scripts/python.exe -c "
from app.agent.tools import bing_search;
hits = bing_search('上海落户政策', page_size=3);
print(f'hits={len(hits)}');
for h in hits[:3]:
    print('-', h.get('document_title'), '|', h.get('metadata', {}).get('url'))
"

# 3. fetch_webpage 工具测试
.venv/Scripts/python.exe -c "
from app.agent.tools import fetch_webpage;
text = fetch_webpage('https://www.gov.cn/zhengce/');
print(f'length={len(text) if text else 0}')
"

# 4. 前端构建
cd frontend
npm run build
```

---

## 阶段 7 验收

| 优化项 | 状态 | 备注 |
|--------|------|------|
| 配置项 | ✅ | `agent_web_search_enabled` / `government_sites` / `job_sites` |
| Bing 搜索工具 | ✅ | `bing_search()` + `fetch_webpage()` |
| 改造 `search_knowledge` | ✅ | 本地无结果/低置信时 fallback + 分级站点过滤 + 正文抓取 |
| 扩展 `build_citations` | ✅ | 支持 `source_type=web` + url/source/published_at |
| 前端 `ReferenceCard.vue` | ✅ | 本地/web 分色展示 + 外部链接 |
| 前端 `MessageItem.vue` | ✅ | 事实核验提示区 |
| 类型定义更新 | ✅ | `Reference` / `AgentAskResult` 扩展 web 字段 |
| 自测 | ✅ | 工具调用 + 接口调用 + 前端展示均通过 |

---

## 下一阶段预告

| 阶段 | 内容 | 依赖 |
|------|------|------|
| **阶段 8** | 生产部署 + 监控告警完善 | 阶段 7 完成（当前阶段） |

---

## 踩坑记录

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| Bing MCP 工具名不一致 | 不同 MCP 服务暴露的工具名不同（`bing_search` / `bing-cn_search` / `web_search`） | `find_tool()` 支持多候选名匹配 |
| fetch_webpage 超时 | 部分网页加载慢，导致整体响应超时 | 设置合理超时（20s），失败降级为使用 snippet |
| NewsAPI 免费版限制 | 只能搜索过去 30 天新闻，且每小时 100 次 | 迁移到 Bing MCP，无此限制 |
