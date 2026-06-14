import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts';
import ChartFrame from '../ChartFrame.jsx';

export default function CPUChart({ data }) {
  return (
    <section className="glass-panel min-w-0 p-5">
      <div className="mb-4">
        <p className="panel-title">CPU Usage by Node</p>
        <h2 className="mt-1 text-lg font-black text-white">ROS2 Process Load</h2>
      </div>
      <ChartFrame className="h-72 min-w-0">
        {({ width, height }) => (
          <BarChart data={data} height={height} margin={{ top: 10, right: 12, left: -18, bottom: 0 }} width={width}>
            <defs>
              <linearGradient id="cpuBarGradient" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#67e8f9" />
                <stop offset="100%" stopColor="#2563eb" />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="4 4" vertical={false} />
            <XAxis dataKey="node" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} unit="%" />
            <Tooltip contentStyle={{ background: 'rgba(2, 6, 23, 0.92)', border: '1px solid rgba(125, 211, 252, 0.18)', borderRadius: 14 }} />
            <Bar dataKey="usage" name="CPU" radius={[10, 10, 4, 4]} fill="url(#cpuBarGradient)" />
          </BarChart>
        )}
      </ChartFrame>
    </section>
  );
}
