import { useEffect, useMemo, useRef, useState } from 'react';
import { DIRECTIONS, randomBetween, randomInt } from '../utils/trafficLogic.js';

const formatTick = (date) =>
  new Intl.DateTimeFormat('en-US', {
    minute: '2-digit',
    second: '2-digit',
  }).format(date);

function createInitialHistory() {
  return Array.from({ length: 20 }, (_, index) => ({
    time: `-${19 - index}s`,
    north: 0,
    south: 0,
    east: 0,
    west: 0,
    latency: 120,
    jitter: 18,
    waitingTime: 0,
    throughput: 0,
  }));
}

export function useTelemetry(traffic) {
  const [history, setHistory] = useState(createInitialHistory);
  const [metrics, setMetrics] = useState({ latency: 132, jitter: 23, cpu: 42, ram: 61 });
  const [nodeMetrics, setNodeMetrics] = useState([
    { node: 'sensor_node', usage: 18, ram: 32, messages: 10, lastUpdate: 'now', online: true },
    { node: 'controller_node', usage: 31, ram: 44, messages: 10, lastUpdate: 'now', online: true },
    { node: 'actuator_node', usage: 24, ram: 39, messages: 10, lastUpdate: 'now', online: true },
    { node: 'dashboard_node', usage: 42, ram: 61, messages: 10, lastUpdate: 'now', online: true },
  ]);
  const previousThroughput = useRef(traffic.throughput);
  const latestTraffic = useRef(traffic);

  useEffect(() => {
    latestTraffic.current = traffic;
  }, [traffic]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      const snapshot = latestTraffic.current;
      const totalQueue = DIRECTIONS.reduce((sum, direction) => sum + snapshot.queues[direction], 0);
      const movingCars = snapshot.cars.filter((car) => car.state === 'moving' || car.state === 'crossing').length;
      const waitingCars = snapshot.cars.filter((car) => car.state === 'waiting').length;
      const throughputDelta = snapshot.throughput - previousThroughput.current;
      previousThroughput.current = snapshot.throughput;
      const waitByDirection = DIRECTIONS.reduce((acc, direction) => {
        const stopped = snapshot.cars.filter((car) => car.direction === direction && car.state === 'waiting');
        acc[direction] = stopped.length
          ? Number((stopped.reduce((sum, car) => sum + car.waitTime, 0) / stopped.length).toFixed(1))
          : 0;
        return acc;
      }, {});
      const speedLoad = snapshot.settings.simulationSpeed;
      const latency = Math.round(Math.min(188, 92 + totalQueue * 2.2 + speedLoad * 6 + randomBetween(0, 18)));
      const jitter = Math.round(Math.min(64, 9 + waitingCars * 1.4 + speedLoad * 3 + randomBetween(0, 7)));
      const cpu = Math.round(Math.min(92, 28 + snapshot.cars.length * 1.5 + speedLoad * 8 + randomBetween(0, 8)));
      const ram = Math.round(Math.min(88, 52 + snapshot.cars.length * 0.7 + randomBetween(0, 4)));
      const now = new Date();
      const averageWaiting = snapshot.queueSummary.averageWaitingTime;

      setMetrics({ latency, jitter, cpu, ram });
      setNodeMetrics([
        {
          node: 'sensor_node',
          usage: Math.round(12 + totalQueue * 0.8 + speedLoad * 2 + randomBetween(0, 5)),
          ram: Math.round(30 + totalQueue * 0.25),
          messages: Math.round(10 * speedLoad + totalQueue * 0.2),
          lastUpdate: formatTick(now),
          online: true,
        },
        {
          node: 'controller_node',
          usage: Math.round(20 + totalQueue * 1.1 + speedLoad * 4 + randomBetween(0, 6)),
          ram: Math.round(38 + totalQueue * 0.35),
          messages: Math.round(10 * speedLoad + movingCars * 0.5),
          lastUpdate: formatTick(now),
          online: true,
        },
        {
          node: 'actuator_node',
          usage: Math.round(16 + movingCars * 1.3 + speedLoad * 3 + randomBetween(0, 6)),
          ram: Math.round(35 + movingCars * 0.35),
          messages: Math.round(10 * speedLoad + movingCars * 0.4),
          lastUpdate: formatTick(now),
          online: true,
        },
        {
          node: 'dashboard_node',
          usage: cpu,
          ram,
          messages: Math.round(8 * speedLoad + snapshot.cars.length * 0.3),
          lastUpdate: formatTick(now),
          online: true,
        },
      ]);
      setHistory((previous) => [
        ...previous.slice(-35),
        {
          time: formatTick(now),
          ...snapshot.queues,
          latency,
          jitter,
          waitingTime: averageWaiting,
          waitNorth: waitByDirection.north,
          waitSouth: waitByDirection.south,
          waitEast: waitByDirection.east,
          waitWest: waitByDirection.west,
          throughput: throughputDelta * 60,
        },
      ]);
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  const cpuChartData = useMemo(
    () => nodeMetrics.map((metric) => ({ node: metric.node, usage: metric.usage })),
    [nodeMetrics],
  );

  return {
    history,
    metrics,
    nodeMetrics,
    cpuChartData,
  };
}
