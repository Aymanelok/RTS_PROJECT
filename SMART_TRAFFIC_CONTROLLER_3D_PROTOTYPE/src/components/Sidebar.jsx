import {
  Activity,
  AlertTriangle,
  BarChart3,
  Cctv,
  FileBarChart,
  Gauge,
  LayoutDashboard,
  Settings,
  TrafficCone,
} from 'lucide-react';

export const menuItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'traffic', label: 'Traffic Monitor', icon: TrafficCone },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'signals', label: 'Signals', icon: Gauge },
  { id: 'devices', label: 'Devices', icon: Cctv },
  { id: 'reports', label: 'Reports', icon: FileBarChart },
  { id: 'settings', label: 'Settings', icon: Settings },
  { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
];

export default function Sidebar({ activePage, onPageChange }) {
  return (
    <aside className="hidden min-h-[calc(100vh-81px)] w-72 shrink-0 border-r border-cyan-300/10 bg-slate-950/45 p-4 backdrop-blur-2xl lg:block">
      <div className="glass-panel mb-5 overflow-hidden p-4">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-300/10 text-cyan-200">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <p className="subtle-label">ROS2 Network</p>
            <p className="text-sm font-bold text-white">4 nodes synchronized</p>
          </div>
        </div>
        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-800">
          <div className="h-full w-full rounded-full bg-gradient-to-r from-cyan-400 via-emerald-400 to-blue-500 shadow-glow" />
        </div>
      </div>

      <nav className="space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = item.id === activePage;
          return (
            <button
              key={item.id}
              className={`group flex w-full items-center gap-3 rounded-2xl border px-4 py-3 text-left text-sm font-semibold transition ${
                active
                  ? 'border-cyan-300/25 bg-cyan-300/10 text-cyan-100 shadow-glow'
                  : 'border-transparent text-slate-400 hover:border-cyan-300/10 hover:bg-white/5 hover:text-slate-100'
              }`}
              onClick={() => onPageChange(item.id)}
              type="button"
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
