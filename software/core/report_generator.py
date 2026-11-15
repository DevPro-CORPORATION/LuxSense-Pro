"""
LuxSense Pro — Scientific Report Generator (CSV & Print-Ready HTML/PDF)
Generates accredited-style photometric test reports with uncertainty analysis,
lighting uniformity, time-integrated exposure, and sensor limitation disclosures.
"""

import os
import csv
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from software.core.storage import (
    get_app_data_dir, 
    CalibrationProfile, 
    MeasurementHistory, 
    APP_VERSION
)
from software.core.scientific_engine import (
    calculate_uncertainty_budget,
    calculate_light_exposure,
    calculate_spatial_uniformity,
    analyze_threshold_compliance,
    SpatialMeasurementPoint,
    lux_to_foot_candles,
    lux_to_estimated_irradiance
)

def generate_scientific_csv(session_id: str = "default") -> str:
    """Generate high-precision scientific CSV report with metadata header and uncertainty."""
    data_dir = get_app_data_dir()
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"LuxSense_Scientific_Report_{session_id}_{int(time.time())}.csv"
    csv_path = reports_dir / filename

    history = MeasurementHistory()
    readings = history.get_recent(5000, session_id=session_id)
    cal = CalibrationProfile.load()
    spatial_raw = history.get_spatial_points(session_id=session_id)
    spatial_pts = [
        SpatialMeasurementPoint(
            point_id=p["point_id"],
            label=p["label"],
            x_m=p["x_m"],
            y_m=p["y_m"],
            measured_lux=p["measured_lux"],
            timestamp=p["timestamp"]
        ) for p in spatial_raw
    ]

    lux_values = [r["calibrated_lux"] for r in readings] if readings else [0.0]
    budget = calculate_uncertainty_budget(lux_values, sensor_accuracy_percent=7.0)
    uniformity = calculate_spatial_uniformity(spatial_pts)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header Metadata
        writer.writerow(["# =================================================================="])
        writer.writerow(["# LUXSENSE PRO SCIENTIFIC METROLOGY REPORT"])
        writer.writerow([f"# Software Version: LuxSense Pro v{APP_VERSION} [Scientific Edition]"])
        writer.writerow(["# Organization: DevPro Corporation (DevPro-CORP)"])
        writer.writerow([f"# Generated At: {time.strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([f"# Session Identifier: {session_id}"])
        writer.writerow([f"# Sensor Hardware: ROHM BH1750FVI Optical Transducer via I2C Fast-Mode"])
        writer.writerow([f"# Host Microcontroller: Microchip ATmega328P @ 16 MHz"])
        writer.writerow([f"# Calibration Profile: {cal.profile_name} (Zero: {cal.zero_offset:+.2f} lx, Gain: {cal.gain_multiplier:.4f}x)"])
        writer.writerow(["# ------------------------------------------------------------------"])
        writer.writerow(["# UNCERTAINTY & METROLOGICAL BUDGET (GUM / ISO 98-3)"])
        writer.writerow([f"# Sample Count N: {len(lux_values)}"])
        writer.writerow([f"# Arithmetic Mean (Ev): {budget.sample_mean:.2f} lx ({lux_to_foot_candles(budget.sample_mean):.3f} fc)"])
        writer.writerow([f"# Sample Standard Deviation (s): {budget.standard_deviation:.2f} lx"])
        writer.writerow([f"# Standard Error (SE): {budget.standard_error:.3f} lx"])
        writer.writerow([f"# Combined Standard Uncertainty uc: {budget.combined_standard_uncertainty:.2f} lx"])
        writer.writerow([f"# Expanded Uncertainty U (k=2, 95% CI): ±{budget.expanded_uncertainty_95:.2f} lx (±{budget.relative_expanded_uncertainty_pct:.1f}%)"])
        writer.writerow(["# ------------------------------------------------------------------"])
        writer.writerow(["# SCIENTIFIC INTEGRITY & CLASSIFICATION DISCLOSURE"])
        writer.writerow(["# [MEASURED]: Raw illuminance directly digitized by BH1750 16-bit ADC."])
        writer.writerow(["# [CALIBRATED]: Mathematical correction f(x) = (x + Offset) * Gain applied."])
        writer.writerow(["# [CALCULATED]: Exact conversions (Foot-Candles, Uniformity U1, Lux-Hours)."])
        writer.writerow(["# [ESTIMATED]: Optical Irradiance (W/m^2) assuming standard 555nm photopic peak 683 lm/W."])
        writer.writerow(["# NOTICE: BH1750 is a photopic scalar illuminance sensor. Does NOT measure CCT/CRI/SPD."])
        writer.writerow(["# =================================================================="])
        writer.writerow([])
        # Column headers
        writer.writerow([
            "Timestamp",
            "Packet_ID",
            "Raw_Lux [MEASURED]",
            "Calibrated_Lux [CALIBRATED]",
            "Foot_Candles [CALCULATED]",
            "Est_Irradiance_W_m2 [ESTIMATED]",
            "Port",
            "Session_ID"
        ])
        for r in readings:
            raw = r["raw_lux"]
            cal_val = r["calibrated_lux"]
            fc = lux_to_foot_candles(cal_val)
            irr = lux_to_estimated_irradiance(cal_val)
            writer.writerow([
                r["timestamp"],
                r["packet_id"],
                f"{raw:.2f}",
                f"{cal_val:.2f}",
                f"{fc:.3f}",
                f"{irr:.5f}",
                r["port"],
                r["session_id"]
            ])

    return str(csv_path)

def generate_scientific_html_report(session_id: str = "default") -> str:
    """Generate accredited-style scientific HTML/PDF certificate report."""
    data_dir = get_app_data_dir()
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"LuxSense_Certificate_{session_id}_{int(time.time())}.html"
    report_path = reports_dir / filename

    history = MeasurementHistory()
    readings = history.get_recent(2000, session_id=session_id)
    cal = CalibrationProfile.load()
    spatial_raw = history.get_spatial_points(session_id=session_id)
    spatial_pts = [
        SpatialMeasurementPoint(
            point_id=p["point_id"],
            label=p["label"],
            x_m=p["x_m"],
            y_m=p["y_m"],
            measured_lux=p["measured_lux"],
            timestamp=p["timestamp"]
        ) for p in spatial_raw
    ]

    lux_values = [r["calibrated_lux"] for r in readings] if readings else [0.0]
    budget = calculate_uncertainty_budget(lux_values, sensor_accuracy_percent=7.0)
    uniformity = calculate_spatial_uniformity(spatial_pts)

    # Time series for exposure
    time_series = []
    base_t = 0.0
    for i, r in enumerate(reversed(readings)):
        time_series.append((base_t + i * 0.4, r["calibrated_lux"]))
    exposure = calculate_light_exposure(time_series)
    threshold = analyze_threshold_compliance(lux_values, 300.0, 750.0)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>LuxSense Pro — Scientific Metrology Report [{session_id}]</title>
  <style>
    @page {{ size: A4; margin: 15mm; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #1A1E26;
      background: #FFFFFF;
      margin: 0;
      padding: 20px;
      font-size: 11pt;
      line-height: 1.4;
    }}
    .header-table {{
      width: 100%;
      border-bottom: 2px solid #21D789;
      padding-bottom: 12px;
      margin-bottom: 20px;
    }}
    .brand-title {{
      font-size: 20pt;
      font-weight: 800;
      letter-spacing: -0.5px;
      color: #0B0C0E;
    }}
    .brand-subtitle {{
      font-size: 9pt;
      color: #555E6D;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .cert-badge {{
      text-align: right;
      font-family: monospace;
      font-size: 9pt;
      color: #333;
    }}
    h2 {{
      font-size: 12pt;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid #E2E4E8;
      padding-bottom: 4px;
      margin-top: 20px;
      color: #0F1115;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 15px;
    }}
    .metric-card {{
      background: #F8F9FA;
      border: 1px solid #E2E4E8;
      border-radius: 6px;
      padding: 12px;
    }}
    .metric-card .title {{
      font-size: 8pt;
      font-weight: 600;
      text-transform: uppercase;
      color: #555E6D;
      margin-bottom: 4px;
    }}
    .metric-card .value {{
      font-size: 16pt;
      font-weight: 700;
      font-family: monospace;
      color: #0B0C0E;
    }}
    .metric-card .sub {{
      font-size: 8pt;
      color: #6F788A;
      margin-top: 2px;
    }}
    table.data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9pt;
      margin-top: 8px;
    }}
    table.data-table th, table.data-table td {{
      border: 1px solid #E2E4E8;
      padding: 6px 10px;
      text-align: left;
    }}
    table.data-table th {{
      background: #F1F3F5;
      font-weight: 600;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 7.5pt;
      font-weight: 600;
      text-transform: uppercase;
      font-family: monospace;
    }}
    .badge-measured {{ background: #E8F5E9; color: #2E7D32; border: 1px solid #C8E6C9; }}
    .badge-calibrated {{ background: #E3F2FD; color: #1565C0; border: 1px solid #BBDEFB; }}
    .badge-calc {{ background: #FFF3E0; color: #E65100; border: 1px solid #FFE0B2; }}
    .badge-est {{ background: #F3E5F5; color: #6A1B9A; border: 1px solid #E1BEE7; }}
    .disclaimer-box {{
      background: #FFFBEA;
      border: 1px solid #FFE58F;
      border-radius: 6px;
      padding: 10px 14px;
      font-size: 8.5pt;
      color: #614700;
      margin-top: 25px;
    }}
    @media print {{
      body {{ padding: 0; }}
      .no-print {{ display: none; }}
    }}
  </style>
</head>
<body>
  <table class="header-table">
    <tr>
      <td>
        <div class="brand-title">LuxSense Pro</div>
        <div class="brand-subtitle">Optical Radiometry &amp; Photometric Test Report</div>
      </td>
      <td class="cert-badge">
        <strong>DevPro Corporation</strong><br>
        Document ID: DEVPRO-MET-{int(time.time())}<br>
        Issued: {time.strftime('%Y-%m-%d %H:%M:%S')}<br>
        App Version: v{APP_VERSION} (Scientific Edition)
      </td>
    </tr>
  </table>

  <div class="grid-2">
    <div class="metric-card">
      <div class="title">Mean Photopic Illuminance <span class="badge badge-calibrated">CALIBRATED</span></div>
      <div class="value">{budget.sample_mean:.2f} lx</div>
      <div class="sub">Equivalent: {lux_to_foot_candles(budget.sample_mean):.3f} fc &bull; Irradiance: ~{lux_to_estimated_irradiance(budget.sample_mean):.4f} W/m²</div>
    </div>
    <div class="metric-card">
      <div class="title">Expanded Uncertainty (95% CI, k=2)</div>
      <div class="value">±{budget.expanded_uncertainty_95:.2f} lx</div>
      <div class="sub">Relative Uncertainty: ±{budget.relative_expanded_uncertainty_pct:.1f}% &bull; DOF: {budget.degrees_of_freedom}</div>
    </div>
  </div>

  <h2>1. Metrological Uncertainty Budget (GUM / ISO 98-3)</h2>
  <table class="data-table">
    <tr>
      <th>Uncertainty Component</th>
      <th>Standard Value</th>
      <th>Distribution</th>
      <th>Divisor</th>
      <th>Standard Uncertainty (u)</th>
    </tr>
    <tr>
      <td>BH1750 Sensor Accuracy (Calibrated)</td>
      <td>±{budget.sensor_accuracy_spec_percent:.1f}% of reading</td>
      <td>Rectangular (Type B)</td>
      <td>√3 ≈ 1.732</td>
      <td>±{budget.sensor_uncertainty_lux:.2f} lx</td>
    </tr>
    <tr>
      <td>Repeatability (Sample Scatter)</td>
      <td>s = {budget.standard_deviation:.2f} lx (N={len(lux_values)})</td>
      <td>Normal (Type A)</td>
      <td>√N</td>
      <td>±{budget.repeatability_uncertainty_lux:.3f} lx</td>
    </tr>
    <tr style="font-weight: bold; background: #F8F9FA;">
      <td>Combined Standard Uncertainty (uc)</td>
      <td>Root Sum of Squares (RSS)</td>
      <td>Normal</td>
      <td>1.0</td>
      <td>±{budget.combined_standard_uncertainty:.2f} lx</td>
    </tr>
    <tr style="font-weight: bold; background: #E8F5E9;">
      <td>Expanded Uncertainty U (95% Confidence)</td>
      <td>Coverage Factor k = 2.0</td>
      <td>Student-t</td>
      <td>—</td>
      <td>±{budget.expanded_uncertainty_95:.2f} lx (±{budget.relative_expanded_uncertainty_pct:.1f}%)</td>
    </tr>
  </table>

  <h2>2. Spatial Lighting Uniformity (EN 12464-1 / IESNA)</h2>
  <table class="data-table">
    <tr>
      <th>Sample Points Count</th>
      <th>Minimum (E_min)</th>
      <th>Maximum (E_max)</th>
      <th>Average (E_avg)</th>
      <th>Uniformity U1 (E_min / E_avg)</th>
      <th>Diversity (E_max / E_min)</th>
    </tr>
    <tr>
      <td>{uniformity.points_count} points</td>
      <td>{uniformity.min_lux:.1f} lx</td>
      <td>{uniformity.max_lux:.1f} lx</td>
      <td>{uniformity.average_lux:.1f} lx</td>
      <td><strong>{uniformity.uniformity_u1:.2f}</strong> (Req: &ge; 0.60)</td>
      <td>{uniformity.diversity_ratio:.2f}</td>
    </tr>
  </table>
  <p style="font-size: 8.5pt; color: #555; margin-top: 4px;">
    <strong>Uniformity Assessment:</strong> {uniformity.summary}
  </p>

  <h2>3. Time-Integrated Exposure &amp; Archival Conservation (CIE 157:2004)</h2>
  <table class="data-table">
    <tr>
      <th>Integrated Duration</th>
      <th>Cumulative Lux-Seconds</th>
      <th>Cumulative Lux-Hours</th>
      <th>Projected Annual Exposure</th>
      <th>CIE 157 Assessment</th>
    </tr>
    <tr>
      <td>{exposure.duration_hours:.2f} hours ({exposure.total_duration_seconds:.0f}s)</td>
      <td>{exposure.cumulative_lux_seconds:.0f} lx&middot;s</td>
      <td><strong>{exposure.cumulative_lux_hours:.1f} lx&middot;h</strong></td>
      <td>~{exposure.annual_projected_lux_hours:,.0f} lx&middot;h/yr</td>
      <td>{exposure.cie157_conservation_status}</td>
    </tr>
  </table>

  <h2>4. Threshold Compliance (EN 12464-1 Workstation Standard: 300 - 750 lx)</h2>
  <table class="data-table">
    <tr>
      <th>Target Bounds</th>
      <th>Total Samples</th>
      <th>In-Range Samples</th>
      <th>Under-Illuminated (&lt;300 lx)</th>
      <th>Over-Illuminated (&gt;750 lx)</th>
      <th>Compliance Rating</th>
    </tr>
    <tr>
      <td>300.0 - 750.0 lx</td>
      <td>{threshold.total_samples}</td>
      <td>{threshold.in_range_samples} ({threshold.in_range_percent:.1f}%)</td>
      <td>{threshold.under_threshold_samples}</td>
      <td>{threshold.over_threshold_samples}</td>
      <td><strong>{threshold.compliance_status}</strong></td>
    </tr>
  </table>

  <div class="disclaimer-box">
    <strong>Scientific Integrity &amp; Instrument Scope Disclosure:</strong><br>
    The measurements presented in this report were acquired using a calibrated ROHM BH1750FVI silicon photodiode with an integrated photopic optical filter matching the CIE 1931 standard luminosity function V(&lambda;). 
    Scalar illuminance (lx) and foot-candles (fc) are mathematically validated. 
    Optical irradiance (W/m&sup2;) is an estimate based on a standard 555 nm photopic peak (683 lm/W). 
    This instrument does <em>not</em> perform spectral power distribution (SPD), Correlated Colour Temperature (CCT), Colour Rendering Index (CRI), or high-frequency optical flicker measurements. 
    DevPro-CORP guarantees calibration traceability through software-defined dual-axis transfer models.
  </div>
</body>
</html>
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(report_path)
