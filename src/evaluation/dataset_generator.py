"""测试集自动生成模块

从文档自动生成评估测试问答对，支持:
- 多难度生成: easy / medium / hard
- 多问题类型: 事实性、比较性、流程性等
"""

import json

import structlog

from src.evaluation.ragas_evaluator import TestCase
from src.infra.config.settings import get_settings

logger = structlog.get_logger()


class GeneratedQA:
    """自动生成的问答对

    Attributes:
        question: 生成的问题
        answer: 生成的答案
        difficulty: 难度级别 (easy / medium / hard)
    """

    def __init__(
        self,
        question: str,
        answer: str,
        difficulty: str = "medium",
    ):
        self.question = question
        self.answer = answer
        self.difficulty = difficulty

    def model_validate(self, data: dict) -> "GeneratedQA":
        """从字典验证并创建实例

        Args:
            data: 字典数据

        Returns:
            GeneratedQA: 验证后的实例
        """
        return GeneratedQA(
            question=data.get("question", ""),
            answer=data.get("answer", ""),
            difficulty=data.get("difficulty", "medium"),
        )


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
    """评估测试集自动生成器

    从文档内容自动生成测试问答对，用于 RAG 系统评估。
    """

    def __init__(self):
        """初始化测试集生成器"""
        settings = get_settings()

        from langchain_openai import ChatOpenAI

        self.llm = ChatOpenAI(
            model=settings.PRIMARY_LLM_MODEL,
            temperature=0.7,
            api_key=settings.DASHSCOPE_API_KEY.get_secret_value(),
            base_url=settings.DASHSCOPE_BASE_URL,
        )

    async def generate_from_documents(
        self,
        documents: list[str],
        count_per_doc: int = 5,
    ) -> list[TestCase]:
        """从文档生成测试集

        Args:
            documents: 文档内容列表
            count_per_doc: 每个文档生成的问答对数量

        Returns:
            list[TestCase]: 生成的测试用例列表
        """
        all_cases = []

        from langchain_core.messages import SystemMessage, HumanMessage

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
