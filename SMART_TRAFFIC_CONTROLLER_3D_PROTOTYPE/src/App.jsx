import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  Cpu,
  Gauge,
  MemoryStick,
  ShieldCheck,
  Timer,
  Workflow,
} from 'lucide-react';
import DashboardLayout from './components/DashboardLayout.jsx';
import Alerts from './components/Pages/Alerts.jsx';
import Analytics from './components/Pages/Analytics.jsx';
import Devices from './components/Pages/Devices.jsx';
import Overview from './components/Pages/Overview.jsx';
import Reports from './components/Pages/Reports.jsx';
import Settings from './components/Pages/Settings.jsx';
import Signals from './components/Pages/Signals.jsx';
import TrafficMonitor from './components/Pages/TrafficMonitor.jsx';
import { useTelemetry } from './hooks/useTelemetry.js';
import { useTrafficSimulation } from './hooks/useTrafficSimulation.js';
import { PHASES } from './utils/trafficLogic.js';

const phaseOrder = [
  PHASES.NORTH_SOUTH_GREEN,
  PHASES.NORTH_SOUTH_YELLOW,
  PHASES.ALL_RED_TO_EAST_WEST,
  PHASES.EAST_WEST_GREEN,
  PHASES.EAST_WEST_YELLOW,
  PHASES.ALL_RED_TO_NORTH_SOUTH,
];

function getPhasePosition(traffic) {
  const durations = {
    [PHASES.NORTH_SOUTH_GREEN]: traffic.settings.greenDuration,
    [PHASES.NORTH_SOUTH_YELLOW]: traffic.settings.yellowDuration,
    [PHASES.ALL_RED_TO_EAST_WEST]: traffic.settings.allRedDuration,
    [PHASES.EAST_WEST_GREEN]: traffic.settings.greenDuration,
    [PHASES.EAST_WEST_YELLOW]: traffic.settings.yellowDuration,
    [PHASES.ALL_RED_TO_NORTH_SOUTH]: traffic.settings.allRedDuration,
  };
  const total = phaseOrder.reduce((sum, phase) => sum + durations[phase], 0);
  const index = phaseOrder.indexOf(traffic.phaseName);
  const completed = index > 0 ? phaseOrder.slice(0, index).reduce((sum, phase) => sum + durations[phase], 0) : 0;
  return Math.round(((completed + Math.min(traffic.phaseElapsed, durations[traffic.phaseName] || 1)) / total) * 100);
}

export default function App() {
  const [activePage, setActivePage] = useState('overview');
  const [theme, setTheme] = useState('dark');
  const traffic = useTrafficSimulation();
  const telemetry = useTelemetry(traffic);

  useEffect(() => {
    document.body.classList.toggle('light-theme', theme === 'light');
  }, [theme]);

  const systemHealth = useMemo(() => {
    const safetyScore = traffic.safety.status === 'SAFE' ? 100 : 82;
    const communicationScore = traffic.safety.communicationErrors > 0 ? 86 : 100;
    const sensorScore = traffic.safety.sensorFaults > 0 ? 78 : 100;
    return [
      { name: 'Sensors', value: 25, score: sensorScore },
      { name: 'Communication', value: 25, score: communicationScore },
      { name: 'Controllers', value: 25, score: safetyScore },
      { name: 'Power', value: 25, score: 100 },
    ];
  }, [traffic.safety]);

  const kpis = useMemo(
    () => [
      {
        title: 'E2E Latency',
        value: `${telemetry.metrics.latency} ms`,
        description: 'sensor to actuator command',
        icon: Timer,
        tone: 'cyan',
      },
      {
        title: 'Jitter',
        value: `${telemetry.metrics.jitter} ms`,
        description: 'control loop variation',
        icon: Activity,
        tone: 'blue',
      },
      {
        title: 'CPU Usage',
        value: `${telemetry.metrics.cpu}%`,
        description: 'dashboard host load',
        icon: Cpu,
        tone: 'yellow',
      },
      {
        title: 'RAM Usage',
        value: `${telemetry.metrics.ram}%`,
        description: 'memory allocation',
        icon: MemoryStick,
        tone: 'violet',
      },
      {
        title: 'Safety Status',
        value: traffic.safety.status,
        description: `${traffic.safety.violations} violations detected`,
        icon: ShieldCheck,
        tone: traffic.safety.status === 'SAFE' ? 'green' : 'yellow',
      },
      {
        title: 'Active Phase',
        value: traffic.phaseLabel,
        description: `${traffic.mode} control`,
        icon: Workflow,
        tone: traffic.phaseTone === 'yellow' ? 'yellow' : traffic.phaseTone === 'red' ? 'red' : 'green',
      },
    ],
    [telemetry.metrics, traffic.mode, traffic.phaseLabel, traffic.phaseTone, traffic.safety],
  );

  const pageProps = {
    traffic,
    telemetry,
    kpis,
    systemHealth,
    phasePosition: getPhasePosition(traffic),
  };

  const page = {
    overview: <Overview {...pageProps} />,
    traffic: <TrafficMonitor traffic={traffic} />,
    analytics: <Analytics telemetry={telemetry} />,
    signals: <Signals traffic={traffic} />,
    devices: <Devices nodeMetrics={telemetry.nodeMetrics} />,
    reports: <Reports telemetry={telemetry} traffic={traffic} />,
    settings: (
      <Settings
        theme={theme}
        traffic={traffic}
        onThemeToggle={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}
      />
    ),
    alerts: <Alerts traffic={traffic} />,
  }[activePage];

  return (
    <DashboardLayout activePage={activePage} now={traffic.now} onPageChange={setActivePage}>
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="panel-title">Control Center</p>
          <h1 className="mt-1 text-2xl font-black text-white">
            {activePage === 'traffic'
              ? 'Traffic Monitor'
              : activePage.charAt(0).toUpperCase() + activePage.slice(1)}
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs font-bold uppercase tracking-[0.16em] text-slate-300">
          <span className="rounded-full border border-cyan-300/15 bg-cyan-300/10 px-3 py-1">
            {traffic.mode} mode
          </span>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
            speed {traffic.settings.simulationSpeed}x
          </span>
          <span className="rounded-full border border-emerald-300/15 bg-emerald-400/10 px-3 py-1 text-emerald-100">
            {traffic.cars.length} vehicles
          </span>
        </div>
      </div>
      {page}
      <section className="glass-panel mt-5 p-5">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="panel-title">Control Policy</p>
            <h2 className="mt-1 text-lg font-black text-white">Real-Time Rules Enabled</h2>
          </div>
          <Gauge className="h-6 w-6 text-cyan-200" />
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
          {[
            'Priority control',
            'Hysteresis threshold',
            'Minimum green time',
            'Maximum green time',
            'Yellow transition',
            'All-red clearance',
          ].map((rule) => (
            <div
              key={rule}
              className="rounded-2xl border border-cyan-300/10 bg-cyan-300/5 px-4 py-3 text-sm font-semibold text-cyan-50"
            >
              {rule}
            </div>
          ))}
        </div>
      </section>
    </DashboardLayout>
  );
}
