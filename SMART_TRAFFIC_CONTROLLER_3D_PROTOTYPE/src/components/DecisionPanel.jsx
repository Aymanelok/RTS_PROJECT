import { BrainCircuit, CheckCircle2, GitBranch, TrafficCone } from 'lucide-react';
import { formatPhaseTime } from '../utils/trafficLogic.js';

export default function DecisionPanel({
  decision,
  nsQueue,
  ewQueue,
  threshold,
  currentPhase,
  phaseElapsed,
}) {
  const exceedsThreshold = Math.abs(decision.difference) > threshold;

  return (
    <section className="glass-panel relative overflow-hidden p-5">
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-400/10 via-transparent to-blue-500/10" />
      <div className="relative">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="panel-title">Current Decision</p>
            <h2 className="mt-1 text-xl font-black text-white">Priority Control Engine</h2>
          </div>
          <div className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 p-3 text-cyan-200 shadow-glow">
            <BrainCircuit className="h-6 w-6" />
          </div>
        </div>

        <div className="mt-5 rounded-2xl border border-white/10 bg-slate-950/50 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="subtle-label">Selected Direction</p>
              <p className="mt-1 text-2xl font-black text-emerald-200">{decision.selectedDirection}</p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-400/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-emerald-200">
              <CheckCircle2 className="h-4 w-4" />
              Live Decision
            </span>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {[
            ['North-South Queue', `${nsQueue} vehicles`],
            ['East-West Queue', `${ewQueue} vehicles`],
            ['Queue Difference', `${Math.abs(decision.difference)} vehicles`],
            ['Hysteresis Threshold', `${threshold} vehicles`],
            ['Current Phase', currentPhase],
            ['Phase Timer', formatPhaseTime(phaseElapsed)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.035] p-3">
              <p className="subtle-label">{label}</p>
              <p className="mt-1 text-lg font-bold text-white">{value}</p>
            </div>
          ))}
        </div>

        <div
          className={`mt-5 rounded-2xl border p-4 ${
            exceedsThreshold ? 'border-emerald-300/15 bg-emerald-400/10' : 'border-cyan-300/15 bg-cyan-400/10'
          }`}
        >
          <div className="flex items-start gap-3">
            <TrafficCone className="mt-0.5 h-5 w-5 shrink-0 text-emerald-200" />
            <div>
              <p className="font-bold text-emerald-100">Decision: {decision.decision}</p>
              <p className="mt-2 text-sm leading-6 text-slate-300">{decision.explanation}</p>
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-cyan-100/70">
          <GitBranch className="h-4 w-4" />
          {'sensor_node -> controller_node -> actuator_node -> dashboard_node'}
        </div>
      </div>
    </section>
  );
}
