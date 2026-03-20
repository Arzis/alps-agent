"""Embedding Provider 统一接口

支持 DashScope (云端) 和 Ollama (本地) 两种 provider。
通过配置 EMBEDDING_PROVIDER 环境变量切换。
"""

from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from src.infra.config.settings import Settings


class BaseEmbeddingProvider(ABC):
    """Embedding Provider 抽象基类"""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """返回 embedding 向量维度"""
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """返回使用的模型名称"""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """返回 API 基础地址"""
        pass

    @abstractmethod
    async def embed(self, texts: str | list[str]) -> list[list[float]]:
        """获取文本的 embedding 向量

        Args:
            texts: 单个文本或文本列表

        Returns:
            list[list[float]]: embedding 向量列表
        """
        pass

    async def embed_one(self, text: str) -> list[float]:
        """获取单个文本的 embedding"""
        results = await self.embed([text])
        return results[0]


class DashScopeProvider(BaseEmbeddingProvider):
    """DashScope (阿里云) Embedding Provider"""

    def __init__(self, settings: Settings):
        self._client = AsyncOpenAI(
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
        )
        self._model = settings.EMBEDDING_MODEL
        self._dimension = settings.EMBEDDING_DIMENSION

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._client.base_url

    async def embed(self, texts: str | list[str]) -> list[list[float]]:
        if isinstance(texts, str):
            texts = [texts]

        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=self._dimension,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]


class OllamaProvider(BaseEmbeddingProvider):
    """Ollama 本地 Embedding Provider"""

    def __init__(self, settings: Settings):
        self._client = AsyncOpenAI(
            api_key=settings.OLLAMA_API_KEY,
            base_url=settings.OLLAMA_BASE_URL,
        )
        self._model = settings.OLLAMA_EMBEDDING_MODEL
        self._dimension = settings.OLLAMA_EMBEDDING_DIMENSION

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._client.base_url

    async def embed(self, texts: str | list[str]) -> list[list[float]]:
        if isinstance(texts, str):
            texts = [texts]

        # Ollama API 兼容 OpenAI 格式
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]


def create_embedding_provider(settings: Settings | None = None) -> BaseEmbeddingProvider:
    """Embedding Provider 工厂函数

    Args:
        settings: 应用配置，如果为 None 则从环境变量加载

    Returns:
        BaseEmbeddingProvider: 当前配置的 embedding provider 实例
    """
    if settings is None:
        settings = Settings()

    if settings.EMBEDDING_PROVIDER == "ollama":
        return OllamaProvider(settings)
    return DashScopeProvider(settings)
