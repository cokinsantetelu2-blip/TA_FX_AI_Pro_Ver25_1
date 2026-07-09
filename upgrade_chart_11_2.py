from pathlib import Path
import re
import shutil

path = Path("chart_pro.py")
text = path.read_text(encoding="utf-8")

shutil.copy(path, "chart_pro_backup_Ver11_1.py")

new_draw_fibonacci = r'''
def draw_fibonacci(ax, df, fib):
    if not fib:
        return

    x_min = df["X"].min()
    x_max = df["X"].max()

    ax.set_xlim(x_min - 1, x_max + 13)

    colors = {
        "0": "#888888",
        "0.236": "#607D8B",
        "0.382": BLUE,
        "0.5": PURPLE,
        "0.618": ORANGE,
        "0.786": "#FF7043",
        "1": "#888888",
    }

    labels = []

    for key, value in fib.items():
        price = safe_float(value, None)
        if price is None:
            continue

        key_text = str(key)
        color = colors.get(key_text, "#78909C")

        ax.hlines(
            price,
            x_min,
            x_max,
            colors=color,
            linestyles="--",
            linewidth=0.8,
            alpha=0.45,
            zorder=2,
        )

        labels.append({
            "price": price,
            "text": f"Fib {key_text}\n{price:.3f}",
            "color": color,
        })

    if not labels:
        return

    y_min, y_max = ax.get_ylim()
    y_range = max(y_max - y_min, 0.001)
    min_gap = y_range * 0.055

    labels = sorted(labels, key=lambda x: x["price"])

    last_y = None
    for item in labels:
        y = item["price"]
        if last_y is not None and y - last_y < min_gap:
            y = last_y + min_gap
        item["label_y"] = y
        last_y = y

    overflow = labels[-1]["label_y"] - y_max
    if overflow > 0:
        for item in labels:
            item["label_y"] -= overflow

    label_x = x_max + 1.3

    for item in labels:
        ax.text(
            label_x,
            item["label_y"],
            item["text"],
            va="center",
            ha="left",
            fontsize=7.5,
            color=TEXT,
            linespacing=0.9,
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor=item["color"],
                edgecolor=item["color"],
                alpha=0.50,
            ),
            zorder=10,
        )
'''

new_draw_price_line = r'''
def draw_price_line(ax, x_min, x_max, price, label, color, linestyle="-"):
    if price is None:
        return

    ax.hlines(
        price,
        x_min,
        x_max,
        colors=color,
        linestyles=linestyle,
        linewidth=1.45,
        alpha=0.95,
        zorder=6,
    )

    label_x = x_max + 6.2

    ax.text(
        label_x,
        price,
        f"{label}\n{price:.3f}",
        va="center",
        ha="left",
        fontsize=8.8,
        color=TEXT,
        weight="bold",
        linespacing=0.9,
        bbox=dict(
            boxstyle="round,pad=0.28",
            facecolor=color,
            edgecolor=color,
            alpha=0.96,
        ),
        zorder=20,
    )
'''

text = re.sub(
    r"\ndef draw_fibonacci\(ax, df, fib\):.*?\ndef draw_price_line",
    "\n" + new_draw_fibonacci + "\ndef draw_price_line",
    text,
    flags=re.S,
)

text = re.sub(
    r"\ndef draw_price_line\(ax, x_min, x_max, price, label, color, linestyle=\"-\"\):.*?\ndef draw_ai_score_gauge",
    "\n" + new_draw_price_line + "\ndef draw_ai_score_gauge",
    text,
    flags=re.S,
)

text = text.replace(
    '        "USDJPY Fibo AI  Ver11 Pro Chart",',
    '        "USDJPY Fibo AI  Ver11.2 Pro Chart",'
)

text = text.replace(
    '        print("Ver11 Proチャート作成成功:", filename)',
    '        print("Ver11.2 Proチャート作成成功:", filename)'
)

path.write_text(text, encoding="utf-8")

print("Ver11.2への自動修正完了")
print("バックアップ作成:", "chart_pro_backup_Ver11_1.py")
print("次に main.py を実行してください")