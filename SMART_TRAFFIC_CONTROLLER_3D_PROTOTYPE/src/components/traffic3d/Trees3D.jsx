function Tree({ position, scale = 1 }) {
  return (
    <group position={position} scale={scale}>
      <mesh position={[0, 0.55, 0]} castShadow>
        <cylinderGeometry args={[0.08, 0.12, 0.9, 8]} />
        <meshStandardMaterial color="#7c2d12" roughness={0.85} />
      </mesh>
      <mesh position={[0, 1.18, 0]} castShadow>
        <sphereGeometry args={[0.55, 14, 12]} />
        <meshStandardMaterial color="#16a34a" roughness={0.7} />
      </mesh>
      <mesh position={[0.25, 1.38, -0.1]} castShadow>
        <sphereGeometry args={[0.42, 12, 10]} />
        <meshStandardMaterial color="#22c55e" roughness={0.72} />
      </mesh>
    </group>
  );
}

function StreetLamp({ position }) {
  return (
    <group position={position}>
      <mesh position={[0, 1.15, 0]} castShadow>
        <cylinderGeometry args={[0.035, 0.045, 2.3, 10]} />
        <meshStandardMaterial color="#334155" metalness={0.5} roughness={0.3} />
      </mesh>
      <mesh position={[0.25, 2.3, 0]} castShadow>
        <boxGeometry args={[0.55, 0.08, 0.08]} />
        <meshStandardMaterial color="#475569" metalness={0.45} roughness={0.3} />
      </mesh>
      <pointLight color="#bae6fd" distance={7} intensity={0.18} position={[0.55, 2.18, 0]} />
      <mesh position={[0.56, 2.18, 0]}>
        <sphereGeometry args={[0.08, 10, 8]} />
        <meshBasicMaterial color="#e0f2fe" />
      </mesh>
    </group>
  );
}

export default function Trees3D() {
  return (
    <group>
      {[
        [-12.5, -12.2],
        [-7.8, -13.8],
        [12.6, -12.9],
        [8.2, -8.2],
        [-12.5, 11.9],
        [-8.2, 8.6],
        [12.6, 12.4],
        [8.4, 8.2],
      ].map(([x, z], index) => (
        <Tree key={`${x}-${z}`} position={[x, 0.08, z]} scale={index % 3 === 0 ? 1.15 : 1} />
      ))}
      {[
        [-7.1, -7.1],
        [7.1, -7.1],
        [-7.1, 7.1],
        [7.1, 7.1],
      ].map(([x, z]) => (
        <StreetLamp key={`${x}-${z}`} position={[x, 0.08, z]} />
      ))}
    </group>
  );
}
