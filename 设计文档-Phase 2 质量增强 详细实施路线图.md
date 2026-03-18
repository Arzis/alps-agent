# Phase 2 质量增强 详细实施路线图

> **目标**: 全面提升 RAG 回答质量，构建完整的质量评估闭环
> **周期**: 3-4 周
> **前置依赖**: Phase 1 MVP 全部验收通过
> **交付物**: 语义分块、多路召回+重排、语义缓存、查询改写、LLM可观测性、自动化RAG评估

------

## 一、Phase 2 任务分解总览

text



```
Phase 2 质量增强 (3-4周)
│
├── Week 7: 查询理解增强 & 语义分块
│   ├── 7.1 查询改写 (多轮指代消解 + Query Rewriting)
│   ├── 7.2 查询扩展 (Multi-Query Expansion)
│   ├── 7.3 语义分块 (SemanticSplitter)
│   ├── 7.4 分块策略路由 (根据文档类型选择策略)
│   └── 7.5 元数据增强提取
│
├── Week 8: 多路召回 & 重排
│   ├── 8.1 Elasticsearch BM25 稀疏检索
│   ├── 8.2 混合检索 + RRF 融合
│   ├── 8.3 Cross-Encoder Rerank
│   ├── 8.4 引用溯源增强
│   └── 8.5 检索质量指标埋点
│
├── Week 9: 语义缓存 & 置信度评估
│   ├── 9.1 Redis Stack 语义缓存
│   ├── 9.2 多级缓存架构
│   ├── 9.3 LLM-based 置信度评估
│   ├── 9.4 幻觉检测
│   └── 9.5 质量评估驱动的降级策略优化
│
└── Week 10: LLM可观测性 & RAG评估
    ├── 10.1 LangFuse 集成 & 部署
    ├── 10.2 全链路 Trace 埋点
    ├── 10.3 RAGAS 评估模块
    ├── 10.4 DeepEval 补充评估
    ├── 10.5 自动化测试集生成
    └── 10.6 评估报告 & 基线建立
```

------

## 二、新增/变更的目录结构

text



```
src/
├── core/
│   ├── rag/
│   │   ├── ingestion/
│   │   │   ├── parser.py              # [不变]
│   │   │   ├── chunker.py             # [重构] 多策略分块
│   │   │   ├── metadata_extractor.py  # [新增] LLM元数据提取
│   │   │   └── pipeline.py            # [增强] 支持策略路由
│   │   ├── retrieval/
│   │   │   ├── dense.py               # [不变]
│   │   │   ├── sparse.py              # [新增] ES BM25
│   │   │   ├── hybrid.py              # [新增] 混合检索 + RRF
│   │   │   ├── reranker.py            # [新增] Cross-Encoder
│   │   │   └── retriever.py           # [重构] 统一检索接口
│   │   └── synthesis/
│   │       ├── synthesizer.py         # [增强] 引用溯源
│   │       └── citation.py            # [新增] 引用提取器
│   ├── orchestrator/
│   │   ├── graph.py                   # [增强] 增加缓存节点
│   │   ├── state.py                   # [增强] 增加质量字段
│   │   ├── engine.py                  # [增强] 缓存集成
│   │   └── nodes/
│   │       ├── query_understanding.py # [重构] LLM改写
│   │       ├── rag_agent.py           # [增强] 多路召回
│   │       ├── quality_gate.py        # [重构] LLM置信度
│   │       ├── cache_lookup.py        # [新增] 缓存查询节点
│   │       └── ...
│   └── quality/                       # [新增] 质量评估
│       ├── __init__.py
│       ├── confidence.py              # 置信度评估
│       └── hallucination.py           # 幻觉检测
├── infra/
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── semantic_cache.py          # [新增] 语义缓存
│   │   └── cache_manager.py           # [新增] 多级缓存管理
│   ├── database/
│   │   ├── elasticsearch.py           # [新增] ES客户端
│   │   └── ...
│   └── logging/
│       ├── logger.py                  # [不变]
│       └── langfuse_tracer.py         # [新增] LangFuse追踪
├── evaluation/                        # [新增] 评估模块
│   ├── __init__.py
│   ├── ragas_evaluator.py
│   ├── deepeval_evaluator.py
│   ├── dataset_generator.py
│   ├── report.py
│   └── runner.py                      # 评估任务运行器
└── api/
    └── routers/
        └── evaluation.py              # [新增] 评估接口
```

### 新增依赖

toml



```
# pyproject.toml 新增依赖

# === Phase 2 新增 ===
# 语义分块
llama-index-core = "^0.11.0"  # 已有, SemanticSplitter在core中

# Elasticsearch
elasticsearch = { version = "^8.12.0", extras = ["async"] }

# Reranker
sentence-transformers = "^3.3.0"   # Cross-Encoder
# 或者使用API: cohere = "^5.0.0"

# 语义缓存 (Redis Stack已支持, 无需额外包)
numpy = "^1.26.0"

# LLM可观测性
langfuse = "^2.50.0"

# RAG评估
ragas = "^0.2.0"
deepeval = "^1.4.0"
datasets = "^3.0.0"                # HuggingFace datasets
```

### Docker Compose 新增服务

YAML



```
# docker/docker-compose.yml 新增

  # ============================================================
  # Elasticsearch - BM25 稀疏检索 (Phase 2)
  # ============================================================
  elasticsearch:
    image: elasticsearch:8.12.0
    container_name: qa-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - qa-network

  # ============================================================
  # LangFuse - LLM可观测性平台 (Phase 2)
  # ============================================================
  langfuse:
    image: langfuse/langfuse:2
    container_name: qa-langfuse
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/langfuse
      NEXTAUTH_SECRET: my-langfuse-secret-key-change-in-production
      NEXTAUTH_URL: http://localhost:3000
      SALT: my-salt-value-change-in-production
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - qa-network

# volumes 新增
volumes:
  es_data:
```

SQL



```
-- docker/configs/postgres/02-phase2-init.sql

-- LangFuse 数据库
CREATE DATABASE langfuse;

-- 评估记录表
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id              VARCHAR(64) PRIMARY KEY,
    name            VARCHAR(256),
    dataset_size    INTEGER,
    status          VARCHAR(32) DEFAULT 'pending',  -- pending / running / completed / failed
    metrics         JSONB DEFAULT '{}',
    config          JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at    TIMESTAMP WITH TIME ZONE
);

-- 评估详情表
CREATE TABLE IF NOT EXISTS evaluation_results (
    id              BIGSERIAL PRIMARY KEY,
    run_id          VARCHAR(64) REFERENCES evaluation_runs(id),
    question        TEXT NOT NULL,
    ground_truth    TEXT,
    generated_answer TEXT,
    contexts        JSONB DEFAULT '[]',
    metrics         JSONB DEFAULT '{}',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_eval_results_run_id ON evaluation_results(run_id);

-- 用户反馈表 (为Phase 3预留)
CREATE TABLE IF NOT EXISTS user_feedback (
    id              BIGSERIAL PRIMARY KEY,
    session_id      VARCHAR(64),
    message_id      BIGINT,
    feedback_type   VARCHAR(16),  -- thumbs_up / thumbs_down
    comment         TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

------

## 三、Week 7：查询理解增强 & 语义分块

### 7.1 查询改写节点重构

Python



```
# src/core/orchestrator/nodes/query_understanding.py

import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from src.core.orchestrator.state import ConversationState
from src.infra.config.settings import get_settings

logger = structlog.get_logger()


# === 结构化输出模型 ===

class QueryUnderstandingOutput(BaseModel):
    """查询理解结果"""
    rewritten_query: str = Field(description="改写后的独立完整查询")
    expanded_queries: list[str] = Field(
        default_factory=list,
        description="2-3个扩展查询, 用于多路召回, 从不同角度表述同一问题",
    )
    intent: str = Field(
        description="意图分类: knowledge_qa / chitchat / unclear",
        default="knowledge_qa",
    )
    reasoning: str = Field(description="改写推理过程", default="")


QUERY_UNDERSTANDING_PROMPT = """你是一个查询理解专家。你的任务是分析用户的当前问题，结合对话历史，生成改写后的查询。

## 任务说明

1. **指代消解**: 如果用户的问题包含代词或省略，需要根据对话历史补全。
   - 例: 历史中提到"年假制度"，用户说"它有什么限制？" → 改写为"年假制度有什么限制？"

2. **查询改写**: 将口语化/模糊的问题改写为清晰、适合检索的查询。
   - 例: "假期咋算的" → "公司员工假期天数如何计算？"

3. **查询扩展**: 生成2-3个语义相同但表述不同的查询，用于多路召回。
   - 例: "年假制度" → ["员工年假政策", "公司带薪休假规定", "年度假期天数标准"]

4. **意图识别**: 
   - knowledge_qa: 需要查询知识库的问题
   - chitchat: 闲聊/寒暄，不需要知识检索
   - unclear: 问题不清晰，需要追问

## 对话历史
{conversation_history}

## 当前用户问题
{current_query}

请以JSON格式输出结果。"""


class QueryUnderstandingNode:
    """查询理解节点 - Phase 2 增强版"""

    def __init__(self, llm: ChatOpenAI | None = None):
        settings = get_settings()
        self.llm = llm or ChatOpenAI(
            model=settings.PRIMARY_LLM_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=30,
        )

    async def __call__(self, state: ConversationState) -> dict:
        """执行查询理解"""
        original_query = state["original_query"]
        messages = state.get("messages", [])

        # 如果是第一轮对话且问题足够清晰, 跳过LLM改写
        if len(messages) <= 1 and len(original_query) > 10:
            return {
                "rewritten_query": original_query,
                "expanded_queries": [original_query],
                "intent": "knowledge_qa",
            }

        # 构建对话历史文本
        history_text = self._format_history(messages)

        # LLM改写
        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content=QUERY_UNDERSTANDING_PROMPT.format(
                        conversation_history=history_text or "(无历史对话)",
                        current_query=original_query,
                    )),
                ],
                response_format={"type": "json_object"},
            )

            result = QueryUnderstandingOutput.model_validate_json(response.content)

            logger.info(
                "query_understanding_completed",
                session_id=state["session_id"],
                original=original_query[:100],
                rewritten=result.rewritten_query[:100],
                expanded_count=len(result.expanded_queries),
                intent=result.intent,
            )

            return {
                "rewritten_query": result.rewritten_query,
                "expanded_queries": result.expanded_queries,
                "intent": result.intent,
            }

        except Exception as e:
            logger.warning(
                "query_understanding_fallback",
                error=str(e),
                session_id=state["session_id"],
            )
            # 降级: 直接使用原始查询
            return {
                "rewritten_query": original_query,
                "expanded_queries": [original_query],
                "intent": "knowledge_qa",
            }

    def _format_history(self, messages: list, max_turns: int = 5) -> str:
        """格式化对话历史"""
        # 取最近的N轮 (排除最后一条, 它是当前用户消息)
        recent = messages[-(max_turns * 2 + 1):-1] if len(messages) > 1 else []
        if not recent:
            return ""

        lines = []
        for msg in recent:
            role = "用户" if hasattr(msg, "type") and msg.type == "human" else "助手"
            content = msg.content if hasattr(msg, "content") else str(msg)
            lines.append(f"{role}: {content[:200]}")

        return "\n".join(lines)
```

### 7.2 语义分块重构

Python



```
# src/core/rag/ingestion/chunker.py

from enum import Enum
from dataclasses import dataclass
import structlog

from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
)
from llama_index.core import Document
from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding

from src.infra.config.settings import Settings, get_settings

logger = structlog.get_logger()


class ChunkingStrategy(str, Enum):
    """分块策略枚举"""
    RECURSIVE = "recursive"        # 递归字符分块 (快, 通用)
    SEMANTIC = "semantic"          # 语义分块 (质量高, 较慢)
    AUTO = "auto"                  # 根据文档类型自动选择


@dataclass
class ChunkerConfig:
    """分块配置"""
    strategy: ChunkingStrategy = ChunkingStrategy.AUTO
    chunk_size: int = 512
    chunk_overlap: int = 50
    # 语义分块参数
    semantic_buffer_size: int = 1
    semantic_breakpoint_percentile: int = 95


class DocumentChunker:
    """
    文档分块器 - Phase 2 多策略版

    支持:
    1. 递归字符分块 (SentenceSplitter) - 通用、快速
    2. 语义分块 (SemanticSplitter) - 基于Embedding相似度自适应分块
    3. 自动策略选择 - 根据文档类型和长度决定
    """

    def __init__(self, config: ChunkerConfig | None = None, embedding_model: OpenAIEmbedding | None = None):
        settings = get_settings()
        self.config = config or ChunkerConfig(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        )

        # 递归分块器 (始终初始化, 作为fallback)
        self._recursive_splitter = SentenceSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[。！？\\.\\!\\?]",
        )

        # 语义分块器 (需要Embedding模型)
        self._semantic_splitter = None
        if embedding_model:
            try:
                self._semantic_splitter = SemanticSplitterNodeParser(
                    buffer_size=self.config.semantic_buffer_size,
                    breakpoint_percentile_threshold=self.config.semantic_breakpoint_percentile,
                    embed_model=embedding_model,
                )
                logger.info("semantic_splitter_initialized")
            except Exception as e:
                logger.warning("semantic_splitter_init_failed", error=str(e))

    def chunk(
        self,
        documents: list[Document],
        doc_id: str,
        collection: str,
        strategy: ChunkingStrategy | None = None,
    ) -> list[TextNode]:
        """
        将文档分块为TextNode

        Args:
            documents: LlamaIndex Document列表
            doc_id: 文档ID
            collection: 知识库集合名
            strategy: 分块策略 (None则使用配置中的策略)
        """
        effective_strategy = strategy or self.config.strategy

        # 自动策略选择
        if effective_strategy == ChunkingStrategy.AUTO:
            effective_strategy = self._auto_select_strategy(documents)

        logger.info(
            "chunking_start",
            doc_id=doc_id,
            strategy=effective_strategy.value,
            num_documents=len(documents),
        )

        # 执行分块
        if effective_strategy == ChunkingStrategy.SEMANTIC and self._semantic_splitter:
            try:
                nodes = self._semantic_chunk(documents)
            except Exception as e:
                logger.warning(
                    "semantic_chunking_failed_fallback_to_recursive",
                    doc_id=doc_id,
                    error=str(e),
                )
                nodes = self._recursive_chunk(documents)
        else:
            nodes = self._recursive_chunk(documents)

        # 注入元数据
        for i, node in enumerate(nodes):
            node.metadata.update({
                "doc_id": doc_id,
                "chunk_index": i,
                "collection": collection,
                "total_chunks": len(nodes),
                "chunking_strategy": effective_strategy.value,
            })
            node.id_ = f"{doc_id}_chunk_{i:04d}"

        # 过滤过短的chunk
        min_length = 20
        nodes = [n for n in nodes if len(n.text.strip()) >= min_length]

        logger.info(
            "chunking_completed",
            doc_id=doc_id,
            strategy=effective_strategy.value,
            num_chunks=len(nodes),
            avg_chunk_length=sum(len(n.text) for n in nodes) // max(len(nodes), 1),
        )

        return nodes

    def _recursive_chunk(self, documents: list[Document]) -> list[TextNode]:
        """递归字符分块"""
        return self._recursive_splitter.get_nodes_from_documents(documents)

    def _semantic_chunk(self, documents: list[Document]) -> list[TextNode]:
        """语义分块"""
        return self._semantic_splitter.get_nodes_from_documents(documents)

    def _auto_select_strategy(self, documents: list[Document]) -> ChunkingStrategy:
        """
        自动选择分块策略

        规则:
        - 短文档 (<2000字): 递归分块 (不值得用语义分块)
        - 长文档且语义分块器可用: 语义分块
        - 其他: 递归分块
        """
        total_length = sum(len(doc.text) for doc in documents)

        if total_length < 2000:
            return ChunkingStrategy.RECURSIVE

        if self._semantic_splitter is not None:
            return ChunkingStrategy.SEMANTIC

        return ChunkingStrategy.RECURSIVE
```

### 7.3 元数据增强提取

Python



```
# src/core/rag/ingestion/metadata_extractor.py

import asyncio
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from llama_index.core.schema import TextNode
from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class ChunkMetadata(BaseModel):
    """从文本块中提取的结构化元数据"""
    title: str = Field(default="", description="该段落的主题/标题")
    keywords: list[str] = Field(default_factory=list, description="3-5个关键词")
    summary: str = Field(default="", description="一句话摘要")
    potential_questions: list[str] = Field(
        default_factory=list,
        description="这段文本可以回答的2-3个问题",
    )


METADATA_EXTRACTION_PROMPT = """分析以下文本段落，提取结构化元数据。

文本:
---
{text}
---

请提取:
1. title: 这段文本的主题/标题 (10字以内)
2. keywords: 3-5个关键词
3. summary: 一句话摘要 (30字以内)
4. potential_questions: 这段文本可以回答的2-3个问题

以JSON格式输出。"""


class MetadataExtractor:
    """
    LLM元数据提取器

    为每个chunk提取:
    - 主题标题
    - 关键词
    - 摘要
    - 可回答的问题 (用于HyDE-like增强检索)
    """

    def __init__(self, llm: ChatOpenAI | None = None, batch_size: int = 5):
        settings = get_settings()
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",  # 用轻量模型降低成本
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=30,
        )
        self.batch_size = batch_size
        self._semaphore = asyncio.Semaphore(10)

    async def extract(self, nodes: list[TextNode]) -> list[TextNode]:
        """
        为所有节点提取元数据

        注意: 这是一个可选步骤, 会增加摄取时间和LLM成本
        但显著提升检索质量
        """
        logger.info("metadata_extraction_start", num_nodes=len(nodes))

        # 批量并行处理
        tasks = []
        for node in nodes:
            tasks.append(self._extract_single(node))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        enriched_nodes = []
        for node, result in zip(nodes, results):
            if isinstance(result, Exception):
                logger.warning(
                    "metadata_extraction_failed",
                    node_id=node.id_,
                    error=str(result),
                )
                enriched_nodes.append(node)  # 使用未增强的原始节点
            else:
                enriched_nodes.append(result)

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(
            "metadata_extraction_completed",
            total=len(nodes),
            success=success_count,
            failed=len(nodes) - success_count,
        )

        return enriched_nodes

    async def _extract_single(self, node: TextNode) -> TextNode:
        """提取单个节点的元数据"""
        async with self._semaphore:
            text = node.text[:2000]  # 限制长度, 控制token消耗

            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="你是一个文本分析专家。请分析文本并提取结构化元数据。"),
                    HumanMessage(content=METADATA_EXTRACTION_PROMPT.format(text=text)),
                ],
                response_format={"type": "json_object"},
            )

            metadata = ChunkMetadata.model_validate_json(response.content)

            # 将提取的元数据注入节点
            node.metadata.update({
                "extracted_title": metadata.title,
                "extracted_keywords": ", ".join(metadata.keywords),
                "extracted_summary": metadata.summary,
                "potential_questions": " | ".join(metadata.potential_questions),
            })

            # 将关键词和问题也追加到文本中, 增强检索效果
            # (这是一种常用的元数据增强trick)
            node.metadata["_enriched_text"] = (
                f"{node.text}\n\n"
                f"关键词: {', '.join(metadata.keywords)}\n"
                f"相关问题: {' '.join(metadata.potential_questions)}"
            )

            return node
```

### 7.4 摄取管道增强

Python



```
# src/core/rag/ingestion/pipeline.py  (Phase 2 增强版)

import asyncio
import time
from datetime import datetime
import structlog

from llama_index.core.schema import TextNode
from llama_index.embeddings.openai import OpenAIEmbedding

from src.core.rag.ingestion.parser import DocumentParser
from src.core.rag.ingestion.chunker import DocumentChunker, ChunkerConfig, ChunkingStrategy
from src.core.rag.ingestion.metadata_extractor import MetadataExtractor
from src.infra.config.settings import Settings, get_settings
from src.infra.database.milvus_client import get_milvus

logger = structlog.get_logger()

_pipeline: "IngestionPipeline | None" = None


class IngestionPipeline:
    """
    文档摄取管道 - Phase 2 增强版

    新增:
    1. 语义分块策略
    2. 元数据增强提取
    3. ES BM25索引写入
    4. 分块策略路由
    """

    def __init__(self, settings: Settings):
        self.settings = settings

        self.parser = DocumentParser()

        # Embedding模型 (用于语义分块 + 向量生成)
        self.embedding_model = OpenAIEmbedding(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            api_base=settings.OPENAI_API_BASE,
            dimensions=settings.EMBEDDING_DIMENSION,
        )

        # 分块器 (带语义分块能力)
        self.chunker = DocumentChunker(
            config=ChunkerConfig(
                strategy=ChunkingStrategy.AUTO,
                chunk_size=settings.RAG_CHUNK_SIZE,
                chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            ),
            embedding_model=self.embedding_model,
        )

        # 元数据提取器
        self.metadata_extractor = MetadataExtractor()

        self._embedding_semaphore = asyncio.Semaphore(
            settings.MAX_EMBEDDING_CONCURRENT
        )

    async def process(
        self,
        doc_id: str,
        file_path: str,
        file_type: str,
        collection: str,
        chunking_strategy: ChunkingStrategy | None = None,
        enable_metadata_extraction: bool = True,
    ) -> int:
        """
        完整的文档处理流程

        Phase 2 新增:
        - 语义分块
        - 元数据增强
        - 同时写入 Milvus(向量) + ES(BM25)
        """
        start_time = time.perf_counter()

        # 1. 解析文档
        logger.info("ingestion_step", step="parsing", doc_id=doc_id)
        documents = await self.parser.parse(file_path, file_type)

        if not documents:
            logger.warning("no_content_parsed", doc_id=doc_id)
            return 0

        # 2. 分块 (支持语义分块)
        logger.info("ingestion_step", step="chunking", doc_id=doc_id)
        nodes = self.chunker.chunk(
            documents,
            doc_id=doc_id,
            collection=collection,
            strategy=chunking_strategy,
        )

        if not nodes:
            logger.warning("no_chunks_generated", doc_id=doc_id)
            return 0

        # 3. 元数据增强 (可选, 增加成本但提升质量)
        if enable_metadata_extraction and len(nodes) <= 100:
            logger.info("ingestion_step", step="metadata_extraction", doc_id=doc_id)
            nodes = await self.metadata_extractor.extract(nodes)

        # 4. 批量Embedding
        logger.info(
            "ingestion_step", step="embedding",
            doc_id=doc_id, num_chunks=len(nodes),
        )
        embeddings = await self._batch_embed(nodes)

        # 5. 并行写入 Milvus + ES
        logger.info("ingestion_step", step="indexing", doc_id=doc_id)
        await asyncio.gather(
            self._upsert_to_milvus(nodes, embeddings, doc_id, collection),
            self._upsert_to_elasticsearch(nodes, doc_id, collection),
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "ingestion_completed",
            doc_id=doc_id,
            num_chunks=len(nodes),
            latency_ms=round(elapsed_ms, 2),
        )

        return len(nodes)

    async def _batch_embed(
        self, nodes: list[TextNode], batch_size: int = 20
    ) -> list[list[float]]:
        """批量计算Embedding"""
        all_embeddings = []
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i: i + batch_size]
            # 使用增强文本(如果有)
            texts = [
                node.metadata.get("_enriched_text", node.text)
                for node in batch
            ]
            async with self._embedding_semaphore:
                batch_embeddings = await self.embedding_model.aget_text_embedding_batch(texts)
                all_embeddings.extend(batch_embeddings)
        return all_embeddings

    async def _upsert_to_milvus(
        self, nodes: list[TextNode], embeddings: list[list[float]],
        doc_id: str, collection: str,
    ):
        """写入Milvus向量数据库"""
        milvus = get_milvus()
        collection_name = self.settings.MILVUS_COLLECTION_NAME

        data = []
        for node, embedding in zip(nodes, embeddings):
            data.append({
                "id": node.id_,
                "doc_id": doc_id,
                "chunk_index": node.metadata.get("chunk_index", 0),
                "content": node.text,
                "embedding": embedding,
                "doc_title": node.metadata.get("source", ""),
                "collection": collection,
                "created_at": int(datetime.utcnow().timestamp()),
            })

        batch_size = 100
        for i in range(0, len(data), batch_size):
            batch = data[i: i + batch_size]
            milvus.upsert(collection_name=collection_name, data=batch)

    async def _upsert_to_elasticsearch(
        self, nodes: list[TextNode], doc_id: str, collection: str,
    ):
        """写入Elasticsearch (BM25 稀疏检索)"""
        try:
            from src.infra.database.elasticsearch import get_elasticsearch
            es = await get_elasticsearch()

            index_name = f"qa_chunks_{collection}"

            # 确保索引存在
            if not await es.indices.exists(index=index_name):
                await es.indices.create(
                    index=index_name,
                    body={
                        "settings": {
                            "number_of_shards": 1,
                            "number_of_replicas": 0,
                            "analysis": {
                                "analyzer": {
                                    "text_analyzer": {
                                        "type": "standard",
                                        # 中文场景可换为 ik_max_word
                                    }
                                }
                            }
                        },
                        "mappings": {
                            "properties": {
                                "chunk_id": {"type": "keyword"},
                                "doc_id": {"type": "keyword"},
                                "content": {
                                    "type": "text",
                                    "analyzer": "text_analyzer",
                                },
                                "doc_title": {"type": "text"},
                                "collection": {"type": "keyword"},
                                "chunk_index": {"type": "integer"},
                                "keywords": {"type": "text"},
                                "summary": {"type": "text"},
                                "created_at": {"type": "date", "format": "epoch_second"},
                            }
                        }
                    },
                )

            # 批量写入
            actions = []
            for node in nodes:
                actions.append({"index": {"_index": index_name, "_id": node.id_}})
                actions.append({
                    "chunk_id": node.id_,
                    "doc_id": doc_id,
                    "content": node.text,
                    "doc_title": node.metadata.get("source", ""),
                    "collection": collection,
                    "chunk_index": node.metadata.get("chunk_index", 0),
                    "keywords": node.metadata.get("extracted_keywords", ""),
                    "summary": node.metadata.get("extracted_summary", ""),
                    "created_at": int(datetime.utcnow().timestamp()),
                })

            if actions:
                await es.bulk(body=actions)

            logger.info(
                "elasticsearch_upserted",
                doc_id=doc_id,
                index=index_name,
                num_docs=len(nodes),
            )

        except Exception as e:
            # ES写入失败不应阻断整个管道
            logger.error(
                "elasticsearch_upsert_failed",
                doc_id=doc_id,
                error=str(e),
            )


def get_ingestion_pipeline() -> IngestionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = IngestionPipeline(get_settings())
    return _pipeline
```

------

## 四、Week 8：多路召回 & 重排

### 8.1 Elasticsearch 客户端 & 稀疏检索

Python



```
# src/infra/database/elasticsearch.py

from elasticsearch import AsyncElasticsearch
from src.infra.config.settings import get_settings
import structlog

logger = structlog.get_logger()

_es_client: AsyncElasticsearch | None = None


async def init_elasticsearch() -> AsyncElasticsearch:
    """初始化Elasticsearch异步客户端"""
    global _es_client
    settings = get_settings()
    _es_client = AsyncElasticsearch(
        hosts=[settings.ELASTICSEARCH_URL],
        request_timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )
    # 验证连接
    info = await _es_client.info()
    logger.info("elasticsearch_connected", version=info["version"]["number"])
    return _es_client


async def get_elasticsearch() -> AsyncElasticsearch:
    if _es_client is None:
        return await init_elasticsearch()
    return _es_client


async def close_elasticsearch():
    global _es_client
    if _es_client:
        await _es_client.close()
        _es_client = None
```

Python



```
# src/core/rag/retrieval/sparse.py

import structlog
from elasticsearch import AsyncElasticsearch

from src.core.rag.retrieval.dense import RetrievedChunk

logger = structlog.get_logger()


class SparseRetriever:
    """
    稀疏检索器 - Elasticsearch BM25

    优势:
    - 精确关键词匹配 (Dense检索可能遗漏)
    - 对专有名词、编号等精确匹配效果好
    - 与Dense互补, 融合后效果显著提升
    """

    def __init__(self, es_client: AsyncElasticsearch):
        self.es = es_client

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """BM25 检索"""
        index_name = f"qa_chunks_{collection}"

        try:
            # 检查索引是否存在
            if not await self.es.indices.exists(index=index_name):
                logger.warning("es_index_not_found", index=index_name)
                return []

            # BM25 搜索
            response = await self.es.search(
                index=index_name,
                body={
                    "query": {
                        "bool": {
                            "should": [
                                # 主内容匹配 (权重最高)
                                {
                                    "match": {
                                        "content": {
                                            "query": query,
                                            "boost": 3.0,
                                        }
                                    }
                                },
                                # 关键词匹配
                                {
                                    "match": {
                                        "keywords": {
                                            "query": query,
                                            "boost": 2.0,
                                        }
                                    }
                                },
                                # 标题匹配
                                {
                                    "match": {
                                        "doc_title": {
                                            "query": query,
                                            "boost": 1.5,
                                        }
                                    }
                                },
                                # 摘要匹配
                                {
                                    "match": {
                                        "summary": {
                                            "query": query,
                                            "boost": 1.0,
                                        }
                                    }
                                },
                            ],
                            "minimum_should_match": 1,
                        }
                    },
                    "size": top_k,
                    "_source": [
                        "chunk_id", "doc_id", "content",
                        "doc_title", "chunk_index", "collection",
                    ],
                },
            )

            hits = response["hits"]["hits"]
            if not hits:
                return []

            # 归一化BM25分数到0-1范围
            max_score = response["hits"]["max_score"] or 1.0

            chunks = []
            for hit in hits:
                source = hit["_source"]
                normalized_score = hit["_score"] / max_score

                chunks.append(
                    RetrievedChunk(
                        chunk_id=source.get("chunk_id", hit["_id"]),
                        doc_id=source["doc_id"],
                        content=source["content"],
                        score=normalized_score,
                        doc_title=source.get("doc_title", ""),
                        chunk_index=source.get("chunk_index", 0),
                        collection=source.get("collection", collection),
                    )
                )

            logger.info(
                "sparse_retrieval_completed",
                query=query[:100],
                collection=collection,
                num_hits=len(chunks),
                max_score=round(max_score, 3),
            )

            return chunks

        except Exception as e:
            logger.error("sparse_retrieval_failed", error=str(e), query=query[:100])
            return []
```

### 8.2 混合检索 + RRF 融合

Python



```
# src/core/rag/retrieval/hybrid.py

import asyncio
from collections import defaultdict
import structlog

from src.core.rag.retrieval.dense import DenseRetriever, RetrievedChunk
from src.core.rag.retrieval.sparse import SparseRetriever
from src.core.rag.retrieval.reranker import CrossEncoderReranker

logger = structlog.get_logger()


class HybridRetriever:
    """
    混合检索器

    1. 并行执行 Dense(Milvus) + Sparse(ES BM25) 检索
    2. RRF (Reciprocal Rank Fusion) 融合排序
    3. Cross-Encoder Rerank 精排
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever | None = None,
        reranker: CrossEncoderReranker | None = None,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        rrf_k: int = 60,
    ):
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.reranker = reranker
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_k = rrf_k

    async def retrieve(
        self,
        query: str,
        expanded_queries: list[str] | None = None,
        collection: str = "default",
        top_k: int = 5,
        retrieval_top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """
        混合检索 + RRF + Rerank

        Args:
            query: 主查询 (改写后的)
            expanded_queries: 扩展查询列表 (用于多路召回)
            collection: 知识库集合名
            top_k: 最终返回数量
            retrieval_top_k: 初始召回数量 (默认 top_k * 4)
        """
        retrieval_top_k = retrieval_top_k or top_k * 4

        # ============================================================
        # Step 1: 并行多路召回
        # ============================================================
        all_queries = [query]
        if expanded_queries:
            all_queries.extend(expanded_queries[:2])  # 最多用2个扩展查询

        retrieval_tasks = []

        # Dense 检索 (每个查询都检索)
        for q in all_queries:
            retrieval_tasks.append(
                self._safe_retrieve(
                    self.dense.retrieve, q, collection, retrieval_top_k, "dense"
                )
            )

        # Sparse 检索 (只用主查询)
        if self.sparse:
            retrieval_tasks.append(
                self._safe_retrieve(
                    self.sparse.retrieve, query, collection, retrieval_top_k, "sparse"
                )
            )

        results = await asyncio.gather(*retrieval_tasks)

        # 按来源分组
        dense_results = []
        sparse_results = []
        for source, chunks in results:
            if source == "dense":
                dense_results.extend(chunks)
            elif source == "sparse":
                sparse_results.extend(chunks)

        # Dense结果去重 (多个查询可能返回相同文档)
        dense_results = self._deduplicate(dense_results)

        logger.info(
            "hybrid_retrieval_raw_results",
            dense_count=len(dense_results),
            sparse_count=len(sparse_results),
            query=query[:100],
        )

        # ============================================================
        # Step 2: RRF 融合
        # ============================================================
        if sparse_results:
            fused = self._reciprocal_rank_fusion(
                dense_results=dense_results,
                sparse_results=sparse_results,
            )
        else:
            # 如果没有Sparse结果, 直接用Dense
            fused = dense_results

        # 取初步Top-K
        candidates = fused[:top_k * 3]  # 给Reranker多一些候选

        # ============================================================
        # Step 3: Rerank (如果配置了Reranker)
        # ============================================================
        if self.reranker and candidates:
            try:
                reranked = await self.reranker.rerank(
                    query=query,
                    chunks=candidates,
                    top_n=top_k,
                )
                logger.info(
                    "rerank_completed",
                    input_count=len(candidates),
                    output_count=len(reranked),
                    query=query[:100],
                )
                return reranked
            except Exception as e:
                logger.error("rerank_failed_using_rrf_results", error=str(e))
                return candidates[:top_k]

        return candidates[:top_k]

    def _reciprocal_rank_fusion(
        self,
        dense_results: list[RetrievedChunk],
        sparse_results: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """
        RRF 融合算法

        score(d) = w_dense / (k + rank_dense(d)) + w_sparse / (k + rank_sparse(d))
        """
        rrf_scores: dict[str, float] = defaultdict(float)
        chunk_map: dict[str, RetrievedChunk] = {}
        source_map: dict[str, set] = defaultdict(set)

        # Dense 分数
        for rank, chunk in enumerate(dense_results, start=1):
            cid = chunk.chunk_id
            rrf_scores[cid] += self.dense_weight / (self.rrf_k + rank)
            chunk_map[cid] = chunk
            source_map[cid].add("dense")

        # Sparse 分数
        for rank, chunk in enumerate(sparse_results, start=1):
            cid = chunk.chunk_id
            rrf_scores[cid] += self.sparse_weight / (self.rrf_k + rank)
            if cid not in chunk_map:
                chunk_map[cid] = chunk
            source_map[cid].add("sparse")

        # 按RRF分数排序
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        fused = []
        for cid in sorted_ids:
            chunk = chunk_map[cid]
            # 用RRF分数替换原始分数
            fused.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    score=rrf_scores[cid],
                    doc_title=chunk.doc_title,
                    chunk_index=chunk.chunk_index,
                    collection=chunk.collection,
                )
            )

        # 记录融合统计
        both_count = sum(1 for s in source_map.values() if len(s) > 1)
        dense_only = sum(1 for s in source_map.values() if s == {"dense"})
        sparse_only = sum(1 for s in source_map.values() if s == {"sparse"})

        logger.info(
            "rrf_fusion_stats",
            total_unique=len(fused),
            both_sources=both_count,
            dense_only=dense_only,
            sparse_only=sparse_only,
        )

        return fused

    def _deduplicate(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """去重, 保留分数最高的"""
        seen = {}
        for chunk in chunks:
            if chunk.chunk_id not in seen or chunk.score > seen[chunk.chunk_id].score:
                seen[chunk.chunk_id] = chunk
        return list(seen.values())

    async def _safe_retrieve(self, fn, query, collection, top_k, source):
        """安全调用检索, 捕获异常"""
        try:
            results = await fn(query=query, collection=collection, top_k=top_k)
            return (source, results)
        except Exception as e:
            logger.error(f"{source}_retrieval_failed", error=str(e))
            return (source, [])
```

### 8.3 Cross-Encoder Reranker

Python



```
# src/core/rag/retrieval/reranker.py

import asyncio
import structlog
from abc import ABC, abstractmethod

from src.core.rag.retrieval.dense import RetrievedChunk

logger = structlog.get_logger()


class BaseReranker(ABC):
    """重排器基类"""

    @abstractmethod
    async def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_n: int = 5
    ) -> list[RetrievedChunk]:
        ...


class CrossEncoderReranker(BaseReranker):
    """
    Cross-Encoder 重排器

    使用BAAI/bge-reranker模型对query-document对进行精排
    比Bi-Encoder(Dense)更精确, 但速度较慢
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, max_length=512)
        logger.info("cross_encoder_reranker_loaded", model=model_name)

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int = 5,
    ) -> list[RetrievedChunk]:
        """使用Cross-Encoder精排"""
        if not chunks:
            return []

        pairs = [(query, chunk.content) for chunk in chunks]

        # Cross-Encoder推理 (CPU/GPU密集, 放到线程池)
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: self.model.predict(pairs).tolist(),
        )

        # 用Rerank分数替换原始分数, 排序
        scored = []
        for chunk, score in zip(chunks, scores):
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    score=float(score),
                    doc_title=chunk.doc_title,
                    chunk_index=chunk.chunk_index,
                    collection=chunk.collection,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)

        logger.info(
            "cross_encoder_rerank_completed",
            input_count=len(chunks),
            output_count=min(top_n, len(scored)),
            top_score=round(scored[0].score, 4) if scored else 0,
            bottom_score=round(scored[-1].score, 4) if scored else 0,
        )

        return scored[:top_n]


class LLMReranker(BaseReranker):
    """
    LLM Reranker (备选方案)

    使用LLM对检索结果打分排序
    优: 无需额外模型部署
    劣: 成本高, 延迟高
    """

    def __init__(self, llm=None):
        from langchain_openai import ChatOpenAI
        from src.infra.config.settings import get_settings
        settings = get_settings()
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
        )

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_n: int = 5,
    ) -> list[RetrievedChunk]:
        """LLM打分重排"""
        from langchain_core.messages import SystemMessage, HumanMessage

        # 构建文档列表
        doc_list = "\n".join(
            f"[文档{i+1}]: {chunk.content[:300]}"
            for i, chunk in enumerate(chunks)
        )

        prompt = f"""你是一个文档相关性评估专家。给定一个查询和多个候选文档，
请对每个文档与查询的相关性打分(0-10分)。

查询: {query}

候选文档:
{doc_list}

请返回JSON格式: {{"scores": [分数1, 分数2, ...]}}
分数越高表示越相关。"""

        response = await self.llm.ainvoke(
            [HumanMessage(content=prompt)],
            response_format={"type": "json_object"},
        )

        import json
        result = json.loads(response.content)
        scores = result.get("scores", [0] * len(chunks))

        scored = []
        for chunk, score in zip(chunks, scores):
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    score=float(score) / 10.0,
                    doc_title=chunk.doc_title,
                    chunk_index=chunk.chunk_index,
                    collection=chunk.collection,
                )
            )

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_n]
```

### 8.4 检索器统一接口重构

Python



```
# src/core/rag/retrieval/retriever.py  (Phase 2 重构)

import structlog
from src.core.rag.retrieval.dense import DenseRetriever, RetrievedChunk
from src.core.rag.retrieval.sparse import SparseRetriever
from src.core.rag.retrieval.hybrid import HybridRetriever
from src.core.rag.retrieval.reranker import BaseReranker, CrossEncoderReranker

logger = structlog.get_logger()


class RAGRetriever:
    """
    RAG检索器 - 统一检索接口

    Phase 2:
    - Dense + Sparse 多路召回
    - RRF 融合
    - Cross-Encoder Rerank
    - 支持查询扩展 (Multi-Query)
    """

    def __init__(
        self,
        dense_retriever: DenseRetriever,
        sparse_retriever: SparseRetriever | None = None,
        reranker: BaseReranker | None = None,
    ):
        self.hybrid = HybridRetriever(
            dense_retriever=dense_retriever,
            sparse_retriever=sparse_retriever,
            reranker=reranker,
        )

    async def retrieve(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        expanded_queries: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """
        统一检索接口

        Args:
            query: 主查询 (建议使用改写后的查询)
            collection: 知识库集合名
            top_k: 返回结果数
            expanded_queries: 扩展查询列表 (查询理解节点生成)
        """
        return await self.hybrid.retrieve(
            query=query,
            expanded_queries=expanded_queries,
            collection=collection,
            top_k=top_k,
        )
```

### 8.5 引用溯源增强

Python



```
# src/core/rag/synthesis/citation.py

import re
import structlog
from pydantic import BaseModel, Field

from src.core.rag.retrieval.dense import RetrievedChunk
from src.schemas.chat import CitationItem

logger = structlog.get_logger()


class CitationExtractor:
    """
    引用溯源提取器

    功能:
    1. 从LLM输出中识别引用标记 [来源X]
    2. 映射到具体的文档和段落
    3. 生成结构化的引用信息
    """

    def extract_citations(
        self,
        answer: str,
        chunks: list[RetrievedChunk],
    ) -> tuple[str, list[CitationItem]]:
        """
        从回答中提取引用, 并生成引用列表

        Returns:
            (处理后的回答, 引用列表)
        """
        citations = []
        used_sources = set()

        # 提取 [来源X] 模式的引用
        pattern = r'\[来源(\d+)\]'
        matches = re.findall(pattern, answer)

        for match in matches:
            source_idx = int(match) - 1  # 转为0-based
            if 0 <= source_idx < len(chunks) and source_idx not in used_sources:
                chunk = chunks[source_idx]
                citations.append(
                    CitationItem(
                        doc_id=chunk.doc_id,
                        doc_title=chunk.doc_title,
                        content=self._truncate_content(chunk.content, 200),
                        chunk_index=chunk.chunk_index,
                        relevance_score=chunk.score,
                    )
                )
                used_sources.add(source_idx)

        # 如果LLM没有生成引用标记, 但有高分文档, 自动添加
        if not citations and chunks:
            for i, chunk in enumerate(chunks[:3]):  # 取top-3
                if chunk.score > 0.5:
                    citations.append(
                        CitationItem(
                            doc_id=chunk.doc_id,
                            doc_title=chunk.doc_title,
                            content=self._truncate_content(chunk.content, 200),
                            chunk_index=chunk.chunk_index,
                            relevance_score=chunk.score,
                        )
                    )

        return answer, citations

    def _truncate_content(self, text: str, max_length: int) -> str:
        """截取内容, 保证在完整句子边界"""
        if len(text) <= max_length:
            return text

        # 在max_length附近找句子结尾
        truncated = text[:max_length]
        last_period = max(
            truncated.rfind("。"),
            truncated.rfind("."),
            truncated.rfind("！"),
            truncated.rfind("？"),
        )

        if last_period > max_length // 2:
            return text[:last_period + 1]

        return truncated + "..."
```

### 8.6 RAG Agent 节点增强

Python



```
# src/core/orchestrator/nodes/rag_agent.py  (Phase 2 增强)

import structlog
from src.core.orchestrator.state import ConversationState
from src.core.rag.retrieval.retriever import RAGRetriever

logger = structlog.get_logger()


class RAGAgentNode:
    """RAG Agent节点 - Phase 2 增强版"""

    def __init__(self, retriever: RAGRetriever):
        self.retriever = retriever

    async def __call__(self, state: ConversationState) -> dict:
        """执行RAG检索 (支持查询扩展 + 多路召回)"""
        query = state["rewritten_query"] or state["original_query"]
        collection = state["collection"]
        expanded_queries = state.get("expanded_queries", [])

        logger.info(
            "rag_agent_start",
            session_id=state["session_id"],
            query=query[:100],
            expanded_count=len(expanded_queries),
            collection=collection,
        )

        # 混合检索 (Dense + Sparse + RRF + Rerank)
        chunks = await self.retriever.retrieve(
            query=query,
            collection=collection,
            top_k=5,
            expanded_queries=expanded_queries if expanded_queries else None,
        )

        # 转为可序列化的dict
        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "content": c.content,
                "score": c.score,
                "doc_title": c.doc_title,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        logger.info(
            "rag_agent_completed",
            session_id=state["session_id"],
            num_results=len(chunks),
            top_score=chunks[0].score if chunks else 0,
        )

        return {
            "retrieved_chunks": chunks_data,
        }
```

------

## 五、Week 9：语义缓存 & 置信度评估

### 9.1 Redis Stack 语义缓存

Python



```
# src/infra/cache/semantic_cache.py

import hashlib
import json
import numpy as np
import structlog
from datetime import datetime

from redis.asyncio import Redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from llama_index.embeddings.openai import OpenAIEmbedding
from src.schemas.chat import CitationItem

logger = structlog.get_logger()


class SemanticCache:
    """
    语义缓存 - 基于Redis Stack向量搜索

    核心思路:
    - 对用户问题计算Embedding
    - 在缓存中搜索语义相似的已回答问题
    - 如果相似度超过阈值, 直接返回缓存答案
    - 大幅减少重复LLM调用, 降低延迟和成本

    性能预期:
    - 缓存命中: ~50ms (vs 完整RAG流程: ~3-5s)
    - 成本节省: 命中时零LLM调用费
    """

    INDEX_NAME = "idx:semantic_cache"
    KEY_PREFIX = "cache:semantic:"

    def __init__(
        self,
        redis: Redis,
        embedding_model: OpenAIEmbedding,
        similarity_threshold: float = 0.92,
        ttl: int = 86400,  # 24小时
        embedding_dim: int = 3072,
    ):
        self.redis = redis
        self.embedding = embedding_model
        self.threshold = similarity_threshold
        self.ttl = ttl
        self.dim = embedding_dim
        self._initialized = False

    async def initialize(self):
        """创建Redis Search 向量索引"""
        if self._initialized:
            return

        try:
            # 检查索引是否已存在
            await self.redis.ft(self.INDEX_NAME).info()
            self._initialized = True
            logger.info("semantic_cache_index_exists")
            return
        except Exception:
            pass

        # 创建索引
        schema = (
            TextField("$.query", as_name="query"),
            TextField("$.answer", as_name="answer"),
            TextField("$.citations", as_name="citations"),
            TextField("$.collection", as_name="collection"),
            NumericField("$.confidence", as_name="confidence"),
            NumericField("$.timestamp", as_name="timestamp"),
            NumericField("$.hit_count", as_name="hit_count"),
            VectorField(
                "$.embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": self.dim,
                    "DISTANCE_METRIC": "COSINE",
                },
                as_name="embedding",
            ),
        )

        definition = IndexDefinition(
            prefix=[self.KEY_PREFIX],
            index_type=IndexType.JSON,
        )

        await self.redis.ft(self.INDEX_NAME).create_index(
            schema, definition=definition
        )

        self._initialized = True
        logger.info("semantic_cache_index_created")

    async def get(
        self, query: str, collection: str = "default"
    ) -> "CacheHit | None":
        """查询语义缓存"""
        await self.initialize()

        # 1. 计算query embedding
        query_embedding = await self.embedding.aget_text_embedding(query)
        embedding_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

        # 2. 向量相似度搜索
        search_query = (
            Query(
                f'(@collection:{{{collection}}})=>[KNN 3 @embedding $vec AS distance]'
            )
            .sort_by("distance")
            .return_fields(
                "query", "answer", "citations", "confidence",
                "distance", "collection", "hit_count",
            )
            .dialect(2)
        )

        try:
            results = await self.redis.ft(self.INDEX_NAME).search(
                search_query,
                query_params={"vec": embedding_bytes},
            )
        except Exception as e:
            logger.error("semantic_cache_search_failed", error=str(e))
            return None

        if not results.docs:
            logger.debug("semantic_cache_miss", query=query[:100])
            return None

        # 3. 检查最佳结果是否超过阈值
        best = results.docs[0]
        distance = float(best.distance)
        similarity = 1 - distance  # COSINE distance -> similarity

        if similarity >= self.threshold:
            # 缓存命中！
            cache_key = best.id

            # 增加命中计数
            try:
                current_count = int(best.hit_count) if best.hit_count else 0
                await self.redis.json().set(
                    cache_key, "$.hit_count", current_count + 1
                )
                # 刷新TTL
                await self.redis.expire(cache_key, self.ttl)
            except Exception:
                pass

            citations = json.loads(best.citations) if best.citations else []

            logger.info(
                "semantic_cache_hit",
                query=query[:100],
                cached_query=best.query[:100] if best.query else "",
                similarity=round(similarity, 4),
                hit_count=current_count + 1,
            )

            return CacheHit(
                answer=best.answer,
                citations=[CitationItem(**c) for c in citations],
                confidence=float(best.confidence) if best.confidence else 0.0,
                similarity=similarity,
                cached_query=best.query or "",
            )

        logger.debug(
            "semantic_cache_miss_below_threshold",
            query=query[:100],
            best_similarity=round(similarity, 4),
            threshold=self.threshold,
        )
        return None

    async def set(
        self,
        query: str,
        answer: str,
        collection: str = "default",
        citations: list[CitationItem] | None = None,
        confidence: float = 0.0,
    ):
        """写入语义缓存"""
        await self.initialize()

        # 只缓存高质量回答
        if confidence < 0.5:
            logger.debug(
                "semantic_cache_skip_low_confidence",
                confidence=confidence,
            )
            return

        query_embedding = await self.embedding.aget_text_embedding(query)

        cache_key = f"{self.KEY_PREFIX}{hashlib.md5(query.encode()).hexdigest()}"

        citations_json = json.dumps(
            [c.model_dump() for c in (citations or [])],
            ensure_ascii=False,
        )

        await self.redis.json().set(
            cache_key,
            "$",
            {
                "query": query,
                "answer": answer,
                "citations": citations_json,
                "collection": collection,
                "confidence": confidence,
                "embedding": query_embedding,
                "timestamp": int(datetime.utcnow().timestamp()),
                "hit_count": 0,
            },
        )

        await self.redis.expire(cache_key, self.ttl)

        logger.info(
            "semantic_cache_set",
            query=query[:100],
            confidence=confidence,
            ttl=self.ttl,
        )

    async def invalidate_collection(self, collection: str):
        """清除指定集合的所有缓存"""
        # 搜索该collection的所有缓存键
        search_query = Query(f"@collection:{{{collection}}}").no_content()
        try:
            results = await self.redis.ft(self.INDEX_NAME).search(search_query)
            for doc in results.docs:
                await self.redis.delete(doc.id)
            logger.info(
                "semantic_cache_invalidated",
                collection=collection,
                count=len(results.docs),
            )
        except Exception as e:
            logger.error("semantic_cache_invalidate_failed", error=str(e))

    async def get_stats(self) -> dict:
        """获取缓存统计"""
        try:
            info = await self.redis.ft(self.INDEX_NAME).info()
            return {
                "total_entries": info.get("num_docs", 0),
                "index_size_mb": round(
                    int(info.get("inverted_sz_mb", 0)) +
                    int(info.get("vector_index_sz_mb", 0)), 2
                ),
            }
        except Exception:
            return {"total_entries": 0, "index_size_mb": 0}


class CacheHit:
    """缓存命中结果"""
    def __init__(
        self,
        answer: str,
        citations: list[CitationItem],
        confidence: float,
        similarity: float,
        cached_query: str,
    ):
        self.answer = answer
        self.citations = citations
        self.confidence = confidence
        self.similarity = similarity
        self.cached_query = cached_query
```

### 9.2 多级缓存管理器

Python



```
# src/infra/cache/cache_manager.py

import hashlib
import json
import structlog
from redis.asyncio import Redis

from src.infra.cache.semantic_cache import SemanticCache, CacheHit
from src.schemas.chat import CitationItem

logger = structlog.get_logger()


class CacheManager:
    """
    多级缓存管理器

    Level 1: 精确匹配 (Redis KV) - 最快, ~1ms
    Level 2: 语义匹配 (Redis Vector Search) - 快, ~50ms
    """

    def __init__(self, redis: Redis, semantic_cache: SemanticCache):
        self.redis = redis
        self.semantic = semantic_cache

    async def get(
        self, query: str, collection: str = "default"
    ) -> CacheHit | None:
        """查询缓存 (先精确后语义)"""

        # Level 1: 精确匹配
        exact_key = self._exact_key(query, collection)
        exact_result = await self.redis.get(exact_key)
        if exact_result:
            data = json.loads(exact_result)
            logger.info("cache_hit_exact", query=query[:100])
            return CacheHit(
                answer=data["answer"],
                citations=[CitationItem(**c) for c in data.get("citations", [])],
                confidence=data.get("confidence", 0.0),
                similarity=1.0,
                cached_query=query,
            )

        # Level 2: 语义匹配
        semantic_result = await self.semantic.get(query, collection)
        if semantic_result:
            # 同时写入精确缓存 (下次直接命中L1)
            await self._set_exact(query, collection, semantic_result)
            return semantic_result

        return None

    async def set(
        self,
        query: str,
        answer: str,
        collection: str = "default",
        citations: list[CitationItem] | None = None,
        confidence: float = 0.0,
    ):
        """写入缓存 (同时写入L1 + L2)"""
        # L1: 精确缓存
        exact_key = self._exact_key(query, collection)
        data = {
            "answer": answer,
            "citations": [c.model_dump() for c in (citations or [])],
            "confidence": confidence,
        }
        await self.redis.set(exact_key, json.dumps(data, ensure_ascii=False), ex=3600)

        # L2: 语义缓存
        await self.semantic.set(
            query=query,
            answer=answer,
            collection=collection,
            citations=citations,
            confidence=confidence,
        )

    async def invalidate(self, collection: str):
        """清除指定集合的缓存"""
        # 清除精确缓存 (使用pattern删除)
        pattern = f"cache:exact:{collection}:*"
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

        # 清除语义缓存
        await self.semantic.invalidate_collection(collection)

    async def _set_exact(self, query, collection, cache_hit: CacheHit):
        """写入精确缓存"""
        exact_key = self._exact_key(query, collection)
        data = {
            "answer": cache_hit.answer,
            "citations": [c.model_dump() for c in cache_hit.citations],
            "confidence": cache_hit.confidence,
        }
        await self.redis.set(exact_key, json.dumps(data, ensure_ascii=False), ex=3600)

    def _exact_key(self, query: str, collection: str) -> str:
        query_hash = hashlib.md5(query.strip().lower().encode()).hexdigest()
        return f"cache:exact:{collection}:{query_hash}"
```

### 9.3 LLM-based 置信度评估

Python



```
# src/core/quality/confidence.py

import asyncio
import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class ConfidenceAssessment(BaseModel):
    """置信度评估结果"""
    faithfulness: float = Field(ge=0, le=1, description="忠实度: 回答是否基于提供的上下文")
    relevancy: float = Field(ge=0, le=1, description="相关性: 回答是否切题")
    completeness: float = Field(ge=0, le=1, description="完整性: 回答是否覆盖问题的各方面")
    overall: float = Field(ge=0, le=1, description="综合置信度评分")
    reasoning: str = Field(default="", description="评估推理过程")


CONFIDENCE_PROMPT = """你是一个回答质量评估专家。请评估以下问答对的质量。

## 用户问题
{question}

## 参考上下文 (检索到的文档)
{context}

## 生成的回答
{answer}

## 评估维度

1. **faithfulness** (忠实度, 0-1): 回答的内容是否完全基于参考上下文?
   - 1.0: 完全基于上下文, 没有编造
   - 0.5: 部分基于上下文, 有些推断
   - 0.0: 完全编造, 与上下文无关

2. **relevancy** (相关性, 0-1): 回答是否切题? 是否直接回答了用户问题?
   - 1.0: 完全切题
   - 0.5: 部分相关
   - 0.0: 完全偏题

3. **completeness** (完整性, 0-1): 回答是否覆盖了问题的所有方面?
   - 1.0: 全面完整
   - 0.5: 回答了主要部分
   - 0.0: 严重遗漏

4. **overall** (综合评分, 0-1): 综合考虑以上因素的整体质量分

请以JSON格式输出评估结果。"""


class ConfidenceEvaluator:
    """
    LLM-based 置信度评估器

    使用LLM评估RAG回答的质量, 从多个维度打分:
    - faithfulness: 忠实度 (是否基于上下文)
    - relevancy: 相关性 (是否切题)
    - completeness: 完整性 (是否全面)

    综合评分用于:
    - 决定是否降级到Codex
    - 决定是否需要人工审查 (Phase 3)
    - 缓存决策 (只缓存高质量回答)
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        settings = get_settings()
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",  # 用轻量模型, 降低成本
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=30,
        )

    async def evaluate(
        self,
        question: str,
        answer: str,
        contexts: list[str],
    ) -> ConfidenceAssessment:
        """评估回答质量"""

        context_text = "\n---\n".join(contexts) if contexts else "(无参考上下文)"

        try:
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="你是一个严格的回答质量评估专家。"),
                    HumanMessage(
                        content=CONFIDENCE_PROMPT.format(
                            question=question,
                            context=context_text[:3000],  # 限制长度
                            answer=answer[:2000],
                        )
                    ),
                ],
                response_format={"type": "json_object"},
            )

            assessment = ConfidenceAssessment.model_validate_json(response.content)

            logger.info(
                "confidence_evaluated",
                faithfulness=assessment.faithfulness,
                relevancy=assessment.relevancy,
                completeness=assessment.completeness,
                overall=assessment.overall,
            )

            return assessment

        except Exception as e:
            logger.error("confidence_evaluation_failed", error=str(e))
            # 降级: 基于检索分数的简单评估
            return self._fallback_assessment(contexts)

    def _fallback_assessment(self, contexts: list[str]) -> ConfidenceAssessment:
        """降级评估: 无法调用LLM时使用"""
        if not contexts:
            return ConfidenceAssessment(
                faithfulness=0.0, relevancy=0.0,
                completeness=0.0, overall=0.0,
                reasoning="No context available, fallback assessment",
            )
        return ConfidenceAssessment(
            faithfulness=0.5, relevancy=0.5,
            completeness=0.5, overall=0.5,
            reasoning="LLM evaluation failed, using fallback",
        )
```

Python



```
# src/core/quality/hallucination.py

import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class HallucinationResult(BaseModel):
    """幻觉检测结果"""
    has_hallucination: bool = Field(description="是否存在幻觉")
    hallucination_score: float = Field(ge=0, le=1, description="幻觉程度 0=无幻觉, 1=完全幻觉")
    hallucinated_claims: list[str] = Field(
        default_factory=list,
        description="被判定为幻觉的具体声明",
    )
    reasoning: str = ""


HALLUCINATION_PROMPT = """你是一个幻觉检测专家。请检查以下回答是否包含"幻觉"(即不被参考资料支持的虚假信息)。

## 参考资料
{context}

## 待检查的回答
{answer}

## 任务
1. 将回答拆分为独立的事实声明
2. 逐一检查每个声明是否被参考资料支持
3. 标记不被支持的声明为"幻觉"

输出JSON:
- has_hallucination: 是否存在幻觉
- hallucination_score: 幻觉程度 (0-1, 幻觉声明数/总声明数)
- hallucinated_claims: 被判定为幻觉的声明列表
- reasoning: 检测推理过程"""


class HallucinationDetector:
    """
    幻觉检测器

    检测LLM回答中是否包含不被参考资料支持的虚假信息
    """

    def __init__(self, llm: ChatOpenAI | None = None):
        settings = get_settings()
        self.llm = llm or ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
            timeout=30,
        )

    async def detect(
        self, answer: str, contexts: list[str]
    ) -> HallucinationResult:
        """检测幻觉"""
        if not contexts:
            return HallucinationResult(
                has_hallucination=True,
                hallucination_score=1.0,
                reasoning="No reference context provided",
            )

        try:
            context_text = "\n---\n".join(contexts)

            response = await self.llm.ainvoke(
                [
                    SystemMessage(content="你是一个严格的幻觉检测专家。"),
                    HumanMessage(
                        content=HALLUCINATION_PROMPT.format(
                            context=context_text[:3000],
                            answer=answer[:2000],
                        )
                    ),
                ],
                response_format={"type": "json_object"},
            )

            result = HallucinationResult.model_validate_json(response.content)

            logger.info(
                "hallucination_detected",
                has_hallucination=result.has_hallucination,
                score=result.hallucination_score,
                num_claims=len(result.hallucinated_claims),
            )

            return result

        except Exception as e:
            logger.error("hallucination_detection_failed", error=str(e))
            return HallucinationResult(
                has_hallucination=False,
                hallucination_score=0.3,
                reasoning=f"Detection failed: {str(e)}",
            )
```

### 9.4 质量评估节点重构

Python



```
# src/core/orchestrator/nodes/quality_gate.py  (Phase 2 重构)

import asyncio
import structlog

from src.core.orchestrator.state import ConversationState
from src.core.quality.confidence import ConfidenceEvaluator, ConfidenceAssessment
from src.core.quality.hallucination import HallucinationDetector
from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class QualityGateNode:
    """
    质量评估节点 - Phase 2 LLM-based

    评估维度:
    1. 基于检索分数的初步评估
    2. LLM-based 置信度评估 (faithfulness + relevancy + completeness)
    3. 幻觉检测

    决策规则:
    - overall >= 0.7  → 直接返回 (generate_answer)
    - overall >= 0.4  → 降级Codex (codex_fallback)
    - overall < 0.4   → 需要人工审查 (Phase 3)
    """

    def __init__(
        self,
        confidence_evaluator: ConfidenceEvaluator | None = None,
        hallucination_detector: HallucinationDetector | None = None,
    ):
        self.confidence_evaluator = confidence_evaluator or ConfidenceEvaluator()
        self.hallucination_detector = hallucination_detector or HallucinationDetector()

    async def __call__(self, state: ConversationState) -> dict:
        """执行质量评估"""
        answer = state.get("answer", "")
        chunks = state.get("retrieved_chunks", [])
        query = state.get("rewritten_query") or state["original_query"]

        # 如果还没有生成答案 (在RAG检索之后, 答案生成之前)
        # 则仅基于检索分数做初步评估
        if not answer:
            return self._retrieval_only_assessment(chunks)

        contexts = [c["content"] for c in chunks]

        # 并行执行: 置信度评估 + 幻觉检测
        confidence_task = self.confidence_evaluator.evaluate(
            question=query,
            answer=answer,
            contexts=contexts,
        )
        hallucination_task = self.hallucination_detector.detect(
            answer=answer,
            contexts=contexts,
        )

        confidence_result, hallucination_result = await asyncio.gather(
            confidence_task, hallucination_task,
            return_exceptions=True,
        )

        # 处理异常
        if isinstance(confidence_result, Exception):
            logger.error("confidence_eval_error", error=str(confidence_result))
            confidence_result = ConfidenceAssessment(
                faithfulness=0.5, relevancy=0.5,
                completeness=0.5, overall=0.5,
            )

        if isinstance(hallucination_result, Exception):
            logger.error("hallucination_detect_error", error=str(hallucination_result))
            hallucination_result = None

        # 综合评分 (考虑幻觉)
        overall = confidence_result.overall
        if hallucination_result and hallucination_result.has_hallucination:
            # 有幻觉时降低置信度
            penalty = hallucination_result.hallucination_score * 0.3
            overall = max(0.0, overall - penalty)

        logger.info(
            "quality_gate_evaluated",
            session_id=state["session_id"],
            confidence_overall=round(confidence_result.overall, 3),
            hallucination=hallucination_result.hallucination_score if hallucination_result else "N/A",
            final_confidence=round(overall, 3),
        )

        return {
            "confidence": overall,
            "quality_metrics": {
                "faithfulness": confidence_result.faithfulness,
                "relevancy": confidence_result.relevancy,
                "completeness": confidence_result.completeness,
                "hallucination_score": (
                    hallucination_result.hallucination_score
                    if hallucination_result else 0.0
                ),
            },
        }

    def _retrieval_only_assessment(self, chunks: list[dict]) -> dict:
        """仅基于检索结果的初步评估"""
        if not chunks:
            return {"confidence": 0.0, "quality_metrics": {}}

        scores = [c.get("score", 0) for c in chunks]
        top_score = max(scores)
        avg_score = sum(scores) / len(scores)
        confidence = 0.6 * top_score + 0.4 * avg_score

        return {"confidence": confidence, "quality_metrics": {}}


def should_fallback(state: ConversationState) -> str:
    """条件路由: 根据质量评估决定下一步"""
    settings = get_settings()
    confidence = state.get("confidence", 0)

    if confidence >= settings.CONFIDENCE_THRESHOLD_PASS:
        return "generate_answer"
    else:
        return "codex_fallback"
```

### 9.5 LangGraph 图增强（加入缓存节点）

Python



```
# src/core/orchestrator/nodes/cache_lookup.py

import structlog
from langchain_core.messages import AIMessage

from src.core.orchestrator.state import ConversationState
from src.infra.cache.cache_manager import CacheManager

logger = structlog.get_logger()


class CacheLookupNode:
    """缓存查询节点 - 在RAG之前检查缓存"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    async def __call__(self, state: ConversationState) -> dict:
        """检查语义缓存"""
        query = state.get("rewritten_query") or state["original_query"]
        collection = state["collection"]

        cache_hit = await self.cache.get(query, collection)

        if cache_hit:
            logger.info(
                "cache_hit_in_graph",
                session_id=state["session_id"],
                similarity=round(cache_hit.similarity, 4),
            )
            return {
                "answer": cache_hit.answer,
                "citations": [c.model_dump() for c in cache_hit.citations],
                "confidence": cache_hit.confidence,
                "model_used": "cache",
                "fallback_used": False,
                "cache_hit": True,
                "messages": [AIMessage(content=cache_hit.answer)],
            }

        return {"cache_hit": False}


def should_skip_rag(state: ConversationState) -> str:
    """条件路由: 缓存命中则跳过RAG"""
    if state.get("cache_hit", False):
        return "skip_to_end"
    
    intent = state.get("intent", "knowledge_qa")
    if intent == "chitchat":
        return "codex_fallback"  # 闲聊不走RAG
    
    return "rag_agent"
```

Python



```
# src/core/orchestrator/graph.py  (Phase 2 增强)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.core.orchestrator.state import ConversationState
from src.core.orchestrator.nodes.query_understanding import QueryUnderstandingNode
from src.core.orchestrator.nodes.cache_lookup import CacheLookupNode, should_skip_rag
from src.core.orchestrator.nodes.rag_agent import RAGAgentNode
from src.core.orchestrator.nodes.quality_gate import QualityGateNode, should_fallback
from src.core.orchestrator.nodes.response_synthesizer import ResponseSynthesizerNode
from src.core.orchestrator.nodes.codex_fallback import CodexFallbackNode


def build_graph(
    query_understanding_node: QueryUnderstandingNode,
    cache_lookup_node: CacheLookupNode,
    rag_agent_node: RAGAgentNode,
    quality_gate_node: QualityGateNode,
    response_synthesizer_node: ResponseSynthesizerNode,
    codex_fallback_node: CodexFallbackNode,
) -> StateGraph:
    """
    构建Phase 2对话图

    Phase 2 新增:
    - 查询理解增强 (LLM改写)
    - 语义缓存查询
    - 意图路由 (闲聊直接走Codex)
    - LLM-based 质量评估
    """

    graph = StateGraph(ConversationState)

    # === 节点 ===
    graph.add_node("query_understanding", query_understanding_node)
    graph.add_node("cache_lookup",        cache_lookup_node)
    graph.add_node("rag_agent",           rag_agent_node)
    graph.add_node("generate_answer",     response_synthesizer_node)
    graph.add_node("quality_gate",        quality_gate_node)
    graph.add_node("codex_fallback",      codex_fallback_node)

    # === 边 ===
    graph.add_edge(START, "query_understanding")
    graph.add_edge("query_understanding", "cache_lookup")

    # 缓存命中 → 跳过RAG, 直接结束
    # 闲聊 → Codex
    # 知识问答 → RAG
    graph.add_conditional_edges(
        "cache_lookup",
        should_skip_rag,
        {
            "skip_to_end":   END,           # 缓存命中
            "codex_fallback": "codex_fallback",  # 闲聊
            "rag_agent":     "rag_agent",   # 知识问答
        },
    )

    graph.add_edge("rag_agent", "generate_answer")
    graph.add_edge("generate_answer", "quality_gate")

    # 质量评估决策
    graph.add_conditional_edges(
        "quality_gate",
        should_fallback,
        {
            "generate_answer": END,          # 质量OK, 直接结束 (答案已生成)
            "codex_fallback":  "codex_fallback",  # 降级
        },
    )

    graph.add_edge("codex_fallback", END)

    return graph
```

text



```
Phase 2 图可视化:

    ┌─────────────────┐
    │      START      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ query_under-    │ ← LLM改写 + 指代消解 + 查询扩展
    │ standing        │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  cache_lookup   │ ← 语义缓存查询
    └───┬────┬────┬───┘
        │    │    │
   命中 │    │闲聊 │知识问答
        ▼    │    ▼
    ┌──────┐ │  ┌──────────────┐
    │ END  │ │  │  rag_agent   │ ← Dense+Sparse+RRF+Rerank
    └──────┘ │  └──────┬───────┘
             │         │
             │         ▼
             │  ┌──────────────┐
             │  │generate_answer│ ← RAG答案合成 + 引用
             │  └──────┬───────┘
             │         │
             │         ▼
             │  ┌──────────────┐
             │  │ quality_gate │ ← LLM置信度 + 幻觉检测
             │  └───┬──────┬───┘
             │      │      │
             │  ≥0.7│  <0.7│
             │      ▼      │
             │  ┌──────┐   │
             │  │ END  │   │
             │  └──────┘   │
             │             ▼
             │      ┌──────────────┐
             └─────▶│codex_fallback│ ← 降级兜底
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     END      │
                    └──────────────┘
```

------

## 六、Week 10：LLM 可观测性 & RAG 评估

### 10.1 LangFuse 集成

Python



```
# src/infra/logging/langfuse_tracer.py

import structlog
from langfuse import Langfuse
from langfuse.callback import CallbackHandler as LangfuseCallbackHandler

from src.infra.config.settings import get_settings

logger = structlog.get_logger()

_langfuse: Langfuse | None = None


class LangfuseConfig:
    """LangFuse配置 - 添加到Settings中"""
    LANGFUSE_ENABLED: bool = True
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"


def init_langfuse() -> Langfuse | None:
    """初始化LangFuse客户端"""
    global _langfuse
    settings = get_settings()

    if not getattr(settings, "LANGFUSE_ENABLED", False):
        logger.info("langfuse_disabled")
        return None

    try:
        _langfuse = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        # 验证连接
        _langfuse.auth_check()
        logger.info("langfuse_connected", host=settings.LANGFUSE_HOST)
        return _langfuse
    except Exception as e:
        logger.warning("langfuse_init_failed", error=str(e))
        return None


def get_langfuse() -> Langfuse | None:
    return _langfuse


class LLMTracer:
    """
    LLM调用追踪器

    功能:
    1. 追踪每次LLM调用 (输入/输出/Token/延迟)
    2. 关联到会话 (session_id)
    3. 构建调用链路 (Trace -> Span -> Generation)
    4. 成本估算
    """

    def __init__(self, langfuse: Langfuse | None = None):
        self.langfuse = langfuse or _langfuse

    def create_trace(
        self,
        session_id: str,
        user_id: str = "default",
        name: str = "chat_completion",
        metadata: dict | None = None,
    ) -> "TraceContext":
        """创建一个追踪上下文"""
        if not self.langfuse:
            return NoOpTraceContext()

        trace = self.langfuse.trace(
            name=name,
            session_id=session_id,
            user_id=user_id,
            metadata=metadata or {},
        )

        return TraceContext(trace=trace, langfuse=self.langfuse)

    def get_langchain_callback(
        self,
        session_id: str,
        user_id: str = "default",
    ) -> LangfuseCallbackHandler | None:
        """获取LangChain回调处理器 (自动追踪LLM调用)"""
        if not self.langfuse:
            return None

        return LangfuseCallbackHandler(
            public_key=get_settings().LANGFUSE_PUBLIC_KEY,
            secret_key=get_settings().LANGFUSE_SECRET_KEY,
            host=get_settings().LANGFUSE_HOST,
            session_id=session_id,
            user_id=user_id,
        )


class TraceContext:
    """追踪上下文 - 管理Span生命周期"""

    def __init__(self, trace, langfuse: Langfuse):
        self.trace = trace
        self.langfuse = langfuse

    def span(self, name: str, **kwargs):
        """创建子Span"""
        return self.trace.span(name=name, **kwargs)

    def generation(self, name: str, **kwargs):
        """记录LLM Generation"""
        return self.trace.generation(name=name, **kwargs)

    def score(self, name: str, value: float, comment: str = ""):
        """记录评分"""
        self.trace.score(name=name, value=value, comment=comment)

    def update(self, **kwargs):
        """更新Trace元数据"""
        self.trace.update(**kwargs)

    def flush(self):
        """刷新到LangFuse服务器"""
        self.langfuse.flush()


class NoOpTraceContext:
    """空操作追踪上下文 (LangFuse未启用时使用)"""
    def span(self, *args, **kwargs): return self
    def generation(self, *args, **kwargs): return self
    def score(self, *args, **kwargs): pass
    def update(self, *args, **kwargs): pass
    def flush(self): pass
    def end(self, *args, **kwargs): pass
```

### 10.2 编排引擎集成 LangFuse 追踪

Python



```
# src/core/orchestrator/engine.py  (Phase 2 增强 - 关键变更部分)

class ConversationOrchestrator:
    """Phase 2 增强: 增加缓存 + LangFuse追踪"""

    def __init__(
        self,
        compiled_graph,
        memory_manager,
        cache_manager,          # [新增]
        llm_tracer,             # [新增]
        pg_pool,
    ):
        self.graph = compiled_graph
        self.memory = memory_manager
        self.cache = cache_manager
        self.tracer = llm_tracer
        self.pg_pool = pg_pool

    async def run(
        self,
        session_id: str,
        message: str,
        collection: str = "default",
    ) -> OrchestratorResult:
        """执行一轮对话"""
        start_time = time.perf_counter()

        # 创建LangFuse追踪
        trace_ctx = self.tracer.create_trace(
            session_id=session_id,
            name="chat_completion",
            metadata={"collection": collection, "query": message[:200]},
        )

        try:
            # 加载对话历史
            history_span = trace_ctx.span(name="load_memory")
            history = await self.memory.load_context(session_id, max_turns=5)
            history_span.end()

            # 构建初始状态
            initial_messages = self._build_initial_messages(history, message)

            initial_state = {
                "messages": initial_messages,
                "session_id": session_id,
                "collection": collection,
                "original_query": message,
                "rewritten_query": "",
                "expanded_queries": [],
                "intent": "knowledge_qa",
                "retrieved_chunks": [],
                "answer": "",
                "citations": [],
                "confidence": 0.0,
                "quality_metrics": {},
                "model_used": "",
                "tokens_used": 0,
                "fallback_used": False,
                "cache_hit": False,
                "error": None,
            }

            thread_config = {"configurable": {"thread_id": session_id}}

            # 获取LangChain回调 (自动追踪LLM调用)
            langfuse_callback = self.tracer.get_langchain_callback(session_id)
            if langfuse_callback:
                thread_config["callbacks"] = [langfuse_callback]

            # 执行图
            result_state = await self.graph.ainvoke(
                initial_state, config=thread_config,
            )

            # 记录质量分数到LangFuse
            trace_ctx.score(
                name="confidence",
                value=result_state.get("confidence", 0),
            )
            trace_ctx.score(
                name="cache_hit",
                value=1.0 if result_state.get("cache_hit") else 0.0,
            )

            # 保存记忆
            if not result_state.get("cache_hit"):
                await self.memory.save_turn(
                    session_id=session_id,
                    user_message=message,
                    assistant_message=result_state["answer"],
                )

                # 写入缓存 (仅高质量回答)
                if result_state.get("confidence", 0) >= 0.5:
                    citations = [CitationItem(**c) for c in result_state.get("citations", [])]
                    await self.cache.set(
                        query=result_state.get("rewritten_query") or message,
                        answer=result_state["answer"],
                        collection=collection,
                        citations=citations,
                        confidence=result_state["confidence"],
                    )

            # 持久化到PostgreSQL
            await self._save_to_db(session_id, message, result_state)

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # 更新Trace
            trace_ctx.update(
                output=result_state["answer"][:500],
                metadata={
                    "latency_ms": elapsed_ms,
                    "cache_hit": result_state.get("cache_hit", False),
                    "fallback_used": result_state.get("fallback_used", False),
                },
            )

            return OrchestratorResult(
                answer=result_state["answer"],
                citations=[CitationItem(**c) for c in result_state.get("citations", [])],
                confidence=result_state.get("confidence", 0),
                model_used=result_state.get("model_used", ""),
                fallback_used=result_state.get("fallback_used", False),
                tokens_used=result_state.get("tokens_used", 0),
            )

        except Exception as e:
            trace_ctx.score(name="error", value=1.0, comment=str(e))
            logger.exception("orchestrator_error", session_id=session_id)
            return OrchestratorResult(
                answer="抱歉，处理您的问题时出现了错误。请稍后重试。",
            )
        finally:
            trace_ctx.flush()
```

### 10.3 RAGAS 评估模块

Python



```
# src/evaluation/ragas_evaluator.py

import json
import uuid
from datetime import datetime
import structlog

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)
from pydantic import BaseModel, Field

from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class TestCase(BaseModel):
    """单个测试用例"""
    question: str
    ground_truth: str | None = None
    generated_answer: str | None = None
    contexts: list[str] = Field(default_factory=list)


class EvaluationMetrics(BaseModel):
    """评估指标"""
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    answer_correctness: float | None = None


class EvaluationReport(BaseModel):
    """评估报告"""
    run_id: str
    name: str
    total_samples: int
    avg_metrics: EvaluationMetrics
    per_sample_metrics: list[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    config: dict = Field(default_factory=dict)


class RagasEvaluator:
    """
    RAGAS 评估器

    指标:
    - faithfulness: 答案是否基于上下文 (忠实度)
    - answer_relevancy: 答案是否切题
    - context_precision: 检索的上下文是否精确
    - context_recall: 检索是否召回了所有相关信息
    - answer_correctness: 答案是否正确 (需要ground_truth)
    """

    def __init__(self):
        settings = get_settings()
        # RAGAS内部使用的LLM
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
        )
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
        )

    async def evaluate_batch(
        self,
        test_cases: list[TestCase],
        name: str = "evaluation",
        metrics_list: list[str] | None = None,
    ) -> EvaluationReport:
        """
        批量评估

        Args:
            test_cases: 测试用例列表
            name: 评估任务名称
            metrics_list: 要计算的指标 (默认全部)
        """
        run_id = f"eval_{uuid.uuid4().hex[:12]}"

        logger.info(
            "ragas_evaluation_start",
            run_id=run_id,
            name=name,
            num_samples=len(test_cases),
        )

        # 构建HuggingFace Dataset
        data = {
            "question": [],
            "answer": [],
            "contexts": [],
        }

        has_ground_truth = any(tc.ground_truth for tc in test_cases)
        if has_ground_truth:
            data["ground_truth"] = []

        for tc in test_cases:
            data["question"].append(tc.question)
            data["answer"].append(tc.generated_answer or "")
            data["contexts"].append(tc.contexts)
            if has_ground_truth:
                data["ground_truth"].append(tc.ground_truth or "")

        dataset = Dataset.from_dict(data)

        # 选择指标
        selected_metrics = self._select_metrics(metrics_list, has_ground_truth)

        # 执行评估
        try:
            results = evaluate(
                dataset=dataset,
                metrics=selected_metrics,
                llm=self.llm,
                embeddings=self.embeddings,
                raise_exceptions=False,
            )

            # 构建报告
            results_df = results.to_pandas()

            avg_metrics = EvaluationMetrics(
                faithfulness=self._safe_mean(results_df, "faithfulness"),
                answer_relevancy=self._safe_mean(results_df, "answer_relevancy"),
                context_precision=self._safe_mean(results_df, "context_precision"),
                context_recall=self._safe_mean(results_df, "context_recall"),
                answer_correctness=self._safe_mean(results_df, "answer_correctness"),
            )

            per_sample = results_df.to_dict(orient="records")

            report = EvaluationReport(
                run_id=run_id,
                name=name,
                total_samples=len(test_cases),
                avg_metrics=avg_metrics,
                per_sample_metrics=per_sample,
                config={
                    "metrics": [m.name for m in selected_metrics],
                    "llm_model": "gpt-4o-mini",
                },
            )

            # 持久化报告
            await self._save_report(report)

            logger.info(
                "ragas_evaluation_completed",
                run_id=run_id,
                avg_faithfulness=avg_metrics.faithfulness,
                avg_relevancy=avg_metrics.answer_relevancy,
                avg_precision=avg_metrics.context_precision,
            )

            return report

        except Exception as e:
            logger.error("ragas_evaluation_failed", run_id=run_id, error=str(e))
            raise

    def _select_metrics(self, metrics_list, has_ground_truth):
        """选择评估指标"""
        all_metrics = {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "context_precision": context_precision,
        }

        if has_ground_truth:
            all_metrics.update({
                "context_recall": context_recall,
                "answer_correctness": answer_correctness,
            })

        if metrics_list:
            return [all_metrics[m] for m in metrics_list if m in all_metrics]
        return list(all_metrics.values())

    def _safe_mean(self, df, col):
        """安全计算均值"""
        if col in df.columns:
            values = df[col].dropna()
            return round(float(values.mean()), 4) if len(values) > 0 else None
        return None

    async def _save_report(self, report: EvaluationReport):
        """保存评估报告到PostgreSQL"""
        from src.infra.database.postgres import get_postgres_pool
        pool = await get_postgres_pool()

        await pool.execute(
            """INSERT INTO evaluation_runs 
               (id, name, dataset_size, status, metrics, config, completed_at)
               VALUES ($1, $2, $3, $4, $5, $6, NOW())""",
            report.run_id,
            report.name,
            report.total_samples,
            "completed",
            json.dumps(report.avg_metrics.model_dump(), ensure_ascii=False),
            json.dumps(report.config, ensure_ascii=False),
        )

        # 保存每条结果
        for sample in report.per_sample_metrics:
            await pool.execute(
                """INSERT INTO evaluation_results 
                   (run_id, question, ground_truth, generated_answer, contexts, metrics)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                report.run_id,
                sample.get("question", ""),
                sample.get("ground_truth", ""),
                sample.get("answer", ""),
                json.dumps(sample.get("contexts", []), ensure_ascii=False),
                json.dumps(
                    {k: v for k, v in sample.items()
                     if k not in ("question", "answer", "contexts", "ground_truth")},
                    ensure_ascii=False,
                ),
            )
```

### 10.4 DeepEval 补充评估

Python



```
# src/evaluation/deepeval_evaluator.py

import structlog
from deepeval import evaluate as deepeval_evaluate
from deepeval.metrics import (
    FaithfulnessMetric,
    ContextualRelevancyMetric,
    HallucinationMetric,
    AnswerRelevancyMetric,
    GEval,
)
from deepeval.test_case import LLMTestCase

from src.evaluation.ragas_evaluator import TestCase, EvaluationMetrics

logger = structlog.get_logger()


class DeepEvalEvaluator:
    """
    DeepEval 评估器

    与RAGAS互补:
    - GEval: 自定义评估标准 (如企业级规范)
    - HallucinationMetric: 更细粒度的幻觉检测
    - 支持Conversational评估 (多轮对话质量)
    """

    def __init__(self):
        self.metrics = [
            FaithfulnessMetric(
                threshold=0.7,
                include_reason=True,
            ),
            ContextualRelevancyMetric(
                threshold=0.7,
                include_reason=True,
            ),
            HallucinationMetric(
                threshold=0.5,
                include_reason=True,
            ),
            AnswerRelevancyMetric(
                threshold=0.7,
                include_reason=True,
            ),
            # 自定义企业级评估标准
            GEval(
                name="企业问答规范",
                criteria=(
                    "评估答案是否符合企业问答规范: "
                    "1. 语言专业得体 "
                    "2. 不包含不确定/模棱两可的表述(除非确实无法确认) "
                    "3. 提供了可操作的具体信息 "
                    "4. 引用了来源"
                ),
                evaluation_params=[
                    LLMTestCase.input,
                    LLMTestCase.actual_output,
                    LLMTestCase.retrieval_context,
                ],
                threshold=0.6,
            ),
        ]

    async def evaluate_batch(
        self, test_cases: list[TestCase]
    ) -> dict:
        """批量评估"""
        deepeval_cases = []

        for tc in test_cases:
            deepeval_cases.append(
                LLMTestCase(
                    input=tc.question,
                    actual_output=tc.generated_answer or "",
                    expected_output=tc.ground_truth,
                    retrieval_context=tc.contexts,
                )
            )

        try:
            results = deepeval_evaluate(
                test_cases=deepeval_cases,
                metrics=self.metrics,
                run_async=True,
                print_results=False,
            )

            # 提取分数
            metric_scores = {}
            for metric in self.metrics:
                scores = []
                for tc in deepeval_cases:
                    for m in tc.metrics:
                        if m.name == metric.name and m.score is not None:
                            scores.append(m.score)
                if scores:
                    metric_scores[metric.name] = {
                        "avg": round(sum(scores) / len(scores), 4),
                        "min": round(min(scores), 4),
                        "max": round(max(scores), 4),
                    }

            logger.info("deepeval_evaluation_completed", metrics=metric_scores)
            return metric_scores

        except Exception as e:
            logger.error("deepeval_evaluation_failed", error=str(e))
            raise
```

### 10.5 测试集生成 & 评估运行器

Python



```
# src/evaluation/dataset_generator.py

import json
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from src.evaluation.ragas_evaluator import TestCase
from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class GeneratedQA(BaseModel):
    """自动生成的问答对"""
    question: str
    answer: str
    difficulty: str = "medium"  # easy / medium / hard


TESTSET_GENERATION_PROMPT = """根据以下文档内容，生成{count}个测试问答对。

文档内容:
---
{document_text}
---

要求:
1. 问题应覆盖文档的不同方面
2. 包含不同难度: 简单(直接信息提取)、中等(需要理解)、困难(需要推理/多段信息)
3. 答案应该准确、完整，基于文档内容
4. 生成多样化的问题类型: 事实性、比较性、流程性等

输出JSON数组格式: [{{"question": "...", "answer": "...", "difficulty": "easy/medium/hard"}}]"""


class TestsetGenerator:
    """评估测试集自动生成器"""

    def __init__(self):
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.PRIMARY_LLM_MODEL,
            temperature=0.7,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
        )

    async def generate_from_documents(
        self,
        documents: list[str],
        count_per_doc: int = 5,
    ) -> list[TestCase]:
        """从文档生成测试集"""
        all_cases = []

        for doc_text in documents:
            try:
                response = await self.llm.ainvoke(
                    [
                        SystemMessage(content="你是一个测试数据生成专家。"),
                        HumanMessage(
                            content=TESTSET_GENERATION_PROMPT.format(
                                count=count_per_doc,
                                document_text=doc_text[:5000],
                            )
                        ),
                    ],
                    response_format={"type": "json_object"},
                )

                # 解析结果
                result = json.loads(response.content)
                qa_pairs = result if isinstance(result, list) else result.get("questions", [])

                for qa in qa_pairs:
                    generated = GeneratedQA.model_validate(qa)
                    all_cases.append(
                        TestCase(
                            question=generated.question,
                            ground_truth=generated.answer,
                        )
                    )

            except Exception as e:
                logger.error("testset_generation_failed", error=str(e))
                continue

        logger.info("testset_generated", total=len(all_cases))
        return all_cases
```

Python



```
# src/evaluation/runner.py

import structlog
from src.evaluation.ragas_evaluator import RagasEvaluator, TestCase, EvaluationReport
from src.evaluation.deepeval_evaluator import DeepEvalEvaluator
from src.evaluation.dataset_generator import TestsetGenerator
from src.core.orchestrator.engine import ConversationOrchestrator

logger = structlog.get_logger()


class EvaluationRunner:
    """
    评估运行器

    完整流程:
    1. 加载/生成测试集
    2. 对每个问题执行RAG问答
    3. 收集回答和检索上下文
    4. 运行RAGAS + DeepEval评估
    5. 生成报告
    """

    def __init__(
        self,
        orchestrator: ConversationOrchestrator,
        ragas_evaluator: RagasEvaluator,
        deepeval_evaluator: DeepEvalEvaluator | None = None,
    ):
        self.orchestrator = orchestrator
        self.ragas = ragas_evaluator
        self.deepeval = deepeval_evaluator

    async def run_evaluation(
        self,
        test_cases: list[TestCase],
        collection: str = "default",
        name: str = "evaluation",
    ) -> EvaluationReport:
        """
        执行完整评估

        1. 对每个问题执行RAG
        2. 收集回答
        3. 运行评估
        """
        logger.info(
            "evaluation_run_start",
            name=name,
            num_cases=len(test_cases),
            collection=collection,
        )

        # Step 1: 执行RAG, 收集回答
        enriched_cases = []
        for i, tc in enumerate(test_cases):
            try:
                result = await self.orchestrator.run(
                    session_id=f"eval_{name}_{i}",
                    message=tc.question,
                    collection=collection,
                )

                enriched_cases.append(
                    TestCase(
                        question=tc.question,
                        ground_truth=tc.ground_truth,
                        generated_answer=result.answer,
                        contexts=[c.content for c in result.citations] if result.citations else [],
                    )
                )

                logger.debug(
                    "evaluation_sample_completed",
                    index=i,
                    question=tc.question[:100],
                    confidence=result.confidence,
                )

            except Exception as e:
                logger.error(
                    "evaluation_sample_failed",
                    index=i,
                    error=str(e),
                )
                enriched_cases.append(
                    TestCase(
                        question=tc.question,
                        ground_truth=tc.ground_truth,
                        generated_answer="[ERROR] " + str(e),
                        contexts=[],
                    )
                )

        # Step 2: RAGAS评估
        report = await self.ragas.evaluate_batch(
            test_cases=enriched_cases,
            name=name,
        )

        # Step 3: DeepEval评估 (可选)
        if self.deepeval:
            try:
                deepeval_results = await self.deepeval.evaluate_batch(enriched_cases)
                report.config["deepeval_metrics"] = deepeval_results
            except Exception as e:
                logger.error("deepeval_failed", error=str(e))

        logger.info(
            "evaluation_run_completed",
            name=name,
            faithfulness=report.avg_metrics.faithfulness,
            relevancy=report.avg_metrics.answer_relevancy,
            precision=report.avg_metrics.context_precision,
        )

        return report
```

### 10.6 评估 API

Python



```
# src/api/routers/evaluation.py

import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
import structlog

from src.evaluation.ragas_evaluator import TestCase, EvaluationReport
from src.evaluation.runner import EvaluationRunner
from src.evaluation.dataset_generator import TestsetGenerator

logger = structlog.get_logger()
router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


class RunEvaluationRequest(BaseModel):
    """运行评估请求"""
    name: str = "manual_evaluation"
    collection: str = "default"
    test_cases: list[TestCase]
    run_deepeval: bool = False


class GenerateTestsetRequest(BaseModel):
    """生成测试集请求"""
    collection: str = "default"
    count_per_doc: int = 5
    max_docs: int = 10


@router.post("/run")
async def run_evaluation(
    request: RunEvaluationRequest,
    background_tasks: BackgroundTasks,
):
    """触发评估任务 (后台异步执行)"""
    task_id = f"eval_{uuid.uuid4().hex[:12]}"

    # 异步执行评估
    background_tasks.add_task(
        _run_evaluation_task,
        task_id=task_id,
        name=request.name,
        collection=request.collection,
        test_cases=request.test_cases,
        run_deepeval=request.run_deepeval,
    )

    return {
        "task_id": task_id,
        "status": "running",
        "message": f"评估任务已启动, 共 {len(request.test_cases)} 个样本",
    }


async def _run_evaluation_task(task_id, name, collection, test_cases, run_deepeval):
    """后台评估任务"""
    from src.evaluation.ragas_evaluator import RagasEvaluator
    from src.evaluation.deepeval_evaluator import DeepEvalEvaluator

    try:
        ragas = RagasEvaluator()
        deepeval = DeepEvalEvaluator() if run_deepeval else None

        # 获取orchestrator (需要依赖注入改进)
        from src.api.main import app
        orchestrator = app.state.orchestrator

        runner = EvaluationRunner(
            orchestrator=orchestrator,
            ragas_evaluator=ragas,
            deepeval_evaluator=deepeval,
        )

        report = await runner.run_evaluation(
            test_cases=test_cases,
            collection=collection,
            name=name,
        )

        logger.info("evaluation_task_completed", task_id=task_id)

    except Exception as e:
        logger.error("evaluation_task_failed", task_id=task_id, error=str(e))


@router.post("/generate-testset")
async def generate_testset(request: GenerateTestsetRequest):
    """自动生成评估测试集"""
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()

    # 从数据库获取文档内容
    rows = await pool.fetch(
        """SELECT id, filename FROM documents 
           WHERE collection = $1 AND status = 'completed'
           LIMIT $2""",
        request.collection, request.max_docs,
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No completed documents in collection: {request.collection}",
        )

    # 获取文档的chunk内容
    doc_texts = []
    for row in rows:
        from src.infra.database.milvus_client import get_milvus
        milvus = get_milvus()
        from src.infra.config.settings import get_settings

        chunks = milvus.query(
            collection_name=get_settings().MILVUS_COLLECTION_NAME,
            filter=f'doc_id == "{row["id"]}"',
            output_fields=["content"],
            limit=20,
        )

        if chunks:
            doc_text = "\n\n".join([c["content"] for c in chunks])
            doc_texts.append(doc_text)

    # 生成测试集
    generator = TestsetGenerator()
    test_cases = await generator.generate_from_documents(
        documents=doc_texts,
        count_per_doc=request.count_per_doc,
    )

    return {
        "total": len(test_cases),
        "test_cases": [tc.model_dump() for tc in test_cases],
    }


@router.get("/reports")
async def list_evaluation_reports(
    page: int = 1,
    page_size: int = 20,
):
    """获取评估报告列表"""
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()
    offset = (page - 1) * page_size

    rows = await pool.fetch(
        """SELECT id, name, dataset_size, status, metrics, config, 
                  created_at, completed_at
           FROM evaluation_runs 
           ORDER BY created_at DESC
           LIMIT $1 OFFSET $2""",
        page_size, offset,
    )

    return [
        {
            "run_id": row["id"],
            "name": row["name"],
            "dataset_size": row["dataset_size"],
            "status": row["status"],
            "metrics": row["metrics"],
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]


@router.get("/reports/{run_id}")
async def get_evaluation_report(run_id: str):
    """获取评估报告详情"""
    from src.infra.database.postgres import get_postgres_pool

    pool = await get_postgres_pool()

    run = await pool.fetchrow(
        "SELECT * FROM evaluation_runs WHERE id = $1", run_id
    )
    if not run:
        raise HTTPException(status_code=404, detail="Report not found")

    samples = await pool.fetch(
        """SELECT question, ground_truth, generated_answer, contexts, metrics
           FROM evaluation_results WHERE run_id = $1""",
        run_id,
    )

    return {
        "run_id": run["id"],
        "name": run["name"],
        "dataset_size": run["dataset_size"],
        "status": run["status"],
        "avg_metrics": run["metrics"],
        "config": run["config"],
        "created_at": run["created_at"].isoformat(),
        "samples": [
            {
                "question": s["question"],
                "ground_truth": s["ground_truth"],
                "generated_answer": s["generated_answer"],
                "metrics": s["metrics"],
            }
            for s in samples
        ],
    }
```

------

## 七、Phase 2 配置增强

Python



```
# src/infra/config/settings.py  (新增字段)

class Settings(BaseSettings):
    # ... Phase 1 字段 ...

    # === Phase 2 新增 ===

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # Reranker
    RERANKER_ENABLED: bool = True
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    # 备选: 使用Cohere API
    # COHERE_API_KEY: str = ""
    # RERANKER_TYPE: str = "cross_encoder"  # cross_encoder / cohere / llm

    # 语义缓存
    SEMANTIC_CACHE_ENABLED: bool = True
    SEMANTIC_CACHE_THRESHOLD: float = 0.92  # 相似度阈值
    SEMANTIC_CACHE_TTL: int = 86400  # 24小时

    # 元数据提取
    METADATA_EXTRACTION_ENABLED: bool = True

    # LangFuse
    LANGFUSE_ENABLED: bool = False
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "http://localhost:3000"

    # 查询理解
    QUERY_REWRITING_ENABLED: bool = True

    # 混合检索权重
    DENSE_WEIGHT: float = 0.6
    SPARSE_WEIGHT: float = 0.4

    # 置信度评估
    CONFIDENCE_EVALUATION_MODE: str = "llm"  # simple / llm
```

------

## 八、Phase 2 验收标准

### 功能验收

| #    | 功能       | 验收标准                                       | 状态 |
| ---- | ---------- | ---------------------------------------------- | ---- |
| 1    | 查询改写   | 多轮对话中指代消解正确率 > 80%                 | ⬜    |
| 2    | 查询扩展   | 每个查询生成 2-3 个语义等价扩展查询            | ⬜    |
| 3    | 语义分块   | 长文档自动使用语义分块，分块边界合理           | ⬜    |
| 4    | BM25 检索  | ES 索引正确建立，BM25 检索可用                 | ⬜    |
| 5    | 混合检索   | Dense + Sparse 双路召回 + RRF 融合             | ⬜    |
| 6    | Rerank     | Cross-Encoder 重排，Top-5 结果质量提升         | ⬜    |
| 7    | 语义缓存   | 语义相似问题命中率 > 30%，命中延迟 < 100ms     | ⬜    |
| 8    | 置信度评估 | LLM 多维度评估，自动降级决策准确               | ⬜    |
| 9    | 幻觉检测   | 能识别回答中不被上下文支持的声明               | ⬜    |
| 10   | LangFuse   | 所有LLM调用可追踪，Token/延迟/成本可视化       | ⬜    |
| 11   | RAGAS 评估 | 可批量评估，输出 faithfulness/relevancy 等指标 | ⬜    |
| 12   | 测试集生成 | 从文档自动生成测试问答对                       | ⬜    |

### 质量基线（Phase 2 完成后建立）

| 指标              | 目标基线 | 说明                    |
| ----------------- | -------- | ----------------------- |
| Faithfulness      | ≥ 0.80   | 答案基于上下文的程度    |
| Answer Relevancy  | ≥ 0.75   | 回答切题程度            |
| Context Precision | ≥ 0.70   | 检索结果的精确度        |
| 缓存命中率        | ≥ 25%    | 重复/相似问题的缓存命中 |
| P95 延迟 (含缓存) | < 1s     | 缓存命中时的端到端延迟  |
| P95 延迟 (无缓存) | < 8s     | 完整RAG流程延迟         |

### 性能对比 (Phase 1 vs Phase 2)

| 指标         | Phase 1 | Phase 2 目标       | 提升幅度 |
| ------------ | ------- | ------------------ | -------- |
| 回答准确率   | ~70%    | ≥ 85%              | +15%     |
| 检索召回率   | ~60%    | ≥ 80%              | +20%     |
| 首次回答延迟 | ~4s     | ~5s (质量提升代价) | -        |
| 缓存命中延迟 | N/A     | < 100ms            | 新增     |
| 幻觉率       | 未检测  | < 10%              | 新增     |

------

## 九、Phase 2 → Phase 3 过渡预留

| 扩展点   | 预留位置                        | Phase 3 计划                                  |
| -------- | ------------------------------- | --------------------------------------------- |
| 人工审查 | quality_gate 已区分阈值         | 增加 `human_review` 节点 + `interrupt_before` |
| MCP 工具 | 图中可新增 `tool_agent` 节点    | 增加 MCP 客户端 + 工具注册中心                |
| 安全护栏 | 可在 query_understanding 后插入 | 输入检查 + 输出过滤                           |
| 多租户   | Milvus partition_key / ES index | 添加 tenant_id 过滤                           |
| 长期记忆 | MemoryManager 已预留接口        | 增加 PostgreSQL + Milvus 语义搜索             |
| 用户反馈 | user_feedback 表已创建          | 增加反馈API + 训练数据收集                    |
| 限流熔断 | 中间件层已预留                  | 增加 Redis-based 限流 + Circuit Breaker       |