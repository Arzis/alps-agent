import React from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface LineChartProps {
  xAxis: string[];
  series: Array<{
    name: string;
    data: (string | number)[];
    color?: string;
  }>;
  height?: number;
  title?: string;
}

const LineChart: React.FC<LineChartProps> = ({
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
        type: 'cross',
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
      boundaryGap: false,
      data: xAxis,
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: {
        formatter: (value: number) => value.toFixed(1),
      },
    },
    series: series.map((s) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.data,
      lineStyle: {
        width: 2,
      },
      itemStyle: {
        color: s.color,
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: s.color ? `${s.color}40` : '#1677ff40' },
            { offset: 1, color: s.color ? `${s.color}05` : '#1677ff05' },
          ],
        },
      },
    })),
  };

  return (
    <ReactECharts option={option} style={{ height }} opts={{ renderer: 'svg' }} />
  );
};

export default LineChart;
