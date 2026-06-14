import { getSignalsForPhase, PHASES } from './trafficLogic.js';

export function hasGreenConflict(signals) {
  const nsGreen = signals.north === 'green' || signals.south === 'green';
  const ewGreen = signals.east === 'green' || signals.west === 'green';
  return nsGreen && ewGreen;
}

export function validateTrafficCommand(command) {
  const signals = command.signals || getSignalsForPhase(command.phaseName || PHASES.MANUAL_ALL_RED);

  if (hasGreenConflict(signals)) {
    return {
      ok: false,
      reason: 'Command rejected by Safety Monitor: North-South and East-West cannot be green at the same time.',
      safePhaseName: PHASES.MANUAL_ALL_RED,
      safeSignals: getSignalsForPhase(PHASES.MANUAL_ALL_RED),
    };
  }

  return {
    ok: true,
    reason: 'Command accepted by Safety Monitor.',
    safePhaseName: command.phaseName,
    safeSignals: signals,
  };
}
