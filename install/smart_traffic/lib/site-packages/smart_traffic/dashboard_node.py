#!/usr/bin/env python3
"""
dashboard_node.py — Smart Traffic Controller v5
================================================
Nœud tableau de bord : visualisation et analyse temps réel avancée.

NOUVELLES FONCTIONNALITÉS TEMPS-RÉEL :
  ┌─ Métriques RT ──────────────────────────────────────────────────────┐
  │  • Jitter inter-arrivée par nœud (écart à la période nominale)      │
  │  • Latence End-to-End pipeline complet (sensor→ctrl→actuator)       │
  │  • WCET tracker (Worst-Case Execution Time glissant)                │
  │  • Taux de deadline miss en % (miss rate), pas seulement compteur   │
  │  • Fenêtres glissantes : 10 s / 30 s / 60 s par nœud               │
  │  • Détection de bursts de misses (3 misses consécutifs = CRITIQUE)  │
  └─────────────────────────────────────────────────────────────────────┘
  ┌─ Schedulabilité ────────────────────────────────────────────────────┐
  │  • Vérification Rate Monotonic (RM) en ligne                        │
  │  • Calcul utilisation CPU U = Σ(Ci/Ti) dynamique                   │
  │  • Test d'admissibilité RM : U ≤ n(2^(1/n) − 1)                    │
  └─────────────────────────────────────────────────────────────────────┘
  ┌─ Sécurité ──────────────────────────────────────────────────────────┐
  │  • Moniteur invariant : |{d∈D | lights[d]=GREEN}| ≤ 1 (runtime)   │
  │  • Détection perte de messages (gaps de séquence)                   │
  │  • Alerte CRITIQUE si violation sécurité                            │
  └─────────────────────────────────────────────────────────────────────┘
  ┌─ Infrastructure ────────────────────────────────────────────────────┐
  │  • Serveur HTTP intégré port 8765 (dashboard HTML + /api/status)    │
  │  • Surveillance ressources système : CPU%, RAM%, latence OS         │
  │  • Health-check timer 5 s avec pub /dashboard_health               │
  │  • Export CSV enrichi (jitter, e2e, wcet, miss_rate)               │
  │  • Graphe E2E + jitter sensor dans matplotlib                       │
  └─────────────────────────────────────────────────────────────────────┘

Dépendances : matplotlib, pandas, numpy, psutil (optionnel)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String

import json
import time
import os
import math
import threading
import http.server
import socketserver
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
from matplotlib.animation import FuncAnimation
import pandas as pd
import numpy as np

# psutil optionnel (monitoring système)
try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

# ══════════════════════════════════════════════════════════════
#  CONSTANTES TEMPS-RÉEL
# ══════════════════════════════════════════════════════════════
DIRECTIONS        = ["N", "S", "E", "O"]
DIR_LABELS        = {"N": "Nord", "S": "Sud", "E": "Est", "O": "Ouest"}
MAX_POINTS        = 300           # taille historique graphes

# Deadlines strictes (ms)
DEADLINE_SENSOR   = 100.0
DEADLINE_CTRL     = 80.0
DEADLINE_ACT      = 50.0
DEADLINE_E2E      = 200.0         # Deadline end-to-end pipeline

# Périodes nominales (ms) pour calcul jitter
PERIOD_SENSOR     = 100.0
PERIOD_CTRL       = 100.0
PERIOD_ACT        = 100.0

# WCET estimés (ms) — utilisés pour RM
WCET_SENSOR       = 5.0
WCET_CTRL         = 8.0
WCET_ACT          = 4.0

# Seuils d'alerte
JITTER_WARN_MS    = 15.0          # ms — tolérance jitter avant warning
BURST_MISS_COUNT  = 3             # misses consécutifs → alerte CRITIQUE
MISS_RATE_WARN    = 0.02          # 2 % miss rate → warning
MISS_RATE_CRIT    = 0.05          # 5 % miss rate → critique

# Fenêtres glissantes (secondes)
WINDOW_SHORT      = 10.0
WINDOW_MED        = 30.0
WINDOW_LONG       = 60.0

# Infrastructure
UPDATE_INTERVAL   = 350           # ms — refresh matplotlib
CSV_EXPORT_DIR    = os.path.expanduser("~/smart_traffic_logs")
HTTP_PORT         = 8765
HEALTH_PERIOD_S   = 5.0           # secondes entre health-checks

# Schedulabilité RM : Σ(Ci/Ti) ≤ n(2^(1/n) − 1)
N_TASKS           = 3
RM_BOUND          = N_TASKS * (2 ** (1.0 / N_TASKS) - 1)   # ≈ 0.7798

RT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

# ── Palette de couleurs
COLORS = {
    "sensor":      "#00D4FF",
    "controller":  "#FF7F50",
    "actuator":    "#39FF14",
    "e2e":         "#C084FC",
    "jitter":      "#FACC15",
    "deadline":    "#FF2D55",
    "wcet":        "#FB923C",
    "bg":          "#06090F",
    "panel":       "#0B1120",
    "surface":     "#111827",
    "text":        "#E8EDF5",
    "text_dim":    "#6B7A99",
    "grid":        "#1A2340",
    "GREEN":       "#2ECC71",
    "RED":         "#E74C3C",
    "YELLOW":      "#F39C12",
    "border":      "#1E2A44",
    "CRITICAL":    "#FF0055",
}

LIGHT_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}


# ══════════════════════════════════════════════════════════════
#  MONITEUR DE SÉCURITÉ (runtime verification)
# ══════════════════════════════════════════════════════════════
class SafetyMonitor:
    """
    Vérification en ligne de l'invariant de sécurité critique :
      ∀ t : |{ d ∈ DIRECTIONS | lights[d] = GREEN }| ≤ 1

    Implémenté comme un model checker en ligne (runtime verification).
    """

    def __init__(self, logger=None):
        self._logger         = logger
        self.violations      = 0
        self.checks          = 0
        self.last_violation  : Optional[str] = None
        self._lock           = threading.Lock()

    def check(self, lights: Dict[str, str]) -> bool:
        """
        Vérifie l'invariant. Retourne True si sûr, False si violation.
        Thread-safe.
        """
        with self._lock:
            self.checks += 1
            green_dirs = [d for d, s in lights.items() if s == "GREEN"]
            if len(green_dirs) > 1:
                self.violations += 1
                msg = (f"🚨 VIOLATION #{self.violations}: "
                       f"{len(green_dirs)} feux VERTS simultanés : {green_dirs}")
                self.last_violation = f"{datetime.now():%H:%M:%S} — {msg}"
                if self._logger:
                    self._logger.fatal(f"[SafetyMonitor] {msg}")
                return False
            return True

    @property
    def rate(self) -> float:
        """Taux de violation (%)."""
        with self._lock:
            return (self.violations / self.checks * 100) if self.checks else 0.0


# ══════════════════════════════════════════════════════════════
#  ANALYSEUR DE JITTER
# ══════════════════════════════════════════════════════════════
class JitterAnalyzer:
    """
    Mesure le jitter inter-arrivée d'un nœud périodique.
    Jitter = |t_arrivée − t_attendue| selon la période nominale.
    """

    def __init__(self, period_ms: float, window: int = MAX_POINTS):
        self._period    = period_ms / 1000.0     # en secondes
        self._last_t    : Optional[float] = None
        self.jitter_ms  : deque = deque(maxlen=window)
        self._lock      = threading.Lock()

    def record(self) -> Optional[float]:
        """Enregistre une arrivée et retourne le jitter en ms."""
        now = time.monotonic()
        with self._lock:
            if self._last_t is not None:
                elapsed   = now - self._last_t
                jitter    = abs(elapsed - self._period) * 1000.0
                self.jitter_ms.append(jitter)
                self._last_t = now
                return jitter
            self._last_t = now
            return None

    def stats(self) -> Dict:
        with self._lock:
            data = list(self.jitter_ms)
        if not data:
            return {"mean": 0, "max": 0, "p95": 0}
        arr = sorted(data)
        return {
            "mean": round(float(np.mean(arr)), 3),
            "max":  round(float(max(arr)), 3),
            "p95":  round(arr[int(0.95 * len(arr))], 3),
        }


# ══════════════════════════════════════════════════════════════
#  TRACKER WCET (Worst Case Execution Time)
# ══════════════════════════════════════════════════════════════
class WCETTracker:
    """
    Suit le WCET observé sur une fenêtre glissante.
    Si WCET_observé > WCET_estimé → WCET_bust détecté.
    """

    def __init__(self, wcet_nominal_ms: float, window: int = MAX_POINTS):
        self._nominal = wcet_nominal_ms
        self._history : deque = deque(maxlen=window)
        self._lock    = threading.Lock()
        self.busts    = 0

    def record(self, exec_ms: float) -> bool:
        """Retourne True si bust WCET détecté."""
        bust = exec_ms > self._nominal
        with self._lock:
            self._history.append(exec_ms)
            if bust:
                self.busts += 1
        return bust

    @property
    def wcet_observed(self) -> float:
        with self._lock:
            return max(self._history, default=0.0)

    @property
    def history(self) -> List[float]:
        with self._lock:
            return list(self._history)


# ══════════════════════════════════════════════════════════════
#  FENÊTRE GLISSANTE TEMPORELLE
# ══════════════════════════════════════════════════════════════
class SlidingWindow:
    """
    Stocke des couples (timestamp, valeur) et permet d'extraire
    les statistiques sur des intervalles glissants.
    """

    def __init__(self, maxlen: int = 1000):
        self._data : deque = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, value: float) -> None:
        with self._lock:
            self._data.append((time.monotonic(), value))

    def get_window(self, seconds: float) -> List[float]:
        """Retourne les valeurs des `seconds` dernières secondes."""
        cutoff = time.monotonic() - seconds
        with self._lock:
            return [v for t, v in self._data if t >= cutoff]

    def stats_window(self, seconds: float, deadline: float) -> Dict:
        vals = self.get_window(seconds)
        if not vals:
            return {"mean": 0, "max": 0, "p95": 0, "miss_rate": 0, "n": 0}
        arr = sorted(vals)
        missed = sum(1 for v in vals if v > deadline)
        return {
            "mean":      round(float(np.mean(arr)), 2),
            "max":       round(float(max(arr)), 2),
            "p95":       round(arr[int(0.95 * len(arr))], 2),
            "miss_rate": round(missed / len(vals), 4),
            "n":         len(vals),
        }


# ══════════════════════════════════════════════════════════════
#  TRACKER E2E LATENCE
# ══════════════════════════════════════════════════════════════
class E2ETracker:
    """
    Calcule la latence end-to-end : sensor_lat + ctrl_lat + act_lat.
    Un triplet (s, c, a) est formé dès que les 3 nœuds ont publié
    pour le même cycle (seq).
    """

    def __init__(self, window: int = MAX_POINTS):
        self._lock  = threading.Lock()
        self._e2e   : deque = deque(maxlen=window)
        self._buf_s : deque = deque(maxlen=10)    # buffer sensor_lat
        self._buf_c : deque = deque(maxlen=10)    # buffer ctrl_lat
        self._buf_a : deque = deque(maxlen=10)    # buffer act_lat
        self.misses = 0

    def add_sensor(self, lat: float) -> None:
        with self._lock:
            self._buf_s.append(lat)
            self._try_compute()

    def add_ctrl(self, lat: float) -> None:
        with self._lock:
            self._buf_c.append(lat)
            self._try_compute()

    def add_act(self, lat: float) -> None:
        with self._lock:
            self._buf_a.append(lat)
            self._try_compute()

    def _try_compute(self) -> None:
        """Calcule E2E si les 3 buffers ont au moins un élément."""
        if self._buf_s and self._buf_c and self._buf_a:
            e2e = self._buf_s[-1] + self._buf_c[-1] + self._buf_a[-1]
            self._e2e.append(e2e)
            if e2e > DEADLINE_E2E:
                self.misses += 1

    @property
    def history(self) -> List[float]:
        with self._lock:
            return list(self._e2e)

    def stats(self) -> Dict:
        data = self.history
        if not data:
            return {"mean": 0, "max": 0, "p95": 0, "miss_rate": 0}
        arr = sorted(data)
        missed = sum(1 for v in data if v > DEADLINE_E2E)
        return {
            "mean":      round(float(np.mean(arr)), 2),
            "max":       round(float(max(arr)), 2),
            "p95":       round(arr[int(0.95 * len(arr))], 2),
            "miss_rate": round(missed / len(data), 4),
        }


# ══════════════════════════════════════════════════════════════
#  VÉRIFICATEUR RM EN LIGNE
# ══════════════════════════════════════════════════════════════
class RMSchedulabilityChecker:
    """
    Vérifie la schedulabilité Rate-Monotonic en ligne.
    U = Σ(Ci/Ti) — test suffisant : U ≤ n·(2^(1/n) − 1)
    """

    def __init__(self):
        # (WCET_observé, Période) pour chaque nœud
        self._tasks = {
            "sensor":     {"wcet": WCET_SENSOR, "period": PERIOD_SENSOR},
            "controller": {"wcet": WCET_CTRL,   "period": PERIOD_CTRL},
            "actuator":   {"wcet": WCET_ACT,     "period": PERIOD_ACT},
        }
        self._lock = threading.Lock()

    def update_wcet(self, node: str, wcet_ms: float) -> None:
        """Met à jour le WCET observé pour un nœud."""
        with self._lock:
            if node in self._tasks:
                self._tasks[node]["wcet"] = max(
                    self._tasks[node]["wcet"], wcet_ms
                )

    def utilization(self) -> float:
        """Calcule U = Σ(Ci/Ti)."""
        with self._lock:
            return sum(
                t["wcet"] / t["period"]
                for t in self._tasks.values()
            )

    def is_schedulable(self) -> bool:
        return self.utilization() <= RM_BOUND

    def report(self) -> Dict:
        u = self.utilization()
        with self._lock:
            tasks_copy = {k: dict(v) for k, v in self._tasks.items()}
        return {
            "utilization": round(u, 4),
            "bound":       round(RM_BOUND, 4),
            "schedulable": u <= RM_BOUND,
            "margin_pct":  round((RM_BOUND - u) / RM_BOUND * 100, 1),
            "tasks":       tasks_copy,
        }


# ══════════════════════════════════════════════════════════════
#  SYSTÈME D'ALERTES
# ══════════════════════════════════════════════════════════════
class AlertManager:
    """
    Gestion centralisée des alertes avec niveaux de sévérité.
    Niveaux : INFO / WARN / CRITICAL
    Détecte les bursts de misses consécutifs.
    """

    LEVELS = {"INFO": 0, "WARN": 1, "CRITICAL": 2}

    def __init__(self, maxlen: int = 100):
        self._alerts     : deque = deque(maxlen=maxlen)
        self._lock       = threading.Lock()
        self._consec     = {"sensor": 0, "controller": 0, "actuator": 0}
        self.counts      = {"INFO": 0, "WARN": 0, "CRITICAL": 0}

    def push(self, level: str, source: str, msg: str) -> None:
        entry = {
            "t":      datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level":  level,
            "source": source,
            "msg":    msg,
        }
        with self._lock:
            self._alerts.append(entry)
            self.counts[level] = self.counts.get(level, 0) + 1

    def check_miss(self, node: str, missed: bool) -> Optional[str]:
        """
        Suit les misses consécutifs. Si BURST_MISS_COUNT misses de suite →
        retourne niveau CRITICAL, sinon WARN ou None.
        """
        if missed:
            self._consec[node] = self._consec.get(node, 0) + 1
            if self._consec[node] >= BURST_MISS_COUNT:
                return "CRITICAL"
            return "WARN"
        else:
            self._consec[node] = 0
            return None

    def recent(self, n: int = 20) -> List[Dict]:
        with self._lock:
            return list(self._alerts)[-n:]

    def snapshot(self) -> Dict:
        with self._lock:
            return {
                "recent": list(self._alerts)[-30:],
                "counts": dict(self.counts),
            }


# ══════════════════════════════════════════════════════════════
#  SERVEUR HTTP
# ══════════════════════════════════════════════════════════════
class DashboardHTTPHandler(http.server.BaseHTTPRequestHandler):
    """
    Sert le dashboard HTML + endpoint REST /api/status.
    GET /           → smart_traffic_dashboard.html
    GET /api/status → JSON snapshot complet (sans csv_rows)
    GET /api/rm     → rapport schedulabilité RM
    GET /api/alerts → alertes récentes
    """

    store_ref  = None
    rm_ref     = None
    alert_ref  = None

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_html()
        elif self.path == "/api/status":
            self._serve_status()
        elif self.path == "/api/rm":
            self._serve_rm()
        elif self.path == "/api/alerts":
            self._serve_alerts()
        else:
            self.send_response(404)
            self.end_headers()

    # ── HTML
    def _serve_html(self):
        for p in [
            Path(__file__).parent / "smart_traffic_dashboard.html",
            Path(__file__).parent / "dashboard.html",
        ]:
            if p.exists():
                content = p.read_bytes()
                self._send(200, "text/html; charset=utf-8", content)
                return
        self._send(404, "text/plain", b"HTML not found")

    # ── /api/status
    def _serve_status(self):
        if self.store_ref:
            snap = self.store_ref.snapshot()
            snap.pop("csv_rows", None)
            self._send(200, "application/json", json.dumps(snap).encode())
        else:
            self._send(200, "application/json", b"{}")

    # ── /api/rm
    def _serve_rm(self):
        if self.rm_ref:
            self._send(200, "application/json",
                       json.dumps(self.rm_ref.report()).encode())
        else:
            self._send(200, "application/json", b"{}")

    # ── /api/alerts
    def _serve_alerts(self):
        if self.alert_ref:
            self._send(200, "application/json",
                       json.dumps(self.alert_ref.snapshot()).encode())
        else:
            self._send(200, "application/json", b"{}")

    def _send(self, code: int, ct: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # Silence des logs HTTP


# ══════════════════════════════════════════════════════════════
#  DATA STORE — ENRICHI
# ══════════════════════════════════════════════════════════════
class DataStore:
    """
    Stockage thread-safe centralisé avec :
    - Historiques de latences (sensor, ctrl, actuator, e2e)
    - Jitter trackers par nœud
    - WCET trackers par nœud
    - Fenêtres glissantes (10s / 30s / 60s)
    - Compteurs et miss rates
    - Données système (CPU, RAM)
    """

    def __init__(self, safety: SafetyMonitor, alerts: AlertManager,
                 rm: RMSchedulabilityChecker):
        self._lock = threading.Lock()

        # ── Références aux moniteurs
        self._safety = safety
        self._alerts = alerts
        self._rm     = rm

        # ── Historiques latences (pour graphes)
        self.sensor_lat     : deque = deque(maxlen=MAX_POINTS)
        self.controller_lat : deque = deque(maxlen=MAX_POINTS)
        self.actuator_lat   : deque = deque(maxlen=MAX_POINTS)
        self.timestamps     : deque = deque(maxlen=MAX_POINTS)

        # ── Jitter trackers
        self.jitter_sensor  = JitterAnalyzer(PERIOD_SENSOR)
        self.jitter_ctrl    = JitterAnalyzer(PERIOD_CTRL)
        self.jitter_act     = JitterAnalyzer(PERIOD_ACT)

        # ── WCET trackers
        self.wcet_sensor    = WCETTracker(WCET_SENSOR)
        self.wcet_ctrl      = WCETTracker(WCET_CTRL)
        self.wcet_act       = WCETTracker(WCET_ACT)

        # ── Fenêtres glissantes
        self.sw_sensor      = SlidingWindow()
        self.sw_ctrl        = SlidingWindow()
        self.sw_act         = SlidingWindow()

        # ── E2E tracker
        self.e2e            = E2ETracker()

        # ── Deadline misses (cumulatif)
        self.missed = {"sensor": 0, "controller": 0, "actuator": 0}
        self.total  = {"sensor": 0, "controller": 0, "actuator": 0}

        # ── État feux
        self.lights       : Dict[str, str] = {d: "RED" for d in DIRECTIONS}
        self.active_green : Optional[str]  = None
        self.counts       : Dict[str, int] = {d: 0 for d in DIRECTIONS}

        # ── CSV rows
        self.csv_rows : list = []

        # ── Métriques système
        self.sys_cpu_pct  : deque = deque(maxlen=60)
        self.sys_ram_pct  : deque = deque(maxlen=60)

        # ── Détection perte de messages (séquences)
        self._last_seq    : Dict[str, int] = {}
        self.msg_lost     : Dict[str, int] = {"sensor": 0, "controller": 0, "actuator": 0}

        # ── Compteur global
        self.total_msgs   = 0

    # ──────────────────────────────────────────────
    # Méthodes d'ajout
    # ──────────────────────────────────────────────
    def add_sensor(self, lat_ms: float, missed: int, seq: int = -1) -> None:
        jitter = self.jitter_sensor.record()
        bust   = self.wcet_sensor.record(lat_ms)
        self._rm.update_wcet("sensor", lat_ms)
        self.sw_sensor.add(lat_ms)
        self.e2e.add_sensor(lat_ms)

        with self._lock:
            self.sensor_lat.append(lat_ms)
            self.timestamps.append(time.time())
            self.missed["sensor"] = missed
            self.total["sensor"]  = self.total.get("sensor", 0) + 1
            self.total_msgs += 1
            # Détection perte séquence
            self._check_seq("sensor", seq)
            self.csv_rows.append({
                "ts":          time.time(),
                "node":        "sensor",
                "latency_ms":  lat_ms,
                "deadline_ms": DEADLINE_SENSOR,
                "miss":        int(lat_ms > DEADLINE_SENSOR),
                "jitter_ms":   round(jitter, 3) if jitter else 0,
                "wcet_bust":   int(bust),
                "seq":         seq,
            })

        # Alertes
        is_miss = lat_ms > DEADLINE_SENSOR
        lvl = self._alerts.check_miss("sensor", is_miss)
        if lvl:
            self._alerts.push(lvl, "sensor",
                              f"Deadline miss lat={lat_ms:.2f}ms (deadline={DEADLINE_SENSOR}ms)"
                              + (" — BURST!" if lvl == "CRITICAL" else ""))
        if bust:
            self._alerts.push("WARN", "sensor",
                              f"WCET bust: {lat_ms:.2f}ms > {WCET_SENSOR}ms estimé")
        if jitter and jitter > JITTER_WARN_MS:
            self._alerts.push("WARN", "sensor",
                              f"Jitter élevé: {jitter:.2f}ms > {JITTER_WARN_MS}ms")

    def add_controller(self, lat_ms: float, missed: int,
                       active: str, counts: dict, seq: int = -1) -> None:
        jitter = self.jitter_ctrl.record()
        bust   = self.wcet_ctrl.record(lat_ms)
        self._rm.update_wcet("controller", lat_ms)
        self.sw_ctrl.add(lat_ms)
        self.e2e.add_ctrl(lat_ms)

        with self._lock:
            self.controller_lat.append(lat_ms)
            self.missed["controller"] = missed
            self.total["controller"]  = self.total.get("controller", 0) + 1
            self.total_msgs += 1
            if active:
                self.active_green = active
            if counts:
                self.counts.update(counts)
            self._check_seq("controller", seq)
            self.csv_rows.append({
                "ts":          time.time(),
                "node":        "controller",
                "latency_ms":  lat_ms,
                "deadline_ms": DEADLINE_CTRL,
                "miss":        int(lat_ms > DEADLINE_CTRL),
                "jitter_ms":   round(jitter, 3) if jitter else 0,
                "wcet_bust":   int(bust),
                "seq":         seq,
            })

        is_miss = lat_ms > DEADLINE_CTRL
        lvl = self._alerts.check_miss("controller", is_miss)
        if lvl:
            self._alerts.push(lvl, "controller",
                              f"Deadline miss lat={lat_ms:.2f}ms"
                              + (" — BURST!" if lvl == "CRITICAL" else ""))
        if bust:
            self._alerts.push("WARN", "controller",
                              f"WCET bust: {lat_ms:.2f}ms > {WCET_CTRL}ms estimé")

    def add_actuator(self, lat_ms: float, missed: int,
                     lights: dict, seq: int = -1) -> None:
        jitter = self.jitter_act.record()
        bust   = self.wcet_act.record(lat_ms)
        self._rm.update_wcet("actuator", lat_ms)
        self.sw_act.add(lat_ms)
        self.e2e.add_act(lat_ms)

        with self._lock:
            self.actuator_lat.append(lat_ms)
            self.missed["actuator"] = missed
            self.total["actuator"]  = self.total.get("actuator", 0) + 1
            self.total_msgs += 1
            if lights:
                self.lights.update(lights)
                # Vérification sécurité à chaque update des feux
                self._safety.check(self.lights)
            self._check_seq("actuator", seq)
            self.csv_rows.append({
                "ts":          time.time(),
                "node":        "actuator",
                "latency_ms":  lat_ms,
                "deadline_ms": DEADLINE_ACT,
                "miss":        int(lat_ms > DEADLINE_ACT),
                "jitter_ms":   round(jitter, 3) if jitter else 0,
                "wcet_bust":   int(bust),
                "seq":         seq,
            })

        is_miss = lat_ms > DEADLINE_ACT
        lvl = self._alerts.check_miss("actuator", is_miss)
        if lvl:
            self._alerts.push(lvl, "actuator",
                              f"Deadline miss lat={lat_ms:.2f}ms"
                              + (" — BURST!" if lvl == "CRITICAL" else ""))
        if bust:
            self._alerts.push("WARN", "actuator",
                              f"WCET bust: {lat_ms:.2f}ms > {WCET_ACT}ms estimé")

    def _check_seq(self, node: str, seq: int) -> None:
        """Détecte les sauts de numéros de séquence (perte de messages)."""
        if seq < 0:
            return
        last = self._last_seq.get(node, -1)
        if last >= 0 and seq != last + 1:
            lost = seq - last - 1
            if lost > 0:
                self.msg_lost[node] = self.msg_lost.get(node, 0) + lost
                self._alerts.push("WARN", node,
                                  f"{lost} message(s) perdu(s) "
                                  f"(seq attendu={last+1}, reçu={seq})")
        self._last_seq[node] = seq

    def update_sys_metrics(self) -> None:
        """Met à jour CPU% et RAM% via psutil."""
        if _PSUTIL:
            self.sys_cpu_pct.append(psutil.cpu_percent(interval=None))
            self.sys_ram_pct.append(psutil.virtual_memory().percent)

    # ──────────────────────────────────────────────
    # Snapshot complet pour HTTP / matplotlib
    # ──────────────────────────────────────────────
    def snapshot(self) -> Dict:
        with self._lock:
            sl = list(self.sensor_lat)
            cl = list(self.controller_lat)
            al = list(self.actuator_lat)
            lights  = self.lights.copy()
            counts  = self.counts.copy()
            missed  = self.missed.copy()
            total   = self.total.copy()
            lost    = self.msg_lost.copy()
            cpu_l   = list(self.sys_cpu_pct)
            ram_l   = list(self.sys_ram_pct)
            csv_r   = list(self.csv_rows)

        e2e_h   = self.e2e.history
        jit_s   = list(self.jitter_sensor.jitter_ms)
        jit_c   = list(self.jitter_ctrl.jitter_ms)
        jit_a   = list(self.jitter_act.jitter_ms)

        # Taux de miss
        def miss_rate(node_key):
            t = total.get(node_key, 0)
            m = missed.get(node_key, 0)
            return round(m / t, 4) if t > 0 else 0.0

        return {
            # Séries temporelles brutes
            "sensor_lat":     sl,
            "controller_lat": cl,
            "actuator_lat":   al,
            "e2e_lat":        e2e_h,
            "jitter_sensor":  jit_s,
            "jitter_ctrl":    jit_c,
            "jitter_act":     jit_a,

            # État
            "lights":         lights,
            "active_green":   self.active_green,
            "counts":         counts,

            # Compteurs
            "missed":         missed,
            "total":          total,
            "msg_lost":       lost,
            "total_msgs":     self.total_msgs,

            # Taux de miss
            "miss_rate": {
                "sensor":     miss_rate("sensor"),
                "controller": miss_rate("controller"),
                "actuator":   miss_rate("actuator"),
                "e2e":        self.e2e.stats().get("miss_rate", 0),
            },

            # Statistiques détaillées par nœud
            "stats": {
                "sensor":     self._node_stats(sl, jit_s, DEADLINE_SENSOR,
                                               self.wcet_sensor),
                "controller": self._node_stats(cl, jit_c, DEADLINE_CTRL,
                                               self.wcet_ctrl),
                "actuator":   self._node_stats(al, jit_a, DEADLINE_ACT,
                                               self.wcet_act),
                "e2e":        self.e2e.stats(),
            },

            # Fenêtres glissantes
            "windows": {
                "sensor": {
                    "10s":  self.sw_sensor.stats_window(WINDOW_SHORT, DEADLINE_SENSOR),
                    "30s":  self.sw_sensor.stats_window(WINDOW_MED,   DEADLINE_SENSOR),
                    "60s":  self.sw_sensor.stats_window(WINDOW_LONG,  DEADLINE_SENSOR),
                },
                "controller": {
                    "10s":  self.sw_ctrl.stats_window(WINDOW_SHORT, DEADLINE_CTRL),
                    "30s":  self.sw_ctrl.stats_window(WINDOW_MED,   DEADLINE_CTRL),
                    "60s":  self.sw_ctrl.stats_window(WINDOW_LONG,  DEADLINE_CTRL),
                },
                "actuator": {
                    "10s":  self.sw_act.stats_window(WINDOW_SHORT, DEADLINE_ACT),
                    "30s":  self.sw_act.stats_window(WINDOW_MED,   DEADLINE_ACT),
                    "60s":  self.sw_act.stats_window(WINDOW_LONG,  DEADLINE_ACT),
                },
            },

            # Sécurité
            "safety": {
                "violations":      self._safety.violations,
                "checks":          self._safety.checks,
                "violation_rate":  round(self._safety.rate, 4),
                "last_violation":  self._safety.last_violation,
            },

            # Système
            "system": {
                "cpu_pct":  round(float(np.mean(cpu_l)), 1) if cpu_l else 0,
                "ram_pct":  round(float(np.mean(ram_l)), 1) if ram_l else 0,
                "psutil":   _PSUTIL,
            },

            # Schedulabilité RM
            "rm": self._safety and self._get_rm_report(),

            # Alertes
            "alerts":    self._alerts.snapshot(),

            # CSV
            "csv_rows":  csv_r,
        }

    def _get_rm_report(self) -> Dict:
        # Accès via la référence dans DashboardNode
        return {}  # Sera surchargé par DashboardNode

    @staticmethod
    def _node_stats(lats, jitters, deadline, wcet_tracker) -> Dict:
        if not lats:
            return {"mean": 0, "max": 0, "p95": 0, "min": 0,
                    "ok": True, "wcet_obs": 0, "jitter_mean": 0,
                    "jitter_max": 0}
        arr = sorted(lats)
        p95 = arr[int(0.95 * len(arr))]
        j_arr = sorted(jitters) if jitters else []
        return {
            "mean":       round(float(np.mean(arr)), 2),
            "min":        round(float(min(arr)), 2),
            "max":        round(float(max(arr)), 2),
            "p95":        round(p95, 2),
            "std":        round(float(np.std(arr)), 2),
            "ok":         p95 < deadline,
            "wcet_obs":   round(wcet_tracker.wcet_observed, 2),
            "wcet_busts": wcet_tracker.busts,
            "jitter_mean": round(float(np.mean(j_arr)), 2) if j_arr else 0,
            "jitter_max":  round(float(max(j_arr)), 2) if j_arr else 0,
        }


# ══════════════════════════════════════════════════════════════
#  DASHBOARD PLOTTER — MATPLOTLIB ENRICHI
# ══════════════════════════════════════════════════════════════
class DashboardPlotter:
    """
    Dashboard matplotlib avec 4 lignes de graphes :
      Ligne 0 : Latences temps réel (capteur / contrôleur / actionneur)
      Ligne 1 : E2E pipeline | Jitter capteur | Deadline miss bars | RM util
      Ligne 2 : Feux de signalisation | Stats système
    """

    def __init__(self, store: DataStore, rm: RMSchedulabilityChecker):
        self._store = store
        self._rm    = rm
        self._setup_figure()

    def _setup_figure(self) -> None:
        plt.style.use("dark_background")
        self._fig = plt.figure(
            figsize=(20, 12),
            facecolor=COLORS["bg"],
            num="🚦 Smart Traffic Controller — Dashboard RT v5"
        )
        self._fig.suptitle(
            "🚦  Smart Traffic Controller — Dashboard Temps Réel v5",
            fontsize=14, fontweight="bold",
            color=COLORS["text"], y=0.988,
            fontfamily="monospace",
        )
        self._fig.text(0.99, 0.003,
                       f"http://localhost:{HTTP_PORT}  |  RT v5",
                       ha="right", va="bottom", fontsize=7,
                       color=COLORS["text_dim"], fontstyle="italic")

        # ── Compteur live (coin bas-gauche)
        self._status_txt = self._fig.text(
            0.01, 0.003, "",
            ha="left", va="bottom", fontsize=7,
            color=COLORS["text_dim"], fontfamily="monospace"
        )

        # Layout 3 lignes × 4 colonnes
        gs = gridspec.GridSpec(
            3, 4,
            figure=self._fig,
            hspace=0.52, wspace=0.38,
            left=0.05, right=0.98,
            top=0.95, bottom=0.05,
        )

        # ── Ligne 0 : Latences (pleine largeur) ─────────────
        self._ax_lat = self._fig.add_subplot(gs[0, :])
        self._style_ax(self._ax_lat, "Latences Nœuds Temps Réel (ms)")
        self._ax_lat.set_ylabel("ms", color=COLORS["text_dim"], fontsize=8)

        self._line_s, = self._ax_lat.plot(
            [], [], color=COLORS["sensor"],     linewidth=1.6, alpha=0.9,
            label=f"Capteur (dl={DEADLINE_SENSOR:.0f}ms)")
        self._line_c, = self._ax_lat.plot(
            [], [], color=COLORS["controller"], linewidth=1.6, alpha=0.9,
            label=f"Contrôleur (dl={DEADLINE_CTRL:.0f}ms)")
        self._line_a, = self._ax_lat.plot(
            [], [], color=COLORS["actuator"],   linewidth=1.6, alpha=0.9,
            label=f"Actionneur (dl={DEADLINE_ACT:.0f}ms)")

        for dl, col in [(DEADLINE_SENSOR, COLORS["sensor"]),
                        (DEADLINE_CTRL,   COLORS["controller"]),
                        (DEADLINE_ACT,    COLORS["actuator"])]:
            self._ax_lat.axhline(dl, color=col, linestyle=":", alpha=0.4, linewidth=1)

        leg = self._ax_lat.legend(
            loc="upper right", fontsize=8,
            facecolor=COLORS["panel"], edgecolor=COLORS["border"],
            labelcolor=COLORS["text"]
        )
        leg.get_frame().set_linewidth(0.5)

        # ── Ligne 1 col 0-1 : Latence E2E ───────────────────
        self._ax_e2e = self._fig.add_subplot(gs[1, :2])
        self._style_ax(self._ax_e2e, f"Latence End-to-End Pipeline (deadline {DEADLINE_E2E:.0f} ms)")
        self._ax_e2e.set_ylabel("ms", color=COLORS["text_dim"], fontsize=8)
        self._line_e2e, = self._ax_e2e.plot(
            [], [], color=COLORS["e2e"], linewidth=1.5, alpha=0.9, label="E2E")
        self._ax_e2e.axhline(DEADLINE_E2E, color=COLORS["deadline"],
                             linestyle="--", alpha=0.5, linewidth=1,
                             label=f"Deadline {DEADLINE_E2E:.0f}ms")
        self._ax_e2e.legend(fontsize=7, facecolor=COLORS["panel"],
                            edgecolor=COLORS["border"], labelcolor=COLORS["text"])

        # ── Ligne 1 col 2 : Jitter capteur ──────────────────
        self._ax_jitter = self._fig.add_subplot(gs[1, 2])
        self._style_ax(self._ax_jitter, f"Jitter Inter-Arrivée Capteur")
        self._ax_jitter.set_ylabel("ms", color=COLORS["text_dim"], fontsize=8)
        self._line_jitter, = self._ax_jitter.plot(
            [], [], color=COLORS["jitter"], linewidth=1.2, alpha=0.85)
        self._ax_jitter.axhline(JITTER_WARN_MS, color=COLORS["deadline"],
                                linestyle=":", alpha=0.5, linewidth=1)

        # ── Ligne 1 col 3 : Utilisation RM ──────────────────
        self._ax_rm = self._fig.add_subplot(gs[1, 3])
        self._style_ax(self._ax_rm, "Schedulabilité Rate-Monotonic")
        self._ax_rm.axis("off")

        # ── Ligne 2 col 0-2 : Feux de signalisation ─────────
        self._ax_lights = self._fig.add_subplot(gs[2, :3])
        self._ax_lights.set_facecolor(COLORS["panel"])
        self._ax_lights.set_title(
            "État Feux — Invariant Sécurité : ∀t |{d: GREEN}| ≤ 1",
            color=COLORS["text"], fontsize=9
        )
        self._ax_lights.set_xlim(-0.5, 4.5)
        self._ax_lights.set_ylim(-1.1, 3.2)
        self._ax_lights.axis("off")

        # ── Ligne 2 col 3 : Statistiques étendues ───────────
        self._ax_stats = self._fig.add_subplot(gs[2, 3])
        self._ax_stats.set_facecolor(COLORS["panel"])
        self._ax_stats.set_title("Métriques RT", color=COLORS["text"], fontsize=9)
        self._ax_stats.axis("off")

    # ── Utilitaire style axe
    def _style_ax(self, ax, title: str) -> None:
        ax.set_facecolor(COLORS["panel"])
        ax.set_title(title, color=COLORS["text"], fontsize=9, pad=6)
        ax.tick_params(colors=COLORS["text_dim"], labelsize=7)
        for sp in ax.spines.values():
            sp.set_color(COLORS["border"])
            sp.set_linewidth(0.5)
        ax.grid(True, color=COLORS["grid"], alpha=0.45, linestyle="--", linewidth=0.4)

    # ── Point d'entrée animation
    def start_animation(self) -> None:
        self._ani = FuncAnimation(
            self._fig,
            self._update_frame,
            interval=UPDATE_INTERVAL,
            blit=False,
            cache_frame_data=False,
        )
        plt.show()

    def _update_frame(self, frame: int) -> None:
        snap = self._store.snapshot()
        self._update_latencies(snap)
        self._update_e2e(snap)
        self._update_jitter(snap)
        self._update_rm()
        self._update_lights(snap)
        self._update_stats(snap)
        # Statut global
        rm = self._rm.report()
        safety = snap.get("safety", {})
        alert_c = snap.get("alerts", {}).get("counts", {})
        crit = alert_c.get("CRITICAL", 0)
        warns = alert_c.get("WARN", 0)
        status = (f"msgs={snap['total_msgs']}  |  "
                  f"miss=S:{snap['missed'].get('sensor',0)} "
                  f"C:{snap['missed'].get('controller',0)} "
                  f"A:{snap['missed'].get('actuator',0)}  |  "
                  f"violations={safety.get('violations',0)}  |  "
                  f"RM={'OK' if rm['schedulable'] else 'VIOLATION'}  |  "
                  f"alerts CRIT={crit} WARN={warns}  |  "
                  f"{datetime.now():%H:%M:%S}")
        self._status_txt.set_text(status)
        color = COLORS["CRITICAL"] if crit > 0 else (COLORS["YELLOW"] if warns > 0 else COLORS["GREEN"])
        self._status_txt.set_color(color)

    # ── Graphe latences
    def _update_latencies(self, snap: dict) -> None:
        sl = snap["sensor_lat"]
        cl = snap["controller_lat"]
        al = snap["actuator_lat"]
        n = max(len(sl), len(cl), len(al), 1)
        xs = np.arange(n)

        def pad(d, n):
            return [np.nan] * (n - len(d)) + list(d)

        self._line_s.set_data(xs, pad(sl, n))
        self._line_c.set_data(xs, pad(cl, n))
        self._line_a.set_data(xs, pad(al, n))

        all_v = [v for lst in [sl, cl, al] for v in lst]
        if all_v:
            self._ax_lat.set_ylim(0, max(max(all_v) * 1.15, DEADLINE_SENSOR * 1.1))
            self._ax_lat.set_xlim(0, n)

    # ── Graphe E2E
    def _update_e2e(self, snap: dict) -> None:
        e2e = snap.get("e2e_lat", [])
        if e2e:
            xs = np.arange(len(e2e))
            self._line_e2e.set_data(xs, e2e)
            self._ax_e2e.set_xlim(0, len(e2e))
            self._ax_e2e.set_ylim(0, max(max(e2e) * 1.15, DEADLINE_E2E * 1.1))

    # ── Graphe jitter
    def _update_jitter(self, snap: dict) -> None:
        jit = snap.get("jitter_sensor", [])
        if jit:
            xs = np.arange(len(jit))
            self._line_jitter.set_data(xs, jit)
            self._ax_jitter.set_xlim(0, len(jit))
            self._ax_jitter.set_ylim(0, max(max(jit) * 1.2, JITTER_WARN_MS * 1.5))

    # ── Rapport RM (texte)
    def _update_rm(self) -> None:
        if not hasattr(self, '_rm_texts'):
            self._rm_texts = []
            y = 0.95
            for _ in range(14):
                t = self._ax_rm.text(
                    0.05, y, "",
                    transform=self._ax_rm.transAxes,
                    fontsize=8, fontfamily="monospace", va="top"
                )
                self._rm_texts.append(t)
                y -= 0.075

        rpt = self._rm.report()
        u   = rpt["utilization"]
        u_s = rpt["tasks"]["sensor"]["wcet"] / rpt["tasks"]["sensor"]["period"]
        u_c = rpt["tasks"]["controller"]["wcet"] / rpt["tasks"]["controller"]["period"]
        u_a = rpt["tasks"]["actuator"]["wcet"] / rpt["tasks"]["actuator"]["period"]
        ok_col = COLORS["GREEN"] if rpt["schedulable"] else COLORS["CRITICAL"]

        lines = [
            ("┌─ RM ANALYSIS ────", COLORS["text_dim"]),
            (f"  U_sensor : {u_s:.4f}", COLORS["sensor"]),
            (f"  U_ctrl   : {u_c:.4f}", COLORS["controller"]),
            (f"  U_act    : {u_a:.4f}", COLORS["actuator"]),
            ("  ──────────────────", COLORS["grid"]),
            (f"  Σ U      : {u:.4f}", ok_col),
            (f"  Borne RM : {RM_BOUND:.4f}", COLORS["text_dim"]),
            (f"  Marge    : {rpt['margin_pct']:+.1f}%", ok_col),
            ("  ──────────────────", COLORS["grid"]),
            (f"  {'✓ SCHEDULABLE' if rpt['schedulable'] else '✕ NON-SCHED'}", ok_col),
            ("└──────────────────", COLORS["text_dim"]),
            (f"  n={N_TASKS} tâches", COLORS["text_dim"]),
            (f"  Test Liu & Layland", COLORS["text_dim"]),
            ("", COLORS["text_dim"]),
        ]
        for t_obj, (txt, col) in zip(self._rm_texts, lines):
            t_obj.set_text(txt)
            t_obj.set_color(col)

    # ── Feux de signalisation
    def _update_lights(self, snap: dict) -> None:
        if not hasattr(self, '_light_elems'):
            self._light_elems = {}
            for i, d in enumerate(DIRECTIONS):
                box = FancyBboxPatch(
                    (i - 0.40, 0.10), 0.80, 2.40,
                    boxstyle="round,pad=0.06",
                    facecolor=COLORS["bg"], edgecolor=COLORS["RED"],
                    linewidth=0.8, zorder=2
                )
                self._ax_lights.add_patch(box)

                circles = {}
                for st, yp in [("RED", 2.20), ("YELLOW", 1.40), ("GREEN", 0.60)]:
                    c = Circle((i, yp), 0.26, facecolor=COLORS[st], alpha=0.12, zorder=3)
                    self._ax_lights.add_patch(c)
                    circles[st] = c

                label = self._ax_lights.text(
                    i, -0.20, DIR_LABELS[d],
                    ha="center", va="top", color=COLORS["text_dim"],
                    fontsize=9, fontweight="normal"
                )
                badge = self._ax_lights.text(
                    i, 2.78, "", ha="center", va="top",
                    fontsize=8, fontweight="bold"
                )
                cnt_txt = self._ax_lights.text(
                    i, -0.62, "", ha="center", va="top",
                    color=COLORS["text_dim"], fontsize=8, fontfamily="monospace"
                )
                miss_txt = self._ax_lights.text(
                    i, -0.90, "", ha="center", va="top",
                    color=COLORS["text_dim"], fontsize=7, fontfamily="monospace"
                )
                self._light_elems[d] = {
                    "box": box, "circles": circles,
                    "label": label, "badge": badge,
                    "count": cnt_txt, "miss": miss_txt,
                }

        lights = snap["lights"]
        counts = snap["counts"]
        missed = snap["missed"]
        total  = snap.get("total", {})

        for d in DIRECTIONS:
            state = lights.get(d, "RED")
            col   = COLORS.get(state, COLORS["RED"])
            elem  = self._light_elems[d]

            elem["box"].set_edgecolor(col)
            elem["box"].set_linewidth(2.5 if state in ["GREEN", "YELLOW"] else 0.8)
            elem["box"].set_facecolor(
                "#001a06" if state == "GREEN" else
                "#1a1000" if state == "YELLOW" else COLORS["bg"]
            )

            for st, circle in elem["circles"].items():
                circle.set_alpha(0.92 if state == st else 0.10)

            elem["label"].set_color(col if state != "RED" else COLORS["text_dim"])
            elem["label"].set_fontweight("bold" if state != "RED" else "normal")

            state_map = {"GREEN": "▶ VERT", "YELLOW": "⚡ JAUNE", "RED": ""}
            elem["badge"].set_text(state_map.get(state, ""))
            elem["badge"].set_color(col)

            elem["count"].set_text(f"{counts.get(d, 0)} véh.")
            elem["count"].set_color(col if state == "GREEN" else COLORS["text_dim"])

            # Miss rate par direction (affichage approximatif via nœud capteur)
            t = total.get("sensor", 0)
            m = missed.get("sensor", 0)
            rate = m / t * 100 if t > 0 else 0
            elem["miss"].set_text(f"miss {rate:.1f}%" if t > 0 else "")

    # ── Stats étendues
    def _update_stats(self, snap: dict) -> None:
        if not hasattr(self, '_stat_txts'):
            self._stat_txts = []
            y = 0.97
            for _ in range(30):
                t = self._ax_stats.text(
                    0.02, y, "",
                    transform=self._ax_stats.transAxes,
                    fontsize=7, fontfamily="monospace", va="top"
                )
                self._stat_txts.append(t)
                y -= 0.036

        st   = snap.get("stats", {})
        s_s  = st.get("sensor", {})
        c_s  = st.get("controller", {})
        a_s  = st.get("actuator", {})
        e_s  = st.get("e2e", {})
        mr   = snap.get("miss_rate", {})
        sys_ = snap.get("system", {})
        saf  = snap.get("safety", {})
        win  = snap.get("windows", {})

        lights = snap["lights"]
        yellow_d = next((d for d in DIRECTIONS if lights.get(d) == "YELLOW"), None)
        active_d = yellow_d or snap.get("active_green")
        active_st = "JAUNE" if yellow_d else "VERT"
        active_col = COLORS["YELLOW"] if yellow_d else COLORS["GREEN"]

        w10 = win.get("sensor", {}).get("10s", {})
        total_miss = sum(snap["missed"].values())
        sys_ok = total_miss == 0

        lines = [
            ("┌─ CAPTEUR ─────────────────", COLORS["sensor"]),
            (f"  Moy:{s_s.get('mean',0):6.2f}  Max:{s_s.get('max',0):6.2f} ms", COLORS["text"]),
            (f"  P95:{s_s.get('p95',0):6.2f}  Std:{s_s.get('std',0):5.2f} ms", COLORS["text"]),
            (f"  WCET obs:{s_s.get('wcet_obs',0):5.2f} ms", COLORS["wcet"]),
            (f"  Jitter m:{s_s.get('jitter_mean',0):5.2f} mx:{s_s.get('jitter_max',0):5.2f}", COLORS["jitter"]),
            (f"  Miss {snap['missed'].get('sensor',0)} ({mr.get('sensor',0)*100:.1f}%)", COLORS["deadline"] if snap['missed'].get('sensor',0) > 0 else COLORS["GREEN"]),
            ("├─ CONTRÔLEUR ──────────────", COLORS["controller"]),
            (f"  Moy:{c_s.get('mean',0):6.2f}  Max:{c_s.get('max',0):6.2f} ms", COLORS["text"]),
            (f"  P95:{c_s.get('p95',0):6.2f}  Std:{c_s.get('std',0):5.2f} ms", COLORS["text"]),
            (f"  WCET obs:{c_s.get('wcet_obs',0):5.2f} ms", COLORS["wcet"]),
            (f"  Miss {snap['missed'].get('controller',0)} ({mr.get('controller',0)*100:.1f}%)", COLORS["deadline"] if snap['missed'].get('controller',0) > 0 else COLORS["GREEN"]),
            ("├─ ACTIONNEUR ──────────────", COLORS["actuator"]),
            (f"  Moy:{a_s.get('mean',0):6.2f}  Max:{a_s.get('max',0):6.2f} ms", COLORS["text"]),
            (f"  P95:{a_s.get('p95',0):6.2f}  Std:{a_s.get('std',0):5.2f} ms", COLORS["text"]),
            (f"  WCET obs:{a_s.get('wcet_obs',0):5.2f} ms", COLORS["wcet"]),
            (f"  Miss {snap['missed'].get('actuator',0)} ({mr.get('actuator',0)*100:.1f}%)", COLORS["deadline"] if snap['missed'].get('actuator',0) > 0 else COLORS["GREEN"]),
            ("├─ E2E PIPELINE ────────────", COLORS["e2e"]),
            (f"  Moy:{e_s.get('mean',0):6.2f}  P95:{e_s.get('p95',0):6.2f} ms", COLORS["text"]),
            (f"  Miss-rate E2E: {mr.get('e2e',0)*100:.1f}%", COLORS["deadline"] if mr.get('e2e',0) > 0 else COLORS["GREEN"]),
            ("├─ FENÊTRE 10 s ────────────", COLORS["text_dim"]),
            (f"  Capteur  P95: {w10.get('p95',0):.2f} ms", COLORS["sensor"]),
            (f"  Miss 10s: {w10.get('miss_rate',0)*100:.1f}%", COLORS["deadline"] if w10.get('miss_rate',0) > MISS_RATE_WARN else COLORS["GREEN"]),
            ("├─ SÉCURITÉ ────────────────", COLORS["CRITICAL"] if saf.get('violations',0) > 0 else COLORS["GREEN"]),
            (f"  Violations: {saf.get('violations',0)}", COLORS["CRITICAL"] if saf.get('violations',0) > 0 else COLORS["GREEN"]),
            ("├─ SYSTÈME ─────────────────", COLORS["text_dim"]),
            (f"  CPU: {sys_.get('cpu_pct',0):.1f}%   RAM: {sys_.get('ram_pct',0):.1f}%", COLORS["text_dim"]),
            (f"  Actif: {active_d or '—'} ({active_st})", active_col),
            (f"  Total msgs: {snap.get('total_msgs',0)}", COLORS["text_dim"]),
            ("└────────────────────────────", COLORS["grid"]),
            (f"  {datetime.now().strftime('%H:%M:%S.%f')[:-3]}", COLORS["text_dim"]),
        ]

        for t_obj, (text, col) in zip(self._stat_txts, lines):
            t_obj.set_text(text)
            t_obj.set_color(col)


# ══════════════════════════════════════════════════════════════
#  DASHBOARD NODE
# ══════════════════════════════════════════════════════════════
class DashboardNode(Node):
    """
    Nœud ROS2 tableau de bord — version RT v5.

    Abonnements :
        /sensor_stats      /controller_stats  /actuator_stats
        /actuator_feedback /traffic_data      /light_commands

    Publications :
        /dashboard_health  (std_msgs/String — JSON health report)
    """

    def __init__(self):
        super().__init__("dashboard_node")

        # ── Moniteurs RT ──────────────────────────────────────
        self._safety = SafetyMonitor(self.get_logger())
        self._alerts = AlertManager()
        self._rm     = RMSchedulabilityChecker()
        self._store  = DataStore(self._safety, self._alerts, self._rm)

        # Patch snapshot pour inclure RM
        self._store._get_rm_report = self._rm.report

        # ── Abonnements ───────────────────────────────────────
        self.create_subscription(String, "/sensor_stats",      self._on_sensor,       RT_QOS)
        self.create_subscription(String, "/controller_stats",  self._on_controller,   RT_QOS)
        self.create_subscription(String, "/actuator_stats",    self._on_actuator,     RT_QOS)
        self.create_subscription(String, "/actuator_feedback", self._on_feedback,     RT_QOS)
        self.create_subscription(String, "/traffic_data",      self._on_traffic_data, RT_QOS)
        self.create_subscription(String, "/light_commands",    self._on_light_cmd,    RT_QOS)

        # ── Publication health ─────────────────────────────────
        self._pub_health = self.create_publisher(String, "/dashboard_health", RT_QOS)

        # ── Timers ────────────────────────────────────────────
        os.makedirs(CSV_EXPORT_DIR, exist_ok=True)
        self._csv_path = os.path.join(
            CSV_EXPORT_DIR,
            f"rt_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        self.create_timer(30.0,          self._export_csv)
        self.create_timer(HEALTH_PERIOD_S, self._publish_health)
        self.create_timer(1.0,           self._update_sys_metrics)

        # ── Serveur HTTP ──────────────────────────────────────
        DashboardHTTPHandler.store_ref = self._store
        DashboardHTTPHandler.rm_ref    = self._rm
        DashboardHTTPHandler.alert_ref = self._alerts
        self._start_http_server()

        # ── Alerte démarrage ──────────────────────────────────
        self._alerts.push("INFO", "system",
                          f"DashboardNode v5 démarré — HTTP:{HTTP_PORT} | "
                          f"RM_bound={RM_BOUND:.4f}")

        self.get_logger().info(
            f"\n[DashboardNode] ✅ Démarré\n"
            f"  CSV      → {self._csv_path}\n"
            f"  HTTP     → http://localhost:{HTTP_PORT}\n"
            f"  RM bound → {RM_BOUND:.4f} ({N_TASKS} tâches)\n"
            f"  Health   → /dashboard_health (toutes {HEALTH_PERIOD_S}s)\n"
            f"  Sécurité → SafetyMonitor actif\n"
            f"  psutil   → {'disponible' if _PSUTIL else 'non installé'}"
        )

    # ── Callbacks abonnements ─────────────────────────────────
    def _on_traffic_data(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            counts = d.get("counts")
            if counts:
                with self._store._lock:
                    self._store.counts.update(counts)
        except Exception as e:
            self.get_logger().warn(f"[Dashboard] traffic_data: {e}")

    def _on_light_cmd(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            state  = d.get("state", {})
            lights = state.get("lights", {})
            counts = d.get("counts", {})
            if lights:
                with self._store._lock:
                    self._store.lights.update(lights)
                    if state.get("active_green"):
                        self._store.active_green = state["active_green"]
                # Vérification sécurité immédiate
                self._safety.check(lights)
            if counts:
                with self._store._lock:
                    self._store.counts.update(counts)
        except Exception as e:
            self.get_logger().warn(f"[Dashboard] light_cmd: {e}")

    def _on_sensor(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            self._store.add_sensor(
                d.get("latency_ms", 0),
                d.get("missed_deadlines", 0),
                d.get("seq", -1),
            )
        except Exception as e:
            self.get_logger().warn(f"[Dashboard] sensor: {e}")

    def _on_controller(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            self._store.add_controller(
                d.get("latency_ms", 0),
                d.get("missed_deadlines", 0),
                d.get("active_green"),
                None,
                d.get("seq", -1),
            )
        except Exception as e:
            self.get_logger().warn(f"[Dashboard] controller: {e}")

    def _on_actuator(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            self._store.add_actuator(
                d.get("latency_ms", 0),
                d.get("missed_deadlines", 0),
                None,
                d.get("seq", -1),
            )
        except Exception as e:
            self.get_logger().warn(f"[Dashboard] actuator: {e}")

    def _on_feedback(self, msg: String) -> None:
        try:
            d = json.loads(msg.data)
            lights = d.get("lights", {})
            if lights:
                self._store.add_actuator(
                    d.get("processing_ms", 0),
                    0,
                    lights,
                )
        except Exception as e:
            self.get_logger().warn(f"[Dashboard] feedback: {e}")

    # ── Timers callbacks ──────────────────────────────────────
    def _publish_health(self) -> None:
        """Publie un rapport de santé du système RT sur /dashboard_health."""
        snap = self._store.snapshot()
        rm   = self._rm.report()
        e2e  = snap.get("stats", {}).get("e2e", {})
        mr   = snap.get("miss_rate", {})
        saf  = snap.get("safety", {})

        total_miss = sum(snap["missed"].values())
        all_ok = (
            total_miss == 0
            and rm["schedulable"]
            and saf.get("violations", 0) == 0
        )

        health = {
            "timestamp":     time.time(),
            "status":        "OK" if all_ok else "DEGRADED",
            "total_msgs":    snap["total_msgs"],
            "missed_total":  total_miss,
            "miss_rates":    mr,
            "e2e_p95_ms":    e2e.get("p95", 0),
            "rm_util":       rm["utilization"],
            "rm_schedulable": rm["schedulable"],
            "safety_violations": saf.get("violations", 0),
            "msg_lost":      snap.get("msg_lost", {}),
            "alerts_crit":   snap.get("alerts", {}).get("counts", {}).get("CRITICAL", 0),
        }

        out      = String()
        out.data = json.dumps(health)
        self._pub_health.publish(out)

        level = self.get_logger().info if all_ok else self.get_logger().warn
        level(
            f"[HealthCheck] status={health['status']} | "
            f"msgs={health['total_msgs']} | miss={total_miss} | "
            f"e2e_p95={health['e2e_p95_ms']:.2f}ms | "
            f"RM={'OK' if rm['schedulable'] else 'NON-SCHED'} U={rm['utilization']:.4f} | "
            f"violations={health['safety_violations']}"
        )

    def _update_sys_metrics(self) -> None:
        """Met à jour CPU/RAM toutes les secondes."""
        self._store.update_sys_metrics()

    def _export_csv(self) -> None:
        """Export CSV enrichi (latence, jitter, wcet, miss_rate, seq)."""
        snap = self._store.snapshot()
        rows = snap.get("csv_rows", [])
        if not rows:
            return
        try:
            df = pd.DataFrame(rows)
            df.to_csv(self._csv_path, index=False)
            self.get_logger().info(
                f"[DashboardNode] CSV exporté : {self._csv_path} ({len(df)} lignes)"
            )
        except Exception as e:
            self.get_logger().error(f"[DashboardNode] Erreur CSV : {e}")

    def _start_http_server(self) -> None:
        try:
            server = socketserver.ThreadingTCPServer(("", HTTP_PORT), DashboardHTTPHandler)
            server.allow_reuse_address = True
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            self.get_logger().info(
                f"[DashboardNode] HTTP → http://localhost:{HTTP_PORT}"
            )
        except OSError as e:
            self.get_logger().warn(
                f"[DashboardNode] HTTP server error (port {HTTP_PORT}): {e}"
            )

    def get_store(self) -> DataStore:
        return self._store

    def get_rm(self) -> RMSchedulabilityChecker:
        return self._rm


# ══════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════
def run_dashboard_ros(args=None):
    rclpy.init(args=args)
    node = DashboardNode()

    # Thread ROS2 spin (daemon)
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    # Matplotlib dans le thread principal (requis)
    plotter = DashboardPlotter(node.get_store(), node.get_rm())
    try:
        plotter.start_animation()
    except KeyboardInterrupt:
        node.get_logger().info("[DashboardNode] Arrêt demandé.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main(args=None):
    run_dashboard_ros(args)


if __name__ == "__main__":
    main()
