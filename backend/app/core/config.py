"""全局配置：从 .env 读取，pydantic-settings 管理。"""

import secrets
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,  # 支持大小写不敏感的 env 变量读取
    )

    # 应用
    app_name: str = "高校智慧就业服务平台 - AI问答模块"
    app_env: str = "dev"
    app_debug: bool = True
    api_prefix: str = "/api/v1"

    # 服务监听地址（直接运行 main.py 时生效）
    # 127.0.0.1=仅本机；0.0.0.0=允许局域网访问后端
    server_host: str = "127.0.0.1"
    server_port: int = 8000

    # 数据库
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = Field(default="", description="数据库密码，生产环境必须设置")
    db_name: str = "claudecode_rag"
    db_charset: str = "utf8mb4"
    db_pool_size: int = 10
    db_pool_recycle: int = 3600
    db_echo: bool = False

    # JWT 鉴权
    jwt_secret: str = Field(default="", description="JWT密钥，生产环境必须设置（建议至少32位）")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = Field(default=120, ge=5, le=1440, description="令牌有效期(分钟)，默认2小时")

    # 文件上传
    upload_dir: str = "uploads"
    max_upload_mb: int = 50

    # RAG：DashScope(阿里百炼，OpenAI 兼容接口)
    dashscope_api_key: str = Field(default="", description="DashScope API Key，从环境变量 DASHSCOPE_API_KEY 读取")
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    embedding_model: str = "text-embedding-v4"
    embedding_dim: int = 1024
    llm_model: str = "qwen3.7-max"

    # 语义分块（基于句子嵌入相似度的百分位落差法）
    chunk_min_chars: int = 200  # 块最小字符数（低于则继续合并短句）
    chunk_max_chars: int = 500  # 块最大字符数（超过则在句子边界强制断开）
    semantic_breakpoint_percentile: int = 95  # 相邻句子距离的百分位阈值，超过即语义断点

    # 向量库(Chroma 本地嵌入式)
    chroma_dir: str = "chroma_data"
    chroma_collection: str = "kb_chunks"

    # ===== Redis（Embedding 缓存 L2；不可用时自动降级，非强依赖）=====
    redis_enabled: bool = True  # 总开关；置 false 则完全跳过 Redis 直接走内存+DB
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""  # 无密码留空
    redis_socket_timeout: float = 1.5  # 连接/读写超时(秒)，超时即视为不可用并降级
    embedding_cache_ttl: int = 86400  # Redis 中 embedding 的过期秒数（默认 24h）
    embedding_memory_cache_size: int = 4096  # L1 进程内存 LRU 容量（条数）

    # ===== LangSmith（LLM 调用链路追踪；阶段 1+ 使用）=====
    # 全局开关：置 false 则不启用追踪。API Key 从环境变量 LANGSMITH_API_KEY 读取，不写死。
    langsmith_enabled: bool = True
    langsmith_api_key: str = Field(default="", description="LangSmith API Key，从环境变量 LANGSMITH_API_KEY 读取")
    langsmith_project: str = "myproject"  # 项目名（LangSmith 控制台中的 Project）
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    # 检索问答
    retrieve_top_k: int = 5
    retrieve_score_threshold: float = 0.4  # 最高分低于此值走"无法回答"兜底

    # FAQ 命中优先
    faq_collection: str = "kb_faqs"
    faq_score_threshold: float = 0.75  # 问法相似度达到此值直接返回 FAQ 标准答案

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """验证 JWT 密钥：生产环境必须设置且足够长。"""
        if info.data.get("app_env") == "production":
            if not v or len(v) < 32:
                raise ValueError("生产环境必须设置至少32位的JWT密钥（建议64位以上）")
        # 开发环境自动生成更长的密钥（64字符 ≈ 48字节）
        return v if v else secrets.token_urlsafe(64)

    @field_validator("db_password")
    @classmethod
    def validate_db_password(cls, v: str, info) -> str:
        """验证数据库密码：生产环境必须设置。"""
        if info.data.get("app_env") == "production" and not v:
            raise ValueError("生产环境必须设置数据库密码")
        return v

    @field_validator("app_debug")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """验证调试模式：生产环境不能开启。"""
        if info.data.get("app_env") == "production" and v:
            raise ValueError("生产环境不能开启调试模式")
        return v

    @property
    def database_url(self) -> str:
        """SQLAlchemy 连接串（PyMySQL 驱动）。"""
        # 密码中包含特殊字符时需要 URL 编码
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.db_password)
        return (
            f"mysql+pymysql://{self.db_user}:{encoded_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset={self.db_charset}"
        )


@lru_cache
def get_settings() -> Settings:
    """全局单例配置。"""
    return Settings()


settings = get_settings()
