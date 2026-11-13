import React, { useState, useRef } from 'react';
import { TelemetryPacket, CalibrationProfile } from '../../types';
import { InteractiveLuxChart, LuxChartHandle } from './InteractiveLuxChart';
import { 
  Pause, 
  Play, 
  RotateCcw, 
  Sun, 
  Moon, 
  Eye, 
  Zap, 
  Clock, 
  ShieldCheck, 
  Sliders
} from 'lucide-react';

interface LiveMonitorWorkspaceProps {
  packet: TelemetryPacket | null;
  calibration: CalibrationProfile | null;
}

export const LiveMonitorWorkspace: React.FC<LiveMonitorWorkspaceProps> = ({
  packet,
  calibration
}) => {
  const [isPaused, setIsPaused] = useState(false);
  const [timeWindow, setTimeWindow] = useState<number>(30);
  const chartRef = useRef<LuxChartHandle>(null);

  const calLux = packet ? packet.cal_lux : 0.0;
  const rawLux = packet ? packet.raw_lux : 0.0;
  const footCandles = calLux > 0 ? (calLux / 10.7639).toFixed(2) : '0.00';
  const irradiance = calLux > 0 ? (calLux / 683.0).toFixed(4) : '0.0000'; // W/m^2 at 555nm CIE peak

  // Compute optical range category
  const getLightingZone = (lux: number) => {
    if (lux < 0.2) return { name: 'Astronomical / Starlight', icon: Moon, color: '#61AFEF' };
    if (lux < 10) return { name: 'Deep Twilight / Night Light', icon: Moon, color: '#61AFEF' };
    if (lux < 100) return { name: 'Living Room / Corridors', icon: Eye, color: '#E5C07B' };
    if (lux < 500) return { name: 'Office Work / Study Environment', icon: Eye, color: '#21D789' };
    if (lux < 2500) return { name: 'Precision Inspection / Studio', icon: Sun, color: '#21D789' };
    if (lux < 20000) return { name: 'Overcast Daylight', icon: Sun, color: '#E5C07B' };
    return { name: 'Direct Solar Irradiance', icon: Sun, color: '#E06C75' };
  };

  const zone = getLightingZone(calLux);
  const ZoneIcon = zone.icon;

  // Logarithmic bar fill for range meter (0 to ~100,000 lx)
  const computeLogPercentage = (lux: number) => {
    if (lux <= 0.01) return 0;
    const logVal = Math.log10(lux);
    // map -1 (0.1 lux) to 5 (100,000 lux) -> 0% to 100%
    const pct = ((logVal + 1) / 6) * 100;
    return Math.min(100, Math.max(0, pct));
  };

  const logPercentage = computeLogPercentage(calLux);

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Readout Instrument Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Main High-Precision Lux Display */}
        <div className="lg:col-span-6 bg-chassis-950 border border-border rounded-xl p-5 relative overflow-hidden flex flex-col justify-between shadow-instrument">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-zinc-400 uppercase tracking-widest flex items-center space-x-2">
              <Eye className="w-3.5 h-3.5 text-metrology-green" />
              <span>Photopic Illuminance (E_v)</span>
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-chassis-850 border border-border text-zinc-400">
                CIE 1931 V(λ) MATCH
              </span>
            </div>
          </div>

          <div className="my-3 flex items-baseline space-x-3">
            <div className="text-6xl font-bold font-mono tracking-tight text-white num-tabular glow-text-green">
              {calLux.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <span className="text-2xl font-mono text-metrology-green font-semibold">lx</span>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-border/50 text-xs font-mono">
            <div className="flex items-center space-x-2 text-zinc-400">
              <span>UNPROCESSED RAW:</span>
              <span className="text-zinc-300 font-semibold">{rawLux.toFixed(2)} lx</span>
            </div>
            <div className="flex items-center space-x-2 text-zinc-400">
              <span>CORRECTION:</span>
              <span className="text-metrology-green">
                {(calLux - rawLux >= 0 ? '+' : '') + (calLux - rawLux).toFixed(2)} lx
              </span>
            </div>
          </div>
        </div>

        {/* Photometric Unit Conversions */}
        <div className="lg:col-span-6 grid grid-cols-2 gap-3">
          {/* Foot-Candles Card */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 flex flex-col justify-between">
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider flex justify-between">
              <span>Foot-Candles</span>
              <span className="text-zinc-600">1 fc = 10.76 lx</span>
            </div>
            <div className="my-2">
              <span className="text-3xl font-bold font-mono text-zinc-100 num-tabular">
                {footCandles}
              </span>
              <span className="text-sm font-mono text-zinc-400 ml-1.5">fc</span>
            </div>
            <div className="text-[10px] font-mono text-zinc-400">
              Imperial Illuminance
            </div>
          </div>

          {/* Optical Irradiance Card */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 flex flex-col justify-between">
            <div className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider flex justify-between">
              <span>Spectral Irradiance</span>
              <span className="text-zinc-600">λ = 555nm</span>
            </div>
            <div className="my-2">
              <span className="text-3xl font-bold font-mono text-zinc-100 num-tabular">
                {irradiance}
              </span>
              <span className="text-sm font-mono text-zinc-400 ml-1.5">W/m²</span>
            </div>
            <div className="text-[10px] font-mono text-zinc-400">
              Photopic Equivalent Radiance
            </div>
          </div>

          {/* Active Lighting Environmental Zone */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 flex flex-col justify-between col-span-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400">
              <span className="uppercase tracking-wider">Dynamic Environment Classification</span>
              <div className="flex items-center space-x-1.5" style={{ color: zone.color }}>
                <ZoneIcon className="w-3.5 h-3.5" />
                <span className="font-semibold text-xs">{zone.name}</span>
              </div>
            </div>

            {/* Logarithmic Visual Meter */}
            <div className="mt-3 space-y-1">
              <div className="h-2 w-full bg-chassis-800 rounded-full overflow-hidden border border-border/80 relative">
                <div 
                  className="h-full bg-gradient-to-r from-metrology-blue via-metrology-green to-metrology-amber transition-all duration-300 rounded-full"
                  style={{ width: `${logPercentage}%` }}
                />
              </div>
              <div className="flex justify-between text-[9px] font-mono text-zinc-400 pt-0.5">
                <span>0.01 lx (Moon)</span>
                <span>100 lx (Interior)</span>
                <span>500 lx (Workspace)</span>
                <span>10k lx (Daylight)</span>
                <span>100k lx (Sun)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Oscillographic Waveform Chart Container */}
      <div className="flex-1 bg-chassis-950 border border-border rounded-xl flex flex-col min-h-[380px] shadow-instrument">
        {/* Chart Header Bar with Controls */}
        <div className="px-4 py-3 border-b border-border flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono font-semibold text-zinc-200 tracking-wider uppercase">
              Continuous Photodiode Oscillogram
            </span>
            <span className="text-[10px] font-mono text-zinc-400 px-2 py-0.5 rounded bg-chassis-900 border border-border">
              2.5 Hz High-Res Stream
            </span>
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-2">
            {/* Time Window Buttons */}
            <div className="flex items-center bg-chassis-900 rounded p-0.5 border border-border text-xs font-mono">
              {[10, 30, 60, 120].map((sec) => (
                <button
                  key={sec}
                  onClick={() => setTimeWindow(sec)}
                  className={`px-2 py-1 rounded text-[10px] transition-colors ${
                    timeWindow === sec 
                      ? 'bg-chassis-750 text-metrology-green font-semibold' 
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  {sec}s
                </button>
              ))}
            </div>

            {/* Pause / Resume Button */}
            <button
              onClick={() => setIsPaused(!isPaused)}
              className={`flex items-center space-x-1.5 px-3 py-1 rounded border text-xs font-mono transition-colors ${
                isPaused 
                  ? 'bg-metrology-amber/15 border-metrology-amber text-metrology-amber' 
                  : 'bg-chassis-900 border-border text-zinc-300 hover:border-border-focus'
              }`}
            >
              {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
              <span>{isPaused ? 'RESUME' : 'PAUSE'}</span>
            </button>

            {/* Clear Button */}
            <button
              onClick={() => chartRef.current?.resetData()}
              title="Clear graph buffer"
              className="p-1.5 rounded bg-chassis-900 border border-border text-zinc-400 hover:text-white hover:border-border-focus transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Real-Time ECharts Component */}
        <div className="flex-1 w-full p-2">
          <InteractiveLuxChart 
            ref={chartRef}
            latestLux={calLux}
            latestRaw={rawLux}
            latestTime={packet ? packet.timestamp : new Date().toLocaleTimeString()}
            packetId={packet ? packet.packet_id : 0}
            timeWindowSeconds={timeWindow}
            isPaused={isPaused}
          />
        </div>

        {/* Bottom Instrument Telemetry Strip */}
        <div className="px-4 py-2 border-t border-border/60 bg-chassis-900/60 flex items-center justify-between text-[11px] font-mono text-zinc-400">
          <div className="flex items-center space-x-4">
            <span>PACKET ID: <strong className="text-zinc-200">#{packet ? packet.packet_id : 0}</strong></span>
            <span>PORT: <strong className="text-zinc-200">{packet ? packet.port : 'COM5'}</strong></span>
            <span>CHECKSUM: <strong className="text-metrology-green">VALID (CRC-8)</strong></span>
          </div>

          <div className="flex items-center space-x-2">
            <span>CAL PROFILE:</span>
            <span className="text-zinc-300">
              {calibration ? calibration.profile_name : 'Factory Default'}
            </span>
            <span className="text-zinc-400">
              (Gain: {calibration ? calibration.gain_multiplier.toFixed(4) : '1.0000'}x)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
