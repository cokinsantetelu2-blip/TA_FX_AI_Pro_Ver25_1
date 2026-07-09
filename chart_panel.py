# chart_panel.py
# TA FX AI Pro Ver17.0
# 右パネル表示
# AI SIGNAL / BUY SCORE / SELL SCORE / 採用方向 / 反転確認AI 対応版

import textwrap
import math
from matplotlib.patches import Rectangle, FancyBboxPatch, Wedge

from chart_style import (
    PANEL,
    BORDER,
    TEXT,
    SUBTEXT,
    GREEN,
    RED,
    YELLOW,
    clean_text,
    safe_float,
)


def get_signal_style(signal):
    s = str(signal).upper()

    if "BUY" in s or "買" in s:
        return "BUY", GREEN

    if "SELL" in s or "売" in s:
        return "SELL", RED

    return "WAIT", YELLOW


def draw_ai_score_gauge(ax, score):
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.35, 1.25)
    ax.axis("off")

    score = safe_float(score, 0)
    score = max(0, min(100, score))

    ax.text(
        -1.05,
        1.08,
        "AI SCORE",
        fontsize=13,
        color=TEXT,
        weight="bold",
        ha="left",
        va="center",
    )

    zones = [
        (180, 108, RED),
        (108, 54, YELLOW),
        (54, 0, GREEN),
    ]

    for start, end, color in zones:
        ax.add_patch(
            Wedge(
                (0, 0),
                1.0,
                end,
                start,
                width=0.22,
                facecolor=color,
                edgecolor="none",
                alpha=0.9,
            )
        )

    angle = 180 - (score / 100) * 180

    ax.plot(
        [0, 0.78 * math.cos(math.radians(angle))],
        [0, 0.78 * math.sin(math.radians(angle))],
        color=TEXT,
        linewidth=3.8,
        solid_capstyle="round",
    )

    ax.add_patch(
        Wedge(
            (0, 0),
            0.08,
            0,
            360,
            facecolor=TEXT,
            edgecolor="none",
            alpha=1.0,
        )
    )

    ax.text(
        0,
        -0.17,
        f"{score:.0f}",
        color=TEXT,
        fontsize=18,
        ha="center",
        va="center",
        weight="bold",
    )


def draw_score_row(ax, y, label, value, color):
    ax.text(
        0.08,
        y,
        label,
        transform=ax.transAxes,
        fontsize=9.5,
        color=SUBTEXT,
        weight="bold",
        ha="left",
        va="center",
    )

    ax.text(
        0.92,
        y,
        clean_text(value),
        transform=ax.transAxes,
        fontsize=14,
        color=color,
        weight="bold",
        ha="right",
        va="center",
    )


def draw_signal_panel(
    ax,
    signal="WAIT",
    win_rate_text="-",
    rr_text="-",
    reason_text="-",
    buy_score=None,
    sell_score=None,
    adopted_side=None,
    **kwargs,
):
    ax.axis("off")

    label, color = get_signal_style(signal)

    card = FancyBboxPatch(
        (0.04, 0.03),
        0.92,
        0.94,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        transform=ax.transAxes,
        facecolor=PANEL,
        edgecolor=BORDER,
        linewidth=1.4,
    )

    ax.add_patch(card)

    ax.text(
        0.08,
        0.94,
        "AI SIGNAL",
        transform=ax.transAxes,
        fontsize=10,
        color=SUBTEXT,
        weight="bold",
        ha="left",
    )

    ax.text(
        0.08,
        0.85,
        label,
        transform=ax.transAxes,
        fontsize=32,
        color=color,
        weight="bold",
        ha="left",
    )

    ax.add_patch(
        Rectangle(
            (0.08, 0.77),
            0.80,
            0.016,
            transform=ax.transAxes,
            facecolor=color,
            edgecolor="none",
            alpha=0.95,
        )
    )

    ax.text(
        0.08,
        0.68,
        "Win Rate",
        transform=ax.transAxes,
        fontsize=10,
        color=SUBTEXT,
        ha="left",
    )

    ax.text(
        0.92,
        0.68,
        clean_text(win_rate_text),
        transform=ax.transAxes,
        fontsize=11,
        color=TEXT,
        weight="bold",
        ha="right",
    )

    ax.text(
        0.08,
        0.60,
        "Risk Reward",
        transform=ax.transAxes,
        fontsize=10,
        color=SUBTEXT,
        ha="left",
    )

    ax.text(
        0.92,
        0.60,
        clean_text(rr_text),
        transform=ax.transAxes,
        fontsize=11,
        color=TEXT,
        weight="bold",
        ha="right",
    )

    ax.plot(
        [0.08, 0.92],
        [0.53, 0.53],
        transform=ax.transAxes,
        color=BORDER,
        linewidth=1,
    )

    draw_score_row(
        ax,
        0.47,
        "BUY SCORE",
        f"{safe_float(buy_score, 0):.0f}",
        GREEN,
    )

    draw_score_row(
        ax,
        0.40,
        "SELL SCORE",
        f"{safe_float(sell_score, 0):.0f}",
        RED,
    )

    side_text = clean_text(adopted_side, "WAIT")

    if side_text == "BUY":
        side_color = GREEN
    elif side_text == "SELL":
        side_color = RED
    else:
        side_color = YELLOW

    draw_score_row(
        ax,
        0.33,
        "採用方向",
        side_text,
        side_color,
    )

    ax.plot(
        [0.08, 0.92],
        [0.27, 0.27],
        transform=ax.transAxes,
        color=BORDER,
        linewidth=1,
    )

    ax.text(
        0.08,
        0.25,
        "Analysis",
        transform=ax.transAxes,
        fontsize=10,
        color=SUBTEXT,
        weight="bold",
        ha="left",
    )

    reason = clean_text(reason_text)
    reason = textwrap.fill(reason, width=22)

    ax.text(
        0.08,
        0.20,
        reason,
        transform=ax.transAxes,
        fontsize=8.3,
        color=TEXT,
        ha="left",
        va="top",
        linespacing=1.35,
    )

    ax.plot(
        [0.08, 0.92],
        [0.10, 0.10],
        transform=ax.transAxes,
        color=BORDER,
        linewidth=1,
        alpha=0.8,
    )

    ax.text(
        0.08,
        0.05,
        "TA FX AI Pro Ver17",
        transform=ax.transAxes,
        fontsize=8.5,
        color=SUBTEXT,
        alpha=0.75,
        ha="left",
    )