import React, { useState, useEffect } from 'react';
import { bridge, UserSettings } from '../../bridge/bridgeClient';
import { 
  Settings, 
  DownloadCloud, 
  RefreshCw, 
  ShieldCheck, 
  Terminal, 
  HardDrive, 
  CheckCircle, 
  AlertTriangle, 
  Radio, 
  ArrowUpRight,
  ExternalLink,
  RotateCw,
  FolderOpen
} from 'lucide-react';

interface SettingsWorkspaceProps {
  onUpdateAvailableChange?: (available: boolean) => void;
}

export const SettingsWorkspace: React.FC<SettingsWorkspaceProps> = ({
  onUpdateAvailableChange
}) => {
  // Settings state
  const [settings, setSettings] = useState<UserSettings>({
    serial_port: 'COM5',
    baud_rate: 115200,
    update_channel: 'stable',
    auto_check_updates: true,
    last_update_check: null,
    latest_known_version: '2.1.0'
  });

  const [availablePorts, setAvailablePorts] = useState<string[]>([]);
  const [isScanningPorts, setIsScanningPorts] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Update Center state
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<any>(null);
  const [downloadProgress, setDownloadProgress] = useState<{
    downloaded: number;
    total: number;
    percent: number;
  } | null>(null);
  const [readyInstallerPath, setReadyInstallerPath] = useState<string | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);

  // Load settings & ports
  useEffect(() => {
    const loadInit = async () => {
      try {
        const s = await bridge.getSettings();
        if (s) setSettings(s);
        scanSerialPorts();
      } catch (e) {
        console.error('Failed to init settings:', e);
      }
    };
    loadInit();

    // Subscribe to update events
    const unsubUpdate = bridge.onUpdateResult((res) => {
      setIsCheckingUpdate(false);
      setUpdateInfo(res);
      if (res?.available && onUpdateAvailableChange) {
        onUpdateAvailableChange(true);
      }
    });

    const unsubProgress = bridge.onDownloadProgress((down, tot, pct) => {
      setDownloadProgress({ downloaded: down, total: tot, percent: pct });
    });

    const unsubReady = bridge.onReadyToInstall((path) => {
      setDownloadProgress(null);
      setReadyInstallerPath(path);
    });

    const unsubError = bridge.onVerificationError((err) => {
      setVerificationError(err);
      setDownloadProgress(null);
    });

    return () => {
      unsubUpdate();
      unsubProgress();
      unsubReady();
      unsubError();
    };
  }, []);

  const scanSerialPorts = async () => {
    setIsScanningPorts(true);
    try {
      const ports = await bridge.scanPorts();
      setAvailablePorts(ports);
    } catch (e) {
      console.error('Port scan failed:', e);
    } finally {
      setIsScanningPorts(false);
    }
  };

  const handleSaveSettings = async (newSettings: UserSettings) => {
    setSettings(newSettings);
    try {
      await bridge.saveSettings(newSettings);
      setSaveStatus('Preferences saved successfully.');
      setTimeout(() => setSaveStatus(null), 3000);
    } catch (e) {
      setSaveStatus('Failed to persist settings.');
    }
  };

  const handleCheckUpdates = () => {
    setIsCheckingUpdate(true);
    setVerificationError(null);
    setReadyInstallerPath(null);
    bridge.checkForUpdates(settings.update_channel);
  };

  const handleDownloadUpdate = () => {
    if (!updateInfo) return;
    setVerificationError(null);
    bridge.downloadUpdate(updateInfo);
  };

  const handleInstallUpdate = () => {
    bridge.installUpdate();
  };

  const baudRates = [9600, 19200, 38400, 57600, 115200];

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Header */}
      <div className="bg-chassis-950 p-4 rounded-xl border border-border flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center space-x-2">
            <Settings className="w-4 h-4 text-metrology-green" />
            <span>Instrument Settings & Update Center</span>
          </h2>
          <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
            Manage communication serial bus, GitHub release distribution channel, and data persistence.
          </p>
        </div>
        {saveStatus && (
          <div className="text-xs font-mono text-metrology-green bg-metrology-green/10 border border-metrology-green/30 px-3 py-1 rounded flex items-center space-x-1.5">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{saveStatus}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Section 1: GitHub In-App Update Center (Spans 7 cols) */}
        <div className="lg:col-span-7 bg-chassis-950 border border-border rounded-xl p-5 space-y-4 flex flex-col justify-between shadow-instrument">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center space-x-2">
                <DownloadCloud className="w-4 h-4 text-metrology-green" />
                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                  GitHub Software Update Center
                </span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-chassis-850 border border-border text-zinc-400">
                DevPro-CORPORATION / LuxSense-Pro
              </span>
            </div>

            {/* Version Comparison Card */}
            <div className="grid grid-cols-2 gap-3 bg-chassis-900 p-3 rounded-lg border border-border">
              <div>
                <div className="text-[10px] font-mono text-zinc-400 uppercase">Installed Version</div>
                <div className="text-xl font-bold font-mono text-white mt-1">
                  v2.2.0
                </div>
                <div className="text-[10px] font-mono text-metrology-green mt-0.5">
                  Current Active Build
                </div>
              </div>

              <div>
                <div className="text-[10px] font-mono text-zinc-400 uppercase">Latest Available</div>
                <div className="text-xl font-bold font-mono text-metrology-green mt-1">
                  {updateInfo?.version ? `v${updateInfo.version}` : 'v2.2.0'}
                </div>
                <div className="text-[10px] font-mono text-zinc-400 mt-0.5">
                  {updateInfo?.available ? 'Update Ready' : 'Up to Date'}
                </div>
              </div>
            </div>

            {/* Channel Selection */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-zinc-300 block">
                Release Distribution Channel:
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => handleSaveSettings({ ...settings, update_channel: 'stable' })}
                  className={`p-3 rounded-lg border text-left transition-all font-mono text-xs ${
                    settings.update_channel === 'stable'
                      ? 'bg-chassis-800 border-metrology-green text-white shadow-glow-green'
                      : 'bg-chassis-900 border-border text-zinc-400 hover:border-border-focus'
                  }`}
                >
                  <div className="flex items-center justify-between font-bold">
                    <span>Stable Channel</span>
                    {settings.update_channel === 'stable' && <CheckCircle className="w-3.5 h-3.5 text-metrology-green" />}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-1">
                    Validated commercial production releases with Authenticode verification.
                  </div>
                </button>

                <button
                  onClick={() => handleSaveSettings({ ...settings, update_channel: 'beta' })}
                  className={`p-3 rounded-lg border text-left transition-all font-mono text-xs ${
                    settings.update_channel === 'beta'
                      ? 'bg-chassis-800 border-metrology-amber text-white shadow-glow-amber'
                      : 'bg-chassis-900 border-border text-zinc-400 hover:border-border-focus'
                  }`}
                >
                  <div className="flex items-center justify-between font-bold">
                    <span className="text-metrology-amber">Beta Channel</span>
                    {settings.update_channel === 'beta' && <CheckCircle className="w-3.5 h-3.5 text-metrology-amber" />}
                  </div>
                  <div className="text-[10px] text-zinc-400 mt-1">
                    Early access release candidates, new DSP filters and experimental drivers.
                  </div>
                </button>
              </div>
            </div>

            {/* Release Notes Preview */}
            {updateInfo?.body && (
              <div className="space-y-1.5">
                <div className="text-xs font-mono text-zinc-300">
                  Release Notes — {updateInfo.release_name || updateInfo.tag_name}:
                </div>
                <div className="bg-chassis-900 border border-border rounded p-3 text-xs font-mono text-zinc-300 max-h-32 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                  {updateInfo.body}
                </div>
              </div>
            )}

            {/* Download Progress Bar */}
            {downloadProgress && (
              <div className="space-y-1.5 bg-chassis-900 p-3 rounded border border-border">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-zinc-300">Downloading Update Package...</span>
                  <span className="text-metrology-green font-bold">{downloadProgress.percent.toFixed(1)}%</span>
                </div>
                <div className="h-2 w-full bg-chassis-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-metrology-green transition-all duration-200"
                    style={{ width: `${downloadProgress.percent}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-zinc-400">
                  <span>{(downloadProgress.downloaded / 1048576).toFixed(1)} MB / {(downloadProgress.total / 1048576).toFixed(1)} MB</span>
                  <span>Verifying SHA-256 Checksum on completion</span>
                </div>
              </div>
            )}

            {/* Error alerts */}
            {verificationError && (
              <div className="bg-metrology-crimson/15 border border-metrology-crimson p-3 rounded-lg text-xs font-mono text-metrology-crimson flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                <span>Verification Error: {verificationError} (Download aborted)</span>
              </div>
            )}

            {/* Ready to install notification */}
            {readyInstallerPath && (
              <div className="bg-metrology-green/15 border border-metrology-green p-3 rounded-lg text-xs font-mono text-metrology-green flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 flex-shrink-0" />
                  <span>SHA-256 verified! Package ready for silent upgrade.</span>
                </div>
                <button
                  onClick={handleInstallUpdate}
                  className="px-3 py-1 rounded bg-metrology-green text-chassis-950 font-bold hover:bg-metrology-green/90 transition-colors shadow-glow-green"
                >
                  INSTALL &amp; RESTART
                </button>
              </div>
            )}
          </div>

          {/* Action Footer for Updates */}
          <div className="pt-4 border-t border-border flex items-center justify-between">
            <div className="text-[10px] font-mono text-zinc-400">
              Last check: {settings.last_update_check || '2026-11-13 22:00:00'}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleCheckUpdates}
                disabled={isCheckingUpdate}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-chassis-850 border border-border text-xs font-mono text-zinc-200 hover:border-border-focus transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isCheckingUpdate ? 'animate-spin' : ''}`} />
                <span>{isCheckingUpdate ? 'CHECKING...' : 'CHECK FOR UPDATES'}</span>
              </button>

              {updateInfo?.available && !readyInstallerPath && !downloadProgress && (
                <button
                  onClick={handleDownloadUpdate}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-metrology-green text-chassis-950 text-xs font-mono font-bold hover:bg-metrology-green/90 transition-colors shadow-glow-green"
                >
                  <DownloadCloud className="w-3.5 h-3.5" />
                  <span>DOWNLOAD UPDATE</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Section 2: Hardware Interface & Data Persistence (Spans 5 cols) */}
        <div className="lg:col-span-5 space-y-4 flex flex-col">
          {/* Serial Port Hardware Interface */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
                <Radio className="w-3.5 h-3.5 text-metrology-green" />
                <span>Hardware COM Port Interface</span>
              </span>
              <button
                onClick={scanSerialPorts}
                disabled={isScanningPorts}
                className="text-[10px] font-mono text-zinc-400 hover:text-metrology-green flex items-center space-x-1"
              >
                <RotateCw className={`w-3 h-3 ${isScanningPorts ? 'animate-spin' : ''}`} />
                <span>SCAN</span>
              </button>
            </div>

            <div className="space-y-2 font-mono text-xs">
              <div>
                <label className="text-zinc-400 text-[11px] block mb-1">Serial COM Port:</label>
                <select
                  value={settings.serial_port}
                  onChange={(e) => handleSaveSettings({ ...settings, serial_port: e.target.value })}
                  className="w-full bg-chassis-900 border border-border rounded p-2 text-zinc-200 focus:border-border-focus focus:outline-none"
                >
                  {availablePorts.length > 0 ? (
                    availablePorts.map((p, i) => (
                      <option key={i} value={p.split(' ')[0]}>{p}</option>
                    ))
                  ) : (
                    <option value="COM5">COM5 — Arduino Uno (ATmega328P)</option>
                  )}
                </select>
              </div>

              <div>
                <label className="text-zinc-400 text-[11px] block mb-1">Baud Rate (UART):</label>
                <select
                  value={settings.baud_rate}
                  onChange={(e) => handleSaveSettings({ ...settings, baud_rate: parseInt(e.target.value) })}
                  className="w-full bg-chassis-900 border border-border rounded p-2 text-zinc-200 focus:border-border-focus focus:outline-none"
                >
                  {baudRates.map((b) => (
                    <option key={b} value={b}>{b} baud</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Cryptographic & Storage Security */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-3 flex-1">
            <div className="text-xs font-mono font-bold text-white uppercase tracking-wider border-b border-border pb-2 flex items-center space-x-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-metrology-green" />
              <span>Decoupled Storage &amp; Safety</span>
            </div>

            <div className="space-y-2 text-[11px] font-mono text-zinc-400 leading-relaxed">
              <div className="p-2.5 bg-chassis-900 rounded border border-border">
                <div className="text-zinc-200 font-semibold mb-1 flex items-center space-x-1">
                  <HardDrive className="w-3 h-3 text-metrology-blue" />
                  <span>AppData Persistence Isolation:</span>
                </div>
                <code className="text-[10px] text-zinc-400 block bg-chassis-950 p-1 rounded border border-border/50">
                  %APPDATA%\DevPro\LuxSensePro\
                </code>
                <p className="mt-1 text-[10px] text-zinc-400">
                  Settings, calibration profiles, and historical SQLite measurements are preserved across updates and rollbacks.
                </p>
              </div>

              <div className="p-2.5 bg-chassis-900 rounded border border-border">
                <div className="text-zinc-200 font-semibold mb-1 flex items-center space-x-1">
                  <ShieldCheck className="w-3 h-3 text-metrology-green" />
                  <span>Dual Verification Gate:</span>
                </div>
                <p className="text-[10px] text-zinc-400">
                  1. SHA-256 Digest checked against release manifest.<br/>
                  2. Windows Authenticode digital signature verified.<br/>
                  3. Standalone updater.exe provides automatic rollback.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

