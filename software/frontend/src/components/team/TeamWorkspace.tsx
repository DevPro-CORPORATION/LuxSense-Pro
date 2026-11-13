import React from 'react';
import { 
  Users, 
  ShieldCheck, 
  Award, 
  GitBranch, 
  Cpu, 
  Layers, 
  Code2, 
  Sparkles,
  ExternalLink,
  Building
} from 'lucide-react';

export const TeamWorkspace: React.FC = () => {
  const teamMembers = [
    {
      name: 'M Somasundaram',
      role: 'Lead Systems Architect & Embedded Firmware',
      focus: 'ATmega328P Bare-Metal Firmware, I2C Bus Arbitration, Rolling-128 XOR Cipher',
      experience: '12+ years in hardware telemetry, embedded C/C++, and real-time instrumentation systems.',
      icon: Cpu,
      color: '#21D789'
    },
    {
      name: 'Alex Chen',
      role: 'Optical Metrology & Signal Processing Engineer',
      focus: 'CIE 1931 Photopic Observer Curves, Mathematical Calibration Engines, Dark Offset Correction',
      experience: 'Specialist in radiometry, spectroradiometric characterization, and precision photodiode sensors.',
      icon: Layers,
      color: '#61AFEF'
    },
    {
      name: 'Sarah Jenkins',
      role: 'Desktop Platform & Cryptographic Security Lead',
      focus: 'PySide6 Qt Shell, Authenticode Verification, Inno Setup CI/CD, Automatic Rollback Updater',
      experience: 'Expert in Windows systems engineering, cryptographic hash verification, and secure update pipelines.',
      icon: ShieldCheck,
      color: '#E5C07B'
    }
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto">
      {/* Top Organization Header */}
      <div className="bg-chassis-950 p-5 rounded-xl border border-border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-instrument">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-chassis-850 border border-metrology-green/40 flex items-center justify-center text-metrology-green shadow-glow-green">
            <Building className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
                DevPro Corporation (DevPro-CORP)
              </h2>
              <span className="text-[10px] px-2 py-0.5 rounded bg-metrology-green/10 text-metrology-green border border-metrology-green/30 font-mono">
                OFFICIAL REPO OWNER
              </span>
            </div>
            <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
              Precision scientific instrumentation, radiometry engineering, and mission-critical telemetry software.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 font-mono text-xs">
          <div className="bg-chassis-900 px-3 py-1.5 rounded border border-border text-zinc-300">
            Organization: <strong className="text-white">DevPro-CORP</strong>
          </div>
        </div>
      </div>

      {/* Team Member Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {teamMembers.map((member, idx) => {
          const MemberIcon = member.icon;
          return (
            <div 
              key={idx}
              className="bg-chassis-950 border border-border rounded-xl p-5 flex flex-col justify-between space-y-4 relative overflow-hidden group hover:border-border-focus transition-all shadow-instrument"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div 
                    className="w-10 h-10 rounded-lg bg-chassis-900 border border-border flex items-center justify-center"
                    style={{ color: member.color }}
                  >
                    <MemberIcon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-zinc-400 bg-chassis-900 px-2 py-0.5 rounded border border-border/60">
                    CORE LEAD
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold font-mono text-white tracking-tight">
                    {member.name}
                  </h3>
                  <div className="text-xs font-mono font-medium mt-0.5" style={{ color: member.color }}>
                    {member.role}
                  </div>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-border/50 text-[11px] font-mono text-zinc-400">
                  <div>
                    <span className="text-zinc-500 font-semibold block text-[10px] uppercase">Domain Ownership:</span>
                    <span className="text-zinc-300 leading-snug">{member.focus}</span>
                  </div>
                  <div className="pt-1">
                    <span className="text-zinc-500 font-semibold block text-[10px] uppercase">Engineering Profile:</span>
                    <span className="text-zinc-400 leading-snug">{member.experience}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-border/40 flex items-center justify-between text-[10px] font-mono text-zinc-400">
                <span>VERIFIED COMMITS: GPG SIGNED</span>
                <span className="text-metrology-green font-semibold">100% PASS</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Corporate Philosophy & Metrology Standards */}
      <div className="bg-chassis-950 border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2">
          <Award className="w-4 h-4 text-metrology-green" />
          <span>DevPro-CORP Engineering Tenets &amp; Metrology Standards</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1 font-mono text-xs">
          <div className="bg-chassis-900 p-3.5 rounded-lg border border-border space-y-1">
            <div className="text-white font-semibold text-xs flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-metrology-green" />
              <span>Photometric Fidelity</span>
            </div>
            <p className="text-[11px] text-zinc-400 leading-relaxed">
              Strict conformity to the CIE 1931 photopic luminosity function $V(\lambda)$, ensuring measurements match standard human eye response without infrared contamination.
            </p>
          </div>

          <div className="bg-chassis-900 p-3.5 rounded-lg border border-border space-y-1">
            <div className="text-white font-semibold text-xs flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-metrology-blue" />
              <span>Cryptographic Safety</span>
            </div>
            <p className="text-[11px] text-zinc-400 leading-relaxed">
              All binary releases and telemetry packets are cryptographically guarded. SHA-256 manifests, Authenticode signatures, and rolling keystream ciphers are mandatory.
            </p>
          </div>

          <div className="bg-chassis-900 p-3.5 rounded-lg border border-border space-y-1">
            <div className="text-white font-semibold text-xs flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-metrology-amber" />
              <span>Zero-Data-Loss Invariant</span>
            </div>
            <p className="text-[11px] text-zinc-400 leading-relaxed">
              Every calibration curve, historical reading, and configuration state resides in protected AppData storage, completely immune to application upgrades or rollbacks.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
