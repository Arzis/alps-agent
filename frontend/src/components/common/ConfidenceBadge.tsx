import React from 'react';
import { Tag, Tooltip, Progress } from 'antd';

interface ConfidenceBadgeProps {
  value: number; // 0-1
  showProgress?: boolean;
  size?: 'small' | 'default';
}

const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  value,
  showProgress = false,
  size = 'default',
}) => {
  const getColor = (v: number) => {
    if (v >= 0.8) return 'green';
    if (v >= 0.5) return 'orange';
    return 'red';
  };

  const getText = (v: number) => {
    if (v >= 0.8) return '高';
    if (v >= 0.5) return '中';
    return '低';
  };

  const color = getColor(value);
  const text = getText(value);
  const percentage = Math.round(value * 100);

  const colorMap: Record<string, string> = {
    green: '#52c41a',
    orange: '#faad14',
    red: '#ff4d4f',
  };

  if (showProgress) {
    return (
      <Tooltip title={`置信度: ${percentage}% (${text})`}>
        <div className="flex items-center gap-2">
          <Progress
            percent={percentage}
            size="small"
            strokeColor={colorMap[color]}
            showInfo={false}
            style={{ width: size === 'small' ? 60 : 80 }}
          />
          <span className="text-xs text-gray-500">{percentage}%</span>
        </div>
      </Tooltip>
    );
  }

  return (
    <Tooltip title={`置信度: ${percentage}% (${text})`}>
      <Tag color={color}>
        置信度 {percentage}%
      </Tag>
    </Tooltip>
  );
};

export default ConfidenceBadge;
