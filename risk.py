# risk.py
# TA FX AI Pro Ver21
# ATR平均比較AI 対応 TP/SL AI


def get_trade_width(symbol):
    symbol = str(symbol).upper()

    # USDJPY系
    if "JPY" in symbol:
        return {
            "sl": 0.200,
            "tp1": 0.300,
            "tp2": 0.600,
            "digits": 3
        }

    # XAUUSD / GOLD
    if "XAU" in symbol or "GOLD" in symbol:
        return {
            "sl": 20.0,
            "tp1": 30.0,
            "tp2": 60.0,
            "digits": 2
        }

    # BTC / ETH
    if "BTC" in symbol or "ETH" in symbol:
        return {
            "sl": 500.0,
            "tp1": 750.0,
            "tp2": 1500.0,
            "digits": 2
        }

    # XRP
    if "XRP" in symbol:
        return {
            "sl": 0.020,
            "tp1": 0.030,
            "tp2": 0.060,
            "digits": 3
        }

    # EURUSD / GBPUSD / AUDUSD / USDCHF
    return {
        "sl": 0.0020,
        "tp1": 0.0030,
        "tp2": 0.0060,
        "digits": 5
    }


def get_atr_multiplier(atr, atr_average=None):
    """
    Ver21 ATR平均比較AI

    固定閾値は使わない。
    現在ATR ÷ 30日平均ATR で判定する。

    低ボラ   : 0.80未満 → 0.75倍
    通常ボラ : 0.80〜1.20 → 1.00倍
    高ボラ   : 1.20超 → 1.50倍
    """

    if atr is None or atr_average is None:
        return 1.00

    try:
        atr = float(atr)
        atr_average = float(atr_average)
    except Exception:
        return 1.00

    if atr <= 0 or atr_average <= 0:
        return 1.00

    ratio = atr / atr_average

    if ratio < 0.80:
        return 0.75

    if ratio > 1.20:
        return 1.50

    return 1.00


def get_atr_volatility_label(atr, atr_average=None):
    if atr is None or atr_average is None:
        return "通常ボラ"

    try:
        atr = float(atr)
        atr_average = float(atr_average)
    except Exception:
        return "通常ボラ"

    if atr <= 0 or atr_average <= 0:
        return "通常ボラ"

    ratio = atr / atr_average

    if ratio < 0.80:
        return "低ボラ"

    if ratio > 1.20:
        return "高ボラ"

    return "通常ボラ"


def get_atr_ratio(atr, atr_average=None):
    if atr is None or atr_average is None:
        return None

    try:
        atr = float(atr)
        atr_average = float(atr_average)
    except Exception:
        return None

    if atr <= 0 or atr_average <= 0:
        return None

    return round(atr / atr_average, 2)


def calculate_trade_plan(
    current_price,
    signal,
    symbol="USDJPY",
    atr=None,
    atr_average=None,
):

    width = get_trade_width(symbol)

    multiplier = get_atr_multiplier(atr, atr_average)
    volatility_label = get_atr_volatility_label(atr, atr_average)
    atr_ratio = get_atr_ratio(atr, atr_average)

    print(
        f"ATR={atr}  "
        f"30日平均ATR={atr_average}  "
        f"ATR比率={atr_ratio}  "
        f"ボラ={volatility_label}  "
        f"倍率={multiplier}  "
        f"Symbol={symbol}"
    )

    sl_width = width["sl"] * multiplier
    tp1_width = width["tp1"] * multiplier
    tp2_width = width["tp2"] * multiplier

    digits = width["digits"]

    entry = round(current_price, digits)

    if "売り" in signal or "SELL" in signal:
        direction = "sell"

    elif "買い" in signal or "BUY" in signal or "エントリーOK" in signal:
        direction = "buy"

    else:
        direction = "wait"

    if direction == "wait":
        return {
            "direction": "wait",
            "entry": "見送り",
            "stop": "なし",
            "tp1": "なし",
            "tp2": "なし",
            "rr1": "なし",
            "rr2": "なし",
            "atr": atr,
            "atr_average": atr_average,
            "atr_ratio": atr_ratio,
            "volatility": volatility_label,
            "atr_multiplier": multiplier,
        }

    if direction == "buy":
        stop = round(entry - sl_width, digits)
        tp1 = round(entry + tp1_width, digits)
        tp2 = round(entry + tp2_width, digits)

    else:
        stop = round(entry + sl_width, digits)
        tp1 = round(entry - tp1_width, digits)
        tp2 = round(entry - tp2_width, digits)

    rr1 = round(abs(tp1 - entry) / abs(entry - stop), 2)
    rr2 = round(abs(tp2 - entry) / abs(entry - stop), 2)

    return {
        "direction": direction,
        "entry": entry,
        "stop": stop,
        "tp1": tp1,
        "tp2": tp2,
        "rr1": rr1,
        "rr2": rr2,
        "atr": atr,
        "atr_average": atr_average,
        "atr_ratio": atr_ratio,
        "volatility": volatility_label,
        "atr_multiplier": multiplier,
    }