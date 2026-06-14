#!/usr/bin/env python3
"""
actuator_node.py — Smart Traffic Controller
============================================
Nœud actionneur : reçoit les commandes de feux et applique les changements
d'état physiques (simulation). Vérifie l'invariant de sécurité critique.

Contraintes temps réel :
  - Traitement commande + application : ≤ 50 ms (WCET)
  - Vérification sécurité : systématique à chaque commande

PROPRIÉTÉ DE SÉCURITÉ CRITIQUE :
  ∀ t : |{ d ∈ DIRECTIONS | lights[d] = GREEN }| ≤ 1
  (Au plus une direction verte à tout instant)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String

import json
import time
from collections import deque
from typing import Optional

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
DIRECTIONS         = ["N", "S", "E", "O"]
ACTUATOR_DEADLINE  = 50.0          # ms — deadline stricte
LATENCY_WINDOW     = 200

RT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

# Emojis pour l'affichage des feux
LIGHT_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}


class SafetyMonitor:
    """
    Moniteur de sécurité formel.

    Vérifie en continu la propriété :
      "jamais deux feux verts simultanément"

    Implémentation : model checking en ligne (runtime verification).
    """

    def __init__(self, logger):
        self._logger         = logger
        self._violation_count = 0

    def check(self, lights: dict[str, str]) -> bool:
        """
        Vérifie l'invariant de sécurité.

        Returns:
            True  → état sûr
            False → VIOLATION DÉTECTÉE
        """
        green_dirs = [d for d, s in lights.items() if s == "GREEN"]
        n_green    = len(green_dirs)

        if n_green > 1:
            self._violation_count += 1
            self._logger.fatal(
                f"[SafetyMonitor] 🚨 VIOLATION CRITIQUE #{self._violation_count} — "
                f"{n_green} feux VERTS simultanés : {green_dirs} "
                f"— ARRÊT D'URGENCE REQUIS"
            )
            return False

        if n_green == 0:
            self._logger.debug("[SafetyMonitor] Phase tous-rouges (transition) ✓")
        else:
            self._logger.debug(
                f"[SafetyMonitor] Invariant OK — seul {green_dirs[0]} est VERT ✓"
            )
        return True

    @property
    def violations(self) -> int:
        return self._violation_count


class PhysicalActuator:
    """
    Simule les actionneurs physiques des feux de signalisation.

    Dans un système réel, cette classe enverrait des signaux GPIO
    ou des commandes CAN/MODBUS aux contrôleurs de feux.
    """

    def __init__(self, logger):
        self._logger  = logger
        self._current = {d: "RED" for d in DIRECTIONS}
        self._changes  = 0

    def apply(self, new_lights: dict[str, str]) -> list[tuple[str, str, str]]:
        """
        Applique les nouveaux états de feux.

        Returns:
            Liste des changements effectués : [(direction, ancien, nouveau), ...]
        """
        changes = []
        for d in DIRECTIONS:
            old = self._current.get(d, "RED")
            new = new_lights.get(d, "RED")
            if old != new:
                self._current[d] = new
                changes.append((d, old, new))
                self._changes += 1
                # Simulation délai hardware (µs → négligeable)
                self._logger.info(
                    f"[Actuator] 🚦 {d}: {LIGHT_EMOJI[old]} → {LIGHT_EMOJI[new]}"
                )
        return changes

    def current_state(self) -> dict[str, str]:
        return self._current.copy()

    @property
    def total_changes(self) -> int:
        return self._changes


class ActuatorNode(Node):
    """
    Nœud ROS2 actionneur des feux de signalisation.

    Abonnements :
        /light_commands   (std_msgs/String — JSON)
    Publications :
        /actuator_feedback (std_msgs/String — JSON)
        /actuator_stats    (std_msgs/String — JSON)
    """

    def __init__(self):
        super().__init__("actuator_node")

        # ── Abonnements ───────────────────────────────────────
        self._sub = self.create_subscription(
            String, "/light_commands", self._on_command, RT_QOS
        )

        # ── Publications ──────────────────────────────────────
        self._pub_feedback = self.create_publisher(
            String, "/actuator_feedback", RT_QOS
        )
        self._pub_stats = self.create_publisher(
            String, "/actuator_stats", RT_QOS
        )

        # ── Composants ────────────────────────────────────────
        self._safety    = SafetyMonitor(self.get_logger())
        self._actuator  = PhysicalActuator(self.get_logger())

        # ── Métriques ─────────────────────────────────────────
        self._latencies    = deque(maxlen=LATENCY_WINDOW)
        self._missed        = 0
        self._total_cmds    = 0
        self._last_active:  Optional[str] = None

        self.get_logger().info(
            f"[ActuatorNode] Démarré — deadline={ACTUATOR_DEADLINE} ms"
        )
        self._log_current_state()

    # ─────────────────────────────────────────────────────────
    # Callback : commande reçue du contrôleur
    # ─────────────────────────────────────────────────────────
    def _on_command(self, msg: String) -> None:
        t_start = time.monotonic_ns()

        try:
            cmd = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self.get_logger().error(f"[ActuatorNode] JSON invalide : {e}")
            return

        seq    = cmd.get("seq", -1)
        state  = cmd.get("state", {})
        lights = state.get("lights", {})
        self._total_cmds += 1

        # ── 1. Vérification sécurité AVANT application ────────
        safe = self._safety.check(lights)
        if not safe:
            # Commande rejetée — état d'urgence
            self.get_logger().fatal(
                f"[ActuatorNode] 🚫 Commande rejetée (seq={seq}) — violation sécurité !"
            )
            self._publish_feedback(seq, lights, [], "SAFETY_VIOLATION", t_start)
            return

        # ── 2. Application physique des feux ──────────────────
        changes = self._actuator.apply(lights)

        # ── 3. Log changements ────────────────────────────────
        active = state.get("active_green")
        if active != self._last_active:
            self.get_logger().info(
                f"[ActuatorNode] ➡ Changement de phase : "
                f"{self._last_active or 'INIT'} → {active or 'TOUS_ROUGES'}"
            )
            self._last_active = active

        # ── 4. Feedback ───────────────────────────────────────
        t_end       = time.monotonic_ns()
        latency_ms  = (t_end - t_start) / 1e6
        self._latencies.append(latency_ms)

        status = "OK" if latency_ms <= ACTUATOR_DEADLINE else "DEADLINE_MISS"
        self._publish_feedback(seq, lights, changes, status, t_start)

        # ── 5. Vérification deadline ──────────────────────────
        if latency_ms > ACTUATOR_DEADLINE:
            self._missed += 1
            self.get_logger().error(
                f"[ActuatorNode] ⚠ DEADLINE MISS #{self._missed} — "
                f"lat={latency_ms:.2f} ms > {ACTUATOR_DEADLINE} ms (seq={seq})"
            )
        else:
            self.get_logger().debug(
                f"[ActuatorNode] seq={seq:05d} | "
                f"vert={active} | {len(changes)} changement(s) | "
                f"lat={latency_ms:.2f} ms"
            )

        # Stats toutes les 20 commandes
        if self._total_cmds % 20 == 0:
            self._publish_stats(latency_ms)

    def _publish_feedback(
        self,
        seq:      int,
        lights:   dict,
        changes:  list,
        status:   str,
        t_start:  int,
    ) -> None:
        t_now = time.monotonic_ns()
        fb = {
            "seq":                seq,
            "timestamp":          time.time(),
            "status":             status,
            "lights":             lights,
            "changes":            [{"dir": c[0], "from": c[1], "to": c[2]} for c in changes],
            "safety_violations":  self._safety.violations,
            "processing_ms":      round((t_now - t_start) / 1e6, 3),
        }
        msg      = String()
        msg.data = json.dumps(fb)
        self._pub_feedback.publish(msg)

    def _publish_stats(self, last_lat: float) -> None:
        lats = list(self._latencies)
        if not lats:
            return
        lats_sorted = sorted(lats)
        p95 = lats_sorted[int(0.95 * len(lats_sorted))]

        stats = {
            "node":              "actuator",
            "timestamp":         time.time(),
            "latency_ms":        last_lat,
            "lat_mean_ms":       sum(lats) / len(lats),
            "lat_max_ms":        max(lats),
            "lat_p95_ms":        p95,
            "missed_deadlines":  self._missed,
            "total_commands":    self._total_cmds,
            "total_changes":     self._actuator.total_changes,
            "safety_violations": self._safety.violations,
        }
        msg      = String()
        msg.data = json.dumps(stats)
        self._pub_stats.publish(msg)

        self.get_logger().info(
            f"[ActuatorNode] Stats — "
            f"lat_moy={stats['lat_mean_ms']:.2f} ms | "
            f"p95={p95:.2f} ms | "
            f"missed={self._missed} | "
            f"violations={self._safety.violations}"
        )

    def _log_current_state(self) -> None:
        state = self._actuator.current_state()
        line  = " | ".join(f"{d}:{LIGHT_EMOJI[state[d]]}" for d in DIRECTIONS)
        self.get_logger().info(f"[ActuatorNode] État initial : {line}")


# ──────────────────────────────────────────────
# Point d'entrée
# ──────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = ActuatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("[ActuatorNode] Arrêt demandé.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
