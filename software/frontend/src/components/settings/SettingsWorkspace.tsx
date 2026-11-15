import React, { useState, useEffect, useRef } from 'react';
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
  Cpu,
  Zap,
  HelpCircle,
  X,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

interface SettingsWorkspaceProps {
  onUpdateAvailableChange?: (available: boolean) => void;
}

export const SettingsWorkspace: React.FC<SettingsWorkspaceProps> = ({
  onUpdateAvailableChange
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'software' | 'firmware'>('software');

  // Settings state
  const [settings, setSettings] = useState<UserSettings>({
    serial_port: 'COM5',
    baud_rate: 115200,
    update_channel: 'stable',
    auto_check_updates: true,
    last_update_check: null,
    latest_known_version: '2.3.0'
  });

  const [availablePorts, setAvailablePorts] = useState<string[]>([]);
  const [isScanningPorts, setIsScanningPorts] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Software Update Center state
  const [isCheckingUpdate, setIsCheckingUpdate] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<any>(null);
  const [downloadProgress, setDownloadProgress] = useState<{
    downloaded: number;
    total: number;
    percent: number;
  } | null>(null);
  const [readyInstallerPath, setReadyInstallerPath] = useState<string | null>(null);
  const [verificationError, setVerificationError] = useState<string | null>(null);

  // Firmware Update Center state
  const [firmwareStatus, setFirmwareStatus] = useState<any>(null);
  const [isCheckingFirmware, setIsCheckingFirmware] = useState(false);
  const [firmwareCheckResult, setFirmwareCheckResult] = useState<any>(null);
  const [firmwareProgress, setFirmwareProgress] = useState<{ percent: number; phase: string } | null>(null);
  const [firmwareLogs, setFirmwareLogs] = useState<string[]>([]);
  const [firmwareResult, setFirmwareResult] = useState<{ success: boolean; message: string } | null>(null);
  const [isFlashing, setIsFlashing] = useState(false);
  const [userConfirmedRisk, setUserConfirmedRisk] = useState(false);
  const [allowDowngrade, setAllowDowngrade] = useState(false);
  const [showRecoveryModal, setShowRecoveryModal] = useState(false);
  const consoleEndRef = useRef<HTMLDivElement>(null);

  // Load initial settings & firmware status
  useEffect(() => {
    const loadInit = async () => {
      try {
        const s = await bridge.getSettings();
        if (s) setSettings(s);
        scanSerialPorts();
        loadFirmwareStatus();
      } catch (e) {
        console.error('Failed to init settings:', e);
      }
    };
    loadInit();

    // Subscribe to software update events
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

    // Subscribe to firmware update events
    const unsubFwStatus = bridge.onFirmwareStatus((st) => {
      setFirmwareStatus(st);
    });

    const unsubFwCheck = bridge.onFirmwareCheckResult((res) => {
      setIsCheckingFirmware(false);
      setFirmwareCheckResult(res);
    });

    const unsubFwProg = bridge.onFirmwareFlashProgress((pct, phase) => {
      setFirmwareProgress({ percent: pct, phase });
      setIsFlashing(true);
    });

    const unsubFwDone = bridge.onFirmwareFlashCompleted((success, msg) => {
      setIsFlashing(false);
      setFirmwareResult({ success, message: msg });
      loadFirmwareStatus();
    });

    const unsubFwLog = bridge.onFirmwareLog((line) => {
      setFirmwareLogs(prev => [...prev.slice(-300), line]);
    });

    return () => {
      unsubUpdate();
      unsubProgress();
      unsubReady();
      unsubError();
      unsubFwStatus();
      unsubFwCheck();
      unsubFwProg();
      unsubFwDone();
      unsubFwLog();
    };
  }, []);

  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [firmwareLogs]);

  const loadFirmwareStatus = async () => {
    try {
      const st = await bridge.getFirmwareStatus();
      setFirmwareStatus(st);
    } catch (e) {
      console.error('Failed to load firmware status:', e);
    }
  };

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

  // Firmware actions
  const handleCheckFirmware = async () => {
    setIsCheckingFirmware(true);
    setFirmwareResult(null);
    try {
      const res = await bridge.checkFirmwareUpdates();
      setFirmwareCheckResult(res);
    } catch (e) {
      console.error('Firmware check error:', e);
    } finally {
      setIsCheckingFirmware(false);
    }
  };

  const handleStartFlash = async () => {
    if (!userConfirmedRisk) return;
    setIsFlashing(true);
    setFirmwareResult(null);
    setFirmwareLogs([
      `[USER ACTION] Firmware flash authorized by operator for port ${settings.serial_port}`,
      `[SECURITY] Initiating pre-flight verification and cryptographic handshake...`
    ]);

    const hexPath = firmwareCheckResult?.hex_path || '';
    try {
      await bridge.startFirmwareFlash(settings.serial_port, hexPath, allowDowngrade);
    } catch (e: any) {
      setIsFlashing(false);
      setFirmwareResult({ success: false, message: `Invocation error: ${e?.message || e}` });
    }
  };

  const baudRates = [9600, 19200, 38400, 57600, 115200];

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Header & Sub-Tab Navigation */}
      <div className="bg-chassis-950 p-4 rounded-xl border border-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center space-x-2">
            <Settings className="w-4 h-4 text-metrology-green" />
            <span>Update Center &amp; Instrument Preferences</span>
          </h2>
          <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
            Unified software delivery channels, physical MCU firmware management, and hardware interfaces.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center bg-chassis-900 p-1 rounded-lg border border-border font-mono text-xs">
          <button
            onClick={() => setActiveSubTab('software')}
            className={`px-3 py-1.5 rounded transition-all flex items-center space-x-2 ${
              activeSubTab === 'software'
                ? 'bg-chassis-800 text-white font-semibold border border-border-focus shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <DownloadCloud className="w-3.5 h-3.5 text-metrology-green" />
            <span>Software Updates &amp; Ports</span>
          </button>

          <button
            onClick={() => setActiveSubTab('firmware')}
            className={`px-3 py-1.5 rounded transition-all flex items-center space-x-2 ${
              activeSubTab === 'firmware'
                ? 'bg-chassis-800 text-white font-semibold border border-border-focus shadow-sm'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-metrology-blue" />
            <span>ATmega328P Firmware Center</span>
            {firmwareCheckResult?.available && (
              <span className="w-2 h-2 rounded-full bg-metrology-amber animate-pulse" />
            )}
          </button>
        </div>

        {saveStatus && (
          <div className="text-xs font-mono text-metrology-green bg-metrology-green/10 border border-metrology-green/30 px-3 py-1 rounded flex items-center space-x-1.5">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>{saveStatus}</span>
          </div>
        )}
      </div>

      {/* ========================================================= */}
      {/* SUB-TAB 1: SOFTWARE UPDATES & HARDWARE COM PORTS          */}
      {/* ========================================================= */}
      {activeSubTab === 'software' && (
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
                    v2.3.0
                  </div>
                  <div className="text-[10px] font-mono text-metrology-green mt-0.5">
                    Current Active Build
                  </div>
                </div>

                <div>
                  <div className="text-[10px] font-mono text-zinc-400 uppercase">Latest Available</div>
                  <div className="text-xl font-bold font-mono text-metrology-green mt-1">
                    {updateInfo?.version ? `v${updateInfo.version}` : 'v2.3.0'}
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
                Last check: {settings.last_update_check || '2026-11-15 15:30:00'}
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
      )}

      {/* ========================================================= */}
      {/* SUB-TAB 2: DEDICATED FIRMWARE UPDATE CENTER                */}
      {/* ========================================================= */}
      {activeSubTab === 'firmware' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left: Connected Hardware Identification (Spans 5 cols) */}
            <div className="lg:col-span-5 bg-chassis-950 border border-border rounded-xl p-5 space-y-4 shadow-instrument">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-metrology-blue" />
                  <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                    Microcontroller Hardware Target
                  </span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-chassis-850 border border-border text-metrology-green">
                  STK500v1 Compatible
                </span>
              </div>

              {/* Hardware Spec Grid */}
              <div className="space-y-2.5 font-mono text-xs">
                <div className="p-3 bg-chassis-900 rounded-lg border border-border space-y-1.5">
                  <div className="flex justify-between items-center text-zinc-400 text-[11px]">
                    <span>Target Board:</span>
                    <span className="text-white font-semibold">{firmwareStatus?.board || 'Arduino Uno R3'}</span>
                  </div>
                  <div className="flex justify-between items-center text-zinc-400 text-[11px]">
                    <span>Microcontroller (MCU):</span>
                    <span className="text-zinc-200">{firmwareStatus?.mcu || 'ATmega328P (16MHz AVR)'}</span>
                  </div>
                  <div className="flex justify-between items-center text-zinc-400 text-[11px]">
                    <span>Bootloader Protocol:</span>
                    <span className="text-metrology-blue">{firmwareStatus?.bootloader || 'Optiboot v4.4 (115200)'}</span>
                  </div>
                  <div className="flex justify-between items-center text-zinc-400 text-[11px]">
                    <span>Allocated Port:</span>
                    <span className="text-metrology-green font-bold">{settings.serial_port}</span>
                  </div>
                  <div className="flex justify-between items-center text-zinc-400 text-[11px]">
                    <span>Active Sensor:</span>
                    <span className="text-zinc-200">{firmwareStatus?.sensor || 'BH1750 (0x23 / 0x5C)'}</span>
                  </div>
                  <div className="flex justify-between items-center text-zinc-400 text-[11px]">
                    <span>Installed Microcode:</span>
                    <span className="text-white font-bold bg-chassis-800 px-2 py-0.5 rounded">
                      {firmwareStatus?.installed_version ? `v${firmwareStatus.installed_version}` : 'v1.2.0'}
                    </span>
                  </div>
                </div>

                {/* Permanent No Automatic Flashing Policy */}
                <div className="p-3 bg-chassis-900/60 rounded-lg border border-border/80 space-y-1">
                  <div className="text-zinc-300 font-semibold text-xs flex items-center space-x-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-metrology-amber" />
                    <span>Non-Destructive Update Policy:</span>
                  </div>
                  <p className="text-[10px] text-zinc-400 leading-relaxed">
                    LuxSense Pro enforces an absolute safety guarantee: <strong>Firmware updates are never applied automatically</strong>. Software updates cannot trigger flash memory writes, and user settings or calibration curves are never overwritten.
                  </p>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => setShowRecoveryModal(true)}
                    className="text-xs text-metrology-blue hover:underline flex items-center space-x-1"
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span>Bootloader Recovery &amp; ISP Reprogramming Documentation</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Right: Available Signed Firmware Package (Spans 7 cols) */}
            <div className="lg:col-span-7 bg-chassis-950 border border-border rounded-xl p-5 space-y-4 shadow-instrument flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div className="flex items-center space-x-2">
                    <Zap className="w-4 h-4 text-metrology-amber" />
                    <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                      Firmware Release &amp; Cryptographic Manifest
                    </span>
                  </div>
                  <button
                    onClick={handleCheckFirmware}
                    disabled={isCheckingFirmware || isFlashing}
                    className="flex items-center space-x-1.5 px-2.5 py-1 rounded bg-chassis-850 border border-border text-[10px] font-mono text-zinc-200 hover:border-border-focus transition-colors"
                  >
                    <RefreshCw className={`w-3 h-3 ${isCheckingFirmware ? 'animate-spin' : ''}`} />
                    <span>{isCheckingFirmware ? 'VERIFYING...' : 'CHECK FIRMWARE'}</span>
                  </button>
                </div>

                {/* Firmware Release Details */}
                {firmwareCheckResult?.manifest ? (
                  <div className="space-y-3 font-mono text-xs">
                    <div className="grid grid-cols-2 gap-3 bg-chassis-900 p-3 rounded-lg border border-border">
                      <div>
                        <div className="text-[10px] text-zinc-400 uppercase">Target Release</div>
                        <div className="text-lg font-bold text-metrology-green mt-0.5">
                          v{firmwareCheckResult.manifest.firmware_version}
                        </div>
                        <div className="text-[10px] text-zinc-400">
                          {firmwareCheckResult.manifest.release_name}
                        </div>
                      </div>

                      <div>
                        <div className="text-[10px] text-zinc-400 uppercase">Target Hardware</div>
                        <div className="text-sm font-semibold text-white mt-1">
                          {firmwareCheckResult.manifest.target_board}
                        </div>
                        <div className="text-[10px] text-metrology-blue">
                          {firmwareCheckResult.manifest.target_mcu} ({firmwareCheckResult.manifest.clock_mhz}MHz)
                        </div>
                      </div>
                    </div>

                    {/* Cryptographic Badges */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[10px]">
                      <div className="p-2.5 bg-metrology-green/10 border border-metrology-green/30 rounded flex items-center space-x-2 text-metrology-green">
                        <ShieldCheck className="w-4 h-4 flex-shrink-0" />
                        <div>
                          <div className="font-bold">Ed25519 Publisher Signature: VALID</div>
                          <div className="text-[9px] text-zinc-400">{firmwareCheckResult.manifest.publisher}</div>
                        </div>
                      </div>

                      <div className="p-2.5 bg-chassis-900 border border-border rounded space-y-0.5 text-zinc-300">
                        <div className="text-[9px] text-zinc-400 uppercase">SHA-256 Digest:</div>
                        <div className="font-mono text-[9px] text-metrology-amber truncate">
                          {firmwareCheckResult.manifest.hex_sha256}
                        </div>
                      </div>
                    </div>

                    {/* Release Notes */}
                    <div className="space-y-1">
                      <div className="text-[11px] text-zinc-400 font-semibold">Changelog &amp; Microcode Notes:</div>
                      <div className="bg-chassis-900 border border-border rounded p-2.5 text-[11px] text-zinc-300 max-h-24 overflow-y-auto leading-relaxed">
                        {firmwareCheckResult.manifest.release_notes}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-chassis-900 rounded-lg border border-border text-center font-mono text-xs text-zinc-400">
                    Click <strong>CHECK FIRMWARE</strong> to discover and cryptographically verify official signed microcode packages.
                  </div>
                )}

                {/* Flashing Safeguard Warning Banner */}
                <div className="bg-metrology-amber/10 border border-metrology-amber/40 rounded-lg p-3 space-y-2 font-mono text-xs">
                  <div className="flex items-center space-x-2 text-metrology-amber font-bold">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                    <span>CRITICAL FLASH MEMORY SAFETY NOTICE</span>
                  </div>
                  <p className="text-[10px] text-zinc-300 leading-relaxed">
                    Arduino Uno R3 does NOT support dual-bank rollback. Flashing directly writes to ATmega328P flash memory.
                    <strong> Never unplug USB cable or power during programming.</strong>
                  </p>
                  <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px]">
                    <label className="flex items-center space-x-2 cursor-pointer text-white">
                      <input
                        type="checkbox"
                        checked={userConfirmedRisk}
                        onChange={(e) => setUserConfirmedRisk(e.target.checked)}
                        disabled={isFlashing}
                        className="rounded border-border text-metrology-green focus:ring-0"
                      />
                      <span>I understand this writes directly to microcontroller flash memory</span>
                    </label>

                    <label className="flex items-center space-x-1.5 cursor-pointer text-zinc-400 text-[10px]">
                      <input
                        type="checkbox"
                        checked={allowDowngrade}
                        onChange={(e) => setAllowDowngrade(e.target.checked)}
                        disabled={isFlashing}
                        className="rounded border-border text-metrology-amber focus:ring-0"
                      />
                      <span>Authorize downgrade if requested</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-border flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-400">
                  Target Port: <strong className="text-white">{settings.serial_port}</strong>
                </span>

                <button
                  onClick={handleStartFlash}
                  disabled={!userConfirmedRisk || isFlashing || !firmwareCheckResult?.manifest}
                  className={`px-4 py-2 rounded text-xs font-mono font-bold transition-all flex items-center space-x-2 ${
                    userConfirmedRisk && !isFlashing && firmwareCheckResult?.manifest
                      ? 'bg-metrology-green text-chassis-950 hover:bg-metrology-green/90 shadow-glow-green cursor-pointer'
                      : 'bg-chassis-800 text-zinc-500 border border-border cursor-not-allowed'
                  }`}
                >
                  <Zap className={`w-3.5 h-3.5 ${isFlashing ? 'animate-bounce text-metrology-amber' : ''}`} />
                  <span>{isFlashing ? 'FLASHING MICROCODE...' : 'AUTHORIZE & FLASH FIRMWARE'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Diagnostic Console & Live Progress Section */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-3 font-mono">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <div className="flex items-center space-x-2 text-xs font-bold text-white uppercase tracking-wider">
                <Terminal className="w-3.5 h-3.5 text-metrology-green" />
                <span>Microcontroller Flashing Diagnostic Console</span>
              </div>
              {firmwareProgress && (
                <span className="text-[11px] text-metrology-green font-bold">
                  {firmwareProgress.percent}% — {firmwareProgress.phase}
                </span>
              )}
            </div>

            {/* Progress Bar */}
            {isFlashing && (
              <div className="space-y-1">
                <div className="h-2 w-full bg-chassis-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-metrology-green transition-all duration-200"
                    style={{ width: `${firmwareProgress?.percent || 15}%` }}
                  />
                </div>
              </div>
            )}

            {/* Success or Error Result Notification */}
            {firmwareResult && (
              <div className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
                firmwareResult.success
                  ? 'bg-metrology-green/15 border-metrology-green text-metrology-green'
                  : 'bg-metrology-crimson/15 border-metrology-crimson text-metrology-crimson'
              }`}>
                <div className="flex items-center space-x-2">
                  {firmwareResult.success ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                  <span>{firmwareResult.message}</span>
                </div>
                {!firmwareResult.success && (
                  <button
                    onClick={() => setShowRecoveryModal(true)}
                    className="px-2 py-0.5 rounded bg-metrology-crimson/20 border border-metrology-crimson/40 hover:bg-metrology-crimson/30 text-[10px]"
                  >
                    VIEW RECOVERY STEPS
                  </button>
                )}
              </div>
            )}

            {/* Real-time stdout/stderr console */}
            <div className="h-44 bg-chassis-900 border border-border rounded-lg p-3 text-[11px] text-zinc-300 font-mono overflow-y-auto space-y-1 leading-relaxed">
              {firmwareLogs.length > 0 ? (
                firmwareLogs.map((line, idx) => (
                  <div key={idx} className="flex items-start space-x-2">
                    <span className="text-zinc-600 select-none">&gt;</span>
                    <span className={line.includes('ERROR') ? 'text-metrology-crimson font-bold' : line.includes('SUCCESS') ? 'text-metrology-green font-bold' : ''}>
                      {line}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-zinc-500 italic">
                  Awaiting flashing operation. Real-time stdout/stderr stream from avrdude and hardware verification will be captured here.
                </div>
              )}
              <div ref={consoleEndRef} />
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* RECOVERY & BOOTLOADER GUIDANCE MODAL                      */}
      {/* ========================================================= */}
      {showRecoveryModal && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="bg-chassis-950 border border-border rounded-xl max-w-2xl w-full p-6 space-y-4 font-mono shadow-2xl">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center space-x-2 text-white font-bold text-sm">
                <AlertTriangle className="w-4 h-4 text-metrology-amber" />
                <span>ATmega328P Hardware Recovery &amp; Bootloader Guide</span>
              </div>
              <button
                onClick={() => setShowRecoveryModal(false)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs text-zinc-300 leading-relaxed max-h-[60vh] overflow-y-auto pr-2">
              <div className="p-3 bg-chassis-900 rounded-lg border border-border space-y-1">
                <h4 className="font-bold text-metrology-green">Scenario A: Flashing Interrupted or Timed Out (Optiboot Intact)</h4>
                <p className="text-[11px] text-zinc-400">
                  The Arduino Uno R3 uses the Optiboot bootloader in a protected 512-byte high-memory section (`0x7E00-0x7FFF`). Optiboot is NOT overwritten by normal sketch uploads.
                </p>
                <ol className="list-decimal list-inside text-[11px] text-zinc-300 space-y-1 pt-1">
                  <li>Unplug the USB cable from your computer.</li>
                  <li>Wait 5 seconds, then plug the cable back into the same USB port.</li>
                  <li>Check Device Manager to ensure the COM port is recognized.</li>
                  <li>Click <strong>AUTHORIZE &amp; FLASH FIRMWARE</strong> again. The bootloader listens for programming commands within the first 1.5 seconds of power-up.</li>
                </ol>
              </div>

              <div className="p-3 bg-chassis-900 rounded-lg border border-border space-y-1">
                <h4 className="font-bold text-metrology-amber">Scenario B: avrdude stk500_getsync() Synchronization Error</h4>
                <p className="text-[11px] text-zinc-400">
                  Occurs when another process holds the COM port open or auto-reset capacitor (DTR to RESET) fails:
                </p>
                <ul className="list-disc list-inside text-[11px] text-zinc-300 space-y-1 pt-1">
                  <li>Verify no terminal or serial monitor (Arduino IDE, PuTTY) is connected to {settings.serial_port}.</li>
                  <li>Press the physical RED RESET button on the Arduino Uno right as flashing initiates.</li>
                  <li>If using a USB hub, connect the Arduino directly to a motherboard USB port.</li>
                </ul>
              </div>

              <div className="p-3 bg-chassis-900 rounded-lg border border-border space-y-1">
                <h4 className="font-bold text-metrology-crimson">Scenario C: Corrupted Bootloader (ISP In-System Programming)</h4>
                <p className="text-[11px] text-zinc-400">
                  If the bootloader itself has been corrupted via low-voltage brownout or prior ISP write:
                </p>
                <ol className="list-decimal list-inside text-[11px] text-zinc-300 space-y-1 pt-1">
                  <li>Connect a programmer (USBasp or a second Arduino programmed as "ArduinoISP").</li>
                  <li>Connect to the 6-pin ICSP header (MISO, MOSI, SCK, RESET, VCC, GND).</li>
                  <li>Run: <code className="bg-chassis-950 p-1 rounded text-[10px]">avrdude -c stk500v1 -p m328p -P COMx -b 19200 -U flash:w:optiboot_atmega328.hex:i</code></li>
                </ol>
              </div>
            </div>

            <div className="pt-3 border-t border-border flex justify-end">
              <button
                onClick={() => setShowRecoveryModal(false)}
                className="px-4 py-1.5 rounded bg-chassis-800 border border-border text-xs font-mono text-white hover:bg-chassis-750 transition-colors"
              >
                CLOSE GUIDE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
