import Road3D from './Road3D.jsx';
import Sidewalk3D from './Sidewalk3D.jsx';
import TrafficLight3D from './TrafficLight3D.jsx';
import Trees3D from './Trees3D.jsx';
import Vehicle3D from './Vehicle3D.jsx';

export default function Intersection3D({ cars, signals, activeAxis, phaseTone }) {
  return (
    <group>
      <Road3D activeAxis={activeAxis} phaseTone={phaseTone} />
      <Sidewalk3D />
      <Trees3D />
      <TrafficLight3D position={[-5.8, 0.08, -5.8]} rotation={Math.PI} status={signals.north} />
      <TrafficLight3D position={[5.8, 0.08, 5.8]} rotation={0} status={signals.south} />
      <TrafficLight3D position={[5.8, 0.08, -5.8]} rotation={-Math.PI / 2} status={signals.east} />
      <TrafficLight3D position={[-5.8, 0.08, 5.8]} rotation={Math.PI / 2} status={signals.west} />
      {cars.map((car) => (
        <Vehicle3D key={car.id} car={car} />
      ))}
    </group>
  );
}
