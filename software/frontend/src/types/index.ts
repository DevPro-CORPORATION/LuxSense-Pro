export type WorkspaceTab = 
  | 'monitor' 
  | 'scientific'
  | 'analytics' 
  | 'calibration'
  | 'hardware' 
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
  theme?: 'dark' | 'light' | 'system';
}

export interface TelemetryRecord {
  id?: number;
  timestamp: string;
  session_id?: string;
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

export interface UncertaintyBudget {
  sample_mean: number;
  standard_deviation: number;
  standard_error: number;
  degrees_of_freedom: number;
  sensor_accuracy_spec_percent: number;
  sensor_uncertainty_lux: number;
  repeatability_uncertainty_lux: number;
  combined_standard_uncertainty: number;
  expanded_uncertainty_95: number;
  relative_expanded_uncertainty_pct: number;
}

export interface ExposureReport {
  total_duration_seconds: number;
  duration_hours: number;
  cumulative_lux_seconds: number;
  cumulative_lux_hours: number;
  average_lux: number;
  daily_projected_lux_hours: number;
  annual_projected_lux_hours: number;
  cie157_conservation_status: string;
}

export interface SpatialMeasurementPoint {
  point_id: string;
  session_id?: string;
  label: string;
  x_m: number;
  y_m: number;
  measured_lux: number;
  timestamp: string;
}

export interface UniformityReport {
  points_count: number;
  min_lux: number;
  max_lux: number;
  average_lux: number;
  uniformity_u1: number;
  uniformity_u2: number;
  diversity_ratio: number;
  en12464_compliant: boolean;
  summary: string;
}

export interface ExperimentSession {
  session_id: string;
  name: string;
  operator: string;
  lighting_type: string;
  created_at: string;
  min_threshold: number;
  max_threshold: number;
  notes: string;
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

export interface FirmwareStatus {
  board: string;
  mcu: string;
  bootloader: string;
  port: string;
  baud_rate: number;
  installed_version: string;
  is_connected: boolean;
  sensor: string;
  hardware_state: string;
}

export interface FirmwareManifestInfo {
  firmware_version: string;
  release_name: string;
  published_at: string;
  target_board: string;
  target_mcu: string;
  bootloader: string;
  baud_rate: number;
  clock_mhz: number;
  supported_sensors: string[];
  min_app_version: string;
  hex_filename: string;
  hex_sha256: string;
  hex_size: number;
  release_notes: string;
  publisher: string;
  signature: string;
}

export interface FirmwareCheckResult {
  available: boolean;
  valid?: boolean;
  message?: string;
  manifest?: FirmwareManifestInfo;
  hex_available?: boolean;
  hex_path?: string;
  error?: string;
}
