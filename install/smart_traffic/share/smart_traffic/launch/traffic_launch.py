"""
traffic_launch.py — Smart Traffic Controller
=============================================
Fichier de lancement ROS2 : démarre les 4 nœuds automatiquement.

Usage :
    ros2 launch smart_traffic traffic_launch.py
    ros2 launch smart_traffic traffic_launch.py log_level:=debug
    ros2 launch smart_traffic traffic_launch.py enable_dashboard:=false
"""



from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    LogInfo,
    TimerAction,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessStart, OnProcessExit
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    # ── Arguments configurables ───────────────────────────────
    log_level_arg = DeclareLaunchArgument(
        "log_level",
        default_value="info",
        description="Niveau de log : debug | info | warn | error",
        choices=["debug", "info", "warn", "error"],
    )

    enable_dashboard_arg = DeclareLaunchArgument(
        "enable_dashboard",
        default_value="true",
        description="Activer le dashboard graphique (true/false)",
    )

    log_level    = LaunchConfiguration("log_level")
    enable_dash  = LaunchConfiguration("enable_dashboard")

    # ── Nœud 1 : Capteur ─────────────────────────────────────
    sensor_node = Node(
        package="smart_traffic",
        executable="sensor_node",
        name="sensor_node",
        namespace="traffic",
        output="screen",
        emulate_tty=True,
        arguments=["--ros-args", "--log-level", log_level],
        parameters=[
            {"use_sim_time": False},
        ],
        remappings=[
            ("/traffic_data",  "/traffic/traffic_data"),
            ("/sensor_stats",  "/traffic/sensor_stats"),
        ],
    )

    # ── Nœud 2 : Contrôleur (démarré 1 s après le capteur) ───
    controller_node = TimerAction(
        period=1.0,
        actions=[
            Node(
                package="smart_traffic",
                executable="controller_node",
                name="controller_node",
                namespace="traffic",
                output="screen",
                emulate_tty=True,
                arguments=["--ros-args", "--log-level", log_level],
                parameters=[
                    {"use_sim_time": False},
                ],
                remappings=[
                    ("/traffic_data",      "/traffic/traffic_data"),
                    ("/light_commands",    "/traffic/light_commands"),
                    ("/controller_stats",  "/traffic/controller_stats"),
                ],
            )
        ],
    )

    # ── Nœud 3 : Actionneur (démarré 2 s après) ──────────────
    actuator_node = TimerAction(
        period=2.0,
        actions=[
            Node(
                package="smart_traffic",
                executable="actuator_node",
                name="actuator_node",
                namespace="traffic",
                output="screen",
                emulate_tty=True,
                arguments=["--ros-args", "--log-level", log_level],
                parameters=[
                    {"use_sim_time": False},
                ],
                remappings=[
                    ("/light_commands",    "/traffic/light_commands"),
                    ("/actuator_feedback", "/traffic/actuator_feedback"),
                    ("/actuator_stats",    "/traffic/actuator_stats"),
                ],
            )
        ],
    )

    # ── Nœud 4 : Dashboard (démarré 3 s après, si activé) ────
    dashboard_node = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="smart_traffic",
                executable="dashboard_node",
                name="dashboard_node",
                namespace="traffic",
                output="screen",
                emulate_tty=True,
                condition=IfCondition(enable_dash),
                arguments=["--ros-args", "--log-level", log_level],
                parameters=[
                    {"use_sim_time": False},
                ],
                remappings=[
                    ("/sensor_stats",      "/traffic/sensor_stats"),
                    ("/controller_stats",  "/traffic/controller_stats"),
                    ("/actuator_stats",    "/traffic/actuator_stats"),
                    ("/actuator_feedback", "/traffic/actuator_feedback"),
                    ("/traffic_data",      "/traffic/traffic_data"),
                    ("/light_commands",    "/traffic/light_commands"),
                ],
            )
        ],
    )

    # ── Messages de démarrage ─────────────────────────────────
    startup_msg = LogInfo(
        msg="[traffic_launch] 🚦 Démarrage Smart Traffic Controller..."
    )
    ready_msg = TimerAction(
        period=4.0,
        actions=[
            LogInfo(msg="[traffic_launch] ✅ Tous les nœuds démarrés.")
        ],
    )

    return LaunchDescription([
        # Arguments
        log_level_arg,
        enable_dashboard_arg,
        # Messages
        startup_msg,
        # Nœuds (ordre séquentiel via TimerAction)
        sensor_node,
        controller_node,
        actuator_node,
        dashboard_node,
        ready_msg,
    ])
