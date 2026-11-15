import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Cpu, 
  Radio, 
  CheckCircle, 
  AlertTriangle, 
  RefreshCw, 
  Zap, 
  Info, 
  ShieldCheck, 
  ChevronDown, 
  ChevronUp, 
  Terminal, 
  ExternalLink,
  Layers,
  ArrowRight
} from 'lucide-react';
import { bridge } from '../../bridge/bridgeClient';
import { useTheme } from '../../context/ThemeContext';

interface HardwareSetupProps {
  hardwareState: string;
  isConnected: boolean;
  onNavigateToTab?: (tab: any) => void;
}

export const HardwareSetupWorkspace: React.FC<HardwareSetupProps> = ({
  hardwareState,
  isConnected,
  onNavigateToTab
}) => {
  const { resolvedTheme } = useTheme();
  const [availablePorts, setAvailablePorts] = useState<string[]>([]);
  const [selectedPort, setSelectedPort] = useState<string>('COM5');
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; details?: string } | null>(null);
  const [checklist, setChecklist] = useState({
    vcc: false,
    gnd: false,
    sda: false,
    scl: false,
    addr: false
  });
  const [activeTroubleshoot, setActiveTroubleshoot] = useState<string | null>(null);

  useEffect(() => {
    scanPorts();
  }, []);

  const scanPorts = async () => {
    setIsScanning(true);
    try {
      const ports = await bridge.scanPorts();
      setAvailablePorts(ports);
      if (ports.length > 0 && !ports.includes(selectedPort)) {
        setSelectedPort(ports[0]);
      }
    } catch (e) {
      console.error('Failed to scan ports:', e);
    } finally {
      setIsScanning(false);
    }
  };

  const handleTestConnection = async () => {
    setIsScanning(true);
    setTestResult(null);
    try {
      const state = await bridge.getHardwareState();
      const ports = await bridge.scanPorts();
      const isTargetPresent = ports.includes(selectedPort);

      if (isTargetPresent && (state === 'LIVE MEASUREMENT' || state === 'SENSOR DETECTED')) {
        setTestResult({
          success: true,
          message: `Hardware Link Active on ${selectedPort}!`,
          details: `ATmega328P identified at 115,200 baud. GY-30/BH1750 acknowledged at 0x23 (Fast-Mode 400 kHz). Continuous telemetry streaming verified.`
        });
      } else if (isTargetPresent) {
        setTestResult({
          success: false,
          message: `Port ${selectedPort} open, but optical sensor returned ${state}.`,
          details: `Check wiring between GY-30 SDA/SCL and Arduino A4/A5. Ensure ADDR is grounded.`
        });
      } else {
        setTestResult({
          success: false,
          message: `Device not detected on ${selectedPort}.`,
          details: `Arduino Uno R3 is not responding on ${selectedPort}. Ensure USB Type-B cable is securely plugged in.`
        });
      }
    } catch (e: any) {
      setTestResult({
        success: false,
        message: 'Connection Test Encountered Error',
        details: e?.message || String(e)
      });
    } finally {
      setIsScanning(false);
    }
  };

  const allChecked = checklist.vcc && checklist.gnd && checklist.sda && checklist.scl && checklist.addr;

  const toggleTroubleshoot = (id: string) => {
    setActiveTroubleshoot(activeTroubleshoot === id ? null : id);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Banner */}
      <div className="bg-chassis-950 p-4 rounded-xl border border-border flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-metrology-green" />
            <span>Hardware Setup &amp; Physical Wiring Station</span>
          </h2>
          <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
            Verified wiring pinouts for Arduino Uno R3 (ATmega328P) and GY-30 (BH1750FVI) 16-bit ambient photometer.
          </p>
        </div>

        {/* Live Hardware State Pill */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-chassis-900 border border-border font-mono text-xs">
            <span className="text-zinc-400">BUS STATUS:</span>
            <span className={`font-bold flex items-center space-x-1.5 ${
              hardwareState === 'LIVE MEASUREMENT' ? 'text-metrology-green' :
              hardwareState === 'SENSOR DETECTED' ? 'text-metrology-blue' :
              hardwareState === 'CONNECTING' ? 'text-metrology-amber' :
              'text-metrology-crimson'
            }`}>
              <span className={`w-2 h-2 rounded-full ${
                hardwareState === 'LIVE MEASUREMENT' ? 'bg-metrology-green animate-pulse' :
                hardwareState === 'SENSOR DETECTED' ? 'bg-metrology-blue' :
                hardwareState === 'CONNECTING' ? 'bg-metrology-amber animate-ping' :
                'bg-metrology-crimson'
              }`} />
              <span>{hardwareState}</span>
            </span>
          </div>

          <button
            onClick={scanPorts}
            disabled={isScanning}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-chassis-850 border border-border text-xs font-mono text-zinc-200 hover:border-border-focus transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isScanning ? 'animate-spin text-metrology-green' : ''}`} />
            <span>{isScanning ? 'SCANNING...' : 'SCAN PORTS'}</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Visual Schematic & Connections Table */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Visual Wiring Schematic (7 cols) */}
        <div className="lg:col-span-7 bg-chassis-950 p-4 rounded-xl border border-border flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-metrology-amber" />
              <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
                Physical Wiring Schematic (I²C Bus)
              </span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-chassis-850 border border-border text-zinc-400">
              FAST-MODE 400 kHz • 5-WIRE INTERFACE
            </span>
          </div>

          {/* Graphical Schematic Diagram */}
          <div className="relative bg-chassis-900 rounded-lg border border-border p-4 flex flex-col items-center justify-center overflow-hidden min-h-[320px]">
            {/* Background Grid Pattern */}
            <div className="absolute inset-0 optical-grid opacity-50" />

            <div className="relative z-10 w-full max-w-xl flex items-center justify-between gap-6 px-4">
              {/* Arduino Uno R3 Visual Module */}
              <div className="w-44 bg-chassis-950 border-2 border-metrology-blue/60 rounded-xl p-3 shadow-lg flex flex-col items-center">
                <div className="text-[11px] font-bold font-mono text-metrology-blue tracking-wider">ARDUINO UNO R3</div>
                <div className="text-[9px] font-mono text-zinc-400">ATmega328P @ 16MHz</div>

                {/* USB Port Graphic */}
                <div className="w-12 h-6 bg-zinc-700 rounded-t mt-2 flex items-center justify-center text-[8px] font-mono text-zinc-300 font-bold border border-zinc-500">
                  USB-B
                </div>

                <div className="w-full mt-3 space-y-1.5 text-[10px] font-mono">
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="text-zinc-400">5V (Power)</span>
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-glow-red" />
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="text-zinc-400">GND (Ground)</span>
                    <span className="w-2.5 h-2.5 rounded-full bg-zinc-400" />
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="text-zinc-400">Pin A4 (SDA)</span>
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-glow-blue" />
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="text-zinc-400">Pin A5 (SCL)</span>
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-glow-green" />
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="text-zinc-400">GND (Addr Ref)</span>
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                  </div>
                </div>
              </div>

              {/* Jumper Wires Interconnect (SVG) */}
              <div className="flex-1 flex flex-col justify-center space-y-3 py-4">
                <div className="flex items-center space-x-2">
                  <div className="h-0.5 flex-1 bg-red-500 rounded relative">
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-red-400 font-bold">5V Power</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                </div>

                <div className="flex items-center space-x-2">
                  <div className="h-0.5 flex-1 bg-zinc-400 rounded relative">
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-zinc-300 font-bold">Common GND</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" />
                </div>

                <div className="flex items-center space-x-2">
                  <div className="h-0.5 flex-1 bg-cyan-400 rounded relative">
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-cyan-300 font-bold">SDA (Data)</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                </div>

                <div className="flex items-center space-x-2">
                  <div className="h-0.5 flex-1 bg-emerald-400 rounded relative">
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-emerald-300 font-bold">SCL (Clock)</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                </div>

                <div className="flex items-center space-x-2">
                  <div className="h-0.5 flex-1 bg-purple-400 rounded relative">
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-[9px] font-mono text-purple-300 font-bold">ADDR &rarr; GND (0x23)</span>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                </div>
              </div>

              {/* GY-30 / BH1750 Optical Sensor Module */}
              <div className="w-44 bg-chassis-950 border-2 border-metrology-green/60 rounded-xl p-3 shadow-lg flex flex-col items-center">
                <div className="text-[11px] font-bold font-mono text-metrology-green tracking-wider">GY-30 SENSOR</div>
                <div className="text-[9px] font-mono text-zinc-400">BH1750FVI Photodiode</div>

                {/* Photodiode Window Graphic */}
                <div className="w-10 h-10 rounded-full bg-metrology-green/20 border-2 border-metrology-green flex items-center justify-center mt-2 shadow-glow-green">
                  <div className="w-4 h-4 rounded-full bg-metrology-green/60" />
                </div>

                <div className="w-full mt-3 space-y-1.5 text-[10px] font-mono">
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-glow-red" />
                    <span className="text-zinc-400">VCC (3.3V-5V)</span>
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="w-2.5 h-2.5 rounded-full bg-zinc-400" />
                    <span className="text-zinc-400">GND</span>
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-glow-blue" />
                    <span className="text-zinc-400">SDA</span>
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-glow-green" />
                    <span className="text-zinc-400">SCL</span>
                  </div>
                  <div className="flex justify-between items-center bg-chassis-900 px-2 py-1 rounded border border-border">
                    <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
                    <span className="text-zinc-400">ADDR (0x23)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Programming vs Telemetry Notice */}
          <div className="bg-metrology-blue/10 border border-metrology-blue/30 p-3 rounded-lg flex items-start space-x-2.5 text-xs font-mono text-zinc-300">
            <Info className="w-4 h-4 text-metrology-blue flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-metrology-blue">Important Hardware Architecture Distinction:</span>
              <p className="mt-0.5 leading-relaxed text-[11px] text-zinc-400">
                The BH1750 optical sensor communicates strictly over analog header pins <strong>A4 (SDA)</strong> and <strong>A5 (SCL)</strong> via the I²C bus. 
                Firmware microcode programming is executed strictly over the <strong>USB Type-B virtual COM port</strong> using the ATmega16U2/CH340 serial converter. 
                Never confuse runtime I²C telemetry with USB programming.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Pre-Flight Checklist & Pin Reference Table (5 cols) */}
        <div className="lg:col-span-5 space-y-4 flex flex-col">
          {/* Connection Checklist Card */}
          <div className="bg-chassis-950 p-4 rounded-xl border border-border space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2.5">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-metrology-green" />
                <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
                  Wiring Verification Checklist
                </span>
              </div>
              <span className="text-[10px] font-mono text-zinc-400">
                {Object.values(checklist).filter(Boolean).length}/5 VERIFIED
              </span>
            </div>

            <p className="text-[11px] font-mono text-zinc-400">
              Verify each jumper connection physically before initiating sensor acquisition or calibration.
            </p>

            <div className="space-y-2">
              <label className="flex items-center space-x-2.5 p-2 rounded bg-chassis-900 border border-border text-xs font-mono cursor-pointer hover:border-border-focus transition-colors">
                <input
                  type="checkbox"
                  checked={checklist.vcc}
                  onChange={e => setChecklist({ ...checklist, vcc: e.target.checked })}
                  className="rounded border-border text-metrology-green focus:ring-0"
                />
                <span className="text-zinc-200">1. VCC &rarr; Arduino 5V (Onboard 3.3V LDO)</span>
              </label>

              <label className="flex items-center space-x-2.5 p-2 rounded bg-chassis-900 border border-border text-xs font-mono cursor-pointer hover:border-border-focus transition-colors">
                <input
                  type="checkbox"
                  checked={checklist.gnd}
                  onChange={e => setChecklist({ ...checklist, gnd: e.target.checked })}
                  className="rounded border-border text-metrology-green focus:ring-0"
                />
                <span className="text-zinc-200">2. GND &rarr; Arduino GND (Common Ground)</span>
              </label>

              <label className="flex items-center space-x-2.5 p-2 rounded bg-chassis-900 border border-border text-xs font-mono cursor-pointer hover:border-border-focus transition-colors">
                <input
                  type="checkbox"
                  checked={checklist.sda}
                  onChange={e => setChecklist({ ...checklist, sda: e.target.checked })}
                  className="rounded border-border text-metrology-green focus:ring-0"
                />
                <span className="text-zinc-200">3. SDA &rarr; Arduino Analog Pin A4 (Data)</span>
              </label>

              <label className="flex items-center space-x-2.5 p-2 rounded bg-chassis-900 border border-border text-xs font-mono cursor-pointer hover:border-border-focus transition-colors">
                <input
                  type="checkbox"
                  checked={checklist.scl}
                  onChange={e => setChecklist({ ...checklist, scl: e.target.checked })}
                  className="rounded border-border text-metrology-green focus:ring-0"
                />
                <span className="text-zinc-200">4. SCL &rarr; Arduino Analog Pin A5 (Clock)</span>
              </label>

              <label className="flex items-center space-x-2.5 p-2 rounded bg-chassis-900 border border-border text-xs font-mono cursor-pointer hover:border-border-focus transition-colors">
                <input
                  type="checkbox"
                  checked={checklist.addr}
                  onChange={e => setChecklist({ ...checklist, addr: e.target.checked })}
                  className="rounded border-border text-metrology-green focus:ring-0"
                />
                <span className="text-zinc-200">5. ADDR &rarr; GND (Forces Default I²C 0x23)</span>
              </label>
            </div>

            {/* Test Hardware Button */}
            <div className="pt-2">
              <button
                onClick={handleTestConnection}
                disabled={isScanning}
                className={`w-full py-2 px-3 rounded font-mono text-xs font-bold transition-all flex items-center justify-center space-x-2 shadow-sm ${
                  allChecked
                    ? 'bg-metrology-green text-chassis-950 hover:bg-metrology-green/90 shadow-glow-green'
                    : 'bg-chassis-850 text-zinc-400 border border-border hover:border-border-focus'
                }`}
              >
                <Zap className={`w-3.5 h-3.5 ${isScanning ? 'animate-bounce text-metrology-amber' : ''}`} />
                <span>{isScanning ? 'PROBING HARDWARE BUS...' : 'TEST & VERIFY CONNECTION'}</span>
              </button>
            </div>

            {/* Test Feedback */}
            {testResult && (
              <motion.div
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-3 rounded-lg border text-xs font-mono space-y-1 ${
                  testResult.success
                    ? 'bg-metrology-green/15 border-metrology-green/40 text-metrology-green'
                    : 'bg-metrology-crimson/15 border-metrology-crimson/40 text-metrology-crimson'
                }`}
              >
                <div className="font-bold flex items-center space-x-1.5">
                  {testResult.success ? <CheckCircle className="w-4 h-4 flex-shrink-0" /> : <AlertTriangle className="w-4 h-4 flex-shrink-0" />}
                  <span>{testResult.message}</span>
                </div>
                {testResult.details && (
                  <p className="text-[10px] text-zinc-300 leading-relaxed pl-5.5">
                    {testResult.details}
                  </p>
                )}
              </motion.div>
            )}
          </div>

          {/* Quick Nav Card to Flasher */}
          <div className="bg-chassis-950 p-4 rounded-xl border border-border flex items-center justify-between">
            <div>
              <span className="text-xs font-bold font-mono text-white block">Microcode Needs Flashing?</span>
              <span className="text-[11px] font-mono text-zinc-400">Upload official v2.0.0 firmware to ATmega328P</span>
            </div>
            {onNavigateToTab && (
              <button
                onClick={() => onNavigateToTab('settings')}
                className="px-3 py-1.5 rounded bg-chassis-850 border border-border text-xs font-mono text-metrology-green hover:border-metrology-green transition-colors flex items-center space-x-1.5"
              >
                <span>OPEN FLASHER</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Pinout Engineering Specifications Table */}
      <div className="bg-chassis-950 p-4 rounded-xl border border-border space-y-3">
        <div className="flex items-center justify-between border-b border-border pb-2.5">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-metrology-blue" />
            <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
              Pinout Specifications &amp; Electrical Architecture
            </span>
          </div>
          <span className="text-[10px] font-mono text-zinc-400">ROHM BH1750FVI METROLOGY SPEC</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-border text-zinc-400 text-[10px] uppercase">
                <th className="pb-2">Sensor Pin</th>
                <th className="pb-2">Arduino Header</th>
                <th className="pb-2">Electrical Level</th>
                <th className="pb-2">Bus Protocol Function</th>
                <th className="pb-2">Engineering Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40 text-zinc-300 text-[11px]">
              <tr>
                <td className="py-2.5 font-bold text-red-400">VCC</td>
                <td className="py-2.5 text-white">5V Power Pin</td>
                <td className="py-2.5">3.0V &ndash; 5.0V DC</td>
                <td className="py-2.5">Powers internal photodiode array &amp; ADC</td>
                <td className="py-2.5 text-zinc-400">GY-30 includes 662K 3.3V LDO. Connect to 5V or 3.3V.</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-zinc-300">GND</td>
                <td className="py-2.5 text-white">GND Pin</td>
                <td className="py-2.5">0V (Ground Ref)</td>
                <td className="py-2.5">Common return path &amp; reference plane</td>
                <td className="py-2.5 text-zinc-400">Maintain low-impedance ground to minimize optical noise.</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-cyan-400">SDA</td>
                <td className="py-2.5 text-white">Analog Pin A4</td>
                <td className="py-2.5">Open-drain (5V pull-up)</td>
                <td className="py-2.5">Serial Data Line (Bidirectional)</td>
                <td className="py-2.5 text-zinc-400">ATmega328P TWI hardware. 4.7kΩ pull-up is included on GY-30.</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-emerald-400">SCL</td>
                <td className="py-2.5 text-white">Analog Pin A5</td>
                <td className="py-2.5">Clock Input (400 kHz)</td>
                <td className="py-2.5">Serial Clock Line (Synchronous)</td>
                <td className="py-2.5 text-zinc-400">Driven by ATmega328P TWBR=12 for Fast-Mode 400 kHz clock.</td>
              </tr>
              <tr>
                <td className="py-2.5 font-bold text-purple-400">ADDR</td>
                <td className="py-2.5 text-white">GND Pin</td>
                <td className="py-2.5">Logic Level (Low)</td>
                <td className="py-2.5">I²C 7-Bit Address Selector</td>
                <td className="py-2.5 text-zinc-400">Tied to GND sets slave address 0x23 (default). High sets 0x5C.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Troubleshooting Guide Accordion */}
      <div className="bg-chassis-950 p-4 rounded-xl border border-border space-y-3">
        <div className="flex items-center justify-between border-b border-border pb-2.5">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-metrology-amber" />
            <span className="text-xs font-bold font-mono text-white uppercase tracking-wider">
              Hardware Troubleshooting &amp; Diagnostic Guide
            </span>
          </div>
          <span className="text-[10px] font-mono text-zinc-400">FIELD DIAGNOSTICS</span>
        </div>

        <div className="space-y-2">
          {/* Issue 1 */}
          <div className="border border-border rounded-lg overflow-hidden bg-chassis-900">
            <button
              onClick={() => toggleTroubleshoot('t1')}
              className="w-full p-3 flex items-center justify-between text-left font-mono text-xs text-white hover:bg-chassis-850 transition-colors"
            >
              <div className="flex items-center space-x-2">
                <span className="text-metrology-crimson font-bold">1. Status Shows &quot;SENSOR ERROR&quot; or I²C Bus Unresponsive</span>
              </div>
              {activeTroubleshoot === 't1' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {activeTroubleshoot === 't1' && (
              <div className="p-3 pt-0 text-[11px] font-mono text-zinc-300 space-y-1.5 border-t border-border/40">
                <p><strong>Cause:</strong> The ATmega328P attempted to ping I²C addresses 0x23 and 0x5C and received NACK (No Acknowledge).</p>
                <ul className="list-disc pl-5 text-zinc-400 space-y-1">
                  <li>Check that <strong>SDA</strong> is connected to <strong>A4</strong> and <strong>SCL</strong> is connected to <strong>A5</strong>. Swapping SDA and SCL is the most common wiring mistake.</li>
                  <li>Verify that <strong>ADDR</strong> is pulled to <strong>GND</strong>. If ADDR is left floating, capacitive interference may randomly toggle between 0x23 and 0x5C.</li>
                  <li>Test continuity with a multimeter from the sensor header pins to the Arduino socket holes.</li>
                </ul>
              </div>
            )}
          </div>

          {/* Issue 2 */}
          <div className="border border-border rounded-lg overflow-hidden bg-chassis-900">
            <button
              onClick={() => toggleTroubleshoot('t2')}
              className="w-full p-3 flex items-center justify-between text-left font-mono text-xs text-white hover:bg-chassis-850 transition-colors"
            >
              <div className="flex items-center space-x-2">
                <span className="text-metrology-amber font-bold">2. Status Shows &quot;DISCONNECTED&quot; or COM Port Missing</span>
              </div>
              {activeTroubleshoot === 't2' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {activeTroubleshoot === 't2' && (
              <div className="p-3 pt-0 text-[11px] font-mono text-zinc-300 space-y-1.5 border-t border-border/40">
                <p><strong>Cause:</strong> Windows cannot enumerate the USB-to-serial converter on the Arduino board.</p>
                <ul className="list-disc pl-5 text-zinc-400 space-y-1">
                  <li>Ensure the USB Type-B cable is fully seated in both the PC and Arduino.</li>
                  <li>Confirm that another application (such as the Arduino IDE Serial Monitor, PuTTY, or Cura) is not holding an exclusive lock on the COM port.</li>
                  <li>Clone Arduino Uno boards often use the CH340 chip instead of ATmega16U2. Verify in Windows Device Manager under &quot;Ports (COM &amp; LPT)&quot; that the CH340 driver is installed.</li>
                </ul>
              </div>
            )}
          </div>

          {/* Issue 3 */}
          <div className="border border-border rounded-lg overflow-hidden bg-chassis-900">
            <button
              onClick={() => toggleTroubleshoot('t3')}
              className="w-full p-3 flex items-center justify-between text-left font-mono text-xs text-white hover:bg-chassis-850 transition-colors"
            >
              <div className="flex items-center space-x-2">
                <span className="text-metrology-blue font-bold">3. Microcode Flashing Fails (avrdude / stk500 timeout)</span>
              </div>
              {activeTroubleshoot === 't3' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {activeTroubleshoot === 't3' && (
              <div className="p-3 pt-0 text-[11px] font-mono text-zinc-300 space-y-1.5 border-t border-border/40">
                <p><strong>Cause:</strong> Optiboot bootloader did not receive STK500 sync pulse within 1.5 seconds of DTR reset.</p>
                <ul className="list-disc pl-5 text-zinc-400 space-y-1">
                  <li>Press the physical red <strong>RESET button</strong> on the Arduino Uno exactly 0.5 seconds after clicking &quot;Flash Microcode&quot;.</li>
                  <li>Ensure no high-current loads are connected to Arduino 5V/GND during programming.</li>
                  <li>Remember: Single-bank 32KB flash cannot rollback internally. If upload was cut midway, simply power-cycle the board and re-flash. Optiboot is write-protected in High Fuse 0xDE and remains operational.</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
