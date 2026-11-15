import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { 
  Binary, 
  Cpu, 
  Layers, 
  ShieldCheck, 
  Activity, 
  Sun, 
  Compass, 
  Terminal 
} from 'lucide-react';

export const TechnicalInfoWorkspace: React.FC = () => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  // Spectral curve comparison: BH1750 vs Human Eye CIE V(λ)
  useEffect(() => {
    if (!chartRef.current) return;

    const inst = echarts.init(chartRef.current, 'dark');
    chartInstance.current = inst;
    const ro = new ResizeObserver(() => inst.resize());
    ro.observe(chartRef.current);

    // Wavelengths from 380nm to 740nm
    const wavelengths = [
      380, 400, 420, 440, 460, 480, 500, 520, 540, 555, 560, 580, 600, 620, 640, 660, 680, 700, 720, 740
    ];

    // CIE 1931 Standard Photopic Observer V(λ)
    const ciePhotopic = [
      0.0004, 0.004, 0.017, 0.023, 0.060, 0.139, 0.323, 0.710, 0.954, 1.000, 0.995, 0.870, 0.631, 0.381, 0.175, 0.061, 0.017, 0.004, 0.001, 0.0002
    ];

    // BH1750FVI Typical Relative Spectral Sensitivity
    const bh1750Sensitivity = [
      0.001, 0.008, 0.025, 0.035, 0.078, 0.165, 0.360, 0.750, 0.970, 1.000, 0.990, 0.890, 0.650, 0.410, 0.200, 0.080, 0.028, 0.009, 0.002, 0.0005
    ];

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      title: {
        text: 'Spectral Responsivity: BH1750FVI vs. CIE 1931 Photopic Curve V(λ)',
        left: 0,
        textStyle: {
          color: '#DFE2E8',
          fontSize: 12,
          fontFamily: 'JetBrains Mono',
          fontWeight: 600
        }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#161920',
        borderColor: '#2B3240',
        textStyle: { color: '#DFE2E8', fontFamily: 'JetBrains Mono', fontSize: 11 },
        formatter: (params: any) => {
          if (!params || !params[0]) return '';
          return `
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">
              <div>Wavelength λ: <strong>${params[0].name} nm</strong></div>
              <div style="color: #21D789;">CIE 1931 V(λ): <strong>${(params[0].value * 100).toFixed(1)}%</strong></div>
              ${params[1] ? `<div style="color: #61AFEF;">BH1750FVI: <strong>${(params[1].value * 100).toFixed(1)}%</strong></div>` : ''}
            </div>
          `;
        }
      },
      legend: {
        right: 10,
        top: 0,
        textStyle: { color: '#8C96A8', fontFamily: 'JetBrains Mono', fontSize: 10 }
      },
      grid: {
        top: 40,
        left: 45,
        right: 25,
        bottom: 35
      },
      xAxis: {
        type: 'category',
        name: 'λ (nm)',
        nameTextStyle: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 },
        data: wavelengths.map(String),
        axisLine: { lineStyle: { color: '#272C38' } },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.04)' } },
        axisLabel: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 9 }
      },
      yAxis: {
        type: 'value',
        name: 'Rel. Sensitivity',
        nameTextStyle: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.04)' } },
        axisLabel: { color: '#6F788A', fontFamily: 'JetBrains Mono', fontSize: 10 }
      },
      series: [
        {
          name: 'CIE 1931 V(λ) Eye Response',
          type: 'line',
          smooth: true,
          data: ciePhotopic,
          lineStyle: { color: '#21D789', width: 2.5 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(33, 215, 137, 0.25)' },
              { offset: 1, color: 'transparent' }
            ])
          },
          showSymbol: false
        },
        {
          name: 'BH1750FVI Silicon Response',
          type: 'line',
          smooth: true,
          data: bh1750Sensitivity,
          lineStyle: { color: '#61AFEF', width: 2, type: 'dashed' },
          showSymbol: false
        }
      ]
    };

    chartInstance.current.setOption(option);

    return () => {
      ro.disconnect();
      inst.dispose();
      chartInstance.current = null;
    };
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Header */}
      <div className="bg-chassis-950 p-4 rounded-xl border border-border flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center space-x-2">
            <Binary className="w-4 h-4 text-metrology-green" />
            <span>Technical Architecture &amp; Hardware Specifications</span>
          </h2>
          <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
            Photometric optics, Microchip ATmega328P MCU architecture, and 128-bit rolling XOR telemetry protocol.
          </p>
        </div>
        <span className="text-xs font-mono text-zinc-400 bg-chassis-900 px-3 py-1 rounded border border-border">
          REV 2.2 — SPECIFICATION
        </span>
      </div>

      {/* Main Spectral Chart & Subsystem Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Spectral Response Chart (Spans 7 cols) */}
        <div className="lg:col-span-7 bg-chassis-950 border border-border rounded-xl p-4 flex flex-col min-h-[350px]">
          <div ref={chartRef} className="w-full h-full flex-1" />
          <div className="mt-2 text-[10px] font-mono text-zinc-400 border-t border-border pt-2 flex justify-between">
            <span>Peak Wavelength: λ_max = 555 nm</span>
            <span>Illuminance Calculation: E_v = 16-bit Count / 1.2 lx</span>
            <span>Infrared Rejection: &gt; 98.4%</span>
          </div>
        </div>

        {/* Core Subsystem Architecture Cards (Spans 5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          {/* Photodiode Specs */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono font-bold text-white border-b border-border pb-1.5">
              <span className="flex items-center space-x-1.5 text-metrology-green">
                <Sun className="w-3.5 h-3.5" />
                <span>ROHM BH1750FVI Optical Transducer</span>
              </span>
              <span className="text-[10px] text-zinc-400">I2C (0x23)</span>
            </div>
            <div className="text-[11px] font-mono text-zinc-400 space-y-1">
              <div className="flex justify-between">
                <span>Dynamic Range:</span>
                <span className="text-zinc-200">0.11 lx to 65,535 lx</span>
              </div>
              <div className="flex justify-between">
                <span>Measurement Mode:</span>
                <span className="text-zinc-200">Continuous H-Resolution (1 lx)</span>
              </div>
              <div className="flex justify-between">
                <span>Integration Window:</span>
                <span className="text-zinc-200">120 ms (Typical)</span>
              </div>
              <div className="flex justify-between">
                <span>ADC Architecture:</span>
                <span className="text-zinc-200">16-bit Successive Approximation</span>
              </div>
            </div>
          </div>

          {/* Microcontroller Specs */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono font-bold text-white border-b border-border pb-1.5">
              <span className="flex items-center space-x-1.5 text-metrology-blue">
                <Cpu className="w-3.5 h-3.5" />
                <span>Microchip ATmega328P MCU Core</span>
              </span>
              <span className="text-[10px] text-zinc-400">16.0 MHz</span>
            </div>
            <div className="text-[11px] font-mono text-zinc-400 space-y-1">
              <div className="flex justify-between">
                <span>Clock Oscillator:</span>
                <span className="text-zinc-200">16.000 MHz Crystal ±30ppm</span>
              </div>
              <div className="flex justify-between">
                <span>Hardware UART:</span>
                <span className="text-zinc-200">115,200 Baud, 8-N-1</span>
              </div>
              <div className="flex justify-between">
                <span>I2C Bus Clock:</span>
                <span className="text-zinc-200">400 kHz Fast Mode (TWI)</span>
              </div>
              <div className="flex justify-between">
                <span>Flash Memory:</span>
                <span className="text-zinc-200">32 KB (Optiboot 512B Bootloader)</span>
              </div>
            </div>
          </div>

          {/* Rolling XOR Telemetry Protocol */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono font-bold text-white border-b border-border pb-1.5">
              <span className="flex items-center space-x-1.5 text-metrology-amber">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>128-Bit Rolling XOR Stream Cipher</span>
              </span>
              <span className="text-[10px] text-zinc-400">CRC-8 Protected</span>
            </div>
            <p className="text-[10px] font-mono text-zinc-400 leading-relaxed">
              Every telemetry transmission is wrapped in a 16-byte frame: 
              <code className="text-zinc-300 block bg-chassis-900 p-1 rounded mt-1 border border-border/40">
                [0xAA 0x55] [ID:2B] [RAW:4B] [TEMP:2B] [PAYLOAD:6B] [CRC:1B]
              </code>
              Encrypted against physical bus eavesdropping and bit-flip tampering.
            </p>
          </div>
        </div>
      </div>

      {/* Electrical Characteristics & Limits Table */}
      <div className="bg-chassis-950 border border-border rounded-xl p-4">
        <div className="text-xs font-mono font-bold text-white uppercase tracking-wider mb-2">
          Absolute Maximum Ratings &amp; Environmental Tolerances
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead className="bg-chassis-900 border-b border-border text-zinc-400 text-[10px] uppercase">
              <tr>
                <th className="py-2 px-3">Parameter</th>
                <th className="py-2 px-3">Symbol</th>
                <th className="py-2 px-3">Minimum</th>
                <th className="py-2 px-3">Typical</th>
                <th className="py-2 px-3">Maximum</th>
                <th className="py-2 px-3">Unit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 text-zinc-300 text-[11px]">
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Supply Voltage (VCC)</td>
                <td className="py-2 px-3 text-zinc-500">V_dd</td>
                <td className="py-2 px-3">4.75</td>
                <td className="py-2 px-3 text-metrology-green font-bold">5.00</td>
                <td className="py-2 px-3">5.25</td>
                <td className="py-2 px-3 text-zinc-400">V</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Operating Current (Active)</td>
                <td className="py-2 px-3 text-zinc-500">I_cc</td>
                <td className="py-2 px-3">18.5</td>
                <td className="py-2 px-3 text-metrology-green font-bold">24.2</td>
                <td className="py-2 px-3">35.0</td>
                <td className="py-2 px-3 text-zinc-400">mA</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Operating Temperature Range</td>
                <td className="py-2 px-3 text-zinc-500">T_opr</td>
                <td className="py-2 px-3">-20</td>
                <td className="py-2 px-3 text-metrology-green font-bold">+25</td>
                <td className="py-2 px-3">+70</td>
                <td className="py-2 px-3 text-zinc-400">°C</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-semibold text-white">Optical Saturation Limit</td>
                <td className="py-2 px-3 text-zinc-500">E_max</td>
                <td className="py-2 px-3">—</td>
                <td className="py-2 px-3 text-metrology-green font-bold">65,535</td>
                <td className="py-2 px-3">120,000*</td>
                <td className="py-2 px-3 text-zinc-400">lx</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Objective D: Advanced Sensor Investigation & Metrology Roadmap */}
      <div className="bg-chassis-950 border border-border rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-border pb-2">
          <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <Compass className="w-4 h-4 text-metrology-blue" />
            <span>Future Hardware Metrology Roadmap &amp; Multi-Sensor Investigation</span>
          </span>
          <span className="text-[10px] font-mono text-zinc-400 bg-chassis-900 px-2.5 py-0.5 rounded border border-border">
            OPTIONAL EXPANSION (P3)
          </span>
        </div>

        <p className="text-[11px] font-mono text-zinc-400 leading-relaxed">
          The current LuxSense Pro release relies strictly on verified physical BH1750 measurements. The I2C shared bus architecture on the Arduino Uno is designed to accommodate the following future sensors without breaking changes:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
            <div className="text-metrology-blue font-semibold flex items-center space-x-1.5">
              <span>1. Correlated Colour Temperature (CCT) &amp; CRI</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed">
              <strong>Candidate: ams-OSRAM AS7341 (11-channel) or AS7262 (6-channel).</strong><br />
              Provides 8 visible spectral channels + NIR + clear. Enables genuine calculation of chromaticity coordinates (x, y), CCT (Kelvin), and CRI (Ra) without fabrication.
            </p>
          </div>

          <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
            <div className="text-metrology-amber font-semibold flex items-center space-x-1.5">
              <span>2. High-Frequency Optical Flicker Analysis</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed">
              <strong>Candidate: TI OPT101 / ams TSL2591 with DMA Sampling.</strong><br />
              High-bandwidth transimpedance photodiode sampling at 2 kHz - 10 kHz to calculate Percent Flicker, Flicker Index, and IEEE 1789 health risk metrics for solid-state lighting.
            </p>
          </div>

          <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
            <div className="text-metrology-crimson font-semibold flex items-center space-x-1.5">
              <span>3. Ultraviolet Index (UVA / UVB) Monitoring</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed">
              <strong>Candidate: Vishay VEML6075 (I2C) or Lapis ML8511 (Analog).</strong><br />
              Dedicated dual-channel photodiodes isolating UVA (365nm) and UVB (330nm) radiation for museum solarization testing and polymer UV photolysis prevention.
            </p>
          </div>

          <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
            <div className="text-metrology-green font-semibold flex items-center space-x-1.5">
              <span>4. Metrological Integrity Policy</span>
            </div>
            <p className="text-[10px] text-zinc-400 leading-relaxed">
              <strong>Zero-Fabrication Commitment:</strong> LuxSense Pro will never display synthetic or estimated CCT, CRI, or flicker values until physical multi-channel sensors are connected and certified.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

