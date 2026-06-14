#!/usr/bin/env python3
"""
simulation.py — Smart Traffic Controller
=========================================
Phase 1 : Simulation complète SANS ROS2 ni Gazebo.

Architecture de simulation :
  - Threads indépendants pour chaque nœud
  - Files de messages (queues) pour la communication inter-nœuds
  - Durée : 60 secondes
  - Vérifications :
      ✓ Latence end-to-end < 180 ms (95e percentile)
      ✓ Aucune violation de sécurité (jamais 2 feux verts)
      ✓ Deadline misses < 5%

Usage :
    python3 simulation.py
    python3 simulation.py --duration 120 --verbose
"""

import argparse
import json
import math
import os
import queue
import random
import statistics
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DIRECTIONS        = ["N", "S", "E", "O"]
SIM_DURATION_S    = 60
SENSOR_PERIOD_S   = 0.100      # 10 Hz
SENSOR_DEADLINE   = 0.100      # 100 ms
CTRL_DEADLINE     = 0.080      # 80 ms
ACT_DEADLINE      = 0.050      # 50 ms
E2E_DEADLINE      = 0.180      # 180 ms end-to-end
MIN_GREEN_TIME    = 5.0
MAX_GREEN_TIME    = 30.0
HYSTERESIS        = 3
MAX_VEHICLES      = 30


# ══════════════════════════════════════════════
# MODÈLE DE TRAFIC
# ══════════════════════════════════════════════
class TrafficModel:
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self._t0 = time.monotonic()
        self._offsets = {d: random.uniform(0, 2 * math.pi) for d in DIRECTIONS}

    def sample(self) -> dict:
        t = time.monotonic() - self._t0
        return {
            d: max(0, min(MAX_VEHICLES,
                round(10 + 8 * math.sin(2 * math.pi * t / 30 + self._offsets[d])
                      + random.gauss(0, 1.5))))
            for d in DIRECTIONS
        }


# ══════════════════════════════════════════════
# MESSAGES
# ══════════════════════════════════════════════
@dataclass
class TrafficMessage:
    seq:       int
    timestamp: float
    counts:    dict
    t_sent:    float = field(default_factory=time.monotonic)


@dataclass
class CommandMessage:
    seq:          int
    timestamp:    float
    lights:       dict
    active_green: Optional[str]
    reason:       str
    t_sent:       float = field(default_factory=time.monotonic)


@dataclass
class FeedbackMessage:
    seq:     int
    status:  str
    lights:  dict
    changes: list
    lat_ms:  float


# ══════════════════════════════════════════════
# MÉTRIQUES GLOBALES (thread-safe)
# ══════════════════════════════════════════════
class Metrics:
    def __init__(self):
        self._lock = threading.Lock()

        self.sensor_lats:     list = []
        self.controller_lats: list = []
        self.actuator_lats:   list = []
        self.e2e_lats:        list = []

        self.sensor_missed    = 0
        self.controller_missed = 0
        self.actuator_missed  = 0

        self.safety_violations = 0
        self.total_cycles      = 0
        self.phase_changes     = 0

        self.light_history: list = []  # [(timestamp, active_green)]

    def add(self, name: str, lat_s: float) -> bool:
        """Ajoute une latence. Retourne True si deadline miss."""
        with self._lock:
            lat_ms = lat_s * 1000
            if name == "sensor":
                self.sensor_lats.append(lat_ms)
                if lat_s > SENSOR_DEADLINE:
                    self.sensor_missed += 1
                    return True
            elif name == "controller":
                self.controller_lats.append(lat_ms)
                if lat_s > CTRL_DEADLINE:
                    self.controller_missed += 1
                    return True
            elif name == "actuator":
                self.actuator_lats.append(lat_ms)
                if lat_s > ACT_DEADLINE:
                    self.actuator_missed += 1
                    return True
            elif name == "e2e":
                self.e2e_lats.append(lat_ms)
                if lat_s > E2E_DEADLINE:
                    return True
        return False

    def record_cycle(self, active: Optional[str]) -> None:
        with self._lock:
            self.total_cycles += 1
            self.light_history.append((time.time(), active))

    def record_violation(self) -> None:
        with self._lock:
            self.safety_violations += 1

    def record_phase_change(self) -> None:
        with self._lock:
            self.phase_changes += 1

    def percentile(self, data: list, p: float) -> float:
        if not data:
            return 0.0
        s = sorted(data)
        idx = max(0, int(p / 100 * len(s)) - 1)
        return s[idx]

    def report(self) -> dict:
        with self._lock:
            def stats(lst):
                if not lst:
                    return {"mean": 0, "max": 0, "min": 0, "p95": 0, "p99": 0, "n": 0}
                return {
                    "mean": statistics.mean(lst),
                    "max":  max(lst),
                    "min":  min(lst),
                    "p95":  self.percentile(lst, 95),
                    "p99":  self.percentile(lst, 99),
                    "n":    len(lst),
                }
            return {
                "sensor":     stats(self.sensor_lats),
                "controller": stats(self.controller_lats),
                "actuator":   stats(self.actuator_lats),
                "e2e":        stats(self.e2e_lats),
                "missed": {
                    "sensor":     self.sensor_missed,
                    "controller": self.controller_missed,
                    "actuator":   self.actuator_missed,
                },
                "safety_violations": self.safety_violations,
                "total_cycles":      self.total_cycles,
                "phase_changes":     self.phase_changes,
            }


# ══════════════════════════════════════════════
# NŒUD CAPTEUR (thread)
# ══════════════════════════════════════════════
class SimSensorNode(threading.Thread):
    def __init__(self, out_q: queue.Queue, metrics: Metrics, stop: threading.Event,
                 verbose: bool = False):
        super().__init__(name="SensorNode", daemon=True)
        self._out     = out_q
        self._metrics = metrics
        self._stop    = stop
        self._verbose = verbose
        self._model   = TrafficModel()
        self._seq     = 0

    def run(self):
        print("[SensorNode] ▶ Démarré (10 Hz)")
        next_wake = time.monotonic()

        while not self._stop.is_set():
            t_start = time.monotonic()
            self._seq += 1

            # Acquisition
            counts = self._model.sample()
            msg    = TrafficMessage(
                seq=self._seq,
                timestamp=time.time(),
                counts=counts,
                t_sent=t_start,
            )

            # Publication
            try:
                self._out.put_nowait(msg)
            except queue.Full:
                print(f"[SensorNode] ⚠ Queue pleine (seq={self._seq})")

            # Mesure latence
            lat = time.monotonic() - t_start
            missed = self._metrics.add("sensor", lat)
            if missed:
                print(f"[SensorNode] ⚠ DEADLINE MISS — lat={lat*1000:.1f} ms (seq={self._seq})")
            elif self._verbose:
                print(f"[SensorNode] seq={self._seq:04d} | trafic={[counts[d] for d in DIRECTIONS]} | lat={lat*1000:.2f} ms")

            # Attente période
            next_wake += SENSOR_PERIOD_S
            sleep_dur = next_wake - time.monotonic()
            if sleep_dur > 0:
                time.sleep(sleep_dur)

        print("[SensorNode] ■ Arrêté")


# ══════════════════════════════════════════════
# NŒUD CONTRÔLEUR (thread)
# ══════════════════════════════════════════════
class SimControllerNode(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q: queue.Queue,
                 metrics: Metrics, stop: threading.Event, verbose: bool = False):
        super().__init__(name="ControllerNode", daemon=True)
        self._in      = in_q
        self._out     = out_q
        self._metrics = metrics
        self._stop    = stop
        self._verbose = verbose

        # État ordonnanceur
        self._lights:       dict          = {d: "RED" for d in DIRECTIONS}
        self._active_green: Optional[str] = None
        self._green_since:  float         = 0.0

    def run(self):
        print("[ControllerNode] ▶ Démarré")
        while not self._stop.is_set():
            try:
                msg: TrafficMessage = self._in.get(timeout=0.2)
            except queue.Empty:
                continue

            t_start = time.monotonic()

            # Décision
            reason = self._decide(msg.counts)

            # Construction commande
            cmd = CommandMessage(
                seq=msg.seq,
                timestamp=time.time(),
                lights=self._lights.copy(),
                active_green=self._active_green,
                reason=reason,
                t_sent=t_start,
            )

            try:
                self._out.put_nowait(cmd)
            except queue.Full:
                print(f"[ControllerNode] ⚠ Queue pleine (seq={msg.seq})")

            # Métriques
            lat    = time.monotonic() - t_start
            e2e    = time.monotonic() - msg.t_sent
            missed = self._metrics.add("controller", lat)
            self._metrics.add("e2e", e2e)
            self._metrics.record_cycle(self._active_green)

            if missed:
                print(f"[ControllerNode] ⚠ DEADLINE MISS — lat={lat*1000:.1f} ms")
            elif self._verbose:
                print(f"[ControllerNode] {reason} | lat={lat*1000:.2f} ms | e2e={e2e*1000:.2f} ms")

    def _decide(self, counts: dict) -> str:
        now = time.monotonic()

        if self._active_green is None:
            best = max(counts, key=lambda d: counts[d])
            self._set_green(best)
            return f"INIT→{best}({counts[best]})"

        dur = now - self._green_since

        if dur >= MAX_GREEN_TIME:
            best = max(counts, key=lambda d: counts[d])
            self._set_green(best)
            return f"MAX_TIME→{best}"

        if dur < MIN_GREEN_TIME:
            return f"HOLD_{self._active_green}({dur:.1f}s<{MIN_GREEN_TIME}s)"

        best = max(counts, key=lambda d: counts[d])
        if best != self._active_green and counts[best] - counts[self._active_green] >= HYSTERESIS:
            prev = self._active_green
            self._set_green(best)
            return f"SWITCH {prev}→{best} Δ={counts[best]-counts[prev]}"

        return f"HOLD_{self._active_green}({counts[self._active_green]}veh)"

    def _set_green(self, direction: str) -> None:
        if direction != self._active_green:
            self._metrics.record_phase_change()
        for d in DIRECTIONS:
            self._lights[d] = "GREEN" if d == direction else "RED"
        self._active_green = direction
        self._green_since  = time.monotonic()


# ══════════════════════════════════════════════
# NŒUD ACTIONNEUR (thread)
# ══════════════════════════════════════════════
class SimActuatorNode(threading.Thread):
    def __init__(self, in_q: queue.Queue, metrics: Metrics, stop: threading.Event,
                 verbose: bool = False):
        super().__init__(name="ActuatorNode", daemon=True)
        self._in      = in_q
        self._metrics = metrics
        self._stop    = stop
        self._verbose = verbose
        self._current = {d: "RED" for d in DIRECTIONS}

    def run(self):
        print("[ActuatorNode] ▶ Démarré")
        while not self._stop.is_set():
            try:
                cmd: CommandMessage = self._in.get(timeout=0.2)
            except queue.Empty:
                continue

            t_start = time.monotonic()

            # ── VÉRIFICATION SÉCURITÉ ─────────────────────────
            green_dirs = [d for d, s in cmd.lights.items() if s == "GREEN"]
            if len(green_dirs) > 1:
                self._metrics.record_violation()
                print(f"[ActuatorNode] 🚨 VIOLATION CRITIQUE — {len(green_dirs)} feux verts : {green_dirs}")
                continue  # Commande rejetée

            # ── Application ───────────────────────────────────
            changes = []
            for d in DIRECTIONS:
                old = self._current.get(d, "RED")
                new = cmd.lights.get(d, "RED")
                if old != new:
                    changes.append((d, old, new))
                    self._current[d] = new

            if changes and self._verbose:
                for d, o, n in changes:
                    EMOJI = {"GREEN": "🟢", "RED": "🔴", "YELLOW": "🟡"}
                    print(f"[ActuatorNode] 🚦 {d}: {EMOJI[o]}→{EMOJI[n]}")

            # ── Métriques ─────────────────────────────────────
            lat    = time.monotonic() - t_start
            missed = self._metrics.add("actuator", lat)
            if missed:
                print(f"[ActuatorNode] ⚠ DEADLINE MISS — lat={lat*1000:.1f} ms")

        print("[ActuatorNode] ■ Arrêté")


# ══════════════════════════════════════════════
# RAPPORT DE SIMULATION
# ══════════════════════════════════════════════
def print_report(metrics: Metrics, duration: float) -> dict:
    report = metrics.report()

    SEPARATOR = "═" * 65
    SEP2      = "─" * 65

    print(f"\n{SEPARATOR}")
    print("  📊  RAPPORT DE SIMULATION — SMART TRAFFIC CONTROLLER")
    print(f"{SEPARATOR}")
    print(f"  Durée          : {duration:.1f} s")
    print(f"  Cycles totaux  : {report['total_cycles']}")
    print(f"  Changements de phase : {report['phase_changes']}")
    print(f"{SEP2}")

    for node_name, dl_ms in [("sensor", SENSOR_DEADLINE*1000),
                               ("controller", CTRL_DEADLINE*1000),
                               ("actuator", ACT_DEADLINE*1000),
                               ("e2e", E2E_DEADLINE*1000)]:
        s   = report[node_name]
        lbl = {"sensor": "CAPTEUR   ", "controller": "CONTRÔLEUR", "actuator": "ACTIONNEUR", "e2e": "END-TO-END"}[node_name]
        ok  = "✅" if s["p95"] <= dl_ms else "❌"
        print(f"\n  {ok} {lbl} (deadline={dl_ms:.0f} ms)")
        print(f"     Moy={s['mean']:6.2f} ms | Max={s['max']:6.2f} ms | "
              f"P95={s['p95']:6.2f} ms | P99={s['p99']:6.2f} ms | N={s['n']}")

    print(f"\n{SEP2}")
    print("  ⏱  DEADLINE MISSES")

    total_s = report["sensor"]["n"]
    total_c = report["controller"]["n"]
    total_a = report["actuator"]["n"]

    miss_s  = report["missed"]["sensor"]
    miss_c  = report["missed"]["controller"]
    miss_a  = report["missed"]["actuator"]

    rate_s  = miss_s / total_s * 100 if total_s else 0
    rate_c  = miss_c / total_c * 100 if total_c else 0
    rate_a  = miss_a / total_a * 100 if total_a else 0

    print(f"     Capteur    : {miss_s:4d}/{total_s} ({rate_s:.2f}%) {'✅' if rate_s < 5 else '❌'}")
    print(f"     Contrôleur : {miss_c:4d}/{total_c} ({rate_c:.2f}%) {'✅' if rate_c < 5 else '❌'}")
    print(f"     Actionneur : {miss_a:4d}/{total_a} ({rate_a:.2f}%) {'✅' if rate_a < 5 else '❌'}")

    print(f"\n{SEP2}")
    print("  🔒  VÉRIFICATION FORMELLE")
    sv = report["safety_violations"]
    print(f"     Violations de sécurité (2 verts simultanés) : {sv}")
    print(f"     Invariant respecté : {'✅ OUI' if sv == 0 else '❌ NON — CRITIQUE'}")

    # ── Résumé global ─────────────────────────────────────────
    print(f"\n{SEP2}")
    p95_e2e    = report["e2e"]["p95"]
    schedulable = (
        p95_e2e <= E2E_DEADLINE * 1000
        and sv == 0
        and rate_s < 5
        and rate_c < 5
        and rate_a < 5
    )
    verdict = "✅ SYSTÈME VALIDE — Toutes les contraintes sont respectées" if schedulable \
              else "❌ SYSTÈME NON CONFORME — Contraintes violées"
    print(f"\n  {verdict}")
    print(f"{SEPARATOR}\n")

    return {"schedulable": schedulable, "report": report}


def export_csv(metrics: Metrics, path: str) -> None:
    import csv
    rows = []
    for lat in metrics.sensor_lats:
        rows.append({"node": "sensor", "latency_ms": lat, "deadline_ms": SENSOR_DEADLINE*1000})
    for lat in metrics.controller_lats:
        rows.append({"node": "controller", "latency_ms": lat, "deadline_ms": CTRL_DEADLINE*1000})
    for lat in metrics.actuator_lats:
        rows.append({"node": "actuator", "latency_ms": lat, "deadline_ms": ACT_DEADLINE*1000})
    for lat in metrics.e2e_lats:
        rows.append({"node": "e2e", "latency_ms": lat, "deadline_ms": E2E_DEADLINE*1000})

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["node", "latency_ms", "deadline_ms"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  📁 CSV exporté : {path} ({len(rows)} lignes)")


# ══════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════
def run_simulation(duration: float = SIM_DURATION_S, verbose: bool = False) -> dict:
    print(f"\n{'═'*65}")
    print("  🚦  SMART TRAFFIC CONTROLLER — SIMULATION PHASE 1")
    print(f"{'═'*65}")
    print(f"  Durée     : {duration} s")
    print(f"  Fréquence : 10 Hz (capteur)")
    print(f"  Deadlines : Capteur={SENSOR_DEADLINE*1000:.0f}ms | "
          f"Ctrl={CTRL_DEADLINE*1000:.0f}ms | Act={ACT_DEADLINE*1000:.0f}ms | "
          f"E2E={E2E_DEADLINE*1000:.0f}ms")
    print(f"{'─'*65}\n")

    # ── Queues de communication ───────────────────────────────
    q_sensor_ctrl = queue.Queue(maxsize=20)
    q_ctrl_act    = queue.Queue(maxsize=20)

    # ── Métriques partagées ───────────────────────────────────
    metrics = Metrics()
    stop    = threading.Event()

    # ── Nœuds ────────────────────────────────────────────────
    sensor     = SimSensorNode(q_sensor_ctrl, metrics, stop, verbose)
    controller = SimControllerNode(q_sensor_ctrl, q_ctrl_act, metrics, stop, verbose)
    actuator   = SimActuatorNode(q_ctrl_act, metrics, stop, verbose)

    # ── Démarrage ─────────────────────────────────────────────
    t_start = time.monotonic()
    for t in [sensor, controller, actuator]:
        t.start()

    # ── Boucle principale avec progress bar ───────────────────
    try:
        while time.monotonic() - t_start < duration:
            elapsed = time.monotonic() - t_start
            pct     = elapsed / duration * 100
            bar     = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            snap    = metrics.report()

            sys.stdout.write(
                f"\r  [{bar}] {pct:5.1f}% | "
                f"Cycles:{snap['total_cycles']:4d} | "
                f"E2E_P95:{snap['e2e']['p95']:5.1f}ms | "
                f"Violations:{snap['safety_violations']}"
            )
            sys.stdout.flush()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n  Simulation interrompue.")

    # ── Arrêt propre ──────────────────────────────────────────
    stop.set()
    actual_duration = time.monotonic() - t_start
    print()

    # ── Rapport ───────────────────────────────────────────────
    result = print_report(metrics, actual_duration)

    # ── Export CSV ────────────────────────────────────────────
    csv_path = f"simulation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    export_csv(metrics, csv_path)

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Smart Traffic Controller — Simulation Phase 1"
    )
    parser.add_argument("--duration", type=float, default=SIM_DURATION_S,
                        help=f"Durée de simulation en secondes (défaut: {SIM_DURATION_S})")
    parser.add_argument("--verbose", action="store_true",
                        help="Affichage détaillé des événements")
    args = parser.parse_args()

    result = run_simulation(duration=args.duration, verbose=args.verbose)
    sys.exit(0 if result["schedulable"] else 1)
