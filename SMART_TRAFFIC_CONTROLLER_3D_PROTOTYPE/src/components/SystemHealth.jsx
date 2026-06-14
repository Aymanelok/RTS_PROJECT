import { Cell, Pie, PieChart, Tooltip } from 'recharts';
import ChartFrame from './ChartFrame.jsx';

const colors = ['#22c55e', '#22d3ee', '#60a5fa', '#facc15'];

export default function SystemHealth({ data }) {
  const averageScore = Math.round(data.reduce((sum, item) => sum + item.score, 0) / data.length);

  return (
    <section className="glass-panel min-w-0 p-5">
      <div className="mb-4">
        <p className="panel-title">System Health</p>
        <h2 className="mt-1 text-lg font-black text-white">Subsystem Availability</h2>
      </div>
      <div className="grid items-center gap-4 sm:grid-cols-[1fr_0.9fr]">
        <div className="relative h-64 min-w-0">
          <ChartFrame className="h-full min-w-0">
            {({ width, height }) => (
              <PieChart height={height} width={width}>
                <Pie data={data} dataKey="value" innerRadius="62%" outerRadius="88%" paddingAngle={4}>
                  {data.map((entry, index) => (
                    <Cell key={entry.name} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(_, __, item) => [`${item.payload.score}%`, item.payload.name]}
                  contentStyle={{
                    background: 'rgba(2, 6, 23, 0.92)',
                    border: '1px solid rgba(125, 211, 252, 0.18)',
                    borderRadius: 14,
                  }}
                />
              </PieChart>
            )}
          </ChartFrame>
          <div className="pointer-events-none absolute inset-0 grid place-items-center">
            <div className="text-center">
              <p className="text-4xl font-black text-white">{averageScore}%</p>
              <p className="subtle-label">Healthy</p>
            </div>
          </div>
        </div>
        <div className="space-y-3">
          {data.map((item, index) => (
            <div key={item.name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.035] px-4 py-3">
              <div className="flex items-center gap-3">
                <span className="h-3 w-3 rounded-full" style={{ background: colors[index] }} />
                <span className="text-sm font-semibold text-slate-200">{item.name}</span>
              </div>
              <span className="font-mono text-sm font-black text-emerald-200">{item.score}%</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
