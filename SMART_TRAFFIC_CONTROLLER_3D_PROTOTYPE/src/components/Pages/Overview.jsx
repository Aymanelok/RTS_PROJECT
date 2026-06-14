import ControlBar from '../ControlBar.jsx';
import DecisionPanel from '../DecisionPanel.jsx';
import KPICard from '../KPICard.jsx';
import QueueCard from '../QueueCard.jsx';
import SafetyMonitor from '../SafetyMonitor.jsx';
import SystemHealth from '../SystemHealth.jsx';
import TrafficSimulation from '../TrafficSimulation.jsx';
import LatencyChart from '../Charts/LatencyChart.jsx';
import PhaseTimeline from '../Charts/PhaseTimeline.jsx';
import VehiclesChart from '../Charts/VehiclesChart.jsx';

const queueConfig = [
  { direction: 'north', label: 'NORTH', color: 'green' },
  { direction: 'south', label: 'SOUTH', color: 'cyan' },
  { direction: 'east', label: 'EAST', color: 'yellow' },
  { direction: 'west', label: 'WEST', color: 'red' },
];

export default function Overview({ traffic, telemetry, kpis, systemHealth, phasePosition }) {
  return (
    <div className="grid grid-cols-1 gap-5 2xl:grid-cols-[minmax(0,1.35fr)_minmax(440px,0.9fr)]">
      <div className="space-y-5">
        <ControlBar traffic={traffic} />
        <TrafficSimulation
          activeAxis={traffic.activeAxis}
          activePhase={traffic.phaseLabel}
          cars={traffic.cars}
          phaseDuration={traffic.phaseDuration}
          phaseElapsed={traffic.phaseElapsed}
          phaseTone={traffic.phaseTone}
          signals={traffic.signals}
        />

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {queueConfig.map((item) => (
            <QueueCard
              key={item.direction}
              {...item}
              max={24}
              value={traffic.queues[item.direction]}
            />
          ))}
        </div>

        <div className="grid gap-5 xl:grid-cols-2">
          <VehiclesChart data={telemetry.history} />
          <LatencyChart data={telemetry.history} />
        </div>

        <PhaseTimeline nowPosition={phasePosition} />
      </div>

      <div className="space-y-5">
        <section className="grid gap-4 sm:grid-cols-2">
          {kpis.map((kpi) => (
            <KPICard key={kpi.title} {...kpi} />
          ))}
        </section>

        <DecisionPanel
          currentPhase={traffic.phaseLabel}
          decision={traffic.decision}
          ewQueue={traffic.queueSummary.ewQueue}
          nsQueue={traffic.queueSummary.nsQueue}
          phaseElapsed={traffic.phaseElapsed}
          threshold={traffic.settings.hysteresisThreshold}
        />

        <SafetyMonitor safety={traffic.safety} />

        <SystemHealth data={systemHealth} />
      </div>
    </div>
  );
}
