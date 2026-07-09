
# ranking_engine.py
# TA FX AI Pro Ver13.4
# Ranking Score Engine
# ADX・MTF・EMA・MACD・RSI対応版

def safe_int(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def safe_text(value):
    if value is None:
        return ""
    return str(value)


def is_wait_signal(signal):
    text = safe_text(signal).upper()
    raw = safe_text(signal)
    return "WAIT" in text or "見送り" in raw


def is_buy_signal(signal):
    text = safe_text(signal).upper()
    raw = safe_text(signal)
    return "BUY" in text or "買" in raw


def is_sell_signal(signal):
    text = safe_text(signal).upper()
    raw = safe_text(signal)
    return "SELL" in text or "売" in raw


def get_signal_direction(signal):
    if is_buy_signal(signal):
        return "BUY"

    if is_sell_signal(signal):
        return "SELL"

    return "WAIT"


def get_text_direction(text):
    text = safe_text(text)

    buy_words = [
        "強い上向き",
        "上向き",
        "EMA75上向き",
        "ゴールデンクロス",
        "上昇優勢",
        "買い勢い拡大",
        "強気包み足",
        "下ヒゲ反発",
        "強い陽線",
    ]

    sell_words = [
        "強い下向き",
        "下向き",
        "EMA75下向き",
        "デッドクロス",
        "下降優勢",
        "売り勢い拡大",
        "弱気包み足",
        "上ヒゲ反落",
        "強い陰線",
    ]

    if text in buy_words:
        return "BUY"

    if text in sell_words:
        return "SELL"

    return "NEUTRAL"


def get_signal_bonus(signal):
    raw = safe_text(signal)

    if is_wait_signal(signal):
        return -25

    if is_buy_signal(signal) or is_sell_signal(signal):
        return 15

    if "候補" in raw:
        return 8

    return 0


def get_rank_text_bonus(rank_text):
    text = safe_text(rank_text)

    if text == "最強":
        return 12

    if text == "強い":
        return 8

    if text == "候補":
        return 4

    if text == "見送り強め":
        return -5

    if text == "見送り":
        return -12

    if text == "弱い":
        return -8

    return 0


def get_win_rate_bonus(win_rate_number):
    win_rate = safe_int(win_rate_number, 0)

    if win_rate >= 80:
        return 10

    if win_rate >= 75:
        return 8

    if win_rate >= 68:
        return 5

    if win_rate >= 62:
        return 2

    if win_rate <= 50:
        return -8

    return 0


def get_raw_score_bonus(raw_score, score):
    raw = safe_int(raw_score, 0)
    adjusted = safe_int(score, 0)

    if raw > adjusted:
        diff = raw - adjusted

        if diff >= 20:
            return -10

        if diff >= 10:
            return -5

    return 0


def get_adx_bonus(result):
    adx_value = safe_float(result.get("adx_value"), 0)
    adx_text = safe_text(result.get("adx_text"))

    if adx_value >= 40 or adx_text == "非常に強いトレンド":
        return 12

    if adx_value >= 30 or adx_text == "強いトレンド":
        return 9

    if adx_value >= 25 or adx_text == "トレンドあり":
        return 6

    if adx_value >= 20 or adx_text == "弱いトレンド":
        return 2

    if adx_text == "レンジ気味":
        return -12

    return 0


def count_mtf_alignment(mtf):
    if not isinstance(mtf, dict):
        return 0, "NEUTRAL"

    values = [
        safe_text(mtf.get("1H")),
        safe_text(mtf.get("4H")),
        safe_text(mtf.get("1D")),
    ]

    buy_count = 0
    sell_count = 0

    for value in values:
        upper = value.upper()

        if "BUY" in upper or "買" in value or "上昇" in value:
            buy_count += 1

        if "SELL" in upper or "売" in value or "下降" in value:
            sell_count += 1

    if buy_count > sell_count:
        return buy_count, "BUY"

    if sell_count > buy_count:
        return sell_count, "SELL"

    return 0, "NEUTRAL"


def get_mtf_bonus(result):
    mtf_count, mtf_direction = count_mtf_alignment(result.get("mtf"))
    signal_direction = get_signal_direction(result.get("signal"))

    bonus = 0

    if mtf_count >= 3:
        bonus += 10
    elif mtf_count == 2:
        bonus += 5
    elif mtf_count == 1:
        bonus += 1

    if signal_direction in ["BUY", "SELL"] and mtf_direction in ["BUY", "SELL"]:
        if signal_direction == mtf_direction:
            bonus += 6
        else:
            bonus -= 12

    return bonus


def get_ema_bonus(result):
    ema20_text = safe_text(result.get("ema20_text"))
    ema75_text = safe_text(result.get("ema75_text"))

    ema20_direction = get_text_direction(ema20_text)
    ema75_direction = get_text_direction(ema75_text)
    signal_direction = get_signal_direction(result.get("signal"))

    bonus = 0

    if ema20_direction in ["BUY", "SELL"] and ema20_direction == ema75_direction:
        bonus += 7

    if ema20_direction in ["BUY", "SELL"] and ema75_direction in ["BUY", "SELL"]:
        if ema20_direction != ema75_direction:
            bonus -= 12

    if signal_direction in ["BUY", "SELL"] and ema20_direction in ["BUY", "SELL"]:
        if signal_direction == ema20_direction:
            bonus += 4
        else:
            bonus -= 8

    return bonus


def get_macd_bonus(result):
    macd_cross_text = safe_text(result.get("macd_cross_text"))
    macd_hist_text = safe_text(result.get("macd_hist_text"))

    cross_direction = get_text_direction(macd_cross_text)
    hist_direction = get_text_direction(macd_hist_text)
    signal_direction = get_signal_direction(result.get("signal"))

    bonus = 0

    if hist_direction in ["BUY", "SELL"]:
        bonus += 5

    if cross_direction in ["BUY", "SELL"]:
        bonus += 4

    if cross_direction in ["BUY", "SELL"] and hist_direction in ["BUY", "SELL"]:
        if cross_direction == hist_direction:
            bonus += 5
        else:
            bonus -= 10

    if signal_direction in ["BUY", "SELL"] and hist_direction in ["BUY", "SELL"]:
        if signal_direction == hist_direction:
            bonus += 4
        else:
            bonus -= 8

    if macd_hist_text == "勢い減少":
        bonus -= 6

    return bonus


def get_candle_bonus(result):
    candle_text = safe_text(result.get("candle_text"))
    candle_direction = get_text_direction(candle_text)
    signal_direction = get_signal_direction(result.get("signal"))

    if candle_text in ["迷い足", "特になし", "データ不足"]:
        return -3 if candle_text == "迷い足" else 0

    if signal_direction in ["BUY", "SELL"] and candle_direction in ["BUY", "SELL"]:
        if signal_direction == candle_direction:
            return 5
        return -6

    if candle_direction in ["BUY", "SELL"]:
        return 3

    return 0


def get_rsi_bonus(result):
    rsi = safe_float(result.get("rsi14"), 50)
    signal_direction = get_signal_direction(result.get("signal"))

    if rsi >= 75:
        if signal_direction == "BUY":
            return -8
        if signal_direction == "SELL":
            return 4

    if rsi <= 25:
        if signal_direction == "SELL":
            return -8
        if signal_direction == "BUY":
            return 4

    if 45 <= rsi <= 60:
        return 2

    if 35 <= rsi < 45 or 60 < rsi <= 65:
        return 1

    return 0


def get_direction_consistency_bonus(result):
    signal_direction = get_signal_direction(result.get("signal"))

    if signal_direction == "WAIT":
        return 0

    directions = [
        get_text_direction(result.get("ema20_text")),
        get_text_direction(result.get("ema75_text")),
        get_text_direction(result.get("macd_cross_text")),
        get_text_direction(result.get("macd_hist_text")),
        get_text_direction(result.get("candle_text")),
    ]

    same = directions.count(signal_direction)

    opposite = 0
    if signal_direction == "BUY":
        opposite = directions.count("SELL")
    elif signal_direction == "SELL":
        opposite = directions.count("BUY")

    if same >= 4 and opposite == 0:
        return 12

    if same >= 3 and opposite == 0:
        return 8

    if same >= 2 and opposite == 0:
        return 4

    if opposite >= 3:
        return -15

    if opposite >= 2:
        return -10

    return 0


def get_ai_score_bonus(ai_score):
    if ai_score >= 90:
        return 8

    if ai_score >= 80:
        return 5

    if ai_score >= 70:
        return 2

    if ai_score < 50:
        return -8

    return 0


def get_symbol_priority(symbol):
    symbol = safe_text(symbol).upper()

    priority = {
        "USDJPY": 12,
        "EURJPY": 11,
        "GBPJPY": 10,
        "AUDJPY": 9,
        "EURUSD": 8,
        "GBPUSD": 7,
        "AUDUSD": 6,
        "USDCHF": 5,
        "USDCAD": 4,
        "BTC": 3,
        "ETH": 2,
        "XRP": 1,
    }

    return priority.get(symbol, 0)


def calculate_ranking_score(result):
    if not result:
        return 0

    status = safe_text(result.get("status")).upper()

    if status != "OK":
        return -999

    ai_score = safe_int(result.get("score"), 0)
    raw_score = safe_int(result.get("raw_score"), ai_score)
    signal = result.get("signal", "")
    rank_text = result.get("rank_text", "")
    win_rate_number = result.get("win_rate_number", 0)

    ranking_score = ai_score

    ranking_score += get_signal_bonus(signal)
    ranking_score += get_rank_text_bonus(rank_text)
    ranking_score += get_win_rate_bonus(win_rate_number)
    ranking_score += get_raw_score_bonus(raw_score, ai_score)
    ranking_score += get_ai_score_bonus(ai_score)

    ranking_score += get_adx_bonus(result)
    ranking_score += get_mtf_bonus(result)
    ranking_score += get_ema_bonus(result)
    ranking_score += get_macd_bonus(result)
    ranking_score += get_candle_bonus(result)
    ranking_score += get_rsi_bonus(result)
    ranking_score += get_direction_consistency_bonus(result)

    if is_wait_signal(signal):
        ranking_score -= 12

    # Ranking Scoreの最低値を0にする
    ranking_score = max(0, ranking_score)

    return ranking_score



def get_best_sort_key(result):
    ranking_score = safe_int(result.get("ranking_score"), 0)
    ai_score = safe_int(result.get("score"), 0)
    raw_score = safe_int(result.get("raw_score"), ai_score)
    win_rate = safe_int(result.get("win_rate_number"), 0)
    signal_rank = safe_int(result.get("signal_rank"), 0)
    rank_power = safe_int(result.get("rank_power"), 0)
    adx_value = safe_float(result.get("adx_value"), 0)
    mtf_count, mtf_direction = count_mtf_alignment(result.get("mtf"))
    symbol_priority = get_symbol_priority(result.get("symbol"))

    return (
        ranking_score,
        ai_score,
        signal_rank,
        win_rate,
        rank_power,
        adx_value,
        mtf_count,
        raw_score,
        symbol_priority,
    )


def apply_ranking_scores(results):
    ranked = []

    for result in results:
        if result is None:
            continue

        result["ranking_score"] = calculate_ranking_score(result)
        ranked.append(result)

    ranked = sorted(
        ranked,
        key=get_best_sort_key,
        reverse=True
    )

    return ranked


def choose_best_trade(results):
    if not results:
        return None

    ranked = apply_ranking_scores(results)

    if not ranked:
        return None

    return ranked[0]