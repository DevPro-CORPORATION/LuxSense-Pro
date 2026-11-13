export type WorkspaceTab = 
  | 'monitor' 
  | 'analytics' 
  | 'calibration' 
  | 'settings' 
  | 'techinfo' 
  | 'team';

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

export interface StatisticalSummary {
  min: number;
  max: number;
  mean: number;
  stdDev: number;
  median: number;
  crestFactor: number;
  sampleCount: number;
}

export interface UpdateInfo {
  available: boolean;
  version: string;
  tag_name: string;
  channel: 'stable' | 'beta';
  release_name: string;
  body: string;
  download_url?: string;
  sha256?: string;
}
