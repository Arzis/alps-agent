import React, { useState, useEffect } from 'react';
import { Card, Row, Col, DatePicker, Select, Skeleton } from 'antd';
import LineChart from '@/components/charts/LineChart';
import { getEvaluationReports } from '@/services/evaluationService';
import type { EvaluationReportSummary } from '@/types/evaluation';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

const TrendCharts: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState<EvaluationReportSummary[]>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await getEvaluationReports(1, 30);
        setReports(data.reports);
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // 准备图表数据
  const prepareChartData = () => {
    const sortedReports = [...reports]
      .sort((a, b) => dayjs(a.created_at).valueOf() - dayjs(b.created_at).valueOf())
      .slice(-14); // 最近14条

    return {
      xAxis: sortedReports.map((r) =>
        dayjs(r.created_at).format('MM-DD')
      ),
      series: [
        {
          name: '忠实度',
          data: sortedReports.map((r) =>
            r.metrics?.faithfulness?.toFixed(2) ?? 0
          ),
          color: '#52c41a',
        },
        {
          name: '答案相关性',
          data: sortedReports.map((r) =>
            r.metrics?.answer_relevancy?.toFixed(2) ?? 0
          ),
          color: '#1677ff',
        },
        {
          name: '上下文精度',
          data: sortedReports.map((r) =>
            r.metrics?.context_precision?.toFixed(2) ?? 0
          ),
          color: '#faad14',
        },
        {
          name: '上下文召回',
          data: sortedReports.map((r) =>
            r.metrics?.context_recall?.toFixed(2) ?? 0
          ),
          color: '#722ed1',
        },
      ],
    };
  };

  if (loading) {
    return <Skeleton active />;
  }

  const chartData = prepareChartData();

  return (
    <div className="space-y-6">
      {/* 筛选栏 */}
      <Card>
        <Row gutter={16}>
          <Col span={8}>
            <span className="text-gray-500 mr-2">时间范围:</span>
            <RangePicker
              style={{ width: 250 }}
              defaultValue={[dayjs().subtract(30, 'day'), dayjs()]}
            />
          </Col>
          <Col span={8}>
            <span className="text-gray-500 mr-2">评估名称:</span>
            <Select
              style={{ width: 200 }}
              placeholder="全部"
              options={[
                { label: '全部', value: 'all' },
                ...reports.map((r) => ({ label: r.name, value: r.name })),
              ]}
            />
          </Col>
        </Row>
      </Card>

      {/* 趋势图 */}
      <Card title="质量趋势 (近14次评估)">
        <LineChart
          xAxis={chartData.xAxis}
          series={chartData.series}
          height={350}
        />
      </Card>

      {/* 指标对比 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="指标分布">
            <div className="space-y-4">
              {chartData.series.map((s) => {
                const avg = s.data.reduce((a, b) => a + parseFloat(b), 0) / s.data.length;
                return (
                  <div key={s.name}>
                    <div className="flex justify-between mb-1">
                      <span>{s.name}</span>
                      <span className="font-medium">
                        {avg.toFixed(2)}
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${avg * 100}%`,
                          backgroundColor: s.color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="指标说明">
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-medium text-green-600">忠实度:</span>
                <span className="text-gray-600 ml-2">
                  回答与上下文的匹配程度
                </span>
              </div>
              <div>
                <span className="font-medium text-blue-600">答案相关性:</span>
                <span className="text-gray-600 ml-2">
                  回答与问题的相关程度
                </span>
              </div>
              <div>
                <span className="font-medium text-yellow-600">上下文精度:</span>
                <span className="text-gray-600 ml-2">
                  检索片段的相关程度
                </span>
              </div>
              <div>
                <span className="font-medium text-purple-600">上下文召回:</span>
                <span className="text-gray-600 ml-2">
                  检索覆盖答案的程度
                </span>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TrendCharts;
