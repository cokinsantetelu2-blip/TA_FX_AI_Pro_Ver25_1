# ai_judge_v123.py
# TA FX AI Pro Ver13.2
# AI判定・ランキング強化版

def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def judge_ema_slope(ema_values):
    if not ema_values or len(ema_values) < 8:
        return "データ不足", 0

    values = [safe_float(v) for v in ema_values[-8:]]
    values = [v for v in values if v is not None]

    if len(values) < 8:
        return "データ不足", 0

    short_slope = values[-1] - values[-4]
    long_slope = values[-1] - values[0]

    base_price = abs(values[-1])
    if base_price <= 0:
        base_price = 1

    short_rate = short_slope / base_price
    long_rate = long_slope / base_price

    if short_rate > 0.00045 and long_rate > 0.00090:
        return "強い上向き", 15

    if short_rate < -0.00045 and long_rate < -0.00090:
        return "強い下向き", 15

    if long_rate > 0.00045:
        return "上向き", 10

    if long_rate < -0.00045:
        return "下向き", 10

    return "横ばい", -5


def judge_ema75_slope(ema_values):
    if not ema_values or len(ema_values) < 12:
        return "データ不足", 0

    values = [safe_float(v) for v in ema_values[-12:]]
    values = [v for v in values if v is not None]

    if len(values) < 12:
        return "データ不足", 0

    slope = values[-1] - values[0]

    base_price = abs(values[-1])
    if base_price <= 0:
        base_price = 1

    slope_rate = slope / base_price

    if slope_rate > 0.00055:
        return "EMA75上向き", 12

    if slope_rate < -0.00055:
        return "EMA75下向き", 12

    return "EMA75横ばい", -5


def judge_macd_cross(macd_values, signal_values):
    if not macd_values or not signal_values:
        return "データ不足", 0

    if len(macd_values) < 4 or len(signal_values) < 4:
        return "データ不足", 0

    macd_prev = safe_float(macd_values[-2])
    macd_now = safe_float(macd_values[-1])
    sig_prev = safe_float(signal_values[-2])
    sig_now = safe_float(signal_values[-1])

    if None in [macd_prev, macd_now, sig_prev, sig_now]:
        return "データ不足", 0

    diff_now = macd_now - sig_now
    diff_prev = macd_prev - sig_prev

    if macd_prev <= sig_prev and macd_now > sig_now:
        return "ゴールデンクロス", 15

    if macd_prev >= sig_prev and macd_now < sig_now:
        return "デッドクロス", 15

    if diff_now > diff_prev and macd_now > sig_now:
        return "上昇優勢", 8

    if diff_now < diff_prev and macd_now < sig_now:
        return "下降優勢", 8

    return "クロスなし", 0


def judge_macd_histogram(hist_values):
    if not hist_values or len(hist_values) < 4:
        return "データ不足", 0

    h0 = safe_float(hist_values[-3])
    h1 = safe_float(hist_values[-2])
    h2 = safe_float(hist_values[-1])

    if h0 is None or h1 is None or h2 is None:
        return "データ不足", 0

    if h2 > 0 and abs(h2) > abs(h1) and abs(h1) >= abs(h0):
        return "買い勢い拡大", 10

    if h2 < 0 and abs(h2) > abs(h1) and abs(h1) >= abs(h0):
        return "売り勢い拡大", 10

    if abs(h2) < abs(h1):
        return "勢い減少", -5

    return "変化なし", 0


def judge_adx(adx):
    adx = safe_float(adx)

    if adx is None:
        return "データ不足", 0

    if adx >= 40:
        return "非常に強いトレンド", 18

    if adx >= 30:
        return "強いトレンド", 15

    if adx >= 25:
        return "トレンドあり", 10

    if adx >= 20:
        return "弱いトレンド", 5

    return "レンジ気味", -12


def judge_candle_pattern(candles):
    if not candles or len(candles) < 3:
        return "データ不足", 0

    c1 = candles[-2]
    c2 = candles[-1]

    try:
        o1 = float(c1["open"])
        close1 = float(c1["close"])
        o2 = float(c2["open"])
        h2 = float(c2["high"])
        l2 = float(c2["low"])
        close2 = float(c2["close"])
    except Exception:
        return "データ不足", 0

    body2 = abs(close2 - o2)
    range2 = h2 - l2

    if range2 <= 0:
        return "判定不可", 0

    upper_shadow = h2 - max(o2, close2)
    lower_shadow = min(o2, close2) - l2
    body_rate = body2 / range2

    if close1 < o1 and close2 > o2 and close2 > o1 and o2 < close1:
        return "強気包み足", 15

    if close1 > o1 and close2 < o2 and close2 < o1 and o2 > close1:
        return "弱気包み足", 15

    if lower_shadow > body2 * 2.2 and upper_shadow < body2:
        return "下ヒゲ反発", 10

    if upper_shadow > body2 * 2.2 and lower_shadow < body2:
        return "上ヒゲ反落", 10

    if body_rate >= 0.65 and close2 > o2:
        return "強い陽線", 8

    if body_rate >= 0.65 and close2 < o2:
        return "強い陰線", 8

    if body_rate < 0.2:
        return "迷い足", -10

    return "特になし", 0


def get_direction(text):
    if text in [
        "強い上向き",
        "上向き",
        "EMA75上向き",
        "ゴールデンクロス",
        "上昇優勢",
        "買い勢い拡大",
        "強気包み足",
        "下ヒゲ反発",
        "強い陽線",
    ]:
        return "BUY"

    if text in [
        "強い下向き",
        "下向き",
        "EMA75下向き",
        "デッドクロス",
        "下降優勢",
        "売り勢い拡大",
        "弱気包み足",
        "上ヒゲ反落",
        "強い陰線",
    ]:
        return "SELL"

    return "NEUTRAL"


def calculate_direction_bonus(
    ema_slope_text,
    ema75_slope_text,
    macd_cross_text,
    macd_hist_text,
    candle_text,
):
    directions = [
        get_direction(ema_slope_text),
        get_direction(ema75_slope_text),
        get_direction(macd_cross_text),
        get_direction(macd_hist_text),
        get_direction(candle_text),
    ]

    buy_count = directions.count("BUY")
    sell_count = directions.count("SELL")

    if buy_count >= 4 and sell_count == 0:
        return 12

    if sell_count >= 4 and buy_count == 0:
        return 12

    if buy_count >= 3 and sell_count == 0:
        return 7

    if sell_count >= 3 and buy_count == 0:
        return 7

    if buy_count >= 2 and sell_count >= 2:
        return -15

    if buy_count >= 1 and sell_count >= 2:
        return -8

    if sell_count >= 1 and buy_count >= 2:
        return -8

    return 0


def calculate_trend_quality_bonus(
    ema_slope_text,
    ema75_slope_text,
    macd_hist_text,
    adx_text,
):
    score = 0

    strong_adx = adx_text in [
        "非常に強いトレンド",
        "強いトレンド",
        "トレンドあり",
    ]

    buy_trend = (
        ema_slope_text in ["強い上向き", "上向き"]
        and ema75_slope_text == "EMA75上向き"
        and macd_hist_text == "買い勢い拡大"
    )

    sell_trend = (
        ema_slope_text in ["強い下向き", "下向き"]
        and ema75_slope_text == "EMA75下向き"
        and macd_hist_text == "売り勢い拡大"
    )

    if buy_trend and strong_adx:
        score += 12

    if sell_trend and strong_adx:
        score += 12

    if adx_text == "レンジ気味":
        score -= 10

    if adx_text == "弱いトレンド":
        score -= 3

    return score


def calculate_conflict_penalty(
    ema_slope_text,
    ema75_slope_text,
    macd_cross_text,
    macd_hist_text,
):
    score = 0

    if (
        ema_slope_text in ["強い上向き", "上向き"]
        and ema75_slope_text == "EMA75下向き"
    ):
        score -= 14

    if (
        ema_slope_text in ["強い下向き", "下向き"]
        and ema75_slope_text == "EMA75上向き"
    ):
        score -= 14

    if (
        ema_slope_text in ["強い上向き", "上向き"]
        and macd_hist_text == "売り勢い拡大"
    ):
        score -= 10

    if (
        ema_slope_text in ["強い下向き", "下向き"]
        and macd_hist_text == "買い勢い拡大"
    ):
        score -= 10

    if (
        macd_cross_text == "ゴールデンクロス"
        and macd_hist_text == "売り勢い拡大"
    ):
        score -= 8

    if (
        macd_cross_text == "デッドクロス"
        and macd_hist_text == "買い勢い拡大"
    ):
        score -= 8

    return score


def calculate_ai_score_v123(
    base_score=0,
    ema_slope_text=None,
    ema75_slope_text=None,
    macd_cross_text=None,
    macd_hist_text=None,
    adx_text=None,
    candle_text=None,
):
    score = safe_float(base_score)

    if score is None:
        score = 0

    score = int(score)

    add_map = {
        "強い上向き": 15,
        "強い下向き": 15,
        "上向き": 10,
        "下向き": 10,
        "横ばい": -6,

        "EMA75上向き": 12,
        "EMA75下向き": 12,
        "EMA75横ばい": -6,

        "ゴールデンクロス": 15,
        "デッドクロス": 15,
        "上昇優勢": 8,
        "下降優勢": 8,
        "クロスなし": -2,

        "買い勢い拡大": 10,
        "売り勢い拡大": 10,
        "勢い減少": -7,
        "変化なし": -2,

        "非常に強いトレンド": 18,
        "強いトレンド": 15,
        "トレンドあり": 10,
        "弱いトレンド": 3,
        "レンジ気味": -12,

        "強気包み足": 15,
        "弱気包み足": 15,
        "下ヒゲ反発": 10,
        "上ヒゲ反落": 10,
        "強い陽線": 8,
        "強い陰線": 8,
        "迷い足": -10,
    }

    for text in [
        ema_slope_text,
        ema75_slope_text,
        macd_cross_text,
        macd_hist_text,
        adx_text,
        candle_text,
    ]:
        score += add_map.get(text, 0)

    score += calculate_direction_bonus(
        ema_slope_text,
        ema75_slope_text,
        macd_cross_text,
        macd_hist_text,
        candle_text,
    )

    score += calculate_trend_quality_bonus(
        ema_slope_text,
        ema75_slope_text,
        macd_hist_text,
        adx_text,
    )

    score += calculate_conflict_penalty(
        ema_slope_text,
        ema75_slope_text,
        macd_cross_text,
        macd_hist_text,
    )

    if score < 0:
        score = 0

    if score > 100:
        score = 100

    return score