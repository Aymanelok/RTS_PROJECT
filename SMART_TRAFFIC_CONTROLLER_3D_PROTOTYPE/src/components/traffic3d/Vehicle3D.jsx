import { useFrame } from '@react-three/fiber';
import { memo, useMemo, useRef } from 'react';
import { Color, Vector3 } from 'three';
import { damp, directionRotation, percentToWorld } from './sceneUtils.js';

const tmpTarget = new Vector3();

function Wheel({ position }) {
  return (
    <mesh position={position} rotation={[Math.PI / 2, 0, 0]} castShadow>
      <cylinderGeometry args={[0.18, 0.18, 0.14, 16]} />
      <meshStandardMaterial color="#020617" roughness={0.55} metalness={0.25} />
    </mesh>
  );
}

function LightDot({ position, color, intensity = 0.8 }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[0.055, 10, 8]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={intensity} />
    </mesh>
  );
}

function VehicleBody({ car }) {
  const dims = useMemo(() => {
    if (car.type === 'bus') return { width: 0.95, length: 2.45, height: 0.72, cabin: 1.85 };
    if (car.type === 'ambulance') return { width: 0.9, length: 2.15, height: 0.72, cabin: 1.45 };
    return { width: 0.82, length: 1.68, height: 0.5, cabin: 0.85 };
  }, [car.type]);
  const bodyColor = car.type === 'ambulance' ? '#f8fafc' : car.color;
  const color = useMemo(() => new Color(bodyColor), [bodyColor]);

  return (
    <group>
      <mesh position={[0, 0.33, 0]} castShadow receiveShadow>
        <boxGeometry args={[dims.width, dims.height, dims.length]} />
        <meshStandardMaterial color={color} metalness={0.2} roughness={0.36} />
      </mesh>
      <mesh position={[0, 0.77, car.type === 'bus' ? -0.05 : -0.15]} castShadow>
        <boxGeometry args={[dims.width * 0.78, dims.height * 0.62, dims.cabin]} />
        <meshStandardMaterial color={car.type === 'ambulance' ? '#e0f2fe' : '#1e293b'} metalness={0.12} roughness={0.25} transparent opacity={0.92} />
      </mesh>
      {car.type === 'ambulance' && (
        <>
          <mesh position={[0, 0.83, 0]}>
            <boxGeometry args={[0.12, 0.05, dims.length * 0.9]} />
            <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={0.25} />
          </mesh>
          <mesh position={[-0.18, 1.13, -0.2]}>
            <boxGeometry args={[0.18, 0.08, 0.16]} />
            <meshStandardMaterial color="#ef4444" emissive="#ef4444" emissiveIntensity={1.4} />
          </mesh>
          <mesh position={[0.18, 1.13, -0.2]}>
            <boxGeometry args={[0.18, 0.08, 0.16]} />
            <meshStandardMaterial color="#38bdf8" emissive="#38bdf8" emissiveIntensity={1.4} />
          </mesh>
          <pointLight color="#ef4444" distance={4} intensity={0.45} position={[-0.25, 1.2, -0.2]} />
          <pointLight color="#38bdf8" distance={4} intensity={0.45} position={[0.25, 1.2, -0.2]} />
        </>
      )}
      <Wheel position={[-dims.width * 0.55, 0.25, -dims.length * 0.32]} />
      <Wheel position={[dims.width * 0.55, 0.25, -dims.length * 0.32]} />
      <Wheel position={[-dims.width * 0.55, 0.25, dims.length * 0.32]} />
      <Wheel position={[dims.width * 0.55, 0.25, dims.length * 0.32]} />
      <LightDot color="#fef3c7" position={[-dims.width * 0.28, 0.38, -dims.length * 0.53]} />
      <LightDot color="#fef3c7" position={[dims.width * 0.28, 0.38, -dims.length * 0.53]} />
      <LightDot color="#ef4444" intensity={0.45} position={[-dims.width * 0.28, 0.36, dims.length * 0.53]} />
      <LightDot color="#ef4444" intensity={0.45} position={[dims.width * 0.28, 0.36, dims.length * 0.53]} />
      <mesh position={[0, 0.04, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[dims.length * 0.42, 24]} />
        <meshBasicMaterial color="#020617" transparent opacity={0.28} />
      </mesh>
    </group>
  );
}

function Vehicle3D({ car }) {
  const groupRef = useRef();
  const [targetX, , targetZ] = percentToWorld(car.x, car.y);

  useFrame((_, delta) => {
    if (!groupRef.current) return;
    tmpTarget.set(targetX, 0.12, targetZ);
    groupRef.current.position.x = damp(groupRef.current.position.x, tmpTarget.x, 16, delta);
    groupRef.current.position.y = damp(groupRef.current.position.y, tmpTarget.y, 16, delta);
    groupRef.current.position.z = damp(groupRef.current.position.z, tmpTarget.z, 16, delta);
    groupRef.current.rotation.y = damp(groupRef.current.rotation.y, directionRotation(car.direction), 10, delta);
  });

  return (
    <group
      ref={groupRef}
      position={[targetX, 0.12, targetZ]}
      rotation={[0, directionRotation(car.direction), 0]}
    >
      <VehicleBody car={car} />
    </group>
  );
}

export default memo(Vehicle3D);
