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
  theme?: 'dark' | 'light' | 'system';
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
type HardwareStateListener = (state: string) => void;
type UpdateResultListener = (result: any) => void;
type DownloadProgressListener = (downloaded: number, total: number, percent: number) => void;
type ReadyToInstallListener = (path: string) => void;
type VerificationErrorListener = (err: string) => void;
type FirmwareStatusListener = (status: any) => void;
type FirmwareCheckListener = (result: any) => void;
type FirmwareProgressListener = (percent: number, phase: string) => void;
type FirmwareCompletedListener = (success: boolean, message: string) => void;
type FirmwareLogListener = (line: string) => void;

class BridgeClient {
  private isQtConnected = false;
  private backendObj: any = null;

  private telemetryListeners: TelemetryListener[] = [];
  private statusListeners: StatusListener[] = [];
  private hardwareStateListeners: HardwareStateListener[] = [];
  private updateResultListeners: UpdateResultListener[] = [];
  private downloadProgressListeners: DownloadProgressListener[] = [];
  private readyToInstallListeners: ReadyToInstallListener[] = [];
  private verificationErrorListeners: VerificationErrorListener[] = [];
  private firmwareStatusListeners: FirmwareStatusListener[] = [];
  private firmwareCheckListeners: FirmwareCheckListener[] = [];
  private firmwareProgressListeners: FirmwareProgressListener[] = [];
  private firmwareCompletedListeners: FirmwareCompletedListener[] = [];
  private firmwareLogListeners: FirmwareLogListener[] = [];

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

    if (this.backendObj.hardwareStateChanged) {
      this.backendObj.hardwareStateChanged.connect((state: string) => {
        this.hardwareStateListeners.forEach(fn => fn(state));
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

    if (this.backendObj.firmwareStatusChanged) {
      this.backendObj.firmwareStatusChanged.connect((jsonStr: string) => {
        try {
          const st = JSON.parse(jsonStr);
          this.firmwareStatusListeners.forEach(fn => fn(st));
        } catch {
          this.firmwareStatusListeners.forEach(fn => fn(jsonStr));
        }
      });
    }

    if (this.backendObj.firmwareCheckResult) {
      this.backendObj.firmwareCheckResult.connect((jsonStr: string) => {
        try {
          const res = JSON.parse(jsonStr);
          this.firmwareCheckListeners.forEach(fn => fn(res));
        } catch {
          this.firmwareCheckListeners.forEach(fn => fn({ available: false, error: jsonStr }));
        }
      });
    }

    if (this.backendObj.firmwareFlashProgress) {
      this.backendObj.firmwareFlashProgress.connect((pct: number, phase: string) => {
        this.firmwareProgressListeners.forEach(fn => fn(pct, phase));
      });
    }

    if (this.backendObj.firmwareFlashCompleted) {
      this.backendObj.firmwareFlashCompleted.connect((success: boolean, msg: string) => {
        this.firmwareCompletedListeners.forEach(fn => fn(success, msg));
      });
    }

    if (this.backendObj.firmwareLogEmitted) {
      this.backendObj.firmwareLogEmitted.connect((line: string) => {
        this.firmwareLogListeners.forEach(fn => fn(line));
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

  public onHardwareState(cb: HardwareStateListener) {
    this.hardwareStateListeners.push(cb);
    return () => {
      this.hardwareStateListeners = this.hardwareStateListeners.filter(f => f !== cb);
    };
  }

  public async getHardwareState(): Promise<string> {
    if (this.backendObj?.getHardwareState) {
      return await this.backendObj.getHardwareState();
    }
    return 'DISCONNECTED';
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

  public onFirmwareStatus(cb: FirmwareStatusListener) {
    this.firmwareStatusListeners.push(cb);
    return () => {
      this.firmwareStatusListeners = this.firmwareStatusListeners.filter(f => f !== cb);
    };
  }

  public onFirmwareCheckResult(cb: FirmwareCheckListener) {
    this.firmwareCheckListeners.push(cb);
    return () => {
      this.firmwareCheckListeners = this.firmwareCheckListeners.filter(f => f !== cb);
    };
  }

  public onFirmwareFlashProgress(cb: FirmwareProgressListener) {
    this.firmwareProgressListeners.push(cb);
    return () => {
      this.firmwareProgressListeners = this.firmwareProgressListeners.filter(f => f !== cb);
    };
  }

  public onFirmwareFlashCompleted(cb: FirmwareCompletedListener) {
    this.firmwareCompletedListeners.push(cb);
    return () => {
      this.firmwareCompletedListeners = this.firmwareCompletedListeners.filter(f => f !== cb);
    };
  }

  public onFirmwareLog(cb: FirmwareLogListener) {
    this.firmwareLogListeners.push(cb);
    return () => {
      this.firmwareLogListeners = this.firmwareLogListeners.filter(f => f !== cb);
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
      last_update_check: '2026-11-15 15:30:00',
      latest_known_version: '2.3.0',
      theme: 'dark',
    };
  }

  public async getAppVersion(): Promise<string> {
    if (this.backendObj?.getAppVersion) {
      return await this.backendObj.getAppVersion();
    }
    return '2.3.0';
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

  // Scientific Edition API Methods
  public async getUncertaintyBudget(sessionId: string = 'default', accuracyPct: number = 7.0): Promise<any> {
    if (this.backendObj?.getUncertaintyBudget) {
      const res = await this.backendObj.getUncertaintyBudget(sessionId, accuracyPct);
      return JSON.parse(res);
    }
    return {
      sample_mean: 542.80,
      standard_deviation: 3.42,
      standard_error: 0.342,
      degrees_of_freedom: 99,
      sensor_accuracy_spec_percent: accuracyPct,
      sensor_uncertainty_lux: 21.94,
      repeatability_uncertainty_lux: 0.342,
      combined_standard_uncertainty: 21.94,
      expanded_uncertainty_95: 43.88,
      relative_expanded_uncertainty_pct: 8.08
    };
  }

  public async getExposureReport(sessionId: string = 'default'): Promise<any> {
    if (this.backendObj?.getExposureReport) {
      const res = await this.backendObj.getExposureReport(sessionId);
      return JSON.parse(res);
    }
    return {
      total_duration_seconds: 3600.0,
      duration_hours: 1.0,
      cumulative_lux_seconds: 1954080.0,
      cumulative_lux_hours: 542.8,
      average_lux: 542.8,
      daily_projected_lux_hours: 5428.0,
      annual_projected_lux_hours: 1981220.0,
      cie157_conservation_status: "COMPLIANT: Standard Archival Laboratory Storage"
    };
  }

  public async recordSpatialPoint(sessionId: string, pointId: string, label: string, x: number, y: number, lux: number): Promise<boolean> {
    if (this.backendObj?.recordSpatialPoint) {
      return await this.backendObj.recordSpatialPoint(sessionId, pointId, label, x, y, lux);
    }
    return true;
  }

  public async getSpatialPoints(sessionId: string = 'default'): Promise<any[]> {
    if (this.backendObj?.getSpatialPoints) {
      const res = await this.backendObj.getSpatialPoints(sessionId);
      return JSON.parse(res);
    }
    return [
      { point_id: "P1", label: "Desk Left", x_m: 0.0, y_m: 0.0, measured_lux: 512.4, timestamp: "10:14:02" },
      { point_id: "P2", label: "Desk Center", x_m: 0.6, y_m: 0.0, measured_lux: 554.8, timestamp: "10:14:15" },
      { point_id: "P3", label: "Desk Right", x_m: 1.2, y_m: 0.0, measured_lux: 538.1, timestamp: "10:14:30" },
      { point_id: "P4", label: "Rear Wall", x_m: 0.6, y_m: 1.0, measured_lux: 489.2, timestamp: "10:14:45" }
    ];
  }

  public async clearSpatialPoints(sessionId: string = 'default'): Promise<boolean> {
    if (this.backendObj?.clearSpatialPoints) {
      return await this.backendObj.clearSpatialPoints(sessionId);
    }
    return true;
  }

  public async getUniformityReport(sessionId: string = 'default'): Promise<any> {
    if (this.backendObj?.getUniformityReport) {
      const res = await this.backendObj.getUniformityReport(sessionId);
      return JSON.parse(res);
    }
    return {
      points_count: 4,
      min_lux: 489.2,
      max_lux: 554.8,
      average_lux: 523.6,
      uniformity_u1: 0.934,
      uniformity_u2: 0.882,
      diversity_ratio: 1.13,
      en12464_compliant: true,
      summary: "Compliant with EN 12464-1 (U1 = 0.93 >= 0.60). High spatial lighting uniformity."
    };
  }

  public async createExperimentSession(sessionId: string, name: string, operator: string, lightingType: string, minTh: number, maxTh: number, notes: string): Promise<boolean> {
    if (this.backendObj?.createExperimentSession) {
      return await this.backendObj.createExperimentSession(sessionId, name, operator, lightingType, minTh, maxTh, notes);
    }
    return true;
  }

  public async listExperimentSessions(): Promise<any[]> {
    if (this.backendObj?.listExperimentSessions) {
      const res = await this.backendObj.listExperimentSessions();
      return JSON.parse(res);
    }
    return [
      {
        session_id: "default",
        name: "Standard Laboratory Baseline",
        operator: "DevPro Metrologist",
        lighting_type: "Broadband Ambient (LED/Daylight)",
        created_at: "2026-11-15 10:00:00",
        min_threshold: 300.0,
        max_threshold: 750.0,
        notes: "Baseline calibration and repeatability evaluation."
      }
    ];
  }

  public async exportScientificReport(sessionId: string = 'default', formatType: string = 'csv'): Promise<string> {
    if (this.backendObj?.exportScientificReport) {
      return await this.backendObj.exportScientificReport(sessionId, formatType);
    }
    return `LuxSense_Scientific_Report_${sessionId}.${formatType}`;
  }

  public async getSerialLatency(): Promise<number> {
    if (this.backendObj?.getSerialLatency) {
      return await this.backendObj.getSerialLatency();
    }
    return 1.4;
  }

  // Firmware Management Methods
  public async getFirmwareStatus(): Promise<any> {
    if (this.backendObj?.getFirmwareStatus) {
      const res = await this.backendObj.getFirmwareStatus();
      return JSON.parse(res);
    }
    return {
      board: "Arduino Uno R3",
      mcu: "ATmega328P (16MHz)",
      bootloader: "Optiboot v4.4 (STK500v1)",
      port: "COM5",
      baud_rate: 115200,
      installed_version: "1.2.0",
      is_connected: true,
      sensor: "BH1750 (0x23 / 0x5C)",
      hardware_state: "LIVE MEASUREMENT"
    };
  }

  public async checkFirmwareUpdates(): Promise<any> {
    if (this.backendObj?.checkFirmwareUpdates) {
      const res = await this.backendObj.checkFirmwareUpdates();
      return JSON.parse(res);
    }
    return {
      available: true,
      valid: true,
      message: "Valid DevPro-CORP Ed25519 Publisher Signature",
      manifest: {
        firmware_version: "2.0.0",
        release_name: "LuxSense Pro Microcode v2.0.0 (Scientific Radiometry)",
        target_board: "arduino:avr:uno",
        target_mcu: "atmega328p",
        bootloader: "optiboot",
        clock_mhz: 16,
        release_notes: "Dynamic dual-address I2C detection, handshake verification, and explicit disconnection reporting.",
        publisher: "DevPro-CORP Root Authority",
        hex_sha256: "0d252ba9d2fbe909055ffece802cd815879001916b41587d278c33ba19cc5c23"
      }
    };
  }

  public async startFirmwareFlash(port: string, hexPath: string = '', allowDowngrade: boolean = false): Promise<boolean> {
    if (this.backendObj?.startFirmwareFlash) {
      return await this.backendObj.startFirmwareFlash(port, hexPath, allowDowngrade);
    }
    return true;
  }

  public abortFirmwareFlash(): void {
    if (this.backendObj?.abortFirmwareFlash) {
      this.backendObj.abortFirmwareFlash();
    }
  }

  public async getFirmwareDiagnosticLogs(): Promise<string> {
    if (this.backendObj?.getFirmwareDiagnosticLogs) {
      return await this.backendObj.getFirmwareDiagnosticLogs();
    }
    return "Firmware flashing log initialized.";
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

