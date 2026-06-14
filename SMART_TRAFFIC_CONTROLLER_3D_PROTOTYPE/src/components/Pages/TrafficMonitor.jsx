import { CarFront, Timer } from 'lucide-react';
import ControlBar from '../ControlBar.jsx';
import QueueCard from '../QueueCard.jsx';
import TrafficSimulation from '../TrafficSimulation.jsx';
import { DIRECTION_LABELS, formatPhaseTime } from '../../utils/trafficLogic.js';

const queueConfig = [
  { direction: 'north', label: 'NORTH', color: 'green' },
  { direction: 'south', label: 'SOUTH', color: 'cyan' },
  { direction: 'east', label: 'EAST', color: 'yellow' },
  { direction: 'west', label: 'WEST', color: 'red' },
];

export default function TrafficMonitor({ traffic }) {
  const visibleCars = traffic.cars.slice(0, 18);

  return (
    <div className="space-y-5">
      <ControlBar traffic={traffic} />
      <div className="grid gap-5 xl:grid-cols-[1.3fr_0.7fr]">
        <TrafficSimulation
          activeAxis={traffic.activeAxis}
          activePhase={traffic.phaseLabel}
          cars={traffic.cars}
          className="xl:col-span-1"
          phaseDuration={traffic.phaseDuration}
          phaseElapsed={traffic.phaseElapsed}
          phaseTone={traffic.phaseTone}
          signals={traffic.signals}
        />
        <section className="glass-panel p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="panel-title">Current Phase</p>
              <h2 className="mt-1 text-2xl font-black text-white">{traffic.phaseLabel}</h2>
            </div>
            <Timer className="h-7 w-7 text-cyan-200" />
          </div>
          <div className="mt-5 grid gap-3">
            <div className="rounded-2xl border border-cyan-300/10 bg-cyan-300/5 p-4">
              <p className="subtle-label">Phase Timer</p>
              <p className="mt-1 text-4xl font-black text-white">{formatPhaseTime(traffic.phaseElapsed)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
              <p className="subtle-label">Mode</p>
              <p className="mt-1 text-xl font-black text-emerald-100">{traffic.mode.toUpperCase()}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
              <p className="subtle-label">Throughput</p>
              <p className="mt-1 text-xl font-black text-white">{traffic.throughput} vehicles exited</p>
            </div>
          </div>
        </section>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {queueConfig.map((item) => (
          <QueueCard key={item.direction} {...item} max={24} value={traffic.queues[item.direction]} />
        ))}
      </div>

      <section className="glass-panel overflow-hidden p-5">
        <div className="mb-4 flex items-center gap-3">
          <CarFront className="h-5 w-5 text-cyan-200" />
          <div>
            <p className="panel-title">Vehicle List</p>
            <h2 className="mt-1 text-lg font-black text-white">Tracked Vehicles</h2>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="text-xs uppercase tracking-[0.16em] text-slate-400">
              <tr>
                <th className="py-3">ID</th>
                <th>Direction</th>
                <th>Type</th>
                <th>State</th>
                <th>Speed</th>
                <th>Distance to Stop</th>
                <th>Wait Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {visibleCars.map((car) => (
                <tr key={car.id} className="text-slate-200">
                  <td className="py-3 font-mono text-xs text-cyan-100">{car.id.slice(0, 18)}</td>
                  <td>{DIRECTION_LABELS[car.direction]}</td>
                  <td className="capitalize">{car.type}</td>
                  <td className="capitalize">{car.state}</td>
                  <td>{car.speed.toFixed(1)} %/s</td>
                  <td>{car.distanceToStopLine.toFixed(1)}%</td>
                  <td>{car.waitTime.toFixed(1)}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
