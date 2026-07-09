# chart_mobile.py
# TA FX AI Pro Ver15.0
# Mobile Chart 完成版
# BUYフィボ / SELLフィボ 2本表示対応版

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        return float(value)
    except Exception:
        return default


def _safe_text(value, default="-"):
    try:
        if value is None:
            return default
        return str(value)
    except Exception:
        return default


def _setup_font():
    plt.rcParams["font.family"] = "Yu Gothic"
    plt.rcParams["axes.unicode_minus"] = False

def _normalize_candles(candles):
    if candles is None or len(candles) < 10:
        return None

    df = pd.DataFrame(candles).copy()

    rename_map = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Datetime": "time",
        "Date": "time",
        "Time": "time",
    }
    df.rename(columns=rename_map, inplace=True)

    required = ["open", "high", "low", "close"]
    for col in required:
        if col not in df.columns:
            return None
        df[col] = df[col].apply(_safe_float)

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
    else:
        df["time"] = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="h")

    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df.tail(80).reset_index(drop=True)

    if len(df) < 10:
        return None

    df["x"] = range(len(df))
    return df


def _draw_candles(ax, df):
    width = 0.72

    for _, row in df.iterrows():
        x = row["x"]
        o = row["open"]
        h = row["high"]
        l = row["low"]
        c = row["close"]

        up = c >= o
        color = "#00c853" if up else "#ff1744"

        ax.plot([x, x], [l, h], color=color, linewidth=1.8, solid_capstyle="round")

        body_low = min(o, c)
        body_height = abs(c - o)

        if body_height < 0.001:
            body_height = 0.001

        rect = Rectangle(
            (x - width / 2, body_low),
            width,
            body_height,
            facecolor=color,
            edgecolor=color,
            linewidth=1.0,
        )
        ax.add_patch(rect)


def _line_width_for_fib(level):
    text = str(level)

    if "61" in text or "50" in text:
        return 2.2
    if "38" in text or "78" in text:
        return 1.8
    return 1.2


def _draw_single_fib_set(
    ax,
    fib,
    df,
    title="FIB",
    line_color="#ffd54f",
    box_color="#fff176",
    edge_color="#fbc02d",
    label_offset=1.2,
    linestyle="-",
):
    if not fib:
        return

    x_max = df["x"].max()
    label_x = x_max + label_offset

    target_levels = [
        "23.6%",
        "38.2%",
        "50.0%",
        "61.8%",
        "78.6%",
    ]

    for level in target_levels:
        if level not in fib:
            continue

        price = _safe_float(fib.get(level))

        if price is None:
            continue

        lw = _line_width_for_fib(level)

        ax.axhline(
            price,
            color=line_color,
            linewidth=lw,
            alpha=0.82,
            linestyle=linestyle,
        )

        ax.text(
            label_x,
            price,
            f"{title} {level}  {price:.3f}",
            fontsize=11,
            fontweight="bold",
            color="black",
            va="center",
            ha="left",
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor=box_color,
                edgecolor=edge_color,
                alpha=0.92,
            ),
        )


def _draw_fibs(ax, fib=None, buy_fib=None, sell_fib=None, df=None):
    if df is None:
        return

    if buy_fib or sell_fib:
        _draw_single_fib_set(
            ax,
            buy_fib,
            df,
            title="BUY",
            line_color="#00c853",
            box_color="#c8f7c5",
            edge_color="#00a152",
            label_offset=1.2,
            linestyle="-",
        )

        _draw_single_fib_set(
            ax,
            sell_fib,
            df,
            title="SELL",
            line_color="#ff1744",
            box_color="#ffcdd2",
            edge_color="#d50000",
            label_offset=5.7,
            linestyle="--",
        )

        return

    _draw_single_fib_set(
        ax,
        fib,
        df,
        title="FIB",
        line_color="#ffd54f",
        box_color="#fff176",
        edge_color="#fbc02d",
        label_offset=1.2,
        linestyle="-",
    )


def _draw_price_line(ax, current_price, df):
    price = _safe_float(current_price)

    if price is None:
        price = _safe_float(df["close"].iloc[-1])

    if price is None:
        return

    x_max = df["x"].max()

    ax.axhline(price, color="#00e5ff", linewidth=2.4, alpha=0.95)

    ax.text(
        x_max + 1.2,
        price,
        f"NOW {price:.3f}",
        fontsize=14,
        fontweight="bold",
        color="white",
        va="center",
        ha="left",
        bbox=dict(
            boxstyle="round,pad=0.28",
            facecolor="#00acc1",
            edgecolor="#006064",
            alpha=0.98,
        ),
    )


def _draw_trade_levels(ax, entry_text=None, stop_text=None, tp1_text=None, tp2_text=None):
    levels = [
        ("ENTRY", entry_text, "#2962ff"),
        ("SL", stop_text, "#d50000"),
        ("TP1", tp1_text, "#00c853"),
        ("TP2", tp2_text, "#00a152"),
    ]

    x_left, _ = ax.get_xlim()

    for name, text, color in levels:
        if not text:
            continue

        raw = str(text)
        price = None

        for part in raw.replace(":", " ").split():
            price = _safe_float(part)
            if price is not None:
                break

        if price is None:
            continue

        ax.axhline(price, color=color, linewidth=2.3, alpha=0.9, linestyle="--")

        ax.text(
            x_left + 1,
            price,
            f"{name} {price:.3f}",
            fontsize=12,
            fontweight="bold",
            color="white",
            va="center",
            ha="left",
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor=color,
                edgecolor=color,
                alpha=0.95,
            ),
        )


def _judge_signal_color(signal):
    text = _safe_text(signal, "").upper()

    if "BUY" in text or "買" in text:
        return "#00c853"
    if "SELL" in text or "売" in text:
        return "#ff1744"
    return "#ffb300"


def _draw_info_panel(
    ax,
    signal=None,
    ai_score=0,
    win_rate_text="-",
    rsi14=None,
    dow_text=None,
    mtf_text=None,
    title="TA FX AI Pro Ver15",
):
    ax.axis("off")

    signal_text = _safe_text(signal, "WAIT")
    signal_color = _judge_signal_color(signal_text)

    rsi_text = "-"
    rsi_value = _safe_float(rsi14)
    if rsi_value is not None:
        rsi_text = f"{rsi_value:.1f}"

    lines = [
        ("SIGNAL", signal_text, signal_color),
        ("AI SCORE", f"{ai_score}", "#111111"),
        ("WIN RATE", _safe_text(win_rate_text), "#111111"),
        ("RSI14", rsi_text, "#111111"),
        ("DOW", _safe_text(dow_text), "#111111"),
        ("MTF", _safe_text(mtf_text), "#111111"),
    ]

    ax.text(
        0.01,
        0.86,
        title,
        fontsize=15,
        fontweight="bold",
        color="#111111",
        transform=ax.transAxes,
    )

    x = 0.01
    y = 0.48

    for label, value, color in lines:
        ax.text(
            x,
            y,
            f"{label}: {value}",
            fontsize=11,
            fontweight="bold",
            color=color,
            transform=ax.transAxes,
            va="center",
        )
        x += 0.165

        if x > 0.86:
            x = 0.01
            y -= 0.28


def create_mobile_chart_1h(
    candles,
    fib=None,
    buy_fib=None,
    sell_fib=None,
    current_price=None,
    signal=None,
    ai_score=0,
    win_rate_text="-",
    rsi14=None,
    dow_text=None,
    mtf_text=None,
    entry_text=None,
    stop_text=None,
    tp1_text=None,
    tp2_text=None,
    filename="mobile_chart_1h.png",
):
    _setup_font()

    df = _normalize_candles(candles)

    if df is None:
        print("スマホチャート作成失敗: ローソク足データ不足")
        return None

    fig = plt.figure(figsize=(8, 10), dpi=120)
    gs = fig.add_gridspec(2, 1, height_ratios=[8.7, 1.3], hspace=0.08)

    ax = fig.add_subplot(gs[0])
    info_ax = fig.add_subplot(gs[1])

    fig.patch.set_facecolor("#f5f5f5")
    ax.set_facecolor("#ffffff")

    _draw_candles(ax, df)

    high = df["high"].max()
    low = df["low"].min()
    pad = max((high - low) * 0.12, 0.05)

    ax.set_ylim(low - pad, high + pad)
    ax.set_xlim(-1, len(df) + 15)

    _draw_fibs(
        ax,
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
        df=df,
    )

    _draw_price_line(ax, current_price, df)

    _draw_trade_levels(
        ax,
        entry_text=entry_text,
        stop_text=stop_text,
        tp1_text=tp1_text,
        tp2_text=tp2_text,
    )

    _draw_info_panel(
        info_ax,
        signal=signal,
        ai_score=ai_score,
        win_rate_text=win_rate_text,
        rsi14=rsi14,
        dow_text=dow_text,
        mtf_text=mtf_text,
        title="TA FX AI Pro Ver15",
    )

    ax.grid(True, linestyle="--", alpha=0.25)
    ax.tick_params(axis="y", labelsize=12)
    ax.tick_params(axis="x", labelsize=9)

    tick_positions = list(range(0, len(df), max(1, len(df) // 5)))
    tick_labels = []

    for pos in tick_positions:
        try:
            t = df.loc[pos, "time"]
            tick_labels.append(pd.to_datetime(t).strftime("%m/%d\n%H:%M"))
        except Exception:
            tick_labels.append(str(pos))

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)

    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")

    for spine in ["top", "left"]:
        ax.spines[spine].set_visible(False)

    plt.subplots_adjust(left=0.04, right=0.76, top=0.97, bottom=0.04)

    try:
        fig.savefig(
            filename,
            dpi=120,
            bbox_inches="tight",
            pad_inches=0.15,
        )
        plt.close(fig)
        return filename

    except Exception as e:
        plt.close(fig)
        print("スマホチャート保存失敗:", e)
        return None


def create_mobile_chart_image(
    candles,
    fib=None,
    buy_fib=None,
    sell_fib=None,
    current_price=None,
    signal=None,
    ai_score=0,
    win_rate_text="-",
    rsi14=None,
    dow_text=None,
    mtf_text=None,
    entry_text=None,
    stop_text=None,
    tp1_text=None,
    tp2_text=None,
    filename="mobile_chart.png",
):
    return create_mobile_chart_1h(
        candles=candles,
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
        current_price=current_price,
        signal=signal,
        ai_score=ai_score,
        win_rate_text=win_rate_text,
        rsi14=rsi14,
        dow_text=dow_text,
        mtf_text=mtf_text,
        entry_text=entry_text,
        stop_text=stop_text,
        tp1_text=tp1_text,
        tp2_text=tp2_text,
        filename=filename,
    )


def create_mobile_chart_4h(
    candles,
    fib=None,
    buy_fib=None,
    sell_fib=None,
    current_price=None,
    signal=None,
    ai_score=0,
    win_rate_text="-",
    rsi14=None,
    dow_text=None,
    mtf_text=None,
    entry_text=None,
    stop_text=None,
    tp1_text=None,
    tp2_text=None,
    filename="mobile_chart_4h.png",
):
    return create_mobile_chart_1h(
        candles=candles,
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
        current_price=current_price,
        signal=signal,
        ai_score=ai_score,
        win_rate_text=win_rate_text,
        rsi14=rsi14,
        dow_text=dow_text,
        mtf_text=mtf_text,
        entry_text=entry_text,
        stop_text=stop_text,
        tp1_text=tp1_text,
        tp2_text=tp2_text,
        filename=filename,
    )


def create_mobile_chart_1d(
    candles,
    fib=None,
    buy_fib=None,
    sell_fib=None,
    current_price=None,
    signal=None,
    ai_score=0,
    win_rate_text="-",
    rsi14=None,
    dow_text=None,
    mtf_text=None,
    entry_text=None,
    stop_text=None,
    tp1_text=None,
    tp2_text=None,
    filename="mobile_chart_1d.png",
):
    return create_mobile_chart_1h(
        candles=candles,
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
        current_price=current_price,
        signal=signal,
        ai_score=ai_score,
        win_rate_text=win_rate_text,
        rsi14=rsi14,
        dow_text=dow_text,
        mtf_text=mtf_text,
        entry_text=entry_text,
        stop_text=stop_text,
        tp1_text=tp1_text,
        tp2_text=tp2_text,
        filename=filename,
    )