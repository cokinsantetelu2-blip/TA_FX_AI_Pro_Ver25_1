# chart_pro.py
# USDJPY_Fibo_AI Ver11.1 完成版
# TradingView風 Telegram画像チャート
# 改善点:
# ・フィボナッチを右側ラベル表示
# ・Entry / SL / TP ラベルを右側に見やすく表示
# ・ラベル重なりを軽減
# ・Telegramで一目判断しやすい横長レイアウト

import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.gridspec import GridSpec

warnings.filterwarnings("ignore")


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


BG = "#0B0E11"
PANEL = "#151A22"
GRID = "#1E2630"
BORDER = "#2A2E39"
TEXT = "#FFFFFF"
SUBTEXT = "#B0BEC5"

GREEN = "#26A69A"
RED = "#EF5350"
BLUE = "#42A5F5"
ORANGE = "#FFA726"
YELLOW = "#FFCA28"
PURPLE = "#AB47BC"

FIB_GRAY = "#8A949E"


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


def normalize_candles(candles):
    if candles is None or len(candles) < 20:
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

    if len(df) < 20:
        return None

    # 土日・休場時間の空白を消すため、X軸は日時ではなく連番
    df["X"] = range(len(df))

    return df


def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def calculate_macd(close):
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    return macd, signal, hist


def calculate_adx(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]

    up_move = high.diff()
    down_move = low.diff() * -1

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    plus_di = 100 * pd.Series(plus_dm).rolling(period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(period).mean() / atr

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()

    return adx.fillna(0)


def extract_price(text):
    return safe_float(text, None)


def get_signal_style(signal):
    s = str(signal).upper()

    if "BUY" in s or "買" in s:
        return "BUY", GREEN

    if "SELL" in s or "売" in s:
        return "SELL", RED

    return "WAIT", YELLOW


def style_axis(ax):
    ax.set_facecolor(BG)
    ax.grid(True, color=GRID, linewidth=0.7, alpha=0.85)
    ax.tick_params(colors=SUBTEXT, labelsize=9)

    for spine in ax.spines.values():
        spine.set_color(BORDER)


def draw_candles(ax, df):
    width = 0.62

    for _, row in df.iterrows():
        x = row["X"]
        o = row["open"]
        h = row["high"]
        l = row["low"]
        c = row["close"]

        color = GREEN if c >= o else RED

        ax.vlines(x, l, h, color=color, linewidth=1.1, alpha=0.95)

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
            linewidth=0.8,
            alpha=0.95,
        )

        ax.add_patch(rect)


def adjust_label_positions(prices, y_min, y_max):
    if not prices:
        return []

    data = sorted(prices, key=lambda x: x["price"])
    y_range = max(y_max - y_min, 0.001)
    min_gap = y_range * 0.035

    result = []

    for item in data:
        y = item["price"]

        if result and y - result[-1]["label_y"] < min_gap:
            y = result[-1]["label_y"] + min_gap

        item = item.copy()
        item["label_y"] = y
        result.append(item)

    overflow = result[-1]["label_y"] - y_max

    if overflow > 0:
        for item in result:
            item["label_y"] -= overflow

    for i in range(len(result) - 2, -1, -1):
        if result[i + 1]["label_y"] - result[i]["label_y"] < min_gap:
            result[i]["label_y"] = result[i + 1]["label_y"] - min_gap

    for item in result:
        item["label_y"] = max(y_min, min(y_max, item["label_y"]))

    return result


def draw_right_label(ax, x, price, label_y, text, color, fontsize=8.5):
    ax.text(
        x,
        label_y,
        text,
        va="center",
        ha="left",
        fontsize=fontsize,
        color=TEXT,
        weight="bold",
        bbox=dict(
            boxstyle="round,pad=0.28",
            facecolor=color,
            edgecolor=color,
            alpha=0.96,
        ),
        zorder=20,
    )

    if abs(label_y - price) > 0.001:
        ax.plot(
            [x - 0.35, x - 0.05],
            [price, label_y],
            color=color,
            linewidth=0.8,
            alpha=0.75,
            zorder=19,
        )


def draw_fibonacci(ax, df, fib, y_min, y_max):
    if not fib:
        return

    x_min = df["X"].min()
    x_max = df["X"].max()
    label_x = x_max + 1.2

    colors = {
        "0": "#777777",
        "0.236": "#607D8B",
        "0.382": BLUE,
        "0.5": PURPLE,
        "0.618": ORANGE,
        "0.786": "#FF7043",
        "1": "#777777",
    }

    labels = []

    for key, value in fib.items():
        price = safe_float(value, None)
        if price is None:
            continue

        key_text = str(key)
        color = colors.get(key_text, FIB_GRAY)

        ax.hlines(
            price,
            x_min,
            x_max,
            colors=color,
            linestyles="--",
            linewidth=0.9,
            alpha=0.70,
            zorder=2,
        )

        labels.append(
            {
                "price": price,
                "text": f"Fib {key_text}  {price:.3f}",
                "color": color,
            }
        )

    labels = adjust_label_positions(labels, y_min, y_max)

    for item in labels:
        draw_right_label(
            ax=ax,
            x=label_x,
            price=item["price"],
            label_y=item["label_y"],
            text=item["text"],
            color=item["color"],
            fontsize=8,
        )


def draw_trade_lines(ax, x_min, x_max, items, y_min, y_max):
    clean_items = []

    for item in items:
        price = item["price"]

        if price is None:
            continue

        ax.hlines(
            price,
            x_min,
            x_max,
            colors=item["color"],
            linestyles=item["linestyle"],
            linewidth=item["linewidth"],
            alpha=item["alpha"],
            zorder=5,
        )

        clean_items.append(item)

    labels = adjust_label_positions(clean_items, y_min, y_max)
    label_x = x_max + 5.0

    for item in labels:
        draw_right_label(
            ax=ax,
            x=label_x,
            price=item["price"],
            label_y=item["label_y"],
            text=f"{item['label']} {item['price']:.3f}",
            color=item["color"],
            fontsize=9,
        )


def draw_ai_score_gauge(ax, score):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1)
    ax.axis("off")

    score = safe_float(score, 0)
    score = max(0, min(100, score))

    ax.text(
        0,
        0.88,
        "AI SCORE",
        fontsize=12,
        color=TEXT,
        weight="bold",
        ha="left",
    )

    zones = [
        (0, 40, RED),
        (40, 70, YELLOW),
        (70, 100, GREEN),
    ]

    for start, end, color in zones:
        ax.add_patch(
            Rectangle(
                (start, 0.30),
                end - start,
                0.28,
                facecolor=color,
                edgecolor="none",
                alpha=0.9,
            )
        )

    ax.vlines(score, 0.18, 0.72, color=TEXT, linewidth=2.6)

    ax.text(
        score,
        0.05,
        f"{score:.0f}",
        color=TEXT,
        fontsize=12,
        ha="center",
        weight="bold",
    )


def draw_signal_panel(ax, signal, win_rate_text, rr_text, reason_text):
    ax.axis("off")

    label, color = get_signal_style(signal)

    box = FancyBboxPatch(
        (0.02, 0.05),
        0.96,
        0.90,
        boxstyle="round,pad=0.02,rounding_size=0.025",
        transform=ax.transAxes,
        facecolor=PANEL,
        edgecolor=BORDER,
        linewidth=1.2,
    )

    ax.add_patch(box)

    ax.text(
        0.07,
        0.78,
        label,
        transform=ax.transAxes,
        fontsize=32,
        color=color,
        weight="bold",
        ha="left",
        va="center",
    )

    ax.text(
        0.07,
        0.58,
        f"勝率: {clean_text(win_rate_text)}",
        transform=ax.transAxes,
        fontsize=12,
        color=TEXT,
        ha="left",
        va="center",
    )

    ax.text(
        0.07,
        0.43,
        f"RR: {clean_text(rr_text)}",
        transform=ax.transAxes,
        fontsize=11,
        color=TEXT,
        ha="left",
        va="center",
    )

    ax.text(
        0.07,
        0.22,
        f"理由: {clean_text(reason_text)}",
        transform=ax.transAxes,
        fontsize=9.5,
        color=SUBTEXT,
        ha="left",
        va="center",
        wrap=True,
    )


def make_time_labels(df, count=6):
    length = len(df)

    if length <= count:
        indexes = list(range(length))
    else:
        indexes = np.linspace(0, length - 1, count).astype(int).tolist()

    positions = []
    labels = []

    for i in indexes:
        try:
            t = pd.to_datetime(df.loc[i, "time"])
            positions.append(df.loc[i, "X"])
            labels.append(t.strftime("%m/%d\n%H:%M"))
        except Exception:
            pass

    return positions, labels


def create_pro_chart_image(
    candles,
    fib=None,
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
    rr_text=None,
    reason_text=None,
    filename="chart_pro.png",
):
    df = normalize_candles(candles)

    if df is None:
        print("チャート作成失敗: ローソク足データ不足")
        return None

    df["ema20"] = ema(df["close"], 20)
    df["ema75"] = ema(df["close"], 75)

    df["macd"], df["macd_signal"], df["macd_hist"] = calculate_macd(df["close"])
    df["adx"] = calculate_adx(df)

    if current_price is None:
        current_price = float(df["close"].iloc[-1])
    else:
        current_price = safe_float(current_price, float(df["close"].iloc[-1]))

    entry_price = extract_price(entry_text)
    stop_price = extract_price(stop_text)
    tp1_price = extract_price(tp1_text)
    tp2_price = extract_price(tp2_text)

    fig = plt.figure(figsize=(16, 10), dpi=130)
    fig.patch.set_facecolor(BG)

    gs = GridSpec(
        5,
        4,
        figure=fig,
        height_ratios=[0.55, 3.6, 1.15, 1.05, 0.9],
        width_ratios=[3, 3, 3, 2.4],
        hspace=0.12,
        wspace=0.16,
    )

    ax_title = fig.add_subplot(gs[0, :3])
    ax_gauge = fig.add_subplot(gs[0, 3])
    ax_chart = fig.add_subplot(gs[1, :3])
    ax_panel = fig.add_subplot(gs[1, 3])
    ax_macd = fig.add_subplot(gs[2, :3], sharex=ax_chart)
    ax_adx = fig.add_subplot(gs[3, :3], sharex=ax_chart)
    ax_info = fig.add_subplot(gs[4, :])

    for ax in [ax_chart, ax_macd, ax_adx]:
        style_axis(ax)

    ax_title.axis("off")
    ax_title.text(
        0,
        0.62,
        "USDJPY Fibo AI  Ver11.1 Pro Chart",
        fontsize=18,
        color=TEXT,
        weight="bold",
        ha="left",
        va="center",
    )

    ax_title.text(
        0,
        0.18,
        f"現在価格: {current_price:.3f}    Font: {JP_FONT}",
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
        linewidth=1.4,
        label="EMA20",
        zorder=4,
    )

    ax_chart.plot(
        df["X"],
        df["ema75"],
        color=ORANGE,
        linewidth=1.4,
        label="EMA75",
        zorder=4,
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

    if fib:
        for value in fib.values():
            p = safe_float(value, None)
            if p is not None:
                prices_for_range.append(p)

    prices_for_range = [p for p in prices_for_range if p is not None]

    price_min = min(prices_for_range)
    price_max = max(prices_for_range)
    margin = (price_max - price_min) * 0.16

    if margin <= 0:
        margin = 0.1

    y_min = price_min - margin
    y_max = price_max + margin

    ax_chart.set_ylim(y_min, y_max)

    # 右側ラベル用の余白
    ax_chart.set_xlim(x_min - 1, x_max + 13)

    draw_fibonacci(ax_chart, df, fib, y_min, y_max)

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

    draw_trade_lines(ax_chart, x_min, x_max, trade_items, y_min, y_max)

    ax_chart.set_ylabel("Price", color=SUBTEXT)

    ax_chart.legend(
        loc="upper left",
        fontsize=9,
        facecolor=PANEL,
        edgecolor=BORDER,
        labelcolor=TEXT,
    )

    draw_signal_panel(
        ax_panel,
        signal=signal,
        win_rate_text=win_rate_text,
        rr_text=rr_text,
        reason_text=reason_text,
    )

    hist_colors = [GREEN if v >= 0 else RED for v in df["macd_hist"]]

    ax_macd.bar(
        df["X"],
        df["macd_hist"],
        color=hist_colors,
        width=0.65,
        alpha=0.8,
    )

    ax_macd.plot(
        df["X"],
        df["macd"],
        color=BLUE,
        linewidth=1.2,
        label="MACD",
    )

    ax_macd.plot(
        df["X"],
        df["macd_signal"],
        color=ORANGE,
        linewidth=1.1,
        label="Signal",
    )

    ax_macd.axhline(0, color=SUBTEXT, linewidth=0.8, alpha=0.6)
    ax_macd.set_ylabel("MACD", color=SUBTEXT)

    ax_macd.legend(
        loc="upper left",
        fontsize=8,
        facecolor=PANEL,
        edgecolor=BORDER,
        labelcolor=TEXT,
    )

    ax_adx.plot(
        df["X"],
        df["adx"],
        color="#CE93D8",
        linewidth=1.4,
        label="ADX",
    )

    ax_adx.axhline(20, color=YELLOW, linestyle="--", linewidth=0.9, alpha=0.7)
    ax_adx.axhline(25, color=RED, linestyle="--", linewidth=0.9, alpha=0.7)

    ax_adx.set_ylabel("ADX", color=SUBTEXT)
    ax_adx.set_ylim(0, max(40, df["adx"].max() + 5))

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

    info_text = (
        f"{clean_text(dow_text)}    |    "
        f"{clean_text(mtf_text)}    |    "
        f"RSI14: {clean_text(rsi14)}    |    "
        f"{clean_text(entry_text)} / "
        f"{clean_text(stop_text)} / "
        f"{clean_text(tp1_text)} / "
        f"{clean_text(tp2_text)}"
    )

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

        print("Ver11.1 Proチャート作成成功:", filename)

        return filename

    except Exception as e:
        plt.close(fig)
        print("チャート作成失敗:", e)
        return None


# 古いmain.py対策
def create_chart_image(*args, **kwargs):
    return create_pro_chart_image(*args, **kwargs)