import React, { useState, useEffect } from 'react';
import { bridge, TelemetryPacket, DeviceStatus } from '../../bridge/bridgeClient';
import { useTheme } from '../../context/ThemeContext';
import { 
  Activity, 
  Cpu, 
  Wifi, 
  WifiOff, 
  ShieldCheck, 
  Layers,
  Sun,
  Moon,
  Radio
} from 'lucide-react';

interface HeaderProps {
  currentPacket: TelemetryPacket | null;
  statusMessage: string;
  statusColor: string;
  hardwareState?: string;
  isConnected: boolean;
  appVersion?: string;
  deviceStatus?: DeviceStatus | null;
}

export const Header: React.FC<HeaderProps> = ({
  currentPacket,
  statusMessage,
  statusColor,
  hardwareState = 'CONNECTING',
  isConnected,
  appVersion = '2.3.2',
  deviceStatus
}) => {
  const { theme, setTheme } = useTheme();
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
    <header className="h-12 bg-chassis-950 border-b border-border flex items-center justify-between px-4 select-none">
      {/* Brand & Metrology Instrument Identifier */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center w-7 h-7 rounded bg-chassis-800 border border-border-focus text-metrology-green shadow-glow-green">
          <Activity className="w-4 h-4" />
        </div>
        <div className="flex flex-col">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-xs tracking-wider text-white uppercase">LuxSense Pro</span>
            <span className="text-[10px] px-1.5 py-0.2 bg-chassis-750 text-metrology-green border border-metrology-green/30 rounded font-mono font-semibold">
              v{appVersion}
            </span>
          </div>
          <span className="text-[10px] text-zinc-400 tracking-tight font-mono">
            OPTICAL RADIOMETRY WORKSTATION &bull; DEVPRO-CORP
          </span>
        </div>
      </div>

      {/* Center Instrument Telemetry Status */}
      <div className="hidden md:flex items-center space-x-3 text-xs font-mono">
        {/* Explicit Hardware State Badge */}
        <div className="flex items-center space-x-2 bg-chassis-850 px-2.5 py-1 rounded border border-border">
          <div 
            className={`w-2.5 h-2.5 rounded-full ${
              hardwareState === 'LIVE MEASUREMENT' ? 'animate-pulse bg-[#21D789]' :
              hardwareState === 'CONNECTING' ? 'animate-ping bg-[#E5C07B]' :
              hardwareState === 'SENSOR DETECTED' ? 'bg-[#61AFEF]' :
              'bg-[#E06C75]'
            }`}
          />
          <span className="font-bold text-[11px] tracking-wider uppercase" style={{
            color: hardwareState === 'LIVE MEASUREMENT' ? '#21D789' :
                   hardwareState === 'CONNECTING' ? '#E5C07B' :
                   hardwareState === 'SENSOR DETECTED' ? '#61AFEF' :
                   '#E06C75'
          }}>
            {hardwareState}
          </span>
        </div>

        {/* Arduino Controller Status Badge */}
        <div className="flex items-center space-x-1.5 bg-chassis-850 px-2.5 py-1 rounded border border-border">
          <Cpu className={`w-3.5 h-3.5 ${
            deviceStatus?.arduino_online ? 'text-metrology-green' : 
            hardwareState === 'CONNECTING' ? 'text-amber-400' : 'text-metrology-crimson'
          }`} />
          <span className="text-[10px] uppercase text-zinc-400">MCU:</span>
          <span className={`text-[11px] font-bold ${
            deviceStatus?.arduino_online ? 'text-metrology-green' : 
            hardwareState === 'CONNECTING' ? 'text-amber-400' : 'text-metrology-crimson'
          }`}>
            {deviceStatus?.arduino_online ? `UNO (${deviceStatus.port || 'USB'})` : 
             hardwareState === 'CONNECTING' ? 'PROBING...' : 'OFFLINE'}
          </span>
        </div>

        {/* BH1750 Sensor Status Badge */}
        <div className="flex items-center space-x-1.5 bg-chassis-850 px-2.5 py-1 rounded border border-border">
          <Layers className={`w-3.5 h-3.5 ${
            deviceStatus?.sensor_active ? 'text-metrology-green' : 
            deviceStatus?.arduino_online ? 'text-amber-400' : 'text-zinc-500'
          }`} />
          <span className="text-[10px] uppercase text-zinc-400">SENSOR:</span>
          <span className={`text-[11px] font-bold ${
            deviceStatus?.sensor_active ? 'text-metrology-green' : 
            deviceStatus?.arduino_online ? 'text-amber-400' : 'text-zinc-500'
          }`}>
            {deviceStatus?.sensor_active ? `BH1750 (${deviceStatus.sensor_addr || '0x23'})` :
             deviceStatus?.arduino_online ? 'DISCONNECTED' : 'OFFLINE'}
          </span>
        </div>

        {currentPacket && (
          <div className="flex items-center space-x-1.5 bg-chassis-850 px-2.5 py-1 rounded border border-border text-zinc-400">
            <ShieldCheck className="w-3.5 h-3.5 text-metrology-green" />
            <span className="text-metrology-green font-mono text-[11px]">XOR-128 OK</span>
          </div>
        )}
      </div>

      {/* Right Controls, Appearance Toggle & Clock */}
      <div className="flex items-center space-x-3">
        {/* Global Appearance Toggle: Light / Dark */}
        <div 
          className="flex items-center bg-chassis-900 border border-border rounded p-0.5" 
          role="group" 
          aria-label="Global Appearance Mode"
        >
          <button
            type="button"
            onClick={() => setTheme('light')}
            title="Light Mode (Standard High-Ambient Metrology)"
            className={`p-1 rounded transition-colors flex items-center justify-center ${
              theme === 'light'
                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Sun className="w-3.5 h-3.5" />
            <span className="sr-only">Light</span>
          </button>
          <button
            type="button"
            onClick={() => setTheme('dark')}
            title="Dark Mode (Low-Ambient Cleanroom Metrology)"
            className={`p-1 rounded transition-colors flex items-center justify-center ${
              theme === 'dark'
                ? 'bg-metrology-green/20 text-metrology-green border border-metrology-green/40 shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Moon className="w-3.5 h-3.5" />
            <span className="sr-only">Dark</span>
          </button>
        </div>

        <div className="text-xs font-mono text-zinc-400 hidden sm:block bg-chassis-900 px-2.5 py-1 rounded border border-border/50">
          {clock}
        </div>
      </div>
    </header>
  );
};

