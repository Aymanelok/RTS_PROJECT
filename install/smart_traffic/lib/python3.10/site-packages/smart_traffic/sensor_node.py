#!/usr/bin/env python3
"""
sensor_node.py — Smart Traffic Controller
=========================================
Nœud capteur : génère les données de trafic pour les 4 directions
(Nord, Sud, Est, Ouest) à une fréquence de 10 Hz (période = 100 ms).

Contraintes temps réel :
  - Période     : 100 ms
  - Deadline    : 100 ms (implicite)
  - WCET estimé : < 10 ms (génération + publication)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String

import json
import time
import random
import math
import logging

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
DIRECTIONS         = ["N", "S", "E", "O"]
PUBLISH_PERIOD_MS  = 100          # 10 Hz → 100 ms
DEADLINE_MS        = 100          # deadline stricte
MAX_VEHICLES       = 30           # max véhicules par direction
PEAK_HOUR_BIAS     = 2.5          # facteur multiplicatif heure de pointe

# QoS temps réel : fiabilité + historique minimal
RT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)


class TrafficPattern:
    """Modèle de trafic synthétique avec variation temporelle."""

    def __init__(self):
        self._t0 = time.monotonic()
        # Bruit indépendant par direction
        self._noise_seed = {d: random.random() * 100 for d in DIRECTIONS}

    def sample(self) -> dict:
        """Retourne un échantillon de trafic [N, S, E, O]."""
        elapsed = time.monotonic() - self._t0
        counts  = {}
        for d in DIRECTIONS:
            # Signal de base : sinusoïde lente (cycle de 30 s)
            base  = 10 + 8 * math.sin(2 * math.pi * elapsed / 30 + self._noise_seed[d])
            # Bruit gaussien léger
            noise = random.gauss(0, 1.5)
            # Saturation
            counts[d] = max(0, min(MAX_VEHICLES, round(base + noise)))
        return counts


class SensorNode(Node):
    """
    Nœud ROS2 capteur trafic.

    Publications :
        /traffic_data  (std_msgs/String — JSON)
        /sensor_stats  (std_msgs/String — JSON métriques)
    """

    def __init__(self):
        super().__init__("sensor_node")

        # ── Éditeurs ──────────────────────────────────────────
        self._pub_traffic = self.create_publisher(
            String, "/traffic_data", RT_QOS
        )
        self._pub_stats = self.create_publisher(
            String, "/sensor_stats", RT_QOS
        )

        # ── Timer principal 10 Hz ─────────────────────────────
        self._timer = self.create_timer(
            PUBLISH_PERIOD_MS / 1000.0, self._timer_callback
        )

        # ── État interne ──────────────────────────────────────
        self._pattern     = TrafficPattern()
        self._seq         = 0          # numéro de séquence
        self._latencies   = []         # historique latences (ms)
        self._missed      = 0          # deadlines manquées
        self._last_cb_ns  = None       # timestamp du dernier callback

        self.get_logger().info(
            f"[SensorNode] Démarré — période={PUBLISH_PERIOD_MS} ms | "
            f"deadline={DEADLINE_MS} ms"
        )

    # ─────────────────────────────────────────────────────────
    # Callback timer principal
    # ─────────────────────────────────────────────────────────
    def _timer_callback(self) -> None:
        t_start = time.monotonic_ns()

        # 1. Vérification inter-arrivée (jitter détection)
        if self._last_cb_ns is not None:
            jitter_ms = (t_start - self._last_cb_ns) / 1e6 - PUBLISH_PERIOD_MS
            if abs(jitter_ms) > 15:  # tolérance 15 ms
                self.get_logger().warn(
                    f"[SensorNode] Jitter élevé : {jitter_ms:+.1f} ms (seq={self._seq})"
                )
        self._last_cb_ns = t_start

        # 2. Acquisition données trafic
        counts = self._pattern.sample()
        self._seq += 1

        # 3. Construction message
        payload = {
            "seq":        self._seq,
            "timestamp":  time.time(),           # epoch s
            "counts":     counts,                # {"N":x, "S":x, ...}
            "total":      sum(counts.values()),
        }
        msg       = String()
        msg.data  = json.dumps(payload)
        self._pub_traffic.publish(msg)

        # 4. Calcul latence de publication
        t_end      = time.monotonic_ns()
        latency_ms = (t_end - t_start) / 1e6
        self._latencies.append(latency_ms)

        # 5. Vérification deadline
        if latency_ms > DEADLINE_MS:
            self._missed += 1
            self.get_logger().error(
                f"[SensorNode] ⚠ DEADLINE MISS #{self._missed} — "
                f"latence={latency_ms:.2f} ms > {DEADLINE_MS} ms (seq={self._seq})"
            )
        else:
            self.get_logger().debug(
                f"[SensorNode] seq={self._seq:05d} | "
                f"trafic={[counts[d] for d in DIRECTIONS]} | "
                f"lat={latency_ms:.2f} ms"
            )

        # 6. Publication des statistiques (toutes les 10 publications)
        if self._seq % 10 == 0:
            self._publish_stats(latency_ms)

    def _publish_stats(self, last_latency_ms: float) -> None:
        lats = self._latencies[-100:] if len(self._latencies) > 100 else self._latencies
        stats = {
            "seq":            self._seq,
            "node":           "sensor",
            "timestamp":      time.time(),
            "latency_ms":     last_latency_ms,
            "lat_mean_ms":    sum(lats) / len(lats) if lats else 0,
            "lat_max_ms":     max(lats) if lats else 0,
            "missed_deadlines": self._missed,
            "total_published":  self._seq,
        }
        msg      = String()
        msg.data = json.dumps(stats)
        self._pub_stats.publish(msg)

        self.get_logger().info(
            f"[SensorNode] Stats — "
            f"lat_moy={stats['lat_mean_ms']:.2f} ms | "
            f"lat_max={stats['lat_max_ms']:.2f} ms | "
            f"deadlines_missed={self._missed}"
        )


# ──────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("[SensorNode] Arrêt demandé par l'utilisateur.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
