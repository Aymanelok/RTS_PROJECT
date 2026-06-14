import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, CarFront } from 'lucide-react';

const directionIcons = {
  north: ArrowUp,
  south: ArrowDown,
  east: ArrowRight,
  west: ArrowLeft,
};

const colorMap = {
  green: 'from-emerald-400 to-green-500 text-emerald-200 border-emerald-300/20',
  cyan: 'from-cyan-400 to-blue-500 text-cyan-200 border-cyan-300/20',
  yellow: 'from-yellow-300 to-amber-500 text-yellow-100 border-yellow-300/20',
  red: 'from-red-400 to-rose-500 text-red-100 border-red-300/20',
};

export default function QueueCard({ direction, label, value, max, color }) {
  const DirectionIcon = directionIcons[direction];
  const progress = Math.min(100, Math.round((value / max) * 100));

  return (
    <article className={`glass-panel border p-4 ${colorMap[color].split(' ').slice(2).join(' ')}`}>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="subtle-label">{label}</p>
          <div className="mt-2 flex items-end gap-2">
            <p className="text-3xl font-black text-white">{value}</p>
            <span className="pb-1 text-xs text-slate-400">/ {max} max</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/5 text-slate-200">
            <DirectionIcon className="h-5 w-5" />
          </div>
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/5 text-slate-200">
            <CarFront className="h-5 w-5" />
          </div>
        </div>
      </div>
      <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-slate-800/80">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${colorMap[color].split(' ').slice(0, 2).join(' ')} shadow-glow transition-all duration-500`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </article>
  );
}
