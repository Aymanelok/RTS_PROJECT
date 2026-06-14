import { CalendarDays, CloudSun, RadioTower, ShieldCheck } from 'lucide-react';

const formatDate = (date) =>
  new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: '2-digit',
    year: 'numeric',
  }).format(date);

const formatTime = (date) =>
  new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }).format(date);

export default function Header({ now }) {
  return (
    <header className="sticky top-0 z-40 border-b border-cyan-300/10 bg-slate-950/70 px-4 py-4 backdrop-blur-2xl lg:px-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex items-center gap-4">
          <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyan-300/25 bg-cyan-300/10 text-cyan-200 shadow-glow">
            <RadioTower className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-xl font-black tracking-[0.18em] text-white md:text-2xl">
                SMART TRAFFIC CONTROLLER
              </h1>
              <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/25 bg-emerald-400/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-emerald-200 shadow-greenGlow">
                <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-300" />
                SYSTEM ONLINE
              </span>
            </div>
            <p className="mt-1 text-sm font-medium text-cyan-100/70">
              Adaptive • Connected • Safe
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 md:flex md:items-center">
          <div className="glass-panel flex items-center gap-3 rounded-2xl px-4 py-3">
            <CloudSun className="h-5 w-5 text-yellow-200" />
            <div>
              <p className="subtle-label">Weather</p>
              <p className="font-bold text-white">28°C</p>
            </div>
          </div>
          <div className="glass-panel flex items-center gap-3 rounded-2xl px-4 py-3">
            <CalendarDays className="h-5 w-5 text-cyan-200" />
            <div>
              <p className="subtle-label">{formatDate(now)}</p>
              <p className="font-mono text-lg font-bold text-white">{formatTime(now)}</p>
            </div>
          </div>
          <div className="glass-panel col-span-2 flex items-center gap-3 rounded-2xl px-4 py-3 md:col-span-1">
            <ShieldCheck className="h-5 w-5 text-emerald-300" />
            <div>
              <p className="subtle-label">Safety Monitor</p>
              <p className="font-bold text-emerald-200">No conflicts detected</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
