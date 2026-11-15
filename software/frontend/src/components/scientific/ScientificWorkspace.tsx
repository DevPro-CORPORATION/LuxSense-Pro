import React, { useState, useEffect } from 'react';
import { bridge, TelemetryPacket } from '../../bridge/bridgeClient';
import { 
  UncertaintyBudget, 
  ExposureReport, 
  SpatialMeasurementPoint, 
  UniformityReport, 
  ExperimentSession 
} from '../../types';
import { 
  Microscope, 
  ShieldCheck, 
  MapPin, 
  Clock, 
  FileText, 
  Download, 
  Plus, 
  Trash2, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  Layers,
  Sparkles,
  BarChart,
  Grid
} from 'lucide-react';

interface ScientificWorkspaceProps {
  currentPacket: TelemetryPacket | null;
}

export const ScientificWorkspace: React.FC<ScientificWorkspaceProps> = ({ currentPacket }) => {
  const [activeSubTab, setActiveSubTab] = useState<'uncertainty' | 'exposure' | 'spatial' | 'sessions' | 'integrity'>('uncertainty');
  
  // Uncertainty state
  const [accuracySpecPct, setAccuracySpecPct] = useState<number>(7.0);
  const [budget, setBudget] = useState<UncertaintyBudget | null>(null);

  // Exposure state
  const [exposure, setExposure] = useState<ExposureReport | null>(null);

  // Spatial mapping state
  const [spatialPoints, setSpatialPoints] = useState<SpatialMeasurementPoint[]>([]);
  const [uniformity, setUniformity] = useState<UniformityReport | null>(null);
  const [newPointLabel, setNewPointLabel] = useState<string>('Task Station Center');
  const [newPointX, setNewPointX] = useState<number>(0.6);
  const [newPointY, setNewPointY] = useState<number>(0.0);

  // Sessions state
  const [sessions, setSessions] = useState<ExperimentSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('default');
  const [newSessionName, setNewSessionName] = useState<string>('');
  const [newSessionOperator, setNewSessionOperator] = useState<string>('DevPro Metrologist');
  const [newSessionSource, setNewSessionSource] = useState<string>('LED 4000K');
  const [isCreatingSession, setIsCreatingSession] = useState<boolean>(false);

  // Status message
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const b = await bridge.getUncertaintyBudget(selectedSessionId, accuracySpecPct);
      setBudget(b);

      const exp = await bridge.getExposureReport(selectedSessionId);
      setExposure(exp);

      const pts = await bridge.getSpatialPoints(selectedSessionId);
      setSpatialPoints(pts);

      const uni = await bridge.getUniformityReport(selectedSessionId);
      setUniformity(uni);

      const sessList = await bridge.listExperimentSessions();
      setSessions(sessList);
    } catch (e) {
      console.error('Error loading scientific metrics:', e);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, [selectedSessionId, accuracySpecPct]);

  // Spatial actions
  const handleRecordSpatialPoint = async () => {
    const lux = currentPacket ? currentPacket.cal_lux : 520.0;
    const ptId = `P${spatialPoints.length + 1}`;
    await bridge.recordSpatialPoint(selectedSessionId, ptId, newPointLabel, newPointX, newPointY, lux);
    setActionNotice(`Recorded point ${ptId} (${newPointLabel}) at ${lux.toFixed(2)} lx`);
    setTimeout(() => setActionNotice(null), 3000);
    loadData();
  };

  const handleClearSpatial = async () => {
    await bridge.clearSpatialPoints(selectedSessionId);
    setActionNotice('Cleared spatial mapping points for this session.');
    setTimeout(() => setActionNotice(null), 3000);
    loadData();
  };

  // Session actions
  const handleCreateSession = async () => {
    if (!newSessionName.trim()) return;
    const newId = `sess_${Date.now()}`;
    await bridge.createExperimentSession(
      newId,
      newSessionName,
      newSessionOperator,
      newSessionSource,
      300.0,
      750.0,
      'Laboratory experimental test'
    );
    setSelectedSessionId(newId);
    setIsCreatingSession(false);
    setNewSessionName('');
    setActionNotice(`Created experiment session ${newSessionName}`);
    setTimeout(() => setActionNotice(null), 3000);
    loadData();
  };

  // Report actions
  const handleExportCsv = async () => {
    const filename = await bridge.exportScientificReport(selectedSessionId, 'csv');
    setActionNotice(`Exported scientific CSV to ${filename}`);
    setTimeout(() => setActionNotice(null), 4000);
  };

  const handleExportHtml = async () => {
    const filename = await bridge.exportScientificReport(selectedSessionId, 'html');
    setActionNotice(`Generated printable certificate at ${filename}`);
    setTimeout(() => setActionNotice(null), 4000);
  };

  const liveCalLux = currentPacket ? currentPacket.cal_lux : (budget ? budget.sample_mean : 0);
  const liveRawLux = currentPacket ? currentPacket.raw_lux : 0;
  const liveFc = (liveCalLux / 10.7639104).toFixed(3);

  return (
    <div className="flex-1 flex flex-col h-full bg-chassis-900 p-5 space-y-4 overflow-y-auto font-sans">
      {/* Top Metrology Header */}
      <div className="bg-chassis-950 p-4 rounded-xl border border-border flex flex-wrap items-center justify-between gap-3 shadow-instrument">
        <div>
          <div className="flex items-center space-x-2">
            <Microscope className="w-4 h-4 text-metrology-green" />
            <h2 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
              Scientific Metrology &amp; Laboratory Suite
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-metrology-green/10 text-metrology-green border border-metrology-green/30">
              SCIENTIFIC EDITION
            </span>
          </div>
          <p className="text-[11px] font-mono text-zinc-400 mt-0.5">
            GUM / ISO 98-3 uncertainty budgets, CIE 157:2004 lux-hours, EN 12464-1 uniformity, and experiment sessions.
          </p>
        </div>

        {/* Session selector */}
        <div className="flex items-center space-x-2 font-mono text-xs">
          <span className="text-zinc-400 text-[11px]">Active Session:</span>
          <select
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
            className="bg-chassis-900 border border-border rounded px-2.5 py-1 text-zinc-200 focus:outline-none focus:border-border-focus text-xs font-mono"
          >
            {sessions.map(s => (
              <option key={s.session_id} value={s.session_id}>
                {s.name} ({s.lighting_type})
              </option>
            ))}
          </select>
          <button
            onClick={() => setIsCreatingSession(true)}
            className="p-1 rounded bg-chassis-850 border border-border hover:border-border-focus text-zinc-300"
            title="Create New Experiment Session"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {actionNotice && (
        <div className="bg-metrology-green/10 border border-metrology-green/40 p-2.5 rounded-lg text-xs font-mono text-metrology-green flex items-center space-x-2">
          <CheckCircle className="w-4 h-4" />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* Sub-tab Navigation */}
      <div className="flex items-center space-x-2 border-b border-border pb-1 font-mono text-xs select-none">
        {[
          { id: 'uncertainty', label: '1. Uncertainty Lab (GUM)', icon: ShieldCheck },
          { id: 'exposure', label: '2. Light Exposure (CIE 157)', icon: Clock },
          { id: 'spatial', label: '3. Spatial Uniformity (EN 12464)', icon: Grid },
          { id: 'sessions', label: '4. Session Comparisons', icon: Layers },
          { id: 'integrity', label: '5. Scientific Integrity & Reports', icon: FileText },
        ].map(tab => {
          const TabIcon = tab.icon;
          const isActive = activeSubTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSubTab(tab.id as any)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-t-lg transition-colors border-t border-l border-r ${
                isActive
                  ? 'bg-chassis-950 border-border text-metrology-green font-semibold'
                  : 'border-transparent text-zinc-400 hover:text-zinc-200'
              }`}
            >
              <TabIcon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* SUB-TAB 1: UNCERTAINTY BUDGET (GUM / ISO 98-3) */}
      {activeSubTab === 'uncertainty' && (
        <div className="space-y-4">
          {/* Top Live Reading with Error Interval */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-6 bg-chassis-950 border border-border rounded-xl p-5 shadow-instrument flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-zinc-400 uppercase tracking-widest flex items-center space-x-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-metrology-green" />
                  <span>Calibrated Illuminance &plusmn; Expanded Uncertainty (95% CI)</span>
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-chassis-850 border border-border text-zinc-400">
                  k = 2.0 (GUM ISO 98-3)
                </span>
              </div>

              <div className="my-3">
                <div className="flex items-baseline space-x-2 font-mono">
                  <span className="text-5xl font-bold text-white num-tabular glow-text-green">
                    {liveCalLux.toFixed(2)}
                  </span>
                  <span className="text-xl text-zinc-400">&plusmn; {budget ? budget.expanded_uncertainty_95.toFixed(2) : '0.00'}</span>
                  <span className="text-2xl text-metrology-green font-bold">lx</span>
                </div>
                <div className="text-xs font-mono text-zinc-400 mt-1 flex items-center space-x-3">
                  <span>Foot-Candles: <strong className="text-zinc-200">{liveFc} fc</strong></span>
                  <span>&bull;</span>
                  <span>Relative Uncertainty: <strong className="text-metrology-green">&plusmn;{budget ? budget.relative_expanded_uncertainty_pct.toFixed(1) : '0.0'}%</strong></span>
                </div>
              </div>

              <div className="pt-2 border-t border-border/50 text-[11px] font-mono text-zinc-400 flex justify-between">
                <span>[MEASURED RAW]: {liveRawLux.toFixed(2)} lx</span>
                <span>[DEGREES OF FREEDOM]: {budget ? budget.degrees_of_freedom : 0}</span>
                <span>[REPEATABILITY SE]: &plusmn;{budget ? budget.standard_error.toFixed(3) : '0.000'} lx</span>
              </div>
            </div>

            {/* Sensor Specification Selector */}
            <div className="lg:col-span-6 bg-chassis-950 border border-border rounded-xl p-5 flex flex-col justify-between">
              <div>
                <span className="text-xs font-mono font-bold text-white uppercase tracking-wider block mb-1">
                  Type B Sensor Accuracy Budget
                </span>
                <p className="text-[11px] font-mono text-zinc-400 mb-3">
                  ROHM BH1750 factory tolerance is &plusmn;20%. With DevPro optical reference calibration, standard uncertainty drops to &plusmn;5% &ndash; &plusmn;7%.
                </p>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-zinc-300">Sensor Accuracy Tolerance:</span>
                    <span className="text-metrology-green font-bold">&plusmn;{accuracySpecPct.toFixed(1)}%</span>
                  </div>
                  <input
                    type="range"
                    min="3.0"
                    max="20.0"
                    step="0.5"
                    value={accuracySpecPct}
                    onChange={(e) => setAccuracySpecPct(parseFloat(e.target.value))}
                    className="w-full accent-metrology-green h-1.5 bg-chassis-800 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] font-mono text-zinc-400">
                    <span>3.0% (Metrology Grade)</span>
                    <span>7.0% (Calibrated Bench)</span>
                    <span>20.0% (Raw Factory)</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-2.5 bg-chassis-900 rounded border border-border text-[10px] font-mono text-zinc-400">
                Formula: u_combined = &radic;(u_sensor&sup2; + u_repeatability&sup2;) &bull; Expanded U = 2.0 &times; u_combined
              </div>
            </div>
          </div>

          {/* Uncertainty Budget Breakdown Table */}
          {budget && (
            <div className="bg-chassis-950 border border-border rounded-xl p-4">
              <div className="text-xs font-mono font-bold text-white uppercase tracking-wider mb-2">
                Uncertainty Budget Breakdown (GUM Table)
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-chassis-900 border-b border-border text-zinc-400 text-[10px] uppercase">
                    <tr>
                      <th className="py-2 px-3">Uncertainty Source</th>
                      <th className="py-2 px-3">Type</th>
                      <th className="py-2 px-3">Distribution</th>
                      <th className="py-2 px-3">Divisor</th>
                      <th className="py-2 px-3 text-right">Standard Uncertainty (u)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 text-zinc-300 text-[11px]">
                    <tr>
                      <td className="py-2 px-3 font-semibold text-white">BH1750 Sensor Accuracy Spec</td>
                      <td className="py-2 px-3 text-zinc-400">Type B</td>
                      <td className="py-2 px-3">Rectangular (&plusmn;{budget.sensor_accuracy_spec_percent}%)</td>
                      <td className="py-2 px-3">&radic;3 &asymp; 1.732</td>
                      <td className="py-2 px-3 text-right text-zinc-200 num-tabular">&plusmn;{budget.sensor_uncertainty_lux.toFixed(2)} lx</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-3 font-semibold text-white">Measurement Repeatability</td>
                      <td className="py-2 px-3 text-zinc-400">Type A</td>
                      <td className="py-2 px-3">Normal (s = {budget.standard_deviation.toFixed(2)} lx)</td>
                      <td className="py-2 px-3">&radic;N</td>
                      <td className="py-2 px-3 text-right text-zinc-200 num-tabular">&plusmn;{budget.repeatability_uncertainty_lux.toFixed(3)} lx</td>
                    </tr>
                    <tr className="bg-chassis-900/60 font-semibold text-metrology-blue">
                      <td className="py-2 px-3">Combined Standard Uncertainty (u_c)</td>
                      <td className="py-2 px-3">—</td>
                      <td className="py-2 px-3">Root-Sum-Squares (RSS)</td>
                      <td className="py-2 px-3">1.0</td>
                      <td className="py-2 px-3 text-right num-tabular">&plusmn;{budget.combined_standard_uncertainty.toFixed(2)} lx</td>
                    </tr>
                    <tr className="bg-chassis-850 font-bold text-metrology-green">
                      <td className="py-2 px-3">Expanded Uncertainty U (95.45% Confidence)</td>
                      <td className="py-2 px-3">—</td>
                      <td className="py-2 px-3">Student-t (Coverage Factor k=2.0)</td>
                      <td className="py-2 px-3">—</td>
                      <td className="py-2 px-3 text-right num-tabular">&plusmn;{budget.expanded_uncertainty_95.toFixed(2)} lx (&plusmn;{budget.relative_expanded_uncertainty_pct.toFixed(1)}%)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 2: LIGHT EXPOSURE (CIE 157:2004) */}
      {activeSubTab === 'exposure' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-chassis-950 border border-border rounded-xl p-4">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Cumulative Exposure</div>
              <div className="text-2xl font-bold font-mono text-white num-tabular mt-1">
                {exposure ? exposure.cumulative_lux_hours.toFixed(1) : '0.0'} <span className="text-sm text-metrology-green">lx&middot;h</span>
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-1">
                {exposure ? exposure.cumulative_lux_seconds.toLocaleString() : '0'} lx&middot;s integrated
              </div>
            </div>

            <div className="bg-chassis-950 border border-border rounded-xl p-4">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Sampling Duration</div>
              <div className="text-2xl font-bold font-mono text-metrology-blue num-tabular mt-1">
                {exposure ? exposure.duration_hours.toFixed(2) : '0.00'} <span className="text-sm text-zinc-400">hours</span>
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-1">
                {exposure ? exposure.total_duration_seconds.toFixed(0) : '0'} seconds total run
              </div>
            </div>

            <div className="bg-chassis-950 border border-border rounded-xl p-4">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Projected Annual Load</div>
              <div className="text-2xl font-bold font-mono text-metrology-amber num-tabular mt-1">
                {exposure ? (exposure.annual_projected_lux_hours / 1000).toFixed(1) : '0.0'} <span className="text-sm text-zinc-400">klx&middot;h/yr</span>
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-1">
                Assumes 10 hours/day &times; 365 days
              </div>
            </div>
          </div>

          {/* Archival Museum Standards Gauge */}
          <div className="bg-chassis-950 border border-border rounded-xl p-5 space-y-3">
            <div className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center justify-between">
              <span>CIE 157:2004 Archival Conservation Thresholds</span>
              <span className="text-metrology-green text-[11px] font-semibold">
                {exposure?.cie157_conservation_status}
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="p-3 bg-chassis-900 rounded border border-border flex justify-between items-center">
                <div>
                  <div className="text-white font-semibold">Category 1: Highly Sensitive Artifacts (50,000 lx&middot;h/year)</div>
                  <div className="text-[10px] text-zinc-400">Silk, historical paper, watercolors, dyed textiles, tapestries.</div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  exposure && exposure.annual_projected_lux_hours <= 50000 
                    ? 'bg-metrology-green/20 text-metrology-green border border-metrology-green/40' 
                    : 'bg-chassis-800 text-zinc-500'
                }`}>
                  {exposure && exposure.annual_projected_lux_hours <= 50000 ? 'SAFE' : 'EXCEEDED'}
                </span>
              </div>

              <div className="p-3 bg-chassis-900 rounded border border-border flex justify-between items-center">
                <div>
                  <div className="text-white font-semibold">Category 2: Moderately Sensitive Artifacts (150,000 lx&middot;h/year)</div>
                  <div className="text-[10px] text-zinc-400">Oil and tempera paintings, wood, leather, natural materials.</div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  exposure && exposure.annual_projected_lux_hours <= 150000 
                    ? 'bg-metrology-green/20 text-metrology-green border border-metrology-green/40' 
                    : 'bg-chassis-800 text-zinc-500'
                }`}>
                  {exposure && exposure.annual_projected_lux_hours <= 150000 ? 'SAFE' : 'EXCEEDED'}
                </span>
              </div>

              <div className="p-3 bg-chassis-900 rounded border border-border flex justify-between items-center">
                <div>
                  <div className="text-white font-semibold">Category 3: Standard Exhibits (450,000 lx&middot;h/year)</div>
                  <div className="text-[10px] text-zinc-400">Stone, ceramics, glass, uncoated metals.</div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  exposure && exposure.annual_projected_lux_hours <= 450000 
                    ? 'bg-metrology-green/20 text-metrology-green border border-metrology-green/40' 
                    : 'bg-metrology-crimson/20 text-metrology-crimson border border-metrology-crimson/40'
                }`}>
                  {exposure && exposure.annual_projected_lux_hours <= 450000 ? 'SAFE' : 'HAZARD'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 3: SPATIAL ILLUMINANCE MAPPING (EN 12464-1) */}
      {activeSubTab === 'spatial' && (
        <div className="space-y-4">
          {/* Uniformity Metrics Header */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="bg-chassis-950 border border-border rounded-xl p-3">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Uniformity U1 (E_min / E_avg)</div>
              <div className="text-2xl font-bold font-mono text-metrology-green num-tabular mt-1">
                {uniformity ? uniformity.uniformity_u1.toFixed(3) : '0.000'}
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-0.5">EN 12464 Req: &ge; 0.60</div>
            </div>

            <div className="bg-chassis-950 border border-border rounded-xl p-3">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Uniformity U2 (E_min / E_max)</div>
              <div className="text-2xl font-bold font-mono text-white num-tabular mt-1">
                {uniformity ? uniformity.uniformity_u2.toFixed(3) : '0.000'}
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-0.5">Extremum Spread Ratio</div>
            </div>

            <div className="bg-chassis-950 border border-border rounded-xl p-3">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Diversity Ratio (E_max / E_min)</div>
              <div className="text-2xl font-bold font-mono text-metrology-blue num-tabular mt-1">
                {uniformity ? uniformity.diversity_ratio.toFixed(2) : '1.00'}
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-0.5">Luminance Contrast</div>
            </div>

            <div className="bg-chassis-950 border border-border rounded-xl p-3">
              <div className="text-[10px] font-mono text-zinc-400 uppercase">Sample Points</div>
              <div className="text-2xl font-bold font-mono text-zinc-200 num-tabular mt-1">
                {spatialPoints.length}
              </div>
              <div className="text-[10px] font-mono text-zinc-400 mt-0.5">Coordinates mapped</div>
            </div>
          </div>

          {/* Record Position Panel */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5 text-metrology-green" />
                <span>Manual Spatial Point Capture</span>
              </span>
              <button
                onClick={handleClearSpatial}
                className="text-[10px] font-mono text-zinc-400 hover:text-metrology-crimson flex items-center space-x-1"
              >
                <Trash2 className="w-3 h-3" />
                <span>CLEAR POINTS</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 font-mono text-xs items-end">
              <div>
                <label className="text-zinc-400 text-[10px] block mb-1">Point Description:</label>
                <input
                  type="text"
                  value={newPointLabel}
                  onChange={(e) => setNewPointLabel(e.target.value)}
                  className="w-full bg-chassis-900 border border-border rounded p-2 text-zinc-200 focus:outline-none focus:border-border-focus text-xs font-mono"
                  placeholder="e.g. Desk Front Left"
                />
              </div>

              <div>
                <label className="text-zinc-400 text-[10px] block mb-1">X Coordinate (meters):</label>
                <input
                  type="number"
                  step="0.1"
                  value={newPointX}
                  onChange={(e) => setNewPointX(parseFloat(e.target.value) || 0)}
                  className="w-full bg-chassis-900 border border-border rounded p-2 text-zinc-200 focus:outline-none focus:border-border-focus text-xs font-mono"
                />
              </div>

              <div>
                <label className="text-zinc-400 text-[10px] block mb-1">Y Coordinate (meters):</label>
                <input
                  type="number"
                  step="0.1"
                  value={newPointY}
                  onChange={(e) => setNewPointY(parseFloat(e.target.value) || 0)}
                  className="w-full bg-chassis-900 border border-border rounded p-2 text-zinc-200 focus:outline-none focus:border-border-focus text-xs font-mono"
                />
              </div>

              <button
                onClick={handleRecordSpatialPoint}
                className="p-2 rounded bg-metrology-green text-chassis-950 font-bold hover:bg-metrology-green/90 transition-colors shadow-glow-green text-xs font-mono flex items-center justify-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>SAMPLE LIVE ({liveCalLux.toFixed(1)} lx)</span>
              </button>
            </div>
          </div>

          {/* Spatial Heatmap Table */}
          <div className="bg-chassis-950 border border-border rounded-xl p-4">
            <div className="text-xs font-mono font-bold text-white uppercase tracking-wider mb-2">
              Spatial Grid Mapped Points ({spatialPoints.length} total)
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-chassis-900 border-b border-border text-zinc-400 text-[10px] uppercase">
                  <tr>
                    <th className="py-2 px-3">Point ID</th>
                    <th className="py-2 px-3">Location Label</th>
                    <th className="py-2 px-3">Coordinates (X, Y)</th>
                    <th className="py-2 px-3 text-right">Measured Lux</th>
                    <th className="py-2 px-3 text-right">Foot-Candles</th>
                    <th className="py-2 px-3 text-center">Uniformity Ratio vs Mean</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-zinc-300 text-[11px]">
                  {spatialPoints.map(p => {
                    const avg = uniformity?.average_lux || 500.0;
                    const ratio = (p.measured_lux / avg);
                    return (
                      <tr key={p.point_id} className="hover:bg-chassis-850/50">
                        <td className="py-2 px-3 font-bold text-metrology-green">{p.point_id}</td>
                        <td className="py-2 px-3 text-white font-medium">{p.label}</td>
                        <td className="py-2 px-3 text-zinc-400">({p.x_m.toFixed(2)}m, {p.y_m.toFixed(2)}m)</td>
                        <td className="py-2 px-3 text-right text-zinc-100 font-bold num-tabular">{p.measured_lux.toFixed(2)} lx</td>
                        <td className="py-2 px-3 text-right text-zinc-400 num-tabular">{(p.measured_lux / 10.7639).toFixed(2)} fc</td>
                        <td className="py-2 px-3 text-center">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                            ratio >= 0.8 && ratio <= 1.2 
                              ? 'bg-metrology-green/15 text-metrology-green' 
                              : 'bg-metrology-amber/15 text-metrology-amber'
                          }`}>
                            {(ratio * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 4: SESSIONS & COMPARISONS */}
      {activeSubTab === 'sessions' && (
        <div className="space-y-4">
          <div className="bg-chassis-950 border border-border rounded-xl p-4">
            <div className="flex items-center justify-between border-b border-border pb-2 mb-3">
              <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                Experiment Session History ({sessions.length} recorded)
              </span>
              <button
                onClick={() => setIsCreatingSession(!isCreatingSession)}
                className="px-2.5 py-1 rounded bg-chassis-850 border border-border text-xs font-mono text-zinc-200 hover:border-border-focus"
              >
                + NEW EXPERIMENT SESSION
              </button>
            </div>

            {isCreatingSession && (
              <div className="p-3 bg-chassis-900 border border-border rounded-lg mb-4 grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
                <div>
                  <label className="text-zinc-400 text-[10px] block mb-1">Session Name:</label>
                  <input
                    type="text"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    placeholder="e.g. Daylight Penetration Trial #2"
                    className="w-full bg-chassis-950 border border-border rounded p-1.5 text-zinc-200 text-xs"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 text-[10px] block mb-1">Operator:</label>
                  <input
                    type="text"
                    value={newSessionOperator}
                    onChange={(e) => setNewSessionOperator(e.target.value)}
                    className="w-full bg-chassis-950 border border-border rounded p-1.5 text-zinc-200 text-xs"
                  />
                </div>
                <div>
                  <label className="text-zinc-400 text-[10px] block mb-1">Lighting Source:</label>
                  <input
                    type="text"
                    value={newSessionSource}
                    onChange={(e) => setNewSessionSource(e.target.value)}
                    className="w-full bg-chassis-950 border border-border rounded p-1.5 text-zinc-200 text-xs"
                  />
                </div>
                <div className="sm:col-span-3 flex justify-end space-x-2">
                  <button
                    onClick={() => setIsCreatingSession(false)}
                    className="px-3 py-1 rounded border border-border text-zinc-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateSession}
                    className="px-4 py-1 rounded bg-metrology-green text-chassis-950 font-bold hover:bg-metrology-green/90"
                  >
                    Create Session
                  </button>
                </div>
              </div>
            )}

            <div className="space-y-2">
              {sessions.map(s => (
                <div
                  key={s.session_id}
                  onClick={() => setSelectedSessionId(s.session_id)}
                  className={`p-3 rounded-lg border transition-all cursor-pointer font-mono text-xs flex items-center justify-between ${
                    selectedSessionId === s.session_id
                      ? 'bg-chassis-800 border-metrology-green text-white shadow-glow-green'
                      : 'bg-chassis-900 border-border text-zinc-400 hover:border-border-focus'
                  }`}
                >
                  <div>
                    <div className="font-bold text-zinc-200">{s.name}</div>
                    <div className="text-[10px] text-zinc-400">
                      Operator: {s.operator} &bull; Source: {s.lighting_type} &bull; Created: {s.created_at}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] px-2 py-0.5 rounded bg-chassis-950 border border-border text-zinc-300">
                      ID: {s.session_id}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 5: SCIENTIFIC INTEGRITY & EXPORT */}
      {activeSubTab === 'integrity' && (
        <div className="space-y-4">
          {/* Classification Table */}
          <div className="bg-chassis-950 border border-border rounded-xl p-5 space-y-3">
            <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-metrology-green" />
              <span>Scientific Integrity &amp; Photometric Value Classification</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
                <span className="badge badge-measured">[MEASURED] Direct Transducer Output</span>
                <p className="text-[11px] text-zinc-400 leading-relaxed pt-1">
                  Raw illuminance digitized directly by the ROHM BH1750FVI 16-bit successive approximation ADC via I2C bus: E_raw = count / 1.2 lx.
                </p>
              </div>

              <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
                <span className="badge badge-calibrated">[CALIBRATED] Metrology Corrected</span>
                <p className="text-[11px] text-zinc-400 leading-relaxed pt-1">
                  Mathematical correction applying optical bench zero-offset and gain multiplier: E_cal = (E_raw + Offset) &times; Gain.
                </p>
              </div>

              <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
                <span className="badge badge-calc">[CALCULATED] Mathematically Derived</span>
                <p className="text-[11px] text-zinc-400 leading-relaxed pt-1">
                  Exact physical units derived from geometry and time: Foot-Candles (lx / 10.7639), Lux-Hours (&int; E dt), and Uniformity ratios (U1 = E_min / E_avg).
                </p>
              </div>

              <div className="p-3 bg-chassis-900 rounded border border-border space-y-1">
                <span className="badge badge-est">[ESTIMATED] Optical Model Assumption</span>
                <p className="text-[11px] text-zinc-400 leading-relaxed pt-1">
                  Photopic irradiance (W/m&sup2;) estimated using the CIE standard luminous efficacy of 683 lm/W at 555 nm. Labeled as estimated because real spectral distributions vary.
                </p>
              </div>
            </div>

            {/* Scientific Disclaimers */}
            <div className="p-3.5 bg-metrology-amber/10 border border-metrology-amber/30 rounded-lg text-xs font-mono text-zinc-300 space-y-1">
              <div className="text-metrology-amber font-bold flex items-center space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Sensor Scope &amp; Non-Fabrication Guarantee:</span>
              </div>
              <p className="text-[11px] text-zinc-400 leading-relaxed">
                The BH1750FVI is a single broadband silicon photodiode with an integrated optical filter tuned to the photopic luminosity curve V(&lambda;). 
                <strong> LuxSense Pro strictly refuses to fabricate spectral power distributions (SPD), Correlated Colour Temperature (CCT), Colour Rendering Index (CRI), or optical flicker percentages.</strong> Fabricating these values without multi-channel or high-frequency optical sensors would compromise scientific metrology standards.
              </p>
            </div>
          </div>

          {/* Export Report Actions */}
          <div className="bg-chassis-950 border border-border rounded-xl p-5 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-sm font-bold font-mono text-white">Generate Official Metrology Reports</div>
              <div className="text-xs font-mono text-zinc-400 mt-0.5">
                Produce accredited-style test certificates with uncertainty budgets and uniformity records.
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={handleExportCsv}
                className="flex items-center space-x-2 px-4 py-2 rounded bg-chassis-850 border border-border hover:border-border-focus text-xs font-mono text-zinc-200 transition-colors font-semibold"
              >
                <Download className="w-3.5 h-3.5" />
                <span>EXPORT SCIENTIFIC CSV</span>
              </button>

              <button
                onClick={handleExportHtml}
                className="flex items-center space-x-2 px-4 py-2 rounded bg-metrology-green text-chassis-950 text-xs font-mono font-bold hover:bg-metrology-green/90 transition-colors shadow-glow-green"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>GENERATE PRINT CERTIFICATE (HTML/PDF)</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
