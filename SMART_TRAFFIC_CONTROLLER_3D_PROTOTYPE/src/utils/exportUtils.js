export function downloadTextFile(filename, content, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function telemetryToCsv(rows) {
  const header = ['time', 'north', 'south', 'east', 'west', 'latency', 'jitter', 'waitingTime', 'throughput'];
  const body = rows.map((row) =>
    header.map((key) => JSON.stringify(row[key] ?? '')).join(','),
  );
  return [header.join(','), ...body].join('\n');
}

export function createSummaryReport({ telemetry, traffic }) {
  const latest = telemetry.history.at(-1) || {};
  return [
    'SMART TRAFFIC CONTROLLER - SUMMARY REPORT',
    '',
    `Current phase: ${traffic.phaseLabel}`,
    `Mode: ${traffic.mode.toUpperCase()}`,
    `North queue: ${traffic.queues.north}`,
    `South queue: ${traffic.queues.south}`,
    `East queue: ${traffic.queues.east}`,
    `West queue: ${traffic.queues.west}`,
    `Throughput: ${traffic.throughput} vehicles`,
    `Average waiting time: ${latest.waitingTime ?? 0}s`,
    `E2E latency: ${latest.latency ?? 0} ms`,
    `Safety status: ${traffic.safety.status}`,
    `Active alerts: ${traffic.alerts.length}`,
  ].join('\n');
}
