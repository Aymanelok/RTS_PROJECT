import { CheckCircle2, RadioTower, ShieldAlert } from 'lucide-react';
import TrafficLight from '../TrafficLight.jsx';
import { DIRECTION_LABELS } from '../../utils/trafficLogic.js';

const statusClasses = {
  green: 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100',
  yellow: 'border-yellow-300/20 bg-yellow-400/10 text-yellow-100',
  red: 'border-red-300/20 bg-red-400/10 text-red-100',
};

export default function Signals({ traffic }) {
  const { controls } = traffic;

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_0.9fr]">
      <section className="glass-panel p-5">
        <div className="mb-5">
          <p className="panel-title">Traffic Light Status</p>
          <h2 className="mt-1 text-xl font-black text-white">Live Signal Matrix</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {Object.entries(traffic.signals).map(([direction, signal]) => (
            <article key={direction} className={`relative min-h-40 rounded-2xl border p-4 ${statusClasses[signal]}`}>
              <TrafficLight className="!relative !left-auto !top-auto" label={direction} status={signal} />
              <div className="absolute right-4 top-4 text-right">
                <p className="subtle-label">{DIRECTION_LABELS[direction]}</p>
                <p className="mt-1 text-2xl font-black uppercase">{signal}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="glass-panel p-5">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="panel-title">Manual Controls</p>
            <h2 className="mt-1 text-xl font-black text-white">Signal Override Panel</h2>
          </div>
          <RadioTower className="h-6 w-6 text-cyan-200" />
        </div>
        <div className="grid gap-3">
          <button className="rounded-2xl border border-emerald-300/20 bg-emerald-400/10 px-4 py-3 text-left font-bold text-emerald-100 hover:bg-emerald-400/20" onClick={controls.forceNorthSouthGreen} type="button">
            Force North-South green
          </button>
          <button className="rounded-2xl border border-emerald-300/20 bg-emerald-400/10 px-4 py-3 text-left font-bold text-emerald-100 hover:bg-emerald-400/20" onClick={controls.forceEastWestGreen} type="button">
            Force East-West green
          </button>
          <button className="rounded-2xl border border-yellow-300/20 bg-yellow-400/10 px-4 py-3 text-left font-bold text-yellow-100 hover:bg-yellow-400/20" onClick={controls.forceYellowTransition} type="button">
            Force yellow transition
          </button>
          <button className="rounded-2xl border border-red-300/20 bg-red-400/10 px-4 py-3 text-left font-bold text-red-100 hover:bg-red-400/20" onClick={controls.forceAllRed} type="button">
            Force all red
          </button>
          <button className="rounded-2xl border border-cyan-300/20 bg-cyan-400/10 px-4 py-3 text-left font-bold text-cyan-100 hover:bg-cyan-400/20" onClick={controls.returnToAutomatic} type="button">
            Return to automatic mode
          </button>
          <button className="rounded-2xl border border-yellow-300/20 bg-yellow-400/10 px-4 py-3 text-left font-bold text-yellow-100 hover:bg-yellow-400/20" onClick={controls.simulateSafetyViolation} type="button">
            <span className="inline-flex items-center gap-2">
              <ShieldAlert className="h-4 w-4" />
              Attempt unsafe conflicting green
            </span>
          </button>
        </div>
        <div className="mt-5 flex items-center gap-2 rounded-2xl border border-emerald-300/20 bg-emerald-400/10 p-4 text-sm text-emerald-100">
          <CheckCircle2 className="h-5 w-5" />
          Manual commands are validated before reaching the actuator.
        </div>
      </section>
    </div>
  );
}
