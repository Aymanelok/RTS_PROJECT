"""
setup.py — Smart Traffic Controller
Configuration du package Python ROS2.
"""

import os
from glob import glob
from setuptools import find_packages, setup

PACKAGE_NAME = "smart_traffic"

setup(
    name=PACKAGE_NAME,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),

    # ── Ressources de données ────────────────────────────────
    data_files=[
        # Index des packages ament
        ("share/ament_index/resource_index/packages", [f"resource/{PACKAGE_NAME}"]),
        # package.xml
        (f"share/{PACKAGE_NAME}", ["package.xml"]),
        # Fichiers launch
        (f"share/{PACKAGE_NAME}/launch", glob("launch/*.py")),
        # Fichiers de configuration (si présents)
        (f"share/{PACKAGE_NAME}/config", glob("config/*.yaml")),
    ],

    # ── Métadonnées ──────────────────────────────────────────
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Smart Traffic Team",
    maintainer_email="student@university.ac.ma",
    description="Smart Traffic Controller — Système ROS2 temps réel",
    license="MIT",

    # ── Tests ────────────────────────────────────────────────
    tests_require=["pytest"],

    # ── Points d'entrée (executables ROS2) ───────────────────
    entry_points={
        "console_scripts": [
            f"sensor_node     = {PACKAGE_NAME}.sensor_node:main",
            f"controller_node = {PACKAGE_NAME}.controller_node:main",
            f"actuator_node   = {PACKAGE_NAME}.actuator_node:main",
            f"dashboard_node  = {PACKAGE_NAME}.dashboard_node:main",
        ],
    },
)
