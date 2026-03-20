import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Tag, Button, Skeleton, Select, DatePicker } from 'antd';
import {
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import MetricCard from '@/components/charts/MetricCard';
import LineChart from '@/components/charts/LineChart';
import dayjs from 'dayjs';

const MonitoringPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('1h');

  useEffect(() => {
    // 模拟加载
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  // 模拟数据
  const mockMetrics = {
    qps: 42,
    p95Latency: 3.2,
    cacheHitRate: 35,
    fallbackRate: 8,
  };

  const timeOptions = [
    { label: '最近1小时', value: '1h' },
    { label: '最近6小时', value: '6h' },
    { label: '最近24小时', value: '24h' },
    { label: '最近7天', value: '7d' },
  ];

  const chartData = {
    xAxis: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00'],
    series: [
      {
        name: '请求量',
        data: [35, 42, 38, 55, 48, 42],
        color: '#1677ff',
      },
    ],
  };

  const latencyData = {
    xAxis: ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00'],
    series: [
      {
        name: 'P95延迟',
        data: [3.5, 3.2, 3.8, 2.9, 3.2, 3.2],
        color: '#faad14',
      },
    ],
  };

  const services = [
    { name: 'PostgreSQL', status: 'healthy' },
    { name: 'Redis', status: 'healthy' },
    { name: 'Milvus', status: 'healthy' },
    { name: 'OpenAI API', status: 'healthy' },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleOutlined className="text-green-500" />;
      case 'degraded':
        return <ExclamationCircleOutlined className="text-yellow-500" />;
      case 'down':
        return <CloseCircleOutlined className="text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      healthy: { color: 'success', text: '正常' },
      degraded: { color: 'warning', text: '降级' },
      down: { color: 'error', text: '故障' },
    };
    const { color, text } = statusMap[status] || { color: 'default', text: status };
    return <Tag color={color}>{text}</Tag>;
  };

  if (loading) {
    return <Skeleton active />;
  }

  return (
    <div className="space-y-6">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">系统监控</h1>
          <p className="text-sm text-gray-500 mt-1">
            实时监控 RAG 系统运行状态和性能指标
          </p>
        </div>
        <div className="flex gap-2">
          <Select
            value={timeRange}
            onChange={setTimeRange}
            options={timeOptions}
            style={{ width: 120 }}
          />
          <Button icon={<ReloadOutlined />}>刷新</Button>
        </div>
      </div>

      {/* 指标卡片 */}
      <Row gutter={16}>
        <Col span={6}>
          <MetricCard
            title="请求 QPS"
            value={mockMetrics.qps}
            suffix="/s"
            trend={12}
            trendLabel="较上期"
            color="#1677ff"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="P95 延迟"
            value={mockMetrics.p95Latency}
            suffix="s"
            trend={-9}
            trendLabel="较上期"
            color="#faad14"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="缓存命中率"
            value={mockMetrics.cacheHitRate}
            suffix="%"
            trend={5}
            trendLabel="较上期"
            color="#52c41a"
          />
        </Col>
        <Col span={6}>
          <MetricCard
            title="降级比例"
            value={mockMetrics.fallbackRate}
            suffix="%"
            trend={-2}
            trendLabel="较上期"
            color="#722ed1"
          />
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="请求量趋势">
            <LineChart
              xAxis={chartData.xAxis}
              series={chartData.series}
              height={250}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="延迟分布">
            <LineChart
              xAxis={latencyData.xAxis}
              series={latencyData.series}
              height={250}
            />
          </Card>
        </Col>
      </Row>

      {/* 服务状态 */}
      <Card title="服务健康状态">
        <Row gutter={16}>
          {services.map((service) => (
            <Col span={6} key={service.name}>
              <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                {getStatusIcon(service.status)}
                <div>
                  <div className="font-medium">{service.name}</div>
                  {getStatusTag(service.status)}
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 熔断器状态 */}
      <Card title="熔断器状态">
        <Row gutter={16}>
          {[
            { name: 'LLM 调用', failures: 0, max: 5, status: 'closed' },
            { name: 'Milvus 查询', failures: 0, max: 3, status: 'closed' },
            { name: 'Redis 查询', failures: 0, max: 3, status: 'closed' },
          ].map((cb) => (
            <Col span={8} key={cb.name}>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{cb.name}</span>
                  {cb.status === 'closed' ? (
                    <Tag color="success">关闭</Tag>
                  ) : (
                    <Tag color="warning">半开</Tag>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {cb.failures}/{cb.max} failures
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );
};

export default MonitoringPage;
