import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Skeleton } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { getEvaluationReports } from '@/services/evaluationService';
import type { EvaluationReportSummary } from '@/types/evaluation';
import MetricCard from '@/components/charts/MetricCard';

const EvalDashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState<EvaluationReportSummary[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await getEvaluationReports(1, 5);
        setReports(data.reports);
      } catch (error) {
        console.error('Failed to load reports:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // 计算平均值
  const latestReport = reports[0];
  const avgFaithfulness = latestReport?.metrics?.faithfulness ?? 0;
  const avgRelevancy = latestReport?.metrics?.answer_relevancy ?? 0;
  const avgPrecision = latestReport?.metrics?.context_precision ?? 0;
  const avgRecall = latestReport?.metrics?.context_recall ?? 0;

  if (loading) {
    return <Skeleton active />;
  }

  return (
    <div className="space-y-6">
      {/* 指标卡片 */}
      <Row gutter={16}>
        <Col span={6}>
          <MetricCard
            title="忠实度 (Faithfulness)"
            value={avgFaithfulness}
            precision={2}
            trend={3}
            trendLabel="较上期"
            color="#52c41a"
            tooltip="回答与上下文的匹配程度"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="答案相关性"
            value={avgRelevancy}
            precision={2}
            trend={5}
            trendLabel="较上期"
            color="#52c41a"
            tooltip="回答与问题的相关程度"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="上下文精度"
            value={avgPrecision}
            precision={2}
            trend={8}
            trendLabel="较上期"
            color="#52c41a"
            tooltip="检索到的上下文的相关程度"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="上下文召回"
            value={avgRecall}
            precision={2}
            trend={4}
            trendLabel="较上期"
            color="#52c41a"
            tooltip="检索到的上下文覆盖答案的程度"
          />
        </Col>
      </Row>

      {/* 最新评估详情 */}
      {latestReport && (
        <Card title="最新评估基线">
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="评估名称"
                value={latestReport.name}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="样本数量"
                value={latestReport.dataset_size}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="状态"
                value={latestReport.status === 'completed' ? '已完成' : '处理中'}
                valueStyle={{
                  color: latestReport.status === 'completed' ? '#52c41a' : '#faad14',
                }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="评估时间"
                value={new Date(latestReport.created_at).toLocaleDateString()}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* 质量指标说明 */}
      <Card title="质量指标说明">
        <Row gutter={16}>
          <Col span={12}>
            <div className="mb-4">
              <h4 className="font-medium mb-2">Faithfulness (忠实度)</h4>
              <p className="text-sm text-gray-600">
                衡量生成的回答是否忠实于检索到的上下文。当回答中的陈述都可以从上下文中推断出来时，忠实度得分高。
              </p>
              <Progress
                percent={Math.round(avgFaithfulness * 100)}
                strokeColor="#52c41a"
                className="mt-2"
              />
            </div>
            <div className="mb-4">
              <h4 className="font-medium mb-2">Answer Relevancy (答案相关性)</h4>
              <p className="text-sm text-gray-600">
                衡量回答与问题的相关程度。相关回答应该直接针对问题，不包含冗余信息。
              </p>
              <Progress
                percent={Math.round(avgRelevancy * 100)}
                strokeColor="#1677ff"
                className="mt-2"
              />
            </div>
          </Col>
          <Col span={12}>
            <div className="mb-4">
              <h4 className="font-medium mb-2">Context Precision (上下文精度)</h4>
              <p className="text-sm text-gray-600">
                衡量检索到的上下文片段与问题的相关程度。高精度意味着排序靠前的片段更相关。
              </p>
              <Progress
                percent={Math.round(avgPrecision * 100)}
                strokeColor="#faad14"
                className="mt-2"
              />
            </div>
            <div className="mb-4">
              <h4 className="font-medium mb-2">Context Recall (上下文召回)</h4>
              <p className="text-sm text-gray-600">
                衡量检索到的上下文是否覆盖了回答问题所需的全部信息。
              </p>
              <Progress
                percent={Math.round(avgRecall * 100)}
                strokeColor="#722ed1"
                className="mt-2"
              />
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default EvalDashboard;
