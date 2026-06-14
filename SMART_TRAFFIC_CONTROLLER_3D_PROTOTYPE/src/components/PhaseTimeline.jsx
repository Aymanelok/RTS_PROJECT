const timelineRows = [
  {
    label: 'Phase 1: EAST-WEST',
    segments: [
      { left: 0, width: 28, color: 'bg-emerald-400' },
      { left: 28, width: 6, color: 'bg-yellow-300' },
      { left: 34, width: 66, color: 'bg-red-500/75' },
    ],
  },
  {
    label: 'Phase 2: NORTH-SOUTH',
    segments: [
      { left: 0, width: 34, color: 'bg-red-500/75' },
      { left: 34, width: 34, color: 'bg-emerald-400' },
      { left: 68, width: 6, color: 'bg-yellow-300' },
      { left: 74, width: 26, color: 'bg-red-500/75' },
    ],
  },
  {
    label: 'Phase 3: EAST-WEST',
    segments: [
      { left: 0, width: 74, color: 'bg-red-500/75' },
      { left: 74, width: 18, color: 'bg-emerald-400' },
      { left: 92, width: 5, color: 'bg-yellow-300' },
    ],
  },
  {
    label: 'Phase 4: ALL RED CLEARANCE',
    segments: [
      { left: 32, width: 4, color: 'bg-slate-500' },
      { left: 96, width: 4, color: 'bg-slate-500' },
    ],
  },
];

export default function PhaseTimeline({ nowPosition }) {
  return (
    <section className="glass-panel p-5">
      <div className="mb-8 flex items-center justify-between gap-3">
        <div>
          <p className="panel-title">Phase Timeline</p>
          <h2 className="mt-1 text-lg font-black text-white">Gantt Program View</h2>
        </div>
        <div className="hidden gap-2 text-xs text-slate-300 sm:flex">
          <span className="rounded-full bg-emerald-400/20 px-2 py-1 text-emerald-100">Green</span>
          <span className="rounded-full bg-yellow-300/20 px-2 py-1 text-yellow-100">Transition</span>
          <span className="rounded-full bg-red-500/20 px-2 py-1 text-red-100">Red</span>
          <span className="rounded-full bg-slate-500/25 px-2 py-1 text-slate-200">Clearance</span>
        </div>
      </div>
      <div className="space-y-4">
        {timelineRows.map((row) => (
          <div key={row.label} className="grid gap-3 md:grid-cols-[12rem_1fr] md:items-center">
            <p className="text-sm font-bold text-slate-200">{row.label}</p>
            <div className="timeline-track">
              <div className="timeline-now" style={{ left: `${nowPosition}%` }} />
              {row.segments.map((segment, index) => (
                <span
                  key={`${row.label}-${index}`}
                  className={`timeline-segment ${segment.color}`}
                  style={{ left: `${segment.left}%`, width: `${segment.width}%` }}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
