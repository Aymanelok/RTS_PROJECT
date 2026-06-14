import { OrbitControls } from '@react-three/drei';

export default function CameraController() {
  return (
    <OrbitControls
      enableDamping
      enablePan={false}
      maxDistance={36}
      maxPolarAngle={1.15}
      minDistance={20}
      minPolarAngle={0.72}
      target={[0, 0, 0]}
    />
  );
}
