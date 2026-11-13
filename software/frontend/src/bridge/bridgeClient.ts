/**
 * LuxSense Pro — Qt WebChannel Communication Bridge
 * Connects the React TypeScript application to the PySide6 hardware engine.
 * Includes a realistic simulation mode for standalone browser previews and testing.
 */

export interface TelemetryPacket {
  raw_lux: number;
  cal_lux: number;
  packet_id: number;
  port: string;
  timestamp: string;
  checksum_ok: boolean;
}

export interface CalibrationProfile {
  profile_name: string;
  zero_offset: number;
  gain_multiplier: number;
  calibrated_at: string;
  notes: string;
}

export interface UserSettings {
  serial_port: string;
  baud_rate: number;
  update_channel: 'stable' | 'beta';
  auto_check_updates: boolean;
  last_update_check: string | null;
  latest_known_version: string;
}

export interface TelemetryRecord {
  id?: number;
  timestamp: string;
  packet_id: number;
  raw_lux: number;
  calibrated_lux: number;
  port: string;
}

declare global {
  interface Window {
    qt?: {
      webChannelTransport: any;
    };
    QWebChannel?: any;
    backend?: any;
  }
}

type TelemetryListener = (packet: TelemetryPacket) => void;
type StatusListener = (message: string, color: string) => void;
type UpdateResultListener = (result: any) => void;
type DownloadProgressListener = (downloaded: number, total: number, percent: number) => void;
type ReadyToInstallListener = (path: string) => void;
type VerificationErrorListener = (err: string) => void;

class BridgeClient {
  private isQtConnected = false;
  private backendObj: any = null;

  private telemetryListeners: TelemetryListener[] = [];
  private statusListeners: StatusListener[] = [];
  private updateResultListeners: UpdateResultListener[] = [];
  private downloadProgressListeners: DownloadProgressListener[] = [];
  private readyToInstallListeners: ReadyToInstallListener[] = [];
  private verificationErrorListeners: VerificationErrorListener[] = [];

  // Standalone simulation state
  private simulationInterval: any = null;
  private simPacketCounter = 1;
  private simBaseLux = 542.8;

  constructor() {
    this.initBridge();
  }

  private initBridge() {
    if (typeof window !== 'undefined' && window.qt && window.qt.webChannelTransport && window.QWebChannel) {
      new window.QWebChannel(window.qt.webChannelTransport, (channel: any) => {
        this.backendObj = channel.objects.backend;
        this.isQtConnected = true;
        console.info('[Bridge] Connected to PySide6 QtWebChannel backend.');
        this.attachQtSignals();
      });
    } else {
      console.info('[Bridge] Running in standalone web mode. Initializing realistic sensor emulation.');
      this.initStandaloneEmulation();
    }
  }

  private attachQtSignals() {
    if (!this.backendObj) return;

    if (this.backendObj.telemetryReceived) {
      this.backendObj.telemetryReceived.connect((jsonStr: string) => {
        try {
          const packet: TelemetryPacket = JSON.parse(jsonStr);
          this.telemetryListeners.forEach(fn => fn(packet));
        } catch (e) {
          console.error('[Bridge] Error parsing telemetry payload:', e);
        }
      });
    }

    if (this.backendObj.statusChanged) {
      this.backendObj.statusChanged.connect((msg: string, col: string) => {
        this.statusListeners.forEach(fn => fn(msg, col));
      });
    }

    if (this.backendObj.updateCheckResult) {
      this.backendObj.updateCheckResult.connect((jsonStr: string) => {
        try {
          const res = JSON.parse(jsonStr);
          this.updateResultListeners.forEach(fn => fn(res));
        } catch (e) {
          this.updateResultListeners.forEach(fn => fn({ message: jsonStr }));
        }
      });
    }

    if (this.backendObj.downloadProgress) {
      this.backendObj.downloadProgress.connect((down: number, total: number, pct: number) => {
        this.downloadProgressListeners.forEach(fn => fn(down, total, pct));
      });
    }

    if (this.backendObj.readyToInstall) {
      this.backendObj.readyToInstall.connect((path: string) => {
        this.readyToInstallListeners.forEach(fn => fn(path));
      });
    }

    if (this.backendObj.verificationError) {
      this.backendObj.verificationError.connect((err: string) => {
        this.verificationErrorListeners.forEach(fn => fn(err));
      });
    }
  }

  private initStandaloneEmulation() {
    this.statusListeners.forEach(fn => fn('Connected to Virtual Metrology Sensor (COM5)', '#21D789'));

    this.simulationInterval = setInterval(() => {
      this.simPacketCounter++;
      // Realistic physical drift of ambient illumination
      const drift = (Math.random() - 0.49) * 4.2;
      this.simBaseLux = Math.max(1.0, this.simBaseLux + drift);
      const raw = parseFloat(this.simBaseLux.toFixed(2));
      const cal = parseFloat((raw * 1.0).toFixed(2));

      const packet: TelemetryPacket = {
        raw_lux: raw,
        cal_lux: cal,
        packet_id: this.simPacketCounter,
        port: 'COM5',
        timestamp: new Date().toLocaleTimeString(),
        checksum_ok: true,
      };

      this.telemetryListeners.forEach(fn => fn(packet));
    }, 400); // 2.5 Hz continuous high-res mode matching BH1750
  }

  // Event subscription methods
  public onTelemetry(cb: TelemetryListener) {
    this.telemetryListeners.push(cb);
    return () => {
      this.telemetryListeners = this.telemetryListeners.filter(f => f !== cb);
    };
  }

  public onStatus(cb: StatusListener) {
    this.statusListeners.push(cb);
    return () => {
      this.statusListeners = this.statusListeners.filter(f => f !== cb);
    };
  }

  public onUpdateResult(cb: UpdateResultListener) {
    this.updateResultListeners.push(cb);
    return () => {
      this.updateResultListeners = this.updateResultListeners.filter(f => f !== cb);
    };
  }

  public onDownloadProgress(cb: DownloadProgressListener) {
    this.downloadProgressListeners.push(cb);
    return () => {
      this.downloadProgressListeners = this.downloadProgressListeners.filter(f => f !== cb);
    };
  }

  public onReadyToInstall(cb: ReadyToInstallListener) {
    this.readyToInstallListeners.push(cb);
    return () => {
      this.readyToInstallListeners = this.readyToInstallListeners.filter(f => f !== cb);
    };
  }

  public onVerificationError(cb: VerificationErrorListener) {
    this.verificationErrorListeners.push(cb);
    return () => {
      this.verificationErrorListeners = this.verificationErrorListeners.filter(f => f !== cb);
    };
  }

  // Commands to Python
  public async scanPorts(): Promise<string[]> {
    if (this.backendObj?.scanPorts) {
      const res = await this.backendObj.scanPorts();
      return JSON.parse(res);
    }
    return ['COM5 — Arduino Uno (ATmega328P)', 'COM3 — USB-SERIAL CH340'];
  }

  public async connectHardware(port: string, baud: number): Promise<void> {
    if (this.backendObj?.connectHardware) {
      await this.backendObj.connectHardware(port, baud);
    } else {
      console.log(`[Bridge] connectHardware: ${port} @ ${baud}`);
    }
  }

  public async disconnectHardware(): Promise<void> {
    if (this.backendObj?.disconnectHardware) {
      await this.backendObj.disconnectHardware();
    }
  }

  public async getCalibration(): Promise<CalibrationProfile> {
    if (this.backendObj?.getCalibration) {
      const res = await this.backendObj.getCalibration();
      return JSON.parse(res);
    }
    return {
      profile_name: 'Standard Factory (BH1750)',
      zero_offset: 0.0,
      gain_multiplier: 1.0,
      calibrated_at: '2026-11-13',
      notes: 'Standard BH1750 high-resolution photopic curve',
    };
  }

  public async saveCalibration(zero: number, gain: number, notes: string): Promise<boolean> {
    if (this.backendObj?.saveCalibration) {
      return await this.backendObj.saveCalibration(zero, gain, notes);
    }
    console.log('[Bridge] saveCalibration:', { zero, gain, notes });
    return true;
  }

  public async getSettings(): Promise<UserSettings> {
    if (this.backendObj?.getSettings) {
      const res = await this.backendObj.getSettings();
      return JSON.parse(res);
    }
    return {
      serial_port: 'COM5',
      baud_rate: 115200,
      update_channel: 'stable',
      auto_check_updates: true,
      last_update_check: '2026-11-13 22:00:00',
      latest_known_version: '2.1.0',
    };
  }

  public async saveSettings(settings: UserSettings): Promise<boolean> {
    if (this.backendObj?.saveSettings) {
      return await this.backendObj.saveSettings(JSON.stringify(settings));
    }
    return true;
  }

  public checkForUpdates(channel: 'stable' | 'beta'): void {
    if (this.backendObj?.checkForUpdates) {
      this.backendObj.checkForUpdates(channel);
    } else {
      // Standalone simulation response
      setTimeout(() => {
        this.updateResultListeners.forEach(fn =>
          fn({
            available: true,
            version: '2.1.0',
            tag_name: 'v2.1.0',
            channel: channel,
            release_name: `LuxSense Pro v2.1.0 [${channel.toUpperCase()}]`,
            body: `### Release Highlights:\n* **Dual Channels:** Stable & Beta distribution channels.\n* **SHA-256 Validation:** Immediate deletion on tamper.\n* **Updater Bootstrapper:** Automatic backup & rollback.\n* **Persistent Storage:** Zero data loss in AppData.`,
          })
        );
      }, 1200);
    }
  }

  public downloadUpdate(releaseData: any): void {
    if (this.backendObj?.downloadUpdate) {
      this.backendObj.downloadUpdate(JSON.stringify(releaseData));
    } else {
      // Standalone download simulation
      let progress = 0;
      const total = 39522420;
      const interval = setInterval(() => {
        progress += 4000000;
        const pct = Math.min(100, (progress / total) * 100);
        this.downloadProgressListeners.forEach(fn => fn(progress, total, pct));
        if (pct >= 100) {
          clearInterval(interval);
          this.readyToInstallListeners.forEach(fn => fn('C:\\ProgramData\\LuxSense-Pro-Setup-v2.1.0.exe'));
        }
      }, 350);
    }
  }

  public installUpdate(): void {
    if (this.backendObj?.installUpdate) {
      this.backendObj.installUpdate();
    } else {
      alert('[Bridge Simulation] Invoking Standalone Updater Bootstrapper: Handing off to updater.exe with PID wait.');
    }
  }

  public async getTelemetryHistory(limit: number = 100): Promise<TelemetryRecord[]> {
    if (this.backendObj?.getTelemetryHistory) {
      const res = await this.backendObj.getTelemetryHistory(limit);
      return JSON.parse(res);
    }
    // Standalone sample history
    return Array.from({ length: 30 }).map((_, i) => ({
      id: 30 - i,
      timestamp: new Date(Date.now() - i * 15000).toLocaleTimeString(),
      packet_id: 1000 - i,
      raw_lux: parseFloat((520 + Math.sin(i) * 35).toFixed(2)),
      calibrated_lux: parseFloat((520 + Math.sin(i) * 35).toFixed(2)),
      port: 'COM5',
    }));
  }

  public async exportHistoryCsv(): Promise<string> {
    if (this.backendObj?.exportHistoryCsv) {
      return await this.backendObj.exportHistoryCsv();
    }
    return 'luxsense_telemetry_export.csv';
  }

  public minimize(): void {
    if (this.backendObj?.minimizeWindow) this.backendObj.minimizeWindow();
  }
  public maximize(): void {
    if (this.backendObj?.maximizeWindow) this.backendObj.maximizeWindow();
  }
  public close(): void {
    if (this.backendObj?.closeWindow) this.backendObj.closeWindow();
  }
}

export const bridge = new BridgeClient();
