import CPUChart from '../Charts/CPUChart.jsx';
import JitterChart from '../Charts/JitterChart.jsx';
import LatencyChart from '../Charts/LatencyChart.jsx';
import ThroughputChart from '../Charts/ThroughputChart.jsx';
import VehiclesChart from '../Charts/VehiclesChart.jsx';
import WaitingTimeChart from '../Charts/WaitingTimeChart.jsx';

export default function Analytics({ telemetry }) {
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <VehiclesChart data={telemetry.history} />
      <WaitingTimeChart data={telemetry.history} />
      <ThroughputChart data={telemetry.history} />
      <LatencyChart data={telemetry.history} />
      <JitterChart data={telemetry.history} />
      <CPUChart data={telemetry.cpuChartData} />
    </div>
  );
}
