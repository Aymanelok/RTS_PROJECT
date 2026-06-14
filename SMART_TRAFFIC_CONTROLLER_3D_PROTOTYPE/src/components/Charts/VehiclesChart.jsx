import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import ChartFrame from '../ChartFrame.jsx';

export default function VehiclesChart({ data }) {
  return (
    <section className="glass-panel min-w-0 p-5">
      <div className="mb-4">
        <p className="panel-title">Vehicles per Direction</p>
        <h2 className="mt-1 text-lg font-black text-white">Live Queue Evolution</h2>
      </div>
      <ChartFrame className="h-72 min-w-0">
        {({ width, height }) => (
          <LineChart data={data} height={height} margin={{ top: 10, right: 16, left: -18, bottom: 0 }} width={width}>
            <defs>
              <filter id="lineGlow" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="4 4" />
            <XAxis dataKey="time" tickLine={false} axisLine={false} minTickGap={22} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: 'rgba(2, 6, 23, 0.92)', border: '1px solid rgba(125, 211, 252, 0.18)', borderRadius: 14 }} />
            <Legend />
            <Line activeDot={{ r: 5 }} dot={false} filter="url(#lineGlow)" stroke="#22c55e" strokeLinecap="round" strokeWidth={3.2} type="monotone" dataKey="north" name="North" />
            <Line activeDot={{ r: 5 }} dot={false} filter="url(#lineGlow)" stroke="#22d3ee" strokeLinecap="round" strokeWidth={3.2} type="monotone" dataKey="south" name="South" />
            <Line activeDot={{ r: 5 }} dot={false} filter="url(#lineGlow)" stroke="#facc15" strokeLinecap="round" strokeWidth={3.2} type="monotone" dataKey="east" name="East" />
            <Line activeDot={{ r: 5 }} dot={false} filter="url(#lineGlow)" stroke="#ef4444" strokeLinecap="round" strokeWidth={3.2} type="monotone" dataKey="west" name="West" />
          </LineChart>
        )}
      </ChartFrame>
    </section>
  );
}
