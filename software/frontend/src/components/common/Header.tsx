import React, { useState, useEffect } from 'react';
import { bridge, TelemetryPacket } from '../../bridge/bridgeClient';
import { 
  Activity, 
  Cpu, 
  Minus, 
  Square, 
  X, 
  Wifi, 
  WifiOff, 
  ShieldCheck, 
  Layers
} from 'lucide-react';

interface HeaderProps {
  currentPacket: TelemetryPacket | null;
  statusMessage: string;
  statusColor: string;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  currentPacket,
  statusMessage,
  statusColor,
  isConnected
}) => {
  const [clock, setClock] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setClock(now.toTimeString().split(' ')[0] + '.' + String(Math.floor(now.getMilliseconds() / 100)));
    };
    updateTime();
    const interval = setInterval(updateTime, 100);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-12 bg-chassis-950 border-b border-border flex items-center justify-between px-4 select-none drag-region">
      {/* Brand & Metrology Instrument Identifier */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-7 h-7 rounded bg-chassis-800 border border-border-focus text-metrology-green shadow-glow-green">
          <Activity className="w-4 h-4" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-xs tracking-wider text-white uppercase">LuxSense Pro</span>
            <span className="text-[10px] px-1.5 py-0.2 bg-chassis-750 text-metrology-green border border-metrology-green/30 rounded font-mono">
              v2.1.0
            </span>
          </div>
          <span className="text-[10px] text-zinc-400 tracking-tight font-mono">
            OPTICAL RADIOMETRY WORKSTATION &bull; DEVRPO-CORP
          </span>
        </div>
      </div>

      {/* Center Instrument Telemetry Status */}
      <div className="hidden md:flex items-center space-x-6 text-xs font-mono">
        <div className="flex items-center space-x-2 bg-chassis-850 px-3 py-1 rounded border border-border">
          <div 
            className="w-2 h-2 rounded-full animate-pulse" 
            style={{ backgroundColor: statusColor || (isConnected ? '#21D789' : '#E06C75') }} 
          />
          <span className="text-zinc-300 font-medium">
            {statusMessage || (isConnected ? 'ACTIVE SAMPLING 2.5Hz' : 'OFFLINE / DISCONNECTED')}
          </span>
        </div>

        <div className="flex items-center space-x-2 text-zinc-400">
          <Cpu className="w-3.5 h-3.5 text-zinc-500" />
          <span>MCU:</span>
          <span className="text-zinc-200">ATmega328P</span>
        </div>

        <div className="flex items-center space-x-2 text-zinc-400">
          <Layers className="w-3.5 h-3.5 text-zinc-500" />
          <span>SENSOR:</span>
          <span className="text-zinc-200">BH1750FVI</span>
        </div>

        {currentPacket && (
          <div className="flex items-center space-x-2 text-zinc-400">
            <ShieldCheck className="w-3.5 h-3.5 text-metrology-green" />
            <span>CIPHER:</span>
            <span className="text-metrology-green font-mono">XOR-128 OK</span>
          </div>
        )}
      </div>

      {/* Right Controls & Clock */}
      <div className="flex items-center space-x-4 no-drag">
        <div className="text-xs font-mono text-zinc-400 hidden sm:block bg-chassis-900 px-2 py-0.5 rounded border border-border/50">
          {clock}
        </div>

        {/* Window action buttons (Qt Shell) */}
        <div className="flex items-center space-x-1 pl-2 border-l border-border">
          <button 
            onClick={() => bridge.minimize()}
            title="Minimize"
            className="w-7 h-7 flex items-center justify-center rounded hover:bg-chassis-800 text-zinc-400 hover:text-white transition-colors"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button 
            onClick={() => bridge.maximize()}
            title="Maximize / Restore"
            className="w-7 h-7 flex items-center justify-center rounded hover:bg-chassis-800 text-zinc-400 hover:text-white transition-colors"
          >
            <Square className="w-3 h-3" />
          </button>
          <button 
            onClick={() => bridge.close()}
            title="Exit"
            className="w-7 h-7 flex items-center justify-center rounded hover:bg-metrology-crimson/20 text-zinc-400 hover:text-metrology-crimson transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
};

