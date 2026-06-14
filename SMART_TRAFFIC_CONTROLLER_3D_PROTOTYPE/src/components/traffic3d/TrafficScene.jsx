import { Grid, Preload, Stars } from '@react-three/drei';
import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import CameraController from './CameraController.jsx';
import Intersection3D from './Intersection3D.jsx';

export default function TrafficScene({ cars, signals, activeAxis, phaseTone }) {
  return (
    <Canvas
      camera={{ position: [13, 18, 18], fov: 42, near: 0.1, far: 90 }}
      dpr={[1, 1.75]}
      shadows
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
    >
      <color attach="background" args={['#020617']} />
      <fog attach="fog" args={['#020617', 30, 64]} />
      <ambientLight intensity={0.62} />
      <directionalLight
        castShadow
        color="#e0f2fe"
        intensity={1.75}
        position={[12, 18, 10]}
        shadow-mapSize-height={1024}
        shadow-mapSize-width={1024}
      />
      <pointLight color="#22d3ee" distance={28} intensity={0.4} position={[-12, 8, -8]} />
      <Suspense fallback={null}>
        <Stars count={80} depth={40} factor={2} fade speed={0.2} />
        <Intersection3D activeAxis={activeAxis} cars={cars} phaseTone={phaseTone} signals={signals} />
        <Grid
          args={[46, 46]}
          cellColor="#0e7490"
          cellSize={2}
          fadeDistance={30}
          fadeStrength={1.5}
          position={[0, -0.07, 0]}
          sectionColor="#22d3ee"
          sectionSize={8}
        />
        <CameraController />
        <Preload all />
      </Suspense>
    </Canvas>
  );
}
