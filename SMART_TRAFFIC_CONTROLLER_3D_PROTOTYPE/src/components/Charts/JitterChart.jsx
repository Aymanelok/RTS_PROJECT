import { Area, AreaChart, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts';
import ChartFrame from '../ChartFrame.jsx';

export default function JitterChart({ data }) {
  return (
    <section className="glass-panel min-w-0 p-5">
      <div className="mb-4">
        <p className="panel-title">Jitter</p>
        <h2 className="mt-1 text-lg font-black text-white">Loop Variation</h2>
      </div>
      <ChartFrame className="h-72 min-w-0">
        {({ width, height }) => (
          <AreaChart data={data} height={height} margin={{ top: 10, right: 16, left: -18, bottom: 0 }} width={width}>
            <defs>
              <linearGradient id="jitterFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.38} />
                <stop offset="100%" stopColor="#a78bfa" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="4 4" />
            <XAxis dataKey="time" tickLine={false} axisLine={false} minTickGap={22} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: 'rgba(2, 6, 23, 0.92)', border: '1px solid rgba(125, 211, 252, 0.18)', borderRadius: 14 }} />
            <Area activeDot={{ r: 5 }} dataKey="jitter" fill="url(#jitterFill)" name="Jitter" stroke="#a78bfa" strokeLinecap="round" strokeWidth={3.2} type="monotone" />
          </AreaChart>
        )}
      </ChartFrame>
    </section>
  );
}
