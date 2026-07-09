# chart_pro.py
# TA FX AI Pro Ver16.0
# Main総合チャート
# BUYフィボ / SELLフィボ 同時表示対応版
# BUY SCORE / SELL SCORE / 採用方向 表示対応版

import warnings
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import settings

from chart_style import (
    BG,
    PANEL,
    BORDER,
    TEXT,
    SUBTEXT,
    GREEN,
    RED,
    BLUE,
    ORANGE,
    YELLOW,
    PURPLE,
    safe_float,
    clean_text,
    style_axis,
)

from chart_indicator import (
    ema,
    calculate_macd,
    calculate_adx,
)

from chart_draw import (
    draw_candles,
    draw_fibonacci,
    draw_trade_lines,
    draw_tf_trade_lines,
    make_time_labels,
)

from chart_panel import (
    draw_ai_score_gauge,
    draw_signal_panel,
)

warnings.filterwarnings("ignore")


def format_price(value):
    try:
        value = float(value)

        if "JPY" in settings.SYMBOL_NAME:
            return f"{value:.3f}"

        if settings.SYMBOL_NAME in ["BTC", "ETH"]:
            return f"{value:.2f}"

        if settings.SYMBOL_NAME == "XRP":
            return f"{value:.4f}"

        return f"{value:.5f}"

    except Exception:
        return str(value)


def normalize_candles(candles, limit=None):
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
            print(f"ローソク足データに {col} がありません")
            return None
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
    else:
        df["time"] = pd.date_range(end=datetime.now(), periods=len(df), freq="h")

    df.dropna(subset=["open", "high", "low", "close"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    if limit:
        df = df.tail(limit).reset_index(drop=True)

    if len(df) < 10:
        return None

    df["X"] = range(len(df))

    return df


def add_indicators(df):
    df = df.copy()
    df["ema20"] = ema(df["close"], 20)
    df["ema75"] = ema(df["close"], 75)
    df["macd"], df["macd_signal"], df["macd_hist"] = calculate_macd(df["close"])
    df["adx"] = calculate_adx(df)
    return df


def resample_candles(df, rule):
    work = df.copy()

    if "time" not in work.columns:
        return None

    work = work[["time", "open", "high", "low", "close"]].copy()
    work["time"] = pd.to_datetime(work["time"], errors="coerce")
    work.dropna(subset=["time"], inplace=True)

    if len(work) < 5:
        return None

    work.set_index("time", inplace=True)

    resampled = work.resample(rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
    })

    resampled.dropna(inplace=True)
    resampled.reset_index(inplace=True)

    if len(resampled) < 5:
        return None

    resampled["X"] = range(len(resampled))

    return add_indicators(resampled)


def extract_price(text):
    return safe_float(text, None)


def add_fib_prices_to_range(prices_for_range, fib):
    if not fib:
        return

    for value in fib.values():
        p = safe_float(value, None)
        if p is not None:
            prices_for_range.append(p)


def draw_score_box(ax, buy_score=0, sell_score=0, adopted_side="WAIT"):
    try:
        buy_score = int(float(buy_score))
    except Exception:
        buy_score = 0

    try:
        sell_score = int(float(sell_score))
    except Exception:
        sell_score = 0

    adopted_side = clean_text(adopted_side)

    if adopted_side == "":
        adopted_side = "WAIT"

    if adopted_side == "BUY":
        side_color = GREEN
    elif adopted_side == "SELL":
        side_color = RED
    else:
        side_color = YELLOW

    ax.text(
        0.08,
        0.28,
        "BUY SCORE",
        transform=ax.transAxes,
        color=SUBTEXT,
        fontsize=9,
        ha="left",
        va="center",
        weight="bold",
    )

    ax.text(
        0.92,
        0.28,
        f"{buy_score}",
        transform=ax.transAxes,
        color=GREEN,
        fontsize=15,
        ha="right",
        va="center",
        weight="bold",
    )

    ax.text(
        0.08,
        0.20,
        "SELL SCORE",
        transform=ax.transAxes,
        color=SUBTEXT,
        fontsize=9,
        ha="left",
        va="center",
        weight="bold",
    )

    ax.text(
        0.92,
        0.20,
        f"{sell_score}",
        transform=ax.transAxes,
        color=RED,
        fontsize=15,
        ha="right",
        va="center",
        weight="bold",
    )

    ax.text(
        0.08,
        0.12,
        "採用方向",
        transform=ax.transAxes,
        color=SUBTEXT,
        fontsize=9,
        ha="left",
        va="center",
        weight="bold",
    )

    ax.text(
        0.92,
        0.12,
        adopted_side,
        transform=ax.transAxes,
        color=side_color,
        fontsize=15,
        ha="right",
        va="center",
        weight="bold",
    )


def draw_tf_chart(ax, df, title, fib=None, buy_fib=None, sell_fib=None):
    if df is None or len(df) < 5:
        ax.set_facecolor(PANEL)
        ax.text(
            0.5,
            0.5,
            f"{title}\nデータ不足",
            transform=ax.transAxes,
            color=SUBTEXT,
            fontsize=11,
            ha="center",
            va="center",
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return

    style_axis(ax)
    draw_candles(ax, df)

    if "ema20" in df.columns:
        ax.plot(df["X"], df["ema20"], color=BLUE, linewidth=1.0, label="EMA20")

    if "ema75" in df.columns:
        ax.plot(df["X"], df["ema75"], color=ORANGE, linewidth=1.0, label="EMA75")

    x_min = df["X"].min()
    x_max = df["X"].max()

    prices_for_range = [
        df["low"].min(),
        df["high"].max(),
    ]

    add_fib_prices_to_range(prices_for_range, fib)
    add_fib_prices_to_range(prices_for_range, buy_fib)
    add_fib_prices_to_range(prices_for_range, sell_fib)

    prices_for_range = [p for p in prices_for_range if p is not None]

    price_min = min(prices_for_range)
    price_max = max(prices_for_range)
    margin = (price_max - price_min) * 0.14

    if margin <= 0:
        margin = 0.1

    y_min = price_min - margin
    y_max = price_max + margin

    ax.set_xlim(x_min - 1, x_max + 7)
    ax.set_ylim(y_min, y_max)

    draw_fibonacci(
        ax,
        df,
        fib=fib,
        y_min=y_min,
        y_max=y_max,
        compact=True,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
    )

    ax.text(
        0.01,
        0.96,
        title,
        transform=ax.transAxes,
        color=TEXT,
        fontsize=11,
        weight="bold",
        ha="left",
        va="top",
        bbox=dict(facecolor=PANEL, edgecolor=BORDER, alpha=0.85),
    )

    ax.tick_params(axis="x", labelsize=7, colors=SUBTEXT)
    ax.tick_params(axis="y", labelsize=7, colors=SUBTEXT)

    positions, labels = make_time_labels(df)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, color=SUBTEXT, fontsize=7)


def create_pro_chart_image(
    candles,
    candles_4h=None,
    candles_1d=None,
    fib=None,
    buy_fib=None,
    sell_fib=None,
    current_price=None,
    signal=None,
    ai_score=0,
    score=None,
    buy_score=0,
    sell_score=0,
    adopted_side="WAIT",
    win_rate_text="-",
    rsi14=None,
    dow_text=None,
    mtf_text=None,
    entry_text=None,
    stop_text=None,
    tp1_text=None,
    tp2_text=None,
    rr_text=None,
    reason_text=None,
    filename="chart_pro.png",
):
    df = normalize_candles(candles, limit=80)

    if df is None:
        print("チャート作成失敗: 1Hローソク足データ不足")
        return None

    df = add_indicators(df)

    df_4h = normalize_candles(candles_4h, limit=80)
    if df_4h is not None:
        df_4h = add_indicators(df_4h)
    else:
        df_4h = resample_candles(df, "4h")

    df_1d = normalize_candles(candles_1d, limit=80)
    if df_1d is not None:
        df_1d = add_indicators(df_1d)
    else:
        df_1d = resample_candles(df, "1D")

    if current_price is None:
        current_price = float(df["close"].iloc[-1])
    else:
        current_price = safe_float(current_price, float(df["close"].iloc[-1]))

    entry_price = extract_price(entry_text)
    stop_price = extract_price(stop_text)
    tp1_price = extract_price(tp1_text)
    tp2_price = extract_price(tp2_text)

    if score is not None:
        ai_score = score

    fig = plt.figure(figsize=(18.8, 11.2), dpi=130)
    fig.patch.set_facecolor(BG)

    gs = GridSpec(
        6,
        4,
        figure=fig,
        height_ratios=[0.48, 3.30, 1.45, 0.85, 0.75, 0.70],
        width_ratios=[3.0, 3.0, 3.0, 2.45],
        hspace=0.10,
        wspace=0.14,
    )

    ax_title = fig.add_subplot(gs[0, :3])
    ax_gauge = fig.add_subplot(gs[0, 3])

    ax_chart = fig.add_subplot(gs[1, :3])
    ax_panel = fig.add_subplot(gs[1:4, 3])

    ax_4h = fig.add_subplot(gs[2, :1])
    ax_1d = fig.add_subplot(gs[2, 1:3])

    ax_macd = fig.add_subplot(gs[3, :3], sharex=ax_chart)
    ax_adx = fig.add_subplot(gs[4, :3], sharex=ax_chart)

    ax_info = fig.add_subplot(gs[5, :])

    for ax in [ax_chart, ax_macd, ax_adx]:
        style_axis(ax)

    ax_title.axis("off")
    ax_title.text(
        0,
        0.64,
        f"{settings.APP_NAME} {settings.VERSION}  {settings.SYMBOL_NAME}",
        fontsize=18,
        color=TEXT,
        weight="bold",
        ha="left",
        va="center",
    )

    ax_title.text(
        0,
        0.20,
        f"現在価格: {format_price(current_price)}    Market: {settings.SYMBOL}    TF: 1H / 4H / 1D",
        fontsize=10,
        color=SUBTEXT,
        ha="left",
        va="center",
    )

    draw_ai_score_gauge(ax_gauge, ai_score)

    draw_candles(ax_chart, df)

    ax_chart.plot(
        df["X"],
        df["ema20"],
        color=BLUE,
        linewidth=1.5,
        label="EMA20",
        zorder=5,
    )

    ax_chart.plot(
        df["X"],
        df["ema75"],
        color=ORANGE,
        linewidth=1.5,
        label="EMA75",
        zorder=5,
    )

    x_min = df["X"].min()
    x_max = df["X"].max()

    prices_for_range = [
        df["low"].min(),
        df["high"].max(),
        current_price,
        entry_price,
        stop_price,
        tp1_price,
        tp2_price,
    ]

    add_fib_prices_to_range(prices_for_range, fib)
    add_fib_prices_to_range(prices_for_range, buy_fib)
    add_fib_prices_to_range(prices_for_range, sell_fib)

    prices_for_range = [p for p in prices_for_range if p is not None]

    price_min = min(prices_for_range)
    price_max = max(prices_for_range)
    margin = (price_max - price_min) * 0.18

    if margin <= 0:
        margin = 0.1

    y_min = price_min - margin
    y_max = price_max + margin

    ax_chart.set_ylim(y_min, y_max)
    ax_chart.set_xlim(x_min - 1, x_max + 22)

    draw_fibonacci(
        ax_chart,
        df,
        fib=fib,
        y_min=y_min,
        y_max=y_max,
        compact=False,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
    )

    show_trade = signal is not None and (
        "BUY" in str(signal).upper()
        or "SELL" in str(signal).upper()
        or "買" in str(signal)
        or "売" in str(signal)
    )

    trade_items = [
        {
            "price": current_price,
            "label": "NOW",
            "color": "#90CAF9",
            "linestyle": "-",
            "linewidth": 1.5,
            "alpha": 0.95,
        },
        {
            "price": entry_price,
            "label": "ENTRY",
            "color": GREEN,
            "linestyle": "-",
            "linewidth": 1.6,
            "alpha": 0.98,
        },
        {
            "price": stop_price,
            "label": "SL",
            "color": RED,
            "linestyle": "-",
            "linewidth": 1.6,
            "alpha": 0.98,
        },
        {
            "price": tp1_price,
            "label": "TP1",
            "color": PURPLE,
            "linestyle": "--",
            "linewidth": 1.4,
            "alpha": 0.95,
        },
        {
            "price": tp2_price,
            "label": "TP2",
            "color": "#7E57C2",
            "linestyle": "--",
            "linewidth": 1.4,
            "alpha": 0.95,
        },
    ]

    if show_trade:
        draw_trade_lines(
            ax_chart,
            x_min,
            x_max,
            trade_items[1:],
            y_min,
            y_max,
        )

    ax_chart.text(
        0.01,
        0.96,
        "1H Main Chart / Latest 80 Candles / BUY & SELL Fibo",
        transform=ax_chart.transAxes,
        color=TEXT,
        fontsize=11,
        weight="bold",
        ha="left",
        va="top",
        bbox=dict(facecolor=PANEL, edgecolor=BORDER, alpha=0.85),
    )

    ax_chart.set_ylabel("Price", color=SUBTEXT)

    ax_chart.legend(
        loc="upper left",
        fontsize=8,
        facecolor=PANEL,
        edgecolor=BORDER,
        labelcolor=TEXT,
    )

    draw_tf_chart(
        ax_4h,
        df_4h,
        "4H Trend",
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
    )

    draw_tf_chart(
        ax_1d,
        df_1d,
        "1D Direction",
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
    )

    draw_tf_trade_lines(ax_4h, df_4h, trade_items)
    draw_tf_trade_lines(ax_1d, df_1d, trade_items)

    draw_signal_panel(
    ax_panel,
    signal=signal,
    win_rate_text=win_rate_text,
    rr_text=rr_text,
    reason_text=reason_text,
    buy_score=buy_score,
    sell_score=sell_score,
    adopted_side=adopted_side,
)

    draw_score_box(
        ax_panel,
        buy_score=buy_score,
        sell_score=sell_score,
        adopted_side=adopted_side,
    )

    hist_colors = [GREEN if v >= 0 else RED for v in df["macd_hist"]]

    ax_macd.bar(
        df["X"],
        df["macd_hist"],
        color=hist_colors,
        width=0.70,
        alpha=0.8,
    )

    ax_macd.plot(df["X"], df["macd"], color=BLUE, linewidth=1.2, label="MACD")
    ax_macd.plot(df["X"], df["macd_signal"], color=ORANGE, linewidth=1.1, label="Signal")
    ax_macd.axhline(0, color=SUBTEXT, linewidth=0.8, alpha=0.6)
    ax_macd.set_ylabel("MACD", color=SUBTEXT)

    ax_macd.legend(
        loc="upper left",
        fontsize=8,
        facecolor=PANEL,
        edgecolor=BORDER,
        labelcolor=TEXT,
    )

    ax_adx.plot(df["X"], df["adx"], color="#CE93D8", linewidth=1.4, label="ADX")
    ax_adx.axhline(20, color=YELLOW, linestyle="--", linewidth=0.9, alpha=0.7)
    ax_adx.axhline(25, color=RED, linestyle="--", linewidth=0.9, alpha=0.7)
    ax_adx.set_ylabel("ADX", color=SUBTEXT)

    try:
        adx_max = df["adx"].dropna().max()
        if pd.isna(adx_max):
            adx_max = 40
    except Exception:
        adx_max = 40

    ax_adx.set_ylim(0, max(40, adx_max + 5))

    ax_adx.legend(
        loc="upper left",
        fontsize=8,
        facecolor=PANEL,
        edgecolor=BORDER,
        labelcolor=TEXT,
    )

    positions, labels = make_time_labels(df)

    ax_adx.set_xticks(positions)
    ax_adx.set_xticklabels(labels, color=SUBTEXT)

    plt.setp(ax_chart.get_xticklabels(), visible=False)
    plt.setp(ax_macd.get_xticklabels(), visible=False)

    ax_info.axis("off")
    ax_info.set_facecolor(BG)

    parts = [
        f"Market: {settings.SYMBOL_NAME}",
        f"BUY SCORE: {buy_score}",
        f"SELL SCORE: {sell_score}",
        f"採用方向: {adopted_side}",
        clean_text(dow_text),
        clean_text(mtf_text),
        f"RSI14: {clean_text(rsi14)}",
    ]

    if entry_text and "なし" not in str(entry_text):
        parts.append(clean_text(entry_text))

    if stop_text and "なし" not in str(stop_text):
        parts.append(clean_text(stop_text))

    if tp1_text and "なし" not in str(tp1_text):
        parts.append(clean_text(tp1_text))

    if tp2_text and "なし" not in str(tp2_text):
        parts.append(clean_text(tp2_text))

    info_text = "   |   ".join([p for p in parts if p and p != "-"])

    ax_info.text(
        0.01,
        0.5,
        info_text,
        transform=ax_info.transAxes,
        color=SUBTEXT,
        fontsize=10,
        ha="left",
        va="center",
    )

    try:
        fig.savefig(
            filename,
            facecolor=fig.get_facecolor(),
            bbox_inches="tight",
            pad_inches=0.15,
        )

        plt.close(fig)

        print(f"{settings.APP_NAME} {settings.VERSION} Ver16.0 Mainチャート作成成功:", filename)

        return filename

    except Exception as e:
        plt.close(fig)
        print("チャート作成失敗:", e)
        return None


def create_chart_image(*args, **kwargs):
    return create_pro_chart_image(*args, **kwargs)