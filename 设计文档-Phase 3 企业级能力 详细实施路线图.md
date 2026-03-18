# Phase 3 企业级能力 详细实施路线图

> **目标**: 构建完整的企业级能力，包括人工审查、MCP工具调用、安全护栏、长期记忆、多租户、认证鉴权、限流熔断、生产级监控
> **周期**: 3-4 周
> **前置依赖**: Phase 2 全部验收通过
> **交付物**: 可投入企业内部试运行的完整系统

------

## 一、Phase 3 任务分解总览

text



```
Phase 3 企业级能力 (3-4周)
│
├── Week 11: 人工审查 & 可中断/恢复对话
│   ├── 11.1 LangGraph interrupt/resume 机制
│   ├── 11.2 审查队列管理
│   ├── 11.3 审查 WebSocket 实时通知
│   ├── 11.4 审查管理后台 API
│   └── 11.5 审查统计与 SLA 监控
│
├── Week 12: MCP 工具调用 & 安全护栏
│   ├── 12.1 MCP 客户端集成
│   ├── 12.2 工具注册中心
│   ├── 12.3 Tool Agent 节点
│   ├── 12.4 意图路由增强 (知识问答/工具调用/闲聊)
│   ├── 12.5 输入安全护栏 (Prompt注入/敏感信息)
│   └── 12.6 输出安全护栏 (幻觉过滤/合规检查)
│
├── Week 13: 长期记忆 & 多租户 & 认证
│   ├── 13.1 长期记忆 (PostgreSQL + Milvus语义搜索)
│   ├── 13.2 记忆管理器升级 (四层融合)
│   ├── 13.3 多租户数据隔离
│   ├── 13.4 JWT 认证 & RBAC 鉴权
│   └── 13.5 用户反馈收集 API
│
└── Week 14: 限流熔断 & 生产监控 & 稳定化
    ├── 14.1 Redis-based 限流中间件
    ├── 14.2 熔断器 (Circuit Breaker)
    ├── 14.3 Prometheus 指标埋点
    ├── 14.4 Grafana 监控大盘
    ├── 14.5 告警规则配置
    └── 14.6 集成测试 & 压力测试 & 稳定化
```

------

## 二、新增/变更的目录结构

text



```
src/
├── api/
│   ├── middlewares/
│   │   ├── auth.py                    # [新增] JWT认证
│   │   ├── rate_limit.py              # [新增] 限流
│   │   ├── circuit_breaker.py         # [新增] 熔断
│   │   └── ...
│   └── routers/
│       ├── admin.py                   # [新增] 管理/审查接口
│       ├── feedback.py                # [新增] 反馈接口
│       ├── auth.py                    # [新增] 认证接口
│       ├── ws.py                      # [新增] WebSocket接口
│       └── ...
├── core/
│   ├── orchestrator/
│   │   ├── graph.py                   # [重构] 完整图(含审查/工具)
│   │   ├── state.py                   # [增强] 审查/工具/租户字段
│   │   ├── engine.py                  # [增强] 中断/恢复逻辑
│   │   └── nodes/
│   │       ├── human_review.py        # [新增] 人工审查节点
│   │       ├── tool_agent.py          # [新增] 工具调用节点
│   │       ├── intent_router.py       # [新增] 意图路由节点
│   │       ├── guardrails.py          # [新增] 安全护栏节点
│   │       └── ...
│   ├── memory/
│   │   ├── long_term.py              # [新增] 长期记忆
│   │   ├── manager.py                # [重构] 四层融合
│   │   └── ...
│   ├── tools/                         # [新增] 工具系统
│   │   ├── __init__.py
│   │   ├── mcp_client.py             # MCP客户端
│   │   ├── tool_registry.py          # 工具注册中心
│   │   └── builtin/                   # 内置工具
│   │       ├── __init__.py
│   │       ├── calculator.py
│   │       ├── datetime_tool.py
│   │       └── document_search.py
│   ├── guardrails/                    # [新增] 安全护栏
│   │   ├── __init__.py
│   │   ├── input_guard.py
│   │   ├── output_guard.py
│   │   └── rules.py
│   └── auth/                          # [新增] 认证模块
│       ├── __init__.py
│       ├── jwt_handler.py
│       ├── models.py
│       └── rbac.py
├── infra/
│   ├── monitoring/                    # [新增] 监控
│   │   ├── __init__.py
│   │   ├── metrics.py                 # Prometheus指标
│   │   └── health.py                  # 健康检查增强
│   └── websocket/                     # [新增] WebSocket
│       ├── __init__.py
│       └── manager.py
└── schemas/
    ├── auth.py                        # [新增]
    ├── admin.py                       # [新增]
    └── feedback.py                    # [新增]
```

### 新增依赖

toml



```
# pyproject.toml Phase 3 新增

# === MCP ===
langchain-mcp-adapters = "^0.1.0"
mcp = "^1.0.0"

# === 认证 ===
python-jose = { version = "^3.3.0", extras = ["cryptography"] }
passlib = { version = "^1.7.4", extras = ["bcrypt"] }

# === WebSocket ===
websockets = "^13.0"

# === 监控 ===
prometheus-client = "^0.21.0"
prometheus-fastapi-instrumentator = "^7.0.0"

# === 熔断 ===
pybreaker = "^1.2.0"

# === 安全 ===
bleach = "^6.1.0"
```

### Docker Compose 新增

YAML



```
# docker/docker-compose.yml Phase 3 新增

  # ============================================================
  # Prometheus - 指标采集
  # ============================================================
  prometheus:
    image: prom/prometheus:v2.54.0
    container_name: qa-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./configs/prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - qa-network

  # ============================================================
  # Grafana - 可视化大盘
  # ============================================================
  grafana:
    image: grafana/grafana:11.2.0
    container_name: qa-grafana
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_INSTALL_PLUGINS: grafana-clock-panel
    volumes:
      - ./configs/grafana/provisioning:/etc/grafana/provisioning
      - ./configs/grafana/dashboards:/var/lib/grafana/dashboards
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - qa-network

  # ============================================================
  # Alertmanager - 告警管理 (可选)
  # ============================================================
  alertmanager:
    image: prom/alertmanager:v0.27.0
    container_name: qa-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./configs/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    networks:
      - qa-network

volumes:
  prometheus_data:
  grafana_data:
```

SQL



```
-- docker/configs/postgres/03-phase3-init.sql

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(64) PRIMARY KEY,
    username        VARCHAR(128) UNIQUE NOT NULL,
    email           VARCHAR(256) UNIQUE NOT NULL,
    hashed_password VARCHAR(256) NOT NULL,
    display_name    VARCHAR(256),
    role            VARCHAR(32) DEFAULT 'user',  -- admin / reviewer / user
    tenant_id       VARCHAR(64) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_role ON users(role);

-- 租户表
CREATE TABLE IF NOT EXISTS tenants (
    id              VARCHAR(64) PRIMARY KEY,
    name            VARCHAR(256) NOT NULL,
    config          JSONB DEFAULT '{}',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 审查记录表
CREATE TABLE IF NOT EXISTS review_queue (
    id              VARCHAR(64) PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    tenant_id       VARCHAR(64) NOT NULL,
    -- 原始信息
    original_query  TEXT NOT NULL,
    generated_answer TEXT NOT NULL,
    confidence      FLOAT,
    quality_metrics  JSONB DEFAULT '{}',
    retrieved_docs   JSONB DEFAULT '[]',
    -- 审查结果
    status          VARCHAR(32) DEFAULT 'pending',  -- pending / assigned / approved / edited / rejected
    reviewer_id     VARCHAR(64),
    review_action   VARCHAR(32),    -- approve / edit / reject
    edited_answer   TEXT,
    review_comment  TEXT,
    -- 时间
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_at     TIMESTAMP WITH TIME ZONE,
    reviewed_at     TIMESTAMP WITH TIME ZONE,
    -- SLA
    priority        INTEGER DEFAULT 0,  -- 0=normal, 1=high, 2=urgent
    sla_deadline    TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_review_status ON review_queue(status);
CREATE INDEX idx_review_tenant ON review_queue(tenant_id);
CREATE INDEX idx_review_reviewer ON review_queue(reviewer_id);
CREATE INDEX idx_review_priority ON review_queue(priority DESC, created_at ASC);

-- 用户反馈表 (增强Phase 2版本)
CREATE TABLE IF NOT EXISTS user_feedback (
    id              BIGSERIAL PRIMARY KEY,
    session_id      VARCHAR(64) NOT NULL,
    message_id      BIGINT,
    user_id         VARCHAR(64),
    tenant_id       VARCHAR(64),
    feedback_type   VARCHAR(16) NOT NULL,  -- thumbs_up / thumbs_down
    feedback_tags   VARCHAR(256)[],        -- ["inaccurate", "incomplete", "irrelevant"]
    comment         TEXT,
    -- 用于分析的元数据
    query           TEXT,
    answer          TEXT,
    confidence      FLOAT,
    was_fallback    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_session ON user_feedback(session_id);
CREATE INDEX idx_feedback_tenant ON user_feedback(tenant_id);
CREATE INDEX idx_feedback_type ON user_feedback(feedback_type);

-- 更新conversation表增加tenant_id
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64);
ALTER TABLE conversation_sessions ADD COLUMN IF NOT EXISTS user_id_ref VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_sessions_tenant ON conversation_sessions(tenant_id);

-- 更新documents表增加tenant_id
ALTER TABLE documents ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id);
```

------

## 三、Week 11：人工审查 & 可中断/恢复对话

### 11.1 状态定义增强

Python



```
# src/core/orchestrator/state.py  (Phase 3 完整版)

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class HumanReviewResult(BaseModel):
    """人工审查结果"""
    action: Literal["approve", "edit", "reject"]
    edited_answer: str | None = None
    comment: str = ""
    reviewer_id: str = ""


class ToolCallRecord(BaseModel):
    """工具调用记录"""
    tool_name: str
    tool_input: dict
    tool_output: str
    success: bool = True
    latency_ms: float = 0


class ConversationState(TypedDict):
    """LangGraph 对话状态 - Phase 3 完整版"""

    # === LangGraph 消息列表 ===
    messages: Annotated[list[BaseMessage], add_messages]

    # === 会话信息 ===
    session_id: str
    user_id: str
    tenant_id: str
    collection: str

    # === 查询理解 ===
    original_query: str
    rewritten_query: str
    expanded_queries: list[str]
    intent: str   # knowledge_qa / tool_call / chitchat / unclear

    # === 安全护栏 ===
    input_safe: bool
    input_guard_message: str   # 如果不安全, 存储拒绝原因
    output_safe: bool
    output_guard_message: str

    # === RAG ===
    retrieved_chunks: list[dict]
    context_text: str

    # === 工具调用 ===
    tool_calls: list[dict]
    tool_results: list[dict]

    # === 答案 ===
    answer: str
    citations: list[dict]
    confidence: float
    quality_metrics: dict
    model_used: str
    tokens_used: int

    # === 人工审查 ===
    needs_human_review: bool
    review_reason: str
    human_review_result: dict | None   # HumanReviewResult

    # === 控制 ===
    fallback_used: bool
    cache_hit: bool
    error: str | None
```

### 11.2 人工审查节点

Python



```
# src/core/orchestrator/nodes/human_review.py

import uuid
import json
from datetime import datetime, timedelta
import structlog

from langgraph.types import interrupt
from src.core.orchestrator.state import ConversationState

logger = structlog.get_logger()


class HumanReviewNode:
    """
    人工审查节点

    当回答质量不满足阈值时触发:
    1. 将审查请求写入队列 (PostgreSQL)
    2. 通过 WebSocket 实时通知审查员
    3. 调用 LangGraph interrupt() 中断图执行
    4. 等待审查员通过 API 提交结果
    5. 图自动恢复执行
    """

    def __init__(self, pg_pool, ws_manager=None):
        self.pg_pool = pg_pool
        self.ws_manager = ws_manager

    async def __call__(self, state: ConversationState) -> dict:
        """执行人工审查"""

        review_id = f"review_{uuid.uuid4().hex[:12]}"

        # 1. 构建审查请求
        review_request = {
            "review_id": review_id,
            "session_id": state["session_id"],
            "tenant_id": state.get("tenant_id", "default"),
            "original_query": state["original_query"],
            "generated_answer": state.get("answer", ""),
            "confidence": state.get("confidence", 0),
            "quality_metrics": state.get("quality_metrics", {}),
            "review_reason": state.get("review_reason", "low_confidence"),
            "retrieved_docs": [
                {
                    "content": c.get("content", "")[:500],
                    "doc_title": c.get("doc_title", ""),
                    "score": c.get("score", 0),
                }
                for c in state.get("retrieved_chunks", [])[:5]
            ],
        }

        # 2. 写入审查队列
        await self._create_review_record(review_request)

        # 3. WebSocket通知审查员
        if self.ws_manager:
            await self.ws_manager.notify_reviewers(
                tenant_id=state.get("tenant_id", "default"),
                data={
                    "event": "new_review",
                    "review_id": review_id,
                    "session_id": state["session_id"],
                    "query": state["original_query"][:200],
                    "confidence": state.get("confidence", 0),
                    "priority": self._calculate_priority(state),
                },
            )

        logger.info(
            "human_review_requested",
            review_id=review_id,
            session_id=state["session_id"],
            confidence=state.get("confidence", 0),
            reason=state.get("review_reason", ""),
        )

        # 4. ⚡ 中断图执行! 等待人工审查结果
        #    interrupt() 会:
        #    - 将当前state序列化到PostgreSQL checkpoint
        #    - 暂停图执行
        #    - 返回给调用方一个"等待中"的状态
        #
        #    当审查员提交结果后, 外部调用 graph.aupdate_state() + graph.ainvoke(None)
        #    图会从这里恢复, human_review_result 包含审查结果

        human_review_result = interrupt(review_request)

        # === 以下代码在 resume 后才执行 ===

        logger.info(
            "human_review_completed",
            review_id=review_id,
            session_id=state["session_id"],
            action=human_review_result.get("action", "unknown"),
        )

        # 5. 更新审查记录
        await self._update_review_record(
            review_id=review_id,
            result=human_review_result,
        )

        # 6. 根据审查结果决定返回内容
        action = human_review_result.get("action", "approve")

        if action == "approve":
            return {
                "needs_human_review": False,
                "human_review_result": human_review_result,
            }

        elif action == "edit":
            edited_answer = human_review_result.get("edited_answer", state.get("answer", ""))
            return {
                "answer": edited_answer,
                "needs_human_review": False,
                "human_review_result": human_review_result,
                "model_used": "human_edited",
            }

        elif action == "reject":
            return {
                "answer": "",
                "needs_human_review": False,
                "human_review_result": human_review_result,
                "fallback_used": True,  # 标记需要降级
            }

        return {"needs_human_review": False, "human_review_result": human_review_result}

    async def _create_review_record(self, review_request: dict):
        """写入审查队列"""
        priority = 0
        if review_request.get("confidence", 1) < 0.3:
            priority = 2  # urgent
        elif review_request.get("confidence", 1) < 0.5:
            priority = 1  # high

        sla_hours = {0: 24, 1: 4, 2: 1}
        sla_deadline = datetime.utcnow() + timedelta(hours=sla_hours.get(priority, 24))

        await self.pg_pool.execute(
            """INSERT INTO review_queue 
               (id, session_id, tenant_id, original_query, generated_answer,
                confidence, quality_metrics, retrieved_docs, priority, sla_deadline)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            review_request["review_id"],
            review_request["session_id"],
            review_request.get("tenant_id", "default"),
            review_request["original_query"],
            review_request["generated_answer"],
            review_request.get("confidence", 0),
            json.dumps(review_request.get("quality_metrics", {})),
            json.dumps(review_request.get("retrieved_docs", [])),
            priority,
            sla_deadline,
        )

    async def _update_review_record(self, review_id: str, result: dict):
        """更新审查记录"""
        await self.pg_pool.execute(
            """UPDATE review_queue SET 
               status = $1, review_action = $2, edited_answer = $3,
               review_comment = $4, reviewer_id = $5, reviewed_at = NOW()
               WHERE id = $6""",
            "completed",
            result.get("action", "approve"),
            result.get("edited_answer"),
            result.get("comment", ""),
            result.get("reviewer_id", ""),
            review_id,
        )

    def _calculate_priority(self, state: ConversationState) -> int:
        """计算审查优先级"""
        confidence = state.get("confidence", 1)
        if confidence < 0.3:
            return 2  # urgent
        elif confidence < 0.5:
            return 1  # high
        return 0  # normal
```

### 11.3 编排引擎中断/恢复逻辑

Python



```
# src/core/orchestrator/engine.py  (Phase 3 中断/恢复增强)

class ConversationOrchestrator:
    """Phase 3: 完整的中断/恢复支持"""

    def __init__(
        self,
        compiled_graph,
        memory_manager,
        cache_manager,
        llm_tracer,
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
        user_id: str = "default",
        tenant_id: str = "default",
        collection: str = "default",
    ) -> OrchestratorResult:
        """执行对话 (可能在human_review节点中断)"""
        start_time = time.perf_counter()

        history = await self.memory.load_context(
            user_id=user_id,
            session_id=session_id,
            current_query=message,
        )

        initial_messages = self._build_initial_messages(history, message)

        initial_state = {
            "messages": initial_messages,
            "session_id": session_id,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "collection": collection,
            "original_query": message,
            "rewritten_query": "",
            "expanded_queries": [],
            "intent": "knowledge_qa",
            "input_safe": True,
            "input_guard_message": "",
            "output_safe": True,
            "output_guard_message": "",
            "retrieved_chunks": [],
            "context_text": "",
            "tool_calls": [],
            "tool_results": [],
            "answer": "",
            "citations": [],
            "confidence": 0.0,
            "quality_metrics": {},
            "model_used": "",
            "tokens_used": 0,
            "needs_human_review": False,
            "review_reason": "",
            "human_review_result": None,
            "fallback_used": False,
            "cache_hit": False,
            "error": None,
        }

        thread_config = {
            "configurable": {
                "thread_id": session_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
            }
        }

        langfuse_callback = self.tracer.get_langchain_callback(session_id, user_id)
        if langfuse_callback:
            thread_config["callbacks"] = [langfuse_callback]

        try:
            result_state = await self.graph.ainvoke(
                initial_state, config=thread_config,
            )
        except Exception as e:
            logger.exception("graph_execution_error", session_id=session_id)
            return OrchestratorResult(
                answer="抱歉，处理您的问题时出现了错误，请稍后重试。",
                status="error",
            )

        # ============================================================
        # 检查是否被中断 (等待人工审查)
        # ============================================================
        graph_state = await self.graph.aget_state(thread_config)

        if graph_state.next:
            # 有待执行的节点 = 被中断了
            interrupted_node = graph_state.next[0] if graph_state.next else "unknown"

            logger.info(
                "conversation_interrupted",
                session_id=session_id,
                interrupted_at=interrupted_node,
            )

            # 给用户返回"等待审查"的提示
            return OrchestratorResult(
                answer="您的问题正在等待人工审查确认，审查完成后将自动回复您。",
                status="waiting_review",
                session_id=session_id,
                confidence=result_state.get("confidence", 0),
                metadata={
                    "interrupted_at": interrupted_node,
                    "review_reason": result_state.get("review_reason", ""),
                },
            )

        # ============================================================
        # 正常完成
        # ============================================================
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # 保存记忆 + 缓存 + 持久化
        await self._post_process(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            message=message,
            result_state=result_state,
        )

        return OrchestratorResult(
            answer=result_state["answer"],
            citations=[CitationItem(**c) for c in result_state.get("citations", [])],
            confidence=result_state.get("confidence", 0),
            model_used=result_state.get("model_used", ""),
            fallback_used=result_state.get("fallback_used", False),
            tokens_used=result_state.get("tokens_used", 0),
            status="completed",
            session_id=session_id,
            latency_ms=elapsed_ms,
        )

    async def resume(
        self,
        session_id: str,
        review_result: dict,
        reviewer_id: str,
    ) -> OrchestratorResult:
        """
        恢复被中断的对话

        在人工审查完成后调用:
        1. 将审查结果注入到图的状态中
        2. 从中断点继续执行
        """
        thread_config = {
            "configurable": {"thread_id": session_id}
        }

        # 1. 检查当前状态
        current_state = await self.graph.aget_state(thread_config)
        if not current_state.next:
            raise ValueError(f"Session {session_id} is not in interrupted state")

        logger.info(
            "conversation_resuming",
            session_id=session_id,
            reviewer_id=reviewer_id,
            action=review_result.get("action"),
        )

        # 2. 注入审查结果到图状态
        review_data = {
            **review_result,
            "reviewer_id": reviewer_id,
        }

        await self.graph.aupdate_state(
            thread_config,
            values={"human_review_result": review_data},
            as_node="human_review",  # 以human_review节点的身份更新
        )

        # 3. 从中断点恢复执行
        try:
            result_state = await self.graph.ainvoke(
                None,  # None = 从checkpoint恢复
                config=thread_config,
            )
        except Exception as e:
            logger.exception("resume_execution_error", session_id=session_id)
            return OrchestratorResult(
                answer="审查完成，但处理过程出现错误。",
                status="error",
            )

        # 4. 后置处理
        state_values = current_state.values
        await self._post_process(
            session_id=session_id,
            user_id=state_values.get("user_id", "default"),
            tenant_id=state_values.get("tenant_id", "default"),
            message=state_values.get("original_query", ""),
            result_state=result_state,
        )

        logger.info(
            "conversation_resumed_completed",
            session_id=session_id,
            action=review_result.get("action"),
        )

        return OrchestratorResult(
            answer=result_state["answer"],
            citations=[CitationItem(**c) for c in result_state.get("citations", [])],
            confidence=result_state.get("confidence", 0),
            model_used=result_state.get("model_used", ""),
            status="completed",
            session_id=session_id,
        )

    async def get_session_status(self, session_id: str) -> dict:
        """获取会话状态"""
        thread_config = {"configurable": {"thread_id": session_id}}

        try:
            state = await self.graph.aget_state(thread_config)

            if state.next:
                return {
                    "session_id": session_id,
                    "status": "waiting_review",
                    "interrupted_at": state.next[0] if state.next else None,
                    "values": {
                        "original_query": state.values.get("original_query", ""),
                        "confidence": state.values.get("confidence", 0),
                    },
                }
            else:
                return {
                    "session_id": session_id,
                    "status": "completed" if state.values else "not_found",
                }
        except Exception:
            return {"session_id": session_id, "status": "not_found"}

    async def _post_process(self, session_id, user_id, tenant_id, message, result_state):
        """后置处理: 记忆 + 缓存 + 持久化"""
        if not result_state.get("cache_hit"):
            await self.memory.save_turn(
                user_id=user_id,
                session_id=session_id,
                user_message=message,
                assistant_message=result_state.get("answer", ""),
            )

            if result_state.get("confidence", 0) >= 0.5:
                citations = [CitationItem(**c) for c in result_state.get("citations", [])]
                await self.cache.set(
                    query=result_state.get("rewritten_query") or message,
                    answer=result_state["answer"],
                    collection=result_state.get("collection", "default"),
                    citations=citations,
                    confidence=result_state["confidence"],
                )

        await self._save_to_db(session_id, user_id, tenant_id, message, result_state)
```

### 11.4 审查管理 API

Python



```
# src/api/routers/admin.py

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import structlog

from src.core.auth.jwt_handler import get_current_user, require_role
from src.core.auth.models import User
from src.api.dependencies import get_orchestrator

logger = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["Admin"])


class ReviewItem(BaseModel):
    """审查项"""
    review_id: str
    session_id: str
    original_query: str
    generated_answer: str
    confidence: float
    quality_metrics: dict
    retrieved_docs: list[dict]
    status: str
    priority: int
    review_reason: str = ""
    created_at: str
    sla_deadline: str | None = None


class SubmitReviewRequest(BaseModel):
    """提交审查结果"""
    action: str = Field(..., pattern="^(approve|edit|reject)$")
    edited_answer: str | None = None
    comment: str = ""


class ReviewStats(BaseModel):
    """审查统计"""
    total_pending: int
    total_completed_today: int
    avg_review_time_minutes: float
    sla_breach_count: int
    approval_rate: float
    edit_rate: float
    rejection_rate: float


# ============================================================
# 审查队列管理
# ============================================================

@router.get("/reviews", response_model=list[ReviewItem])
async def list_pending_reviews(
    status: str = Query("pending", pattern="^(pending|assigned|all)$"),
    priority: int | None = None,
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(require_role(["admin", "reviewer"])),
):
    """获取待审查列表"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    conditions = ["tenant_id = $1"]
    params = [user.tenant_id]
    param_idx = 2

    if status != "all":
        conditions.append(f"status = ${param_idx}")
        params.append(status)
        param_idx += 1

    if priority is not None:
        conditions.append(f"priority = ${param_idx}")
        params.append(priority)
        param_idx += 1

    where_clause = " AND ".join(conditions)
    offset = (page - 1) * page_size

    rows = await pool.fetch(
        f"""SELECT * FROM review_queue 
            WHERE {where_clause}
            ORDER BY priority DESC, created_at ASC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}""",
        *params, page_size, offset,
    )

    return [
        ReviewItem(
            review_id=row["id"],
            session_id=row["session_id"],
            original_query=row["original_query"],
            generated_answer=row["generated_answer"],
            confidence=row["confidence"] or 0,
            quality_metrics=row["quality_metrics"] or {},
            retrieved_docs=row["retrieved_docs"] or [],
            status=row["status"],
            priority=row["priority"] or 0,
            created_at=row["created_at"].isoformat(),
            sla_deadline=row["sla_deadline"].isoformat() if row["sla_deadline"] else None,
        )
        for row in rows
    ]


@router.post("/reviews/{review_id}/assign")
async def assign_review(
    review_id: str,
    user: User = Depends(require_role(["admin", "reviewer"])),
):
    """分配审查任务给当前用户"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    result = await pool.execute(
        """UPDATE review_queue 
           SET status = 'assigned', reviewer_id = $1, assigned_at = NOW()
           WHERE id = $2 AND status = 'pending' AND tenant_id = $3""",
        user.id, review_id, user.tenant_id,
    )

    if result == "UPDATE 0":
        raise HTTPException(404, "Review not found or already assigned")

    return {"message": "Review assigned", "review_id": review_id, "reviewer": user.id}


@router.post("/reviews/{review_id}/submit")
async def submit_review(
    review_id: str,
    request: SubmitReviewRequest,
    user: User = Depends(require_role(["admin", "reviewer"])),
    orchestrator=Depends(get_orchestrator),
):
    """
    提交审查结果

    这会:
    1. 更新审查记录
    2. 恢复被中断的对话图
    3. 将最终回答返回给用户
    """
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    # 获取审查记录
    review = await pool.fetchrow(
        "SELECT * FROM review_queue WHERE id = $1 AND tenant_id = $2",
        review_id, user.tenant_id,
    )
    if not review:
        raise HTTPException(404, "Review not found")

    if review["status"] not in ("pending", "assigned"):
        raise HTTPException(400, "Review already completed")

    session_id = review["session_id"]

    # 恢复对话
    review_result = {
        "action": request.action,
        "edited_answer": request.edited_answer,
        "comment": request.comment,
        "reviewer_id": user.id,
    }

    try:
        result = await orchestrator.resume(
            session_id=session_id,
            review_result=review_result,
            reviewer_id=user.id,
        )

        logger.info(
            "review_submitted_and_resumed",
            review_id=review_id,
            session_id=session_id,
            action=request.action,
            reviewer=user.id,
        )

        # 通知用户审查完成 (WebSocket)
        from src.infra.websocket.manager import get_ws_manager
        ws = get_ws_manager()
        if ws:
            await ws.notify_user(
                session_id=session_id,
                data={
                    "event": "review_completed",
                    "session_id": session_id,
                    "answer": result.answer,
                    "action": request.action,
                },
            )

        return {
            "message": "Review submitted and conversation resumed",
            "review_id": review_id,
            "session_id": session_id,
            "final_answer": result.answer,
        }

    except Exception as e:
        logger.error(
            "review_resume_failed",
            review_id=review_id,
            error=str(e),
        )
        raise HTTPException(500, f"Failed to resume conversation: {str(e)}")


@router.get("/reviews/stats", response_model=ReviewStats)
async def get_review_stats(
    user: User = Depends(require_role(["admin"])),
):
    """获取审查统计"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()
    tenant_id = user.tenant_id

    pending = await pool.fetchval(
        "SELECT COUNT(*) FROM review_queue WHERE status = 'pending' AND tenant_id = $1",
        tenant_id,
    )

    today_completed = await pool.fetchval(
        """SELECT COUNT(*) FROM review_queue 
           WHERE status = 'completed' AND tenant_id = $1
           AND reviewed_at >= CURRENT_DATE""",
        tenant_id,
    )

    avg_time = await pool.fetchval(
        """SELECT EXTRACT(EPOCH FROM AVG(reviewed_at - created_at)) / 60
           FROM review_queue
           WHERE status = 'completed' AND tenant_id = $1
           AND reviewed_at >= CURRENT_DATE - INTERVAL '7 days'""",
        tenant_id,
    ) or 0

    sla_breached = await pool.fetchval(
        """SELECT COUNT(*) FROM review_queue
           WHERE status = 'pending' AND tenant_id = $1
           AND sla_deadline < NOW()""",
        tenant_id,
    )

    total_completed = await pool.fetchval(
        """SELECT COUNT(*) FROM review_queue
           WHERE status = 'completed' AND tenant_id = $1
           AND reviewed_at >= CURRENT_DATE - INTERVAL '30 days'""",
        tenant_id,
    ) or 1

    approved = await pool.fetchval(
        """SELECT COUNT(*) FROM review_queue
           WHERE review_action = 'approve' AND tenant_id = $1
           AND reviewed_at >= CURRENT_DATE - INTERVAL '30 days'""",
        tenant_id,
    ) or 0

    edited = await pool.fetchval(
        """SELECT COUNT(*) FROM review_queue
           WHERE review_action = 'edit' AND tenant_id = $1
           AND reviewed_at >= CURRENT_DATE - INTERVAL '30 days'""",
        tenant_id,
    ) or 0

    rejected = await pool.fetchval(
        """SELECT COUNT(*) FROM review_queue
           WHERE review_action = 'reject' AND tenant_id = $1
           AND reviewed_at >= CURRENT_DATE - INTERVAL '30 days'""",
        tenant_id,
    ) or 0

    return ReviewStats(
        total_pending=pending,
        total_completed_today=today_completed,
        avg_review_time_minutes=round(float(avg_time), 1),
        sla_breach_count=sla_breached,
        approval_rate=round(approved / total_completed, 3),
        edit_rate=round(edited / total_completed, 3),
        rejection_rate=round(rejected / total_completed, 3),
    )
```

### 11.5 WebSocket 实时通知

Python



```
# src/infra/websocket/manager.py

import json
import asyncio
from collections import defaultdict
import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger()

_ws_manager: "WebSocketManager | None" = None


class WebSocketManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # 按角色和租户分组的活跃连接
        self._reviewer_connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._user_connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def connect_reviewer(self, websocket: WebSocket, tenant_id: str):
        """审查员连接"""
        await websocket.accept()
        async with self._lock:
            self._reviewer_connections[tenant_id].append(websocket)
        logger.info("reviewer_ws_connected", tenant_id=tenant_id)

    async def connect_user(self, websocket: WebSocket, session_id: str):
        """用户连接 (按session_id)"""
        await websocket.accept()
        async with self._lock:
            self._user_connections[session_id].append(websocket)
        logger.info("user_ws_connected", session_id=session_id)

    async def disconnect_reviewer(self, websocket: WebSocket, tenant_id: str):
        """审查员断开"""
        async with self._lock:
            if websocket in self._reviewer_connections[tenant_id]:
                self._reviewer_connections[tenant_id].remove(websocket)

    async def disconnect_user(self, websocket: WebSocket, session_id: str):
        """用户断开"""
        async with self._lock:
            if websocket in self._user_connections[session_id]:
                self._user_connections[session_id].remove(websocket)

    async def notify_reviewers(self, tenant_id: str, data: dict):
        """通知该租户的所有审查员"""
        connections = self._reviewer_connections.get(tenant_id, [])
        message = json.dumps(data, ensure_ascii=False)

        disconnected = []
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)

        # 清理断开的连接
        for ws in disconnected:
            await self.disconnect_reviewer(ws, tenant_id)

    async def notify_user(self, session_id: str, data: dict):
        """通知特定会话的用户"""
        connections = self._user_connections.get(session_id, [])
        message = json.dumps(data, ensure_ascii=False)

        disconnected = []
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            await self.disconnect_user(ws, session_id)


def get_ws_manager() -> WebSocketManager | None:
    return _ws_manager


def init_ws_manager() -> WebSocketManager:
    global _ws_manager
    _ws_manager = WebSocketManager()
    return _ws_manager
```

Python



```
# src/api/routers/ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from src.infra.websocket.manager import get_ws_manager
import structlog

logger = structlog.get_logger()
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/reviewer")
async def reviewer_websocket(
    websocket: WebSocket,
    tenant_id: str = Query(...),
    token: str = Query(...),
):
    """审查员 WebSocket 端点"""
    # 验证token
    from src.core.auth.jwt_handler import verify_token
    try:
        user = verify_token(token)
        if user.role not in ("admin", "reviewer"):
            await websocket.close(code=4003, reason="Insufficient permissions")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    ws_manager = get_ws_manager()
    await ws_manager.connect_reviewer(websocket, tenant_id)

    try:
        while True:
            # 保持连接, 接收心跳
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect_reviewer(websocket, tenant_id)
        logger.info("reviewer_ws_disconnected", tenant_id=tenant_id)


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """用户对话 WebSocket 端点 (接收审查完成通知)"""
    ws_manager = get_ws_manager()
    await ws_manager.connect_user(websocket, session_id)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect_user(websocket, session_id)
```

------

## 四、Week 12：MCP 工具调用 & 安全护栏

### 12.1 MCP 客户端

Python



```
# src/core/tools/mcp_client.py

import asyncio
import structlog
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class MCPServerConfig:
    """MCP Server 配置"""
    def __init__(self, name: str, transport: str, **kwargs):
        self.name = name
        self.transport = transport  # stdio / sse
        self.params = kwargs


class MCPClientManager:
    """
    MCP 客户端管理器

    管理多个 MCP Server 连接, 提供统一的工具调用接口
    """

    def __init__(self):
        self._sessions: dict[str, ClientSession] = {}
        self._tools: dict[str, dict] = {}  # tool_name -> {server, schema}

    async def connect_server(self, config: MCPServerConfig):
        """连接一个 MCP Server"""
        try:
            if config.transport == "stdio":
                server_params = StdioServerParameters(
                    command=config.params["command"],
                    args=config.params.get("args", []),
                    env=config.params.get("env"),
                )
                read_stream, write_stream = await stdio_client(server_params).__aenter__()
                session = ClientSession(read_stream, write_stream)

            elif config.transport == "sse":
                read_stream, write_stream = await sse_client(
                    url=config.params["url"],
                ).__aenter__()
                session = ClientSession(read_stream, write_stream)

            else:
                raise ValueError(f"Unsupported transport: {config.transport}")

            await session.initialize()
            self._sessions[config.name] = session

            # 发现该Server提供的工具
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                self._tools[tool.name] = {
                    "server": config.name,
                    "schema": tool.inputSchema,
                    "description": tool.description or "",
                }

            logger.info(
                "mcp_server_connected",
                server=config.name,
                transport=config.transport,
                tools=[t.name for t in tools_response.tools],
            )

        except Exception as e:
            logger.error(
                "mcp_server_connection_failed",
                server=config.name,
                error=str(e),
            )
            raise

    async def call_tool(
        self, tool_name: str, arguments: dict, timeout: float = 30
    ) -> str:
        """调用MCP工具"""
        if tool_name not in self._tools:
            raise ValueError(f"Tool not found: {tool_name}")

        tool_info = self._tools[tool_name]
        server_name = tool_info["server"]
        session = self._sessions.get(server_name)

        if not session:
            raise RuntimeError(f"MCP server not connected: {server_name}")

        try:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments=arguments),
                timeout=timeout,
            )

            # 提取文本内容
            output_parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    output_parts.append(content.text)

            output = "\n".join(output_parts) if output_parts else str(result.content)

            logger.info(
                "mcp_tool_called",
                tool=tool_name,
                server=server_name,
                output_length=len(output),
            )

            return output

        except asyncio.TimeoutError:
            logger.error("mcp_tool_timeout", tool=tool_name, timeout=timeout)
            raise
        except Exception as e:
            logger.error("mcp_tool_call_failed", tool=tool_name, error=str(e))
            raise

    def get_available_tools(self) -> list[dict]:
        """获取所有可用工具的描述"""
        return [
            {
                "name": name,
                "description": info["description"],
                "parameters": info["schema"],
                "server": info["server"],
            }
            for name, info in self._tools.items()
        ]

    async def close_all(self):
        """关闭所有MCP连接"""
        for name, session in self._sessions.items():
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
        self._sessions.clear()
        self._tools.clear()
```

### 12.2 工具注册中心

Python



```
# src/core/tools/tool_registry.py

import structlog
from langchain_core.tools import tool, BaseTool, StructuredTool
from pydantic import BaseModel, Field

from src.core.tools.mcp_client import MCPClientManager

logger = structlog.get_logger()


class ToolRegistry:
    """
    工具注册中心

    统一管理:
    1. MCP外部工具 (数据库查询/搜索/API等)
    2. 内置工具 (计算器/日期/文档搜索等)
    """

    def __init__(self, mcp_client: MCPClientManager | None = None):
        self.mcp_client = mcp_client
        self._builtin_tools: list[BaseTool] = []
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """注册内置工具"""

        @tool
        def calculator(expression: str) -> str:
            """
            安全的数学计算器。
            输入数学表达式，返回计算结果。
            例如: "2 + 3 * 4", "(100 - 20) / 4"
            """
            import ast
            import operator

            operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.Mod: operator.mod,
            }

            def eval_node(node):
                if isinstance(node, ast.Constant):
                    return node.value
                elif isinstance(node, ast.BinOp):
                    left = eval_node(node.left)
                    right = eval_node(node.right)
                    op = operators.get(type(node.op))
                    if op:
                        return op(left, right)
                elif isinstance(node, ast.UnaryOp):
                    if isinstance(node.op, ast.USub):
                        return -eval_node(node.operand)
                raise ValueError(f"Unsupported expression")

            try:
                tree = ast.parse(expression, mode='eval')
                result = eval_node(tree.body)
                return f"计算结果: {result}"
            except Exception as e:
                return f"计算错误: {str(e)}"

        @tool
        def get_current_datetime(timezone: str = "Asia/Shanghai") -> str:
            """
            获取当前日期和时间。
            可指定时区，默认为北京时间。
            """
            from datetime import datetime
            import zoneinfo

            try:
                tz = zoneinfo.ZoneInfo(timezone)
                now = datetime.now(tz)
                return f"当前时间 ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S')}"
            except Exception as e:
                return f"获取时间失败: {str(e)}"

        self._builtin_tools = [calculator, get_current_datetime]

    def get_all_tools(self) -> list[BaseTool]:
        """获取所有可用工具 (内置 + MCP)"""
        tools = list(self._builtin_tools)

        # 将MCP工具包装为LangChain Tool
        if self.mcp_client:
            for mcp_tool in self.mcp_client.get_available_tools():
                lc_tool = self._wrap_mcp_tool(mcp_tool)
                tools.append(lc_tool)

        return tools

    def get_tool_descriptions(self) -> str:
        """获取工具描述文本 (用于LLM提示)"""
        descriptions = []
        for tool in self.get_all_tools():
            descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(descriptions)

    def _wrap_mcp_tool(self, mcp_tool: dict) -> BaseTool:
        """将MCP工具包装为LangChain BaseTool"""
        mcp_client = self.mcp_client
        tool_name = mcp_tool["name"]

        async def _call_mcp(**kwargs) -> str:
            return await mcp_client.call_tool(tool_name, kwargs)

        return StructuredTool.from_function(
            func=lambda **kwargs: None,  # sync placeholder
            coroutine=_call_mcp,
            name=tool_name,
            description=mcp_tool["description"],
            args_schema=self._build_args_schema(mcp_tool["parameters"]),
        )

    def _build_args_schema(self, json_schema: dict):
        """从JSON Schema构建Pydantic模型"""
        # 简化处理: 动态创建Pydantic模型
        from pydantic import create_model

        fields = {}
        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])

        type_map = {
            "string": (str, ...),
            "integer": (int, ...),
            "number": (float, ...),
            "boolean": (bool, ...),
        }

        for name, prop in properties.items():
            prop_type = prop.get("type", "string")
            default = ... if name in required else None
            python_type = type_map.get(prop_type, (str, ...))[0]
            fields[name] = (python_type, default)

        return create_model("MCPToolArgs", **fields) if fields else None
```

### 12.3 Tool Agent 节点

Python



```
# src/core/orchestrator/nodes/tool_agent.py

import json
import time
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from src.core.orchestrator.state import ConversationState
from src.core.tools.tool_registry import ToolRegistry
from src.infra.config.settings import get_settings

logger = structlog.get_logger()

TOOL_AGENT_PROMPT = """你是一个智能助手，可以使用以下工具来帮助回答用户的问题。

可用工具:
{tool_descriptions}

使用规则:
1. 只在需要时使用工具，不要为了使用而使用
2. 可以多次调用工具获取所需信息
3. 获得工具结果后，结合结果生成最终回答
4. 如果工具调用失败，告知用户并尝试其他方式回答

请根据用户问题决定是否需要调用工具。"""


class ToolAgentNode:
    """
    工具调用 Agent 节点

    支持:
    1. 自动决定是否调用工具
    2. 多步工具调用 (ReAct模式)
    3. 工具结果整合
    4. MCP + 内置工具
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry
        settings = get_settings()
        self.llm = ChatOpenAI(
            model=settings.PRIMARY_LLM_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_API_BASE,
        ).bind_tools(tool_registry.get_all_tools())

    async def __call__(self, state: ConversationState) -> dict:
        """执行工具调用"""
        query = state.get("rewritten_query") or state["original_query"]

        logger.info(
            "tool_agent_start",
            session_id=state["session_id"],
            query=query[:100],
        )

        tool_descriptions = self.registry.get_tool_descriptions()

        messages = [
            SystemMessage(content=TOOL_AGENT_PROMPT.format(
                tool_descriptions=tool_descriptions,
            )),
        ]

        # 加入对话历史
        for msg in state.get("messages", [])[-6:]:
            messages.append(msg)

        messages.append(HumanMessage(content=query))

        # ReAct循环: LLM决策 → 工具调用 → 结果反馈 → 继续或结束
        tool_call_records = []
        max_iterations = 5

        for iteration in range(max_iterations):
            response = await self.llm.ainvoke(messages)
            messages.append(response)

            # 检查是否有工具调用
            if not response.tool_calls:
                # 没有工具调用, LLM直接回答
                break

            # 执行工具调用
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                start_time = time.perf_counter()

                try:
                    # 从注册中心找到工具并执行
                    tools = {t.name: t for t in self.registry.get_all_tools()}
                    tool = tools.get(tool_name)

                    if not tool:
                        result = f"工具 '{tool_name}' 不存在"
                        success = False
                    else:
                        result = await tool.ainvoke(tool_args)
                        success = True

                except Exception as e:
                    result = f"工具调用失败: {str(e)}"
                    success = False

                elapsed_ms = (time.perf_counter() - start_time) * 1000

                tool_call_records.append({
                    "tool_name": tool_name,
                    "tool_input": tool_args,
                    "tool_output": str(result)[:1000],
                    "success": success,
                    "latency_ms": round(elapsed_ms, 2),
                })

                # 将工具结果反馈给LLM
                messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                    )
                )

                logger.info(
                    "tool_called",
                    tool=tool_name,
                    success=success,
                    latency_ms=round(elapsed_ms, 2),
                )

        # 最终答案是最后一条AI消息
        final_answer = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                final_answer = msg.content
                break

        logger.info(
            "tool_agent_completed",
            session_id=state["session_id"],
            num_tool_calls=len(tool_call_records),
            answer_length=len(final_answer),
        )

        return {
            "answer": final_answer,
            "tool_calls": tool_call_records,
            "model_used": get_settings().PRIMARY_LLM_MODEL,
            "messages": [AIMessage(content=final_answer)],
        }
```

### 12.4 意图路由节点

Python



```
# src/core/orchestrator/nodes/intent_router.py

import structlog
from src.core.orchestrator.state import ConversationState

logger = structlog.get_logger()


async def intent_router_node(state: ConversationState) -> dict:
    """
    意图路由节点

    根据查询理解阶段识别的意图, 决定走哪条路径:
    - knowledge_qa → RAG Agent
    - tool_call → Tool Agent
    - chitchat → Codex (直接回答)
    - unclear → 追问澄清
    """
    intent = state.get("intent", "knowledge_qa")

    logger.info(
        "intent_routed",
        session_id=state["session_id"],
        intent=intent,
    )

    return {"intent": intent}


def route_by_intent(state: ConversationState) -> str:
    """条件路由函数"""
    intent = state.get("intent", "knowledge_qa")

    route_map = {
        "knowledge_qa": "rag_agent",
        "tool_call": "tool_agent",
        "chitchat": "codex_fallback",
        "unclear": "codex_fallback",  # 追问也用Codex
    }

    return route_map.get(intent, "rag_agent")
```

### 12.5 安全护栏

Python



```
# src/core/guardrails/input_guard.py

import re
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class GuardResult(BaseModel):
    """护栏检查结果"""
    passed: bool = True
    blocked_reason: str = ""
    risk_level: str = "none"  # none / low / medium / high


class InputGuard:
    """
    输入安全护栏

    检测:
    1. Prompt 注入攻击
    2. 敏感信息 (身份证/手机号等)
    3. 有害内容
    4. 超出业务范围的话题
    """

    # Prompt注入特征模式
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?previous\s+(instructions?|prompts?)",
        r"disregard\s+(all\s+)?previous",
        r"forget\s+(all\s+)?previous",
        r"you\s+are\s+now\s+a",
        r"act\s+as\s+(if\s+)?you",
        r"pretend\s+you\s+are",
        r"system\s*prompt\s*:",
        r"<\s*system\s*>",
        r"###\s*instruction",
        r"ignore\s+above",
        r"do\s+not\s+follow",
        r"override\s+instructions?",
    ]

    # 敏感信息模式 (中国标准)
    SENSITIVE_PATTERNS = {
        "身份证号": r"\d{17}[\dXx]",
        "手机号": r"1[3-9]\d{9}",
        "银行卡号": r"\d{16,19}",
        "邮箱": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    }

    async def check(self, query: str) -> GuardResult:
        """执行输入安全检查"""

        # 1. Prompt注入检测
        injection_result = self._check_prompt_injection(query)
        if not injection_result.passed:
            logger.warning(
                "input_guard_blocked",
                reason="prompt_injection",
                query=query[:200],
            )
            return injection_result

        # 2. 敏感信息检测
        sensitive_result = self._check_sensitive_info(query)
        if not sensitive_result.passed:
            logger.warning(
                "input_guard_blocked",
                reason="sensitive_info",
                risk_level=sensitive_result.risk_level,
            )
            return sensitive_result

        # 3. 长度检查
        if len(query) > 10000:
            return GuardResult(
                passed=False,
                blocked_reason="输入内容过长，请精简您的问题",
                risk_level="low",
            )

        return GuardResult(passed=True)

    def _check_prompt_injection(self, query: str) -> GuardResult:
        """检测Prompt注入"""
        query_lower = query.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, query_lower):
                return GuardResult(
                    passed=False,
                    blocked_reason="检测到潜在的安全风险，请重新表述您的问题",
                    risk_level="high",
                )
        return GuardResult(passed=True)

    def _check_sensitive_info(self, query: str) -> GuardResult:
        """检测敏感信息"""
        detected = []
        for info_type, pattern in self.SENSITIVE_PATTERNS.items():
            if re.search(pattern, query):
                detected.append(info_type)

        if detected:
            return GuardResult(
                passed=False,
                blocked_reason=f"检测到敏感信息 ({', '.join(detected)})，请勿在问题中包含个人隐私信息",
                risk_level="medium",
            )
        return GuardResult(passed=True)
```

Python



```
# src/core/guardrails/output_guard.py

import re
import structlog
from src.core.guardrails.input_guard import GuardResult

logger = structlog.get_logger()


class OutputGuard:
    """
    输出安全护栏

    检测:
    1. 回答中的敏感信息泄露
    2. 不当内容
    3. 企业合规检查
    """

    # 不应出现在回答中的内容
    FORBIDDEN_PATTERNS = [
        r"我是一个AI",     # 保持角色一致性
        r"作为语言模型",
        r"I am an AI",
        r"API\s*key",      # 防止泄露密钥
        r"password\s*[:=]",
        r"secret\s*[:=]",
    ]

    async def check(self, answer: str, contexts: list[str] | None = None) -> GuardResult:
        """执行输出安全检查"""

        # 1. 禁止模式检测
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, answer, re.IGNORECASE):
                return GuardResult(
                    passed=False,
                    blocked_reason=f"输出包含不适当的内容",
                    risk_level="medium",
                )

        # 2. 敏感信息泄露检测
        from src.core.guardrails.input_guard import InputGuard
        input_guard = InputGuard()
        sensitive_check = input_guard._check_sensitive_info(answer)
        if not sensitive_check.passed:
            # 对输出中的敏感信息进行脱敏
            answer = self._mask_sensitive_info(answer)
            return GuardResult(
                passed=True,  # 脱敏后放行
                blocked_reason="output_masked",
                risk_level="low",
            )

        return GuardResult(passed=True)

    def _mask_sensitive_info(self, text: str) -> str:
        """脱敏处理"""
        # 手机号脱敏: 138****1234
        text = re.sub(r'(1[3-9]\d)\d{4}(\d{4})', r'\1****\2', text)
        # 身份证脱敏
        text = re.sub(r'(\d{6})\d{8}(\d{4})', r'\1********\2', text)
        return text
```

Python



```
# src/core/orchestrator/nodes/guardrails.py

import structlog
from langchain_core.messages import AIMessage

from src.core.orchestrator.state import ConversationState
from src.core.guardrails.input_guard import InputGuard
from src.core.guardrails.output_guard import OutputGuard

logger = structlog.get_logger()


class InputGuardrailNode:
    """输入护栏节点 - 在查询理解之前执行"""

    def __init__(self):
        self.guard = InputGuard()

    async def __call__(self, state: ConversationState) -> dict:
        result = await self.guard.check(state["original_query"])
        return {
            "input_safe": result.passed,
            "input_guard_message": result.blocked_reason,
        }


class OutputGuardrailNode:
    """输出护栏节点 - 在最终返回之前执行"""

    def __init__(self):
        self.guard = OutputGuard()

    async def __call__(self, state: ConversationState) -> dict:
        answer = state.get("answer", "")
        if not answer:
            return {"output_safe": True}

        contexts = [c.get("content", "") for c in state.get("retrieved_chunks", [])]
        result = await self.guard.check(answer, contexts)

        return {
            "output_safe": result.passed,
            "output_guard_message": result.blocked_reason,
        }


def should_block_input(state: ConversationState) -> str:
    """条件路由: 输入是否安全"""
    if state.get("input_safe", True):
        return "continue"
    return "block"
```

### 12.6 完整图重构 (Phase 3)

Python



```
# src/core/orchestrator/graph.py  (Phase 3 完整版)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.core.orchestrator.state import ConversationState
from src.core.orchestrator.nodes.guardrails import (
    InputGuardrailNode, OutputGuardrailNode, should_block_input,
)
from src.core.orchestrator.nodes.query_understanding import QueryUnderstandingNode
from src.core.orchestrator.nodes.cache_lookup import CacheLookupNode, should_skip_rag
from src.core.orchestrator.nodes.intent_router import intent_router_node, route_by_intent
from src.core.orchestrator.nodes.rag_agent import RAGAgentNode
from src.core.orchestrator.nodes.tool_agent import ToolAgentNode
from src.core.orchestrator.nodes.response_synthesizer import ResponseSynthesizerNode
from src.core.orchestrator.nodes.quality_gate import QualityGateNode
from src.core.orchestrator.nodes.human_review import HumanReviewNode
from src.core.orchestrator.nodes.codex_fallback import CodexFallbackNode


def build_graph(
    input_guard_node: InputGuardrailNode,
    query_understanding_node: QueryUnderstandingNode,
    cache_lookup_node: CacheLookupNode,
    rag_agent_node: RAGAgentNode,
    tool_agent_node: ToolAgentNode,
    response_synthesizer_node: ResponseSynthesizerNode,
    quality_gate_node: QualityGateNode,
    output_guard_node: OutputGuardrailNode,
    human_review_node: HumanReviewNode,
    codex_fallback_node: CodexFallbackNode,
) -> StateGraph:
    """
    Phase 3 完整对话图

    流程:
    输入护栏 → 查询理解 → 缓存查询 →
      ├─ 缓存命中 → 输出护栏 → END
      ├─ 闲聊 → Codex → 输出护栏 → END
      ├─ 工具调用 → Tool Agent → 质量门控 → ...
      └─ 知识问答 → RAG Agent → 答案生成 → 质量门控 →
            ├─ 高质量 → 输出护栏 → END
            ├─ 中等 → Codex降级 → 输出护栏 → END
            └─ 低质量 → 人工审查 (中断) → 输出护栏 → END
    """

    graph = StateGraph(ConversationState)

    # === 注册所有节点 ===
    graph.add_node("input_guard",         input_guard_node)
    graph.add_node("blocked_response",    blocked_response_node)
    graph.add_node("query_understanding", query_understanding_node)
    graph.add_node("cache_lookup",        cache_lookup_node)
    graph.add_node("intent_router",       intent_router_node)
    graph.add_node("rag_agent",           rag_agent_node)
    graph.add_node("tool_agent",          tool_agent_node)
    graph.add_node("generate_answer",     response_synthesizer_node)
    graph.add_node("quality_gate",        quality_gate_node)
    graph.add_node("output_guard",        output_guard_node)
    graph.add_node("human_review",        human_review_node)
    graph.add_node("codex_fallback",      codex_fallback_node)
    graph.add_node("post_review_route",   post_review_route_node)

    # === 定义边 ===

    # 1. 入口 → 输入护栏
    graph.add_edge(START, "input_guard")

    # 2. 输入护栏: 安全 → 继续 / 不安全 → 拒绝
    graph.add_conditional_edges(
        "input_guard",
        should_block_input,
        {
            "continue": "query_understanding",
            "block": "blocked_response",
        },
    )
    graph.add_edge("blocked_response", END)

    # 3. 查询理解 → 缓存查询
    graph.add_edge("query_understanding", "cache_lookup")

    # 4. 缓存查询: 命中/闲聊/知识问答
    graph.add_conditional_edges(
        "cache_lookup",
        should_skip_rag,
        {
            "skip_to_end": "output_guard",     # 缓存命中
            "codex_fallback": "codex_fallback", # 闲聊
            "rag_agent": "intent_router",       # 需要进一步路由
        },
    )

    # 5. 意图路由
    graph.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {
            "rag_agent": "rag_agent",
            "tool_agent": "tool_agent",
            "codex_fallback": "codex_fallback",
        },
    )

    # 6. RAG Agent → 答案生成 → 质量门控
    graph.add_edge("rag_agent", "generate_answer")
    graph.add_edge("generate_answer", "quality_gate")

    # 7. Tool Agent → 质量门控
    graph.add_edge("tool_agent", "quality_gate")

    # 8. 质量门控: 通过/降级/审查
    graph.add_conditional_edges(
        "quality_gate",
        route_by_quality,
        {
            "pass": "output_guard",
            "fallback_codex": "codex_fallback",
            "human_review": "human_review",
        },
    )

    # 9. Codex降级 → 输出护栏
    graph.add_edge("codex_fallback", "output_guard")

    # 10. 人工审查 (中断点) → 审查后路由
    graph.add_edge("human_review", "post_review_route")

    # 11. 审查后路由: 通过/编辑 → 输出护栏, 拒绝 → Codex
    graph.add_conditional_edges(
        "post_review_route",
        route_after_review,
        {
            "output_guard": "output_guard",
            "codex_fallback": "codex_fallback",
        },
    )

    # 12. 输出护栏 → END
    graph.add_edge("output_guard", END)

    return graph


# === 辅助节点和路由函数 ===

async def blocked_response_node(state: ConversationState) -> dict:
    """被输入护栏拦截时的回复"""
    from langchain_core.messages import AIMessage
    blocked_msg = state.get("input_guard_message", "您的请求无法处理")
    return {
        "answer": blocked_msg,
        "confidence": 1.0,
        "model_used": "guardrail",
        "messages": [AIMessage(content=blocked_msg)],
    }


def route_by_quality(state: ConversationState) -> str:
    """根据质量评估决定路由"""
    from src.infra.config.settings import get_settings
    settings = get_settings()
    confidence = state.get("confidence", 0)

    if confidence >= settings.CONFIDENCE_THRESHOLD_PASS:
        return "pass"
    elif confidence >= settings.CONFIDENCE_THRESHOLD_FALLBACK:
        return "fallback_codex"
    else:
        return "human_review"


async def post_review_route_node(state: ConversationState) -> dict:
    """审查后路由节点"""
    return {}


def route_after_review(state: ConversationState) -> str:
    """审查完成后的路由"""
    review = state.get("human_review_result", {})
    action = review.get("action", "approve")

    if action in ("approve", "edit"):
        return "output_guard"  # 通过/编辑后 → 输出护栏
    else:
        return "codex_fallback"  # 拒绝 → Codex重新生成


async def compile_graph(nodes: dict, postgres_url: str):
    """编译图 (带中断点)"""
    graph = build_graph(**nodes)

    checkpointer = AsyncPostgresSaver.from_conn_string(postgres_url)
    await checkpointer.setup()

    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],  # 在人工审查前中断!
    )

    return compiled
```

text



```
Phase 3 完整图可视化:

    ┌─────────────────┐
    │      START      │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  input_guard    │ ← Prompt注入/敏感信息检测
    └───┬─────────┬───┘
        │         │
   安全 │     不安全│
        ▼         ▼
    ┌────────┐  ┌──────────────┐
    │继续流程│  │blocked_resp  │→ END
    └───┬────┘  └──────────────┘
        │
        ▼
    ┌─────────────────┐
    │ query_under-    │ ← LLM改写+指代消解+意图识别
    │ standing        │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  cache_lookup   │ ← 语义缓存
    └─┬──────┬────┬───┘
      │      │    │
 命中 │  闲聊│    │继续
      │      │    │
      ▼      │    ▼
  output_    │  ┌──────────────┐
  guard      │  │intent_router │ ← 意图路由
  → END      │  └──┬───────┬───┘
             │     │       │
             │  RAG│    Tool│
             │     ▼       ▼
             │  ┌──────┐ ┌──────────┐
             │  │ RAG  │ │  Tool    │
             │  │Agent │ │  Agent   │ ← MCP工具调用
             │  └──┬───┘ └────┬─────┘
             │     │          │
             │     ▼          │
             │  ┌──────────┐  │
             │  │generate  │  │
             │  │_answer   │  │
             │  └────┬─────┘  │
             │       │        │
             │       ▼        ▼
             │  ┌──────────────────┐
             │  │  quality_gate    │ ← LLM置信度+幻觉检测
             │  └─┬──────┬──────┬─┘
             │    │      │      │
             │ ≥0.7  0.4-0.7  <0.4
             │    │      │      │
             │    ▼      ▼      ▼
             │  output  codex  ┌────────────┐
             │  guard   fallb  │human_review│ ← ⚡中断!
             │                 │(interrupt) │
             │                 └─────┬──────┘
             │                       │ (resume后)
             │                       ▼
             │                 ┌────────────┐
             │                 │post_review │
             │                 │_route      │
             │                 └──┬─────┬───┘
             │              通过/编辑  拒绝
             │                 │      │
             │                 ▼      ▼
             │              output  codex
             │              guard   fallback
             │                 │      │
             ▼                 ▼      ▼
    ┌─────────────────────────────────────┐
    │          output_guard               │ ← 输出安全检查
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────┐
    │       END       │
    └─────────────────┘
```

------

## 五、Week 13：长期记忆 & 多租户 & 认证

### 13.1 长期记忆

Python



```
# src/core/memory/long_term.py

import json
from datetime import datetime
import asyncio
import structlog

import asyncpg
from pymilvus import MilvusClient
from llama_index.embeddings.openai import OpenAIEmbedding

logger = structlog.get_logger()


class LongTermMemory:
    """
    长期记忆 - PostgreSQL + Milvus

    能力:
    1. 持久化所有对话历史
    2. 语义搜索: 查找与当前问题相关的历史对话
    3. 用户偏好/知识积累
    """

    MEMORY_COLLECTION = "conversation_memory"

    def __init__(
        self,
        pg_pool: asyncpg.Pool,
        milvus_client: MilvusClient,
        embedding_model: OpenAIEmbedding,
    ):
        self.pg_pool = pg_pool
        self.milvus = milvus_client
        self.embedding = embedding_model

    async def initialize(self):
        """初始化Milvus记忆Collection"""
        if self.milvus.has_collection(self.MEMORY_COLLECTION):
            return

        from pymilvus import CollectionSchema, FieldSchema, DataType

        schema = CollectionSchema(
            fields=[
                FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema("user_id", DataType.VARCHAR, max_length=64),
                FieldSchema("tenant_id", DataType.VARCHAR, max_length=64),
                FieldSchema("session_id", DataType.VARCHAR, max_length=64),
                FieldSchema("text", DataType.VARCHAR, max_length=65535),
                FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=3072),
                FieldSchema("timestamp", DataType.INT64),
            ],
        )

        self.milvus.create_collection(
            collection_name=self.MEMORY_COLLECTION,
            schema=schema,
        )

        index_params = self.milvus.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="HNSW",
            metric_type="COSINE",
            params={"M": 16, "efConstruction": 128},
        )
        index_params.add_index(field_name="user_id", index_type="Trie")
        index_params.add_index(field_name="tenant_id", index_type="Trie")

        self.milvus.create_index(
            collection_name=self.MEMORY_COLLECTION,
            index_params=index_params,
        )
        self.milvus.load_collection(self.MEMORY_COLLECTION)

        logger.info("long_term_memory_collection_initialized")

    async def save_turn(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: dict | None = None,
    ):
        """保存一轮对话到长期记忆"""
        import uuid

        memory_text = f"用户问: {user_message}\n助手答: {assistant_message}"
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

        # 1. 计算embedding
        embedding = await self.embedding.aget_text_embedding(memory_text)

        # 2. 写入Milvus (语义搜索)
        try:
            self.milvus.insert(
                collection_name=self.MEMORY_COLLECTION,
                data=[{
                    "id": memory_id,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "session_id": session_id,
                    "text": memory_text[:65000],
                    "embedding": embedding,
                    "timestamp": int(datetime.utcnow().timestamp()),
                }],
            )
        except Exception as e:
            logger.error("long_term_memory_milvus_save_failed", error=str(e))

    async def search_relevant_history(
        self,
        user_id: str,
        tenant_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """语义搜索用户的历史对话"""
        query_embedding = await self.embedding.aget_text_embedding(query)

        try:
            results = self.milvus.search(
                collection_name=self.MEMORY_COLLECTION,
                data=[query_embedding],
                filter=f'user_id == "{user_id}" and tenant_id == "{tenant_id}"',
                limit=top_k,
                output_fields=["text", "session_id", "timestamp"],
                search_params={
                    "metric_type": "COSINE",
                    "params": {"ef": 64},
                },
            )

            if not results or not results[0]:
                return []

            return [
                {
                    "text": hit["entity"]["text"],
                    "session_id": hit["entity"]["session_id"],
                    "similarity": hit["distance"],
                    "timestamp": hit["entity"]["timestamp"],
                }
                for hit in results[0]
                if hit["distance"] > 0.6  # 只返回相关度较高的
            ]

        except Exception as e:
            logger.error("long_term_memory_search_failed", error=str(e))
            return []
```

### 13.2 记忆管理器升级

Python



```
# src/core/memory/manager.py  (Phase 3 完整版)

import asyncio
import structlog

from redis.asyncio import Redis
import asyncpg
from pymilvus import MilvusClient
from llama_index.embeddings.openai import OpenAIEmbedding

from src.core.memory.short_term import ShortTermMemory
from src.core.memory.long_term import LongTermMemory
from src.infra.config.settings import Settings

logger = structlog.get_logger()


class MemoryManager:
    """
    记忆管理器 - Phase 3 三层融合

    层级:
    1. 短期记忆 (Redis) - 当前会话对话历史
    2. 长期记忆 (PG + Milvus) - 跨会话历史语义搜索
    3. 语义记忆 (Phase 4: 知识图谱) - 预留

    加载上下文时融合多层记忆
    """

    def __init__(
        self,
        redis: Redis,
        pg_pool: asyncpg.Pool,
        milvus_client: MilvusClient,
        embedding_model: OpenAIEmbedding,
        settings: Settings,
    ):
        self.short_term = ShortTermMemory(
            redis=redis,
            ttl=settings.SHORT_TERM_MEMORY_TTL,
            max_messages=settings.MAX_SHORT_TERM_MESSAGES,
        )
        self.long_term = LongTermMemory(
            pg_pool=pg_pool,
            milvus_client=milvus_client,
            embedding_model=embedding_model,
        )

    async def initialize(self):
        """初始化 (创建Milvus Collection等)"""
        await self.long_term.initialize()

    async def load_context(
        self,
        user_id: str,
        session_id: str,
        current_query: str,
        max_short_term_turns: int = 5,
        max_long_term_results: int = 3,
    ) -> list[dict[str, str]]:
        """
        加载融合的对话上下文

        融合策略:
        1. 短期记忆: 当前会话最近N轮
        2. 长期记忆: 语义搜索历史中与当前问题相关的对话片段
        3. 合并去重后返回
        """
        # 并行加载
        short_term_task = self.short_term.get_formatted_history(
            session_id, last_n_turns=max_short_term_turns,
        )
        long_term_task = self.long_term.search_relevant_history(
            user_id=user_id,
            tenant_id="default",  # TODO: 从上下文获取
            query=current_query,
            top_k=max_long_term_results,
        )

        short_messages, long_results = await asyncio.gather(
            short_term_task, long_term_task,
            return_exceptions=True,
        )

        if isinstance(short_messages, Exception):
            logger.error("short_term_memory_load_failed", error=str(short_messages))
            short_messages = []

        if isinstance(long_results, Exception):
            logger.error("long_term_memory_load_failed", error=str(long_results))
            long_results = []

        # 构建上下文
        context = []

        # 先加入长期记忆 (作为"之前相关的对话参考")
        if long_results:
            # 过滤掉当前会话的记录 (避免重复)
            relevant_history = [
                r for r in long_results
                if r.get("session_id") != session_id
            ]
            if relevant_history:
                context.append({
                    "role": "system",
                    "content": (
                        "以下是用户之前相关的对话记录，供参考：\n"
                        + "\n---\n".join(r["text"][:300] for r in relevant_history[:2])
                    ),
                })

        # 再加入短期记忆 (当前会话的对话历史)
        context.extend(short_messages)

        logger.debug(
            "memory_context_loaded",
            session_id=session_id,
            short_term_count=len(short_messages),
            long_term_count=len(long_results) if isinstance(long_results, list) else 0,
            total_context_messages=len(context),
        )

        return context

    async def save_turn(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        assistant_message: str,
        metadata: dict | None = None,
    ):
        """保存一轮对话到所有层"""
        # 短期 (同步)
        await self.short_term.add_exchange(
            session_id=session_id,
            user_message=user_message,
            assistant_message=assistant_message,
            metadata=metadata,
        )

        # 长期 (异步后台, 不阻塞响应)
        asyncio.create_task(
            self._save_long_term(
                user_id, session_id, user_message, assistant_message, metadata,
            )
        )

    async def _save_long_term(
        self, user_id, session_id, user_message, assistant_message, metadata
    ):
        """后台保存到长期记忆"""
        try:
            await self.long_term.save_turn(
                user_id=user_id,
                tenant_id="default",
                session_id=session_id,
                user_message=user_message,
                assistant_message=assistant_message,
                metadata=metadata,
            )
        except Exception as e:
            logger.error("long_term_memory_save_failed", error=str(e))

    async def clear_session(self, session_id: str):
        await self.short_term.clear(session_id)
```

### 13.3 认证模块

Python



```
# src/core/auth/models.py

from pydantic import BaseModel, Field
from datetime import datetime


class User(BaseModel):
    """用户模型"""
    id: str
    username: str
    email: str
    display_name: str = ""
    role: str = "user"      # admin / reviewer / user
    tenant_id: str
    is_active: bool = True


class TokenPayload(BaseModel):
    """JWT载荷"""
    sub: str              # user_id
    username: str
    role: str
    tenant_id: str
    exp: int              # 过期时间


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
```

Python



```
# src/core/auth/jwt_handler.py

import time
from datetime import datetime, timedelta
from functools import wraps

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

from src.core.auth.models import User, TokenPayload
from src.infra.config.settings import get_settings

logger = structlog.get_logger()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()

SECRET_KEY = "your-secret-key-change-in-production-use-env-var"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User) -> tuple[str, int]:
    """创建JWT"""
    expires = int(time.time()) + ACCESS_TOKEN_EXPIRE_HOURS * 3600
    payload = {
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "exp": expires,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, ACCESS_TOKEN_EXPIRE_HOURS * 3600


def verify_token(token: str) -> User:
    """验证JWT, 返回User"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return User(
            id=payload["sub"],
            username=payload["username"],
            email="",
            role=payload["role"],
            tenant_id=payload["tenant_id"],
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> User:
    """FastAPI依赖: 获取当前用户"""
    return verify_token(credentials.credentials)


def require_role(allowed_roles: list[str]):
    """角色检查依赖工厂"""
    async def _check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' not allowed. Required: {allowed_roles}",
            )
        return user
    return _check_role
```

Python



```
# src/api/routers/auth.py

from fastapi import APIRouter, HTTPException
import structlog

from src.core.auth.models import LoginRequest, TokenResponse, User
from src.core.auth.jwt_handler import verify_password, create_access_token, hash_password

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    row = await pool.fetchrow(
        "SELECT * FROM users WHERE username = $1 AND is_active = TRUE",
        request.username,
    )

    if not row or not verify_password(request.password, row["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = User(
        id=row["id"],
        username=row["username"],
        email=row["email"],
        display_name=row["display_name"] or "",
        role=row["role"],
        tenant_id=row["tenant_id"],
    )

    token, expires_in = create_access_token(user)

    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=user,
    )


@router.post("/register")
async def register(
    username: str,
    email: str,
    password: str,
    tenant_id: str = "default",
    role: str = "user",
):
    """注册用户 (仅开发环境)"""
    from src.infra.config.settings import get_settings
    settings = get_settings()
    if settings.ENV == "production":
        raise HTTPException(403, "Registration disabled in production")

    import uuid
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed = hash_password(password)

    await pool.execute(
        """INSERT INTO users (id, username, email, hashed_password, role, tenant_id)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        user_id, username, email, hashed, role, tenant_id,
    )

    return {"user_id": user_id, "message": "User registered"}
```

### 13.4 多租户隔离

Python



```
# src/api/middlewares/auth.py

from fastapi import Request
from src.core.auth.jwt_handler import get_current_user
from src.core.auth.models import User


class TenantContext:
    """租户上下文 - 在请求级别传递租户信息"""

    def __init__(self, tenant_id: str, user: User):
        self.tenant_id = tenant_id
        self.user = user


async def get_tenant_context(request: Request) -> TenantContext:
    """
    获取租户上下文

    多租户隔离策略:
    1. 从JWT中提取tenant_id
    2. 所有数据库查询自动添加tenant_id过滤
    3. Milvus使用partition_key隔离
    4. ES使用按租户分索引
    """
    user = await get_current_user(request)
    return TenantContext(tenant_id=user.tenant_id, user=user)
```

### 13.5 用户反馈 API

Python



```
# src/api/routers/feedback.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import structlog

from src.core.auth.jwt_handler import get_current_user
from src.core.auth.models import User

logger = structlog.get_logger()
router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    """反馈请求"""
    session_id: str
    message_id: int | None = None
    feedback_type: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")
    tags: list[str] = Field(default_factory=list)
    comment: str = ""


@router.post("/submit")
async def submit_feedback(
    request: FeedbackRequest,
    user: User = Depends(get_current_user),
):
    """提交用户反馈"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    # 获取关联的问答内容
    msg = None
    if request.message_id:
        msg = await pool.fetchrow(
            "SELECT content, confidence FROM conversation_messages WHERE id = $1",
            request.message_id,
        )

    await pool.execute(
        """INSERT INTO user_feedback 
           (session_id, message_id, user_id, tenant_id, feedback_type,
            feedback_tags, comment, query, answer, confidence)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
        request.session_id,
        request.message_id,
        user.id,
        user.tenant_id,
        request.feedback_type,
        request.tags,
        request.comment,
        msg["content"] if msg else None,
        None,
        msg["confidence"] if msg else None,
    )

    logger.info(
        "feedback_submitted",
        session_id=request.session_id,
        type=request.feedback_type,
        tags=request.tags,
    )

    return {"message": "Feedback submitted", "session_id": request.session_id}


@router.get("/stats")
async def get_feedback_stats(
    days: int = 30,
    user: User = Depends(get_current_user),
):
    """获取反馈统计"""
    from src.infra.database.postgres import get_postgres_pool
    pool = await get_postgres_pool()

    stats = await pool.fetchrow(
        """SELECT 
            COUNT(*) FILTER (WHERE feedback_type = 'thumbs_up') as positive,
            COUNT(*) FILTER (WHERE feedback_type = 'thumbs_down') as negative,
            COUNT(*) as total
           FROM user_feedback 
           WHERE tenant_id = $1 
           AND created_at >= CURRENT_DATE - ($2 || ' days')::INTERVAL""",
        user.tenant_id, str(days),
    )

    total = stats["total"] or 1
    return {
        "positive": stats["positive"],
        "negative": stats["negative"],
        "total": total,
        "satisfaction_rate": round(stats["positive"] / total, 3),
        "period_days": days,
    }
```

------

## 六、Week 14：限流熔断 & 生产监控

### 14.1 限流中间件

Python



```
# src/api/middlewares/rate_limit.py

import time
import structlog
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from redis.asyncio import Redis

from src.infra.database.redis_client import get_redis

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-based 滑动窗口限流中间件

    策略:
    - 全局限流: 所有请求
    - 用户级限流: 按user_id (JWT)
    - 接口级限流: 按路径
    """

    def __init__(self, app, global_rpm: int = 1000, user_rpm: int = 60):
        super().__init__(app)
        self.global_rpm = global_rpm
        self.user_rpm = user_rpm

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 跳过健康检查等公共路径
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        try:
            redis = await get_redis()
        except Exception:
            # Redis不可用时跳过限流 (降级)
            return await call_next(request)

        # 全局限流
        global_allowed = await self._check_rate(
            redis, "ratelimit:global", self.global_rpm
        )
        if not global_allowed:
            logger.warning("rate_limit_global_exceeded")
            raise HTTPException(429, "Server rate limit exceeded. Please retry later.")

        # 用户级限流
        user_id = self._extract_user_id(request)
        if user_id:
            user_allowed = await self._check_rate(
                redis, f"ratelimit:user:{user_id}", self.user_rpm
            )
            if not user_allowed:
                logger.warning("rate_limit_user_exceeded", user_id=user_id)
                raise HTTPException(429, "User rate limit exceeded. Please slow down.")

        response = await call_next(request)

        # 添加限流相关响应头
        response.headers["X-RateLimit-Limit"] = str(self.user_rpm)
        remaining = await self._get_remaining(
            redis, f"ratelimit:user:{user_id or 'anonymous'}", self.user_rpm
        )
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response

    async def _check_rate(self, redis: Redis, key: str, limit: int) -> bool:
        """滑动窗口限流检查"""
        now = time.time()
        window_start = now - 60  # 1分钟窗口

        pipe = redis.pipeline()
        # 移除过期的记录
        pipe.zremrangebyscore(key, 0, window_start)
        # 统计当前窗口内的请求数
        pipe.zcard(key)
        # 添加当前请求
        pipe.zadd(key, {str(now): now})
        # 设置过期时间
        pipe.expire(key, 120)

        results = await pipe.execute()
        current_count = results[1]

        return current_count < limit

    async def _get_remaining(self, redis: Redis, key: str, limit: int) -> int:
        """获取剩余配额"""
        now = time.time()
        window_start = now - 60
        count = await redis.zcount(key, window_start, now)
        return limit - count

    def _extract_user_id(self, request: Request) -> str | None:
        """从请求中提取用户ID"""
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                from src.core.auth.jwt_handler import verify_token
                user = verify_token(auth.split(" ")[1])
                return user.id
            except Exception:
                pass
        return request.client.host if request.client else None
```

### 14.2 熔断器

Python



```
# src/api/middlewares/circuit_breaker.py

import pybreaker
import structlog
from functools import wraps

logger = structlog.get_logger()


class CircuitBreakerFactory:
    """
    熔断器工厂

    为不同的外部依赖创建独立的熔断器:
    - LLM调用
    - Milvus查询
    - Elasticsearch查询
    - MCP工具调用
    """

    _breakers: dict[str, pybreaker.CircuitBreaker] = {}

    @classmethod
    def get(
        cls,
        name: str,
        fail_max: int = 5,
        reset_timeout: int = 30,
    ) -> pybreaker.CircuitBreaker:
        """获取或创建熔断器"""
        if name not in cls._breakers:

            class LogListener(pybreaker.CircuitBreakerListener):
                def state_change(self, cb, old_state, new_state):
                    logger.warning(
                        "circuit_breaker_state_change",
                        breaker=name,
                        old_state=old_state.name,
                        new_state=new_state.name,
                    )

            cls._breakers[name] = pybreaker.CircuitBreaker(
                fail_max=fail_max,
                reset_timeout=reset_timeout,
                listeners=[LogListener()],
                name=name,
            )

        return cls._breakers[name]

    @classmethod
    def get_all_states(cls) -> dict:
        """获取所有熔断器状态"""
        return {
            name: {
                "state": breaker.current_state,
                "fail_counter": breaker.fail_counter,
            }
            for name, breaker in cls._breakers.items()
        }


# 预定义的熔断器
llm_breaker = CircuitBreakerFactory.get("llm", fail_max=5, reset_timeout=30)
milvus_breaker = CircuitBreakerFactory.get("milvus", fail_max=3, reset_timeout=15)
es_breaker = CircuitBreakerFactory.get("elasticsearch", fail_max=3, reset_timeout=15)
mcp_breaker = CircuitBreakerFactory.get("mcp_tools", fail_max=5, reset_timeout=60)


def with_circuit_breaker(breaker_name: str):
    """熔断器装饰器"""
    breaker = CircuitBreakerFactory.get(breaker_name)

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await breaker.call_async(func, *args, **kwargs)
            except pybreaker.CircuitBreakerError:
                logger.error(
                    "circuit_breaker_open",
                    breaker=breaker_name,
                    function=func.__name__,
                )
                raise RuntimeError(
                    f"Service '{breaker_name}' is currently unavailable (circuit open)"
                )
        return wrapper
    return decorator
```

### 14.3 Prometheus 指标

Python



```
# src/infra/monitoring/metrics.py

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
)
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
import structlog

logger = structlog.get_logger()

# ============================================================
# 自定义业务指标
# ============================================================

# 对话指标
CHAT_REQUESTS_TOTAL = Counter(
    "qa_chat_requests_total",
    "Total chat requests",
    ["status", "model", "tenant_id"],
)

CHAT_LATENCY = Histogram(
    "qa_chat_latency_seconds",
    "Chat request latency",
    ["intent", "cache_hit"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

CHAT_CONFIDENCE = Histogram(
    "qa_chat_confidence",
    "Answer confidence distribution",
    ["model"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# RAG指标
RAG_RETRIEVAL_LATENCY = Histogram(
    "qa_rag_retrieval_latency_seconds",
    "RAG retrieval latency",
    ["retrieval_type"],  # dense / sparse / hybrid
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0],
)

RAG_CHUNKS_RETRIEVED = Histogram(
    "qa_rag_chunks_retrieved",
    "Number of chunks retrieved",
    buckets=[0, 1, 2, 3, 5, 10, 20],
)

# 缓存指标
CACHE_HITS_TOTAL = Counter(
    "qa_cache_hits_total",
    "Cache hits",
    ["cache_level"],  # exact / semantic
)

CACHE_MISSES_TOTAL = Counter(
    "qa_cache_misses_total",
    "Cache misses",
)

# 降级指标
FALLBACK_TOTAL = Counter(
    "qa_fallback_total",
    "Fallback to Codex count",
    ["reason"],  # low_confidence / rag_failed / error
)

# 审查指标
REVIEW_QUEUE_SIZE = Gauge(
    "qa_review_queue_size",
    "Pending reviews in queue",
    ["tenant_id", "priority"],
)

REVIEW_LATENCY = Histogram(
    "qa_review_latency_seconds",
    "Time from review creation to completion",
    buckets=[60, 300, 900, 1800, 3600, 7200, 86400],
)

# LLM指标
LLM_TOKENS_TOTAL = Counter(
    "qa_llm_tokens_total",
    "Total LLM tokens consumed",
    ["model", "operation"],  # chat / embedding / rerank / evaluation
)

LLM_CALLS_TOTAL = Counter(
    "qa_llm_calls_total",
    "Total LLM API calls",
    ["model", "status"],  # success / error
)

LLM_LATENCY = Histogram(
    "qa_llm_latency_seconds",
    "LLM API call latency",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# 工具调用指标
TOOL_CALLS_TOTAL = Counter(
    "qa_tool_calls_total",
    "Tool calls",
    ["tool_name", "status"],
)

# 反馈指标
FEEDBACK_TOTAL = Counter(
    "qa_feedback_total",
    "User feedback count",
    ["type"],  # thumbs_up / thumbs_down
)

# 熔断器指标
CIRCUIT_BREAKER_STATE = Gauge(
    "qa_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["name"],
)

# 系统信息
SYSTEM_INFO = Info(
    "qa_system",
    "System information",
)


def setup_prometheus(app: FastAPI):
    """配置Prometheus指标"""

    # 自动HTTP指标 (请求数/延迟/状态码)
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # 设置系统信息
    from src.infra.config.settings import get_settings
    settings = get_settings()
    SYSTEM_INFO.info({
        "version": settings.APP_VERSION,
        "env": settings.ENV,
        "primary_model": settings.PRIMARY_LLM_MODEL,
    })

    logger.info("prometheus_metrics_configured")
```

### 14.4 Prometheus 配置

YAML



```
# docker/configs/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

scrape_configs:
  - job_name: "qa-api"
    scrape_interval: 10s
    static_configs:
      - targets: ["api:8000"]
    metrics_path: /metrics

  - job_name: "milvus"
    static_configs:
      - targets: ["milvus:9091"]
    metrics_path: /metrics

  - job_name: "redis"
    static_configs:
      - targets: ["redis-exporter:9121"]

  - job_name: "postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]
```

YAML



```
# docker/configs/prometheus/alert_rules.yml

groups:
  - name: qa-assistant-alerts
    rules:
      # 高错误率
      - alert: HighErrorRate
        expr: rate(qa_chat_requests_total{status="error"}[5m]) / rate(qa_chat_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected (> 10%)"

      # 高延迟
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(qa_chat_latency_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency exceeds 10 seconds"

      # 审查队列堆积
      - alert: ReviewQueueBacklog
        expr: qa_review_queue_size > 50
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Review queue has more than 50 pending items"

      # 熔断器打开
      - alert: CircuitBreakerOpen
        expr: qa_circuit_breaker_state == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker is open for {{ $labels.name }}"

      # 降级率过高
      - alert: HighFallbackRate
        expr: rate(qa_fallback_total[5m]) / rate(qa_chat_requests_total[5m]) > 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Fallback rate exceeds 30%"

      # 低满意度
      - alert: LowSatisfaction
        expr: >
          rate(qa_feedback_total{type="thumbs_down"}[1h]) /
          (rate(qa_feedback_total{type="thumbs_up"}[1h]) + rate(qa_feedback_total{type="thumbs_down"}[1h])) > 0.4
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "User satisfaction below 60%"
```

### 14.5 Grafana Dashboard 配置

JSON



```
// docker/configs/grafana/dashboards/qa-overview.json (简化版)
{
  "dashboard": {
    "title": "QA Assistant Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [{"expr": "rate(qa_chat_requests_total[5m])"}]
      },
      {
        "title": "P95 Latency",
        "type": "gauge",
        "targets": [{"expr": "histogram_quantile(0.95, rate(qa_chat_latency_seconds_bucket[5m]))"}]
      },
      {
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [{"expr": "rate(qa_cache_hits_total[5m]) / (rate(qa_cache_hits_total[5m]) + rate(qa_cache_misses_total[5m]))"}]
      },
      {
        "title": "Confidence Distribution",
        "type": "histogram",
        "targets": [{"expr": "qa_chat_confidence_bucket"}]
      },
      {
        "title": "Fallback Rate",
        "type": "stat",
        "targets": [{"expr": "rate(qa_fallback_total[5m]) / rate(qa_chat_requests_total[5m])"}]
      },
      {
        "title": "Review Queue",
        "type": "gauge",
        "targets": [{"expr": "qa_review_queue_size"}]
      },
      {
        "title": "LLM Token Usage",
        "type": "graph",
        "targets": [{"expr": "rate(qa_llm_tokens_total[1h])"}]
      },
      {
        "title": "Circuit Breaker States",
        "type": "table",
        "targets": [{"expr": "qa_circuit_breaker_state"}]
      }
    ]
  }
}
```

------

## 七、Phase 3 验收标准

### 功能验收

| #    | 功能          | 验收标准                                             | 状态 |
| ---- | ------------- | ---------------------------------------------------- | ---- |
| 1    | 人工审查      | 低置信度回答自动进入审查队列，审查员可审批/编辑/拒绝 | ⬜    |
| 2    | 可中断/恢复   | 对话在审查节点正确中断，审查完成后自动恢复           | ⬜    |
| 3    | 审查WebSocket | 新审查请求实时推送给审查员                           | ⬜    |
| 4    | MCP工具调用   | 至少2个MCP Server可连接，工具调用正常                | ⬜    |
| 5    | 内置工具      | 计算器、日期等内置工具可用                           | ⬜    |
| 6    | 意图路由      | 正确区分知识问答/工具调用/闲聊                       | ⬜    |
| 7    | 输入护栏      | Prompt注入、敏感信息被正确拦截                       | ⬜    |
| 8    | 输出护栏      | 敏感信息泄露被脱敏                                   | ⬜    |
| 9    | 长期记忆      | 跨会话语义搜索可用，历史对话可引用                   | ⬜    |
| 10   | JWT认证       | 登录、Token验证、角色鉴权正常                        | ⬜    |
| 11   | 多租户        | 不同租户数据隔离，查询互不影响                       | ⬜    |
| 12   | 限流          | 超过限流阈值返回429                                  | ⬜    |
| 13   | 熔断          | 外部依赖故障时熔断器打开，恢复后自动关闭             | ⬜    |
| 14   | Prometheus    | /metrics 端点暴露所有业务指标                        | ⬜    |
| 15   | Grafana       | 监控大盘展示核心指标                                 | ⬜    |
| 16   | 告警          | 高错误率/高延迟/审查堆积触发告警                     | ⬜    |
| 17   | 用户反馈      | 👍👎反馈收集和统计                                     | ⬜    |

### 性能标准

| 指标            | Phase 2 | Phase 3 目标 | 说明               |
| --------------- | ------- | ------------ | ------------------ |
| P95 延迟 (正常) | ~5s     | < 6s         | 增加护栏但控制增量 |
| P95 延迟 (缓存) | < 100ms | < 100ms      | 不变               |
| 并发支持        | 20      | 100          | 限流保护           |
| 审查响应时间    | N/A     | SLA < 4h     | 高优先级           |
| 护栏延迟增量    | N/A     | < 50ms       | 规则引擎为主       |
| 限流精度        | N/A     | 误差 < 5%    | Redis滑动窗口      |

------

## 八、Phase 3 → Phase 4 过渡预留

| 扩展点           | 预留位置               | Phase 4 计划                |
| ---------------- | ---------------------- | --------------------------- |
| 多Agent编排      | LangGraph图可扩展      | 增加 Supervisor + 专家Agent |
| 辩论机制         | 新增子图               | 正/反方辩论 + Judge裁决     |
| 知识图谱         | MemoryManager预留第4层 | Neo4j 实体关系记忆          |
| Agentic Chunking | Chunker策略可扩展      | LLM判断分块边界             |
| 反馈闭环         | user_feedback表已就绪  | 基于反馈的RAG优化           |
| Prompt版本管理   | 可新增模块             | 版本控制 + A/B测试          |
| K8s部署          | Docker镜像已就绪       | Helm Chart + HPA            |