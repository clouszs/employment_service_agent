# ===== 构建阶段 =====
FROM python:3.11-slim AS builder

WORKDIR /build

# 安装构建依赖（GCC + MySQL 客户端头文件）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装到 /install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ===== 运行阶段 =====
FROM python:3.11-slim AS runtime

WORKDIR /app

# 安装运行时依赖（MySQL 客户端共享库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient81 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Python 包（正确放到 /usr/local）
COPY --from=builder /install /usr/local

# 复制应用代码
COPY app/                    ./app/
COPY alembic.ini            ./
COPY migrations/             ./migrations/

# 创建持久化数据目录
RUN mkdir -p data uploads chroma_data

# 非 root 用户运行（安全）
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \
    CMD curl -f http://localhost:8000/health/live || exit 1

# 启动命令（2 个 worker，生产环境根据 CPU 调整）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
