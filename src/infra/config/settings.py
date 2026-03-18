"""全局配置 - 从环境变量 / .env 文件加载"""

from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置类 - 从环境变量/.env文件加载"""

    # Pydantic Settings 配置
    model_config = SettingsConfigDict(
        env_file=".env",           # 指定 .env 文件路径
        env_file_encoding="utf-8", # .env 文件编码
        case_sensitive=True,       # 环境变量名大小写敏感
        extra="ignore",           # 忽略额外的环境变量
    )

    # === 应用配置 ===
    APP_NAME: str = "Enterprise QA Assistant"  # 应用名称
    APP_VERSION: str = "0.1.0"                 # 应用版本
    ENV: str = "development"                    # 运行环境: development / staging / production
    DEBUG: bool = True                         # 调试模式开关
    API_PREFIX: str = "/api/v1"                 # API 路由前缀

    # === 服务端口配置 ===
    HOST: str = "0.0.0.0"   # API 服务监听地址
    PORT: int = 8000         # API 服务监听端口
    WORKERS: int = 1         # Uvicorn 工作进程数 (开发环境1个，生产环境根据CPU核数设置)

    # === LLM 配置 ===
    OPENAI_API_KEY: SecretStr                              # OpenAI API 密钥
    OPENAI_API_BASE: str = "https://api.openai.com/v1"     # OpenAI API 基础地址

    # 主力模型配置 (用于复杂推理和高质量回答)
    PRIMARY_LLM_MODEL: str = "gpt-4o"                      # 主力模型名称
    PRIMARY_LLM_TEMPERATURE: float = 0.1                  # 温度参数 (低=确定性，高=创造性)
    PRIMARY_LLM_MAX_TOKENS: int = 4096                     # 最大生成 token 数

    # 降级模型配置 (用于简单查询和降级兜底)
    FALLBACK_LLM_MODEL: str = "gpt-4o-mini"               # 降级模型名称
    FALLBACK_LLM_TEMPERATURE: float = 0.0                  # 降级模型温度

    # Embedding 模型配置 (用于文档向量嵌入)
    EMBEDDING_MODEL: str = "text-embedding-3-large"        # Embedding 模型名称
    EMBEDDING_DIMENSION: int = 3072                        # Embedding 向量维度

    # === PostgreSQL 配置 (结构化数据存储) ===
    POSTGRES_HOST: str = "localhost"    # 数据库主机地址
    POSTGRES_PORT: int = 5432          # 数据库端口
    POSTGRES_USER: str = "user"        # 数据库用户名
    POSTGRES_PASSWORD: SecretStr = SecretStr("pass")  # 数据库密码
    POSTGRES_DB: str = "qa_assistant"  # 数据库名称
    POSTGRES_POOL_MIN: int = 5         # 连接池最小连接数
    POSTGRES_POOL_MAX: int = 20        # 连接池最大连接数

    @property
    def POSTGRES_URL(self) -> str:
        """构建 PostgreSQL 连接 URL (同步版本)"""
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    @property
    def POSTGRES_ASYNC_URL(self) -> str:
        """构建 PostgreSQL 连接 URL (异步版本, 用于 asyncpg)"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}"
            f"/{self.POSTGRES_DB}"
        )

    # === Redis 配置 (缓存和会话存储) ===
    REDIS_HOST: str = "localhost"                       # Redis 主机地址
    REDIS_PORT: int = 6379                              # Redis 端口
    REDIS_DB: int = 0                                   # Redis 数据库编号
    REDIS_PASSWORD: SecretStr | None = None             # Redis 密码 (可选)
    REDIS_POOL_MAX: int = 50                            # 连接池最大连接数

    @property
    def REDIS_URL(self) -> str:
        """构建 Redis 连接 URL"""
        password_part = ""
        if self.REDIS_PASSWORD:
            password_part = f":{self.REDIS_PASSWORD.get_secret_value()}@"
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # === Milvus 配置 (向量数据库) ===
    MILVUS_HOST: str = "localhost"           # Milvus 主机地址
    MILVUS_PORT: int = 19530                 # Milvus 端口
    MILVUS_TOKEN: str = ""                   # Milvus 认证令牌
    MILVUS_DB_NAME: str = "default"          # Milvus 数据库名称
    MILVUS_COLLECTION_NAME: str = "knowledge_base"  # 知识库 Collection 名称

    @property
    def MILVUS_URI(self) -> str:
        """构建 Milvus HTTP 连接 URI"""
        return f"http://{self.MILVUS_HOST}:{self.MILVUS_PORT}"

    # === RAG 配置 (检索增强生成) ===
    RAG_CHUNK_SIZE: int = 512       # 文档分块大小 (字符数)
    RAG_CHUNK_OVERLAP: int = 50     # 分块重叠大小 (保持上下文连贯性)
    RAG_TOP_K: int = 5              # 检索返回的最相关文档块数量
    RAG_MIN_CONFIDENCE: float = 0.7 # RAG 回答最低置信度阈值

    # === 并发控制配置 ===
    MAX_CONCURRENT_REQUESTS: int = 10   # 最大并发请求数
    REQUEST_TIMEOUT: int = 120          # 请求超时时间 (秒)

    # === 会话配置 ===
    SESSION_TTL: int = 86400  # 会话 TTL (24小时, 单位: 秒)

    # === 短期记忆配置 ===
    SHORT_TERM_MEMORY_TTL: int = 86400  # 短期记忆 TTL (秒)，默认 24 小时
    MAX_SHORT_TERM_MESSAGES: int = 20   # 短期记忆最大消息数

    # === 日志配置 ===
    LOG_LEVEL: str = "INFO"   # 日志级别: DEBUG / INFO / WARNING / ERROR
    LOG_FORMAT: str = "json"  # 日志格式: json / console

    # === 文件上传配置 ===
    UPLOAD_ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".md", ".txt"}  # 允许的文件类型
    MAX_UPLOAD_SIZE_MB: int = 50  # 最大上传文件大小 (MB)


@lru_cache
def get_settings() -> Settings:
    """获取缓存的 Settings 单例实例"""
    return Settings()
