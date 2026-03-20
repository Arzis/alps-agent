// 评估相关类型定义

export interface TestCase {
  question: string;
  ground_truth?: string;
  generated_answer?: string;
  contexts: string[];
}

export interface EvaluationMetrics {
  faithfulness?: number;
  answer_relevancy?: number;
  context_precision?: number;
  context_recall?: number;
}

export interface EvaluationSample {
  question: string;
  ground_truth: string;
  generated_answer: string;
  metrics: EvaluationMetrics;
}

export interface EvaluationReportSummary {
  run_id: string;
  name: string;
  dataset_size: number;
  status: 'running' | 'completed' | 'failed';
  metrics: EvaluationMetrics;
  created_at: string;
}

export interface EvaluationReportDetail extends EvaluationReportSummary {
  avg_metrics: EvaluationMetrics;
  config: Record<string, unknown>;
  samples: EvaluationSample[];
}

export interface RunEvaluationRequest {
  name: string;
  collection: string;
  test_cases: TestCase[];
  run_deepeval?: boolean;
}

export interface GenerateTestsetRequest {
  collection: string;
  count_per_doc: number;
  max_docs: number;
}
