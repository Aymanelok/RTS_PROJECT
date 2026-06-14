import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  carPalette,
  clamp,
  createDecisionText,
  directionAxis,
  DIRECTIONS,
  getActiveAxis,
  getNextPhase,
  getOpposingGreenPhase,
  getPhaseDuration,
  getPhaseTone,
  getQueueSummary,
  getSignalsForPhase,
  getTransitionPhaseForGreen,
  isGreenPhase,
  laneGeometry,
  PHASE_LABELS,
  PHASES,
  randomBetween,
  randomInt,
} from '../utils/trafficLogic.js';
import { validateTrafficCommand } from '../utils/safetyMonitor.js';

const DEFAULT_SETTINGS = {
  greenDuration: 12,
  yellowDuration: 3,
  allRedDuration: 1,
  minGreenTime: 8,
  maxGreenTime: 15,
  hysteresisThreshold: 6,
  simulationSpeed: 1,
  emergencyMode: true,
};

const SAFE_GAP = 6.8;
const MAX_CARS_PER_DIRECTION = 7;
const INITIAL_COUNTS = { north: 5, south: 4, east: 3, west: 3 };
const intersectionEndProgress = {
  north: 66,
  west: 66,
  south: -34,
  east: -34,
};

let carSequence = 0;

function createCar(direction, options = {}) {
  const geometry = laneGeometry[direction];
  const lane = options.lane ?? randomInt(0, geometry.lanes.length - 1);
  const laneCoordinate = geometry.lanes[lane];
  const progress = options.progress ?? geometry.spawn[geometry.axis] * geometry.delta;
  const position = progress / geometry.delta;
  const type = options.type || (Math.random() > 0.92 ? 'bus' : 'car');
  const maxSpeed = type === 'bus' ? randomBetween(7.5, 10.5) : randomBetween(9.5, 14.5);

  return {
    id: options.id || `${direction}-${Date.now()}-${carSequence++}`,
    direction,
    lane,
    x: geometry.axis === 'x' ? position : laneCoordinate,
    y: geometry.axis === 'y' ? position : laneCoordinate,
    speed: 0,
    maxSpeed: options.maxSpeed ?? maxSpeed,
    acceleration: type === 'bus' ? 5.2 : type === 'ambulance' ? 8.4 : 6.8,
    state: 'moving',
    color: options.color || carPalette[carSequence % carPalette.length],
    type,
    distanceToStopLine: Math.max(0, geometry.stopLine * geometry.delta - progress),
    hasCrossedIntersection: false,
    hasEnteredIntersection: false,
    hasCrossedStopLine: false,
    waitTime: 0,
  };
}

function createInitialCars() {
  const cars = [];
  DIRECTIONS.forEach((direction) => {
    const geometry = laneGeometry[direction];
    const stopProgress = geometry.stopTarget * geometry.delta;
    const count = INITIAL_COUNTS[direction];

    for (let index = 0; index < count; index += 1) {
      const lane = index % geometry.lanes.length;
      const progress = stopProgress - index * SAFE_GAP - randomBetween(0, 1.5);
      cars.push(createCar(direction, { lane, progress }));
    }
  });

  cars.push(
    createCar('east', {
      lane: 0,
      progress: laneGeometry.east.stopTarget * laneGeometry.east.delta - SAFE_GAP * 2.3,
      type: 'ambulance',
      color: '#f8fafc',
      maxSpeed: 15.5,
      id: 'ambulance-primary',
    }),
  );

  return cars;
}

function hasReachedProgress(car, value) {
  const geometry = laneGeometry[car.direction];
  const progress = car[geometry.axis] * geometry.delta;
  return progress >= value;
}

function updateVehicleKinematics(cars, signals, dt, settings) {
  const nextCars = [];

  DIRECTIONS.forEach((direction) => {
    const geometry = laneGeometry[direction];
    const axis = geometry.axis;
    const laneKey = axis === 'x' ? 'y' : 'x';
    const directionCars = cars
      .filter((car) => car.direction === direction)
      .sort((a, b) => b[axis] * geometry.delta - a[axis] * geometry.delta);

    const laneFrontProgress = new Map();

    directionCars.forEach((car) => {
      const progress = car[axis] * geometry.delta;
      const stopLineProgress = geometry.stopLine * geometry.delta;
      const stopTargetProgress = geometry.stopTarget * geometry.delta;
      const signal = signals[direction];
      const hasCrossedStopLine = car.hasCrossedStopLine || progress >= stopLineProgress;
      const hasCrossedIntersection =
        car.hasCrossedIntersection || progress >= intersectionEndProgress[direction];
      const frontKey = `${direction}-${car.lane}`;
      const frontProgress = laneFrontProgress.get(frontKey);
      const mustRespectSignal = !hasCrossedStopLine && signal !== 'green';
      const signalTarget = mustRespectSignal ? stopTargetProgress : Number.POSITIVE_INFINITY;
      const gapTarget =
        typeof frontProgress === 'number' ? frontProgress - SAFE_GAP : Number.POSITIVE_INFINITY;
      const targetProgress = Math.min(signalTarget, gapTarget);
      const emergencyBoost = car.type === 'ambulance' && settings.emergencyMode ? 1.18 : 1;
      const desiredSpeed = car.maxSpeed * emergencyBoost;
      const desiredProgress = progress + desiredSpeed * dt;
      const blocked = desiredProgress >= targetProgress - 0.15;
      const nextProgress = blocked ? Math.max(progress, targetProgress) : desiredProgress;
      const nextPosition = nextProgress / geometry.delta;
      const currentSpeed = blocked ? 0 : desiredSpeed;
      const nextHasCrossedStopLine = hasCrossedStopLine || nextProgress >= stopLineProgress;
      const nextHasCrossedIntersection =
        hasCrossedIntersection || nextProgress >= intersectionEndProgress[direction];
      const insideIntersection =
        nextHasCrossedStopLine && !nextHasCrossedIntersection && nextProgress >= stopLineProgress;
      const waiting = currentSpeed < 0.05 && !nextHasCrossedStopLine;
      const exited = nextProgress >= geometry.exit * geometry.delta;

      laneFrontProgress.set(frontKey, nextProgress);

      if (exited) {
        return;
      }

      nextCars.push({
        ...car,
        [axis]: nextPosition,
        [laneKey]: geometry.lanes[car.lane],
        speed: currentSpeed,
        state: waiting ? 'waiting' : insideIntersection ? 'crossing' : 'moving',
        distanceToStopLine: Math.max(0, stopLineProgress - nextProgress),
        hasCrossedStopLine: nextHasCrossedStopLine,
        hasEnteredIntersection: nextHasCrossedStopLine,
        hasCrossedIntersection: nextHasCrossedIntersection,
        waitTime: waiting ? (car.waitTime || 0) + dt : car.waitTime || 0,
      });
    });
  });

  return nextCars;
}

function countExitedCars(previousCars, nextCars) {
  const nextIds = new Set(nextCars.map((car) => car.id));
  return previousCars.filter((car) => !nextIds.has(car.id)).length;
}

function directionSpawnClear(cars, direction) {
  const geometry = laneGeometry[direction];
  const axis = geometry.axis;
  const spawnProgress = geometry.spawn[axis] * geometry.delta;
  return !cars.some((car) => {
    if (car.direction !== direction) return false;
    const progress = car[axis] * geometry.delta;
    return progress < spawnProgress + SAFE_GAP * 1.7;
  });
}

function withSpawnedCars(cars, spawnCooldowns, dt, settings) {
  const nextCooldowns = { ...spawnCooldowns };
  const nextCars = [...cars];

  DIRECTIONS.forEach((direction) => {
    nextCooldowns[direction] = Math.max(0, (nextCooldowns[direction] || 0) - dt);
    const count = nextCars.filter((car) => car.direction === direction).length;
    if (
      count < MAX_CARS_PER_DIRECTION &&
      nextCooldowns[direction] <= 0 &&
      directionSpawnClear(nextCars, direction)
    ) {
      const type =
        settings.emergencyMode && !nextCars.some((car) => car.type === 'ambulance') && Math.random() > 0.82
          ? 'ambulance'
          : undefined;
      nextCars.push(createCar(direction, { type, color: type === 'ambulance' ? '#f8fafc' : undefined }));
      nextCooldowns[direction] = randomBetween(1.1, 2.6);
    }
  });

  return { cars: nextCars, cooldowns: nextCooldowns };
}

function createAlert(type, message, severity = 'warning') {
  return {
    id: `${type}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type,
    message,
    severity,
    time: new Date().toLocaleTimeString(),
  };
}

export function useTrafficSimulation() {
  const [now, setNow] = useState(new Date());
  const [cars, setCars] = useState(createInitialCars);
  const [phaseName, setPhaseName] = useState(PHASES.NORTH_SOUTH_GREEN);
  const [phaseElapsed, setPhaseElapsed] = useState(0);
  const [mode, setMode] = useState('auto');
  const [isRunning, setIsRunning] = useState(true);
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [throughput, setThroughput] = useState(0);
  const [alerts, setAlerts] = useState([]);
  const [safety, setSafety] = useState({
    status: 'SAFE',
    violations: 0,
    signalConflicts: 0,
    redLightViolations: 0,
    sensorFaults: 0,
    communicationErrors: 0,
    message: 'No conflicting greens or unsafe command detected.',
  });

  const refs = useRef({
    cars: [],
    phaseName: PHASES.NORTH_SOUTH_GREEN,
    phaseElapsed: 0,
    mode: 'auto',
    isRunning: true,
    settings: DEFAULT_SETTINGS,
    spawnCooldowns: { north: 0.4, south: 1.1, east: 1.7, west: 2.2 },
    lastFrame: 0,
  });

  useEffect(() => {
    refs.current.cars = cars;
  }, [cars]);

  useEffect(() => {
    refs.current.phaseName = phaseName;
  }, [phaseName]);

  useEffect(() => {
    refs.current.phaseElapsed = phaseElapsed;
  }, [phaseElapsed]);

  useEffect(() => {
    refs.current.mode = mode;
  }, [mode]);

  useEffect(() => {
    refs.current.isRunning = isRunning;
  }, [isRunning]);

  useEffect(() => {
    refs.current.settings = settings;
  }, [settings]);

  const addAlert = useCallback((type, message, severity = 'warning') => {
    setAlerts((previous) => [createAlert(type, message, severity), ...previous].slice(0, 10));
  }, []);

  const queueSummary = useMemo(() => getQueueSummary(cars), [cars]);
  const signals = useMemo(() => getSignalsForPhase(phaseName), [phaseName]);
  const activeAxis = getActiveAxis(phaseName);
  const phaseTone = getPhaseTone(phaseName);
  const phaseLabel = PHASE_LABELS[phaseName];
  const phaseDuration = getPhaseDuration(phaseName, settings);

  const advanceAutomaticPhase = useCallback((elapsed, phase, summary, currentSettings) => {
    if (!isGreenPhase(phase)) {
      return elapsed >= getPhaseDuration(phase, currentSettings) ? getNextPhase(phase) : phase;
    }

    const activeAxisName = phase === PHASES.NORTH_SOUTH_GREEN ? 'NS' : 'EW';
    const activeQueue = activeAxisName === 'NS' ? summary.nsQueue : summary.ewQueue;
    const opposingQueue = activeAxisName === 'NS' ? summary.ewQueue : summary.nsQueue;
    const difference = activeQueue - opposingQueue;
    const oppositeNeedsService = opposingQueue - activeQueue > currentSettings.hysteresisThreshold;
    const activeNeedsExtension = difference > currentSettings.hysteresisThreshold;
    const minimumServed = elapsed >= currentSettings.minGreenTime;
    const maximumReached = elapsed >= currentSettings.maxGreenTime;
    const plannedReached = elapsed >= currentSettings.greenDuration;

    if (!minimumServed) return phase;
    if (maximumReached) return getTransitionPhaseForGreen(phase);
    if (oppositeNeedsService && elapsed >= currentSettings.minGreenTime) {
      return getTransitionPhaseForGreen(phase);
    }
    if (plannedReached && !activeNeedsExtension) {
      return getTransitionPhaseForGreen(phase);
    }

    return phase;
  }, []);

  useEffect(() => {
    let frameId;

    const animate = (timestamp) => {
      const state = refs.current;
      if (!state.lastFrame) state.lastFrame = timestamp;
      const rawDt = Math.min(0.05, (timestamp - state.lastFrame) / 1000);
      state.lastFrame = timestamp;

      if (state.isRunning) {
        const dt = rawDt * state.settings.simulationSpeed;
        const currentSignals = getSignalsForPhase(state.phaseName);
        const movedCars = updateVehicleKinematics(state.cars, currentSignals, dt, state.settings);
        const exitedCount = countExitedCars(state.cars, movedCars);
        const spawned = withSpawnedCars(movedCars, state.spawnCooldowns, dt, state.settings);
        state.spawnCooldowns = spawned.cooldowns;
        state.cars = spawned.cars;
        setCars(spawned.cars);
        if (exitedCount > 0) {
          setThroughput((value) => value + exitedCount);
        }

        if (state.mode === 'auto') {
          const nextElapsed = state.phaseElapsed + dt;
          const summary = getQueueSummary(spawned.cars);
          const nextPhase = advanceAutomaticPhase(nextElapsed, state.phaseName, summary, state.settings);

          if (nextPhase !== state.phaseName) {
            state.phaseName = nextPhase;
            state.phaseElapsed = 0;
            setPhaseName(nextPhase);
            setPhaseElapsed(0);
          } else {
            state.phaseElapsed = nextElapsed;
            setPhaseElapsed(nextElapsed);
          }
        } else {
          const nextElapsed = state.phaseElapsed + dt;
          state.phaseElapsed = nextElapsed;
          setPhaseElapsed(nextElapsed);
        }
      }

      frameId = requestAnimationFrame(animate);
    };

    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [advanceAutomaticPhase]);

  useEffect(() => {
    const intervalId = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(intervalId);
  }, []);

  const applySafePhase = useCallback(
    (targetPhase, nextMode = 'manual') => {
      const result = validateTrafficCommand({ phaseName: targetPhase });
      setMode(nextMode);

      if (!result.ok) {
        refs.current.phaseName = result.safePhaseName;
        refs.current.phaseElapsed = 0;
        setPhaseName(result.safePhaseName);
        setPhaseElapsed(0);
        setSafety((previous) => ({
          ...previous,
          status: 'WARNING',
          violations: previous.violations + 1,
          signalConflicts: previous.signalConflicts + 1,
          message: result.reason,
        }));
        addAlert('Safety', result.reason, 'critical');
        return false;
      }

      refs.current.phaseName = targetPhase;
      refs.current.phaseElapsed = 0;
      setPhaseName(targetPhase);
      setPhaseElapsed(0);
      setSafety((previous) => ({
        ...previous,
        status: previous.violations > 0 ? 'WARNING' : 'SAFE',
        message:
          previous.violations > 0
            ? 'Previous unsafe command was rejected; latest safe command accepted.'
            : result.reason,
      }));
      return true;
    },
    [addAlert],
  );

  const controls = useMemo(
    () => ({
      startSimulation: () => setIsRunning(true),
      pauseSimulation: () => setIsRunning(false),
      resetSimulation: () => {
        const freshCars = createInitialCars();
        refs.current.cars = freshCars;
        refs.current.phaseName = PHASES.NORTH_SOUTH_GREEN;
        refs.current.phaseElapsed = 0;
        refs.current.spawnCooldowns = { north: 0.4, south: 1.1, east: 1.7, west: 2.2 };
        setCars(freshCars);
        setPhaseName(PHASES.NORTH_SOUTH_GREEN);
        setPhaseElapsed(0);
        setThroughput(0);
        setAlerts([]);
        setSafety({
          status: 'SAFE',
          violations: 0,
          signalConflicts: 0,
          redLightViolations: 0,
          sensorFaults: 0,
          communicationErrors: 0,
          message: 'No conflicting greens or unsafe command detected.',
        });
      },
      setSimulationSpeed: (speed) => {
        setSettings((previous) => ({ ...previous, simulationSpeed: speed }));
      },
      setMode: (nextMode) => {
        setMode(nextMode);
        if (nextMode === 'auto') {
          addAlert('Controller', 'Returned to automatic adaptive control.', 'info');
        }
      },
      updateSetting: (key, value) => {
        setSettings((previous) => ({
          ...previous,
          [key]:
            key === 'greenDuration'
              ? clamp(Number(value), previous.minGreenTime, previous.maxGreenTime)
              : key === 'yellowDuration'
                ? clamp(Number(value), 2, 5)
                : key === 'hysteresisThreshold'
                  ? clamp(Number(value), 1, 14)
                  : key === 'simulationSpeed'
                    ? Number(value)
                    : value,
        }));
      },
      forceNorthSouthGreen: () => applySafePhase(PHASES.NORTH_SOUTH_GREEN),
      forceEastWestGreen: () => applySafePhase(PHASES.EAST_WEST_GREEN),
      forceYellowTransition: () => {
        const phase = directionAxis.north === getActiveAxis(refs.current.phaseName)
          ? PHASES.NORTH_SOUTH_YELLOW
          : PHASES.EAST_WEST_YELLOW;
        applySafePhase(phase);
      },
      forceAllRed: () => applySafePhase(PHASES.MANUAL_ALL_RED),
      returnToAutomatic: () => {
        setMode('auto');
        addAlert('Controller', 'Automatic mode restored.', 'info');
      },
      triggerEmergencyVehicle: () => {
        const summary = getQueueSummary(refs.current.cars);
        const direction = summary.nsQueue >= summary.ewQueue ? 'north' : 'west';
        const ambulance = createCar(direction, {
          type: 'ambulance',
          color: '#f8fafc',
          maxSpeed: 16,
        });
        const nextCars = [ambulance, ...refs.current.cars];
        refs.current.cars = nextCars;
        setCars(nextCars);
        addAlert('Emergency', `Emergency vehicle dispatched from ${direction.toUpperCase()}.`, 'warning');
      },
      clearAlerts: () => {
        setAlerts([]);
        setSafety((previous) => ({
          ...previous,
          status: previous.violations > 0 ? 'WARNING' : 'SAFE',
          message: previous.violations > 0 ? 'Previous violation recorded. No active command conflict.' : 'No active alerts.',
        }));
      },
      simulateSafetyViolation: () => {
        const result = validateTrafficCommand({
          signals: { north: 'green', south: 'green', east: 'green', west: 'green' },
        });
        refs.current.phaseName = PHASES.MANUAL_ALL_RED;
        refs.current.phaseElapsed = 0;
        setPhaseName(PHASES.MANUAL_ALL_RED);
        setPhaseElapsed(0);
        setMode('manual');
        setSafety((previous) => ({
          ...previous,
          status: 'WARNING',
          violations: previous.violations + 1,
          signalConflicts: previous.signalConflicts + 1,
          message: result.reason,
        }));
        addAlert('Safety', result.reason, 'critical');
      },
      injectSensorFault: () => {
        setSafety((previous) => ({
          ...previous,
          status: 'WARNING',
          sensorFaults: previous.sensorFaults + 1,
          message: 'Sensor fault simulated on sensor_node.',
        }));
        addAlert('Sensor', 'Sensor fault simulated on sensor_node.', 'warning');
      },
    }),
    [addAlert, applySafePhase],
  );

  const decision = useMemo(
    () =>
      createDecisionText({
        phaseName,
        nsQueue: queueSummary.nsQueue,
        ewQueue: queueSummary.ewQueue,
        hysteresisThreshold: settings.hysteresisThreshold,
        elapsed: phaseElapsed,
      }),
    [phaseName, phaseElapsed, queueSummary.ewQueue, queueSummary.nsQueue, settings.hysteresisThreshold],
  );

  return {
    now,
    cars,
    signals,
    activeAxis,
    phaseTone,
    phaseName,
    phaseLabel,
    phaseElapsed,
    phaseDuration,
    queueSummary,
    queues: queueSummary.queues,
    settings,
    mode,
    isRunning,
    throughput,
    alerts,
    safety,
    decision,
    controls,
    opposingGreenPhase: getOpposingGreenPhase(phaseName),
  };
}
