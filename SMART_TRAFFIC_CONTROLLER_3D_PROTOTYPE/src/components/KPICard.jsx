export default function KPICard({ icon: Icon, title, value, description, tone = 'cyan' }) {
  const toneClasses = {
    cyan: 'from-cyan-400/20 text-cyan-200 border-cyan-300/20',
    blue: 'from-blue-400/20 text-blue-200 border-blue-300/20',
    green: 'from-emerald-400/20 text-emerald-200 border-emerald-300/20',
    yellow: 'from-yellow-400/20 text-yellow-100 border-yellow-300/20',
    red: 'from-red-400/20 text-red-100 border-red-300/20',
    violet: 'from-violet-400/20 text-violet-100 border-violet-300/20',
  };

  return (
    <article className="glass-panel group relative overflow-hidden p-4">
      <div className={`absolute inset-0 bg-gradient-to-br ${toneClasses[tone]} to-transparent opacity-80`} />
      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className="subtle-label">{title}</p>
          <p className="mt-2 text-2xl font-black tracking-tight text-white">{value}</p>
          <p className="mt-1 text-xs text-slate-400">{description}</p>
        </div>
        <div className={`rounded-2xl border bg-slate-950/50 p-3 ${toneClasses[tone]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </article>
  );
}
