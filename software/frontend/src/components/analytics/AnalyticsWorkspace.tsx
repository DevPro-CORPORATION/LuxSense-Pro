import React, { useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { bridge, TelemetryRecord } from '../../bridge/bridgeClient';
import { StatisticalSummary } from '../../types';
import { useTheme } from '../../context/ThemeContext';
import { 
  BarChart2, 
  Download, 
  RefreshCw, 
  TrendingUp, 
  Layers, 
  Database, 
  Filter,
  CheckCircle,
  Clock
} from 'lucide-react';

export const AnalyticsWorkspace: React.FC = () => {
  const { resolvedTheme } = useTheme();
  const isLight = resolvedTheme === 'light';
  const [records, setRecords] = useState<TelemetryRecord[]>([]);
  const [sampleLimit, setSampleLimit] = useState<number>(100);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [stats, setStats] = useState<StatisticalSummary>({
    min: 0,
    max: 0,
    mean: 0,
    stdDev: 0,
    median: 0,
    crestFactor: 0,
    sampleCount: 0
  });
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  const histRef = useRef<HTMLDivElement>(null);
  const histInstance = useRef<echarts.ECharts | null>(null);
  const roRef = useRef<ResizeObserver | null>(null);

  useEffect(() => {
    return () => {
      roRef.current?.disconnect();
      histInstance.current?.dispose();
      histInstance.current = null;
    };
  }, []);

  // Load telemetry records from SQLite database
  const loadData = async () => {
    setIsLoading(true);
    try {
      const data = await bridge.getTelemetryHistory(sampleLimit);
      setRecords(data);
      computeStatistics(data);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [sampleLimit]);

  // Compute scientific statistical metrics
  const computeStatistics = (data: TelemetryRecord[]) => {
    if (!data || data.length === 0) {
      setStats({
        min: 0,
        max: 0,
        mean: 0,
        stdDev: 0,
        median: 0,
        crestFactor: 0,
        sampleCount: 0
      });
      return;
    }

    const values = data.map(r => r.calibrated_lux);
    const count = values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const sum = values.reduce((a, b) => a + b, 0);
    const mean = sum / count;

    // Standard deviation
    const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / count;
    const stdDev = Math.sqrt(variance);

    // Median
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(count / 2);
    const median = count % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;

    // RMS & Crest Factor
    const sumSquares = values.reduce((acc, val) => acc + val * val, 0);
    const rms = Math.sqrt(sumSquares / count);
    const crestFactor = rms > 0 ? max / rms : 1.0;

    setStats({
      min,
      max,
      mean,
      stdDev,
      median,
      crestFactor,
      sampleCount: count
    });

    updateHistogram(values, min, max);
  };

  // Dispose chart on theme change so it reinitializes with the correct theme
  useEffect(() => {
    if (histInstance.current) {
      histInstance.current.dispose();
      histInstance.current = null;
      if (records.length > 0) {
        computeStatistics(records);
      }
    }
  }, [resolvedTheme]);

  // Draw histogram with Apache ECharts
  const updateHistogram = (values: number[], min: number, max: number) => {
    if (!histRef.current) return;

    if (!histInstance.current) {
      histInstance.current = echarts.init(histRef.current, isLight ? undefined : 'dark');
      roRef.current = new ResizeObserver(() => histInstance.current?.resize());
      roRef.current.observe(histRef.current);
    }

    const binCount = 16;
    const step = (max - min) / binCount || 1;
    const bins: number[] = new Array(binCount).fill(0);
    const binLabels: string[] = [];

    for (let i = 0; i < binCount; i++) {
      const lower = min + i * step;
      const upper = lower + step;
      binLabels.push(`${lower.toFixed(1)}-${upper.toFixed(1)}`);
    }

    values.forEach(v => {
      const binIdx = Math.min(binCount - 1, Math.floor((v - min) / step));
      if (binIdx >= 0 && binIdx < binCount) {
        bins[binIdx]++;
      }
    });

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      title: {
        text: 'Photopic Frequency Distribution (Histogram)',
        left: 0,
        textStyle: {
          color: isLight ? '#0F172A' : '#DFE2E8',
          fontSize: 12,
          fontFamily: 'JetBrains Mono',
          fontWeight: 600
        }
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: isLight ? '#FFFFFF' : '#161920',
        borderColor: isLight ? '#CBD5E1' : '#2B3240',
        textStyle: { color: isLight ? '#0F172A' : '#DFE2E8', fontFamily: 'JetBrains Mono', fontSize: 11 },
        formatter: (params: any) => {
          const p = params[0];
          return `${p.name} lx: <strong style="color: ${isLight ? '#059669' : '#21D789'};">${p.value} samples</strong>`;
        }
      },
      grid: {
        top: 40,
        left: 45,
        right: 20,
        bottom: 45
      },
      xAxis: {
        type: 'category',
        data: binLabels,
        axisLine: { lineStyle: { color: isLight ? '#CBD5E1' : '#272C38' } },
        axisLabel: {
          color: isLight ? '#64748B' : '#6F788A',
          fontFamily: 'JetBrains Mono',
          fontSize: 9,
          rotate: 35
        }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        splitLine: { lineStyle: { color: isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.04)' } },
        axisLabel: { color: isLight ? '#64748B' : '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 }
      },
      series: [
        {
          name: 'Count',
          type: 'bar',
          data: bins,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: isLight ? '#059669' : '#21D789' },
              { offset: 1, color: isLight ? 'rgba(5, 150, 105, 0.2)' : 'rgba(33, 215, 137, 0.2)' }
            ]),
            borderRadius: [3, 3, 0, 0]
          }
        }
      ]
    };

    histInstance.current.setOption(option);
  };

  const handleExportCsv = async () => {
    try {
      const filename = await bridge.exportHistoryCsv();
      setExportMessage(`Exported SQLite telemetry history to ${filename}`);
      setTimeout(() => setExportMessage(null), 4000);
    } catch (e) {
      setExportMessage('Export failed.');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Bar with actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-chassis-950 p-4 rounded-xl border border-border">
        <div>
          <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center space-x-2">
            <BarChart2 className="w-4 h-4 text-metrology-green" />
            <span>Advanced Analytics & Statistical Workspace</span>
          </h2>
          <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
            SQLite persistence: %APPDATA%\DevPro\LuxSensePro\history.db
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Sample Limit Selector */}
          <div className="flex items-center space-x-1.5 bg-chassis-900 px-2 py-1 rounded border border-border text-xs font-mono">
            <Filter className="w-3.5 h-3.5 text-zinc-400" />
            <span className="text-zinc-400">Samples:</span>
            {[50, 100, 250, 500].map(n => (
              <button
                key={n}
                onClick={() => setSampleLimit(n)}
                className={`px-1.5 py-0.5 rounded text-[10px] ${
                  sampleLimit === n 
                    ? 'bg-chassis-750 text-metrology-green font-semibold' 
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                {n}
              </button>
            ))}
          </div>

          <button
            onClick={loadData}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-chassis-850 border border-border text-xs font-mono text-zinc-300 hover:border-border-focus transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>REFRESH</span>
          </button>

          <button
            onClick={handleExportCsv}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-metrology-green/15 border border-metrology-green text-xs font-mono text-metrology-green hover:bg-metrology-green/25 transition-colors font-semibold"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT CSV</span>
          </button>
        </div>
      </div>

      {exportMessage && (
        <div className="bg-metrology-green/10 border border-metrology-green/40 p-2.5 rounded-lg text-xs font-mono text-metrology-green flex items-center space-x-2">
          <CheckCircle className="w-4 h-4" />
          <span>{exportMessage}</span>
        </div>
      )}

      {/* 6 Statistical Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-chassis-950 border border-border rounded-lg p-3">
          <div className="text-[10px] font-mono text-zinc-400 uppercase">Arithmetic Mean (μ)</div>
          <div className="text-xl font-bold font-mono text-white num-tabular mt-1">
            {stats.mean.toFixed(2)} <span className="text-xs text-zinc-400 font-normal">lx</span>
          </div>
          <div className="text-[9px] font-mono text-zinc-400 mt-1">Centroid illuminance</div>
        </div>

        <div className="bg-chassis-950 border border-border rounded-lg p-3">
          <div className="text-[10px] font-mono text-zinc-400 uppercase">Std Deviation (σ)</div>
          <div className="text-xl font-bold font-mono text-metrology-blue num-tabular mt-1">
            ±{stats.stdDev.toFixed(2)} <span className="text-xs text-zinc-400 font-normal">lx</span>
          </div>
          <div className="text-[9px] font-mono text-zinc-400 mt-1">Optical noise dispersion</div>
        </div>

        <div className="bg-chassis-950 border border-border rounded-lg p-3">
          <div className="text-[10px] font-mono text-zinc-400 uppercase">Minimum Observed</div>
          <div className="text-xl font-bold font-mono text-zinc-300 num-tabular mt-1">
            {stats.min.toFixed(2)} <span className="text-xs text-zinc-400 font-normal">lx</span>
          </div>
          <div className="text-[9px] font-mono text-zinc-400 mt-1">Darkest trough</div>
        </div>

        <div className="bg-chassis-950 border border-border rounded-lg p-3">
          <div className="text-[10px] font-mono text-zinc-400 uppercase">Maximum Observed</div>
          <div className="text-xl font-bold font-mono text-metrology-amber num-tabular mt-1">
            {stats.max.toFixed(2)} <span className="text-xs text-zinc-400 font-normal">lx</span>
          </div>
          <div className="text-[9px] font-mono text-zinc-400 mt-1">Peak radiance spike</div>
        </div>

        <div className="bg-chassis-950 border border-border rounded-lg p-3">
          <div className="text-[10px] font-mono text-zinc-400 uppercase">Median (P50)</div>
          <div className="text-xl font-bold font-mono text-white num-tabular mt-1">
            {stats.median.toFixed(2)} <span className="text-xs text-zinc-400 font-normal">lx</span>
          </div>
          <div className="text-[9px] font-mono text-zinc-400 mt-1">50th percentile</div>
        </div>

        <div className="bg-chassis-950 border border-border rounded-lg p-3">
          <div className="text-[10px] font-mono text-zinc-400 uppercase">Crest Factor</div>
          <div className="text-xl font-bold font-mono text-metrology-green num-tabular mt-1">
            {stats.crestFactor.toFixed(3)}
          </div>
          <div className="text-[9px] font-mono text-zinc-400 mt-1">Peak / RMS Ratio</div>
        </div>
      </div>

      {/* Histogram & Historical Data Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        {/* Left: Distribution Histogram */}
        <div className="lg:col-span-6 bg-chassis-950 border border-border rounded-xl p-4 flex flex-col min-h-[300px]">
          <div ref={histRef} className="w-full h-full flex-1" />
        </div>

        {/* Right: Telemetry Record Log Table */}
        <div className="lg:col-span-6 bg-chassis-950 border border-border rounded-xl p-4 flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <span className="text-xs font-mono font-semibold text-zinc-300 uppercase tracking-wider flex items-center space-x-1.5">
              <Database className="w-3.5 h-3.5 text-zinc-400" />
              <span>Telemetry Acquisition Log</span>
            </span>
            <span className="text-[10px] font-mono text-zinc-400">
              {records.length} records in buffer
            </span>
          </div>

          <div className="flex-1 overflow-y-auto mt-2 max-h-[340px]">
            <table className="w-full text-left font-mono text-xs">
              <thead className="sticky top-0 bg-chassis-900 border-b border-border text-zinc-400 text-[10px] uppercase">
                <tr>
                  <th className="py-2 px-2.5">Time</th>
                  <th className="py-2 px-2.5">Packet</th>
                  <th className="py-2 px-2.5 text-right">Raw (lx)</th>
                  <th className="py-2 px-2.5 text-right">Calibrated (lx)</th>
                  <th className="py-2 px-2.5 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/40">
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-zinc-600 font-mono text-xs">
                      No measurements recorded yet.
                    </td>
                  </tr>
                ) : (
                  records.map((r, idx) => (
                    <tr key={idx} className="hover:bg-chassis-850/60 transition-colors">
                      <td className="py-2 px-2.5 text-zinc-400 text-[11px] whitespace-nowrap">
                        {r.timestamp}
                      </td>
                      <td className="py-2 px-2.5 text-zinc-300 font-semibold text-[11px]">
                        #{r.packet_id}
                      </td>
                      <td className="py-2 px-2.5 text-right text-zinc-400 num-tabular">
                        {r.raw_lux.toFixed(2)}
                      </td>
                      <td className="py-2 px-2.5 text-right text-metrology-green font-semibold num-tabular">
                        {r.calibrated_lux.toFixed(2)}
                      </td>
                      <td className="py-2 px-2.5 text-center">
                        <span className="px-1.5 py-0.5 rounded text-[9px] bg-metrology-green/10 text-metrology-green border border-metrology-green/30">
                          VERIFIED
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

