const lensOrder = ['red', 'yellow', 'green'];
const lensColor = {
  red: '#ef4444',
  yellow: '#facc15',
  green: '#22c55e',
};

function Lens({ color, active, position }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[0.16, 18, 14]} />
      <meshStandardMaterial
        color={lensColor[color]}
        emissive={lensColor[color]}
        emissiveIntensity={active ? 2.1 : 0.12}
        roughness={0.28}
      />
      {active && <pointLight color={lensColor[color]} distance={4.5} intensity={0.65} />}
    </mesh>
  );
}

export default function TrafficLight3D({ position, rotation = 0, status = 'red' }) {
  return (
    <group position={position} rotation={[0, rotation, 0]}>
      <mesh position={[0, 1.05, 0]} castShadow>
        <cylinderGeometry args={[0.04, 0.055, 2.1, 12]} />
        <meshStandardMaterial color="#0f172a" metalness={0.45} roughness={0.32} />
      </mesh>
      <mesh position={[0, 2.2, 0]} castShadow>
        <boxGeometry args={[0.48, 1.05, 0.28]} />
        <meshStandardMaterial color="#020617" metalness={0.28} roughness={0.4} />
      </mesh>
      {lensOrder.map((color, index) => (
        <Lens
          key={color}
          active={status === color}
          color={color}
          position={[0, 2.52 - index * 0.31, -0.16]}
        />
      ))}
      <mesh position={[0, 0.04, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[0.32, 20]} />
        <meshBasicMaterial color="#020617" transparent opacity={0.25} />
      </mesh>
    </group>
  );
}
