import { Cpu, HardDrive, Radio, Wifi } from 'lucide-react';

export default function Devices({ nodeMetrics }) {
  return (
    <div className="grid gap-5 lg:grid-cols-2 2xl:grid-cols-4">
      {nodeMetrics.map((node) => (
        <article key={node.node} className="glass-panel p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="panel-title">{node.node}</p>
              <h2 className="mt-1 text-xl font-black text-white">ONLINE</h2>
            </div>
            <div className="rounded-2xl border border-emerald-300/20 bg-emerald-400/10 p-3 text-emerald-200">
              <Wifi className="h-6 w-6" />
            </div>
          </div>
          <div className="mt-5 grid gap-3">
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.035] p-3">
              <span className="inline-flex items-center gap-2 text-slate-300"><Cpu className="h-4 w-4" /> CPU</span>
              <span className="font-mono font-black text-white">{node.usage}%</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.035] p-3">
              <span className="inline-flex items-center gap-2 text-slate-300"><HardDrive className="h-4 w-4" /> RAM</span>
              <span className="font-mono font-black text-white">{node.ram}%</span>
            </div>
            <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.035] p-3">
              <span className="inline-flex items-center gap-2 text-slate-300"><Radio className="h-4 w-4" /> Messages/sec</span>
              <span className="font-mono font-black text-white">{node.messages}</span>
            </div>
            <div className="rounded-2xl border border-cyan-300/10 bg-cyan-300/5 p-3">
              <p className="subtle-label">Last update</p>
              <p className="mt-1 font-mono font-bold text-cyan-100">{node.lastUpdate}</p>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}
