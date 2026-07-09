# indicator.py
# TA FX AI Pro Ver17.0
# EMA / RSI / RSI反転判定 対応版

def calculate_ema(prices, period):
    if not prices or len(prices) < period:
        return None

    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period

    for price in prices[period:]:
        ema = price * k + ema * (1 - k)

    return round(ema, 3)


def calculate_rsi(prices, period=14):
    if not prices or len(prices) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)


def calculate_rsi_series(prices, period=14):
    if not prices or len(prices) <= period + 3:
        return []

    rsi_list = []

    for i in range(period + 1, len(prices) + 1):
        rsi = calculate_rsi(prices[:i], period)
        if rsi is not None:
            rsi_list.append(rsi)

    return rsi_list


def judge_rsi_reversal(prices, period=14):
    rsi_series = calculate_rsi_series(prices, period)

    if len(rsi_series) < 4:
        return {
            "rsi": calculate_rsi(prices, period),
            "direction": "データ不足",
            "buy_reversal": False,
            "sell_reversal": False,
            "text": "RSI反転判定: データ不足",
        }

    rsi_now = rsi_series[-1]
    rsi_prev = rsi_series[-2]
    rsi_prev2 = rsi_series[-3]

    buy_reversal = False
    sell_reversal = False

    if rsi_prev2 >= rsi_prev and rsi_now > rsi_prev and rsi_prev <= 45:
        buy_reversal = True

    if rsi_prev2 <= rsi_prev and rsi_now < rsi_prev and rsi_prev >= 55:
        sell_reversal = True

    if buy_reversal:
        direction = "BUY反転"
        text = f"RSI反転判定: BUY反転 / RSI {rsi_now}"
    elif sell_reversal:
        direction = "SELL反転"
        text = f"RSI反転判定: SELL反転 / RSI {rsi_now}"
    elif rsi_now > rsi_prev:
        direction = "上向き"
        text = f"RSI反転判定: 上向き / RSI {rsi_now}"
    elif rsi_now < rsi_prev:
        direction = "下向き"
        text = f"RSI反転判定: 下向き / RSI {rsi_now}"
    else:
        direction = "横ばい"
        text = f"RSI反転判定: 横ばい / RSI {rsi_now}"

    return {
        "rsi": rsi_now,
        "previous_rsi": rsi_prev,
        "direction": direction,
        "buy_reversal": buy_reversal,
        "sell_reversal": sell_reversal,
        "text": text,
    }


def get_indicators(prices):
    rsi_reversal = judge_rsi_reversal(prices, 14)

    return {
        "ema20": calculate_ema(prices, 20),
        "ema75": calculate_ema(prices, 75),
        "rsi14": calculate_rsi(prices, 14),
        "rsi_reversal": rsi_reversal,
        "rsi_reversal_text": rsi_reversal.get("text"),
        "rsi_buy_reversal": rsi_reversal.get("buy_reversal"),
        "rsi_sell_reversal": rsi_reversal.get("sell_reversal"),
    }