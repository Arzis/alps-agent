import request from './request';
import API_ENDPOINTS from '@/config/api';
import type {
  EvaluationReportSummary,
  EvaluationReportDetail,
  RunEvaluationRequest,
  GenerateTestsetRequest,
  TestCase,
} from '@/types/evaluation';

// 运行评估
export async function runEvaluation(
  data: RunEvaluationRequest
): Promise<{ task_id: string; status: string; message: string }> {
  const res = await request.post(API_ENDPOINTS.evaluationRun, data);
  return res.data;
}

// 生成测试集
export async function generateTestset(
  data: GenerateTestsetRequest
): Promise<{ total: number; test_cases: TestCase[] }> {
  const res = await request.post(API_ENDPOINTS.evaluationGenerate, data);
  return res.data;
}

// 获取评估报告列表
export async function getEvaluationReports(
  page = 1,
  pageSize = 20
): Promise<{ reports: EvaluationReportSummary[]; total: number }> {
  const res = await request.get(API_ENDPOINTS.evaluationReports, {
    params: { page, page_size: pageSize },
  });
  return res.data;
}

// 获取评估报告详情
export async function getEvaluationReportDetail(
  runId: string
): Promise<EvaluationReportDetail> {
  const res = await request.get(API_ENDPOINTS.evaluationReportDetail(runId));
  return res.data;
}
