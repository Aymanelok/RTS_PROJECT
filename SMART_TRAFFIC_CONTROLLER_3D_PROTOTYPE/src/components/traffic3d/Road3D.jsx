import { roadMaterial } from './sceneUtils.js';

function RoadMarking({ position, rotation = [0, 0, 0], size = [0.08, 0.012, 1.2], color = roadMaterial.line }) {
  return (
    <mesh position={position} rotation={rotation} receiveShadow>
      <boxGeometry args={size} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.04} roughness={0.55} />
    </mesh>
  );
}

function ZebraCrossing({ position, vertical = false }) {
  return (
    <group position={position}>
      {Array.from({ length: 10 }, (_, index) => (
        <RoadMarking
          key={index}
          position={vertical ? [(index - 4.5) * 0.52, 0.035, 0] : [0, 0.035, (index - 4.5) * 0.52]}
          size={vertical ? [0.28, 0.025, 1.9] : [1.9, 0.025, 0.28]}
        />
      ))}
    </group>
  );
}

function ArrowMark({ position, rotation = 0 }) {
  return (
    <group position={position} rotation={[0, rotation, 0]}>
      <RoadMarking position={[0, 0.04, 0]} size={[0.08, 0.025, 1.1]} />
      <RoadMarking position={[-0.25, 0.04, -0.46]} rotation={[0, -0.7, 0]} size={[0.08, 0.025, 0.65]} />
      <RoadMarking position={[0.25, 0.04, -0.46]} rotation={[0, 0.7, 0]} size={[0.08, 0.025, 0.65]} />
    </group>
  );
}

export default function Road3D({ activeAxis, phaseTone }) {
  const glowColor = phaseTone === 'yellow' ? '#facc15' : phaseTone === 'red' ? '#ef4444' : '#22c55e';
  const nsActive = activeAxis === 'NS';
  const ewActive = activeAxis === 'EW';

  return (
    <group>
      <mesh position={[0, -0.08, 0]} receiveShadow>
        <boxGeometry args={[37, 0.08, 37]} />
        <meshStandardMaterial color={roadMaterial.grass} roughness={0.85} />
      </mesh>

      <mesh position={[0, 0, 0]} receiveShadow>
        <boxGeometry args={[9.6, 0.08, 37]} />
        <meshStandardMaterial color={roadMaterial.asphalt} roughness={0.62} metalness={0.04} />
      </mesh>
      <mesh position={[0, 0.005, 0]} receiveShadow>
        <boxGeometry args={[37, 0.08, 9.6]} />
        <meshStandardMaterial color={roadMaterial.asphalt} roughness={0.62} metalness={0.04} />
      </mesh>
      <mesh position={[0, 0.015, 0]} receiveShadow>
        <boxGeometry args={[9.8, 0.08, 9.8]} />
        <meshStandardMaterial color={roadMaterial.asphaltLight} roughness={0.58} />
      </mesh>

      <mesh position={[0, 0.055, 0]}>
        <boxGeometry args={nsActive ? [5.9, 0.025, 36] : ewActive ? [36, 0.025, 5.9] : [0.01, 0.01, 0.01]} />
        <meshBasicMaterial color={glowColor} transparent opacity={activeAxis === 'ALL' ? 0 : 0.13} />
      </mesh>

      {Array.from({ length: 16 }, (_, index) => {
        const offset = -16 + index * 2.15;
        return (
          <group key={offset}>
            <RoadMarking position={[0, 0.07, offset]} size={[0.08, 0.02, 1.0]} />
            <RoadMarking position={[offset, 0.071, 0]} rotation={[0, Math.PI / 2, 0]} size={[0.08, 0.02, 1.0]} />
          </group>
        );
      })}

      <RoadMarking position={[-1.6, 0.07, 0]} size={[0.05, 0.02, 37]} color="#94a3b8" />
      <RoadMarking position={[1.6, 0.07, 0]} size={[0.05, 0.02, 37]} color="#94a3b8" />
      <RoadMarking position={[0, 0.07, -1.6]} rotation={[0, Math.PI / 2, 0]} size={[0.05, 0.02, 37]} color="#94a3b8" />
      <RoadMarking position={[0, 0.07, 1.6]} rotation={[0, Math.PI / 2, 0]} size={[0.05, 0.02, 37]} color="#94a3b8" />

      <ZebraCrossing position={[0, 0.08, -6.35]} vertical />
      <ZebraCrossing position={[0, 0.08, 6.35]} vertical />
      <ZebraCrossing position={[-6.35, 0.08, 0]} />
      <ZebraCrossing position={[6.35, 0.08, 0]} />

      <RoadMarking position={[0, 0.09, -6.73]} size={[5.6, 0.03, 0.08]} color="#f8fafc" />
      <RoadMarking position={[0, 0.09, 6.73]} size={[5.6, 0.03, 0.08]} color="#f8fafc" />
      <RoadMarking position={[-6.73, 0.09, 0]} size={[0.08, 0.03, 5.6]} color="#f8fafc" />
      <RoadMarking position={[6.73, 0.09, 0]} size={[0.08, 0.03, 5.6]} color="#f8fafc" />

      <ArrowMark position={[-2.8, 0.1, -10.8]} rotation={Math.PI} />
      <ArrowMark position={[2.8, 0.1, 10.8]} rotation={0} />
      <ArrowMark position={[10.8, 0.1, -2.8]} rotation={-Math.PI / 2} />
      <ArrowMark position={[-10.8, 0.1, 2.8]} rotation={Math.PI / 2} />
    </group>
  );
}
