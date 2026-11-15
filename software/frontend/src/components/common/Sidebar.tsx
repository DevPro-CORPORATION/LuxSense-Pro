import React from 'react';
import { WorkspaceTab } from '../../types';
import { 
  Gauge, 
  Microscope,
  BarChart3, 
  Sliders, 
  Settings, 
  Binary, 
  Users,
  Radio,
  Sparkles
} from 'lucide-react';

interface SidebarProps {
  currentTab: WorkspaceTab;
  onSelectTab: (tab: WorkspaceTab) => void;
  updateAvailable: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  updateAvailable
}) => {
  const navItems = [
    { id: 'monitor' as WorkspaceTab, label: 'Live Monitor', icon: Gauge, hint: 'Photopic acquisition' },
    { id: 'scientific' as WorkspaceTab, label: 'Scientific Lab', icon: Microscope, hint: 'Uncertainty & Spatial' },
    { id: 'analytics' as WorkspaceTab, label: 'Analytics Lab', icon: BarChart3, hint: 'Spectral distributions' },
    { id: 'calibration' as WorkspaceTab, label: 'Calibration', icon: Sliders, hint: 'Gain & dark offset' },
    { id: 'settings' as WorkspaceTab, label: 'Settings & Update', icon: Settings, hint: 'GitHub CI/CD Channel', badge: updateAvailable },
    { id: 'techinfo' as WorkspaceTab, label: 'Tech Architecture', icon: Binary, hint: 'BH1750 & ATmega328P' },
    { id: 'team' as WorkspaceTab, label: 'DevPro Team', icon: Users, hint: 'Organization identity' },
  ];

  return (
    <aside className="w-56 bg-chassis-950 border-r border-border flex flex-col justify-between py-3 select-none">
      <div className="space-y-1 px-2">
        <div className="px-3 pb-2 pt-1 text-[11px] font-mono text-zinc-400 uppercase tracking-widest">
          Workspaces
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-md text-left transition-all duration-150 group relative ${
                isActive 
                  ? 'bg-chassis-800 text-white font-medium border border-border-focus shadow-sm' 
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-chassis-900'
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-metrology-green rounded-r" />
              )}
              <Icon className={`w-4 h-4 transition-colors ${isActive ? 'text-metrology-green' : 'text-zinc-500 group-hover:text-zinc-300'}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs truncate">{item.label}</span>
                  {item.badge && (
                    <span className="w-2 h-2 rounded-full bg-metrology-amber animate-ping" />
                  )}
                </div>
                <div className="text-[10px] text-zinc-400 truncate font-mono">
                  {item.hint}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Hardware Interface Status Card */}
      <div className="px-3">
        <div className="p-3 bg-chassis-900 border border-border rounded-lg space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-zinc-400">INTERFACE</span>
            <span className="text-metrology-green font-semibold flex items-center space-x-1">
              <Radio className="w-3 h-3 animate-pulse" />
              <span>I2C BUS</span>
            </span>
          </div>
          <div className="text-[10px] text-zinc-400 font-mono space-y-0.5">
            <div className="flex justify-between">
              <span>Bus Address:</span>
              <span className="text-zinc-300">0x23 (ADDR GND)</span>
            </div>
            <div className="flex justify-between">
              <span>Clock Speed:</span>
              <span className="text-zinc-300">400 kHz Fast</span>
            </div>
            <div className="flex justify-between">
              <span>Resolution:</span>
              <span className="text-zinc-300">0.11 - 65,535 lx</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

