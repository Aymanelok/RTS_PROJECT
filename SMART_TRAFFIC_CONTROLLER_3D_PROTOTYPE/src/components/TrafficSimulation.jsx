import { Compass, ShieldCheck, Timer } from 'lucide-react';
import TrafficScene from './traffic3d/TrafficScene.jsx';
import { formatPhaseTime } from '../utils/trafficLogic.js';

const statusColor = {
  green: 'bg-emerald-400 shadow-greenGlow',
  red: 'bg-red-500 shadow-redGlow',
  yellow: 'bg-yellow-300 shadow-[0_0_24px_rgba(250,204,21,0.38)]',
  gray: 'bg-slate-500',
};

const directionLabel = {
  north: 'North',
  south: 'South',
  east: 'East',
  west: 'West',
};

export default function TrafficSimulation({
  cars,
  signals,
  activeAxis,
  activePhase,
  phaseTone = 'green',
  phaseElapsed = 0,
  phaseDuration = 0,
  className = '',
  compact = false,
}) {
  const remaining = Math.max(0, phaseDuration - phaseElapsed);
  const movingCount = cars.filter((car) => car.state === 'moving').length;
  const waitingCount = cars.filter((car) => car.state === 'waiting').length;
  const crossingCount = cars.filter((car) => car.state === 'crossing').length;
  const samplePositions = cars
    .slice(0, 10)
    .map((car) => `${car.id}:${car.x.toFixed(2)},${car.y.toFixed(2)},${car.state}`)
    .join('|');
  const trafficSnapshot = JSON.stringify(
    cars.map((car) => ({
      id: car.id,
      direction: car.direction,
      x: Number(car.x.toFixed(2)),
      y: Number(car.y.toFixed(2)),
      state: car.state,
      hasCrossedStopLine: car.hasCrossedStopLine,
      hasEnteredIntersection: car.hasEnteredIntersection,
    })),
  );

  return (
    <section className={`glass-panel traffic-grid overflow-hidden p-4 ${className}`}>
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="panel-title">3D Traffic Simulation</p>
          <h2 className="mt-1 text-xl font-black text-white">Near-Realistic Smart Intersection</h2>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-300">
          <span
            className={`rounded-full border px-3 py-1 ${
              phaseTone === 'yellow'
                ? 'border-yellow-300/30 bg-yellow-300/10 text-yellow-100'
                : phaseTone === 'red'
                  ? 'border-red-300/30 bg-red-400/10 text-red-100'
                  : 'border-emerald-300/20 bg-emerald-400/10 text-emerald-200'
            }`}
          >
            Active phase: {activePhase}
          </span>
          <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-cyan-200">
            <Timer className="h-3.5 w-3.5" />
            {formatPhaseTime(remaining)} remaining
          </span>
          <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-cyan-200">
            {cars.length} vehicles tracked
          </span>
        </div>
      </div>

      <div
        className={`scene-3d relative ${compact ? 'h-[520px]' : 'h-[650px]'}`}
        data-active-axis={activeAxis}
        data-car-count={cars.length}
        data-crossing-count={crossingCount}
        data-moving-count={movingCount}
        data-phase={activePhase}
        data-phase-tone={phaseTone}
        data-sample-positions={samplePositions}
        data-traffic-snapshot={trafficSnapshot}
        data-waiting-count={waitingCount}
      >
        <TrafficScene activeAxis={activeAxis} cars={cars} phaseTone={phaseTone} signals={signals} />

        <div className="pointer-events-none absolute right-4 top-4 z-20 rounded-2xl border border-cyan-300/20 bg-slate-950/75 p-3 shadow-glow backdrop-blur-xl">
          <div className="flex items-center gap-2 text-cyan-100">
            <Compass className="h-5 w-5" />
            <span className="text-lg font-black">N</span>
          </div>
        </div>

        <div className="pointer-events-none absolute bottom-4 left-4 z-20 max-w-[92%] rounded-2xl border border-white/10 bg-slate-950/75 p-3 text-xs text-slate-300 shadow-2xl backdrop-blur-xl">
          <div className="mb-2 flex items-center gap-2 font-bold text-white">
            <ShieldCheck className="h-4 w-4 text-emerald-300" />
            3D Signal Legend
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {[
              ['green', 'Active Direction'],
              ['red', 'Red Signal'],
              ['yellow', 'Transition'],
              ['gray', 'All Red'],
            ].map(([color, label]) => (
              <div key={color} className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${statusColor[color]}`} />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="pointer-events-none absolute right-4 bottom-4 z-20 hidden rounded-2xl border border-white/10 bg-slate-950/70 p-3 text-xs text-slate-300 backdrop-blur-xl sm:block">
          {Object.entries(signals).map(([direction, signal]) => (
            <div key={direction} className="flex min-w-32 items-center justify-between gap-4 py-1">
              <span>{directionLabel[direction]}</span>
              <span className={`h-2.5 w-2.5 rounded-full ${statusColor[signal] || statusColor.gray}`} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
