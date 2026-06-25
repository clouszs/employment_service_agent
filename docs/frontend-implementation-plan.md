# 前端实施方案 — 高校智慧就业服务平台

> **文档版本**：v1.0
> **创建时间**：2026-06-25
> **最后更新**：2026-06-25
> **关联文档**：[Agent模块融合实施方案](../Agent模块融合实施方案.md) · [功能模块实现文档](../功能模块实现文档.md) · [产品介绍文档](../产品介绍文档.md)
> **后端接口总数**：75 个端点（详见下方附录）

---

## 实施状态总览

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1：核心对话界面 | 三栏布局 + SearchBox + askAgent + ChatMessage + ConversationList | ✅ 已完成 |
| Phase 2：统计卡片 | StatsChart + HotQuestions + KbHealthCard + LlmCostCard | 🔄 部分完成（StatsChart 用 StatsOverview 替代） |
| Phase 3：管理页面 | 知识库/运营/监控/用户管理 | ✅ 监控中心已完成，其余页面已存在 |
| Phase 4：视觉特效 | 粒子动画 + 3D 特效 + 数据线条 | ⏸️ V2 再做 |

---

## 一、设计愿景

### 1.1 视觉氛围

**风格定位**：极具未来感的高科技学院风格。

- **背景**：深空蓝渐变（`#0a0e27` → `#1a1f4e`），覆盖全屏
- **动态元素**：流动的抽象数据线条（Canvas 绘制）+ 微弱的点阵网格（CSS radial-gradient 模拟）
- **光影**：核心交互区域有霓虹青蓝色发光效果（`box-shadow: 0 0 30px rgba(0, 255, 255, 0.3)`）
- **字体**：Inter / system-ui 无衬线字体，标题字重 700，正文 400
- **卡片**：半透明磨砂玻璃效果（`backdrop-filter: blur(20px)`）+ 科技感线性边框（`border: 1px solid rgba(0, 255, 255, 0.2)`）
- **3D 元素**：界面角落悬浮 3D 全息地球仪/神经网络节点（Three.js 或 CSS 3D transform 模拟）
- **粒子**：搜索框周围悬浮闪烁的粒子（Canvas 或 CSS animation）

### 1.2 整体布局

```
┌─────────────────────────────────────────────────────────────┐
│  [角色标签：学生 | 老师 | 管理员]                    [用户头像]  │
├───────────┬─────────────────────────────────┬───────────────┤
│           │                                 │               │
│  左侧卡片  │      中央搜索框（磨砂玻璃）        │   右侧卡片     │
│  今日问答   │    🔍 请输入您的问题...           │  热门问题      │
│  统计折线图 │    [AI 图标 + 粒子动画]           │  排行榜        │
│           │                                 │               │
│  [图表区]  │    [历史会话列表]                  │  [排行榜区]    │
│           │                                 │               │
├───────────┴─────────────────────────────────┴───────────────┤
│  底部：知识库状态 / 系统信息                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、页面架构

### 2.1 页面清单

| 页面 | 路径 | 角色 | 说明 |
|------|------|------|------|
| 登录页 | `/login` | 全部 | 用户名 + 密码登录 |
| 聊天主页 | `/` | 学生/老师/管理员 | 核心对话界面 + 统计卡片 |
| 知识库管理 | `/knowledge` | 老师/管理员 | 文档/分类/FAQ/同义词管理 |
| 运营中心 | `/ops` | 老师/管理员 | 日志/反馈/无答案问题/评测集 |
| 监控中心 | `/monitor` | admin/editor | 健康度/成本/拒答记录 |
| 用户管理 | `/users` | admin | 用户 CRUD + 角色分配 |

### 2.2 组件清单

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── AppSidebar.vue          # 侧边导航栏
│   │   ├── AppHeader.vue           # 顶部导航（角色切换 + 用户信息）
│   │   └── RoleSwitcher.vue        # 学生/老师/管理员 标签切换
│   ├── chat/
│   │   ├── SearchBox.vue           # 中央磨砂玻璃搜索框
│   │   ├── ChatMessage.vue         # 单条消息气泡
│   │   ├── CitationCard.vue        # 引用来源卡片
│   │   ├── ConfidenceBadge.vue     # 置信度标签（高/中/低）
│   │   ├── TemporalWarning.vue     # 时效性警告横幅
│   │   ├── RefusalMessage.vue      # 拒答提示 + 建议操作
│   │   └── ConversationList.vue    # 历史会话列表
│   ├── dashboard/
│   │   ├── StatsChart.vue          # 今日问答统计折线图（ECharts）
│   │   ├── HotQuestions.vue        # 热门问题排行榜
│   │   ├── KbHealthCard.vue        # 知识库健康度卡片
│   │   ├── LlmCostCard.vue         # LLM 成本卡片
│   │   └── RefusalStatsCard.vue    # 拒答统计卡片
│   ├── knowledge/
│   │   ├── DocumentTable.vue       # 文档列表表格
│   │   ├── CategoryTree.vue        # 分类树
│   │   ├── FaqTable.vue            # FAQ 管理表格
│   │   └── SynonymTable.vue        # 同义词管理表格
│   ├── ops/
│   │   ├── QueryLogTable.vue       # 问答日志表格
│   │   ├── FeedbackTable.vue       # 反馈明细表格
│   │   ├── UnansweredTable.vue     # 无答案问题表格
│   │   └── EvalCaseTable.vue       # 评测集表格
│   └── monitor/
│       ├── KbHealthPanel.vue       # 知识库健康度面板
│       ├── LlmCostPanel.vue        # LLM 成本面板
│       └── RefusalPanel.vue        # 拒答记录面板
└── views/
    ├── LoginView.vue               # 已有
    ├── ChatView.vue                # 核心对话页（需重设计）
    ├── KnowledgeView.vue           # 知识库管理页
    ├── OpsView.vue                 # 运营中心页
    ├── MonitorView.vue             # 监控中心页
    └── UserManageView.vue          # 用户管理页
```

---

## 三、聊天主页（核心页面）— 按钮/交互与接口映射

### 3.1 整体结构

```
ChatView.vue
├── AppSidebar（左侧导航）
│   ├── 对话
│   ├── 知识库
│   ├── 运营
│   └── 监控
├── AppHeader（顶部）
│   ├── Logo + 标题
│   ├── RoleSwitcher（学生/老师/管理员）
│   └── 用户头像 + 下拉菜单
├── 主体区域
│   ├── 左侧面板（StatisticsPanel）
│   │   ├── StatsChart（今日问答统计折线图）
│   │   └── KbHealthCard（知识库健康度摘要）
│   ├── 中央面板（ChatPanel）
│   │   ├── SearchBox（搜索输入框）
│   │   ├── ChatMessage列表
│   │   ├── CitationCard（引用卡片）
│   │   └── ConversationList（历史会话）
│   └── 右侧面板（InfoPanel）
│       ├── HotQuestions（热门问题排行榜）
│       └── LlmCostCard（LLM 成本摘要）
└── 底部状态栏
```

### 3.2 左侧面板 — 统计卡片

#### 组件：`StatsChart.vue`（今日问答统计折线图）

| 交互元素 | 类型 | 对应接口 | 请求方式 | 说明 |
|----------|------|----------|----------|------|
| 页面加载时自动拉取数据 | 自动 | `GET /api/v1/stats/overview` | GET | 获取今日问答总数、无答案率、点赞率 |
| 页面加载时自动拉取数据 | 自动 | `GET /api/v1/logs/queries?page=1&size=50` | GET | 获取今日问答日志，用于绘制折线图（按小时聚合） |

**响应数据映射：**

| 图表元素 | 数据来源 | 字段 |
|----------|----------|------|
| 折线图 Y 轴（问答数） | `logs/queries` 返回的 `items` | 按 `created_at` 小时分组，count |
| 折线图 X 轴（时间） | `items[].created_at` | 提取小时 |
| 无答案率标注 | `stats/overview` | `no_answer_rate` |
| 点赞率标注 | `stats/overview` | `like_rate` |

#### 组件：`KbHealthCard.vue`（知识库健康度摘要）

| 交互元素 | 类型 | 对应接口 | 请求方式 | 说明 |
|----------|------|----------|----------|------|
| 页面加载时自动拉取 | 自动 | `GET /api/v1/kb-health/latest` | GET | 获取最新健康度快照 |
| 点击"查看详情"按钮 | 点击 | 路由跳转 `/monitor` | — | 跳转到监控中心 |
| 点击"立即检查"按钮 | 点击 | `POST /api/v1/kb-health/run` | POST | 手动触发健康检查（需 admin） |

**响应数据映射：**

| 卡片元素 | 数据来源 | 字段 |
|----------|----------|------|
| 健康度分数（大数字） | `check_date` 返回的 `health_score` | `health_score`（0-100） |
| 即将过期文档数 | 同上 | `warning_count` |
| 已过期文档数 | 同上 | `expired_count` |
| 文档总数 | 同上 | `total_docs` |
| 检查日期 | 同上 | `check_date` |
| 颜色指示 | `health_score` | ≥80 绿色，60-80 黄色，<60 红色 |

### 3.3 中央面板 — 搜索与对话

#### 组件：`SearchBox.vue`（中央搜索框）

| 交互元素 | 类型 | 对应接口 | 请求方式 | 说明 |
|----------|------|----------|----------|------|
| 输入问题后按 Enter 或点击搜索按钮 | 点击/键盘 | `POST /api/v1/ask/agent` | POST | Agent 问答（主流程） |
| 点击"纯检索"按钮 | 点击 | `POST /api/v1/search` | POST | 纯向量检索，不生成回答 |
| 输入框获得焦点 | 事件 | — | — | 触发粒子动画加速 |
| 输入框失去焦点 | 事件 | — | — | 粒子动画减速 |

**请求体：**

```json
// POST /api/v1/ask/agent
{
  "query": "上海落户政策是什么？",
  "conversation_id": null
}

// POST /api/v1/search
{
  "query": "上海落户政策",
  "top_k": 5
}
```

**响应数据映射：**

| 界面元素 | 数据来源 | 字段 |
|----------|----------|------|
| AI 回答文本 | `response` | `response` |
| 置信度标签 | `ConfidenceBadge` | `confidence`（0-1） |
| 路由标签 | 小标签 | `route`（search/direct/refuse/regenerated/cached/error） |
| 引用卡片列表 | `CitationCard` | `citations[]`（document_id/chunk_id/score/snippet） |
| 时效性警告 | `TemporalWarning` | `temporal_warnings[]` |
| 一致性警告 | 小提示 | `consistency_issues[]` |
| 事实核验警告 | 小提示 | `fact_issues[]` |
| 系统警告 | 底部提示条 | `warnings[]` |
| 拒答提示 | `RefusalMessage` | `is_no_answer=true` 时显示 |

#### 组件：`ChatMessage.vue`（单条消息气泡）

| 交互元素 | 类型 | 对应接口 | 请求方式 | 说明 |
|----------|------|----------|----------|------|
| 用户消息 | 显示 | — | — | 右侧气泡，深色背景 |
| AI 回答 | 显示 | — | — | 左侧气泡，带发光边框 |
| 点赞按钮 | 点击 | `POST /api/v1/messages/{message_id}/feedback` | POST | `rating=1` |
| 点踩按钮 | 点击 | `POST /api/v1/messages/{message_id}/feedback` | POST | `rating=-1`，弹出原因输入框 |
| 查看引用 | 点击 | `GET /api/v1/messages/{message_id}/references` | GET | 展开引用卡片 |
| 复制回答 | 点击 | — | — | 调用 Clipboard API |

**反馈请求体：**

```json
// POST /api/v1/messages/123/feedback
{
  "rating": 1,
  "reason": null
}
```

#### 组件：`ConversationList.vue`（历史会话列表）

| 交互元素 | 类型 | 对应接口 | 请求方式 | 说明 |
|----------|------|----------|----------|------|
| 页面加载时拉取会话列表 | 自动 | `GET /api/v1/conversations?page=1&size=20` | GET | 获取当前用户会话列表 |
| 点击会话项 | 点击 | `GET /api/v1/conversations/{id}` | GET | 加载会话详情（含消息） |
| 新建会话按钮 | 点击 | `POST /api/v1/conversations` | POST | 创建新会话 |
| 重命名会话 | 双击/编辑按钮 | `PUT /api/v1/conversations/{id}` | PUT | 更新会话标题 |
| 删除会话 | 点击删除图标 | `DELETE /api/v1/conversations/{id}` | DELETE | 软删除会话 |

### 3.4 右侧面板 — 信息卡片

#### 组件：`HotQuestions.vue`（热门问题排行榜）

| 交互元素 | 类型 | 对应接口 | 请求方式 | 说明 |
|----------|------|----------|----------|------|
| 页面加载时自动拉取 | 自动 | `GET /api/v1/stats/hot-questions?limit=10` | GET | 获取高频问题排行 |

**响应数据映射：**

| 列表元素 | 数据来源 | 字段 |
|----------|----------|------|
| 排名序号 | 数组索引 | — |
| 问题文本 | `question` | `question` |
| 命中次数 | `hit_count` | `hit_count` |
| 最后一问时间 | `last_asked_at` | `last_asked_at` |
| 点击问题 | 点击 | 自动填入搜索框 | `query` |

#### 组件：`LlmCostCard.vue`（LLM 成本摘要）

| 交互元素 | 类型 | 对应接口 | 请求方式 | 说明 |
|----------|------|----------|----------|------|
| 页面加载时自动拉取 | 自动 | `GET /api/v1/llm-cost/daily` | GET | 获取今日成本汇总 |
| 点击"查看详情"按钮 | 点击 | 路由跳转 `/monitor` | — | 跳转到监控中心 |

**响应数据映射：**

| 卡片元素 | 数据来源 | 字段 |
|----------|----------|------|
| 今日总成本 | `total_cost_usd` | `total_cost_usd`（USD） |
| 今日调用次数 | `total_calls` | `total_calls` |
| 按模型拆分 | `models[]` | `model` / `cost_usd` / `call_count` |
| 成本条 | 可视化 | `models[].cost_usd / total_cost_usd` |

---

## 四、角色标签 — 权限与界面切换

### 4.1 角色定义

后端实际采用两层权限体系：
- `user_type`：用户类型（1学生/2毕业生/3辅导员/4老师/5管理员）
- `role_code`：RBAC 角色编码（`admin` / `editor` / `student`）

前端角色标签映射：

| 前端标签 | 对应 role_code | 对应 user_type | 可用功能 | 可访问页面 |
|----------|---------------|---------------|----------|------------|
| 学生 | `student` | 1/2 | 对话问答、查看自己的会话/消息 | 聊天主页 |
| 老师 | `editor` | 3/4 | 对话问答 + 知识库管理 + 运营中心 | 聊天主页 + 知识库 + 运营 |
| 管理员 | `admin` | 5 | 全部功能 + 用户管理 + 监控中心 | 全部页面 |

> **注意**：后端没有独立的 "HR" 角色编码。辅导员(user_type=3) 和老师(user_type=4) 在 RBAC 层面共用 `editor` 角色，权限相同。
> 若业务上需要区分辅导员和老师的权限，需先在后台 `sys_role` 表中新增独立角色编码，再调整前端标签。

### 4.2 角色切换实现

- **前端存储**：登录时获取用户的 `role_code` 列表，存储在 Pinia `useAuthStore`
- **UI 切换**：`RoleSwitcher.vue` 根据最高权限角色显示对应标签（student → 学生，editor → 老师，admin → 管理员）
- **API 权限**：后端通过 `require_roles("admin")` / `require_roles("admin", "editor")` 控制，前端仅做 UI 隐藏，不替代后端鉴权

---

## 五、各页面接口映射总表

### 5.1 聊天主页（ChatView）

| UI 区域 | 组件 | 触发时机 | 接口 | 方法 | 权限 |
|---------|------|----------|------|------|------|
| 搜索框 | SearchBox | 输入后回车/点击搜索 | `POST /api/v1/ask/agent` | POST | 登录用户 |
| 纯检索按钮 | SearchBox | 点击 | `POST /api/v1/search` | POST | 登录用户 |
| 会话列表 | ConversationList | 页面加载 | `GET /api/v1/conversations` | GET | 登录用户 |
| 会话详情 | ConversationList | 点击会话 | `GET /api/v1/conversations/{id}` | GET | 登录用户 |
| 新建会话 | ConversationList | 点击新建 | `POST /api/v1/conversations` | POST | 登录用户 |
| 删除会话 | ConversationList | 点击删除 | `DELETE /api/v1/conversations/{id}` | DELETE | 登录用户 |
| 点赞/点踩 | ChatMessage | 点击 | `POST /api/v1/messages/{id}/feedback` | POST | 登录用户 |
| 查看引用 | ChatMessage | 点击引用 | `GET /api/v1/messages/{id}/references` | GET | 登录用户 |
| 统计图表 | StatsChart | 页面加载 | `GET /api/v1/stats/overview` | GET | admin/editor |
| 统计图表 | StatsChart | 页面加载 | `GET /api/v1/logs/queries` | GET | admin/editor |
| 健康度卡片 | KbHealthCard | 页面加载 | `GET /api/v1/kb-health/latest` | GET | admin/editor |
| 健康度检查 | KbHealthCard | 点击"立即检查" | `POST /api/v1/kb-health/run` | POST | admin |
| 热门问题 | HotQuestions | 页面加载 | `GET /api/v1/stats/hot-questions` | GET | admin/editor |
| 成本卡片 | LlmCostCard | 页面加载 | `GET /api/v1/llm-cost/daily` | GET | admin/editor |

### 5.2 知识库管理页（KnowledgeView）

| UI 区域 | 组件 | 触发时机 | 接口 | 方法 | 权限 |
|---------|------|----------|------|------|------|
| 分类列表 | CategoryTree | 页面加载 | `GET /api/v1/categories` | GET | 登录用户 |
| 新建分类 | CategoryTree | 点击新建 | `POST /api/v1/categories` | POST | admin/editor |
| 修改分类 | CategoryTree | 点击编辑 | `PUT /api/v1/categories/{id}` | PUT | admin/editor |
| 删除分类 | CategoryTree | 点击删除 | `DELETE /api/v1/categories/{id}` | DELETE | admin/editor |
| 文档列表 | DocumentTable | 页面加载/筛选 | `GET /api/v1/documents` | GET | 登录用户 |
| 文档详情 | DocumentTable | 点击查看 | `GET /api/v1/documents/{id}` | GET | 登录用户 |
| 上传文档 | DocumentTable | 点击上传 | `POST /api/v1/documents` | POST | admin/editor |
| 修改文档 | DocumentTable | 点击编辑 | `PUT /api/v1/documents/{id}` | PUT | admin/editor |
| 删除文档 | DocumentTable | 点击删除 | `DELETE /api/v1/documents/{id}` | DELETE | admin/editor |
| 文档分片 | DocumentTable | 点击查看分片 | `GET /api/v1/documents/{id}/chunks` | GET | 登录用户 |
| 解析文档 | DocumentTable | 点击解析 | `POST /api/v1/documents/{id}/parse` | POST | admin/editor |
| 向量化 | DocumentTable | 点击索引 | `POST /api/v1/documents/{id}/index` | POST | admin/editor |
| FAQ 列表 | FaqTable | 页面加载 | `GET /api/v1/faqs` | GET | 登录用户 |
| FAQ CRUD | FaqTable | 增删改 | `POST/PUT/DELETE /api/v1/faqs/{id}` | — | admin/editor |
| 同义词列表 | SynonymTable | 页面加载 | `GET /api/v1/synonyms` | GET | 登录用户 |
| 同义词 CRUD | SynonymTable | 增删改 | `POST/PUT/DELETE /api/v1/synonyms/{id}` | — | admin/editor |

### 5.3 运营中心页（OpsView）

| UI 区域 | 组件 | 触发时机 | 接口 | 方法 | 权限 |
|---------|------|----------|------|------|------|
| 问答日志 | QueryLogTable | 页面加载 | `GET /api/v1/logs/queries` | GET | admin/editor |
| 反馈统计 | FeedbackTable | 页面加载 | `GET /api/v1/feedback/stats` | GET | admin/editor |
| 反馈明细 | FeedbackTable | 页面加载 | `GET /api/v1/feedback` | GET | admin/editor |
| 无答案问题 | UnansweredTable | 页面加载 | `GET /api/v1/unanswered` | GET | admin/editor |
| 处理无答案 | UnansweredTable | 点击处理 | `PUT /api/v1/unanswered/{id}` | PUT | admin/editor |
| 删除无答案 | UnansweredTable | 点击删除 | `DELETE /api/v1/unanswered/{id}` | DELETE | admin/editor |
| 评测集列表 | EvalCaseTable | 页面加载 | `GET /api/v1/eval-cases` | GET | 登录用户 |
| 执行评测 | EvalCaseTable | 点击执行 | `POST /api/v1/eval-cases/run` | POST | admin/editor |
| 评测用例 CRUD | EvalCaseTable | 增删改 | `POST/PUT/DELETE /api/v1/eval-cases/{id}` | — | admin/editor |

### 5.4 监控中心页（MonitorView）

| UI 区域 | 组件 | 触发时机 | 接口 | 方法 | 权限 |
|---------|------|----------|------|------|------|
| 健康度快照 | KbHealthPanel | 页面加载 | `GET /api/v1/kb-health/latest` | GET | admin/editor |
| 健康度历史 | KbHealthPanel | 切换标签 | `GET /api/v1/kb-health/history` | GET | admin/editor |
| 手动检查 | KbHealthPanel | 点击按钮 | `POST /api/v1/kb-health/run` | POST | admin |
| 日成本 | LlmCostPanel | 页面加载 | `GET /api/v1/llm-cost/daily` | GET | admin/editor |
| 月成本 | LlmCostPanel | 切换月份 | `GET /api/v1/llm-cost/monthly` | GET | admin/editor |
| 成本历史 | LlmCostPanel | 切换标签 | `GET /api/v1/llm-cost/history` | GET | admin/editor |
| 拒答列表 | RefusalPanel | 页面加载 | `GET /api/v1/refusal/list` | GET | admin/editor |
| 拒答统计 | RefusalPanel | 页面加载 | `GET /api/v1/refusal/stats` | GET | admin/editor |

### 5.5 用户管理页（UserManageView）

| UI 区域 | 组件 | 触发时机 | 接口 | 方法 | 权限 |
|---------|------|----------|------|------|------|
| 用户列表 | UserTable | 页面加载 | `GET /api/v1/users` | GET | 登录用户 |
| 用户详情 | UserTable | 点击查看 | `GET /api/v1/users/{id}` | GET | 登录用户 |
| 新建用户 | UserTable | 点击新建 | `POST /api/v1/users` | POST | admin |
| 修改用户 | UserTable | 点击编辑 | `PUT /api/v1/users/{id}` | PUT | admin |
| 禁用用户 | UserTable | 点击禁用 | `DELETE /api/v1/users/{id}` | DELETE | admin |
| 物理删除 | UserTable | 点击删除 | `DELETE /api/v1/users/{id}/permanent` | DELETE | admin |
| 重置密码 | UserTable | 点击重置 | `POST /api/v1/users/{id}/reset-password` | POST | admin |
| 查看角色 | UserTable | 点击角色 | `GET /api/v1/users/{id}/roles` | GET | 登录用户 |
| 分配角色 | UserTable | 点击分配 | `PUT /api/v1/users/{id}/roles` | PUT | admin |

---

## 六、API 层实现规划

### 6.1 现有 API 文件

| 文件 | 已有接口数 | 状态 |
|------|-----------|------|
| `frontend/src/api/auth.ts` | 3 | ✅ 已实现 |
| `frontend/src/api/user.ts` | 8 | ✅ 已实现 |
| `frontend/src/api/knowledge.ts` | 8 | ✅ 已实现 |
| `frontend/src/api/chat.ts` | 4 | ✅ 已实现（ask / search / askAgent / getMessageReferences） |
| `frontend/src/api/conversation.ts` | 7 | ✅ 已实现 |
| `frontend/src/api/stats.ts` | 2 | ✅ 已实现 |
| `frontend/src/api/ops.ts` | 6 | ✅ 已实现 |

### 6.2 待实现 API 文件

| 文件 | 需要新增的接口 | 优先级 |
|------|---------------|--------|
| `frontend/src/api/indexTasks.ts` | `getIndexTasks()` | P2 |

### 6.3 已实现 API 文件

| 文件 | 新增内容 | 状态 |
|------|----------|------|
| `frontend/src/api/chat.ts` | `askAgent()`、`getMessageReferences()` | ✅ |
| `frontend/src/api/monitor.ts` | `getKbHealthLatest()` / `getKbHealthHistory()` / `runKbHealthCheck()` / `getLlmCostDaily()` / `getLlmCostMonthly()` / `getLlmCostHistory()` / `getRefusalList()` / `getRefusalStats()` | ✅ |

### 6.3 请求拦截器

**已有：** `frontend/src/api/request.ts` 处理 JWT Token 注入、统一错误处理、401 跳转登录页。

**状态：**
- 401 跳转登录页逻辑 ✅ 已实现
- 403 权限不足提示 ✅ 已由 ElMessage 统一处理
- SSE 流式响应 ⏸️ V2 再做

---

**已有：** `frontend/src/api/request.ts` 处理 JWT Token 注入、统一错误处理、401 跳转登录页。

**状态：**
- 401 跳转登录页逻辑 ✅ 已实现
- 403 权限不足提示 ✅ 已由 ElMessage 统一处理
- SSE 流式响应 ⏸️ V2 再做

---

## 七、状态管理规划

### 7.1 Pinia Store 清单

| Store | 职责 | 已有？ |
|-------|------|--------|
| `useAuthStore` | 用户信息、Token、角色 | ⚠️ 需确认 |
| `useChatStore` | 当前会话、消息列表、加载状态 | ✅ 已实现 |
| `useConversationStore` | 会话列表、当前会话 ID | ⚠️ 部分存在 |
| `useMonitorStore` | 健康度/成本/拒答数据 | ✅ 已实现 |

### 7.2 关键状态流转

```
用户输入问题
  → SearchBox 触发 askAgent()
  → ChatStore 设置 loading=true
  → API 返回 enriched response
  → ChatStore 追加用户消息 + AI 消息
  → ChatMessage 渲染 citation/warning/temporal
  → 同时更新 StatsChart 数据（增量）
```

---

## 八、技术栈确认

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 框架 | Vue 3 (Composition API) | 已有 |
| 路由 | Vue Router 4 | 已有 |
| 状态管理 | Pinia | 已有/需确认 |
| HTTP 客户端 | Axios | 已有 |
| UI 组件 | Element Plus | 已有 |
| 图表 | ECharts | 需安装 |
| 3D 效果 | CSS 3D Transform / Three.js | 建议先用 CSS 实现，性能更好 |
| 动画 | CSS Animation + requestAnimationFrame | 粒子效果 |
| 样式 | `<style scoped>` + CSS 变量 | 保持项目风格一致 |

---

## 九、实施优先级

### Phase 1：核心对话界面（P0）

1. 重设计 `ChatView.vue` — 三栏布局 + 深空蓝主题
2. 实现 `SearchBox.vue` — 磨砂玻璃搜索框 + 粒子动画
3. 对接 `askAgent()` 接口 — 完整响应渲染
4. 实现 `ChatMessage.vue` — 消息气泡 + 引用卡片 + 反馈按钮
5. 实现 `ConversationList.vue` — 历史会话侧边栏

### Phase 2：统计卡片（P1）

1. 实现 `StatsChart.vue` — ECharts 折线图
2. 实现 `HotQuestions.vue` — 热门问题排行榜
3. 实现 `KbHealthCard.vue` / `LlmCostCard.vue` — 监控摘要卡片

### Phase 3：管理页面（P2）

1. 知识库管理页（文档/分类/FAQ/同义词）
2. 运营中心页（日志/反馈/无答案/评测集）
3. 监控中心页（健康度/成本/拒答）
4. 用户管理页

### Phase 4：视觉特效（P3）

1. 搜索框粒子动画
2. 3D 全息地球仪/神经网络节点
3. 流动数据线条背景
4. 点阵网格背景

---

## 十、附录：后端接口完整清单

### 认证模块（3 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 1 | POST | `/api/v1/auth/login` | 登录获取令牌 | ✅ |
| 2 | GET | `/api/v1/auth/me` | 获取当前用户 | ✅ |
| 3 | POST | `/api/v1/auth/change-password` | 修改密码 | ✅ |

### 用户管理（9 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 4 | GET | `/api/v1/users` | 用户列表 | ✅ |
| 5 | GET | `/api/v1/users/{id}` | 用户详情 | ❌ |
| 6 | POST | `/api/v1/users` | 新建用户 | ✅ |
| 7 | PUT | `/api/v1/users/{id}` | 修改用户 | ✅ |
| 8 | DELETE | `/api/v1/users/{id}` | 禁用用户 | ✅ |
| 9 | DELETE | `/api/v1/users/{id}/permanent` | 物理删除 | ✅ |
| 10 | POST | `/api/v1/users/{id}/reset-password` | 重置密码 | ✅ |
| 11 | GET | `/api/v1/users/{id}/roles` | 查看角色 | ✅ |
| 12 | PUT | `/api/v1/users/{id}/roles` | 分配角色 | ✅ |

### 角色管理（3 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 13 | GET | `/api/v1/roles` | 角色列表 | ✅ |
| 14 | POST | `/api/v1/roles` | 新建角色 | ✅ |
| 15 | PUT | `/api/v1/roles/{id}` | 修改角色 | ✅ |

### 知识库管理（20 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 16 | GET | `/api/v1/categories` | 分类列表 | ✅ |
| 17 | POST | `/api/v1/categories` | 新建分类 | ✅ |
| 18 | PUT | `/api/v1/categories/{id}` | 修改分类 | ✅ |
| 19 | DELETE | `/api/v1/categories/{id}` | 删除分类 | ✅ |
| 20 | GET | `/api/v1/documents` | 文档列表 | ✅ |
| 21 | GET | `/api/v1/documents/{id}` | 文档详情 | ✅ |
| 22 | POST | `/api/v1/documents` | 上传文档 | ✅ |
| 23 | PUT | `/api/v1/documents/{id}` | 修改文档 | ✅ |
| 24 | DELETE | `/api/v1/documents/{id}` | 删除文档 | ✅ |
| 25 | GET | `/api/v1/documents/{id}/chunks` | 查看分片 | ✅ |
| 26 | POST | `/api/v1/documents/{id}/parse` | 解析文档 | ✅ |
| 27 | POST | `/api/v1/documents/{id}/index` | 向量化 | ✅ |
| 28 | GET | `/api/v1/index-tasks` | 索引任务列表 | ❌ |
| 29 | GET | `/api/v1/faqs` | FAQ 列表 | ✅ |
| 30 | POST | `/api/v1/faqs` | 新建 FAQ | ✅ |
| 31 | PUT | `/api/v1/faqs/{id}` | 修改 FAQ | ✅ |
| 32 | DELETE | `/api/v1/faqs/{id}` | 删除 FAQ | ✅ |
| 33 | GET | `/api/v1/synonyms` | 同义词列表 | ✅ |
| 34 | POST | `/api/v1/synonyms` | 新建同义词 | ✅ |
| 35 | PUT | `/api/v1/synonyms/{id}` | 修改同义词 | ✅ |
| 36 | DELETE | `/api/v1/synonyms/{id}` | 删除同义词 | ✅ |

### 问答与会话（10 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 37 | POST | `/api/v1/search` | 纯向量检索 | ✅ |
| 38 | POST | `/api/v1/ask` | 同步问答 | ✅ |
| 39 | POST | `/api/v1/ask/stream` | 流式问答(SSE) | ⏸️ V2 再做 |
| 40 | POST | `/api/v1/ask/agent` | Agent 问答 | ✅ |
| 41 | POST | `/api/v1/chat` | Agent 同步对话 | ⏸️ V2 再做 |
| 42 | GET | `/api/v1/conversations` | 会话列表 | ✅ |
| 43 | POST | `/api/v1/conversations` | 新建会话 | ✅ |
| 44 | GET | `/api/v1/conversations/{id}` | 会话详情 | ✅ |
| 45 | PUT | `/api/v1/conversations/{id}` | 重命名会话 | ✅ |
| 46 | DELETE | `/api/v1/conversations/{id}` | 删除会话 | ✅ |

### 消息与反馈（4 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 47 | POST | `/api/v1/messages/{id}/feedback` | 点赞/点踩 | ✅ |
| 48 | GET | `/api/v1/messages/{id}/references` | 查看引用 | ✅ |
| 49 | GET | `/api/v1/conversations/{id}/messages` | 会话消息列表 | ✅ |
| 50 | GET | `/api/v1/messages` | — | — |

### 运营模块（10 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 51 | GET | `/api/v1/sensitive-words` | 敏感词列表 | ✅ |
| 52 | POST | `/api/v1/sensitive-words` | 新建敏感词 | ✅ |
| 53 | PUT | `/api/v1/sensitive-words/{id}` | 修改敏感词 | ✅ |
| 54 | DELETE | `/api/v1/sensitive-words/{id}` | 删除敏感词 | ✅ |
| 55 | GET | `/api/v1/logs/queries` | 问答日志 | ✅ |
| 56 | GET | `/api/v1/stats/overview` | 统计概览 | ✅ |
| 57 | GET | `/api/v1/stats/hot-questions` | 高频问题 | ✅ |
| 58 | POST | `/api/v1/eval-cases/run` | 执行评测 | ✅ |
| 59 | GET | `/api/v1/eval-cases` | 评测集列表 | ✅ |
| 60 | POST | `/api/v1/eval-cases` | 新建评测 | ✅ |
| 61 | PUT | `/api/v1/eval-cases/{id}` | 修改评测 | ✅ |
| 62 | DELETE | `/api/v1/eval-cases/{id}` | 删除评测 | ✅ |
| 63 | GET | `/api/v1/feedback/stats` | 反馈统计 | ✅ |
| 64 | GET | `/api/v1/feedback` | 反馈明细 | ✅ |
| 65 | GET | `/api/v1/unanswered` | 无答案列表 | ✅ |
| 66 | PUT | `/api/v1/unanswered/{id}` | 标记处理 | ✅ |
| 67 | DELETE | `/api/v1/unanswered/{id}` | 删除记录 | ✅ |

### 监控模块（8 个）

| # | 方法 | 路径 | 摘要 | 前端状态 |
|---|------|------|------|----------|
| 68 | GET | `/api/v1/kb-health/latest` | 健康度快照 | ✅ |
| 69 | GET | `/api/v1/kb-health/history` | 健康度历史 | ✅ |
| 70 | POST | `/api/v1/kb-health/run` | 手动检查 | ✅ |
| 71 | GET | `/api/v1/llm-cost/daily` | 日成本 | ✅ |
| 72 | GET | `/api/v1/llm-cost/monthly` | 月成本 | ✅ |
| 73 | GET | `/api/v1/llm-cost/history` | 成本历史 | ✅ |
| 74 | GET | `/api/v1/refusal/list` | 拒答列表 | ✅ |
| 75 | GET | `/api/v1/refusal/stats` | 拒答统计 | ✅ |

---

## 十一、接口优先级矩阵

| 优先级 | 接口 | 所属页面 | 工作量估算 |
|--------|------|----------|-----------|
| **P0** | `ask/agent` | 聊天主页 | 高（核心流程） |
| **P0** | `search` | 聊天主页 | 低 |
| **P0** | `conversations` CRUD | 聊天主页 | 中 |
| **P0** | `auth/login` | 登录页 | 低（已有） |
| **P1** | `stats/overview` + `logs/queries` | 聊天主页 | 中 |
| **P1** | `hot-questions` | 聊天主页 | 低 |
| **P1** | `kb-health/latest` | 聊天主页 | 低 |
| **P1** | `llm-cost/daily` | 聊天主页 | 低 |
| **P1** | `messages/{id}/feedback` | 聊天主页 | 低 |
| **P1** | `messages/{id}/references` | 聊天主页 | 低 |
| **P2** | 知识库 CRUD | 知识库管理 | 中 |
| **P2** | 运营 CRUD | 运营中心 | 中 |
| **P2** | 用户管理 CRUD | 用户管理 | 中 |
| **P2** | 监控全套 | 监控中心 | 中 |
| **P3** | `ask/stream` (SSE) | 聊天主页 | 高 |
| **P3** | 3D 特效 | 全局 | 高 |

---

## 十二、实施建议

1. **Phase 1 优先**：先把聊天主页的三栏布局 + Agent 问答跑通，这是核心价值
2. **复用现有组件**：Element Plus 的 `el-table`、`el-form`、`el-pagination`、`el-card` 等组件已满足大部分管理页需求
3. **ECharts 图表**：折线图用 `line` 类型，柱状图用 `bar` 类型，配置项保持简洁
4. **粒子动画**：先用 CSS `@keyframes` + `div` 实现，不要一开始就上 Canvas/Three.js
5. **SSE 流式**：V2 再做，V1 用同步 `ask/agent` 即可
6. **权限控制**：前端只做 UI 隐藏，后端鉴权已完整，不可绕过

---

**文档结束**
