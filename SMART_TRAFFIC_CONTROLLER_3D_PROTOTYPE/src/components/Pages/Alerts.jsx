import { AlertTriangle, CheckCircle2, ShieldAlert, WifiOff } from 'lucide-react';
import SafetyMonitor from '../SafetyMonitor.jsx';

export default function Alerts({ traffic }) {
  return (
    <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <SafetyMonitor safety={traffic.safety} />
      <section className="glass-panel p-5">
        <div className="mb-5 flex items-center justify-between">
          <div>
            <p className="panel-title">Alerts</p>
            <h2 className="mt-1 text-xl font-black text-white">Safety and Communication Events</h2>
          </div>
          <AlertTriangle className="h-6 w-6 text-yellow-100" />
        </div>
        <div className="mb-4 flex flex-wrap gap-3">
          <button className="inline-flex items-center gap-2 rounded-xl border border-yellow-300/20 bg-yellow-400/10 px-4 py-2 font-bold text-yellow-100" onClick={traffic.controls.simulateSafetyViolation} type="button">
            <ShieldAlert className="h-4 w-4" />
            Simulate safety violation
          </button>
          <button className="inline-flex items-center gap-2 rounded-xl border border-red-300/20 bg-red-400/10 px-4 py-2 font-bold text-red-100" onClick={traffic.controls.injectSensorFault} type="button">
            <WifiOff className="h-4 w-4" />
            Simulate sensor fault
          </button>
          <button className="rounded-xl border border-slate-400/20 bg-white/5 px-4 py-2 font-bold text-slate-200" onClick={traffic.controls.clearAlerts} type="button">
            Clear alerts
          </button>
        </div>
        {traffic.alerts.length === 0 ? (
          <div className="flex items-center gap-3 rounded-2xl border border-emerald-300/20 bg-emerald-400/10 p-5 text-emerald-100">
            <CheckCircle2 className="h-6 w-6" />
            <p className="font-bold">No active alerts</p>
          </div>
        ) : (
          <div className="space-y-3">
            {traffic.alerts.map((alert) => (
              <article key={alert.id} className={`rounded-2xl border p-4 ${
                alert.severity === 'critical'
                  ? 'border-red-300/20 bg-red-400/10'
                  : alert.severity === 'info'
                    ? 'border-cyan-300/20 bg-cyan-400/10'
                    : 'border-yellow-300/20 bg-yellow-400/10'
              }`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-black uppercase tracking-[0.16em] text-white">{alert.type}</p>
                    <p className="mt-2 text-sm text-slate-200">{alert.message}</p>
                  </div>
                  <span className="font-mono text-xs text-slate-400">{alert.time}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
