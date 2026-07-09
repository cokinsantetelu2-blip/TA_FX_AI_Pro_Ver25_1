# reversal_engine.py
# TA FX AI Pro Ver18.0
# Fibonacci Reversal Confirmation Engine
# フィボタッチ後5本以内判定 対応版


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def is_touch_window_valid(touch_status=None):
    if touch_status is None:
        return True

    if not isinstance(touch_status, dict):
        return True

    return bool(touch_status.get("valid", False))


def get_touch_text(touch_status=None):
    if not isinstance(touch_status, dict):
        return "タッチ時間判定なし"

    side = touch_status.get("side")
    level = touch_status.get("level")
    bars = touch_status.get("bars")
    valid = touch_status.get("valid", False)

    if side is None:
        return "フィボ未タッチ"

    if valid:
        return f"{side} {level} タッチ後 {bars}本以内"

    return f"{side} {level} タッチ後 {bars}本経過で期限切れ"


def judge_rsi_reversal(rsi14, direction):
    rsi = safe_float(rsi14)

    if rsi is None:
        return False, "RSI: データ不足"

    if direction == "BUY":
        if rsi <= 35:
            return True, f"RSI反転候補: 売られすぎ {round(rsi, 1)}"
        if 35 < rsi <= 45:
            return True, f"RSI反転気配: {round(rsi, 1)}"
        return False, f"RSI反転弱い: {round(rsi, 1)}"

    if direction == "SELL":
        if rsi >= 65:
            return True, f"RSI反転候補: 買われすぎ {round(rsi, 1)}"
        if 55 <= rsi < 65:
            return True, f"RSI反転気配: {round(rsi, 1)}"
        return False, f"RSI反転弱い: {round(rsi, 1)}"

    return False, "RSI: 方向不明"


def judge_macd_reversal(macd, macd_signal, macd_hist, direction):
    macd = safe_float(macd)
    macd_signal = safe_float(macd_signal)
    macd_hist = safe_float(macd_hist)

    if macd is None or macd_signal is None:
        return False, "MACD: データ不足"

    if direction == "BUY":
        if macd > macd_signal:
            return True, "MACD反転確認: ゴールデンクロス"
        if macd_hist is not None and macd_hist > 0:
            return True, "MACD反転気配: ヒストグラム上向き"
        return False, "MACD反転未確認"

    if direction == "SELL":
        if macd < macd_signal:
            return True, "MACD反転確認: デッドクロス"
        if macd_hist is not None and macd_hist < 0:
            return True, "MACD反転気配: ヒストグラム下向き"
        return False, "MACD反転未確認"

    return False, "MACD: 方向不明"


def judge_candle_reversal(candles, direction):
    if not candles or len(candles) < 2:
        return False, "ローソク足: データ不足"

    last = candles[-1]
    prev = candles[-2]

    try:
        o = float(last["open"])
        h = float(last["high"])
        l = float(last["low"])
        c = float(last["close"])

        po = float(prev["open"])
        pc = float(prev["close"])
    except Exception:
        return False, "ローソク足: 形式エラー"

    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l

    if direction == "BUY":
        if c > o and pc < po and c > po:
            return True, "ローソク足反転: 強気包み足"
        if lower > body * 1.5 and c > o:
            return True, "ローソク足反転: 下ヒゲ陽線"
        if c > o:
            return True, "ローソク足反転気配: 陽線"
        return False, "ローソク足反転未確認"

    if direction == "SELL":
        if c < o and pc > po and c < po:
            return True, "ローソク足反転: 弱気包み足"
        if upper > body * 1.5 and c < o:
            return True, "ローソク足反転: 上ヒゲ陰線"
        if c < o:
            return True, "ローソク足反転気配: 陰線"
        return False, "ローソク足反転未確認"

    return False, "ローソク足: 方向不明"


def judge_reversal(
    direction,
    rsi14=None,
    macd=None,
    macd_signal=None,
    macd_hist=None,
    candles=None,
    touch_status=None,
):
    reasons = []
    score = 0

    touch_text = get_touch_text(touch_status)
    reasons.append(touch_text)

    if not is_touch_window_valid(touch_status):
        return {
            "direction": direction,
            "score": 0,
            "status": "反転期限切れ",
            "rsi_ok": False,
            "macd_ok": False,
            "candle_ok": False,
            "touch_valid": False,
            "touch_text": touch_text,
            "reasons": reasons,
            "text": "反転期限切れ / 0/3",
        }

    candle_ok, candle_reason = judge_candle_reversal(candles, direction)
    rsi_ok, rsi_reason = judge_rsi_reversal(rsi14, direction)
    macd_ok, macd_reason = judge_macd_reversal(macd, macd_signal, macd_hist, direction)

    reasons.append(candle_reason)
    reasons.append(rsi_reason)
    reasons.append(macd_reason)

    if candle_ok:
        score += 1
    if rsi_ok:
        score += 1
    if macd_ok:
        score += 1

    if score >= 3:
        status = "反転確認OK"
    elif score == 2:
        status = "反転確認ややOK"
    elif score == 1:
        status = "反転確認弱い"
    else:
        status = "反転未確認"

    return {
        "direction": direction,
        "score": score,
        "status": status,
        "rsi_ok": rsi_ok,
        "macd_ok": macd_ok,
        "candle_ok": candle_ok,
        "touch_valid": True,
        "touch_text": touch_text,
        "reasons": reasons,
        "text": f"{status} / {score}/3",
    }
