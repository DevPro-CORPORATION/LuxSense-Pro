import React, { useState, useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { bridge, CalibrationProfile, TelemetryPacket } from '../../bridge/bridgeClient';
import { 
  Sliders, 
  Check, 
  Save, 
  RotateCcw, 
  ShieldAlert, 
  FileText, 
  Sparkles,
  Info,
  CheckCircle2
} from 'lucide-react';

interface CalibrationLaboratoryProps {
  currentPacket: TelemetryPacket | null;
  onCalibrationSaved: (profile: CalibrationProfile) => void;
}

export const CalibrationLaboratory: React.FC<CalibrationLaboratoryProps> = ({
  currentPacket,
  onCalibrationSaved
}) => {
  const [zeroOffset, setZeroOffset] = useState<number>(0.0);
  const [gainMultiplier, setGainMultiplier] = useState<number>(1.0);
  const [profileName, setProfileName] = useState<string>('Standard Factory (BH1750)');
  const [notes, setNotes] = useState<string>('Standard BH1750 high-resolution photopic curve');
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  // Load existing profile from backend
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const cal = await bridge.getCalibration();
        if (cal) {
          setZeroOffset(cal.zero_offset);
          setGainMultiplier(cal.gain_multiplier);
          setProfileName(cal.profile_name || 'Standard Factory (BH1750)');
          setNotes(cal.notes || '');
        }
      } catch (err) {
        console.error('Failed to load calibration:', err);
      }
    };
    loadProfile();
  }, []);

  // Update ECharts dual-axis transfer curve
  useEffect(() => {
    if (!chartRef.current) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, 'dark');
      const ro = new ResizeObserver(() => chartInstance.current?.resize());
      ro.observe(chartRef.current);
    }

    const rawDomain = [0, 200, 500, 1000, 2000, 5000, 10000];
    const transferCurve = rawDomain.map(x => [x, Math.max(0, (x + zeroOffset) * gainMultiplier)]);
    const identityCurve = rawDomain.map(x => [x, x]);

    // Current operating point
    const liveRaw = currentPacket ? currentPacket.raw_lux : 0;
    const liveCal = Math.max(0, (liveRaw + zeroOffset) * gainMultiplier);

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      title: {
        text: 'Optical Transfer Function: f(x) = (x + Offset) × Gain',
        left: 0,
        textStyle: {
          color: '#DFE2E8',
          fontSize: 12,
          fontFamily: 'JetBrains Mono',
          fontWeight: 600
        }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#161920',
        borderColor: '#2B3240',
        textStyle: { color: '#DFE2E8', fontFamily: 'JetBrains Mono', fontSize: 11 },
        formatter: (params: any) => {
          if (!params || !params[0]) return '';
          return `
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">
              <div>Raw Photodiode: <strong>${params[0].value[0]} lx</strong></div>
              <div style="color: #21D789;">Calibrated Output: <strong>${Number(params[0].value[1]).toFixed(2)} lx</strong></div>
            </div>
          `;
        }
      },
      legend: {
        right: 10,
        top: 0,
        textStyle: { color: '#8C96A8', fontFamily: 'JetBrains Mono', fontSize: 10 }
      },
      grid: {
        top: 40,
        left: 55,
        right: 30,
        bottom: 35
      },
      xAxis: {
        type: 'value',
        name: 'Raw (lx)',
        nameTextStyle: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 },
        axisLine: { lineStyle: { color: '#272C38' } },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.04)' } },
        axisLabel: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        name: 'Calibrated (lx)',
        nameTextStyle: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.04)' } },
        axisLabel: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 }
      },
      series: [
        {
          name: 'Calibrated Curve',
          type: 'line',
          smooth: true,
          data: transferCurve,
          lineStyle: { color: '#21D789', width: 2.5 },
          showSymbol: false,
          markPoint: {
            data: [
              {
                name: 'Live Operating Point',
                coord: [liveRaw, liveCal],
                value: `${liveCal.toFixed(1)} lx`,
                itemStyle: { color: '#E5C07B' }
              }
            ]
          }
        },
        {
          name: '1:1 Unity Line',
          type: 'line',
          data: identityCurve,
          lineStyle: { color: '#4F5B73', type: 'dashed', width: 1.5 },
          showSymbol: false
        }
      ]
    };

    chartInstance.current.setOption(option);
  }, [zeroOffset, gainMultiplier, currentPacket]);

  // Metrology presets
  const presets = [
    {
      name: 'Factory BH1750 (Raw Metrology)',
      offset: 0.0,
      gain: 1.0000,
      desc: 'Unadjusted factory photodiode response curve.'
    },
    {
      name: 'Diffuser Shield / ND Filter',
      offset: 0.0,
      gain: 1.4250,
      desc: 'Compensates for acrylic diffusion dome absorption (-29.8% attenuation).'
    },
    {
      name: 'Low-Light Cleanroom Lab',
      offset: -0.15,
      gain: 1.0500,
      desc: 'Dark current subtraction for sub-lux precision photometrics.'
    },
    {
      name: 'High-Intensity Solar Attenuation',
      offset: 0.0,
      gain: 0.8800,
      desc: 'Spectral correction for outdoor high-radiance saturation limit.'
    }
  ];

  const handleApplyPreset = (p: typeof presets[0]) => {
    setProfileName(p.name);
    setZeroOffset(p.offset);
    setGainMultiplier(p.gain);
    setNotes(p.desc);
  };

  const handleSave = async () => {
    setSaveStatus('Saving calibration profile...');
    try {
      const ok = await bridge.saveCalibration(zeroOffset, gainMultiplier, notes);
      if (ok) {
        setSaveStatus('Calibration successfully written to %APPDATA% & applied to live pipeline.');
        onCalibrationSaved({
          profile_name: profileName,
          zero_offset: zeroOffset,
          gain_multiplier: gainMultiplier,
          calibrated_at: new Date().toISOString(),
          notes: notes
        });
        setTimeout(() => setSaveStatus(null), 4000);
      } else {
        setSaveStatus('Error saving profile.');
      }
    } catch (e) {
      setSaveStatus('Failed to write calibration.');
    }
  };

  const liveRaw = currentPacket ? currentPacket.raw_lux : 0.0;
  const liveCal = Math.max(0, (liveRaw + zeroOffset) * gainMultiplier);

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-chassis-950 p-4 rounded-xl border border-border">
        <div>
          <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-metrology-green" />
            <span>Photometric Calibration Laboratory</span>
          </h2>
          <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
            Calibrate dark zero offset and optical gain multiplier with transfer curve visualization.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleApplyPreset(presets[0])}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-chassis-850 border border-border text-xs font-mono text-zinc-300 hover:border-border-focus transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>RESET TO FACTORY</span>
          </button>

          <button
            onClick={handleSave}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded bg-metrology-green text-chassis-950 text-xs font-mono font-bold hover:bg-metrology-green/90 transition-colors shadow-glow-green"
          >
            <Save className="w-3.5 h-3.5" />
            <span>SAVE CALIBRATION</span>
          </button>
        </div>
      </div>

      {saveStatus && (
        <div className="bg-metrology-green/10 border border-metrology-green/40 p-2.5 rounded-lg text-xs font-mono text-metrology-green flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{saveStatus}</span>
        </div>
      )}

      {/* Main Grid: Controls & Transfer Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
        {/* Left: Transfer Function Curve Chart */}
        <div className="lg:col-span-7 bg-chassis-950 border border-border rounded-xl p-4 flex flex-col min-h-[380px]">
          <div ref={chartRef} className="w-full h-full flex-1" />

          {/* Real-time operating transfer snapshot */}
          <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs font-mono bg-chassis-900/60 p-2.5 rounded">
            <div className="flex items-center space-x-2">
              <span className="text-zinc-400">CURRENT LIVE SENSOR:</span>
              <span className="text-zinc-200 font-bold">{liveRaw.toFixed(2)} lx</span>
            </div>
            <div className="text-zinc-500">&rarr;</div>
            <div className="flex items-center space-x-2">
              <span className="text-zinc-400">CORRECTED OUTPUT:</span>
              <span className="text-metrology-green font-bold">{liveCal.toFixed(2)} lx</span>
            </div>
            <div className="text-[10px] text-zinc-400">
              Δ {(liveCal - liveRaw >= 0 ? '+' : '') + (liveCal - liveRaw).toFixed(2)} lx
            </div>
          </div>
        </div>

        {/* Right: Parameter Adjustments & Presets */}
        <div className="lg:col-span-5 space-y-4 flex flex-col">
          {/* Sliders Card */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-4">
            <div className="text-xs font-mono font-semibold text-zinc-200 uppercase tracking-wider border-b border-border pb-2">
              Correction Coefficients
            </div>

            {/* Dark Current Zero Offset */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-zinc-300">Dark Current Zero Offset (lx):</span>
                <span className="text-metrology-green font-bold num-tabular">
                  {(zeroOffset >= 0 ? '+' : '') + zeroOffset.toFixed(2)} lx
                </span>
              </div>
              <input
                type="range"
                min="-20.0"
                max="20.0"
                step="0.05"
                value={zeroOffset}
                onChange={(e) => setZeroOffset(parseFloat(e.target.value))}
                className="w-full accent-metrology-green h-1.5 bg-chassis-800 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-zinc-400">
                <span>-20.00 lx</span>
                <span>0.00 (Null)</span>
                <span>+20.00 lx</span>
              </div>
            </div>

            {/* Optical Gain Multiplier */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-zinc-300">Optical Gain Multiplier (k):</span>
                <span className="text-metrology-green font-bold num-tabular">
                  {gainMultiplier.toFixed(4)}x
                </span>
              </div>
              <input
                type="range"
                min="0.2000"
                max="3.0000"
                step="0.005"
                value={gainMultiplier}
                onChange={(e) => setGainMultiplier(parseFloat(e.target.value))}
                className="w-full accent-metrology-green h-1.5 bg-chassis-800 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[10px] font-mono text-zinc-400">
                <span>0.2000x</span>
                <span>1.0000 (Unity)</span>
                <span>3.0000x</span>
              </div>
            </div>

            {/* Notes / Certificate details */}
            <div className="pt-2">
              <label className="text-[11px] font-mono text-zinc-400 block mb-1">
                Calibration Certificate / Technician Log:
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full bg-chassis-900 border border-border rounded p-2 text-xs font-mono text-zinc-200 focus:border-border-focus focus:outline-none resize-none"
                placeholder="Enter optical bench certificate or diffusion parameters..."
              />
            </div>
          </div>

          {/* Presets List */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 flex-1">
            <div className="text-xs font-mono font-semibold text-zinc-200 uppercase tracking-wider border-b border-border pb-2 mb-3">
              Standard Calibration Presets
            </div>

            <div className="space-y-2">
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleApplyPreset(p)}
                  className={`w-full text-left p-2.5 rounded-lg border transition-all text-xs font-mono ${
                    profileName === p.name 
                      ? 'bg-chassis-800 border-metrology-green/50 text-white' 
                      : 'bg-chassis-900 border-border text-zinc-400 hover:border-border-focus hover:text-zinc-200'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span>{p.name}</span>
                    <span className="text-[10px] text-metrology-green">
                      k={p.gain.toFixed(4)}x
                    </span>
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-0.5">
                    {p.desc}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
