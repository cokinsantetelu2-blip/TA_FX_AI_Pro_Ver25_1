# chart_style.py

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib as mpl

mpl.rcParams["font.family"] =  "Yu Gothic"
BG = "#0b0f14"
PANEL = "#1b2130"
GRID = "#2A2E39"
BORDER = "#3B4252"
TEXT = "#FFFFFF"
SUBTEXT = "#B0BEC5"
GREEN = "#26A69A"
RED = "#EF5350"
BLUE = "#42A5F5"
ORANGE = "#FFA726"
YELLOW = "#FFCA28"
PURPLE = "#AB47BC"

FIB_GRAY = "#8A949E"


def setup_japanese_font():
    candidates = [
        "Meiryo",
        "Yu Gothic",
        "Yu Gothic UI",
        "MS Gothic",
        "Noto Sans CJK JP",
        "Noto Sans JP",
        "IPAexGothic",
        "IPAGothic",
    ]

    available = [f.name for f in fm.fontManager.ttflist]

    for font in candidates:
        if font in available:
            plt.rcParams["font.family"] = font
            plt.rcParams["axes.unicode_minus"] = False
            return font

    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False
    return "DejaVu Sans"


JP_FONT = setup_japanese_font()


def safe_float(value, default=None):
    try:
        if value is None:
            return default

        if isinstance(value, str):
            value = value.replace("Entry:", "")
            value = value.replace("ENTRY:", "")
            value = value.replace("SL:", "")
            value = value.replace("TP1:", "")
            value = value.replace("TP2:", "")
            value = value.replace("RR1:", "")
            value = value.replace("RR2:", "")
            value = value.replace("円", "")
            value = value.strip()

        return float(value)
    except Exception:
        return default


def clean_text(value, default="-"):
    if value is None:
        return default

    text = str(value).strip()

    if text == "":
        return default

    return text


def style_axis(ax):
    ax.set_facecolor(BG)
    ax.grid(True, color=GRID, linewidth=0.7, alpha=0.85)
    ax.tick_params(colors=SUBTEXT, labelsize=9)

    for spine in ax.spines.values():
        spine.set_color(BORDER)