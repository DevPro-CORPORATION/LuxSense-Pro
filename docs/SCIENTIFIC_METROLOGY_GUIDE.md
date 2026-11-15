# LuxSense Pro — Scientific Metrology & Photometric Guide

**Document ID:** SMG-DEVPRO-2026-002  
**Product:** LuxSense Pro — Scientific Edition  
**Compliance Standards:** ISO/IEC Guide 98-3 (GUM), CIE 157:2004, EN 12464-1:2021, DIN 5032-7  
**Author:** DevPro-CORP Scientific Instrumentation Division  
**Version:** 2.1.0  

---

## 1. Scientific Metrology Overview

LuxSense Pro Scientific Edition transforms standard photometric data acquisition into a rigorous, laboratory-grade measurement suite. Operating upon high-precision 16-bit digital lux sensors (Rohm BH1750FVI) and backed by a Python/PySide6/Qt metrology engine with a WebEngine scientific UI, LuxSense Pro adheres strictly to international photometric standards and uncertainty budgeting frameworks.

---

## 2. Scientific Measurement Capabilities (Objective B)

### 2.1 Illuminance Measurement Laboratory
* **Direct Photopic Illuminance ($E_v$):** Accurately captures ambient luminous flux per unit area ($\text{lm}/\text{m}^2$).
* **Spectral Match:** The internal sensor uses an integrated optical filter designed to approximate the CIE 1931 standard photopic observer $V(\lambda)$ luminous efficiency curve.
* **Auto-ranging Resolution:** Automatic resolution switching between $1.0\text{ lx}$ and $0.5\text{ lx}$ mode, with high-range capability extending to $121,557\text{ lx}$.

### 2.2 Dual Photometric Units (Lux & Foot-Candles)
* **Conversion Formula:**
  $$1\text{ Foot-Candle (fc)} = 1\text{ lm}/\text{ft}^2 = 10.763910416709722\text{ Lux (lx)}$$
  $$E_{fc} = \frac{E_{lx}}{10.763910416709722}$$
* **Implementation:** The user interface supports instantaneous, lossless toggle between SI metric units ($\text{lx}$) and Imperial architectural units ($\text{fc}$) without re-quantization distortion.

### 2.3 Cumulative Light Exposure & Lux-Hour Analysis (CIE 157:2004)
For museum curatorial preservation, archival document conservation, and biological phototoxicity research, light damage is cumulative. LuxSense Pro implements time-integrated exposure computation:
$$H_v = \int_{0}^{T} E_v(t) \, dt \quad [\text{lx}\cdot\text{s}]$$
$$H_{v,\text{hours}} = \frac{H_v}{3600} \quad [\text{lx}\cdot\text{h}]$$
* **Annual Projected Dose:**
  $$\text{Annual Dose} = \bar{E}_v \times 8760\text{ hours/year} \quad [\text{lx}\cdot\text{h}/\text{year}]$$
* **CIE 157:2004 Conservation Categorization:**
  - **Category I (Highly Responsive / Sensitive):** Silk, historic textiles, watercolors, color photography (Limit: $\le 50\text{ lx}$, $15,000 - 50,000\text{ lx}\cdot\text{h}/\text{yr}$).
  - **Category II (Moderately Responsive):** Oil paintings, tempera, wood, leather, undyed materials (Limit: $\le 200\text{ lx}$, $150,000 - 450,000\text{ lx}\cdot\text{h}/\text{yr}$).
  - **Category III (Low / Insensitive):** Metal, stone, glass, ceramics, unpainted minerals (Limit: $\le 1000\text{ lx}$, Unrestricted).
* **Automated Excursion Tracking:** Real-time computation of dose accumulation against preservation thresholds, warning curators immediately when annual limits are approached or exceeded.

### 2.4 Spatial Illuminance Mapping
* **Point-by-Point Field Surveying:** Enables field technicians to record physical $(X, Y)$ grid positions (in meters or feet) with corresponding surface illuminance.
* **Coordinate Tagging:** Each point captures timestamp, physical coordinates, measured lux, calibrated lux, and optional laboratory zone tags.
* **Database Persistence:** Persisted in the local SQLite engine (`spatial_points` table), surviving restarts and session switches.

### 2.5 Lighting Uniformity Calculations (EN 12464-1)
Architectural and ergonomic standards mandate lighting uniformity to prevent visual fatigue and glare. LuxSense Pro automatically calculates:
1. **Overall Uniformity ($U_1$):**
   $$U_1 = \frac{E_{\min}}{\bar{E}_v} \quad (\text{EN 12464-1 Task Requirement: } \ge 0.60 \text{ or } \ge 0.70)$$
2. **Extreme Uniformity ($U_2$):**
   $$U_2 = \frac{E_{\min}}{E_{\max}} \quad (\text{General Requirement: } \ge 0.40)$$
3. **Diversity Ratio ($D$):**
   $$D = \frac{E_{\max}}{E_{\min}}$$
* **Real-time Assessment:** The system instantly cross-references spatial grid datasets against EN 12464-1 compliance thresholds.

### 2.6 Experiment Session Management
* **Database Isolation:** All sensor readings are linked via `session_id` foreign keys within the SQLite database.
* **Session Lifecycle:** Users can create distinct experiment runs (e.g., "Darkroom Baseline", "LED Fixture A-400", "Daylight Penetration Test"), start and stop acquisition per session, and switch between historical sessions seamlessly.

### 2.7 Multi-Session Comparison & Analytics
* **Statistical Overlays:** Compare mean illuminance, standard deviation, peak lux, exposure rates, and uniformity between sessions.
* **Side-by-Side Reporting:** Generate multi-run comparison metrics for QA/QC auditing.

### 2.8 Statistical Analysis & Uncertainty Budgeting (GUM / ISO 98-3)
Measurement results are incomplete without an evaluation of uncertainty. LuxSense Pro incorporates the ISO/IEC Guide 98-3:2008 (*Guide to the Expression of Uncertainty in Measurement*):

1. **Type A Uncertainty ($u_A$):** Statistically evaluated from repeated continuous observations:
   $$u_A = \frac{s}{\sqrt{N}} = \sqrt{\frac{\sum_{i=1}^N (E_i - \bar{E})^2}{N(N-1)}}$$
2. **Type B Uncertainty ($u_B$):** Evaluated from instrument specifications and calibration certificates:
   - Sensor Accuracy Specification ($u_{B,\text{spec}}$): Assuming rectangular probability distribution:
     $$u_{B,\text{spec}} = \frac{\delta_{\text{spec}} \times \bar{E}}{\sqrt{3}}$$
   - ADC Digitization Quantization ($u_{B,\text{res}}$):
     $$u_{B,\text{res}} = \frac{\text{Resolution}}{2\sqrt{3}}$$
   - Total Type B:
     $$u_B = \sqrt{u_{B,\text{spec}}^2 + u_{B,\text{res}}^2}$$
3. **Combined Standard Uncertainty ($u_c$):**
   $$u_c = \sqrt{u_A^2 + u_B^2}$$
4. **Expanded Uncertainty ($U_{95}$):**
   $$U_{95} = k \times u_c \quad (\text{Coverage factor } k = 2.00 \text{ for } 95.45\% \text{ confidence interval})$$

* **Uncertainty Reporting:** All scientific views display $\bar{E} \pm U_{95}\text{ lx}$ alongside tabular uncertainty budgets.

### 2.9 Configurable Measurement Thresholds & Excursion Tracking
* **Custom Tolerance Windows:** Users configure minimum and maximum acceptable illuminance limits (e.g., $300\text{ lx} \le E_v \le 750\text{ lx}$ for typical office desk tasks).
* **Excursion Diagnostics:** Real-time tracking calculates percentage of time within compliance, total excursion duration, and peak exceedance values.

### 2.10 Scientific CSV and Print-Ready HTML/PDF Reports
* **Export Engines:**
  - **Scientific CSV:** ISO-formatted timestamps, calibration gain/offset parameters, raw lux, calibrated lux, foot-candles, estimated irradiance, and GUM budget summary headers.
  - **Metrology Certificate HTML/PDF:** Beautifully formatted, print-ready metrology certificate featuring DevPro-CORP headers, session statistics, complete GUM uncertainty breakdown, spatial uniformity grid, compliance indicators, and sensor scope disclosures.

---

## 3. Scientific Integrity & Data Provenance (Objective C)

LuxSense Pro strictly adheres to metrological honesty. The user interface and data pipeline enforce clear visual categorization of all surfaced data:

| Classification | Notation | Definition | Permitted Scope |
|---|---|---|---|
| **MEASURED** | `[MEASURED]` | Direct digital counts read from the physical photodiode ADC. | Raw sensor illuminance ($E_{\text{raw}}$). |
| **CALIBRATED** | `[CALIBRATED]` | Values adjusted using traceably verified calibration equations: $E = G \times (E_{\text{raw}} - \text{Offset})$. | Traceable illuminance ($E_{\text{calibrated}}$). |
| **CALCULATED** | `[CALCULATED]` | Mathematically derived values from verified physical relationships. | Foot-candles ($E_{\text{fc}}$), exposure dose ($H_v$), uniformity ($U_1, U_2, D$), GUM uncertainty ($u_c, U_{95}$). |
| **ESTIMATED** | `[ESTIMATED]` | Values derived from theoretical approximations with clear scientific caveats. | Approximate optical irradiance ($E_e \approx E_v / 683\text{ W}/\text{m}^2$ at $\lambda = 555\text{ nm}$). |

### Non-Fabrication Commitment
* **No Synthetic Spectral Distribution:** LuxSense Pro does **NOT** synthesize spectral power distribution (SPD) graphs from a single-channel broadband sensor.
* **No Fabricated CCT or CRI:** Correlated Colour Temperature ($T_{\text{cp}}$) and Colour Rendering Index ($R_a$) require at minimum 3-channel trichromatic $(X, Y, Z)$ or multi-channel spectrometer hardware. LuxSense Pro never fabricates CCT or CRI numbers.
* **No Fabricated Optical Flicker:** Flicker frequency and Percent Flicker require analog sampling rates exceeding $10\text{ kHz}$. LuxSense Pro does not synthesize flicker metrics.

---

## 4. Multi-Sensor Investigation & Hardware Roadmap (Objective D)

To expand LuxSense Pro from photopic illuminance into comprehensive optical radiometry, the following physical sensor integrations have been designed for subsequent hardware revisions:

### 4.1 Correlated Colour Temperature (CCT) & Colour Rendering Index (CRI)
* **Candidate Hardware:** **ams OSRAM AS7341** 11-Channel Spectral Color Sensor / **ams AS7262** 6-Channel Visible Spectral Sensor.
* **Interface:** I2C Fast-Mode (`0x39`).
* **Principle of Operation:** The AS7341 features 8 visible spectral channels (centered at $415, 445, 480, 515, 555, 590, 630, 680\text{ nm}$), 1 near-infrared (NIR) channel, and 1 clear channel.
* **Metrological Capability:** Computes precise CIE 1931 $(x, y)$ chromaticity coordinates, Correlated Colour Temperature (CCT via McCamy or Ohno algorithms), and Colour Rendering Index ($R_a$ / $R_1 - R_{15}$ per CIE 13.3:1995).

### 4.2 High-Speed Optical Flicker Analysis (IEEE 1789)
* **Candidate Hardware:** **Texas Instruments OPT101** Integrated Photodiode & Transimpedance Amplifier / **ams TSL2591** High-Dynamic Photodiode.
* **Interface:** High-speed ADC (e.g., ADS1115 @ 860 SPS or direct ATmega328P free-running ADC @ $9.6\text{ kHz}$).
* **Metrological Capability:**
  - Optical Flicker Index: $\text{Area}_1 / (\text{Area}_1 + \text{Area}_2)$.
  - Percent Flicker: $100\% \times (A - B) / (A + B)$.
  - Modulation Frequency Identification via Fast Fourier Transform (FFT).
  - Assessment against **IEEE 1789-2015** (Recommended Practices for Modulating Current in High-Brightness LEDs for Mitigating Health Risks).

### 4.3 Ultraviolet (UV) Exposure & Index Measurement
* **Candidate Hardware:** **Vishay VEML6075** UVA/UVB I2C Sensor / **LAPIS ML8511** Analog UV Sensor.
* **Interface:** I2C (`0x10`) or 10-bit analog channel.
* **Metrological Capability:**
  - Individual UVA ($315 - 400\text{ nm}$) and UVB ($280 - 315\text{ nm}$) irradiance in $\mu\text{W}/\text{cm}^2$.
  - WHO / WMO Standard Ultraviolet Index (UVI: $0 - 11+$).
  - Cumulative UV photobiological dose tracking for materials aging and museum preservation.

---

## 5. Verification Summary

The scientific features described in this document have been validated through 28 automated test specifications covering unit conversions, cumulative exposure integration, spatial uniformity algorithms, GUM uncertainty calculations, database session isolation, and report generation engines.
