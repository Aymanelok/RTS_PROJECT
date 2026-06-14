import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import ChartFrame from './ChartFrame.jsx';

export default function LatencyChart({ data }) {
  return (
    <section className="glass-panel min-w-0 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="panel-title">E2E Latency</p>
          <h2 className="mt-1 text-lg font-black text-white">Control Loop Timing</h2>
        </div>
        <span className="rounded-full border border-red-300/20 bg-red-400/10 px-3 py-1 text-xs font-bold text-red-100">
          Threshold 200 ms
        </span>
      </div>
      <ChartFrame className="h-72 min-w-0">
        {({ width, height }) => (
          <LineChart data={data} height={height} margin={{ top: 10, right: 16, left: -18, bottom: 0 }} width={width}>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="4 4" />
            <XAxis dataKey="time" tickLine={false} axisLine={false} minTickGap={22} />
            <YAxis domain={[60, 220]} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                background: 'rgba(2, 6, 23, 0.92)',
                border: '1px solid rgba(125, 211, 252, 0.18)',
                borderRadius: 14,
              }}
            />
            <ReferenceLine
              y={200}
              stroke="#ef4444"
              strokeDasharray="7 7"
              label={{ value: '200 ms threshold', position: 'insideTopRight', fill: '#fecaca' }}
            />
            <Line
              type="monotone"
              dataKey="latency"
              name="Latency"
              stroke="#38bdf8"
              strokeWidth={3}
              dot={false}
              isAnimationActive
            />
          </LineChart>
        )}
      </ChartFrame>
    </section>
  );
}
