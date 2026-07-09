# chart_draw.py
# TA FX AI Pro Ver15.2
# TradingView風チャート描画部品 完成版
# BUYフィボ / SELLフィボ 別描画対応版

import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle

from chart_style import (
    TEXT,
    GREEN,
    RED,
    BLUE,
    ORANGE,
    PURPLE,
    FIB_GRAY,
    safe_float,
)


BOX_ALPHA = 0.98
LINE_ALPHA = 0.72

BUY_FIB_COLOR = "#00C853"
SELL_FIB_COLOR = "#FF1744"
BUY_FIB_BOX = "#B9F6CA"
SELL_FIB_BOX = "#FFCDD2"


def draw_candles(ax, df):
    width = 0.62

    if df is None or len(df) == 0:
        return

    for _, row in df.iterrows():
        x = row["X"]
        o = row["open"]
        h = row["high"]
        l = row["low"]
        c = row["close"]

        color = GREEN if c >= o else RED

        ax.vlines(
            x,
            l,
            h,
            color=color,
            linewidth=1.1,
            alpha=0.95,
            zorder=3,
        )

        body_low = min(o, c)
        body_height = abs(c - o)

        if body_height < 0.0001:
            body_height = 0.0001

        ax.add_patch(
            Rectangle(
                (x - width / 2, body_low),
                width,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.8,
                alpha=0.95,
                zorder=4,
            )
        )


def format_price_for_chart(price):
    price = safe_float(price, None)

    if price is None:
        return "-"

    if abs(price) >= 1000:
        return f"{price:.2f}"

    if abs(price) >= 10:
        return f"{price:.3f}"

    if abs(price) >= 1:
        return f"{price:.4f}"

    return f"{price:.5f}"


def draw_box(
    ax,
    x_rate,
    y_rate,
    text,
    color,
    fontsize=7.5,
    pad=0.24,
    ha="left",
):
    ax.text(
        x_rate,
        y_rate,
        text,
        transform=ax.transAxes,
        va="center",
        ha=ha,
        fontsize=fontsize,
        color=TEXT,
        weight="bold",
        bbox=dict(
            boxstyle=f"round,pad={pad}",
            facecolor=color,
            edgecolor=color,
            alpha=BOX_ALPHA,
        ),
        zorder=90,
        clip_on=False,
    )


def price_to_axis_rate(ax, price):
    ymin, ymax = ax.get_ylim()

    if ymax <= ymin:
        return None

    return (price - ymin) / (ymax - ymin)


def draw_price_box(
    ax,
    x_rate,
    price,
    text,
    color,
    fontsize=7.5,
    pad=0.24,
):
    price = safe_float(price, None)

    if price is None:
        return

    y_rate = price_to_axis_rate(ax, price)

    if y_rate is None:
        return

    if y_rate < -0.08 or y_rate > 1.08:
        return

    draw_box(
        ax,
        x_rate,
        y_rate,
        text,
        color,
        fontsize=fontsize,
        pad=pad,
    )


def draw_price_line(
    ax,
    price,
    x_min,
    x_max,
    color,
    linestyle="--",
    linewidth=0.9,
    alpha=LINE_ALPHA,
    zorder=2,
):
    price = safe_float(price, None)

    if price is None:
        return

    ax.hlines(
        price,
        x_min,
        x_max,
        colors=color,
        linestyles=linestyle,
        linewidth=linewidth,
        alpha=alpha,
        zorder=zorder,
    )


def make_fib_label(key):
    text = str(key)

    if "%" in text:
        return text

    try:
        value = float(text)

        if value <= 1:
            return f"{value * 100:.1f}%"

        return f"{value:.1f}%"

    except Exception:
        return text


def get_fib_color(key):
    colors = {
        "0": "#777777",
        "0.0": "#777777",
        "0.0%": "#777777",
        "23.6%": "#607D8B",
        "38.2%": BLUE,
        "50.0%": PURPLE,
        "61.8%": ORANGE,
        "78.6%": "#FF7043",
        "100.0%": "#777777",
        "0.236": "#607D8B",
        "0.382": BLUE,
        "0.5": PURPLE,
        "0.500": PURPLE,
        "0.618": ORANGE,
        "0.786": "#FF7043",
        "1": "#777777",
        "1.0": "#777777",
    }

    return colors.get(str(key), FIB_GRAY)


def fixed_y_positions(count, top=0.78, bottom=0.25):
    if count <= 0:
        return []

    if count == 1:
        return [(top + bottom) / 2]

    return np.linspace(top, bottom, count).tolist()


def avoid_label_overlap(rates, min_gap=0.055):
    if not rates:
        return []

    sorted_rates = sorted(rates, reverse=True)
    adjusted = []

    for rate in sorted_rates:
        if not adjusted:
            adjusted.append(rate)
            continue

        prev = adjusted[-1]

        if prev - rate < min_gap:
            rate = prev - min_gap

        adjusted.append(rate)

    if adjusted and adjusted[-1] < 0.04:
        shift = 0.04 - adjusted[-1]
        adjusted = [r + shift for r in adjusted]

    adjusted = [min(0.96, max(0.04, r)) for r in adjusted]

    return adjusted


def build_fib_items(fib, side="FIB"):
    items = []

    if not fib:
        return items

    target_order = [
        "0.0%",
        "23.6%",
        "38.2%",
        "50.0%",
        "61.8%",
        "78.6%",
        "100.0%",
    ]

    for key in target_order:
        if key not in fib:
            continue

        price = safe_float(fib.get(key), None)

        if price is None:
            continue

        items.append(
            {
                "price": price,
                "label": make_fib_label(key),
                "key": key,
                "side": side,
                "color": get_fib_color(key),
            }
        )

    if not items:
        for key, value in fib.items():
            price = safe_float(value, None)

            if price is None:
                continue

            items.append(
                {
                    "price": price,
                    "label": make_fib_label(key),
                    "key": key,
                    "side": side,
                    "color": get_fib_color(key),
                }
            )

    return sorted(items, key=lambda x: x["price"], reverse=True)


def _draw_single_fib(
    ax,
    df,
    fib,
    y_min,
    y_max,
    side="FIB",
    line_color=None,
    box_color=None,
    title_x=0.925,
    label_x=0.935,
    title_y=0.945,
    compact=False,
    linestyle="--",
):
    if not fib or df is None or len(df) == 0:
        return

    x_min = df["X"].min()
    x_max = df["X"].max()

    items = build_fib_items(fib, side=side)

    visible_items = []

    for item in items:
        price = item["price"]

        if price < y_min or price > y_max:
            continue

        if line_color is None:
            color = item["color"]
        else:
            color = line_color

        visible_items.append(item)

        draw_price_line(
            ax,
            price,
            x_min,
            x_max + 3.0,
            color,
            linestyle=linestyle,
            linewidth=0.80 if compact else 1.05,
            alpha=0.45 if compact else 0.70,
            zorder=2,
        )

    if not visible_items:
        return

    ax.text(
        title_x,
        title_y,
        side,
        transform=ax.transAxes,
        color=TEXT,
        fontsize=7 if compact else 9,
        weight="bold",
        ha="left",
        va="center",
        zorder=90,
        clip_on=False,
    )

    if compact:
        ys = fixed_y_positions(
            len(visible_items),
            top=0.78,
            bottom=0.30,
        )

        for item, y in zip(visible_items, ys):
            label = f"{side} {item['label']}"
            draw_box(
                ax,
                label_x,
                y,
                label,
                box_color or item["color"],
                fontsize=5.5,
                pad=0.13,
            )
    else:
        raw_rates = []

        for item in visible_items:
            rate = price_to_axis_rate(ax, item["price"])
            if rate is not None:
                raw_rates.append(rate)

        adjusted_rates = avoid_label_overlap(raw_rates, min_gap=0.052)

        for item, y in zip(visible_items, adjusted_rates):
            label = f"{side} {item['label']}  {format_price_for_chart(item['price'])}"

            draw_box(
                ax,
                label_x,
                y,
                label,
                box_color or item["color"],
                fontsize=6.8,
                pad=0.20,
            )


def draw_dual_fibonacci(
    ax,
    df,
    buy_fib=None,
    sell_fib=None,
    y_min=None,
    y_max=None,
    compact=False,
):
    if df is None or len(df) == 0:
        return

    if y_min is None or y_max is None:
        y_min, y_max = ax.get_ylim()

    if buy_fib:
        _draw_single_fib(
            ax,
            df,
            buy_fib,
            y_min,
            y_max,
            side="BUY",
            line_color=BUY_FIB_COLOR,
            box_color=BUY_FIB_BOX,
            title_x=0.890 if not compact else 0.900,
            label_x=0.900 if not compact else 0.910,
            title_y=0.945,
            compact=compact,
            linestyle="-",
        )

    if sell_fib:
        _draw_single_fib(
            ax,
            df,
            sell_fib,
            y_min,
            y_max,
            side="SELL",
            line_color=SELL_FIB_COLOR,
            box_color=SELL_FIB_BOX,
            title_x=0.890 if not compact else 0.900,
            label_x=1.025 if not compact else 1.000,
            title_y=0.900,
            compact=compact,
            linestyle="--",
        )


def draw_fibonacci(
    ax,
    df,
    fib=None,
    y_min=None,
    y_max=None,
    compact=False,
    buy_fib=None,
    sell_fib=None,
):
    """
    旧仕様互換 + Ver15対応

    旧:
        draw_fibonacci(ax, df, fib, y_min, y_max)

    新:
        draw_fibonacci(ax, df, y_min=y_min, y_max=y_max, buy_fib=buy_fib, sell_fib=sell_fib)
    """
    if buy_fib or sell_fib:
        draw_dual_fibonacci(
            ax,
            df,
            buy_fib=buy_fib,
            sell_fib=sell_fib,
            y_min=y_min,
            y_max=y_max,
            compact=compact,
        )
        return

    if not fib or df is None or len(df) == 0:
        return

    if y_min is None or y_max is None:
        y_min, y_max = ax.get_ylim()

    _draw_single_fib(
        ax,
        df,
        fib,
        y_min,
        y_max,
        side="FIB",
        line_color=None,
        box_color=None,
        title_x=0.925,
        label_x=0.935,
        title_y=0.945,
        compact=compact,
        linestyle="--",
    )


def build_trade_items(items):
    clean_items = []

    if not items:
        return clean_items

    for item in items:
        price = safe_float(item.get("price"), None)

        if price is None:
            continue

        label = str(item.get("label", "")).upper()

        if label == "NOW":
            continue

        clean_items.append(
            {
                "price": price,
                "label": label,
                "color": item.get("color", TEXT),
                "linestyle": item.get("linestyle", "-"),
                "linewidth": item.get("linewidth", 1.2),
                "alpha": item.get("alpha", 0.95),
            }
        )

    order = {
        "ENTRY": 1,
        "SL": 2,
        "TP1": 3,
        "TP2": 4,
    }

    return sorted(
        clean_items,
        key=lambda x: order.get(str(x.get("label", "")), 99),
    )


def get_trade_line_style(item):
    label = str(item.get("label", "")).upper()

    if label == "ENTRY":
        return {
            "linestyle": "-",
            "linewidth": 1.8,
            "alpha": 0.96,
            "zorder": 7,
            "fontsize": 7.8,
            "pad": 0.23,
        }

    if label == "SL":
        return {
            "linestyle": "-",
            "linewidth": 1.8,
            "alpha": 0.96,
            "zorder": 7,
            "fontsize": 7.8,
            "pad": 0.23,
        }

    return {
        "linestyle": "--",
        "linewidth": 1.4,
        "alpha": 0.88,
        "zorder": 6,
        "fontsize": 7.4,
        "pad": 0.21,
    }


def draw_trade_lines(ax, x_min, x_max, items, y_min, y_max):
    trade_items = build_trade_items(items)

    if not trade_items:
        return

    visible_items = [
        item for item in trade_items
        if y_min <= item["price"] <= y_max
    ]

    if not visible_items:
        return

    raw_rates = []

    for item in visible_items:
        rate = price_to_axis_rate(ax, item["price"])
        raw_rates.append(rate if rate is not None else 0.5)

    adjusted_rates = avoid_label_overlap(raw_rates, min_gap=0.060)

    for item, label_y in zip(visible_items, adjusted_rates):
        style = get_trade_line_style(item)

        draw_price_line(
            ax,
            item["price"],
            x_min,
            x_max + 1.6,
            item["color"],
            linestyle=style["linestyle"],
            linewidth=style["linewidth"],
            alpha=style["alpha"],
            zorder=style["zorder"],
        )

        label = item["label"]

        if label == "ENTRY":
            text = f"ENTRY  {format_price_for_chart(item['price'])}"
        else:
            text = f"{label}  {format_price_for_chart(item['price'])}"

        draw_box(
            ax,
            1.018,
            label_y,
            text,
            item["color"],
            fontsize=style["fontsize"],
            pad=style["pad"],
        )


def draw_tf_trade_lines(ax, df, items, compact=True):
    """
    4H / 1D 用の軽量トレードライン
    ENTRY / SL / TP1 / TP2 を小さく表示
    NOWは表示しない
    """
    if df is None or len(df) == 0:
        return

    trade_items = build_trade_items(items)

    if not trade_items:
        return

    x_min = df["X"].min()
    x_max = df["X"].max()

    y_min, y_max = ax.get_ylim()

    visible_items = [
        item for item in trade_items
        if y_min <= item["price"] <= y_max
    ]

    if not visible_items:
        return

    raw_rates = []

    for item in visible_items:
        rate = price_to_axis_rate(ax, item["price"])
        raw_rates.append(rate if rate is not None else 0.5)

    adjusted_rates = avoid_label_overlap(
        raw_rates,
        min_gap=0.075 if compact else 0.060,
    )

    for item, label_y in zip(visible_items, adjusted_rates):
        style = get_trade_line_style(item)

        label = item["label"]

        draw_price_line(
            ax,
            item["price"],
            x_min,
            x_max + 0.8,
            item["color"],
            linestyle=style["linestyle"],
            linewidth=0.85 if compact else style["linewidth"],
            alpha=0.62,
            zorder=6,
        )

        draw_box(
            ax,
            1.012,
            label_y,
            label,
            item["color"],
            fontsize=5.8 if compact else 7.0,
            pad=0.14 if compact else 0.20,
        )


def make_time_labels(df, count=6):
    if df is None or len(df) == 0:
        return [], []

    length = len(df)

    if length <= count:
        indexes = list(range(length))
    else:
        indexes = np.linspace(
            0,
            length - 1,
            count,
        ).astype(int).tolist()

    positions = []
    labels = []

    for i in indexes:
        try:
            t = pd.to_datetime(df.loc[i, "time"])

            positions.append(df.loc[i, "X"])

            if t.hour == 0 and t.minute == 0:
                labels.append(t.strftime("%m/%d"))
            else:
                labels.append(t.strftime("%m/%d\n%H:%M"))

        except Exception:
            pass

    return positions, labels