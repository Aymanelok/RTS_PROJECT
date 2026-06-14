#!/usr/bin/env python3
"""
ros2_bridge.py — Simulation Réelle Smart Traffic
=================================================
Pont ROS2 ↔ Simulation :
  - S'abonne aux topics /actuator_feedback et /traffic_data
  - Met à jour l'état des feux dans le TrafficEngine en temps réel
  - Fonctionne en mode dégradé (standalone) si ROS2 n'est pas lancé
"""

import json
import threading
import time
from typing import Optional, Callable

from traffic_engine import TrafficEngine, DIRECTIONS

# ─────────────────────────────────────────────────────────
# Tentative d'import ROS2 (optionnel)
# ─────────────────────────────────────────────────────────
try:
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
    from std_msgs.msg import String
    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False


class StandaloneAutoController:
    """
    Contrôleur autonome utilisé si ROS2 n'est pas disponible.
    Simule un cycle de feux simple pour permettre la démonstration visuelle.
    Cycle : chaque direction passe au vert pendant 10 secondes.
    """

    def __init__(self, engine: TrafficEngine):
        self._engine  = engine
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._phase_idx  = 0
        self._phase_time = 0.0
        self._green_time = 10.0  # secondes par phase
        self._yellow_time = 3.0  # secondes pour le jaune
        self._is_yellow = False

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[Bridge-Standalone] Contrôleur autonome démarré (sans ROS2).")

    def stop(self) -> None:
        self._running = False

    def _loop(self) -> None:
        last = time.monotonic()
        while self._running:
            now = time.monotonic()
            dt  = now - last
            last = now

            self._phase_time += dt
            
            if not self._is_yellow:
                if self._phase_time >= self._green_time:
                    self._is_yellow = True
                    self._phase_time = 0.0
            else:
                if self._phase_time >= self._yellow_time:
                    self._is_yellow = False
                    self._phase_time = 0.0
                    self._phase_idx = (self._phase_idx + 1) % len(DIRECTIONS)

            active = DIRECTIONS[self._phase_idx]
            if not self._is_yellow:
                lights = {d: ("GREEN" if d == active else "RED") for d in DIRECTIONS}
            else:
                lights = {d: ("YELLOW" if d == active else "RED") for d in DIRECTIONS}
                
            self._engine.set_all_lights(lights)

            time.sleep(0.1)


if ROS2_AVAILABLE:
    class ROS2BridgeNode(Node):
        """
        Nœud ROS2 léger qui écoute les topics du système principal
        et propage les changements de feux vers le TrafficEngine.
        """

        RT_QOS = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        def __init__(self, engine: TrafficEngine):
            super().__init__("simulation_bridge")
            self._engine = engine
            self._last_lights: dict = {d: "RED" for d in DIRECTIONS}

            # Abonnements
            self.create_subscription(
                String, "/actuator_feedback", self._on_feedback, self.RT_QOS
            )
            self.create_subscription(
                String, "/traffic_data", self._on_traffic, self.RT_QOS
            )
            
            # Publication des compteurs de la simulation
            self._pub_counts = self.create_publisher(String, "/sim_counts", self.RT_QOS)
            self.create_timer(0.1, self._publish_counts)

            self.get_logger().info("[SimBridge] Connecté aux topics ROS2.")

        def _publish_counts(self) -> None:
            """Publie les compteurs de véhicules réels de la simulation 2D."""
            try:
                snap = self._engine.snapshot()
                counts = {d: snap[d]["queue"] for d in DIRECTIONS}
                msg = String()
                msg.data = json.dumps({"counts": counts})
                self._pub_counts.publish(msg)
            except Exception as e:
                self.get_logger().warn(f"[SimBridge] Erreur pub_counts: {e}")

        def _on_feedback(self, msg: String) -> None:
            """Reçoit l'état des feux depuis l'actionneur."""
            try:
                d = json.loads(msg.data)
                lights = d.get("lights", {})
                if lights:
                    self._engine.set_all_lights(lights)
                    self._last_lights = lights
            except Exception as e:
                self.get_logger().warn(f"[SimBridge] Erreur feedback: {e}")

        def _on_traffic(self, msg: String) -> None:
            """Reçoit les compteurs véhicules du capteur (optionnel)."""
            try:
                d = json.loads(msg.data)
                # On pourrait ajuster lambda ici si besoin
                _ = d.get("counts", {})
            except Exception:
                pass


class ROS2Bridge:
    """
    Façade publique : lance le pont ROS2 ou le contrôleur autonome
    selon que ROS2 est disponible ou non.
    """

    def __init__(self, engine: TrafficEngine):
        self._engine     = engine
        self._node       = None
        self._standalone = None
        self._ros_thread: Optional[threading.Thread] = None

    def start(self) -> str:
        """Démarre le pont. Retourne le mode utilisé."""
        if ROS2_AVAILABLE:
            try:
                rclpy.init()
                self._node = ROS2BridgeNode(self._engine)
                self._ros_thread = threading.Thread(
                    target=rclpy.spin, args=(self._node,), daemon=True
                )
                self._ros_thread.start()
                print("[Bridge] Mode ROS2 — Topics: /actuator_feedback, /traffic_data")
                return "ros2"
            except Exception as e:
                print(f"[Bridge] Échec ROS2 ({e}), bascule en mode autonome.")

        # Fallback autonome
        self._standalone = StandaloneAutoController(self._engine)
        self._standalone.start()
        return "standalone"

    def stop(self) -> None:
        if self._node:
            self._node.destroy_node()
            rclpy.shutdown()
        if self._standalone:
            self._standalone.stop()
