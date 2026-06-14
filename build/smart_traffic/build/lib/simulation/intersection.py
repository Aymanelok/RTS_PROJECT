#!/usr/bin/env python3
"""
intersection.py — Simulation Réelle Smart Traffic
==================================================
Visualisation 2D animée de l'intersection :
  - Vue de dessus (top-down)
  - 4 routes + zone d'intersection centrale
  - Voitures animées (rectangles colorés) en file d'attente
  - Feux lumineux (cercles R/Y/G) par direction
  - Compteurs de file et véhicules passés
  - 30 FPS via FuncAnimation
  - Pas d'emojis (compatibilité WSL/Tkinter)
"""

import time
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec

from traffic_engine import TrafficEngine, DIRECTIONS, ARRIVAL_LINE, INTERSECTION_DIST, STOP_LINE

# ──────────────────────────────────────────────────────────
# Palette (sans emojis)
# ──────────────────────────────────────────────────────────
COLORS = {
    "bg":         "#0B0F19",
    "road":       "#1E2433",
    "road_dark":  "#151924",
    "grass":      "#091A11",
    "text":       "#F8F9FA",
    "grid":       "#3D4759",
    "panel":      "#121721",
    "GREEN":      "#00E676",
    "YELLOW":     "#FFEA00",
    "RED":        "#FF1744",
    "dim_green":  "#003318",
    "dim_yellow": "#332D00",
    "dim_red":    "#330009",
    "stop_line":  "#FFFFFF",
    "dash":       "#FFC400",
}

# Dimensions normalisées [0..1]
ROAD_W   = 0.14
INTER_S  = 0.14
CX, CY   = 0.5, 0.5

NORTH_STOP = CY + INTER_S / 2
SOUTH_STOP = CY - INTER_S / 2
EAST_STOP  = CX + INTER_S / 2
WEST_STOP  = CX - INTER_S / 2

TOTAL_LEN     = INTERSECTION_DIST - ARRIVAL_LINE
CANVAS_MARGIN = 0.03


def pos_to_canvas(direction: str, position: float) -> tuple:
    """
    Mapping par morceaux :
      segment 1: ARRIVAL_LINE → STOP_LINE  se mappe sur  bord du canvas → stop-line visuelle
      segment 2: STOP_LINE → INTERSECTION_DIST  se mappe sur  stop-line visuelle → bord oppose

    Cela garantit que position=0 (arrêt physique) = stop-line visuelle.
    """
    hi = 1.0 - CANVAS_MARGIN   # 0.97
    lo = CANVAS_MARGIN          # 0.03

    # Fraction dans chaque segment
    if position <= STOP_LINE:
        # Segment approche : de ARRIVAL_LINE a STOP_LINE
        t = (position - ARRIVAL_LINE) / (STOP_LINE - ARRIVAL_LINE)  # 0..1
        t = max(0.0, min(1.0, t))
    else:
        # Segment intersection : de STOP_LINE a INTERSECTION_DIST
        t = 1.0 + (position - STOP_LINE) / (INTERSECTION_DIST - STOP_LINE)  # 1..2
        t = max(1.0, min(2.0, t))

    if direction == "N":
        x = CX - ROAD_W * 0.25
        if t <= 1.0:
            y = hi - t * (hi - NORTH_STOP)       # 0.97 → NORTH_STOP
        else:
            y = NORTH_STOP - (t - 1.0) * (NORTH_STOP - lo)  # NORTH_STOP → 0.03
        return (x, y)

    elif direction == "S":
        x = CX + ROAD_W * 0.25
        if t <= 1.0:
            y = lo + t * (SOUTH_STOP - lo)        # 0.03 → SOUTH_STOP
        else:
            y = SOUTH_STOP + (t - 1.0) * (hi - SOUTH_STOP)  # SOUTH_STOP → 0.97
        return (x, y)

    elif direction == "E":
        y = CY + ROAD_W * 0.25
        if t <= 1.0:
            x = hi - t * (hi - EAST_STOP)         # 0.97 → EAST_STOP
        else:
            x = EAST_STOP - (t - 1.0) * (EAST_STOP - lo)    # EAST_STOP → 0.03
        return (x, y)

    elif direction == "O":
        y = CY - ROAD_W * 0.25
        if t <= 1.0:
            x = lo + t * (WEST_STOP - lo)          # 0.03 → WEST_STOP
        else:
            x = WEST_STOP + (t - 1.0) * (hi - WEST_STOP)    # WEST_STOP → 0.97
        return (x, y)

    return (0.5, 0.5)


def light_box_pos(direction: str) -> tuple:
    """Position (x, y) du boîtier de feu (à la DROITE du conducteur)."""
    margin = 0.03
    if direction == "N":
        return (CX - ROAD_W / 2 - margin, NORTH_STOP - 0.01)
    elif direction == "S":
        return (CX + ROAD_W / 2 + margin, SOUTH_STOP + 0.01)
    elif direction == "E":
        return (EAST_STOP - 0.01, CY + ROAD_W / 2 + margin)
    elif direction == "O":
        return (WEST_STOP + 0.01, CY - ROAD_W / 2 - margin)


class IntersectionViz:
    """Visualiseur 2D animé de l'intersection (compatible WSL / sans emojis)."""

    def __init__(self, engine: TrafficEngine):
        self._engine = engine
        self._t0     = time.monotonic()
        self._ani    = None
        self._setup_figure()

    def _setup_figure(self) -> None:
        plt.style.use("dark_background")
        self._fig = plt.figure(
            figsize=(15, 9),
            facecolor=COLORS["bg"],
            num="Smart Traffic Controller -- Simulation Reelle"
        )
        self._fig.suptitle(
            "Smart Traffic Controller  --  Simulation Reelle Intersection (Vue du Dessus)",
            fontsize=13, fontweight="bold",
            color=COLORS["text"], y=0.98
        )
        gs = GridSpec(1, 2, figure=self._fig,
                      left=0.01, right=0.98, bottom=0.03, top=0.94,
                      wspace=0.04, width_ratios=[3, 1])

        self._ax      = self._fig.add_subplot(gs[0, 0])
        self._ax_info = self._fig.add_subplot(gs[0, 1])

        for ax in (self._ax, self._ax_info):
            ax.set_facecolor(COLORS["bg"])
            ax.axis("off")

    # ──────────────────────────────────────────────────────
    # Dessin du fond statique
    # ──────────────────────────────────────────────────────
    def _draw_background(self) -> None:
        ax = self._ax

        # Herbe
        ax.add_patch(mpatches.Rectangle((0, 0), 1, 1,
            facecolor=COLORS["grass"], zorder=0))

        # Route verticale (N-S)
        ax.add_patch(mpatches.Rectangle(
            (CX - ROAD_W / 2, 0), ROAD_W, 1,
            facecolor=COLORS["road"], zorder=1))

        # Route horizontale (E-O)
        ax.add_patch(mpatches.Rectangle(
            (0, CY - ROAD_W / 2), 1, ROAD_W,
            facecolor=COLORS["road"], zorder=1))

        # Intersection centrale (couleur légèrement différente)
        ax.add_patch(mpatches.Rectangle(
            (CX - INTER_S / 2, CY - INTER_S / 2), INTER_S, INTER_S,
            facecolor=COLORS["road_dark"], zorder=2))

        # Lignes de séparation (tirets jaunes) verticales
        for y in np.arange(0.02, CY - INTER_S / 2, 0.045):
            ax.add_patch(mpatches.Rectangle(
                (CX - 0.004, y), 0.008, 0.028,
                facecolor=COLORS["dash"], alpha=0.7, zorder=3))
        for y in np.arange(CY + INTER_S / 2 + 0.01, 0.98, 0.045):
            ax.add_patch(mpatches.Rectangle(
                (CX - 0.004, y), 0.008, 0.028,
                facecolor=COLORS["dash"], alpha=0.7, zorder=3))

        # Lignes de séparation horizontales
        for x in np.arange(0.02, CX - INTER_S / 2, 0.045):
            ax.add_patch(mpatches.Rectangle(
                (x, CY - 0.004), 0.028, 0.008,
                facecolor=COLORS["dash"], alpha=0.7, zorder=3))
        for x in np.arange(CX + INTER_S / 2 + 0.01, 0.98, 0.045):
            ax.add_patch(mpatches.Rectangle(
                (x, CY - 0.004), 0.028, 0.008,
                facecolor=COLORS["dash"], alpha=0.7, zorder=3))

        # Stop lines
        lw = 0.005
        # Nord : en bas de la route nord, sur la voie droite
        ax.add_patch(mpatches.Rectangle(
            (CX - ROAD_W / 2, NORTH_STOP - lw), ROAD_W / 2, lw,
            facecolor=COLORS["stop_line"], zorder=4, alpha=0.9))
        # Sud
        ax.add_patch(mpatches.Rectangle(
            (CX, SOUTH_STOP), ROAD_W / 2, lw,
            facecolor=COLORS["stop_line"], zorder=4, alpha=0.9))
        # Est
        ax.add_patch(mpatches.Rectangle(
            (EAST_STOP - lw, CY), lw, ROAD_W / 2,
            facecolor=COLORS["stop_line"], zorder=4, alpha=0.9))
        # Ouest
        ax.add_patch(mpatches.Rectangle(
            (WEST_STOP, CY - ROAD_W / 2), lw, ROAD_W / 2,
            facecolor=COLORS["stop_line"], zorder=4, alpha=0.9))

        # Labels directions
        ax.text(CX, 0.975, "NORD",  ha="center", va="top",
                color=COLORS["text"], fontsize=10, fontweight="bold", zorder=10)
        ax.text(CX, 0.025, "SUD",   ha="center", va="bottom",
                color=COLORS["text"], fontsize=10, fontweight="bold", zorder=10)
        ax.text(0.975, CY, "EST",   ha="right",  va="center",
                color=COLORS["text"], fontsize=10, fontweight="bold", zorder=10)
        ax.text(0.025, CY, "OUEST", ha="left",   va="center",
                color=COLORS["text"], fontsize=10, fontweight="bold", zorder=10)

    # ──────────────────────────────────────────────────────
    # Dessin des voitures
    # ──────────────────────────────────────────────────────
    def _draw_cars(self, snap: dict) -> None:
        ax = self._ax
        for d in DIRECTIONS:
            for car in snap[d]["cars"]:
                cx, cy = pos_to_canvas(d, car["position"])

                # Dimensions selon l'orientation
                if d in ("N", "S"):
                    w, h = 0.022, 0.038
                else:
                    w, h = 0.038, 0.022

                # Corps de la voiture
                ax.add_patch(FancyBboxPatch(
                    (cx - w / 2, cy - h / 2), w, h,
                    boxstyle="round,pad=0.004",
                    facecolor=car["color"],
                    edgecolor="#CCCCCC",
                    linewidth=0.8,
                    alpha=0.95,
                    zorder=6
                ))
                # Pare-brise (rectangle clair)
                if d in ("N", "S"):
                    ax.add_patch(mpatches.Rectangle(
                        (cx - w * 0.28, cy - h * 0.2), w * 0.56, h * 0.32,
                        facecolor="#A8D8F0", alpha=0.75, zorder=7))
                else:
                    ax.add_patch(mpatches.Rectangle(
                        (cx - w * 0.2, cy - h * 0.28), w * 0.32, h * 0.56,
                        facecolor="#A8D8F0", alpha=0.75, zorder=7))

    # ──────────────────────────────────────────────────────
    # Dessin des feux de signalisation
    # ──────────────────────────────────────────────────────
    def _draw_lights(self, snap: dict) -> None:
        ax = self._ax
        for d in DIRECTIONS:
            state  = snap[d]["light"]
            lx, ly = light_box_pos(d)

            # Orientation du boîtier : vertical pour N/S, horizontal pour E/O
            if d in ("N", "S"):
                bw, bh = 0.030, 0.080
                positions = [(lx, ly + 0.027), (lx, ly), (lx, ly - 0.027)]  # R, Y, G
            else:
                bw, bh = 0.080, 0.030
                positions = [(lx + 0.027, ly), (lx, ly), (lx - 0.027, ly)]

            # Boîtier
            border_col = COLORS.get(state, COLORS["RED"])
            ax.add_patch(FancyBboxPatch(
                (lx - bw / 2, ly - bh / 2), bw, bh,
                boxstyle="round,pad=0.003",
                facecolor="#111111",
                edgecolor=border_col,
                linewidth=1.8,
                zorder=8
            ))

            # Les trois lampes : Rouge, Jaune, Vert
            for (px, py), lamp in zip(positions, ["RED", "YELLOW", "GREEN"]):
                on    = (state == lamp)
                color = COLORS[lamp] if on else COLORS[f"dim_{lamp.lower()}"]
                r     = 0.011 if on else 0.008
                ax.add_patch(Circle(
                    (px, py), r,
                    facecolor=color, edgecolor="none",
                    alpha=1.0 if on else 0.4, zorder=9))
                # Halo lumineux si allumé
                if on:
                    ax.add_patch(Circle(
                        (px, py), r * 2.8,
                        facecolor=color, edgecolor="none",
                        alpha=0.18, zorder=8))

            # Texte état + file sous le feu
            q     = snap[d]["queue"]
            label = f"{state}\n{q} veh"
            if d == "N":
                ax.text(lx, ly + bh / 2 + 0.012, label,
                        ha="center", va="bottom", fontsize=7.0,
                        color=border_col, zorder=10)
            elif d == "S":
                ax.text(lx, ly - bh / 2 - 0.012, label,
                        ha="center", va="top", fontsize=7.0,
                        color=border_col, zorder=10)
            elif d == "E":
                ax.text(lx, ly + bh / 2 + 0.014, label,
                        ha="center", va="bottom", fontsize=7.0,
                        color=border_col, zorder=10)
            elif d == "O":
                ax.text(lx, ly - bh / 2 - 0.014, label,
                        ha="center", va="top", fontsize=7.0,
                        color=border_col, zorder=10)

    # ──────────────────────────────────────────────────────
    # Panneau statistiques (droite)
    # ──────────────────────────────────────────────────────
    def _draw_stats_panel(self, snap: dict) -> None:
        ax = self._ax_info
        ax.cla()
        ax.set_facecolor(COLORS["panel"])
        ax.axis("off")

        elapsed = time.monotonic() - self._t0

        ax.text(0.5, 0.98, "STATISTIQUES", ha="center", va="top",
                transform=ax.transAxes, fontsize=11, fontweight="bold",
                color=COLORS["text"])
        ax.text(0.5, 0.94, f"Temps : {elapsed:.0f}s",
                ha="center", va="top", transform=ax.transAxes,
                fontsize=9, color=COLORS["grid"])

        total_crossed = sum(snap[d]["crossed"] for d in DIRECTIONS)

        y = 0.88
        for d in DIRECTIONS:
            ds    = snap[d]
            state = ds["light"]
            q     = ds["queue"]
            c     = ds["crossed"]
            col   = COLORS.get(state, COLORS["RED"])

            # En-tête direction + état feu
            state_bar = "[VERT]"   if state == "GREEN"  else \
                        "[JAUNE]"  if state == "YELLOW" else "[ROUGE]"
            ax.text(0.05, y, f"Direction {d}  {state_bar}",
                    transform=ax.transAxes, fontsize=9, fontweight="bold",
                    color=col, va="top")
            y -= 0.05
            ax.text(0.08, y, f"File d'attente : {q:>2} voitures",
                    transform=ax.transAxes, fontsize=8.5,
                    color=COLORS["text"], va="top", fontfamily="monospace")
            y -= 0.04
            ax.text(0.08, y, f"Passees       : {c:>3} voitures",
                    transform=ax.transAxes, fontsize=8.5,
                    color=COLORS["GREEN"], va="top", fontfamily="monospace")
            y -= 0.06

        # Séparateur (ax.plot supporte transform=transAxes)
        ax.plot([0.05, 0.95], [y + 0.01, y + 0.01],
                color=COLORS["grid"], linewidth=0.8,
                transform=ax.transAxes)
        y -= 0.03
        ax.text(0.05, y, f"Total passes  : {total_crossed}",
                transform=ax.transAxes, fontsize=9, fontweight="bold",
                color=COLORS["text"], va="top", fontfamily="monospace")

        # Légende couleurs voitures
        y -= 0.08
        ax.text(0.05, y, "LEGENDE :", transform=ax.transAxes,
                fontsize=8, color=COLORS["grid"], va="top")
        y -= 0.04
        for label, col in [("Attente / Approche", "#4FC3F7"),
                            ("En mouvement",       "#81C784"),
                            ("Traversee",          "#FFD54F")]:
            # Carré de couleur via ax.plot (marker carré)
            ax.plot([0.08], [y - 0.01], marker="s", markersize=9,
                    color=col, transform=ax.transAxes, clip_on=False)
            ax.text(0.16, y, label, transform=ax.transAxes,
                    fontsize=7.5, color=COLORS["text"], va="top")
            y -= 0.04

    # ──────────────────────────────────────────────────────
    # Boucle d'animation
    # ──────────────────────────────────────────────────────
    def _update(self, frame: int) -> None:
        self._ax.cla()
        self._ax.set_facecolor(COLORS["bg"])
        self._ax.set_xlim(0, 1)
        self._ax.set_ylim(0, 1)
        self._ax.set_aspect("equal")
        self._ax.axis("off")

        snap = self._engine.snapshot()

        self._draw_background()
        self._draw_cars(snap)
        self._draw_lights(snap)
        self._draw_stats_panel(snap)

    def start(self) -> None:
        """Lance l'animation — bloque dans le mainloop matplotlib."""
        self._ani = FuncAnimation(
            self._fig,
            self._update,
            interval=33,          # ~30 FPS
            blit=False,
            cache_frame_data=False,
        )
        plt.show()
