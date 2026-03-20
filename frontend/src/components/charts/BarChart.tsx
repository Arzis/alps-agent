import React from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface BarChartProps {
  xAxis: string[];
  series: Array<{
    name: string;
    data: (string | number)[];
    color?: string;
  }>;
  height?: number;
  title?: string;
}

const BarChart: React.FC<BarChartProps> = ({
  xAxis,
  series,
  height = 300,
  title,
}) => {
  const option: EChartsOption = {
    title: title
      ? {
          text: title,
          left: 'center',
          textStyle: {
            fontSize: 16,
            fontWeight: 'normal',
          },
        }
      : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    legend: {
      data: series.map((s) => s.name),
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: title ? '15%' : '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xAxis,
    },
    yAxis: {
      type: 'value',
    },
    series: series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      itemStyle: {
        color: s.color,
      },
      barWidth: '60%',
    })),
  };

  return (
    <ReactECharts option={option} style={{ height }} opts={{ renderer: 'svg' }} />
  );
};

export default BarChart;
