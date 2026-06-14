export const DIRECTIONS = ['north', 'south', 'east', 'west'];

export const PHASES = {
  NORTH_SOUTH_GREEN: 'NORTH_SOUTH_GREEN',
  NORTH_SOUTH_YELLOW: 'NORTH_SOUTH_YELLOW',
  ALL_RED_TO_EAST_WEST: 'ALL_RED_TO_EAST_WEST',
  EAST_WEST_GREEN: 'EAST_WEST_GREEN',
  EAST_WEST_YELLOW: 'EAST_WEST_YELLOW',
  ALL_RED_TO_NORTH_SOUTH: 'ALL_RED_TO_NORTH_SOUTH',
  MANUAL_ALL_RED: 'MANUAL_ALL_RED',
};

export const PHASE_LABELS = {
  [PHASES.NORTH_SOUTH_GREEN]: 'NORTH-SOUTH GREEN',
  [PHASES.NORTH_SOUTH_YELLOW]: 'NORTH-SOUTH YELLOW',
  [PHASES.ALL_RED_TO_EAST_WEST]: 'ALL RED CLEARANCE',
  [PHASES.EAST_WEST_GREEN]: 'EAST-WEST GREEN',
  [PHASES.EAST_WEST_YELLOW]: 'EAST-WEST YELLOW',
  [PHASES.ALL_RED_TO_NORTH_SOUTH]: 'ALL RED CLEARANCE',
  [PHASES.MANUAL_ALL_RED]: 'MANUAL ALL RED',
};

export const DIRECTION_LABELS = {
  north: 'North',
  south: 'South',
  east: 'East',
  west: 'West',
};

export const directionAxis = {
  north: 'NS',
  south: 'NS',
  east: 'EW',
  west: 'EW',
};

export const laneGeometry = {
  north: {
    axis: 'y',
    delta: 1,
    stopLine: 30.2,
    stopTarget: 25.6,
    spawn: { x: 46, y: -8 },
    exit: 110,
    lanes: [45.5, 48.6],
  },
  south: {
    axis: 'y',
    delta: -1,
    stopLine: 69.8,
    stopTarget: 74.4,
    spawn: { x: 54, y: 108 },
    exit: -10,
    lanes: [54.2, 57.4],
  },
  east: {
    axis: 'x',
    delta: -1,
    stopLine: 69.8,
    stopTarget: 74.4,
    spawn: { x: 108, y: 46 },
    exit: -10,
    lanes: [42.8, 46],
  },
  west: {
    axis: 'x',
    delta: 1,
    stopLine: 30.2,
    stopTarget: 25.6,
    spawn: { x: -8, y: 54 },
    exit: 110,
    lanes: [54, 57.2],
  },
};

export const carPalette = [
  '#22c55e',
  '#38bdf8',
  '#f97316',
  '#60a5fa',
  '#e879f9',
  '#facc15',
  '#f43f5e',
  '#14b8a6',
  '#a78bfa',
  '#fb7185',
  '#2dd4bf',
  '#f8fafc',
];

export const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

export const randomBetween = (min, max) => min + Math.random() * (max - min);

export const randomInt = (min, max) => Math.round(randomBetween(min, max));

export function getSignalsForPhase(phaseName) {
  switch (phaseName) {
    case PHASES.NORTH_SOUTH_GREEN:
      return { north: 'green', south: 'green', east: 'red', west: 'red' };
    case PHASES.NORTH_SOUTH_YELLOW:
      return { north: 'yellow', south: 'yellow', east: 'red', west: 'red' };
    case PHASES.EAST_WEST_GREEN:
      return { north: 'red', south: 'red', east: 'green', west: 'green' };
    case PHASES.EAST_WEST_YELLOW:
      return { north: 'red', south: 'red', east: 'yellow', west: 'yellow' };
    default:
      return { north: 'red', south: 'red', east: 'red', west: 'red' };
  }
}

export function getActiveAxis(phaseName) {
  if (phaseName === PHASES.NORTH_SOUTH_GREEN || phaseName === PHASES.NORTH_SOUTH_YELLOW) {
    return 'NS';
  }
  if (phaseName === PHASES.EAST_WEST_GREEN || phaseName === PHASES.EAST_WEST_YELLOW) {
    return 'EW';
  }
  return 'ALL';
}

export function getPhaseTone(phaseName) {
  if (phaseName.includes('YELLOW')) return 'yellow';
  if (phaseName.includes('GREEN')) return 'green';
  return 'red';
}

export function getNextPhase(phaseName) {
  switch (phaseName) {
    case PHASES.NORTH_SOUTH_GREEN:
      return PHASES.NORTH_SOUTH_YELLOW;
    case PHASES.NORTH_SOUTH_YELLOW:
      return PHASES.ALL_RED_TO_EAST_WEST;
    case PHASES.ALL_RED_TO_EAST_WEST:
      return PHASES.EAST_WEST_GREEN;
    case PHASES.EAST_WEST_GREEN:
      return PHASES.EAST_WEST_YELLOW;
    case PHASES.EAST_WEST_YELLOW:
      return PHASES.ALL_RED_TO_NORTH_SOUTH;
    case PHASES.ALL_RED_TO_NORTH_SOUTH:
    default:
      return PHASES.NORTH_SOUTH_GREEN;
  }
}

export function getPhaseDuration(phaseName, settings) {
  if (phaseName.includes('GREEN')) return settings.greenDuration;
  if (phaseName.includes('YELLOW')) return settings.yellowDuration;
  return settings.allRedDuration;
}

export function isGreenPhase(phaseName) {
  return phaseName === PHASES.NORTH_SOUTH_GREEN || phaseName === PHASES.EAST_WEST_GREEN;
}

export function getOpposingGreenPhase(phaseName) {
  return phaseName === PHASES.NORTH_SOUTH_GREEN
    ? PHASES.EAST_WEST_GREEN
    : PHASES.NORTH_SOUTH_GREEN;
}

export function getTransitionPhaseForGreen(greenPhase) {
  return greenPhase === PHASES.NORTH_SOUTH_GREEN
    ? PHASES.NORTH_SOUTH_YELLOW
    : PHASES.EAST_WEST_YELLOW;
}

export function getQueueSummary(cars) {
  const queues = { north: 0, south: 0, east: 0, west: 0 };
  const waitingTimes = { north: 0, south: 0, east: 0, west: 0 };

  cars.forEach((car) => {
    if (car.state === 'waiting') {
      queues[car.direction] += 1;
      waitingTimes[car.direction] += car.waitTime || 0;
    }
  });

  const totals = {
    ns: queues.north + queues.south,
    ew: queues.east + queues.west,
  };

  const averageWaitingTime = DIRECTIONS.reduce((sum, direction) => {
    if (!queues[direction]) return sum;
    return sum + waitingTimes[direction] / queues[direction];
  }, 0);

  return {
    queues,
    nsQueue: totals.ns,
    ewQueue: totals.ew,
    difference: totals.ns - totals.ew,
    averageWaitingTime: Number((averageWaitingTime / DIRECTIONS.length).toFixed(1)),
  };
}

export function formatPhaseTime(seconds) {
  return `${Math.max(0, Math.ceil(seconds))}s`;
}

export function createDecisionText({ phaseName, nsQueue, ewQueue, hysteresisThreshold, elapsed }) {
  const difference = nsQueue - ewQueue;
  const absDifference = Math.abs(difference);
  const selectedDirection = difference >= 0 ? 'NORTH-SOUTH' : 'EAST-WEST';
  let decision = `Hold ${PHASE_LABELS[phaseName]}`;
  let explanation = 'Queue difference is inside the hysteresis band, so the controller avoids rapid phase flickering.';

  if (absDifference > hysteresisThreshold) {
    if (selectedDirection === 'NORTH-SOUTH') {
      decision = phaseName === PHASES.NORTH_SOUTH_GREEN
        ? 'Extend NORTH-SOUTH phase'
        : 'Prepare transition to NORTH-SOUTH phase';
      explanation = 'North-South demand is above the hysteresis threshold, so priority control favors that axis.';
    } else {
      decision = phaseName === PHASES.EAST_WEST_GREEN
        ? 'Extend EAST-WEST phase'
        : 'Prepare transition to EAST-WEST phase';
      explanation = 'East-West demand is above the hysteresis threshold, so the controller prepares service for that axis.';
    }
  }

  return {
    selectedDirection,
    difference,
    decision,
    explanation,
    phaseTimer: elapsed,
    currentPhase: PHASE_LABELS[phaseName],
  };
}
