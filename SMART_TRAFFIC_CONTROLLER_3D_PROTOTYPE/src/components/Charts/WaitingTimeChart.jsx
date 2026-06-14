import { CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from 'recharts';
import ChartFrame from '../ChartFrame.jsx';

export default function WaitingTimeChart({ data }) {
  return (
    <section className="glass-panel min-w-0 p-5">
      <div className="mb-4">
        <p className="panel-title">Average Waiting Time</p>
        <h2 className="mt-1 text-lg font-black text-white">Stopped Delay per Direction</h2>
      </div>
      <ChartFrame className="h-72 min-w-0">
        {({ width, height }) => (
          <LineChart data={data} height={height} margin={{ top: 10, right: 16, left: -18, bottom: 0 }} width={width}>
            <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" strokeDasharray="4 4" />
            <XAxis dataKey="time" tickLine={false} axisLine={false} minTickGap={22} />
            <YAxis tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: 'rgba(2, 6, 23, 0.92)', border: '1px solid rgba(125, 211, 252, 0.18)', borderRadius: 14 }} />
            <Legend />
            <Line dot={false} stroke="#22c55e" strokeLinecap="round" strokeWidth={3} type="monotone" dataKey="waitNorth" name="North wait" />
            <Line dot={false} stroke="#22d3ee" strokeLinecap="round" strokeWidth={3} type="monotone" dataKey="waitSouth" name="South wait" />
            <Line dot={false} stroke="#facc15" strokeLinecap="round" strokeWidth={3} type="monotone" dataKey="waitEast" name="East wait" />
            <Line dot={false} stroke="#ef4444" strokeLinecap="round" strokeWidth={3} type="monotone" dataKey="waitWest" name="West wait" />
          </LineChart>
        )}
      </ChartFrame>
    </section>
  );
}
