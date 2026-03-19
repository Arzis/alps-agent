"""评估模块

提供 RAG 系统评估能力，包括:
- RAGAS 标准化评估
- DeepEval 补充评估
- 测试集自动生成
- 评估运行器
"""

from src.evaluation.ragas_evaluator import (
    TestCase,
    EvaluationMetrics,
    EvaluationReport,
    RagasEvaluator,
)
from src.evaluation.deepeval_evaluator import DeepEvalEvaluator
from src.evaluation.dataset_generator import TestsetGenerator, GeneratedQA
from src.evaluation.runner import EvaluationRunner

__all__ = [
    "TestCase",
    "EvaluationMetrics",
    "EvaluationReport",
    "RagasEvaluator",
    "DeepEvalEvaluator",
    "TestsetGenerator",
    "GeneratedQA",
    "EvaluationRunner",
]
