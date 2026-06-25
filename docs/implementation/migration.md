# 数据库迁移

> 来源：[功能模块实现文档.md](../功能模块实现文档.md) §12 + [phase-0-environment.md](./phase-0-environment.md)
> 用途：数据库表结构变更、迁移脚本、执行验证

---

## 迁移概览

| 项目 | 内容 |
|------|------|
| 迁移工具 | Alembic 1.18.4 |
| 迁移脚本目录 | `backend/migrations/` |
| Alembic 配置 | `backend/alembic/` |
| 当前 HEAD | `65a7e09c9884` |
| 总表数 | 24 张 |

---

## 迁移版本历史

| 版本 | 内容 | 说明 |
|------|------|------|
| `83dc52f295f1` | 基线空迁移 | stamp 现有 17 表为起点，不执行 DDL |
| `be1122c3c9a7` | 6 张监控日志表 + qa_message 加 5 字段 | Agent 模块核心表 |
| `65a7e09c9884` | embedding_cache 缓存表 | Embedding 三级缓存 L3 |

---

## 新增表清单

| 表名 | 用途 | 所属模块 | 关键字段 |
|------|------|----------|----------|
| `agent_refusal_log` | 拒答记录 | 监控模块 | query, refusal_reason, confidence, created_at |
| `citation_quality_log` | 引用质量评估日志 | 监控模块 | message_id, quality_score, direct_count, indirect_count, none_count, created_at |
| `kb_health_log` | 知识库健康度日志 | 监控模块 | check_date, health_score, warning_docs, expired_docs, total_docs |
| `llm_cost_log` | LLM 成本消耗日志 | 监控模块 | check_date, daily_cost, monthly_cost, token_count, created_at |
| `consistency_issue_log` | 一致性问题日志 | 监控模块 | message_id, issue_type, severity, description, created_at |
| `fact_verification_log` | 事实核验日志 | 监控模块 | message_id, fact_type, extracted_value, validation_result, created_at |
| `embedding_cache` | Embedding 缓存表 | 核心模块 | cache_key, embedding(LONGTEXT), model, dimension, created_at, hit_count |

> 注：6 张监控表最终决定存 MySQL（写多读少），而非 MongoDB。

---

## 修改表清单

| 表名 | 新增字段 | 字段类型 | 说明 |
|------|----------|----------|------|
| `qa_message` | `confidence` | DECIMAL(5,4) | 综合置信度 |
| `qa_message` | `query_risk_level` | VARCHAR(20) | 查询风险等级 (high/medium/low) |
| `qa_message` | `consistency_issues` | JSON | 一致性问题列表 |
| `qa_message` | `fact_issues` | JSON | 事实核验问题列表 |
| `qa_message` | `temporal_warnings` | JSON | 时效性警告列表 |

---

## Alembic 环境配置

### 目录结构

```
backend/
├── alembic/
│   ├── env.py          # 动态注入连接串，绑定 Base.metadata
│   └── script.py.mako  # 迁移脚本模板
├── migrations/         # 版本脚本输出目录（由 alembic.ini 的 version_locations 指定）
│   ├── 83dc52f295f1_*.py
│   ├── be1122c3c9a7_*.py
│   └── 65a7e09c9884_*.py
└── alembic.ini         # 只保留纯英文配置
```

### 关键配置

- `alembic.ini` 只保留纯英文，中文说明写进 `env.py`（Windows GBK 编码坑）
- `env.py` 用 `settings.database_url` 动态注入连接串（不在 ini 存密码）
- `env.py` 绑定 `Base.metadata` 用于自动模型检测

---

## 执行迁移

### 前置条件

1. MySQL 服务已启动（`net start MySQL84`）
2. 虚拟环境已激活
3. 依赖已安装（`pip install -r requirements.txt`）

### 执行命令

```bash
cd backend

# 查看当前迁移状态
.venv/Scripts/python.exe -m alembic current

# 查看迁移历史
.venv/Scripts/python.exe -m alembic history

# 执行迁移到最新版本
.venv/Scripts/python.exe -m alembic upgrade head

# 回滚一个版本
.venv/Scripts/python.exe -m alembic downgrade -1
```

### 验证迁移

```bash
# 确认表数量
mysql -u root -p aiqa -e "SHOW TABLES;" | wc -l
# 应输出 24

# 确认 6 张监控表
mysql -u root -p aiqa -e "SHOW TABLES LIKE 'agent_%';"
mysql -u root -p aiqa -e "SHOW TABLES LIKE 'kb_%';"
mysql -u root -p aiqa -e "SHOW TABLES LIKE 'llm_%';"
mysql -u root -p aiqa -e "SHOW TABLES LIKE 'citation_%';"
mysql -u root -p aiqa -e "SHOW TABLES LIKE 'consistency_%';"
mysql -u root -p aiqa -e "SHOW TABLES LIKE 'fact_%';"

# 确认 embedding_cache 表
mysql -u root -p aiqa -e "SHOW TABLES LIKE 'embedding_cache';"

# 确认 qa_message 新增字段
mysql -u root -p aiqa -e "DESC qa_message;"
```

---

## 迁移脚本（参考）

> 以下为早期手写迁移脚本参考，当前已改用 Alembic 管理。保留供理解表结构。

```python
# 文件：backend/migrations/add_agent_tables.py（参考，非当前使用）

from sqlalchemy import text
from app.core.database import engine

def migrate():
    """执行数据库迁移"""
    with engine.connect() as conn:
        # 创建拒答记录表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_refusal_log (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                query TEXT NOT NULL,
                refusal_reason VARCHAR(200) NOT NULL,
                confidence DECIMAL(5,4),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 创建健康度日志表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kb_health_log (
                id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                check_date DATE NOT NULL,
                health_score DECIMAL(5,4),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_check_date (check_date)
            )
        """))

        # 修改 qa_message 表
        conn.execute(text("""
            ALTER TABLE qa_message
            ADD COLUMN IF NOT EXISTS confidence DECIMAL(5,4),
            ADD COLUMN IF NOT EXISTS query_risk_level VARCHAR(20)
        """))

        conn.commit()

if __name__ == "__main__":
    migrate()
    print("迁移完成")
```

---

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| Windows 上 alembic.ini 中文乱码 | 只保留纯英文配置，中文说明写进 env.py |
| MySQL84 服务未启动 | `net start MySQL84` |
| 迁移版本冲突 | `alembic downgrade -1` 回滚后重新 `upgrade head` |
| 需要创建新迁移 | `alembic revision --autogenerate -m "描述"` |
