import React from 'react';
import { 
  Sparkles, 
  Cpu, 
  ShieldCheck, 
  Printer, 
  FileDown, 
  Check, 
  X, 
  ArrowRight
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export interface ChangelogCategory {
  title: string;
  badge: string;
  items: string[];
}

export interface ChangelogData {
  show: boolean;
  previous_version: string;
  current_version: string;
  release_date: string;
  release_name: string;
  summary: string;
  categories: ChangelogCategory[];
}

interface PostUpdateChangelogModalProps {
  data: ChangelogData;
  onAcknowledge: () => void;
}

export const PostUpdateChangelogModal: React.FC<PostUpdateChangelogModalProps> = ({
  data,
  onAcknowledge
}) => {
  const { resolvedTheme } = useTheme();

  const handlePrint = () => {
    window.print();
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm print:bg-white print:p-0 print:static print:inset-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="changelog-title"
    >
      <div 
        className="w-full max-w-3xl max-h-[90vh] flex flex-col bg-surface-base border border-border-focus rounded-xl shadow-instrument overflow-hidden print:border-none print:shadow-none print:max-h-none print:max-w-none print:w-full print:bg-white print:text-black"
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-chassis-950/80 print:bg-white print:border-b-2 print:border-black/20">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-metrology-green/10 text-metrology-green border border-metrology-green/30 print:border-black print:text-black">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 id="changelog-title" className="text-sm font-bold tracking-wider text-white uppercase print:text-black">
                  Update Succeeded
                </h2>
                <span className="flex items-center space-x-1.5 px-2 py-0.5 text-[10px] font-mono font-semibold rounded bg-chassis-800 text-metrology-green border border-metrology-green/30 print:border-black/30 print:text-black">
                  <span>v{data.previous_version}</span>
                  <ArrowRight className="w-2.5 h-2.5" />
                  <span>v{data.current_version}</span>
                </span>
              </div>
              <p className="text-xs text-zinc-400 font-mono print:text-zinc-600">
                Official DevPro-CORP Production Release &bull; {data.release_date}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 no-print">
            <button
              type="button"
              onClick={handlePrint}
              title="Print release notes"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded text-xs font-mono text-zinc-300 hover:text-white bg-chassis-850 hover:bg-chassis-800 border border-border transition-colors"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print</span>
            </button>
            <button
              type="button"
              onClick={handlePrint}
              title="Save documentation as PDF"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded text-xs font-mono text-zinc-300 hover:text-white bg-chassis-850 hover:bg-chassis-800 border border-border transition-colors"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>PDF</span>
            </button>
            <button
              type="button"
              onClick={onAcknowledge}
              title="Close and acknowledge"
              className="p-1.5 rounded text-zinc-400 hover:text-white hover:bg-chassis-800 transition-colors ml-1"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Scrollable Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 print:overflow-visible print:p-0 print:space-y-4">
          {/* Release Hero Card */}
          <div className="p-4 rounded-lg bg-chassis-900 border border-border/70 print:bg-transparent print:border-none print:p-0">
            <h3 className="text-base font-bold text-white print:text-black mb-1">
              {data.release_name}
            </h3>
            <p className="text-xs text-zinc-300 print:text-zinc-700 leading-relaxed">
              {data.summary}
            </p>
          </div>

          {/* Categories Grid */}
          <div className="space-y-4">
            {data.categories.map((cat, idx) => (
              <div 
                key={idx} 
                className="p-4 rounded-lg bg-surface-panel border border-border/60 print:border print:border-black/20 print:bg-white"
              >
                <div className="flex items-center justify-between mb-2.5">
                  <div className="flex items-center space-x-2">
                    {idx === 0 && <Sparkles className="w-4 h-4 text-amber-400 print:text-black" />}
                    {idx === 1 && <Cpu className="w-4 h-4 text-metrology-blue print:text-black" />}
                    {idx === 2 && <ShieldCheck className="w-4 h-4 text-metrology-green print:text-black" />}
                    <h4 className="text-xs font-bold uppercase tracking-wider text-white print:text-black font-mono">
                      {cat.title}
                    </h4>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-chassis-800 text-zinc-300 border border-border print:text-black print:border-black/30">
                    {cat.badge}
                  </span>
                </div>
                <ul className="space-y-1.5">
                  {cat.items.map((item, itemIdx) => (
                    <li key={itemIdx} className="flex items-start space-x-2 text-xs text-zinc-300 print:text-zinc-800">
                      <span className="text-metrology-green print:text-black font-bold mt-0.5">&bull;</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Integrity and Verification Stamp */}
          <div className="pt-2 border-t border-border/50 text-[10px] font-mono text-zinc-400 print:text-zinc-600 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-3.5 h-3.5 text-metrology-green print:text-black" />
              <span>Cryptographically verified release package &bull; DevPro Root Authority</span>
            </div>
            <span>Workstation ID: APPDATA/DevPro/LuxSensePro</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-3.5 border-t border-border bg-chassis-950/80 no-print">
          <div className="text-[11px] font-mono text-zinc-400">
            Persistent preferences &amp; calibration profiles safely preserved.
          </div>
          <button
            type="button"
            onClick={onAcknowledge}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-metrology-green hover:bg-metrology-green-bright text-chassis-950 font-bold text-xs shadow-glow-green transition-all"
          >
            <Check className="w-4 h-4" />
            <span>Acknowledge &amp; Launch Workstation</span>
          </button>
        </div>
      </div>
    </div>
  );
};
