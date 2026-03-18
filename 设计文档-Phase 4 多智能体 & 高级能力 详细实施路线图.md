1. # Phase 4 多智能体 & 高级能力 详细实施路线图

2. > **目标**: 构建多智能体协作/竞争系统、知识图谱记忆、高级RAG策略、反馈闭环优化、Prompt版本管理，并完成Kubernetes生产部署
   > **周期**: 4-6 周
   > **前置依赖**: Phase 3 全部验收通过
   > **交付物**: 具备多智能体协作能力、知识图谱增强、生产级K8s部署的完整企业智能问答平台

3. ------

4. ## 一、Phase 4 任务分解总览

5. text

6. 

7. ```
   Phase 4 多智能体 & 高级能力 (4-6周)
   │
   ├── Week 15-16: 多智能体编排系统
   │   ├── 15.1 Supervisor Agent 设计与实现
   │   ├── 15.2 专家 Agent 集群 (RAG / Tool / Analyst / Critic)
   │   ├── 15.3 Agent 协作模式 (顺序/并行/委托)
   │   ├── 15.4 Agent 竞争模式 (多策略竞赛)
   │   ├── 15.5 辩论机制 (正方/反方/裁判)
   │   ├── 15.6 投票与共识机制
   │   └── 15.7 多Agent子图嵌入主图
   │
   ├── Week 17: 知识图谱 & Agentic Chunking
   │   ├── 17.1 Neo4j 部署与集成
   │   ├── 17.2 实体关系自动提取
   │   ├── 17.3 知识图谱检索器 (KG Retriever)
   │   ├── 17.4 语义记忆层 (第四层记忆)
   │   ├── 17.5 Agentic Chunking (LLM智能分块)
   │   └── 17.6 三路召回融合 (Dense + Sparse + KG)
   │
   ├── Week 18: 反馈闭环 & Prompt 版本管理
   │   ├── 18.1 反馈驱动的RAG优化管道
   │   ├── 18.2 负反馈自动分析与告警
   │   ├── 18.3 Prompt 版本管理系统
   │   ├── 18.4 Prompt A/B 测试框架
   │   ├── 18.5 自动化评估定时任务
   │   └── 18.6 质量趋势报告
   │
   └── Week 19-20: Kubernetes 生产部署 & 稳定化
       ├── 19.1 Helm Chart 编写
       ├── 19.2 Milvus 分布式集群部署
       ├── 19.3 HPA 自动伸缩
       ├── 19.4 CI/CD 流水线
       ├── 19.5 蓝绿/金丝雀发布
       ├── 19.6 全链路压力测试
       └── 19.7 灾备与数据备份
   ```

8. ------

9. ## 二、新增/变更的目录结构

10. text

11. 

12. ```
    src/
    ├── core/
    │   ├── agents/                           # [新增] 多智能体系统
    │   │   ├── __init__.py
    │   │   ├── base.py                       # Agent基类
    │   │   ├── supervisor.py                 # 主管Agent
    │   │   ├── specialists/
    │   │   │   ├── __init__.py
    │   │   │   ├── rag_specialist.py         # RAG专家
    │   │   │   ├── tool_specialist.py        # 工具专家
    │   │   │   ├── analyst.py               # 分析专家
    │   │   │   └── critic.py                # 批评家/质量审查
    │   │   ├── competition/
    │   │   │   ├── __init__.py
    │   │   │   ├── strategy_runner.py        # 多策略竞赛
    │   │   │   ├── debate.py                # 辩论机制
    │   │   │   ├── voting.py               # 投票/共识
    │   │   │   └── judge.py                # 裁判Agent
    │   │   └── graph.py                      # 多Agent子图定义
    │   ├── rag/
    │   │   ├── ingestion/
    │   │   │   ├── agentic_chunker.py       # [新增] LLM智能分块
    │   │   │   └── ...
    │   │   ├── retrieval/
    │   │   │   ├── kg_retriever.py          # [新增] 知识图谱检索
    │   │   │   ├── hybrid.py               # [增强] 三路融合
    │   │   │   └── ...
    │   │   └── ...
    │   ├── memory/
    │   │   ├── semantic_memory.py           # [新增] 语义记忆(KG)
    │   │   ├── manager.py                   # [增强] 四层融合
    │   │   └── ...
    │   ├── knowledge_graph/                  # [新增] 知识图谱模块
    │   │   ├── __init__.py
    │   │   ├── neo4j_client.py
    │   │   ├── entity_extractor.py
    │   │   └── graph_builder.py
    │   ├── prompt_management/               # [新增] Prompt版本管理
    │   │   ├── __init__.py
    │   │   ├── registry.py
    │   │   ├── versioning.py
    │   │   ├── ab_testing.py
    │   │   └── templates/
    │   │       ├── rag_system.py
    │   │       ├── query_rewrite.py
    │   │       └── ...
    │   └── feedback/                         # [新增] 反馈闭环
    │       ├── __init__.py
    │       ├── analyzer.py
    │       ├── optimizer.py
    │       └── scheduler.py
    ├── infra/
    │   ├── database/
    │   │   ├── neo4j_client.py              # [新增]
    │   │   └── ...
    │   └── ...
    ├── deploy/                               # [新增] K8s部署
    │   ├── helm/
    │   │   └── qa-assistant/
    │   │       ├── Chart.yaml
    │   │       ├── values.yaml
    │   │       ├── values-prod.yaml
    │   │       └── templates/
    │   │           ├── api-deployment.yaml
    │   │           ├── api-service.yaml
    │   │           ├── api-hpa.yaml
    │   │           ├── worker-deployment.yaml
    │   │           ├── configmap.yaml
    │   │           ├── secrets.yaml
    │   │           └── ingress.yaml
    │   ├── ci/
    │   │   ├── Dockerfile.api.prod
    │   │   ├── Dockerfile.worker.prod
    │   │   └── .github/
    │   │       └── workflows/
    │   │           ├── ci.yml
    │   │           └── cd.yml
    │   └── scripts/
    │       ├── deploy.sh
    │       ├── rollback.sh
    │       └── backup.sh
    └── ...
    ```

13. ### 新增依赖

14. toml

15. 

16. ```
    # pyproject.toml Phase 4 新增
    
    # === 知识图谱 ===
    neo4j = "^5.25.0"
    
    # === 多Agent (暂时不引入AutoGen/CrewAI, 用LangGraph原生实现) ===
    # langgraph已有, 无需额外依赖
    
    # === 定时任务 ===
    apscheduler = "^3.10.0"
    
    # === K8s客户端 (可选, 运维脚本用) ===
    # kubernetes = "^30.0.0"
    ```

17. ### Docker Compose 新增

18. YAML

19. 

20. ```
    # docker/docker-compose.yml Phase 4 新增
    
      # ============================================================
      # Neo4j - 知识图谱
      # ============================================================
      neo4j:
        image: neo4j:5.24-community
        container_name: qa-neo4j
        ports:
          - "7474:7474"    # Web UI
          - "7687:7687"    # Bolt协议
        environment:
          NEO4J_AUTH: neo4j/password123
          NEO4J_PLUGINS: '["apoc"]'
          NEO4J_dbms_memory_heap_max__size: 1G
        volumes:
          - neo4j_data:/data
        healthcheck:
          test: ["CMD-SHELL", "neo4j status || exit 1"]
          interval: 30s
          timeout: 10s
          retries: 5
        networks:
          - qa-network
    
    volumes:
      neo4j_data:
    ```

21. SQL

22. 

23. ```
    -- docker/configs/postgres/04-phase4-init.sql
    
    -- Prompt版本管理表
    CREATE TABLE IF NOT EXISTS prompt_versions (
        id              VARCHAR(64) PRIMARY KEY,
        prompt_name     VARCHAR(128) NOT NULL,
        version         INTEGER NOT NULL,
        content         TEXT NOT NULL,
        variables       JSONB DEFAULT '[]',
        description     TEXT,
        status          VARCHAR(32) DEFAULT 'draft',  -- draft / active / archived / ab_testing
        metrics         JSONB DEFAULT '{}',
        created_by      VARCHAR(64),
        created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        activated_at    TIMESTAMP WITH TIME ZONE,
        UNIQUE(prompt_name, version)
    );
    
    CREATE INDEX idx_prompt_name_status ON prompt_versions(prompt_name, status);
    
    -- A/B测试表
    CREATE TABLE IF NOT EXISTS ab_tests (
        id              VARCHAR(64) PRIMARY KEY,
        name            VARCHAR(256) NOT NULL,
        prompt_name     VARCHAR(128) NOT NULL,
        variant_a_id    VARCHAR(64) REFERENCES prompt_versions(id),
        variant_b_id    VARCHAR(64) REFERENCES prompt_versions(id),
        traffic_split   FLOAT DEFAULT 0.5,  -- A的流量占比
        status          VARCHAR(32) DEFAULT 'running',  -- running / completed / cancelled
        results         JSONB DEFAULT '{}',
        start_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        end_at          TIMESTAMP WITH TIME ZONE,
        created_by      VARCHAR(64)
    );
    
    -- A/B测试样本记录
    CREATE TABLE IF NOT EXISTS ab_test_samples (
        id              BIGSERIAL PRIMARY KEY,
        test_id         VARCHAR(64) REFERENCES ab_tests(id),
        variant         VARCHAR(1) NOT NULL,  -- A / B
        session_id      VARCHAR(64),
        prompt_version_id VARCHAR(64),
        query           TEXT,
        answer          TEXT,
        confidence      FLOAT,
        feedback_type   VARCHAR(16),  -- thumbs_up / thumbs_down / null
        latency_ms      FLOAT,
        created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE INDEX idx_ab_samples_test ON ab_test_samples(test_id);
    
    -- 反馈分析报告表
    CREATE TABLE IF NOT EXISTS feedback_analysis_reports (
        id              VARCHAR(64) PRIMARY KEY,
        period_start    TIMESTAMP WITH TIME ZONE,
        period_end      TIMESTAMP WITH TIME ZONE,
        total_feedback  INTEGER,
        positive_count  INTEGER,
        negative_count  INTEGER,
        top_issues      JSONB DEFAULT '[]',
        recommendations JSONB DEFAULT '[]',
        auto_actions    JSONB DEFAULT '[]',
        created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Agent执行记录表
    CREATE TABLE IF NOT EXISTS agent_execution_logs (
        id              BIGSERIAL PRIMARY KEY,
        session_id      VARCHAR(64),
        agent_name      VARCHAR(128),
        agent_role      VARCHAR(64),
        input_summary   TEXT,
        output_summary  TEXT,
        confidence      FLOAT,
        latency_ms      FLOAT,
        tokens_used     INTEGER,
        metadata        JSONB DEFAULT '{}',
        created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    CREATE INDEX idx_agent_logs_session ON agent_execution_logs(session_id);
    CREATE INDEX idx_agent_logs_agent ON agent_execution_logs(agent_name);
    ```

24. ------

25. ## 三、Week 15-16：多智能体编排系统

26. ### 3.1 Agent 基类

27. Python

28. 

29. ```
    # src/core/agents/base.py
    
    import time
    from abc import ABC, abstractmethod
    from dataclasses import dataclass, field
    from typing import Any
    import structlog
    
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    
    from src.infra.config.settings import get_settings
    
    logger = structlog.get_logger()
    
    
    @dataclass
    class AgentOutput:
        """Agent 执行结果"""
        agent_name: str
        answer: str = ""
        confidence: float = 0.0
        reasoning: str = ""
        evidence: list[str] = field(default_factory=list)
        citations: list[dict] = field(default_factory=list)
        metadata: dict = field(default_factory=dict)
        tokens_used: int = 0
        latency_ms: float = 0
    
    
    class BaseAgent(ABC):
        """
        Agent 基类
    
        所有专家Agent继承此类, 实现统一的接口:
        - execute(): 执行核心逻辑
        - get_system_prompt(): 返回系统提示
        """
    
        def __init__(
            self,
            name: str,
            role: str,
            llm: ChatOpenAI | None = None,
        ):
            self.name = name
            self.role = role
            settings = get_settings()
            self.llm = llm or ChatOpenAI(
                model=settings.PRIMARY_LLM_MODEL,
                temperature=0.1,
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
                base_url=settings.OPENAI_API_BASE,
                timeout=settings.LLM_TIMEOUT,
            )
    
        @abstractmethod
        async def execute(
            self,
            query: str,
            context: dict,
            **kwargs,
        ) -> AgentOutput:
            """执行Agent核心逻辑"""
            ...
    
        @abstractmethod
        def get_system_prompt(self) -> str:
            """获取系统提示"""
            ...
    
        async def _call_llm(
            self,
            system_prompt: str,
            user_message: str,
            history: list | None = None,
            response_format: dict | None = None,
        ) -> tuple[str, int]:
            """封装LLM调用"""
            messages = [SystemMessage(content=system_prompt)]
    
            if history:
                for msg in history[-6:]:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    else:
                        messages.append(AIMessage(content=msg["content"]))
    
            messages.append(HumanMessage(content=user_message))
    
            kwargs = {}
            if response_format:
                kwargs["response_format"] = response_format
    
            response = await self.llm.ainvoke(messages, **kwargs)
    
            tokens = 0
            if response.usage_metadata:
                tokens = response.usage_metadata.get("total_tokens", 0)
    
            return response.content, tokens
    
        async def run_with_tracking(
            self,
            query: str,
            context: dict,
            **kwargs,
        ) -> AgentOutput:
            """带追踪的执行入口"""
            start_time = time.perf_counter()
    
            try:
                result = await self.execute(query, context, **kwargs)
                result.latency_ms = (time.perf_counter() - start_time) * 1000
                result.agent_name = self.name
    
                logger.info(
                    "agent_executed",
                    agent=self.name,
                    role=self.role,
                    confidence=result.confidence,
                    latency_ms=round(result.latency_ms, 2),
                    tokens=result.tokens_used,
                )
    
                # 持久化执行记录
                await self._log_execution(query, result, context)
    
                return result
    
            except Exception as e:
                elapsed = (time.perf_counter() - start_time) * 1000
                logger.error(
                    "agent_execution_failed",
                    agent=self.name,
                    error=str(e),
                    latency_ms=round(elapsed, 2),
                )
                return AgentOutput(
                    agent_name=self.name,
                    answer=f"[{self.name}] 执行出错: {str(e)}",
                    confidence=0.0,
                    latency_ms=elapsed,
                )
    
        async def _log_execution(self, query: str, result: AgentOutput, context: dict):
            """记录Agent执行日志"""
            try:
                from src.infra.database.postgres import get_postgres_pool
                pool = await get_postgres_pool()
                await pool.execute(
                    """INSERT INTO agent_execution_logs
                       (session_id, agent_name, agent_role, input_summary,
                        output_summary, confidence, latency_ms, tokens_used, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                    context.get("session_id", ""),
                    self.name,
                    self.role,
                    query[:500],
                    result.answer[:500],
                    result.confidence,
                    result.latency_ms,
                    result.tokens_used,
                    "{}",
                )
            except Exception:
                pass  # 日志记录失败不影响主流程
    ```

30. ### 3.2 专家 Agent 集群

31. Python

32. 

33. ```
    # src/core/agents/specialists/rag_specialist.py
    
    import json
    from src.core.agents.base import BaseAgent, AgentOutput
    from src.core.rag.retrieval.retriever import RAGRetriever
    from src.core.rag.synthesis.citation import CitationExtractor
    
    
    class RAGSpecialist(BaseAgent):
        """
        RAG 专家 Agent
    
        职责:
        1. 从知识库检索最相关的信息
        2. 基于检索结果生成准确答案
        3. 标注引用来源
        4. 自我评估回答质量
        """
    
        def __init__(self, retriever: RAGRetriever, **kwargs):
            super().__init__(
                name="rag_specialist",
                role="知识检索与回答专家",
                **kwargs,
            )
            self.retriever = retriever
            self.citation_extractor = CitationExtractor()
    
        def get_system_prompt(self) -> str:
            return """你是一个知识检索与回答专家。你的任务是:
    
    1. 严格基于提供的参考资料回答问题
    2. 使用 [来源X] 标注引用
    3. 如果参考资料不足以回答问题, 诚实说明
    4. 评估你的回答置信度 (0-1)
    
    回答格式:
    - 先给出回答
    - 然后在末尾标注: [置信度: X.X]
    - 如果信息不足, 说明缺少什么信息"""
    
        async def execute(
            self,
            query: str,
            context: dict,
            **kwargs,
        ) -> AgentOutput:
            """执行RAG检索+回答"""
            collection = context.get("collection", "default")
            expanded_queries = context.get("expanded_queries", [])
    
            # 检索
            chunks = await self.retriever.retrieve(
                query=query,
                collection=collection,
                top_k=5,
                expanded_queries=expanded_queries,
            )
    
            if not chunks:
                return AgentOutput(
                    agent_name=self.name,
                    answer="根据知识库检索, 未找到相关信息。",
                    confidence=0.1,
                    evidence=[],
                )
    
            # 构建上下文
            context_parts = []
            for i, chunk in enumerate(chunks, 1):
                context_parts.append(
                    f"[来源{i}] (文档: {chunk.doc_title}, 相关度: {chunk.score:.2f})\n{chunk.content}"
                )
            context_text = "\n\n---\n\n".join(context_parts)
    
            # 生成答案
            user_prompt = f"""参考资料:
    {context_text}
    
    用户问题: {query}
    
    请基于参考资料回答问题, 标注引用来源, 并在末尾标注置信度。"""
    
            answer, tokens = await self._call_llm(
                system_prompt=self.get_system_prompt(),
                user_message=user_prompt,
                history=context.get("history"),
            )
    
            # 提取置信度
            confidence = self._extract_confidence(answer)
    
            # 提取引用
            answer_clean, citations = self.citation_extractor.extract_citations(
                answer, chunks
            )
    
            return AgentOutput(
                agent_name=self.name,
                answer=answer_clean,
                confidence=confidence,
                evidence=[c.content for c in chunks[:3]],
                citations=[c.model_dump() for c in citations],
                tokens_used=tokens,
                metadata={
                    "num_chunks_retrieved": len(chunks),
                    "top_score": chunks[0].score if chunks else 0,
                },
            )
    
        def _extract_confidence(self, answer: str) -> float:
            """从回答中提取自评置信度"""
            import re
            match = re.search(r'\[置信度[：:]\s*([\d.]+)\]', answer)
            if match:
                try:
                    return min(1.0, max(0.0, float(match.group(1))))
                except ValueError:
                    pass
            return 0.5
    ```

34. Python

35. 

36. ```
    # src/core/agents/specialists/analyst.py
    
    import json
    from src.core.agents.base import BaseAgent, AgentOutput
    
    
    class AnalystAgent(BaseAgent):
        """
        分析专家 Agent
    
        职责:
        1. 对复杂问题进行深度推理分析
        2. 综合多个信息源得出结论
        3. 提供结构化的分析报告
        4. 识别信息中的矛盾和不一致
        """
    
        def __init__(self, **kwargs):
            super().__init__(
                name="analyst",
                role="深度分析与推理专家",
                **kwargs,
            )
    
        def get_system_prompt(self) -> str:
            return """你是一个深度分析与推理专家。你的任务是:
    
    1. 对问题进行多角度分析
    2. 识别信息之间的关联和矛盾
    3. 进行逻辑推理得出结论
    4. 提供结构化的分析结果
    
    分析框架:
    - 问题分解: 将复杂问题拆分为子问题
    - 信息整合: 综合不同来源的信息
    - 逻辑推理: 基于证据推导结论
    - 不确定性标注: 标明哪些结论是确定的, 哪些是推测"""
    
        async def execute(
            self,
            query: str,
            context: dict,
            **kwargs,
        ) -> AgentOutput:
            """执行深度分析"""
            other_agent_outputs = context.get("agent_outputs", {})
    
            # 整合其他Agent的输出
            evidence_text = ""
            if other_agent_outputs:
                parts = []
                for agent_name, output in other_agent_outputs.items():
                    if isinstance(output, dict):
                        parts.append(
                            f"[{agent_name}的回答] (置信度: {output.get('confidence', 'N/A')})\n"
                            f"{output.get('answer', '')[:500]}"
                        )
                evidence_text = "\n\n---\n\n".join(parts)
    
            user_prompt = f"""问题: {query}
    
    已收集的信息:
    {evidence_text if evidence_text else '(暂无其他Agent的输出)'}
    
    请进行深度分析:
    1. 分析问题的各个方面
    2. 指出已有信息中的关键要点
    3. 识别可能的信息缺口或矛盾
    4. 给出你的综合分析结论
    
    以JSON格式输出:
    {{"analysis": "分析过程", "conclusion": "结论", "gaps": ["信息缺口"], "confidence": 0.X}}"""
    
            answer, tokens = await self._call_llm(
                system_prompt=self.get_system_prompt(),
                user_message=user_prompt,
                response_format={"type": "json_object"},
            )
    
            try:
                result = json.loads(answer)
                return AgentOutput(
                    agent_name=self.name,
                    answer=result.get("conclusion", answer),
                    confidence=result.get("confidence", 0.5),
                    reasoning=result.get("analysis", ""),
                    evidence=result.get("gaps", []),
                    tokens_used=tokens,
                )
            except json.JSONDecodeError:
                return AgentOutput(
                    agent_name=self.name,
                    answer=answer,
                    confidence=0.5,
                    tokens_used=tokens,
                )
    ```

37. Python

38. 

39. ```
    # src/core/agents/specialists/critic.py
    
    import json
    from src.core.agents.base import BaseAgent, AgentOutput
    
    
    class CriticAgent(BaseAgent):
        """
        批评家 Agent
    
        职责:
        1. 审查其他Agent的回答质量
        2. 检测事实错误和逻辑漏洞
        3. 识别幻觉和偏见
        4. 提出改进建议
        """
    
        def __init__(self, **kwargs):
            super().__init__(
                name="critic",
                role="质量审查与批判专家",
                **kwargs,
            )
    
        def get_system_prompt(self) -> str:
            return """你是一个严格的质量审查专家。你的任务是:
    
    1. 批判性地审查给定的回答
    2. 检测可能的事实错误
    3. 识别逻辑漏洞和不一致之处
    4. 检查是否存在幻觉 (不被证据支持的声明)
    5. 评估回答的完整性
    
    你的审查必须:
    - 客观公正, 基于证据
    - 指出具体问题, 不泛泛而谈
    - 给出改进建议
    - 对回答质量打分 (0-1)"""
    
        async def execute(
            self,
            query: str,
            context: dict,
            **kwargs,
        ) -> AgentOutput:
            """审查回答质量"""
            answer_to_review = kwargs.get("answer_to_review", "")
            evidence = kwargs.get("evidence", [])
            agent_name = kwargs.get("source_agent", "unknown")
    
            user_prompt = f"""原始问题: {query}
    
    待审查的回答 (来自 {agent_name}):
    {answer_to_review}
    
    参考证据:
    {chr(10).join(f'- {e[:300]}' for e in evidence[:5]) if evidence else '(无参考证据)'}
    
    请严格审查此回答:
    1. 是否存在事实错误?
    2. 是否有逻辑漏洞?
    3. 是否存在幻觉 (不被证据支持的声明)?
    4. 回答是否完整, 有无遗漏?
    5. 总体质量评分 (0-1)
    
    以JSON格式输出:
    {{
        "issues": ["问题1", "问题2"],
        "hallucinations": ["幻觉声明1"],
        "missing_info": ["遗漏信息1"],
        "suggestions": ["改进建议1"],
        "quality_score": 0.X,
        "verdict": "accept / revise / reject"
    }}"""
    
            answer, tokens = await self._call_llm(
                system_prompt=self.get_system_prompt(),
                user_message=user_prompt,
                response_format={"type": "json_object"},
            )
    
            try:
                result = json.loads(answer)
                verdict = result.get("verdict", "accept")
                quality = result.get("quality_score", 0.5)
    
                return AgentOutput(
                    agent_name=self.name,
                    answer=json.dumps(result, ensure_ascii=False),
                    confidence=quality,
                    reasoning=f"Verdict: {verdict}",
                    evidence=result.get("issues", []) + result.get("hallucinations", []),
                    tokens_used=tokens,
                    metadata={
                        "verdict": verdict,
                        "issues_count": len(result.get("issues", [])),
                        "hallucinations_count": len(result.get("hallucinations", [])),
                        "suggestions": result.get("suggestions", []),
                    },
                )
            except json.JSONDecodeError:
                return AgentOutput(
                    agent_name=self.name,
                    answer=answer,
                    confidence=0.5,
                    tokens_used=tokens,
                )
    ```

40. ### 3.3 Supervisor Agent

41. Python

42. 

43. ```
    # src/core/agents/supervisor.py
    
    import json
    import asyncio
    import structlog
    from pydantic import BaseModel, Field
    
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    
    from src.core.agents.base import BaseAgent, AgentOutput
    from src.infra.config.settings import get_settings
    
    logger = structlog.get_logger()
    
    
    class SupervisorDecision(BaseModel):
        """Supervisor 决策"""
        next_action: str = Field(
            description="下一步操作: delegate / parallel / debate / synthesize / done"
        )
        target_agents: list[str] = Field(
            default_factory=list,
            description="目标Agent列表",
        )
        sub_tasks: list[str] = Field(
            default_factory=list,
            description="分解的子任务",
        )
        reasoning: str = Field(default="", description="决策理由")
    
    
    SUPERVISOR_PROMPT = """你是一个智能任务调度主管 (Supervisor)。你管理一个专家团队来回答用户的问题。
    
    ## 你的专家团队
    
    {agent_descriptions}
    
    ## 你的职责
    
    1. **分析任务**: 理解用户问题的复杂度和类型
    2. **调度策略**: 选择最合适的处理方式:
       - `delegate`: 将任务委托给单个最合适的专家
       - `parallel`: 让多个专家并行处理, 各自发挥优势
       - `debate`: 对于争议性或高风险问题, 启动辩论机制
       - `synthesize`: 已有足够信息, 可以合成最终答案
       - `done`: 任务已完成
    
    3. **质量控制**: 审查专家们的输出质量, 决定是否需要进一步处理
    
    ## 当前状态
    
    用户问题: {query}
    已完成的专家输出: {agent_outputs}
    当前迭代: {iteration}/{max_iterations}
    
    ## 决策规则
    
    - 简单事实问题 → delegate 给 rag_specialist
    - 需要计算/工具 → delegate 给 tool_specialist
    - 复杂分析问题 → parallel (rag_specialist + analyst)
    - 答案质量存疑 → debate (让critic审查)
    - 信息充分 → synthesize
    - 迭代达上限 → synthesize (强制结束)
    
    请以JSON格式输出你的决策。"""
    
    
    class SupervisorAgent:
        """
        主管 Agent - 多智能体系统的调度中心
    
        职责:
        1. 分析任务复杂度
        2. 选择协作策略 (委托/并行/辩论)
        3. 分配子任务给专家
        4. 监督执行质量
        5. 决定何时结束 (synthesize)
        """
    
        def __init__(
            self,
            agents: dict[str, BaseAgent],
            max_iterations: int = 5,
        ):
            self.agents = agents
            self.max_iterations = max_iterations
            settings = get_settings()
            self.llm = ChatOpenAI(
                model=settings.PRIMARY_LLM_MODEL,
                temperature=0.0,
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
                base_url=settings.OPENAI_API_BASE,
            )
    
        async def decide(
            self,
            query: str,
            agent_outputs: dict[str, AgentOutput],
            iteration: int,
        ) -> SupervisorDecision:
            """做出调度决策"""
    
            # 强制终止条件
            if iteration >= self.max_iterations:
                return SupervisorDecision(
                    next_action="synthesize",
                    reasoning="达到最大迭代次数, 强制合成答案",
                )
    
            # 如果已有高质量答案, 直接结束
            for name, output in agent_outputs.items():
                if output.confidence >= 0.9 and name == "rag_specialist":
                    return SupervisorDecision(
                        next_action="done",
                        reasoning=f"{name} 已给出高置信度回答 ({output.confidence})",
                    )
    
            # LLM决策
            agent_descriptions = "\n".join(
                f"- {name} ({agent.role})" for name, agent in self.agents.items()
            )
    
            outputs_summary = {}
            for name, output in agent_outputs.items():
                outputs_summary[name] = {
                    "answer": output.answer[:200],
                    "confidence": output.confidence,
                    "reasoning": output.reasoning[:100],
                }
    
            response = await self.llm.ainvoke(
                [
                    SystemMessage(content=SUPERVISOR_PROMPT.format(
                        agent_descriptions=agent_descriptions,
                        query=query,
                        agent_outputs=json.dumps(outputs_summary, ensure_ascii=False) if outputs_summary else "(暂无)",
                        iteration=iteration,
                        max_iterations=self.max_iterations,
                    )),
                ],
                response_format={"type": "json_object"},
            )
    
            try:
                decision = SupervisorDecision.model_validate_json(response.content)
            except Exception:
                decision = SupervisorDecision(
                    next_action="delegate",
                    target_agents=["rag_specialist"],
                    reasoning="决策解析失败, 默认使用RAG专家",
                )
    
            logger.info(
                "supervisor_decision",
                action=decision.next_action,
                targets=decision.target_agents,
                iteration=iteration,
                reasoning=decision.reasoning[:200],
            )
    
            return decision
    
        async def execute_agents(
            self,
            decision: SupervisorDecision,
            query: str,
            context: dict,
            agent_outputs: dict[str, AgentOutput],
        ) -> dict[str, AgentOutput]:
            """根据决策执行Agent"""
    
            if decision.next_action == "delegate":
                # 委托给单个Agent
                for agent_name in decision.target_agents:
                    if agent_name in self.agents:
                        output = await self.agents[agent_name].run_with_tracking(
                            query=query,
                            context={**context, "agent_outputs": {
                                k: v.__dict__ for k, v in agent_outputs.items()
                            }},
                        )
                        agent_outputs[agent_name] = output
    
            elif decision.next_action == "parallel":
                # 并行执行多个Agent
                tasks = []
                target_names = []
                for agent_name in decision.target_agents:
                    if agent_name in self.agents:
                        tasks.append(
                            self.agents[agent_name].run_with_tracking(
                                query=query,
                                context={**context, "agent_outputs": {
                                    k: v.__dict__ for k, v in agent_outputs.items()
                                }},
                            )
                        )
                        target_names.append(agent_name)
    
                results = await asyncio.gather(*tasks, return_exceptions=True)
    
                for name, result in zip(target_names, results):
                    if isinstance(result, Exception):
                        logger.error("parallel_agent_failed", agent=name, error=str(result))
                        agent_outputs[name] = AgentOutput(
                            agent_name=name,
                            answer=f"[{name}] 执行失败",
                            confidence=0,
                        )
                    else:
                        agent_outputs[name] = result
    
            elif decision.next_action == "debate":
                # 启动辩论 (由外部 debate 模块处理)
                pass
    
            return agent_outputs
    
        async def synthesize(
            self,
            query: str,
            agent_outputs: dict[str, AgentOutput],
            context: dict,
        ) -> AgentOutput:
            """合成最终答案"""
            outputs_text = ""
            all_citations = []
            total_tokens = 0
    
            for name, output in agent_outputs.items():
                outputs_text += (
                    f"\n[{name}] (置信度: {output.confidence:.2f})\n"
                    f"{output.answer}\n"
                )
                all_citations.extend(output.citations)
                total_tokens += output.tokens_used
    
            synthesis_prompt = f"""综合以下专家的回答, 生成最终的、高质量的回答。
    
    用户问题: {query}
    
    各专家回答:
    {outputs_text}
    
    要求:
    1. 综合各专家的观点, 取其精华
    2. 优先采用高置信度专家的回答
    3. 如有矛盾, 以证据更充分的为准
    4. 保持引用标注
    5. 给出最终答案的综合置信度"""
    
            final_answer, tokens = await self.llm.ainvoke(
                [HumanMessage(content=synthesis_prompt)],
            ), 0
    
            if hasattr(final_answer, 'content'):
                answer_text = final_answer.content
            else:
                answer_text = str(final_answer)
    
            # 计算综合置信度 (加权平均)
            if agent_outputs:
                weights = {name: o.confidence for name, o in agent_outputs.items()}
                total_weight = sum(weights.values()) or 1
                avg_confidence = sum(
                    o.confidence * o.confidence for o in agent_outputs.values()
                ) / total_weight
            else:
                avg_confidence = 0
    
            return AgentOutput(
                agent_name="supervisor_synthesis",
                answer=answer_text,
                confidence=min(1.0, avg_confidence),
                citations=all_citations,
                tokens_used=total_tokens + tokens,
                metadata={
                    "agents_involved": list(agent_outputs.keys()),
                    "agent_confidences": {
                        k: v.confidence for k, v in agent_outputs.items()
                    },
                },
            )
    ```

44. ### 3.4 辩论机制

45. Python

46. 

47. ```
    # src/core/agents/competition/debate.py
    
    import json
    import asyncio
    import structlog
    from dataclasses import dataclass, field
    from pydantic import BaseModel, Field
    
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    
    from src.core.agents.base import AgentOutput
    from src.infra.config.settings import get_settings
    
    logger = structlog.get_logger()
    
    
    @dataclass
    class DebateRound:
        """辩论轮次"""
        round_number: int
        proponent_argument: str       # 正方论点
        opponent_argument: str        # 反方论点
        proponent_confidence: float = 0.5
        opponent_confidence: float = 0.5
    
    
    class JudgeVerdict(BaseModel):
        """裁判裁决"""
        winner: str = Field(description="proponent / opponent / draw")
        final_answer: str = Field(description="综合最佳答案")
        confidence: float = Field(ge=0, le=1)
        reasoning: str = Field(default="")
        key_arguments: list[str] = Field(default_factory=list)
    
    
    class DebateArena:
        """
        辩论场
    
        机制:
        1. 正方 (Proponent): 支持当前最佳答案
        2. 反方 (Opponent): 质疑和挑战
        3. 多轮辩论 (2-3轮)
        4. 裁判 (Judge) 最终裁决
    
        适用场景:
        - 答案置信度中等 (0.4-0.7)
        - 多个Agent给出不同答案
        - 争议性或高风险问题
        """
    
        def __init__(self, max_rounds: int = 3):
            self.max_rounds = max_rounds
            settings = get_settings()
            self.llm = ChatOpenAI(
                model=settings.PRIMARY_LLM_MODEL,
                temperature=0.3,  # 稍高温度, 鼓励多样性
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
                base_url=settings.OPENAI_API_BASE,
            )
            self.judge_llm = ChatOpenAI(
                model=settings.PRIMARY_LLM_MODEL,
                temperature=0.0,
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
                base_url=settings.OPENAI_API_BASE,
            )
    
        async def debate(
            self,
            query: str,
            initial_answer: str,
            evidence: list[str],
            context: dict | None = None,
        ) -> AgentOutput:
            """执行完整辩论流程"""
    
            logger.info("debate_started", query=query[:100])
    
            rounds: list[DebateRound] = []
    
            for round_num in range(1, self.max_rounds + 1):
                # 正方论证
                proponent_arg = await self._proponent_argue(
                    query=query,
                    current_answer=initial_answer,
                    evidence=evidence,
                    previous_rounds=rounds,
                )
    
                # 反方论证
                opponent_arg = await self._opponent_argue(
                    query=query,
                    current_answer=initial_answer,
                    evidence=evidence,
                    proponent_argument=proponent_arg,
                    previous_rounds=rounds,
                )
    
                round_data = DebateRound(
                    round_number=round_num,
                    proponent_argument=proponent_arg,
                    opponent_argument=opponent_arg,
                )
                rounds.append(round_data)
    
                logger.info(
                    "debate_round_completed",
                    round=round_num,
                    query=query[:100],
                )
    
                # 检查是否已达成共识 (正反方观点趋同)
                if await self._check_consensus(rounds):
                    logger.info("debate_consensus_reached", round=round_num)
                    break
    
            # 裁判裁决
            verdict = await self._judge(query, initial_answer, evidence, rounds)
    
            logger.info(
                "debate_completed",
                rounds=len(rounds),
                winner=verdict.winner,
                confidence=verdict.confidence,
            )
    
            return AgentOutput(
                agent_name="debate_arena",
                answer=verdict.final_answer,
                confidence=verdict.confidence,
                reasoning=verdict.reasoning,
                evidence=verdict.key_arguments,
                metadata={
                    "debate_rounds": len(rounds),
                    "winner": verdict.winner,
                    "round_details": [
                        {
                            "round": r.round_number,
                            "proponent": r.proponent_argument[:200],
                            "opponent": r.opponent_argument[:200],
                        }
                        for r in rounds
                    ],
                },
            )
    
        async def _proponent_argue(
            self,
            query: str,
            current_answer: str,
            evidence: list[str],
            previous_rounds: list[DebateRound],
        ) -> str:
            """正方论证"""
            prev_text = ""
            if previous_rounds:
                last = previous_rounds[-1]
                prev_text = f"\n反方上轮质疑: {last.opponent_argument}\n请针对性地反驳。"
    
            evidence_text = "\n".join(f"- {e[:300]}" for e in evidence[:5])
    
            prompt = f"""你是正方辩手。你需要支持并强化当前答案的正确性。
    
    问题: {query}
    当前答案: {current_answer}
    
    可用证据:
    {evidence_text}
    {prev_text}
    
    请给出你的论证:
    1. 为什么当前答案是正确的
    2. 引用具体证据支持
    3. 如果反方有质疑, 进行反驳"""
    
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
    
        async def _opponent_argue(
            self,
            query: str,
            current_answer: str,
            evidence: list[str],
            proponent_argument: str,
            previous_rounds: list[DebateRound],
        ) -> str:
            """反方论证"""
            evidence_text = "\n".join(f"- {e[:300]}" for e in evidence[:5])
    
            prompt = f"""你是反方辩手。你需要批判性地审视当前答案, 找出问题。
    
    问题: {query}
    当前答案: {current_answer}
    
    正方论点: {proponent_argument}
    
    可用证据:
    {evidence_text}
    
    请给出你的质疑:
    1. 当前答案可能存在的错误或遗漏
    2. 正方论证中的逻辑漏洞
    3. 是否有证据不支持的声明
    4. 如果你认为有更好的答案, 请提出"""
    
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content
    
        async def _judge(
            self,
            query: str,
            initial_answer: str,
            evidence: list[str],
            rounds: list[DebateRound],
        ) -> JudgeVerdict:
            """裁判裁决"""
            debate_log = ""
            for r in rounds:
                debate_log += (
                    f"\n--- 第{r.round_number}轮 ---\n"
                    f"正方: {r.proponent_argument}\n"
                    f"反方: {r.opponent_argument}\n"
                )
    
            evidence_text = "\n".join(f"- {e[:300]}" for e in evidence[:5])
    
            prompt = f"""你是公正的裁判。请根据辩论内容做出最终裁决。
    
    问题: {query}
    初始答案: {initial_answer}
    
    辩论记录:
    {debate_log}
    
    原始证据:
    {evidence_text}
    
    请裁决:
    1. 评估正反双方论点的有效性
    2. 确定哪方的论证更有说服力
    3. 综合给出最准确的最终答案
    4. 给出置信度评分
    
    以JSON格式输出:
    {{"winner": "proponent/opponent/draw", "final_answer": "...", "confidence": 0.X, "reasoning": "...", "key_arguments": ["..."]}}"""
    
            response = await self.judge_llm.ainvoke(
                [HumanMessage(content=prompt)],
                response_format={"type": "json_object"},
            )
    
            try:
                return JudgeVerdict.model_validate_json(response.content)
            except Exception:
                return JudgeVerdict(
                    winner="draw",
                    final_answer=initial_answer,
                    confidence=0.5,
                    reasoning="裁决解析失败, 使用原始答案",
                )
    
        async def _check_consensus(self, rounds: list[DebateRound]) -> bool:
            """检查正反方是否达成共识"""
            if len(rounds) < 2:
                return False
    
            # 简化判断: 如果反方最近的论点中包含"同意"类关键词
            last_opponent = rounds[-1].opponent_argument.lower()
            consensus_indicators = ["同意", "赞同", "确实如此", "没有异议", "正确", "agree"]
            return any(ind in last_opponent for ind in consensus_indicators)
    ```

48. ### 3.5 多策略竞赛

49. Python

50. 

51. ```
    # src/core/agents/competition/strategy_runner.py
    
    import asyncio
    import structlog
    from dataclasses import dataclass
    
    from src.core.agents.base import AgentOutput
    from src.core.agents.competition.judge import JudgeAgent
    
    logger = structlog.get_logger()
    
    
    @dataclass
    class StrategyResult:
        """策略执行结果"""
        strategy_name: str
        output: AgentOutput
        strategy_config: dict
    
    
    class StrategyCompetition:
        """
        多策略竞赛
    
        同一个问题用不同策略生成答案, 然后由Judge选出最佳:
    
        策略池:
        1. Standard RAG (标准检索+生成)
        2. Step-back RAG (先抽象再检索)
        3. Multi-query RAG (多查询扩展)
        4. Direct LLM (不检索, 直接用LLM知识)
        """
    
        def __init__(self, agents: dict, judge: "JudgeAgent"):
            self.agents = agents
            self.judge = judge
    
        async def compete(
            self,
            query: str,
            context: dict,
            strategies: list[str] | None = None,
        ) -> AgentOutput:
            """执行多策略竞赛"""
            strategies = strategies or ["standard_rag", "step_back", "multi_query"]
    
            logger.info(
                "competition_started",
                query=query[:100],
                strategies=strategies,
            )
    
            # 并行执行所有策略
            tasks = []
            strategy_names = []
    
            for strategy in strategies:
                if strategy in self.agents:
                    tasks.append(
                        self.agents[strategy].run_with_tracking(
                            query=query,
                            context={**context, "strategy": strategy},
                        )
                    )
                    strategy_names.append(strategy)
    
            results = await asyncio.gather(*tasks, return_exceptions=True)
    
            # 收集有效结果
            valid_results = []
            for name, result in zip(strategy_names, results):
                if isinstance(result, Exception):
                    logger.error("strategy_failed", strategy=name, error=str(result))
                elif result.confidence > 0.1:
                    valid_results.append(
                        StrategyResult(
                            strategy_name=name,
                            output=result,
                            strategy_config={},
                        )
                    )
    
            if not valid_results:
                return AgentOutput(
                    agent_name="competition",
                    answer="所有策略均未能生成有效回答",
                    confidence=0.0,
                )
    
            if len(valid_results) == 1:
                return valid_results[0].output
    
            # Judge评选
            winner = await self.judge.judge_candidates(
                query=query,
                candidates=valid_results,
            )
    
            logger.info(
                "competition_completed",
                winner=winner.agent_name,
                confidence=winner.confidence,
                strategies_tried=len(valid_results),
            )
    
            return winner
    ```

52. Python

53. 

54. ```
    # src/core/agents/competition/judge.py
    
    import json
    import structlog
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    
    from src.core.agents.base import AgentOutput
    from src.infra.config.settings import get_settings
    
    logger = structlog.get_logger()
    
    
    class JudgeAgent:
        """
        裁判 Agent
    
        评估多个候选答案, 选出最佳
        """
    
        def __init__(self):
            settings = get_settings()
            self.llm = ChatOpenAI(
                model=settings.PRIMARY_LLM_MODEL,
                temperature=0.0,
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
                base_url=settings.OPENAI_API_BASE,
            )
    
        async def judge_candidates(
            self,
            query: str,
            candidates: list,
        ) -> AgentOutput:
            """评估并选出最佳答案"""
    
            candidates_text = ""
            for i, c in enumerate(candidates, 1):
                output = c.output if hasattr(c, 'output') else c
                candidates_text += (
                    f"\n[候选{i}] (策略: {c.strategy_name if hasattr(c, 'strategy_name') else 'unknown'}, "
                    f"自评置信度: {output.confidence:.2f})\n"
                    f"{output.answer[:500]}\n"
                )
    
            prompt = f"""你是答案质量评估裁判。请评估以下候选答案。
    
    问题: {query}
    
    候选答案:
    {candidates_text}
    
    评估维度 (每项1-10分):
    1. 准确性: 答案是否正确
    2. 完整性: 是否覆盖问题所有方面
    3. 相关性: 是否切题
    4. 可读性: 表述是否清晰
    5. 引用质量: 是否有可靠来源
    
    以JSON输出:
    {{
        "best_index": 1,
        "scores": [
            {{"index": 1, "accuracy": 8, "completeness": 7, "relevancy": 9, "readability": 8, "citation": 7, "total": 39}},
            ...
        ],
        "reasoning": "选择理由"
    }}"""
    
            response = await self.llm.ainvoke(
                [HumanMessage(content=prompt)],
                response_format={"type": "json_object"},
            )
    
            try:
                result = json.loads(response.content)
                best_idx = result.get("best_index", 1) - 1  # 转0-based
                best_idx = max(0, min(best_idx, len(candidates) - 1))
    
                winner_candidate = candidates[best_idx]
                winner_output = winner_candidate.output if hasattr(winner_candidate, 'output') else winner_candidate
    
                # 用Judge的评分更新置信度
                scores = result.get("scores", [])
                if scores and best_idx < len(scores):
                    total = scores[best_idx].get("total", 0)
                    judge_confidence = total / 50.0  # 归一化到0-1
                else:
                    judge_confidence = winner_output.confidence
    
                return AgentOutput(
                    agent_name=f"judge_selected_{winner_candidate.strategy_name if hasattr(winner_candidate, 'strategy_name') else 'unknown'}",
                    answer=winner_output.answer,
                    confidence=judge_confidence,
                    citations=winner_output.citations,
                    reasoning=result.get("reasoning", ""),
                    tokens_used=winner_output.tokens_used,
                    metadata={
                        "judge_scores": scores,
                        "selected_strategy": winner_candidate.strategy_name if hasattr(winner_candidate, 'strategy_name') else "unknown",
                    },
                )
    
            except Exception as e:
                logger.error("judge_evaluation_failed", error=str(e))
                # 降级: 选置信度最高的
                best = max(candidates, key=lambda c: (c.output if hasattr(c, 'output') else c).confidence)
                return best.output if hasattr(best, 'output') else best
    ```

55. ### 3.6 投票与共识

56. Python

57. 

58. ```
    # src/core/agents/competition/voting.py
    
    import asyncio
    from collections import Counter
    import structlog
    
    from src.core.agents.base import BaseAgent, AgentOutput
    
    logger = structlog.get_logger()
    
    
    class VotingMechanism:
        """
        投票机制
    
        让多个Agent独立回答同一问题, 然后通过投票产生共识
    
        策略:
        1. 多数投票: 答案归类后选多数
        2. 加权投票: 按置信度加权
        3. 置信度聚合: 综合所有Agent的置信度
        """
    
        def __init__(self, agents: list[BaseAgent]):
            self.agents = agents
    
        async def vote(
            self,
            query: str,
            context: dict,
            method: str = "weighted",
        ) -> AgentOutput:
            """执行投票"""
    
            # 并行执行所有Agent
            tasks = [
                agent.run_with_tracking(query=query, context=context)
                for agent in self.agents
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
    
            valid_outputs = [
                r for r in results
                if not isinstance(r, Exception) and r.confidence > 0
            ]
    
            if not valid_outputs:
                return AgentOutput(
                    agent_name="voting",
                    answer="投票未能产生有效结果",
                    confidence=0.0,
                )
    
            if method == "weighted":
                return self._weighted_vote(valid_outputs)
            elif method == "majority":
                return self._majority_vote(valid_outputs)
            else:
                return self._confidence_aggregate(valid_outputs)
    
        def _weighted_vote(self, outputs: list[AgentOutput]) -> AgentOutput:
            """加权投票 - 按置信度选择"""
            # 选置信度最高的
            best = max(outputs, key=lambda o: o.confidence)
    
            # 综合置信度: 加权平均
            total_weight = sum(o.confidence for o in outputs)
            avg_confidence = total_weight / len(outputs) if outputs else 0
    
            return AgentOutput(
                agent_name="voting_weighted",
                answer=best.answer,
                confidence=min(1.0, (best.confidence + avg_confidence) / 2),
                citations=best.citations,
                reasoning=f"从{len(outputs)}个Agent中选出最佳 (置信度: {best.confidence:.2f})",
                metadata={
                    "voters": len(outputs),
                    "all_confidences": [o.confidence for o in outputs],
                    "winner": best.agent_name,
                },
            )
    
        def _confidence_aggregate(self, outputs: list[AgentOutput]) -> AgentOutput:
            """置信度聚合 - 所有回答的加权融合"""
            total_weight = sum(o.confidence for o in outputs) or 1
    
            # 选权重最高的作为主答案
            best = max(outputs, key=lambda o: o.confidence)
    
            # 聚合所有引用
            all_citations = []
            seen_docs = set()
            for o in outputs:
                for c in o.citations:
                    doc_id = c.get("doc_id", "")
                    if doc_id not in seen_docs:
                        all_citations.append(c)
                        seen_docs.add(doc_id)
    
            return AgentOutput(
                agent_name="voting_aggregated",
                answer=best.answer,
                confidence=sum(o.confidence ** 2 for o in outputs) / total_weight,
                citations=all_citations,
                metadata={
                    "voters": len(outputs),
                    "method": "confidence_aggregate",
                },
            )
    
        def _majority_vote(self, outputs: list[AgentOutput]) -> AgentOutput:
            """多数投票 (简化版: 选置信度中位数以上的共识)"""
            sorted_outputs = sorted(outputs, key=lambda o: o.confidence, reverse=True)
            top_half = sorted_outputs[:max(1, len(sorted_outputs) // 2)]
            best = top_half[0]
    
            return AgentOutput(
                agent_name="voting_majority",
                answer=best.answer,
                confidence=best.confidence,
                citations=best.citations,
            )
    ```

59. ### 3.7 多Agent子图 (嵌入主图)

60. Python

61. 

62. ```
    # src/core/agents/graph.py
    
    import asyncio
    import structlog
    from langchain_core.messages import AIMessage
    
    from src.core.orchestrator.state import ConversationState
    from src.core.agents.supervisor import SupervisorAgent
    from src.core.agents.base import AgentOutput
    from src.core.agents.competition.debate import DebateArena
    from src.core.agents.competition.voting import VotingMechanism
    
    logger = structlog.get_logger()
    
    
    class MultiAgentHubNode:
        """
        多智能体中心节点
    
        集成到主LangGraph图中, 作为"complex_task"意图的处理节点
    
        内部流程:
        1. Supervisor分析任务
        2. 根据决策执行Agent (委托/并行/辩论)
        3. 循环直到Supervisor决定synthesize
        4. 合成最终答案
        """
    
        def __init__(
            self,
            supervisor: SupervisorAgent,
            debate_arena: DebateArena,
        ):
            self.supervisor = supervisor
            self.debate = debate_arena
    
        async def __call__(self, state: ConversationState) -> dict:
            """执行多Agent协作"""
            query = state.get("rewritten_query") or state["original_query"]
    
            context = {
                "session_id": state["session_id"],
                "collection": state.get("collection", "default"),
                "history": [],
                "expanded_queries": state.get("expanded_queries", []),
            }
    
            agent_outputs: dict[str, AgentOutput] = {}
            max_iterations = self.supervisor.max_iterations
    
            logger.info(
                "multi_agent_hub_started",
                session_id=state["session_id"],
                query=query[:100],
            )
    
            for iteration in range(max_iterations):
                # 1. Supervisor决策
                decision = await self.supervisor.decide(
                    query=query,
                    agent_outputs=agent_outputs,
                    iteration=iteration,
                )
    
                # 2. 根据决策执行
                if decision.next_action in ("delegate", "parallel"):
                    agent_outputs = await self.supervisor.execute_agents(
                        decision=decision,
                        query=query,
                        context=context,
                        agent_outputs=agent_outputs,
                    )
    
                elif decision.next_action == "debate":
                    # 获取当前最佳答案用于辩论
                    best_output = max(
                        agent_outputs.values(),
                        key=lambda o: o.confidence,
                        default=AgentOutput(agent_name="none", answer=""),
                    )
                    debate_result = await self.debate.debate(
                        query=query,
                        initial_answer=best_output.answer,
                        evidence=best_output.evidence,
                        context=context,
                    )
                    agent_outputs["debate"] = debate_result
    
                elif decision.next_action in ("synthesize", "done"):
                    break
    
            # 3. 合成最终答案
            if agent_outputs:
                final = await self.supervisor.synthesize(
                    query=query,
                    agent_outputs=agent_outputs,
                    context=context,
                )
            else:
                final = AgentOutput(
                    agent_name="multi_agent_hub",
                    answer="多Agent系统未能生成回答",
                    confidence=0.0,
                )
    
            logger.info(
                "multi_agent_hub_completed",
                session_id=state["session_id"],
                iterations=iteration + 1,
                agents_used=list(agent_outputs.keys()),
                final_confidence=final.confidence,
            )
    
            return {
                "answer": final.answer,
                "confidence": final.confidence,
                "citations": final.citations,
                "model_used": f"multi_agent({','.join(agent_outputs.keys())})",
                "tokens_used": final.tokens_used,
                "messages": [AIMessage(content=final.answer)],
            }
    ```

63. ### 3.8 主图增强 (嵌入多Agent)

64. Python

65. 

66. ```
    # src/core/orchestrator/graph.py  (Phase 4 新增意图路由分支)
    
    # 在 intent_router 的条件边中新增 complex_task 路由:
    
    graph.add_conditional_edges(
        "intent_router",
        route_by_intent,
        {
            "rag_agent":        "rag_agent",
            "tool_agent":       "tool_agent",
            "codex_fallback":   "codex_fallback",
            "complex_task":     "multi_agent_hub",   # [新增] 复杂任务走多Agent
        },
    )
    
    # 多Agent Hub → 质量门控
    graph.add_edge("multi_agent_hub", "quality_gate")
    ```

67. text

68. 

69. ```
    Phase 4 图新增部分:
    
      ┌──────────────┐
      │intent_router │
      └──┬───┬───┬──┬┘
         │   │   │  │
      RAG│Tool│Chat│Complex
         │   │   │  │
         │   │   │  ▼
         │   │   │ ┌──────────────────────────────────────┐
         │   │   │ │       multi_agent_hub                │
         │   │   │ │                                      │
         │   │   │ │  ┌──────────────────┐                │
         │   │   │ │  │   Supervisor     │◀──────────┐    │
         │   │   │ │  └────┬────┬────┬──┘            │    │
         │   │   │ │       │    │    │               │    │
         │   │   │ │    委托│ 并行│ 辩论│              │    │
         │   │   │ │       ▼    ▼    ▼               │    │
         │   │   │ │  ┌────┐ ┌────┐ ┌──────┐        │    │
         │   │   │ │  │RAG │ │分析│ │辩论场│        │    │
         │   │   │ │  │专家│ │专家│ │正/反 │        │    │
         │   │   │ │  └──┬─┘ └──┬─┘ │裁判 │        │    │
         │   │   │ │     │      │   └──┬───┘        │    │
         │   │   │ │     └──────┴──────┘            │    │
         │   │   │ │            │                    │    │
         │   │   │ │            ▼                    │    │
         │   │   │ │     ┌──────────┐               │    │
         │   │   │ │     │批评家审查│───(需改进)────┘    │
         │   │   │ │     └────┬─────┘                     │
         │   │   │ │          │(通过)                     │
         │   │   │ │          ▼                           │
         │   │   │ │     ┌──────────┐                     │
         │   │   │ │     │合成最终  │                     │
         │   │   │ │     │答案      │                     │
         │   │   │ │     └──────────┘                     │
         │   │   │ └──────────────────────────────────────┘
         │   │   │         │
         ▼   ▼   ▼         ▼
      ┌──────────────────────┐
      │    quality_gate      │
      └──────────────────────┘
    ```

70. ------

71. ## 四、Week 17：知识图谱 & Agentic Chunking

72. ### 4.1 Neo4j 客户端

73. Python

74. 

75. ```
    # src/infra/database/neo4j_client.py
    
    from neo4j import AsyncGraphDatabase, AsyncDriver
    import structlog
    
    from src.infra.config.settings import get_settings
    
    logger = structlog.get_logger()
    
    _driver: AsyncDriver | None = None
    
    
    async def init_neo4j() -> AsyncDriver:
        """初始化Neo4j异步驱动"""
        global _driver
        settings = get_settings()
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
        # 验证连接
        async with _driver.session() as session:
            result = await session.run("RETURN 1 AS n")
            record = await result.single()
            logger.info("neo4j_connected", test_value=record["n"])
        return _driver
    
    
    async def get_neo4j() -> AsyncDriver:
        if _driver is None:
            return await init_neo4j()
        return _driver
    
    
    async def close_neo4j():
        global _driver
        if _driver:
            await _driver.close()
            _driver = None
    ```

76. ### 4.2 实体关系提取

77. Python

78. 

79. ```
    # src/core/knowledge_graph/entity_extractor.py
    
    import json
    import asyncio
    import structlog
    from pydantic import BaseModel, Field
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    
    from src.infra.config.settings import get_settings
    
    logger = structlog.get_logger()
    
    
    class Entity(BaseModel):
        """实体"""
        name: str
        type: str      # person / department / policy / concept / product / ...
        properties: dict = Field(default_factory=dict)
    
    
    class Relation(BaseModel):
        """关系"""
        source: str
        target: str
        relation_type: str  # belongs_to / manages / defines / related_to / ...
        properties: dict = Field(default_factory=dict)
    
    
    class ExtractionResult(BaseModel):
        """提取结果"""
        entities: list[Entity] = Field(default_factory=list)
        relations: list[Relation] = Field(default_factory=list)
    
    
    EXTRACTION_PROMPT = """从以下文本中提取实体和关系, 构建知识图谱。
    
    文本:
    ---
    {text}
    ---
    
    实体类型: person, department, policy, concept, product, process, location, date
    关系类型: belongs_to, manages, defines, related_to, has_property, part_of, requires, affects
    
    以JSON格式输出:
    {{
        "entities": [
            {{"name": "实体名", "type": "类型", "properties": {{}}}}
        ],
        "relations": [
            {{"source": "源实体名", "target": "目标实体名", "relation_type": "关系类型", "properties": {{}}}}
        ]
    }}
    
    要求:
    1. 只提取确定的实体和关系
    2. 实体名称统一规范化
    3. 关系方向要明确"""
    
    
    class EntityRelationExtractor:
        """
        实体关系提取器
    
        从文档文本中自动提取实体和关系, 用于构建知识图谱
        """
    
        def __init__(self):
            settings = get_settings()
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
                base_url=settings.OPENAI_API_BASE,
            )
            self._semaphore = asyncio.Semaphore(5)
    
        async def extract(self, text: str) -> ExtractionResult:
            """从文本提取实体和关系"""
            async with self._semaphore:
                try:
                    response = await self.llm.ainvoke(
                        [
                            SystemMessage(content="你是一个知识图谱构建专家。"),
                            HumanMessage(content=EXTRACTION_PROMPT.format(text=text[:3000])),
                        ],
                        response_format={"type": "json_object"},
                    )
                    return ExtractionResult.model_validate_json(response.content)
                except Exception as e:
                    logger.error("entity_extraction_failed", error=str(e))
                    return ExtractionResult()
    
        async def extract_from_conversation(
            self,
            user_message: str,
            assistant_message: str,
            user_id: str,
        ) -> ExtractionResult:
            """从对话中提取实体 (用于语义记忆)"""
            text = f"用户说: {user_message}\n助手回复: {assistant_message}"
            return await self.extract(text)
    ```

80. ### 4.3 知识图谱构建器

81. Python

82. 

83. ```
    # src/core/knowledge_graph/graph_builder.py
    
    import structlog
    from neo4j import AsyncDriver
    
    from src.core.knowledge_graph.entity_extractor import (
        EntityRelationExtractor, Entity, Relation, ExtractionResult,
    )
    
    logger = structlog.get_logger()
    
    
    class KnowledgeGraphBuilder:
        """
        知识图谱构建器
    
        将提取的实体和关系写入 Neo4j
        """
    
        def __init__(self, driver: AsyncDriver, extractor: EntityRelationExtractor):
            self.driver = driver
            self.extractor = extractor
    
        async def initialize(self):
            """创建约束和索引"""
            async with self.driver.session() as session:
                # 实体名称唯一约束
                await session.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE"
                )
                # 全文索引
                try:
                    await session.run(
                        """CREATE FULLTEXT INDEX entity_name_idx IF NOT EXISTS
                           FOR (e:Entity) ON EACH [e.name, e.description]"""
                    )
                except Exception:
                    pass
    
        async def ingest_document(
            self,
            doc_id: str,
            chunks: list[str],
            collection: str,
            tenant_id: str = "default",
        ):
            """从文档chunks中提取知识并写入图谱"""
            total_entities = 0
            total_relations = 0
    
            for i, chunk_text in enumerate(chunks):
                result = await self.extractor.extract(chunk_text)
                if result.entities or result.relations:
                    await self._write_to_neo4j(
                        result, doc_id, collection, tenant_id
                    )
                    total_entities += len(result.entities)
                    total_relations += len(result.relations)
    
            logger.info(
                "kg_document_ingested",
                doc_id=doc_id,
                entities=total_entities,
                relations=total_relations,
            )
    
        async def _write_to_neo4j(
            self,
            result: ExtractionResult,
            doc_id: str,
            collection: str,
            tenant_id: str,
        ):
            """写入Neo4j"""
            async with self.driver.session() as session:
                # 写入实体
                for entity in result.entities:
                    await session.run(
                        """MERGE (e:Entity {name: $name})
                           SET e.type = $type,
                               e.tenant_id = $tenant_id,
                               e.collection = $collection,
                               e.doc_id = $doc_id
                           SET e += $properties""",
                        name=entity.name,
                        type=entity.type,
                        tenant_id=tenant_id,
                        collection=collection,
                        doc_id=doc_id,
                        properties=entity.properties,
                    )
    
                    # 添加类型标签
                    await session.run(
                        f"MATCH (e:Entity {{name: $name}}) SET e:{entity.type.capitalize()}",
                        name=entity.name,
                    )
    
                # 写入关系
                for rel in result.relations:
                    await session.run(
                        f"""MATCH (s:Entity {{name: $source}})
                            MATCH (t:Entity {{name: $target}})
                            MERGE (s)-[r:{rel.relation_type.upper()}]->(t)
                            SET r += $properties
                            SET r.doc_id = $doc_id""",
                        source=rel.source,
                        target=rel.target,
                        properties=rel.properties,
                        doc_id=doc_id,
                    )
    
        async def query_subgraph(
            self,
            entity_name: str,
            depth: int = 2,
            tenant_id: str = "default",
        ) -> list[dict]:
            """查询实体的子图"""
            async with self.driver.session() as session:
                result = await session.run(
                    f"""MATCH path = (e:Entity {{name: $name, tenant_id: $tenant_id}})-[*1..{depth}]-(related)
                        RETURN path LIMIT 50""",
                    name=entity_name,
                    tenant_id=tenant_id,
                )
                paths = []
                async for record in result:
                    path = record["path"]
                    paths.append({
                        "nodes": [dict(node) for node in path.nodes],
                        "relationships": [
                            {
                                "type": rel.type,
                                "start": dict(rel.start_node),
                                "end": dict(rel.end_node),
                            }
                            for rel in path.relationships
                        ],
                    })
                return paths
    ```

84. ### 4.4 知识图谱检索器

85. Python

86. 

87. ```
    # src/core/rag/retrieval/kg_retriever.py
    
    import structlog
    from neo4j import AsyncDriver
    
    from src.core.rag.retrieval.dense import RetrievedChunk
    from src.core.knowledge_graph.entity_extractor import EntityRelationExtractor
    
    logger = structlog.get_logger()
    
    
    class KGRetriever:
        """
        知识图谱检索器
    
        从Neo4j中检索与查询相关的实体和关系:
        1. 从查询中提取实体
        2. 在图谱中查找相关节点
        3. 获取周围的子图
        4. 将图谱信息转换为文本上下文
        """
    
        def __init__(
            self,
            driver: AsyncDriver,
            extractor: EntityRelationExtractor,
        ):
            self.driver = driver
            self.extractor = extractor
    
        async def retrieve(
            self,
            query: str,
            collection: str = "default",
            tenant_id: str = "default",
            top_k: int = 10,
        ) -> list[RetrievedChunk]:
            """从知识图谱检索"""
    
            # 1. 从查询中提取实体
            extraction = await self.extractor.extract(query)
            entity_names = [e.name for e in extraction.entities]
    
            if not entity_names:
                # 尝试全文搜索
                entity_names = await self._fulltext_search(query, tenant_id)
    
            if not entity_names:
                return []
    
            # 2. 查询相关子图
            results = []
            for entity_name in entity_names[:3]:
                subgraph_text = await self._get_entity_context(
                    entity_name, tenant_id, depth=2
                )
                if subgraph_text:
                    results.append(
                        RetrievedChunk(
                            chunk_id=f"kg_{entity_name}",
                            doc_id="knowledge_graph",
                            content=subgraph_text,
                            score=0.7,  # KG结果的固定分数
                            doc_title=f"知识图谱: {entity_name}",
                            chunk_index=0,
                            collection=collection,
                        )
                    )
    
            logger.info(
                "kg_retrieval_completed",
                query=query[:100],
                entities_found=len(entity_names),
                results=len(results),
            )
    
            return results[:top_k]
    
        async def _fulltext_search(self, query: str, tenant_id: str) -> list[str]:
            """全文搜索实体"""
            try:
                async with self.driver.session() as session:
                    result = await session.run(
                        """CALL db.index.fulltext.queryNodes('entity_name_idx', $query)
                           YIELD node, score
                           WHERE node.tenant_id = $tenant_id
                           RETURN node.name AS name, score
                           ORDER BY score DESC LIMIT 5""",
                        query=query,
                        tenant_id=tenant_id,
                    )
                    names = []
                    async for record in result:
                        names.append(record["name"])
                    return names
            except Exception:
                return []
    
        async def _get_entity_context(
            self, entity_name: str, tenant_id: str, depth: int = 2
        ) -> str:
            """获取实体的上下文描述"""
            async with self.driver.session() as session:
                result = await session.run(
                    f"""MATCH (e:Entity {{name: $name, tenant_id: $tenant_id}})
                        OPTIONAL MATCH (e)-[r]-(related:Entity)
                        RETURN e, collect(DISTINCT {{
                            relation: type(r),
                            related_name: related.name,
                            related_type: related.type
                        }}) AS connections
                        LIMIT 1""",
                    name=entity_name,
                    tenant_id=tenant_id,
                )
    
                record = await result.single()
                if not record:
                    return ""
    
                entity = dict(record["e"])
                connections = record["connections"]
    
                # 构建文本描述
                lines = [f"实体: {entity_name} (类型: {entity.get('type', 'unknown')})"]
    
                for conn in connections:
                    if conn.get("related_name"):
                        lines.append(
                            f"  - [{conn['relation']}] → {conn['related_name']} ({conn.get('related_type', '')})"
                        )
    
                return "\n".join(lines)
    ```

88. ### 4.5 三路混合检索增强

89. Python

90. 

91. ```
    # src/core/rag/retrieval/hybrid.py  (Phase 4 增强 - 关键变更部分)
    
    class HybridRetriever:
        """Phase 4: 增加KG检索, 三路融合"""
    
        def __init__(
            self,
            dense_retriever,
            sparse_retriever=None,
            kg_retriever=None,      # [新增]
            reranker=None,
            dense_weight: float = 0.5,
            sparse_weight: float = 0.3,
            kg_weight: float = 0.2,  # [新增]
            rrf_k: int = 60,
        ):
            self.dense = dense_retriever
            self.sparse = sparse_retriever
            self.kg = kg_retriever
            self.reranker = reranker
            self.weights = {
                "dense": dense_weight,
                "sparse": sparse_weight,
                "kg": kg_weight,
            }
            self.rrf_k = rrf_k
    
        async def retrieve(self, query, expanded_queries=None, collection="default",
                           tenant_id="default", top_k=5, retrieval_top_k=None):
            retrieval_top_k = retrieval_top_k or top_k * 4
    
            # 并行三路召回
            tasks = []
    
            # Dense
            all_queries = [query] + (expanded_queries or [])[:2]
            for q in all_queries:
                tasks.append(self._safe_retrieve(
                    self.dense.retrieve, q, collection, retrieval_top_k, "dense"
                ))
    
            # Sparse
            if self.sparse:
                tasks.append(self._safe_retrieve(
                    self.sparse.retrieve, query, collection, retrieval_top_k, "sparse"
                ))
    
            # KG [新增]
            if self.kg:
                tasks.append(self._safe_retrieve(
                    self.kg.retrieve, query, collection, top_k,
                    "kg", tenant_id=tenant_id,
                ))
    
            results = await asyncio.gather(*tasks)
    
            # 按来源分组
            source_results = defaultdict(list)
            for source, chunks in results:
                source_results[source].extend(chunks)
    
            # 去重
            for source in source_results:
                source_results[source] = self._deduplicate(source_results[source])
    
            # RRF三路融合
            fused = self._multi_source_rrf(source_results)
            candidates = fused[:top_k * 3]
    
            # Rerank
            if self.reranker and candidates:
                try:
                    reranked = await self.reranker.rerank(query=query, chunks=candidates, top_n=top_k)
                    return reranked
                except Exception as e:
                    logger.error("rerank_failed", error=str(e))
    
            return candidates[:top_k]
    
        def _multi_source_rrf(self, source_results: dict) -> list[RetrievedChunk]:
            """多源RRF融合"""
            rrf_scores = defaultdict(float)
            chunk_map = {}
    
            for source, chunks in source_results.items():
                weight = self.weights.get(source, 0.1)
                for rank, chunk in enumerate(chunks, start=1):
                    cid = chunk.chunk_id
                    rrf_scores[cid] += weight / (self.rrf_k + rank)
                    if cid not in chunk_map:
                        chunk_map[cid] = chunk
    
            sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
            return [
                RetrievedChunk(
                    chunk_id=cid, doc_id=chunk_map[cid].doc_id,
                    content=chunk_map[cid].content, score=rrf_scores[cid],
                    doc_title=chunk_map[cid].doc_title,
                    chunk_index=chunk_map[cid].chunk_index,
                    collection=chunk_map[cid].collection,
                )
                for cid in sorted_ids
            ]
    ```

92. ### 4.6 Agentic Chunking

93. Python

94. 

95. ```
    # src/core/rag/ingestion/agentic_chunker.py
    
    import json
    import asyncio
    import structlog
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from llama_index.core.schema import TextNode, Document
    
    from src.infra.config.settings import get_settings
    
    logger = structlog.get_logger()
    
    
    AGENTIC_CHUNKING_PROMPT = """你是一个文档分块专家。请分析以下文本, 将其分割为语义完整的独立块。
    
    每个块应该:
    1. 包含一个完整的概念或主题
    2. 可以独立理解, 不依赖上下文
    3. 长度适中 (100-800字)
    4. 在自然的语义边界处分割
    
    文本:
    ---
    {text}
    ---
    
    以JSON格式输出:
    {{
        "chunks": [
            {{
                "content": "块内容",
                "title": "块标题(10字以内)",
                "reason": "为什么在这里分割"
            }}
        ]
    }}"""
    
    
    class AgenticChunker:
        """
        Agentic Chunking - LLM智能分块
    
        使用LLM判断最佳分块边界, 比固定规则/语义分块更精确
    
        优点:
        - 分块边界更自然
        - 每个块语义完整
        - 可处理复杂文档结构
    
        缺点:
        - 成本高 (每个文档需LLM调用)
        - 速度慢
        - 适用于高价值/小批量文档
        """
    
        def __init__(self, max_chunk_length: int = 2000):
            settings = get_settings()
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
                base_url=settings.OPENAI_API_BASE,
            )
            self.max_chunk_length = max_chunk_length
            self._semaphore = asyncio.Semaphore(3)
    
        def chunk(
            self,
            documents: list[Document],
            doc_id: str,
            collection: str,
        ) -> list[TextNode]:
            """同步包装 (兼容Phase 1接口)"""
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已在async上下文中
                import nest_asyncio
                nest_asyncio.apply()
            return loop.run_until_complete(
                self.achunk(documents, doc_id, collection)
            )
    
        async def achunk(
            self,
            documents: list[Document],
            doc_id: str,
            collection: str,
        ) -> list[TextNode]:
            """异步分块"""
            all_nodes = []
    
            for doc in documents:
                text = doc.text
    
                # 如果文本较短, 直接作为一个chunk
                if len(text) < 300:
                    all_nodes.append(TextNode(
                        text=text,
                        metadata={**doc.metadata, "doc_id": doc_id, "collection": collection},
                    ))
                    continue
    
                # 长文本分段处理 (LLM输入长度限制)
                segments = self._split_into_segments(text, self.max_chunk_length)
    
                for segment in segments:
                    chunks = await self._llm_chunk(segment)
                    for chunk in chunks:
                        all_nodes.append(TextNode(
                            text=chunk["content"],
                            metadata={
                                **doc.metadata,
                                "doc_id": doc_id,
                                "collection": collection,
                                "chunk_title": chunk.get("title", ""),
                                "chunking_strategy": "agentic",
                            },
                        ))
    
            # 设置ID和索引
            for i, node in enumerate(all_nodes):
                node.id_ = f"{doc_id}_chunk_{i:04d}"
                node.metadata["chunk_index"] = i
                node.metadata["total_chunks"] = len(all_nodes)
    
            logger.info(
                "agentic_chunking_completed",
                doc_id=doc_id,
                num_chunks=len(all_nodes),
            )
    
            return all_nodes
    
        async def _llm_chunk(self, text: str) -> list[dict]:
            """使用LLM分块"""
            async with self._semaphore:
                try:
                    response = await self.llm.ainvoke(
                        [
                            SystemMessage(content="你是文档分块专家。"),
                            HumanMessage(content=AGENTIC_CHUNKING_PROMPT.format(text=text)),
                        ],
                        response_format={"type": "json_object"},
                    )
                    result = json.loads(response.content)
                    return result.get("chunks", [{"content": text, "title": ""}])
                except Exception as e:
                    logger.warning("agentic_chunking_llm_failed", error=str(e))
                    return [{"content": text, "title": ""}]
    
        def _split_into_segments(self, text: str, max_length: int) -> list[str]:
            """将长文本按段落分成可处理的段"""
            paragraphs = text.split("\n\n")
            segments = []
            current = []
            current_length = 0
    
            for para in paragraphs:
                if current_length + len(para) > max_length and current:
                    segments.append("\n\n".join(current))
                    current = []
                    current_length = 0
                current.append(para)
                current_length += len(para)
    
            if current:
                segments.append("\n\n".join(current))
    
            return segments
    ```

96. ------

97. ## 五、Week 18：反馈闭环 & Prompt 版本管理

98. ### 5.1 反馈分析器

99. Python

100. 

101. ```
     # src/core/feedback/analyzer.py
     
     import json
     from datetime import datetime, timedelta
     import structlog
     from pydantic import BaseModel, Field
     
     from langchain_openai import ChatOpenAI
     from langchain_core.messages import SystemMessage, HumanMessage
     import asyncpg
     
     from src.infra.config.settings import get_settings
     
     logger = structlog.get_logger()
     
     
     class FeedbackIssue(BaseModel):
         """反馈问题分类"""
         category: str       # inaccurate / incomplete / irrelevant / hallucination / other
         description: str
         count: int
         example_queries: list[str] = Field(default_factory=list)
         severity: str = "medium"  # low / medium / high
     
     
     class FeedbackAnalysisReport(BaseModel):
         """反馈分析报告"""
         period_start: datetime
         period_end: datetime
         total_feedback: int
         positive_count: int
         negative_count: int
         satisfaction_rate: float
         top_issues: list[FeedbackIssue]
         recommendations: list[str]
         auto_actions: list[dict] = Field(default_factory=list)
     
     
     class FeedbackAnalyzer:
         """
         反馈分析器
     
         功能:
         1. 聚合分析用户反馈
         2. 识别常见问题模式
         3. 生成优化建议
         4. 触发自动优化动作
         """
     
         def __init__(self, pg_pool: asyncpg.Pool):
             self.pg_pool = pg_pool
             settings = get_settings()
             self.llm = ChatOpenAI(
                 model=settings.PRIMARY_LLM_MODEL,
                 temperature=0.0,
                 api_key=settings.OPENAI_API_KEY.get_secret_value(),
                 base_url=settings.OPENAI_API_BASE,
             )
     
         async def analyze(
             self,
             tenant_id: str = "default",
             days: int = 7,
         ) -> FeedbackAnalysisReport:
             """分析最近N天的反馈"""
             period_end = datetime.utcnow()
             period_start = period_end - timedelta(days=days)
     
             # 获取反馈数据
             feedback_rows = await self.pg_pool.fetch(
                 """SELECT feedback_type, feedback_tags, comment, query, answer, confidence
                    FROM user_feedback
                    WHERE tenant_id = $1 AND created_at >= $2
                    ORDER BY created_at DESC""",
                 tenant_id, period_start,
             )
     
             total = len(feedback_rows)
             positive = sum(1 for r in feedback_rows if r["feedback_type"] == "thumbs_up")
             negative = sum(1 for r in feedback_rows if r["feedback_type"] == "thumbs_down")
     
             # 分析负反馈
             negative_feedback = [r for r in feedback_rows if r["feedback_type"] == "thumbs_down"]
     
             top_issues = []
             recommendations = []
     
             if negative_feedback:
                 analysis = await self._analyze_negative_feedback(negative_feedback)
                 top_issues = analysis.get("issues", [])
                 recommendations = analysis.get("recommendations", [])
     
             report = FeedbackAnalysisReport(
                 period_start=period_start,
                 period_end=period_end,
                 total_feedback=total,
                 positive_count=positive,
                 negative_count=negative,
                 satisfaction_rate=positive / max(total, 1),
                 top_issues=[FeedbackIssue(**i) for i in top_issues],
                 recommendations=recommendations,
             )
     
             # 持久化报告
             await self._save_report(report, tenant_id)
     
             return report
     
         async def _analyze_negative_feedback(self, feedback: list) -> dict:
             """使用LLM分析负反馈模式"""
             samples = []
             for f in feedback[:50]:
                 samples.append({
                     "query": f["query"][:200] if f["query"] else "",
                     "answer": f["answer"][:200] if f["answer"] else "",
                     "tags": f["feedback_tags"] or [],
                     "comment": f["comment"] or "",
                     "confidence": f["confidence"],
                 })
     
             prompt = f"""分析以下{len(samples)}条负面反馈, 识别问题模式并给出优化建议。
     
     反馈数据:
     {json.dumps(samples, ensure_ascii=False, indent=2)}
     
     请输出:
     {{
         "issues": [
             {{"category": "类别", "description": "问题描述", "count": 数量, "example_queries": ["示例"], "severity": "high/medium/low"}}
         ],
         "recommendations": ["建议1", "建议2"],
         "root_causes": ["根因1"]
     }}"""
     
             response = await self.llm.ainvoke(
                 [HumanMessage(content=prompt)],
                 response_format={"type": "json_object"},
             )
     
             return json.loads(response.content)
     
         async def _save_report(self, report: FeedbackAnalysisReport, tenant_id: str):
             """保存分析报告"""
             import uuid
             await self.pg_pool.execute(
                 """INSERT INTO feedback_analysis_reports
                    (id, period_start, period_end, total_feedback,
                     positive_count, negative_count, top_issues, recommendations)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                 f"fbr_{uuid.uuid4().hex[:12]}",
                 report.period_start,
                 report.period_end,
                 report.total_feedback,
                 report.positive_count,
                 report.negative_count,
                 json.dumps([i.model_dump() for i in report.top_issues], ensure_ascii=False),
                 json.dumps(report.recommendations, ensure_ascii=False),
             )
     ```

102. ### 5.2 Prompt 版本管理

103. Python

104. 

105. ```
     # src/core/prompt_management/registry.py
     
     import json
     import uuid
     from datetime import datetime
     import structlog
     import asyncpg
     
     logger = structlog.get_logger()
     
     
     class PromptVersion:
         """Prompt 版本"""
         def __init__(self, id, name, version, content, variables, status, metrics, created_at):
             self.id = id
             self.name = name
             self.version = version
             self.content = content
             self.variables = variables
             self.status = status
             self.metrics = metrics
             self.created_at = created_at
     
         def render(self, **kwargs) -> str:
             """渲染Prompt (替换变量)"""
             result = self.content
             for key, value in kwargs.items():
                 result = result.replace(f"{{{{{key}}}}}", str(value))
             return result
     
     
     class PromptRegistry:
         """
         Prompt 版本管理注册中心
     
         功能:
         1. Prompt CRUD + 版本控制
         2. 获取当前激活版本
         3. A/B测试流量分配
         4. 指标追踪
         """
     
         def __init__(self, pg_pool: asyncpg.Pool):
             self.pg_pool = pg_pool
             self._cache: dict[str, PromptVersion] = {}
     
         async def create_version(
             self,
             prompt_name: str,
             content: str,
             variables: list[str] | None = None,
             description: str = "",
             created_by: str = "",
         ) -> PromptVersion:
             """创建新版本"""
             # 获取当前最新版本号
             latest = await self.pg_pool.fetchval(
                 "SELECT MAX(version) FROM prompt_versions WHERE prompt_name = $1",
                 prompt_name,
             )
             new_version = (latest or 0) + 1
     
             version_id = f"pv_{uuid.uuid4().hex[:12]}"
     
             await self.pg_pool.execute(
                 """INSERT INTO prompt_versions
                    (id, prompt_name, version, content, variables, description, status, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                 version_id, prompt_name, new_version, content,
                 json.dumps(variables or []), description, "draft", created_by,
             )
     
             logger.info(
                 "prompt_version_created",
                 name=prompt_name,
                 version=new_version,
             )
     
             return PromptVersion(
                 id=version_id, name=prompt_name, version=new_version,
                 content=content, variables=variables or [],
                 status="draft", metrics={}, created_at=datetime.utcnow(),
             )
     
         async def activate(self, prompt_name: str, version: int):
             """激活指定版本 (将其他版本设为archived)"""
             async with self.pg_pool.acquire() as conn:
                 async with conn.transaction():
                     # 归档当前激活版本
                     await conn.execute(
                         """UPDATE prompt_versions SET status = 'archived'
                            WHERE prompt_name = $1 AND status = 'active'""",
                         prompt_name,
                     )
                     # 激活指定版本
                     await conn.execute(
                         """UPDATE prompt_versions SET status = 'active', activated_at = NOW()
                            WHERE prompt_name = $1 AND version = $2""",
                         prompt_name, version,
                     )
     
             # 清除缓存
             self._cache.pop(prompt_name, None)
     
             logger.info("prompt_activated", name=prompt_name, version=version)
     
         async def get_active(self, prompt_name: str) -> PromptVersion | None:
             """获取当前激活版本 (带缓存)"""
             if prompt_name in self._cache:
                 return self._cache[prompt_name]
     
             row = await self.pg_pool.fetchrow(
                 """SELECT * FROM prompt_versions
                    WHERE prompt_name = $1 AND status = 'active'
                    ORDER BY version DESC LIMIT 1""",
                 prompt_name,
             )
     
             if not row:
                 return None
     
             pv = PromptVersion(
                 id=row["id"], name=row["prompt_name"],
                 version=row["version"], content=row["content"],
                 variables=json.loads(row["variables"] or "[]"),
                 status=row["status"], metrics=row["metrics"] or {},
                 created_at=row["created_at"],
             )
     
             self._cache[prompt_name] = pv
             return pv
     
         async def get_prompt_or_default(
             self,
             prompt_name: str,
             default_content: str,
             **render_kwargs,
         ) -> str:
             """获取Prompt内容, 如无激活版本则使用默认"""
             pv = await self.get_active(prompt_name)
             if pv:
                 return pv.render(**render_kwargs)
             return default_content.format(**render_kwargs)
     
         async def list_versions(self, prompt_name: str) -> list[dict]:
             """列出所有版本"""
             rows = await self.pg_pool.fetch(
                 """SELECT id, version, status, description, metrics, created_at, activated_at
                    FROM prompt_versions
                    WHERE prompt_name = $1
                    ORDER BY version DESC""",
                 prompt_name,
             )
             return [dict(row) for row in rows]
     
         async def rollback(self, prompt_name: str):
             """回滚到上一个版本"""
             # 获取上一个activated的版本
             prev = await self.pg_pool.fetchrow(
                 """SELECT version FROM prompt_versions
                    WHERE prompt_name = $1 AND status = 'archived'
                    ORDER BY activated_at DESC LIMIT 1""",
                 prompt_name,
             )
             if prev:
                 await self.activate(prompt_name, prev["version"])
                 logger.info("prompt_rolled_back", name=prompt_name, version=prev["version"])
     ```

106. ### 5.3 A/B 测试框架

107. Python

108. 

109. ```
     # src/core/prompt_management/ab_testing.py
     
     import random
     import uuid
     import json
     from datetime import datetime
     import structlog
     import asyncpg
     
     from src.core.prompt_management.registry import PromptRegistry, PromptVersion
     
     logger = structlog.get_logger()
     
     
     class ABTestManager:
         """
         Prompt A/B 测试管理器
     
         流程:
         1. 创建测试: 指定两个Prompt版本 + 流量分配比例
         2. 运行期间: 根据比例随机选择版本
         3. 收集指标: 置信度、反馈、延迟
         4. 分析结果: 统计显著性检验
         5. 决策: 选择优胜版本激活
         """
     
         def __init__(self, pg_pool: asyncpg.Pool, prompt_registry: PromptRegistry):
             self.pg_pool = pg_pool
             self.registry = prompt_registry
             self._active_tests: dict[str, dict] = {}  # prompt_name -> test_config
     
         async def create_test(
             self,
             name: str,
             prompt_name: str,
             version_a: int,
             version_b: int,
             traffic_split: float = 0.5,
             created_by: str = "",
         ) -> str:
             """创建A/B测试"""
             test_id = f"ab_{uuid.uuid4().hex[:12]}"
     
             # 获取版本ID
             va = await self.pg_pool.fetchval(
                 "SELECT id FROM prompt_versions WHERE prompt_name = $1 AND version = $2",
                 prompt_name, version_a,
             )
             vb = await self.pg_pool.fetchval(
                 "SELECT id FROM prompt_versions WHERE prompt_name = $1 AND version = $2",
                 prompt_name, version_b,
             )
     
             if not va or not vb:
                 raise ValueError("Prompt version not found")
     
             await self.pg_pool.execute(
                 """INSERT INTO ab_tests
                    (id, name, prompt_name, variant_a_id, variant_b_id,
                     traffic_split, status, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                 test_id, name, prompt_name, va, vb,
                 traffic_split, "running", created_by,
             )
     
             # 更新Prompt状态
             await self.pg_pool.execute(
                 "UPDATE prompt_versions SET status = 'ab_testing' WHERE id IN ($1, $2)",
                 va, vb,
             )
     
             # 缓存活跃测试
             self._active_tests[prompt_name] = {
                 "test_id": test_id,
                 "variant_a_id": va,
                 "variant_b_id": vb,
                 "traffic_split": traffic_split,
             }
     
             logger.info(
                 "ab_test_created",
                 test_id=test_id,
                 prompt_name=prompt_name,
                 version_a=version_a,
                 version_b=version_b,
                 split=traffic_split,
             )
     
             return test_id
     
         async def get_variant(self, prompt_name: str, session_id: str) -> tuple[PromptVersion, str]:
             """
             获取A/B测试变体
     
             Returns:
                 (PromptVersion, variant_label: "A" / "B")
             """
             test = self._active_tests.get(prompt_name)
             if not test:
                 # 检查数据库
                 row = await self.pg_pool.fetchrow(
                     """SELECT * FROM ab_tests
                        WHERE prompt_name = $1 AND status = 'running'
                        ORDER BY start_at DESC LIMIT 1""",
                     prompt_name,
                 )
                 if not row:
                     # 无活跃测试, 返回默认激活版本
                     pv = await self.registry.get_active(prompt_name)
                     return pv, "default"
                 test = {
                     "test_id": row["id"],
                     "variant_a_id": row["variant_a_id"],
                     "variant_b_id": row["variant_b_id"],
                     "traffic_split": row["traffic_split"],
                 }
                 self._active_tests[prompt_name] = test
     
             # 基于session_id的确定性分流 (同一用户始终看到同一版本)
             hash_val = hash(session_id + test["test_id"]) % 100
             is_variant_a = hash_val < test["traffic_split"] * 100
     
             variant_id = test["variant_a_id"] if is_variant_a else test["variant_b_id"]
             variant_label = "A" if is_variant_a else "B"
     
             row = await self.pg_pool.fetchrow(
                 "SELECT * FROM prompt_versions WHERE id = $1", variant_id,
             )
     
             pv = PromptVersion(
                 id=row["id"], name=row["prompt_name"],
                 version=row["version"], content=row["content"],
                 variables=json.loads(row["variables"] or "[]"),
                 status=row["status"], metrics=row["metrics"] or {},
                 created_at=row["created_at"],
             )
     
             return pv, variant_label
     
         async def record_sample(
             self,
             prompt_name: str,
             variant_label: str,
             session_id: str,
             prompt_version_id: str,
             query: str,
             answer: str,
             confidence: float,
             latency_ms: float,
         ):
             """记录A/B测试样本"""
             test = self._active_tests.get(prompt_name)
             if not test:
                 return
     
             await self.pg_pool.execute(
                 """INSERT INTO ab_test_samples
                    (test_id, variant, session_id, prompt_version_id,
                     query, answer, confidence, latency_ms)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                 test["test_id"], variant_label, session_id, prompt_version_id,
                 query[:500], answer[:500], confidence, latency_ms,
             )
     
         async def get_results(self, test_id: str) -> dict:
             """获取A/B测试结果"""
             samples = await self.pg_pool.fetch(
                 """SELECT variant, 
                           COUNT(*) as count,
                           AVG(confidence) as avg_confidence,
                           AVG(latency_ms) as avg_latency,
                           COUNT(*) FILTER (WHERE feedback_type = 'thumbs_up') as positive,
                           COUNT(*) FILTER (WHERE feedback_type = 'thumbs_down') as negative
                    FROM ab_test_samples
                    WHERE test_id = $1
                    GROUP BY variant""",
                 test_id,
             )
     
             results = {}
             for row in samples:
                 total_feedback = (row["positive"] or 0) + (row["negative"] or 0)
                 results[row["variant"]] = {
                     "count": row["count"],
                     "avg_confidence": round(float(row["avg_confidence"] or 0), 4),
                     "avg_latency_ms": round(float(row["avg_latency"] or 0), 2),
                     "positive_feedback": row["positive"] or 0,
                     "negative_feedback": row["negative"] or 0,
                     "satisfaction_rate": round(
                         (row["positive"] or 0) / max(total_feedback, 1), 3
                     ),
                 }
     
             return results
     
         async def conclude_test(self, test_id: str, winner: str):
             """结束测试, 激活优胜版本"""
             test = await self.pg_pool.fetchrow(
                 "SELECT * FROM ab_tests WHERE id = $1", test_id,
             )
             if not test:
                 raise ValueError("Test not found")
     
             winner_version_id = test["variant_a_id"] if winner == "A" else test["variant_b_id"]
     
             # 获取版本信息
             pv = await self.pg_pool.fetchrow(
                 "SELECT prompt_name, version FROM prompt_versions WHERE id = $1",
                 winner_version_id,
             )
     
             # 激活优胜版本
             await self.registry.activate(pv["prompt_name"], pv["version"])
     
             # 更新测试状态
             results = await self.get_results(test_id)
             await self.pg_pool.execute(
                 """UPDATE ab_tests 
                    SET status = 'completed', end_at = NOW(), results = $1
                    WHERE id = $2""",
                 json.dumps(results), test_id,
             )
     
             # 清除缓存
             self._active_tests.pop(test["prompt_name"], None)
     
             logger.info(
                 "ab_test_concluded",
                 test_id=test_id,
                 winner=winner,
                 prompt_name=pv["prompt_name"],
                 version=pv["version"],
             )
     ```

110. ### 5.4 自动化评估定时任务

111. Python

112. 

113. ```
     # src/core/feedback/scheduler.py
     
     import structlog
     from apscheduler.schedulers.asyncio import AsyncIOScheduler
     from apscheduler.triggers.cron import CronTrigger
     
     logger = structlog.get_logger()
     
     _scheduler: AsyncIOScheduler | None = None
     
     
     async def setup_scheduler(app):
         """配置定时任务"""
         global _scheduler
         _scheduler = AsyncIOScheduler()
     
         # 每日凌晨2点: 反馈分析
         _scheduler.add_job(
             daily_feedback_analysis,
             CronTrigger(hour=2, minute=0),
             id="daily_feedback_analysis",
             name="Daily Feedback Analysis",
         )
     
         # 每周一凌晨3点: 自动化RAG评估
         _scheduler.add_job(
             weekly_rag_evaluation,
             CronTrigger(day_of_week="mon", hour=3, minute=0),
             id="weekly_rag_evaluation",
             name="Weekly RAG Evaluation",
         )
     
         # 每小时: 审查队列SLA检查
         _scheduler.add_job(
             check_review_sla,
             CronTrigger(minute=0),
             id="check_review_sla",
             name="Review SLA Check",
         )
     
         _scheduler.start()
         logger.info("scheduler_started", jobs=len(_scheduler.get_jobs()))
     
     
     async def daily_feedback_analysis():
         """每日反馈分析"""
         from src.core.feedback.analyzer import FeedbackAnalyzer
         from src.infra.database.postgres import get_postgres_pool
     
         try:
             pool = await get_postgres_pool()
             analyzer = FeedbackAnalyzer(pool)
     
             # 获取所有活跃租户
             tenants = await pool.fetch(
                 "SELECT id FROM tenants WHERE is_active = TRUE"
             )
     
             for tenant in tenants:
                 report = await analyzer.analyze(
                     tenant_id=tenant["id"],
                     days=1,
                 )
                 logger.info(
                     "daily_feedback_analysis_completed",
                     tenant_id=tenant["id"],
                     total=report.total_feedback,
                     satisfaction=report.satisfaction_rate,
                     issues=len(report.top_issues),
                 )
     
         except Exception as e:
             logger.error("daily_feedback_analysis_failed", error=str(e))
     
     
     async def weekly_rag_evaluation():
         """每周RAG质量评估"""
         from src.evaluation.runner import EvaluationRunner
         from src.evaluation.ragas_evaluator import RagasEvaluator
         from src.evaluation.dataset_generator import TestsetGenerator
     
         try:
             # 自动生成测试集
             generator = TestsetGenerator()
             # ... 从最近一周的问题中抽样
             # ... 执行评估
             # ... 生成报告
             logger.info("weekly_rag_evaluation_completed")
         except Exception as e:
             logger.error("weekly_rag_evaluation_failed", error=str(e))
     
     
     async def check_review_sla():
         """检查审查SLA"""
         from src.infra.database.postgres import get_postgres_pool
     
         try:
             pool = await get_postgres_pool()
             breached = await pool.fetch(
                 """SELECT id, session_id, tenant_id, priority, sla_deadline
                    FROM review_queue
                    WHERE status IN ('pending', 'assigned')
                    AND sla_deadline < NOW()"""
             )
     
             if breached:
                 logger.warning(
                     "review_sla_breach",
                     count=len(breached),
                     reviews=[r["id"] for r in breached],
                 )
                 # 可以在这里触发告警通知
         except Exception as e:
             logger.error("review_sla_check_failed", error=str(e))
     ```

114. ------

115. ## 六、Week 19-20：Kubernetes 生产部署

116. ### 6.1 Helm Chart

117. YAML

118. 

119. ```
     # deploy/helm/qa-assistant/Chart.yaml
     
     apiVersion: v2
     name: qa-assistant
     description: Enterprise Intelligent QA Assistant
     version: 1.0.0
     appVersion: "1.0.0"
     type: application
     
     dependencies:
       - name: milvus
         version: "4.2.0"
         repository: "https://zilliztech.github.io/milvus-helm/"
         condition: milvus.enabled
       - name: redis
         version: "19.0.0"
         repository: "https://charts.bitnami.com/bitnami"
         condition: redis.enabled
       - name: postgresql
         version: "15.0.0"
         repository: "https://charts.bitnami.com/bitnami"
         condition: postgresql.enabled
       - name: elasticsearch
         version: "8.5.0"
         repository: "https://helm.elastic.co"
         condition: elasticsearch.enabled
     ```

120. YAML

121. 

122. ```
     # deploy/helm/qa-assistant/values.yaml
     
     replicaCount:
       api: 3
       worker: 2
     
     image:
       api:
         repository: your-registry/qa-assistant-api
         tag: "1.0.0"
         pullPolicy: IfNotPresent
       worker:
         repository: your-registry/qa-assistant-worker
         tag: "1.0.0"
         pullPolicy: IfNotPresent
     
     # API服务配置
     api:
       port: 8000
       workers: 4
       resources:
         requests:
           cpu: "500m"
           memory: "1Gi"
         limits:
           cpu: "2"
           memory: "4Gi"
     
     # Worker配置 (需要更多资源: Embedding/Rerank模型)
     worker:
       resources:
         requests:
           cpu: "1"
           memory: "4Gi"
         limits:
           cpu: "4"
           memory: "8Gi"
     
     # HPA自动伸缩
     autoscaling:
       enabled: true
       minReplicas: 2
       maxReplicas: 10
       targetCPUUtilizationPercentage: 70
       targetMemoryUtilizationPercentage: 80
       # 自定义指标 (基于请求延迟)
       customMetrics:
         - type: Pods
           pods:
             metric:
               name: qa_chat_latency_seconds_p95
             target:
               type: AverageValue
               averageValue: "5"
     
     # Ingress
     ingress:
       enabled: true
       className: nginx
       annotations:
         cert-manager.io/cluster-issuer: letsencrypt
         nginx.ingress.kubernetes.io/proxy-body-size: "50m"
         nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
       hosts:
         - host: qa.your-domain.com
           paths:
             - path: /
               pathType: Prefix
       tls:
         - secretName: qa-tls
           hosts:
             - qa.your-domain.com
     
     # 环境变量 (敏感信息通过Secret注入)
     env:
       ENV: production
       LOG_LEVEL: INFO
       LOG_FORMAT: json
       PRIMARY_LLM_MODEL: gpt-4o
       EMBEDDING_MODEL: text-embedding-3-large
       MAX_LLM_CONCURRENT: "50"
     
     # 外部依赖配置
     milvus:
       enabled: true
       cluster:
         enabled: true  # 生产环境用分布式模式
       queryNode:
         replicas: 3
       dataNode:
         replicas: 2
       indexNode:
         replicas: 2
     
     redis:
       enabled: true
       architecture: replication
       replica:
         replicaCount: 2
     
     postgresql:
       enabled: true
       architecture: replication
       primary:
         persistence:
           size: 50Gi
       readReplicas:
         replicaCount: 1
     
     elasticsearch:
       enabled: true
       replicas: 2
       resources:
         requests:
           memory: "2Gi"
     ```

123. ### 6.2 API Deployment

124. YAML

125. 

126. ```
     # deploy/helm/qa-assistant/templates/api-deployment.yaml
     
     apiVersion: apps/v1
     kind: Deployment
     metadata:
       name: {{ include "qa-assistant.fullname" . }}-api
       labels:
         app.kubernetes.io/component: api
     spec:
       replicas: {{ .Values.replicaCount.api }}
       selector:
         matchLabels:
           app.kubernetes.io/component: api
       strategy:
         type: RollingUpdate
         rollingUpdate:
           maxSurge: 1
           maxUnavailable: 0
       template:
         metadata:
           labels:
             app.kubernetes.io/component: api
           annotations:
             prometheus.io/scrape: "true"
             prometheus.io/port: "8000"
             prometheus.io/path: "/metrics"
         spec:
           containers:
             - name: api
               image: "{{ .Values.image.api.repository }}:{{ .Values.image.api.tag }}"
               ports:
                 - containerPort: 8000
               env:
                 {{- range $key, $value := .Values.env }}
                 - name: {{ $key }}
                   value: {{ $value | quote }}
                 {{- end }}
               envFrom:
                 - secretRef:
                     name: {{ include "qa-assistant.fullname" . }}-secrets
               resources:
                 {{- toYaml .Values.api.resources | nindent 12 }}
               readinessProbe:
                 httpGet:
                   path: /health
                   port: 8000
                 initialDelaySeconds: 10
                 periodSeconds: 10
               livenessProbe:
                 httpGet:
                   path: /health
                   port: 8000
                 initialDelaySeconds: 30
                 periodSeconds: 30
                 failureThreshold: 3
               startupProbe:
                 httpGet:
                   path: /health
                   port: 8000
                 initialDelaySeconds: 5
                 periodSeconds: 5
                 failureThreshold: 30  # 最多等150秒启动
     ```

127. ### 6.3 CI/CD 流水线

128. YAML

129. 

130. ```
     # deploy/ci/.github/workflows/ci.yml
     
     name: CI
     
     on:
       push:
         branches: [main, develop]
       pull_request:
         branches: [main]
     
     jobs:
       lint-and-test:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
     
           - name: Setup Python
             uses: actions/setup-python@v5
             with:
               python-version: "3.12"
     
           - name: Install dependencies
             run: |
               pip install poetry
               poetry install
     
           - name: Lint
             run: |
               poetry run ruff check src/ tests/
               poetry run mypy src/
     
           - name: Unit Tests
             run: poetry run pytest tests/unit/ -v --cov=src
     
           - name: Integration Tests
             run: |
               docker compose -f docker/docker-compose.yml up -d postgres redis milvus
               sleep 30
               poetry run pytest tests/integration/ -v
             env:
               OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
     
       build:
         needs: lint-and-test
         runs-on: ubuntu-latest
         if: github.ref == 'refs/heads/main'
         steps:
           - uses: actions/checkout@v4
     
           - name: Build and Push Docker Images
             run: |
               docker build -f deploy/ci/Dockerfile.api.prod -t $REGISTRY/qa-api:${{ github.sha }} .
               docker build -f deploy/ci/Dockerfile.worker.prod -t $REGISTRY/qa-worker:${{ github.sha }} .
               docker push $REGISTRY/qa-api:${{ github.sha }}
               docker push $REGISTRY/qa-worker:${{ github.sha }}
     
       deploy:
         needs: build
         runs-on: ubuntu-latest
         if: github.ref == 'refs/heads/main'
         steps:
           - uses: actions/checkout@v4
     
           - name: Deploy to K8s (Canary)
             run: |
               helm upgrade --install qa-assistant deploy/helm/qa-assistant/ \
                 --set image.api.tag=${{ github.sha }} \
                 --set image.worker.tag=${{ github.sha }} \
                 -f deploy/helm/qa-assistant/values-prod.yaml \
                 --namespace qa-prod
     ```

131. ------

132. ## 七、Phase 4 验收标准

133. ### 功能验收

134. | #    | 功能             | 验收标准                             |
     | ---- | ---------------- | ------------------------------------ |
     | 1    | Supervisor Agent | 能根据问题复杂度选择合适的协作策略   |
     | 2    | 并行Agent执行    | 多Agent并行执行，结果正确融合        |
     | 3    | 辩论机制         | 正反方辩论2-3轮后由Judge裁决         |
     | 4    | 投票机制         | 多Agent独立回答后投票产生共识        |
     | 5    | 多策略竞赛       | 多种RAG策略并行，Judge选出最优       |
     | 6    | 知识图谱检索     | 从Neo4j检索实体关系，作为第三路召回  |
     | 7    | 三路融合         | Dense + Sparse + KG 的RRF融合正常    |
     | 8    | Agentic Chunking | LLM智能分块可用，块边界合理          |
     | 9    | Prompt版本管理   | 创建/激活/回滚Prompt版本             |
     | 10   | A/B测试          | 两个Prompt版本可并行测试，指标可比较 |
     | 11   | 反馈分析         | 自动分析负反馈模式，生成优化建议     |
     | 12   | 定时任务         | 每日反馈分析、每周评估正常运行       |
     | 13   | K8s部署          | Helm一键部署，HPA自动伸缩            |
     | 14   | CI/CD            | 代码合入main后自动测试、构建、部署   |
     | 15   | Milvus分布式     | 多QueryNode，支持高并发检索          |

135. ### 质量基线 (Phase 4 完成后)

136. | 指标              | Phase 3 | Phase 4 目标 | 提升手段         |
     | ----------------- | ------- | ------------ | ---------------- |
     | Faithfulness      | ≥ 0.80  | ≥ 0.88       | 辩论+Critic审查  |
     | Answer Relevancy  | ≥ 0.75  | ≥ 0.85       | 多策略竞赛+Judge |
     | Context Precision | ≥ 0.70  | ≥ 0.80       | KG第三路召回     |
     | 复杂问题准确率    | ~65%    | ≥ 80%        | 多Agent协作      |
     | 用户满意度        | ~75%    | ≥ 85%        | 反馈闭环优化     |
     | P95延迟(复杂任务) | N/A     | < 15s        | 并行Agent        |
     | 系统可用性        | ~99%    | ≥ 99.9%      | K8s + HPA + 熔断 |

137. ------

138. ## 八、完整系统四阶段总结

139. text

140. 

141. ```
     ┌────────────────────────────────────────────────────────────────────┐
     │                    系统演进路线总结                                │
     ├────────────┬───────────────────────────────────────────────────────┤
     │ Phase 1    │ MVP: FastAPI + LangGraph + LlamaIndex + Milvus      │
     │ (4-6周)    │ 基础对话 + 单路Dense检索 + Codex降级 + 短期记忆     │
     │            │ Docker Compose 开发环境                              │
     ├────────────┼───────────────────────────────────────────────────────┤
     │ Phase 2    │ 质量增强: 语义分块 + 多路召回(Dense+BM25) + Rerank  │
     │ (3-4周)    │ 查询改写 + 语义缓存 + LLM置信度 + LangFuse         │
     │            │ RAGAS/DeepEval 评估                                  │
     ├────────────┼───────────────────────────────────────────────────────┤
     │ Phase 3    │ 企业级: 人工审查(interrupt/resume) + MCP工具         │
     │ (3-4周)    │ 安全护栏 + 长期记忆 + 多租户 + JWT认证              │
     │            │ 限流熔断 + Prometheus/Grafana 监控                   │
     ├────────────┼───────────────────────────────────────────────────────┤
     │ Phase 4    │ 高级能力: 多Agent协作/竞争/辩论 + 知识图谱          │
     │ (4-6周)    │ Agentic Chunking + Prompt版本管理 + A/B测试         │
     │            │ 反馈闭环 + Kubernetes 生产部署                       │
     ├────────────┼───────────────────────────────────────────────────────┤
     │ 总计       │ 14-20 周 (约 3.5-5 个月)                            │
     └────────────┴───────────────────────────────────────────────────────┘
     ```

142. 

143. 

144. 