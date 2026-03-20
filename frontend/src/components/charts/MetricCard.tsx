import React from 'react';
import { Card, Statistic, Tooltip } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';

interface MetricCardProps {
  title: string;
  value: number | string;
  suffix?: string;
  precision?: number;
  trend?: number;
  trendLabel?: string;
  color?: string;
  tooltip?: string;
  loading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  suffix,
  precision = 0,
  trend,
  trendLabel,
  color,
  tooltip,
  loading = false,
}) => {
  return (
    <Card size="small" loading={loading}>
      <Statistic
        title={
          <span className="flex items-center gap-1">
            {title}
            {tooltip && (
              <Tooltip title={tooltip}>
                <InfoCircleOutlined className="text-gray-400 text-xs cursor-help" />
              </Tooltip>
            )}
          </span>
        }
        value={value}
        suffix={suffix}
        precision={precision}
        valueStyle={{ color }}
      />
      {trend !== undefined && (
        <div
          className={`text-xs mt-1 ${
            trend >= 0 ? 'text-green-500' : 'text-red-500'
          }`}
        >
          {trend >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          {' '}
          {Math.abs(trend)}% {trendLabel || '较上期'}
        </div>
      )}
    </Card>
  );
};

export default MetricCard;
