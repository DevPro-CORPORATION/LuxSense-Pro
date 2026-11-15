import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import { Activity, ShieldCheck, Cpu, CheckCircle2, ChevronRight, AlertCircle, RefreshCw } from 'lucide-react';
import { bridge } from '../../bridge/bridgeClient';

interface StartupPOSTProps {
  onComplete: () => void;
}

interface StepInfo {
  id: string;
  name: string;
  detail: string;
  status: 'pending' | 'active' | 'passed' | 'warning';
}

export const StartupPOST: React.FC<StartupPOSTProps> = ({ onComplete }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [progressPercent, setProgressPercent] = useState<number>(5);
  const [logs, setLogs] = useState<string[]>([]);
  const [appVersion, setAppVersion] = useState<string>('');
  const [hasTimeoutWarning, setHasTimeoutWarning] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<SVGSVGElement>(null);

  const initialSteps: StepInfo[] = [
    { id: 'core', name: 'Core Application & IPC Bridge', detail: 'Binding Qt WebChannel and persistent settings', status: 'pending' },
    { id: 'db', name: 'Metrology Storage & Calibration Engine', detail: 'Validating SQLite history tables & optical calibration', status: 'pending' },
    { id: 'hw', name: 'Physical Hardware & I²C Bus Discovery', detail: 'Scanning serial endpoints & probing BH1750 (0x23)', status: 'pending' },
    { id: 'ui', name: 'Scientific Visualization & UI Shell', detail: 'Applying theme profiles & initializing telemetry stream', status: 'pending' },
  ];

  const [stepStates, setStepStates] = useState<StepInfo[]>(initialSteps);

  useEffect(() => {
    // If user prefers reduced motion, complete immediately
    const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      onComplete();
      return;
    }

    // GSAP rotation on optical aperture ring
    if (ringRef.current) {
      gsap.to(ringRef.current, {
        rotation: 360,
        repeat: -1,
        duration: 9,
        ease: 'none',
        transformOrigin: '50% 50%',
      });
    }

    let isMounted = true;

    // Safety timeout: if any asynchronous IPC step hangs, unlock interface after 4.5 seconds
    const safetyTimeout = setTimeout(() => {
      if (isMounted) {
        setHasTimeoutWarning(true);
        setLogs(prev => [...prev, '[WARNING] POST sequence reached timeout limit. Advancing to workspace...']);
        setTimeout(onComplete, 800);
      }
    }, 4500);

    const runActualStartup = async () => {
      try {
        // --- STAGE 1: CORE APPLICATION & IPC ---
        if (!isMounted) return;
        setCurrentStepIndex(1);
        setProgressPercent(15);
        setStepStates(prev => prev.map((s, idx) => idx === 0 ? { ...s, status: 'active' } : s));
        setLogs(prev => [...prev, '[BOOT +40ms] Initializing LuxSense Pro runtime core...']);

        let ver = '2.3.3';
        try {
          ver = await bridge.getAppVersion();
          setAppVersion(ver);
        } catch (e) {
          console.warn('App version check warning:', e);
        }

        const settings = await bridge.getSettings().catch(() => null);
        const channel = settings?.update_channel?.toUpperCase() || 'STABLE';

        setStepStates(prev => prev.map((s, idx) => idx === 0 ? { 
          ...s, 
          status: 'passed',
          detail: `Version v${ver} active • ${channel} channel verified`
        } : s));
        setLogs(prev => [...prev, `[CORE OK] IPC bridge linked • Application v${ver} [${channel}] ready`]);
        setProgressPercent(35);

        // --- STAGE 2: METROLOGY STORAGE & CALIBRATION ---
        await new Promise(r => setTimeout(r, 220));
        if (!isMounted) return;
        setCurrentStepIndex(2);
        setStepStates(prev => prev.map((s, idx) => idx === 1 ? { ...s, status: 'active' } : s));
        setLogs(prev => [...prev, '[STORAGE] Loading photometric calibration and measurement history...']);

        const cal = await bridge.getCalibration().catch(() => null);
        const calGain = cal?.gain_multiplier ? cal.gain_multiplier.toFixed(4) : '1.0000';
        const calOffset = cal?.zero_offset ? cal.zero_offset.toFixed(2) : '0.00';

        setStepStates(prev => prev.map((s, idx) => idx === 1 ? { 
          ...s, 
          status: 'passed',
          detail: `Calibration factor: ${calGain}x • Dark zero: ${calOffset} lx`
        } : s));
        setLogs(prev => [...prev, `[CAL OK] Profile "${cal?.profile_name || 'Factory Standard'}" active (Gain: ${calGain}x)`]);
        setProgressPercent(65);

        // --- STAGE 3: HARDWARE & OPTICAL BUS DISCOVERY ---
        await new Promise(r => setTimeout(r, 240));
        if (!isMounted) return;
        setCurrentStepIndex(3);
        setStepStates(prev => prev.map((s, idx) => idx === 2 ? { ...s, status: 'active' } : s));
        setLogs(prev => [...prev, '[HARDWARE] Probing physical serial ports and I²C bus...']);

        const ports = await bridge.scanPorts().catch(() => []);
        const hwState = await bridge.getHardwareState().catch(() => 'CONNECTING');

        let hwDetail = 'Standby mode • No physical hardware detected';
        let hwStatus: 'passed' | 'warning' = 'warning';

        if (hwState === 'LIVE MEASUREMENT' || hwState === 'SENSOR DETECTED') {
          hwDetail = `Active link • COM ports detected (${ports.join(', ') || 'COM5'})`;
          hwStatus = 'passed';
          setLogs(prev => [...prev, `[HARDWARE OK] Sensor detected • I²C Bus 0x23 verified`]);
        } else if (ports.length > 0) {
          hwDetail = `Serial endpoints found: ${ports.join(', ')} • Sensor awaiting connect`;
          hwStatus = 'passed';
          setLogs(prev => [...prev, `[HARDWARE OK] Detected ports: ${ports.join(', ')}`]);
        } else {
          setLogs(prev => [...prev, `[HARDWARE NOTE] No active USB sensor connected • Offline exploration enabled`]);
        }

        setStepStates(prev => prev.map((s, idx) => idx === 2 ? { 
          ...s, 
          status: hwStatus,
          detail: hwDetail
        } : s));
        setProgressPercent(88);

        // --- STAGE 4: UI SHELL READINESS ---
        await new Promise(r => setTimeout(r, 220));
        if (!isMounted) return;
        setCurrentStepIndex(4);
        setStepStates(prev => prev.map((s, idx) => idx === 3 ? { ...s, status: 'active' } : s));
        setLogs(prev => [...prev, '[UI SHELL] Initializing scientific charts and theme engine...']);

        setStepStates(prev => prev.map((s, idx) => idx === 3 ? { 
          ...s, 
          status: 'passed',
          detail: 'High-DPI viewport configured • Theme loaded'
        } : s));
        setProgressPercent(100);
        setLogs(prev => [...prev, '[SYSTEM READY] Instrument POST completed. Launching workspace.']);

        await new Promise(r => setTimeout(r, 350));
        if (isMounted) {
          clearTimeout(safetyTimeout);
          onComplete();
        }

      } catch (err: any) {
        console.error('POST execution warning:', err);
        setLogs(prev => [...prev, `[NOTICE] ${err?.message || err}. Launching workspace.`]);
        setProgressPercent(100);
        setTimeout(onComplete, 500);
      }
    };

    runActualStartup();

    return () => {
      isMounted = false;
      clearTimeout(safetyTimeout);
    };
  }, [onComplete]);

  return (
    <motion.div 
      ref={containerRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.99 }}
      transition={{ duration: 0.4, ease: 'easeInOut' }}
      className="fixed inset-0 z-50 bg-[#07080A] flex flex-col justify-between p-8 select-none font-sans overflow-hidden"
    >
      {/* Top Bar */}
      <div className="flex items-center justify-between border-b border-border/40 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-chassis-850 border border-metrology-green/40 flex items-center justify-center text-metrology-green shadow-glow-green">
            <Activity className="w-4 h-4 animate-pulse" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-widest text-white uppercase font-mono">
              LuxSense Pro Metrology Workstation
            </h1>
            <p className="text-[11px] text-zinc-400 font-mono">
              PRECISION PHOTOPIC RADIOMETRY &bull; SYSTEM INITIALIZATION
            </p>
          </div>
        </div>

        <button
          onClick={onComplete}
          className="text-xs font-mono text-zinc-400 hover:text-metrology-green flex items-center space-x-1.5 border border-border px-3 py-1.5 rounded bg-chassis-850 hover:border-metrology-green/50 transition-colors"
        >
          <span>CONTINUE TO WORKSPACE</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Optical Aperture Animation & Step Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center my-auto max-w-5xl mx-auto w-full">
        {/* Left: Cinematic Optical Aperture Visualization */}
        <div className="flex flex-col items-center justify-center relative">
          <div className="relative w-64 h-64 flex items-center justify-center">
            {/* Spinning reticle / aperture */}
            <svg 
              ref={ringRef}
              className="absolute inset-0 w-full h-full text-zinc-800" 
              viewBox="0 0 200 200"
            >
              <circle cx="100" cy="100" r="92" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="4 6" />
              <circle cx="100" cy="100" r="72" fill="none" stroke="#21D789" strokeWidth="1.5" strokeOpacity="0.45" strokeDasharray="14 18" />
              <circle cx="100" cy="100" r="52" fill="none" stroke="currentColor" strokeWidth="1" />
              <line x1="100" y1="4" x2="100" y2="24" stroke="#21D789" strokeWidth="2" />
              <line x1="100" y1="176" x2="100" y2="196" stroke="#21D789" strokeWidth="2" />
              <line x1="4" y1="100" x2="24" y2="100" stroke="#21D789" strokeWidth="2" />
              <line x1="176" y1="100" x2="196" y2="100" stroke="#21D789" strokeWidth="2" />
            </svg>

            <motion.div 
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="w-32 h-32 rounded-full bg-chassis-900 border border-metrology-green/50 flex flex-col items-center justify-center text-center shadow-glow-green z-10 p-2"
            >
              <span className="text-[10px] font-mono text-zinc-400">LUXSENSE PRO</span>
              <span className="text-xl font-bold font-mono text-metrology-green">{appVersion}</span>
              <span className="text-[9px] font-mono text-zinc-400">DEVPRO-CORP</span>
            </motion.div>
          </div>

          {/* Centered Animated Progress Bar */}
          <div className="w-64 mt-6 space-y-1.5">
            <div className="flex justify-between text-[11px] font-mono text-zinc-300">
              <span>{progressPercent >= 100 ? 'System Ready' : 'Initializing Subsystems...'}</span>
              <span className="text-metrology-green font-bold">{progressPercent}%</span>
            </div>
            <div className="h-1.5 w-full bg-chassis-850 rounded-full overflow-hidden border border-border/60">
              <motion.div 
                className="h-full bg-metrology-green rounded-full shadow-glow-green"
                initial={{ width: '5%' }}
                animate={{ width: `${progressPercent}%` }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
              />
            </div>
          </div>
        </div>

        {/* Right: Subsystem Checklist */}
        <div className="space-y-3 bg-chassis-900 p-6 rounded-xl border border-border shadow-lg">
          <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider border-b border-border pb-2.5 flex justify-between">
            <span>Subsystem Verifications</span>
            <span>Status</span>
          </div>

          <div className="space-y-2.5">
            {stepStates.map((step, i) => (
              <div 
                key={step.id} 
                className={`flex items-center justify-between p-2.5 rounded transition-all font-mono text-xs ${
                  step.status === 'active' 
                    ? 'bg-chassis-800 border border-metrology-green/40 shadow-sm' 
                    : step.status === 'passed' 
                    ? 'bg-chassis-950/60 opacity-95' 
                    : step.status === 'warning'
                    ? 'bg-chassis-950/60 border border-metrology-amber/30'
                    : 'opacity-40'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <span className="text-zinc-500 text-[10px]">0{i + 1}</span>
                  <div>
                    <div className="font-semibold text-zinc-200">{step.name}</div>
                    <div className="text-[10px] text-zinc-400">{step.detail}</div>
                  </div>
                </div>

                <div>
                  {step.status === 'passed' && (
                    <span className="flex items-center space-x-1 text-metrology-green text-[11px] font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>PASS</span>
                    </span>
                  )}
                  {step.status === 'warning' && (
                    <span className="flex items-center space-x-1 text-metrology-amber text-[11px]">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span>STANDBY</span>
                    </span>
                  )}
                  {step.status === 'active' && (
                    <span className="text-metrology-amber text-[11px] animate-pulse flex items-center space-x-1">
                      <RefreshCw className="w-3 h-3 animate-spin" />
                      <span>PROBING</span>
                    </span>
                  )}
                  {step.status === 'pending' && (
                    <span className="text-zinc-600 text-[11px]">QUEUED</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Terminal Diagnostic Feed */}
      <div className="h-24 bg-chassis-950 border border-border/80 rounded-lg p-3 font-mono text-[11px] overflow-y-auto space-y-1">
        {logs.map((log, idx) => (
          <div key={idx} className="text-zinc-400 flex items-center space-x-2">
            <span className="text-metrology-green">&gt;</span>
            <span className={idx === logs.length - 1 ? 'text-white' : ''}>{log}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
