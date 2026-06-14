import { AlertTriangle, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function SafetyMonitor({ safety }) {
  const warning = safety.status !== 'SAFE';
  const rows = [
    ['Violations', safety.violations],
    ['Signal Conflicts', safety.signalConflicts],
    ['Red Light Violations', safety.redLightViolations],
    ['Sensor Faults', safety.sensorFaults],
    ['Communication Errors', safety.communicationErrors],
  ];

  return (
    <section
      className={`glass-panel relative overflow-hidden p-5 ${
        warning ? 'border-yellow-300/30 shadow-[0_0_32px_rgba(250,204,21,0.18)]' : 'border-emerald-300/20 shadow-greenGlow'
      }`}
    >
      <div
        className={`absolute inset-0 ${
          warning
            ? 'bg-[radial-gradient(circle_at_top_right,rgba(250,204,21,0.18),transparent_18rem)]'
            : 'bg-[radial-gradient(circle_at_top_right,rgba(34,197,94,0.18),transparent_18rem)]'
        }`}
      />
      <div className="relative">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className={`panel-title ${warning ? 'text-yellow-100/90' : 'text-emerald-100/90'}`}>
              Safety Monitor
            </p>
            <h2 className="mt-1 text-xl font-black text-white">Fail-Safe Interlock</h2>
          </div>
          <div
            className={`rounded-2xl border p-3 ${
              warning
                ? 'border-yellow-300/25 bg-yellow-400/15 text-yellow-100'
                : 'border-emerald-300/25 bg-emerald-400/15 text-emerald-200'
            }`}
          >
            <ShieldCheck className="h-6 w-6" />
          </div>
        </div>

        <div
          className={`my-6 flex items-center gap-5 rounded-3xl border p-5 ${
            warning
              ? 'border-yellow-300/20 bg-yellow-400/10'
              : 'border-emerald-300/20 bg-emerald-400/10'
          }`}
        >
          <div
            className={`grid h-20 w-20 shrink-0 place-items-center rounded-full border ${
              warning
                ? 'border-yellow-300/30 bg-yellow-400/15 text-yellow-100'
                : 'border-emerald-300/30 bg-emerald-400/15 text-emerald-200 shadow-greenGlow'
            }`}
          >
            {warning ? <AlertTriangle className="h-12 w-12" /> : <CheckCircle2 className="h-12 w-12" />}
          </div>
          <div>
            <p className="subtle-label">Status</p>
            <p className={`text-4xl font-black ${warning ? 'text-yellow-100' : 'text-emerald-100'}`}>
              {safety.status}
            </p>
            <p className={`mt-1 text-sm ${warning ? 'text-yellow-100/75' : 'text-emerald-100/70'}`}>
              {safety.message}
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          {rows.map(([label, value]) => (
            <div
              key={label}
              className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3"
            >
              <span className="text-sm text-slate-300">{label}</span>
              <span
                className={`rounded-full px-3 py-1 font-mono text-sm font-black ${
                  value > 0 ? 'bg-yellow-400/10 text-yellow-100' : 'bg-emerald-400/10 text-emerald-200'
                }`}
              >
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
