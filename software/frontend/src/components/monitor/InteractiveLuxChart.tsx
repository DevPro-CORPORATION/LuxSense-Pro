import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import * as echarts from 'echarts';
import { useTheme } from '../../context/ThemeContext';

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
  const { resolvedTheme } = useTheme();
  const isLight = resolvedTheme === 'light';
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

    const chart = echarts.init(chartRef.current, isLight ? undefined : 'dark', {
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
            color: isLight ? '#94A3B8' : '#4F5B73',
            type: 'dashed'
          },
          crossStyle: {
            color: '#21D789'
          }
        },
        backgroundColor: isLight ? '#FFFFFF' : '#161920',
        borderColor: isLight ? '#CBD5E1' : '#2B3240',
        textStyle: {
          color: isLight ? '#0F172A' : '#DFE2E8',
          fontFamily: 'JetBrains Mono',
          fontSize: 11
        },
        formatter: (params: any) => {
          if (!params || !params[0]) return '';
          const pt = params[0];
          return `
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">
              <div style="color: ${isLight ? '#64748B' : '#8C96A8'}; margin-bottom: 4px;">T: ${pt.name}</div>
              <div style="color: ${isLight ? '#059669' : '#21D789'}; font-weight: bold;">CALIBRATED: ${Number(pt.value).toFixed(2)} lx</div>
              ${params[1] ? `<div style="color: ${isLight ? '#2563EB' : '#61AFEF'};">RAW SENSOR: ${Number(params[1].value).toFixed(2)} lx</div>` : ''}
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
        data: dataSeries.current.map(d => d.time),
        axisLine: { lineStyle: { color: isLight ? '#CBD5E1' : '#272C38' } },
        axisLabel: {
          color: isLight ? '#64748B' : '#6F788A',
          fontFamily: 'JetBrains Mono',
          fontSize: 10,
          interval: 'auto',
          showMaxLabel: true
        },
        splitLine: {
          show: true,
          lineStyle: {
            color: isLight ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.03)',
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
          color: isLight ? '#64748B' : '#6F788A',
          fontFamily: 'JetBrains Mono',
          fontSize: 10,
          formatter: '{value} lx'
        },
        splitLine: {
          lineStyle: {
            color: isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.04)',
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
            color: isLight ? '#059669' : '#21D789',
            width: 2,
            shadowColor: isLight ? 'rgba(5, 150, 105, 0.25)' : 'rgba(33, 215, 137, 0.35)',
            shadowBlur: 8
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: isLight ? 'rgba(5, 150, 105, 0.20)' : 'rgba(33, 215, 137, 0.22)' },
              { offset: 0.8, color: isLight ? 'rgba(5, 150, 105, 0.03)' : 'rgba(33, 215, 137, 0.02)' },
              { offset: 1, color: 'transparent' }
            ])
          },
          data: dataSeries.current.map(d => d.lux)
        },
        {
          name: 'Raw Sensor',
          type: 'line',
          smooth: 0.2,
          showSymbol: false,
          lineStyle: {
            color: isLight ? '#2563EB' : '#61AFEF',
            width: 1,
            type: 'dotted',
            opacity: 0.6
          },
          data: dataSeries.current.map(d => d.raw)
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
  }, [resolvedTheme]);

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

    // Calculate max points based on sample rate (~4.0 Hz)
    const maxPoints = Math.max(20, Math.floor(timeWindowSeconds * 4.0));
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

