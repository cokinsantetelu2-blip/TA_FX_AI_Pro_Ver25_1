# dow.py
# USDJPY_Fibo_AI Ver12.3
# ダウ理論 強化版


def _find_swings(prices, window=3):
    swings = []

    if not prices or len(prices) < window * 2 + 5:
        return swings

    for i in range(window, len(prices) - window):
        price = prices[i]

        left = prices[i - window:i]
        right = prices[i + 1:i + window + 1]

        if price > max(left) and price > max(right):
            swings.append({
                "type": "HIGH",
                "index": i,
                "price": price,
            })

        if price < min(left) and price < min(right):
            swings.append({
                "type": "LOW",
                "index": i,
                "price": price,
            })

    return swings


def judge_dow(prices):
    if not prices or len(prices) < 30:
        return "データ不足"

    swings = _find_swings(prices, window=3)

    highs = [s for s in swings if s["type"] == "HIGH"]
    lows = [s for s in swings if s["type"] == "LOW"]

    if len(highs) < 2 or len(lows) < 2:
        high1 = max(prices[-10:])
        high2 = max(prices[-20:-10])
        low1 = min(prices[-10:])
        low2 = min(prices[-20:-10])

        if high1 > high2 and low1 > low2:
            return "上昇"
        elif high1 < high2 and low1 < low2:
            return "下降"
        else:
            return "レンジ"

    last_high = highs[-1]["price"]
    prev_high = highs[-2]["price"]

    last_low = lows[-1]["price"]
    prev_low = lows[-2]["price"]

    if last_high > prev_high and last_low > prev_low:
        return "上昇"

    if last_high < prev_high and last_low < prev_low:
        return "下降"

    return "レンジ"