import React, { useState } from 'react';
import { Tabs, Button, message } from 'antd';
import { ReloadOutlined, PlayCircleOutlined } from '@ant-design/icons';
import EvalDashboard from './EvalDashboard';
import EvalReport from './EvalReport';
import TrendCharts from './TrendCharts';

const EvaluationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  const tabs = [
    { key: 'dashboard', label: '评估总览', component: <EvalDashboard key={refreshKey} /> },
    { key: 'reports', label: '评估报告', component: <EvalReport key={refreshKey} /> },
    { key: 'trends', label: '质量趋势', component: <TrendCharts key={refreshKey} /> },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold">评估中心</h1>
          <p className="text-sm text-gray-500 mt-1">
            评估问答质量，监控 RAG 系统性能
          </p>
        </div>
        <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
          刷新
        </Button>
      </div>

      {/* 标签页 */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabs.map((tab) => ({
          key: tab.key,
          label: tab.label,
        }))}
      />

      {/* 内容 */}
      <div className="flex-1 overflow-auto">
        {tabs.find((t) => t.key === activeTab)?.component}
      </div>
    </div>
  );
};

export default EvaluationPage;
