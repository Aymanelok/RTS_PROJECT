#!/usr/bin/env python3
"""
run_simulation.py — Smart Traffic Controller
============================================
Point d'entree principal de la simulation reelle.

Usage :
    python3 run_simulation.py                    # mode autonome (sans ROS2)
    python3 run_simulation.py --scenario heure_pointe
    python3 run_simulation.py --scenario incident_E
    python3 run_simulation.py --scenario nuit
    python3 run_simulation.py --ros2             # sync avec vrais noeuds ROS2

Scenarios disponibles :
    normal         -- trafic regulier (defaut)
    heure_pointe   -- rush hour, volumes eleves
    incident_E     -- voie Est quasi bloquee
    nuit           -- trafic nocturne tres faible
"""

import sys
import argparse
import signal

from traffic_engine import TrafficEngine, SCENARIOS
from ros2_bridge import ROS2Bridge, StandaloneAutoController
from intersection import IntersectionViz


def parse_args():
    p = argparse.ArgumentParser(
        description="Smart Traffic Controller -- Simulation Reelle 2D"
    )
    p.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="normal",
        help="Scenario de trafic (defaut: normal)"
    )
    p.add_argument(
        "--ros2",
        action="store_true",
        default=False,
        help="Connexion ROS2 pour synchroniser les feux reels"
    )
    return p.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("  Smart Traffic Controller -- Simulation Reelle 2D")
    print("=" * 60)
    print(f"  Scenario : {args.scenario}")
    print(f"  Mode ROS2 : {'active' if args.ros2 else 'desactive (autonome)'}")
    print("=" * 60)

    # 1. Moteur de simulation
    engine = TrafficEngine()
    engine.set_scenario(args.scenario)
    engine.start()
    print(f"[Engine] Moteur demarre -- scenario '{args.scenario}'")

    # 2. Pont ROS2 ou controleur autonome
    bridge     = None
    standalone = None

    if args.ros2:
        bridge = ROS2Bridge(engine)
        mode   = bridge.start()
    else:
        standalone = StandaloneAutoController(engine)
        standalone.start()
        mode = "standalone"

    print(f"[Bridge] Mode actif : {mode}")

    # 3. Arret propre sur Ctrl+C
    def shutdown(sig=None, frame=None):
        print("\n[Simulation] Arret...")
        engine.stop()
        if bridge:
            bridge.stop()
        if standalone:
            standalone.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    # 4. Lancement visualisation (thread principal)
    print("[Viz] Ouverture fenetre de simulation...")
    viz = IntersectionViz(engine)
    try:
        viz.start()   # bloque ici (matplotlib mainloop)
    except KeyboardInterrupt:
        pass
    finally:
        shutdown()


if __name__ == "__main__":
    main()
