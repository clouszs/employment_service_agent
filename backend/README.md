# 高校智慧就业服务平台 - AI问答模块 —— 后端

FastAPI + SQLAlchemy 2.0 + MySQL 8.x

## 目录结构

```
backend/
├── requirements.txt      # 依赖
├── .env                  # 本地配置(含密码,不提交)
├── .env.example          # 配置模板
└── app/
    ├── main.py           # 应用入口
    ├── core/
    │   ├── config.py     # 配置(读 .env)
    │   ├── database.py   # 引擎/会话/get_db 依赖
    │   └── response.py   # 统一响应+全局异常
    ├── models/
    │   └── models.py     # 16 个 ORM 模型(对应数据库表)
    └── api/
        └── health.py     # 健康检查接口
```

## 快速开始

```bash
cd backend

# 1. 创建虚拟环境
python -m venv .venv
# Windows(Git Bash)
source .venv/Scripts/activate
# Windows(PowerShell)
# .venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3. 确认 .env 中数据库配置正确（默认 127.0.0.1:3306 / root / 123456 / claudecode_rag）

# 4. 启动
uvicorn app.main:app --reload
```

## 验证

- 根路径：http://127.0.0.1:8000/
- 健康检查：http://127.0.0.1:8000/api/v1/health
- Swagger 文档：http://127.0.0.1:8000/docs

健康检查返回 `database.ok = true` 表示已连上数据库。

## 当前进度

- [x] P0 基础设施：配置 / 数据库连接 / 统一响应 / 健康检查
- [ ] P1 用户与权限
- [ ] P2 知识库管理
- [ ] P3 检索与问答
- [ ] P4 会话与反馈
- [ ] P5 运营与统计

接口实现顺序见上级目录 `接口实现顺序.md`。
