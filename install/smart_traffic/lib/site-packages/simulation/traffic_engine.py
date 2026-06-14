#!/usr/bin/env python3
"""
traffic_engine.py — Simulation Reelle Smart Traffic
=====================================================
Moteur de simulation de vehicules corrige :
  - Position-based physics : chaque voiture respecte la voiture devant
  - Feu rouge = arret dur a la stop-line
  - Feu vert  = les voitures partent en file indienne sans chevauchement
  - Arrivees aleatoires selon loi de Poisson
"""

import random
import time
import math
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ──────────────────────────────────────────────────────────
DIRECTIONS        = ["N", "S", "E", "O"]
MAX_QUEUE         = 15
CAR_LENGTH        = 4.5          # metres
CAR_GAP           = 2.0          # metres entre deux voitures
SAFE_DIST         = CAR_LENGTH + CAR_GAP   # 6.5 m espacement minimal
SPEED_APPROACH    = 10.0         # m/s en approche
SPEED_GREEN       = 12.0         # m/s en traversee
ARRIVAL_LINE      = -90.0        # position d'apparition (m)
STOP_LINE         = 0.0          # ligne d'arret (m)
INTERSECTION_DIST = 30.0         # sorti de l'intersection (m)

SCENARIOS = {
    "normal":       {"N": 0.30, "S": 0.25, "E": 0.35, "O": 0.20},
    "heure_pointe": {"N": 1.20, "S": 0.80, "E": 1.50, "O": 0.60},
    "incident_E":   {"N": 0.30, "S": 0.25, "E": 0.02, "O": 0.20},
    "nuit":         {"N": 0.05, "S": 0.05, "E": 0.05, "O": 0.05},
}

CAR_COLORS = [
    "#4FC3F7", "#81C784", "#FFD54F", "#FF8A65",
    "#CE93D8", "#80DEEA", "#FFAB91", "#A5D6A7",
    "#90CAF9", "#F48FB1",
]


@dataclass
class Car:
    """Un vehicule dans la simulation. Position en metres depuis stop-line."""
    car_id:    int
    direction: str
    position:  float      # metres. Negatif = avant l'intersection
    color:     str = "#4FC3F7"
    crossed:   bool = False   # True si a deja passe l'intersection
    created_at: float = field(default_factory=time.monotonic)


class DirectionQueue:
    """
    File de vehicules pour une direction.
    Physique position-based :
      - Tri par position descendante (en tete de file = position la plus haute = plus pres du stop)
      - Chaque voiture garde SAFE_DIST avec la voiture devant elle
      - Feu rouge = limite max a STOP_LINE
      - Feu vert  = limite max a INTERSECTION_DIST (libre)
    """

    def __init__(self, direction: str):
        self.direction = direction
        self.cars: List[Car] = []
        self._id_counter = 0
        self._lock = threading.Lock()
        self._total_crossed = 0

    def spawn_car(self) -> bool:
        """Cree une voiture si la file n'est pas pleine."""
        with self._lock:
            active = [c for c in self.cars if not c.crossed]
            if len(active) >= MAX_QUEUE:
                return False
            self._id_counter += 1
            car = Car(
                car_id    = self._id_counter,
                direction = self.direction,
                position  = ARRIVAL_LINE + random.uniform(-3, 3),
                color     = random.choice(CAR_COLORS),
            )
            self.cars.append(car)
            return True

    def update(self, dt: float, light_state: str) -> None:
        """
        Met a jour toutes les voitures de la file.
        Regles :
          - Voitures AVANT le stop-line (position < 0) : bloquees par feu rouge
          - Voitures DANS l'intersection (position >= 0) : continuent toujours
          - Chaque voiture garde SAFE_DIST avec la voiture devant
        """
        with self._lock:
            active = sorted(
                [c for c in self.cars if not c.crossed],
                key=lambda c: -c.position
            )

            for i, car in enumerate(active):
                # Est-ce que cette voiture est deja dans l'intersection ?
                in_intersection = (car.position > STOP_LINE + 0.001)

                # ── Calcul de la limite de position ──────────────
                if in_intersection:
                    # Deja dans l'intersection → TOUJOURS continuer
                    pos_limit = float('inf')
                elif light_state == "GREEN":
                    pos_limit = float('inf')
                else:
                    # Feu rouge, avant le stop → bloquer au stop-line
                    pos_limit = STOP_LINE

                # Respecter la distance de securite avec la voiture devant
                if i > 0:
                    car_ahead = active[i - 1]
                    ahead_limit = car_ahead.position - SAFE_DIST
                    # Si l'avant est aussi avant le stop et feu rouge
                    if not in_intersection and light_state == "RED":
                        ahead_limit = min(ahead_limit, STOP_LINE)
                    pos_limit = min(pos_limit, ahead_limit)

                # ── Vitesse adaptative ───────────────────────────
                gap = pos_limit - car.position
                if gap <= 0.5:
                    speed = 0.0
                elif gap < 5.0:
                    speed = 2.0 + (gap / 5.0) * 4.0
                elif gap < 20.0:
                    speed = 6.0 + (gap / 20.0) * (SPEED_APPROACH - 6.0)
                else:
                    speed = SPEED_GREEN if in_intersection else SPEED_APPROACH

                # ── Deplacement ──────────────────────────────────
                new_pos = car.position + speed * dt
                car.position = min(new_pos, pos_limit)

                # Marquer comme sortie
                if car.position >= INTERSECTION_DIST:
                    car.crossed = True
                    self._total_crossed += 1

            # Nettoyer les voitures sorties
            self.cars = [c for c in self.cars if not c.crossed]

    def snapshot(self) -> List[dict]:
        """Copie thread-safe pour la visualisation."""
        with self._lock:
            return [
                {
                    "car_id":   c.car_id,
                    "position": c.position,
                    "color":    c.color,
                }
                for c in self.cars
            ]

    @property
    def queue_length(self) -> int:
        with self._lock:
            return sum(1 for c in self.cars
                       if not c.crossed and c.position < STOP_LINE)

    @property
    def total_crossed(self) -> int:
        return self._total_crossed


class TrafficEngine:
    """Moteur principal : gere les 4 directions et les feux."""

    def __init__(self):
        self._queues: Dict[str, DirectionQueue] = {
            d: DirectionQueue(d) for d in DIRECTIONS
        }
        self._lights: Dict[str, str] = {d: "RED" for d in DIRECTIONS}
        self._scenario  = "normal"
        self._lambdas   = dict(SCENARIOS["normal"])
        self._running   = False
        self._thread: Optional[threading.Thread] = None
        self._lock      = threading.Lock()
        self._next_arrival: Dict[str, float] = {d: 1.0 for d in DIRECTIONS}

    def set_scenario(self, name: str) -> None:
        if name in SCENARIOS:
            with self._lock:
                self._scenario = name
                self._lambdas  = dict(SCENARIOS[name])

    def set_light(self, direction: str, state: str) -> None:
        with self._lock:
            self._lights[direction] = state

    def set_all_lights(self, lights: Dict[str, str]) -> None:
        with self._lock:
            self._lights.update(lights)

    def snapshot(self) -> Dict:
        return {
            d: {
                "cars":    self._queues[d].snapshot(),
                "light":   self._lights.get(d, "RED"),
                "queue":   self._queues[d].queue_length,
                "crossed": self._queues[d].total_crossed,
            }
            for d in DIRECTIONS
        }

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        """Boucle principale a 60 Hz."""
        target_dt = 1.0 / 60.0
        last_time = time.monotonic()

        while self._running:
            now  = time.monotonic()
            dt   = now - last_time
            last_time = now

            with self._lock:
                lambdas = dict(self._lambdas)
                lights  = dict(self._lights)

            # Arrivees de vehicules (processus de Poisson)
            for d in DIRECTIONS:
                self._next_arrival[d] -= dt
                if self._next_arrival[d] <= 0:
                    self._queues[d].spawn_car()
                    lam = lambdas.get(d, 0.3)
                    self._next_arrival[d] = (
                        random.expovariate(lam) if lam > 0 else 30.0
                    )

            # Mise a jour physique
            for d in DIRECTIONS:
                self._queues[d].update(dt, lights.get(d, "RED"))

            # Attendre le prochain tick
            elapsed = time.monotonic() - now
            time.sleep(max(0.0, target_dt - elapsed))
