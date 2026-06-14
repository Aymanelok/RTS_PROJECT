const lights = ['red', 'yellow', 'green'];

export default function TrafficLight({ status = 'red', className = '', orientation = 'vertical', label }) {
  return (
    <div className={`traffic-light ${orientation} ${className}`} aria-label={`${label} traffic light`}>
      {lights.map((light) => (
        <span
          key={light}
          className={`lamp ${light} ${status === light ? 'active' : ''}`}
          title={`${label} ${light}`}
        />
      ))}
    </div>
  );
}
