import { MathUtils } from 'three';

export const WORLD_SIZE = 34;
export const WORLD_SCALE = WORLD_SIZE / 100;

export function percentToWorld(x, y) {
  return [(x - 50) * WORLD_SCALE, 0, (y - 50) * WORLD_SCALE];
}

export function directionRotation(direction) {
  switch (direction) {
    case 'north':
      return Math.PI;
    case 'south':
      return 0;
    case 'east':
      return -Math.PI / 2;
    case 'west':
      return Math.PI / 2;
    default:
      return 0;
  }
}

export function damp(current, target, lambda, delta) {
  return MathUtils.damp(current, target, lambda, delta);
}

export const roadMaterial = {
  asphalt: '#10151d',
  asphaltLight: '#182231',
  line: '#e2e8f0',
  curb: '#cbd5e1',
  sidewalk: '#273244',
  grass: '#0f3a2c',
};
