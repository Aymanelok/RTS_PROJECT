import { roadMaterial } from './sceneUtils.js';

function Block({ position, size }) {
  return (
    <mesh position={position} receiveShadow castShadow>
      <boxGeometry args={size} />
      <meshStandardMaterial color={roadMaterial.sidewalk} roughness={0.7} metalness={0.04} />
    </mesh>
  );
}

export default function Sidewalk3D() {
  return (
    <group>
      <Block position={[-10.9, 0.02, -10.9]} size={[9.6, 0.18, 9.6]} />
      <Block position={[10.9, 0.02, -10.9]} size={[9.6, 0.18, 9.6]} />
      <Block position={[-10.9, 0.02, 10.9]} size={[9.6, 0.18, 9.6]} />
      <Block position={[10.9, 0.02, 10.9]} size={[9.6, 0.18, 9.6]} />

      {[
        [-5.65, -10.9, 0.18, 9.6],
        [5.65, -10.9, 0.18, 9.6],
        [-5.65, 10.9, 0.18, 9.6],
        [5.65, 10.9, 0.18, 9.6],
      ].map(([x, z, w, d]) => (
        <Block key={`${x}-${z}`} position={[x, 0.08, z]} size={[w, 0.34, d]} />
      ))}
      {[
        [-10.9, -5.65, 9.6, 0.18],
        [-10.9, 5.65, 9.6, 0.18],
        [10.9, -5.65, 9.6, 0.18],
        [10.9, 5.65, 9.6, 0.18],
      ].map(([x, z, w, d]) => (
        <Block key={`${x}-${z}`} position={[x, 0.08, z]} size={[w, 0.34, d]} />
      ))}
    </group>
  );
}
