import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import * as echarts from 'echarts';

interface DataPoint {
  time: string;
  lux: number;
  raw: number;
  packetId: number;
}

interface InteractiveLuxChartProps {
  latestLux: number;
  latestRaw: number;
  latestTime: string;
  packetId: number;
  timeWindowSeconds?: number;
  isPaused?: boolean;
}

export interface LuxChartHandle {
  resetData: () => void;
}

export const InteractiveLuxChart = forwardRef<LuxChartHandle, InteractiveLuxChartProps>(({
  latestLux,
  latestRaw,
  latestTime,
  packetId,
  timeWindowSeconds = 30,
  isPaused = false
}, ref) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const dataSeries = useRef<DataPoint[]>([]);
  const [peakLux, setPeakLux] = useState<number>(0);

  useImperativeHandle(ref, () => ({
    resetData: () => {
      dataSeries.current = [];
      setPeakLux(0);
      if (chartInstance.current) {
        chartInstance.current.setOption({
          series: [
            { data: [] },
            { data: [] }
          ]
        });
      }
    }
  }));

  // Initialize ECharts instance
  useEffect(() => {
    if (!chartRef.current) return;

    const chart = echarts.init(chartRef.current, 'dark', {
      renderer: 'canvas',
    });
    chartInstance.current = chart;

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      animation: false, // Turn off for real-time 60fps streaming smoothness
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          lineStyle: {
            color: '#4F5B73',
            type: 'dashed'
          },
          crossStyle: {
            color: '#21D789'
          }
        },
        backgroundColor: '#161920',
        borderColor: '#2B3240',
        textStyle: {
          color: '#DFE2E8',
          fontFamily: 'JetBrains Mono',
          fontSize: 11
        },
        formatter: (params: any) => {
          if (!params || !params[0]) return '';
          const pt = params[0];
          return `
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">
              <div style="color: #8C96A8; margin-bottom: 4px;">T: ${pt.name}</div>
              <div style="color: #21D789; font-weight: bold;">CALIBRATED: ${Number(pt.value).toFixed(2)} lx</div>
              ${params[1] ? `<div style="color: #61AFEF;">RAW SENSOR: ${Number(params[1].value).toFixed(2)} lx</div>` : ''}
            </div>
          `;
        }
      },
      grid: {
        top: 24,
        left: 56,
        right: 24,
        bottom: 36,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: [],
        axisLine: { lineStyle: { color: '#272C38' } },
        axisLabel: {
          color: '#6F788A',
          fontFamily: 'JetBrains Mono',
          fontSize: 10,
          interval: 'auto',
          showMaxLabel: true
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.03)',
            type: 'dashed'
          }
        }
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#6F788A',
          fontFamily: 'JetBrains Mono',
          fontSize: 10,
          formatter: '{value} lx'
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.04)',
            type: 'solid'
          }
        }
      },
      series: [
        {
          name: 'Calibrated Lux',
          type: 'line',
          smooth: 0.25,
          showSymbol: false,
          sampling: 'lttb',
          lineStyle: {
            color: '#21D789',
            width: 2,
            shadowColor: 'rgba(33, 215, 137, 0.35)',
            shadowBlur: 8
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(33, 215, 137, 0.22)' },
              { offset: 0.8, color: 'rgba(33, 215, 137, 0.02)' },
              { offset: 1, color: 'transparent' }
            ])
          },
          data: []
        },
        {
          name: 'Raw Sensor',
          type: 'line',
          smooth: 0.2,
          showSymbol: false,
          lineStyle: {
            color: '#61AFEF',
            width: 1,
            type: 'dotted',
            opacity: 0.6
          },
          data: []
        }
      ]
    };

    chart.setOption(option);

    const resizeObserver = new ResizeObserver(() => {
      chart.resize();
    });
    resizeObserver.observe(chartRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.dispose();
      chartInstance.current = null;
    };
  }, []);

  // Append incoming data
  useEffect(() => {
    if (isPaused || !chartInstance.current) return;
    if (packetId === 0 && latestLux === 0 && latestRaw === 0) return;

    const newPt: DataPoint = {
      time: latestTime,
      lux: latestLux,
      raw: latestRaw,
      packetId: packetId
    };

    // Calculate max points based on sample rate (~2.5 Hz)
    const maxPoints = Math.max(20, Math.floor(timeWindowSeconds * 2.5));
    dataSeries.current.push(newPt);
    if (dataSeries.current.length > maxPoints) {
      dataSeries.current.shift();
    }

    if (latestLux > peakLux) {
      setPeakLux(latestLux);
    }

    const categories = dataSeries.current.map(d => d.time);
    const calData = dataSeries.current.map(d => d.lux);
    const rawData = dataSeries.current.map(d => d.raw);

    chartInstance.current.setOption({
      xAxis: {
        data: categories
      },
      series: [
        {
          name: 'Calibrated Lux',
          data: calData
        },
        {
          name: 'Raw Sensor',
          data: rawData
        }
      ]
    });
  }, [packetId, latestLux, latestRaw, latestTime, isPaused, timeWindowSeconds, peakLux]);

  return (
    <div className="w-full h-full relative">
      <div ref={chartRef} className="w-full h-full" />
      {peakLux > 0 && (
        <div className="absolute top-2 right-4 text-[10px] font-mono text-zinc-400 bg-chassis-950/80 px-2 py-0.5 rounded border border-border/60">
          PEAK HOLD: <span className="text-metrology-green font-bold">{peakLux.toFixed(2)} lx</span>
        </div>
      )}
    </div>
  );
});

InteractiveLuxChart.displayName = 'InteractiveLuxChart';

