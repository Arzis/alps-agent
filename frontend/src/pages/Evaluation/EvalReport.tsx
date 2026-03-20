import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, Modal, message } from 'antd';
import { EyeOutlined, ReloadOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { getEvaluationReports } from '@/services/evaluationService';
import type { EvaluationReportSummary } from '@/types/evaluation';
import EmptyState from '@/components/common/EmptyState';
import dayjs from 'dayjs';

const EvalReport: React.FC = () => {
  const [reports, setReports] = useState<EvaluationReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const loadReports = async () => {
    try {
      setLoading(true);
      const data = await getEvaluationReports(page, 10);
      setReports(data.reports);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to load reports:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, [page]);

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      completed: { color: 'success', text: '已完成' },
      running: { color: 'processing', text: '运行中' },
      failed: { color: 'error', text: '失败' },
    };
    const { color, text } = statusMap[status] || { color: 'default', text: status };
    return <Tag color={color}>{text}</Tag>;
  };

  const columns: ColumnsType<EvaluationReportSummary> = [
    {
      title: '评估名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <span className="font-medium">{name}</span>,
    },
    {
      title: '样本数',
      dataIndex: 'dataset_size',
      key: 'dataset_size',
      width: 100,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: getStatusTag,
    },
    {
      title: '忠实度',
      dataIndex: ['metrics', 'faithfulness'],
      key: 'faithfulness',
      width: 100,
      render: (v?: number) =>
        v !== undefined ? (
          <span className={v >= 0.8 ? 'text-green-600' : v >= 0.5 ? 'text-orange-500' : 'text-red-500'}>
            {v.toFixed(2)}
          </span>
        ) : (
          '-'
        ),
    },
    {
      title: '答案相关性',
      dataIndex: ['metrics', 'answer_relevancy'],
      key: 'answer_relevancy',
      width: 120,
      render: (v?: number) =>
        v !== undefined ? (
          <span className={v >= 0.8 ? 'text-green-600' : v >= 0.5 ? 'text-orange-500' : 'text-red-500'}>
            {v.toFixed(2)}
          </span>
        ) : (
          '-'
        ),
    },
    {
      title: '评估时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            disabled={record.status !== 'completed'}
          >
            查看
          </Button>
        </Space>
      ),
    },
  ];

  if (reports.length === 0 && !loading) {
    return (
      <EmptyState
        type="default"
        title="暂无评估报告"
        description="运行评估任务以生成报告"
      />
    );
  }

  return (
    <div>
      <Table
        columns={columns}
        dataSource={reports}
        rowKey="run_id"
        loading={loading}
        pagination={{
          current: page,
          total,
          showSizeChanger: false,
          showTotal: (total) => `共 ${total} 条`,
          onChange: (p) => setPage(p),
        }}
      />
    </div>
  );
};

export default EvalReport;
