# Real-Time Smart Traffic Controller

Professional React/Vite dashboard prototype for a ROS2 smart traffic light control project.

## Features

- Dark smart-city control center interface
- Animated 2D four-way intersection simulation
- North/South, East/West, yellow transition, and all-red clearance phase states
- Real-time simulated queue counters, latency, jitter, CPU, RAM, and clock updates
- Safety Monitor with conflict and fault counters
- Recharts telemetry panels for traffic queues, latency, CPU by node, and health donut
- Phase timeline in a Gantt-style layout
- Reusable React components for presentation-friendly code structure

## Tech Stack

- React.js
- Vite
- Tailwind CSS
- Recharts
- Lucide React

## Run Locally

```bash
npm install
npm run dev
```

Then open the local Vite URL shown in the terminal, usually:

```text
http://localhost:5173
```

## Build

```bash
npm run build
```

The production files will be generated in `dist/`.
