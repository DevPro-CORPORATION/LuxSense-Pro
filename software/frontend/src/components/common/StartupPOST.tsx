import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { Activity, ShieldCheck, Cpu, CheckCircle2, ChevronRight } from 'lucide-react';

interface StartupPOSTProps {
  onComplete: () => void;
}

interface StepInfo {
  id: string;
  name: string;
  detail: string;
  status: 'pending' | 'active' | 'passed';
}

export const StartupPOST: React.FC<StartupPOSTProps> = ({ onComplete }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [logs, setLogs] = useState<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const logoRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<SVGSVGElement>(null);

  const steps: StepInfo[] = [
    { id: 'bios', name: 'ATmega328P Core POST', detail: 'Clock 16.000 MHz, Flash 32KB verify', status: 'pending' },
    { id: 'i2c', name: 'BH1750FVI Optical Bus Check', detail: 'I2C 0x23 ACK, Continuous H-Res Mode', status: 'pending' },
    { id: 'crypto', name: 'Cryptographic Engine Sync', detail: 'Rolling 128-bit XOR keystream init', status: 'pending' },
    { id: 'cal', name: 'Photopic Calibration Profile', detail: 'Applying dark zero offset & optical gain', status: 'pending' },
    { id: 'history', name: 'SQLite Storage Telemetry DB', detail: 'Verifying tables, journal mode WAL', status: 'pending' },
    { id: 'channel', name: 'GitHub Update Infrastructure', detail: 'Stable/Beta release channel handshake', status: 'pending' },
  ];

  const [stepStates, setStepStates] = useState<StepInfo[]>(steps);

  useEffect(() => {
    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      onComplete();
      return;
    }

    // GSAP animation on the optical aperture ring
    if (ringRef.current) {
      gsap.to(ringRef.current, {
        rotation: 360,
        repeat: -1,
        duration: 8,
        ease: 'none',
        transformOrigin: '50% 50%',
      });
    }

    // Sequence execution
    let idx = 0;
    const interval = setInterval(() => {
      if (idx < steps.length) {
        const step = steps[idx];
        setStepStates(prev => prev.map((s, i) => {
          if (i === idx) return { ...s, status: 'active' };
          if (i < idx) return { ...s, status: 'passed' };
          return s;
        }));

        setLogs(prev => [
          ...prev,
          `[POST +${(idx * 280 + 120)}ms] [${step.id.toUpperCase()}] ${step.name}: ${step.detail} -> OK`
        ]);

        idx++;
        setCurrentStepIndex(idx);
      } else {
        clearInterval(interval);
        setStepStates(prev => prev.map(s => ({ ...s, status: 'passed' })));
        setLogs(prev => [...prev, '[SYSTEM READY] Instrument POST completed. All 6 subsystems nominal.']);
        setTimeout(() => {
          onComplete();
        }, 600);
      }
    }, 280);

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <motion.div 
      ref={containerRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ duration: 0.5, ease: 'easeInOut' }}
      className="fixed inset-0 z-50 bg-[#07080A] flex flex-col justify-between p-10 select-none font-sans overflow-hidden"
    >
      {/* Top Bar */}
      <div className="flex items-center justify-between border-b border-border/40 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-chassis-850 border border-metrology-green/40 flex items-center justify-center text-metrology-green shadow-glow-green">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-widest text-white uppercase font-mono">
              LuxSense Pro Metrology Workstation
            </h1>
            <p className="text-[11px] text-zinc-400 font-mono">
              FIRMWARE POST &bull; INSTRUMENT BOOTSTRAP SEQUENCE
            </p>
          </div>
        </div>

        <button
          onClick={onComplete}
          className="text-xs font-mono text-zinc-400 hover:text-metrology-green flex items-center space-x-1 border border-border px-3 py-1.5 rounded bg-chassis-850 hover:border-metrology-green/50 transition-colors"
        >
          <span>BYPASS SEQUENCE</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Optical Aperture Animation & Step Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center my-auto max-w-5xl mx-auto w-full">
        {/* Left: Cinematic Optical Aperture Visualization */}
        <div className="flex flex-col items-center justify-center relative">
          <div className="relative w-64 h-64 flex items-center justify-center">
            {/* Spinning reticle / aperture */}
            <svg 
              ref={ringRef}
              className="absolute inset-0 w-full h-full text-zinc-800" 
              viewBox="0 0 200 200"
            >
              <circle cx="100" cy="100" r="90" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="4 6" />
              <circle cx="100" cy="100" r="70" fill="none" stroke="#21D789" strokeWidth="1.5" strokeOpacity="0.4" strokeDasharray="12 18" />
              <circle cx="100" cy="100" r="50" fill="none" stroke="currentColor" strokeWidth="1" />
              <line x1="100" y1="5" x2="100" y2="25" stroke="#21D789" strokeWidth="2" />
              <line x1="100" y1="175" x2="100" y2="195" stroke="#21D789" strokeWidth="2" />
              <line x1="5" y1="100" x2="25" y2="100" stroke="#21D789" strokeWidth="2" />
              <line x1="175" y1="100" x2="195" y2="100" stroke="#21D789" strokeWidth="2" />
            </svg>

            <motion.div 
              ref={logoRef}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.6 }}
              className="w-28 h-28 rounded-full bg-chassis-900 border border-metrology-green/50 flex flex-col items-center justify-center text-center shadow-glow-green z-10"
            >
              <span className="text-[10px] font-mono text-zinc-400">LUXSENSE</span>
              <span className="text-xl font-bold font-mono text-metrology-green">2.2.0</span>
              <span className="text-[9px] font-mono text-zinc-400">DEVPRO-CORP</span>
            </motion.div>
          </div>

          <div className="mt-6 text-center">
            <div className="text-xs font-mono text-metrology-green font-semibold uppercase tracking-wider">
              {currentStepIndex >= steps.length ? 'System Ready' : `Calibrating Photodiode Array (${currentStepIndex}/${steps.length})`}
            </div>
            <div className="text-[11px] font-mono text-zinc-400 mt-1">
              BH1750 High-Resolution 16-Bit Radiometric Core
            </div>
          </div>
        </div>

        {/* Right: Subsystem Checklist */}
        <div className="space-y-3 bg-chassis-900 p-6 rounded-xl border border-border">
          <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider border-b border-border pb-2 flex justify-between">
            <span>Subsystem Diagnostics</span>
            <span>Status</span>
          </div>

          <div className="space-y-2.5">
            {stepStates.map((step, i) => (
              <div 
                key={step.id} 
                className={`flex items-center justify-between p-2 rounded transition-all font-mono text-xs ${
                  step.status === 'active' 
                    ? 'bg-chassis-800 border border-metrology-green/30' 
                    : step.status === 'passed' 
                    ? 'bg-chassis-950/60 opacity-90' 
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
                    <span className="flex items-center space-x-1 text-metrology-green text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>PASS</span>
                    </span>
                  )}
                  {step.status === 'active' && (
                    <span className="text-metrology-amber text-[11px] animate-pulse">
                      TESTING...
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

