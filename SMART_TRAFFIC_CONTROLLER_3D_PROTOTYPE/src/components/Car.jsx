const rotationByDirection = {
  north: 180,
  south: 0,
  east: -90,
  west: 90,
};

export default function Car({ car }) {
  const {
    direction,
    color = '#38bdf8',
    x,
    y,
    state,
    type = 'car',
  } = car;
  const emergency = type === 'ambulance';

  return (
    <div
      className={`car ${direction} ${state} ${type} ${emergency ? 'emergency' : ''}`}
      style={{
        top: `${y}%`,
        left: `${x}%`,
        '--car-color': color,
        '--car-rotation': `${rotationByDirection[direction]}deg`,
      }}
      aria-label={emergency ? 'emergency vehicle' : `${direction} ${type}`}
      data-direction={direction}
      data-state={state}
      data-type={type}
      data-vehicle-id={car.id}
    >
      {emergency && <span className="beacon" />}
      <div className="car-body" />
      <span className="headlight left" />
      <span className="headlight right" />
    </div>
  );
}
