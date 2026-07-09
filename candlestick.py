# candlestick.py

def judge_candlestick(prices):

    if not prices or len(prices) < 5:
        return False, "データ不足"

    o = prices[-4]
    h = max(prices[-4:])
    l = min(prices[-4:])
    c = prices[-1]

    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l

    if lower > body * 2:
        return True, "ピンバー"

    if upper > body * 2:
        return True, "上ヒゲピンバー"

    if body <= 0.01:
        return True, "十字線"

    if c > o and body >= 0.10:
        return True, "大陽線"

    if c < o and body >= 0.10:
        return True, "大陰線"

    return False, "通常"