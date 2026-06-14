import {
  Ambulance,
  Pause,
  Play,
  RotateCcw,
  ShieldAlert,
  TimerReset,
  XCircle,
  Zap,
} from 'lucide-react';

const speedOptions = [1, 2, 4];

export default function ControlBar({ traffic }) {
  const { controls, isRunning, mode, settings } = traffic;

  return (
    <section className="glass-panel flex flex-wrap items-center gap-3 p-4">
      <button
        className="inline-flex items-center gap-2 rounded-xl border border-emerald-300/20 bg-emerald-400/10 px-3 py-2 text-sm font-bold text-emerald-100 transition hover:bg-emerald-400/20"
        onClick={controls.startSimulation}
        type="button"
      >
        <Play className="h-4 w-4" />
        Start
      </button>
      <button
        className="inline-flex items-center gap-2 rounded-xl border border-yellow-300/20 bg-yellow-400/10 px-3 py-2 text-sm font-bold text-yellow-100 transition hover:bg-yellow-400/20"
        onClick={controls.pauseSimulation}
        type="button"
      >
        <Pause className="h-4 w-4" />
        Pause
      </button>
      <button
        className="inline-flex items-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-400/10 px-3 py-2 text-sm font-bold text-cyan-100 transition hover:bg-cyan-400/20"
        onClick={controls.resetSimulation}
        type="button"
      >
        <RotateCcw className="h-4 w-4" />
        Reset
      </button>

      <div className="h-8 w-px bg-white/10" />

      <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/40 p-1">
        {speedOptions.map((speed) => (
          <button
            key={speed}
            className={`rounded-lg px-3 py-1.5 text-sm font-black transition ${
              settings.simulationSpeed === speed
                ? 'bg-cyan-300/15 text-cyan-100 shadow-glow'
                : 'text-slate-400 hover:bg-white/5 hover:text-white'
            }`}
            onClick={() => controls.setSimulationSpeed(speed)}
            type="button"
          >
            {speed}x
          </button>
        ))}
      </div>

      <button
        className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-bold transition ${
          mode === 'auto'
            ? 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100'
            : 'border-slate-500/20 bg-slate-500/10 text-slate-200'
        }`}
        onClick={() => controls.returnToAutomatic()}
        type="button"
      >
        <TimerReset className="h-4 w-4" />
        Auto mode
      </button>
      <button
        className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-bold transition ${
          mode === 'manual'
            ? 'border-blue-300/20 bg-blue-400/10 text-blue-100'
            : 'border-slate-500/20 bg-slate-500/10 text-slate-200'
        }`}
        onClick={() => controls.setMode('manual')}
        type="button"
      >
        <Zap className="h-4 w-4" />
        Manual mode
      </button>
      <button
        className="inline-flex items-center gap-2 rounded-xl border border-red-300/20 bg-red-400/10 px-3 py-2 text-sm font-bold text-red-100 transition hover:bg-red-400/20"
        onClick={controls.triggerEmergencyVehicle}
        type="button"
      >
        <Ambulance className="h-4 w-4" />
        Trigger emergency
      </button>
      <button
        className="inline-flex items-center gap-2 rounded-xl border border-yellow-300/20 bg-yellow-400/10 px-3 py-2 text-sm font-bold text-yellow-100 transition hover:bg-yellow-400/20"
        onClick={controls.simulateSafetyViolation}
        type="button"
      >
        <ShieldAlert className="h-4 w-4" />
        Test safety
      </button>
      <button
        className="inline-flex items-center gap-2 rounded-xl border border-slate-400/20 bg-white/5 px-3 py-2 text-sm font-bold text-slate-200 transition hover:bg-white/10"
        onClick={controls.clearAlerts}
        type="button"
      >
        <XCircle className="h-4 w-4" />
        Clear alerts
      </button>

      <span className="ml-auto rounded-full border border-white/10 bg-slate-950/50 px-3 py-1 text-xs font-bold uppercase tracking-[0.16em] text-slate-300">
        {isRunning ? 'Simulation running' : 'Simulation paused'}
      </span>
    </section>
  );
}
