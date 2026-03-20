import React from 'react';
import { Spin } from 'antd';

interface LoadingProps {
  tip?: string;
  size?: 'small' | 'default' | 'large';
  fullscreen?: boolean;
}

const Loading: React.FC<LoadingProps> = ({
  tip = '加载中...',
  size = 'default',
  fullscreen = false,
}) => {
  const spin = <Spin tip={tip} size={size} />;

  if (fullscreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/80 z-50">
        {spin}
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center py-8">
      {spin}
    </div>
  );
};

export default Loading;
