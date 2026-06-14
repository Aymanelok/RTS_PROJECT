import { Download, FileJson, FileText } from 'lucide-react';
import { createSummaryReport, downloadTextFile, telemetryToCsv } from '../../utils/exportUtils.js';

export default function Reports({ traffic, telemetry }) {
  const exportCsv = () => {
    downloadTextFile('smart-traffic-telemetry.csv', telemetryToCsv(telemetry.history), 'text/csv');
  };

  const exportJson = () => {
    downloadTextFile(
      'smart-traffic-telemetry.json',
      JSON.stringify({ history: telemetry.history, nodes: telemetry.nodeMetrics, safety: traffic.safety }, null, 2),
      'application/json',
    );
  };

  const exportSummary = () => {
    downloadTextFile(
      'smart-traffic-summary-report.txt',
      createSummaryReport({ telemetry, traffic }),
      'text/plain',
    );
  };

  return (
    <section className="glass-panel p-5">
      <div className="mb-5">
        <p className="panel-title">Reports</p>
        <h2 className="mt-1 text-xl font-black text-white">Export Presentation Telemetry</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <button className="rounded-2xl border border-cyan-300/20 bg-cyan-400/10 p-5 text-left text-cyan-100 transition hover:bg-cyan-400/20" onClick={exportCsv} type="button">
          <Download className="mb-4 h-7 w-7" />
          <p className="text-lg font-black">Export CSV</p>
          <p className="mt-2 text-sm text-cyan-100/70">Queue, latency, jitter, waiting time, throughput.</p>
        </button>
        <button className="rounded-2xl border border-blue-300/20 bg-blue-400/10 p-5 text-left text-blue-100 transition hover:bg-blue-400/20" onClick={exportJson} type="button">
          <FileJson className="mb-4 h-7 w-7" />
          <p className="text-lg font-black">Export JSON</p>
          <p className="mt-2 text-sm text-blue-100/70">Mock telemetry dataset with node and safety state.</p>
        </button>
        <button className="rounded-2xl border border-emerald-300/20 bg-emerald-400/10 p-5 text-left text-emerald-100 transition hover:bg-emerald-400/20" onClick={exportSummary} type="button">
          <FileText className="mb-4 h-7 w-7" />
          <p className="text-lg font-black">Generate Summary</p>
          <p className="mt-2 text-sm text-emerald-100/70">Plain-language report for oral presentation.</p>
        </button>
      </div>
    </section>
  );
}
