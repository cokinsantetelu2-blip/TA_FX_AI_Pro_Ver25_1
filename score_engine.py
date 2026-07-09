# score_engine.py
# TA FX AI Pro Ver25.0
# BUY / SELL 別スコア計算エンジン
# AI採点監査対応版
# 目的：採点ロジックを変えず、各項目の点数内訳を返す

def clamp_score(score):
    try:
        score = int(score)
    except Exception:
        score = 0

    if score < 0:
        return 0

    if score > 100:
        return 100

    return score


def safe_text(value):
    if value is None:
        return ""
    return str(value)


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def make_empty_breakdown(total=0):
    return {
        "FIBO": 0,
        "REVERSAL": 0,
        "RSI": 0,
        "MACD": 0,
        "DOW": 0,
        "MTF": 0,
        "CANDLE": 0,
        "ATR": 0,
        "CAP": 0,
        "TOTAL": clamp_score(total),
    }


def is_touch(fibo_touch):
    if not fibo_touch:
        return False

    if isinstance(fibo_touch, dict):
        return bool(fibo_touch.get("touch", False))

    return False


def is_within_limit(touch_info):
    if not isinstance(touch_info, dict):
        return True

    return bool(touch_info.get("within_limit", False))


def get_elapsed_bars(touch_info):
    if not isinstance(touch_info, dict):
        return "-"

    return touch_info.get("elapsed_bars", "-")


def get_reversal_score(reversal):
    if not isinstance(reversal, dict):
        return 0

    try:
        return int(reversal.get("score", 0))
    except Exception:
        return 0


def get_reversal_text(reversal):
    if not isinstance(reversal, dict):
        return "反転確認データなし"

    text = reversal.get("text")
    if text:
        return str(text)

    status = reversal.get("status", "反転確認データなし")
    score = reversal.get("score", 0)

    return f"{status} / {score}/3"


def get_reversal_reasons(reversal):
    if not isinstance(reversal, dict):
        return ["反転確認データなし"]

    reasons = reversal.get("reasons", [])

    if isinstance(reasons, list):
        return reasons

    return [str(reasons)]


def score_reversal(reversal):
    reversal_score = get_reversal_score(reversal)
    reversal_text = get_reversal_text(reversal)

    if reversal_score >= 3:
        return 30, f"{reversal_text} +30"

    if reversal_score == 2:
        return 20, f"{reversal_text} +20"

    if reversal_score == 1:
        return 8, f"{reversal_text} +8"

    return 0, f"{reversal_text} +0"


def score_rsi_for_buy(rsi14):
    rsi = safe_float(rsi14)

    if rsi is None:
        return 0, "RSIデータ不足"

    if rsi <= 30:
        return 8, "RSI強い売られ過ぎ"
    if rsi <= 40:
        return 5, "RSI売られ過ぎ寄り"
    if rsi <= 50:
        return 2, "RSI反発余地あり"

    return 0, "RSI買い加点なし"


def score_rsi_for_sell(rsi14):
    rsi = safe_float(rsi14)

    if rsi is None:
        return 0, "RSIデータ不足"

    if rsi >= 70:
        return 8, "RSI強い買われ過ぎ"
    if rsi >= 60:
        return 5, "RSI買われ過ぎ寄り"
    if rsi >= 50:
        return 2, "RSI下落余地あり"

    return 0, "RSI売り加点なし"


def score_macd_for_buy(macd_cross_text=None, macd_hist_text=None):
    text = safe_text(macd_cross_text) + " " + safe_text(macd_hist_text)

    score = 0
    reasons = []

    if "ゴールデン" in text or "上昇" in text or "買" in text:
        score += 5
        reasons.append("MACD買い方向")

    if "勢い" in text or "強い" in text or "拡大" in text:
        score += 3
        reasons.append("MACD勢いあり")

    if score == 0:
        reasons.append("MACD買い加点なし")

    return min(score, 8), " / ".join(reasons)


def score_macd_for_sell(macd_cross_text=None, macd_hist_text=None):
    text = safe_text(macd_cross_text) + " " + safe_text(macd_hist_text)

    score = 0
    reasons = []

    if "デッド" in text or "下降" in text or "売" in text:
        score += 5
        reasons.append("MACD売り方向")

    if "勢い" in text or "強い" in text or "拡大" in text:
        score += 3
        reasons.append("MACD勢いあり")

    if score == 0:
        reasons.append("MACD売り加点なし")

    return min(score, 8), " / ".join(reasons)


def score_dow_for_buy(dow_text):
    text = safe_text(dow_text)

    if "上昇" in text:
        return 10, "ダウ上昇一致"

    if "レンジ" in text:
        return 3, "ダウレンジ"

    return 0, "ダウ買い不一致"


def score_dow_for_sell(dow_text):
    text = safe_text(dow_text)

    if "下降" in text:
        return 10, "ダウ下降一致"

    if "レンジ" in text:
        return 3, "ダウレンジ"

    return 0, "ダウ売り不一致"


def score_mtf_for_buy(mtf):
    if not isinstance(mtf, dict):
        return 0, "MTFデータ不足"

    score = 0

    one_h = safe_text(mtf.get("1H"))
    four_h = safe_text(mtf.get("4H"))
    one_d = safe_text(mtf.get("1D"))

    if "上昇" in one_h or "BUY" in one_h.upper():
        score += 4

    if "上昇" in four_h or "BUY" in four_h.upper():
        score += 3

    if "上昇" in one_d or "BUY" in one_d.upper():
        score += 3

    if score > 0:
        return min(score, 10), f"MTF買い方向 {score}点"

    return 0, "MTF買い不一致"


def score_mtf_for_sell(mtf):
    if not isinstance(mtf, dict):
        return 0, "MTFデータ不足"

    score = 0

    one_h = safe_text(mtf.get("1H"))
    four_h = safe_text(mtf.get("4H"))
    one_d = safe_text(mtf.get("1D"))

    if "下降" in one_h or "SELL" in one_h.upper():
        score += 4

    if "下降" in four_h or "SELL" in four_h.upper():
        score += 3

    if "下降" in one_d or "SELL" in one_d.upper():
        score += 3

    if score > 0:
        return min(score, 10), f"MTF売り方向 {score}点"

    return 0, "MTF売り不一致"


def score_candle_for_buy(candle_text):
    text = safe_text(candle_text)

    buy_words = [
        "陽線",
        "反転",
        "包み",
        "ピンバー",
        "下ヒゲ",
        "買",
        "上昇",
    ]

    for word in buy_words:
        if word in text:
            return 8, "ローソク足買い反転"

    return 0, "ローソク足買い加点なし"


def score_candle_for_sell(candle_text):
    text = safe_text(candle_text)

    sell_words = [
        "陰線",
        "反転",
        "包み",
        "ピンバー",
        "上ヒゲ",
        "売",
        "下降",
    ]

    for word in sell_words:
        if word in text:
            return 8, "ローソク足売り反転"

    return 0, "ローソク足売り加点なし"


def score_atr_average(atr=None, atr_average=None, atr_status=None):
    """
    ATR平均比較AIをAIスコアへ反映

    高ボラ: +5
    通常ボラ: ±0
    低ボラ: -5
    """

    text = safe_text(atr_status)

    if "高ボラ" in text:
        return 5, "ATR平均比較AI: 高ボラ +5"

    if "低ボラ" in text:
        return -5, "ATR平均比較AI: 低ボラ -5"

    if "通常" in text:
        return 0, "ATR平均比較AI: 通常ボラ ±0"

    current_atr = safe_float(atr)
    average_atr = safe_float(atr_average)

    if current_atr is None or average_atr is None or average_atr <= 0:
        return 0, "ATR平均比較AI: データ不足 ±0"

    ratio = current_atr / average_atr

    if ratio >= 1.30:
        return 5, "ATR平均比較AI: 高ボラ +5"

    if ratio <= 0.70:
        return -5, "ATR平均比較AI: 低ボラ -5"

    return 0, "ATR平均比較AI: 通常ボラ ±0"


def calculate_buy_score(
    buy_fibo_touch=None,
    rsi14=None,
    macd_cross_text=None,
    macd_hist_text=None,
    dow_text=None,
    mtf=None,
    candle_text=None,
    buy_reversal=None,
    buy_touch_info=None,
    atr=None,
    atr_average=None,
    atr_status=None,
):
    score = 0
    reasons = []
    breakdown = make_empty_breakdown(0)

    if not is_touch(buy_fibo_touch):
        reasons.append("BUYフィボ未タッチ")
        breakdown["TOTAL"] = 0
        return 0, reasons, breakdown

    if buy_touch_info is not None and not is_within_limit(buy_touch_info):
        elapsed = get_elapsed_bars(buy_touch_info)
        reasons.append(f"BUYフィボタッチから{elapsed}本経過")
        reasons.append("BUYフィボタッチ5本以内ではないため採点対象外")
        breakdown["TOTAL"] = 0
        return 0, reasons, breakdown

    fibo_score = 30
    score += fibo_score
    breakdown["FIBO"] = fibo_score
    reasons.append("BUYフィボタッチ +30")

    if buy_touch_info is not None:
        elapsed = get_elapsed_bars(buy_touch_info)
        reasons.append(f"BUYフィボタッチから{elapsed}本経過 / 5本以内")

    reversal_score, reversal_reason = score_reversal(buy_reversal)
    score += reversal_score
    breakdown["REVERSAL"] = reversal_score
    reasons.append(f"BUY反転確認: {reversal_reason}")

    for reason in get_reversal_reasons(buy_reversal):
        reasons.append(f"BUY反転理由: {reason}")

    rsi_score, rsi_reason = score_rsi_for_buy(rsi14)
    score += rsi_score
    breakdown["RSI"] = rsi_score
    reasons.append(f"{rsi_reason} +{rsi_score}")

    macd_score, macd_reason = score_macd_for_buy(macd_cross_text, macd_hist_text)
    score += macd_score
    breakdown["MACD"] = macd_score
    reasons.append(f"{macd_reason} +{macd_score}")

    dow_score, dow_reason = score_dow_for_buy(dow_text)
    score += dow_score
    breakdown["DOW"] = dow_score
    reasons.append(f"{dow_reason} +{dow_score}")

    mtf_score, mtf_reason = score_mtf_for_buy(mtf)
    score += mtf_score
    breakdown["MTF"] = mtf_score
    reasons.append(f"{mtf_reason} +{mtf_score}")

    candle_score, candle_reason = score_candle_for_buy(candle_text)
    score += candle_score
    breakdown["CANDLE"] = candle_score
    reasons.append(f"{candle_reason} +{candle_score}")

    atr_average_score, atr_average_reason = score_atr_average(
        atr=atr,
        atr_average=atr_average,
        atr_status=atr_status,
    )
    score += atr_average_score
    breakdown["ATR"] = atr_average_score
    reasons.append(atr_average_reason)

    before_cap_score = score

    if get_reversal_score(buy_reversal) == 0:
        score = min(score, 55)
        reasons.append("BUY反転未確認のため55点上限")

    if get_reversal_score(buy_reversal) == 1:
        score = min(score, 68)
        reasons.append("BUY反転確認弱いため68点上限")

    final_score = clamp_score(score)
    breakdown["CAP"] = final_score - clamp_score(before_cap_score)
    breakdown["TOTAL"] = final_score

    return final_score, reasons, breakdown


def calculate_sell_score(
    sell_fibo_touch=None,
    rsi14=None,
    macd_cross_text=None,
    macd_hist_text=None,
    dow_text=None,
    mtf=None,
    candle_text=None,
    sell_reversal=None,
    sell_touch_info=None,
    atr=None,
    atr_average=None,
    atr_status=None,
):
    score = 0
    reasons = []
    breakdown = make_empty_breakdown(0)

    if not is_touch(sell_fibo_touch):
        reasons.append("SELLフィボ未タッチ")
        breakdown["TOTAL"] = 0
        return 0, reasons, breakdown

    if sell_touch_info is not None and not is_within_limit(sell_touch_info):
        elapsed = get_elapsed_bars(sell_touch_info)
        reasons.append(f"SELLフィボタッチから{elapsed}本経過")
        reasons.append("SELLフィボタッチ5本以内ではないため採点対象外")
        breakdown["TOTAL"] = 0
        return 0, reasons, breakdown

    fibo_score = 30
    score += fibo_score
    breakdown["FIBO"] = fibo_score
    reasons.append("SELLフィボタッチ +30")

    if sell_touch_info is not None:
        elapsed = get_elapsed_bars(sell_touch_info)
        reasons.append(f"SELLフィボタッチから{elapsed}本経過 / 5本以内")

    reversal_score, reversal_reason = score_reversal(sell_reversal)
    score += reversal_score
    breakdown["REVERSAL"] = reversal_score
    reasons.append(f"SELL反転確認: {reversal_reason}")

    for reason in get_reversal_reasons(sell_reversal):
        reasons.append(f"SELL反転理由: {reason}")

    rsi_score, rsi_reason = score_rsi_for_sell(rsi14)
    score += rsi_score
    breakdown["RSI"] = rsi_score
    reasons.append(f"{rsi_reason} +{rsi_score}")

    macd_score, macd_reason = score_macd_for_sell(macd_cross_text, macd_hist_text)
    score += macd_score
    breakdown["MACD"] = macd_score
    reasons.append(f"{macd_reason} +{macd_score}")

    dow_score, dow_reason = score_dow_for_sell(dow_text)
    score += dow_score
    breakdown["DOW"] = dow_score
    reasons.append(f"{dow_reason} +{dow_score}")

    mtf_score, mtf_reason = score_mtf_for_sell(mtf)
    score += mtf_score
    breakdown["MTF"] = mtf_score
    reasons.append(f"{mtf_reason} +{mtf_score}")

    candle_score, candle_reason = score_candle_for_sell(candle_text)
    score += candle_score
    breakdown["CANDLE"] = candle_score
    reasons.append(f"{candle_reason} +{candle_score}")

    atr_average_score, atr_average_reason = score_atr_average(
        atr=atr,
        atr_average=atr_average,
        atr_status=atr_status,
    )
    score += atr_average_score
    breakdown["ATR"] = atr_average_score
    reasons.append(atr_average_reason)

    before_cap_score = score

    if get_reversal_score(sell_reversal) == 0:
        score = min(score, 55)
        reasons.append("SELL反転未確認のため55点上限")

    if get_reversal_score(sell_reversal) == 1:
        score = min(score, 68)
        reasons.append("SELL反転確認弱いため68点上限")

    final_score = clamp_score(score)
    breakdown["CAP"] = final_score - clamp_score(before_cap_score)
    breakdown["TOTAL"] = final_score

    return final_score, reasons, breakdown


def judge_buy_sell_score(
    buy_fibo_touch=None,
    sell_fibo_touch=None,
    rsi14=None,
    macd_cross_text=None,
    macd_hist_text=None,
    dow_text=None,
    mtf=None,
    candle_text=None,
    buy_reversal=None,
    sell_reversal=None,
    buy_touch_info=None,
    sell_touch_info=None,
    atr=None,
    atr_average=None,
    atr_status=None,
):
    buy_touch = is_touch(buy_fibo_touch)
    sell_touch = is_touch(sell_fibo_touch)

    buy_score, buy_reasons, buy_score_breakdown = calculate_buy_score(
        buy_fibo_touch=buy_fibo_touch,
        rsi14=rsi14,
        macd_cross_text=macd_cross_text,
        macd_hist_text=macd_hist_text,
        dow_text=dow_text,
        mtf=mtf,
        candle_text=candle_text,
        buy_reversal=buy_reversal,
        buy_touch_info=buy_touch_info,
        atr=atr,
        atr_average=atr_average,
        atr_status=atr_status,
    )

    sell_score, sell_reasons, sell_score_breakdown = calculate_sell_score(
        sell_fibo_touch=sell_fibo_touch,
        rsi14=rsi14,
        macd_cross_text=macd_cross_text,
        macd_hist_text=macd_hist_text,
        dow_text=dow_text,
        mtf=mtf,
        candle_text=candle_text,
        sell_reversal=sell_reversal,
        sell_touch_info=sell_touch_info,
        atr=atr,
        atr_average=atr_average,
        atr_status=atr_status,
    )

    if not buy_touch and not sell_touch:
        return {
            "score": 0,
            "signal": "WAIT",
            "side": "WAIT",
            "adopted_side": "WAIT",
            "buy_score": 0,
            "sell_score": 0,
            "score_breakdown": make_empty_breakdown(0),
            "buy_score_breakdown": buy_score_breakdown,
            "sell_score_breakdown": sell_score_breakdown,
            "reasons": [
                "BUYフィボ未タッチ",
                "SELLフィボ未タッチ",
                "フィボタッチなしのため見送り",
            ],
            "buy_reasons": buy_reasons,
            "sell_reasons": sell_reasons,
            "buy_reversal": buy_reversal,
            "sell_reversal": sell_reversal,
        }

    if buy_touch_info is not None and not is_within_limit(buy_touch_info):
        buy_score = 0
        buy_score_breakdown["TOTAL"] = 0

    if sell_touch_info is not None and not is_within_limit(sell_touch_info):
        sell_score = 0
        sell_score_breakdown["TOTAL"] = 0

    if buy_score == 0 and sell_score == 0:
        return {
            "score": 0,
            "signal": "WAIT",
            "side": "WAIT",
            "adopted_side": "WAIT",
            "buy_score": buy_score,
            "sell_score": sell_score,
            "score_breakdown": make_empty_breakdown(0),
            "buy_score_breakdown": buy_score_breakdown,
            "sell_score_breakdown": sell_score_breakdown,
            "reasons": [
                "フィボタッチ5本以内ではないためWAIT",
                "BUY/SELLともに採点対象外",
            ],
            "buy_reasons": buy_reasons,
            "sell_reasons": sell_reasons,
            "buy_reversal": buy_reversal,
            "sell_reversal": sell_reversal,
        }

    if buy_score >= sell_score:
        adopted_side = "BUY"
        signal = "BUY候補"
        score = buy_score
        reasons = buy_reasons
        score_breakdown = buy_score_breakdown
    else:
        adopted_side = "SELL"
        signal = "SELL候補"
        score = sell_score
        reasons = sell_reasons
        score_breakdown = sell_score_breakdown

    if adopted_side == "BUY" and get_reversal_score(buy_reversal) == 0:
        signal = "WAIT"
        adopted_side = "WAIT"
        score = 0
        reasons = buy_reasons + ["BUYフィボタッチ後の反転未確認のためWAIT"]
        score_breakdown = make_empty_breakdown(0)

    if adopted_side == "SELL" and get_reversal_score(sell_reversal) == 0:
        signal = "WAIT"
        adopted_side = "WAIT"
        score = 0
        reasons = sell_reasons + ["SELLフィボタッチ後の反転未確認のためWAIT"]
        score_breakdown = make_empty_breakdown(0)

    final_score = clamp_score(score)
    score_breakdown["TOTAL"] = final_score

    return {
        "score": final_score,
        "signal": signal,
        "side": adopted_side,
        "adopted_side": adopted_side,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "score_breakdown": score_breakdown,
        "buy_score_breakdown": buy_score_breakdown,
        "sell_score_breakdown": sell_score_breakdown,
        "reasons": reasons,
        "buy_reasons": buy_reasons,
        "sell_reasons": sell_reasons,
        "buy_reversal": buy_reversal,
        "sell_reversal": sell_reversal,
    }


def calculate_win_rate(score):
    score = clamp_score(score)

    if score >= 90:
        return "勝率目安：約80〜90%"

    if score >= 80:
        return "勝率目安：約75〜85%"

    if score >= 70:
        return "勝率目安：約65〜75%"

    if score >= 60:
        return "勝率目安：約55〜65%"

    if score >= 50:
        return "勝率目安：約50〜60%"

    return "勝率目安：低め"


def calculate_total_score(
    base_score,
    ema20_score=0,
    ema75_score=0,
    macd_score=0,
    macd_hist_score=0,
    adx_score=0,
    atr_score=0,
    candle_score=0,
    fib_score=0,
    atr=None,
    atr_average=None,
    atr_status=None,
):
    score = base_score

    score += ema20_score
    score += ema75_score
    score += macd_score
    score += macd_hist_score
    score += adx_score
    score += atr_score
    score += candle_score
    score += fib_score

    atr_average_score, _ = score_atr_average(
        atr=atr,
        atr_average=atr_average,
        atr_status=atr_status,
    )
    score += atr_average_score

    return clamp_score(score)


def calculate_total_score_with_breakdown(
    base_score,
    ema20_score=0,
    ema75_score=0,
    macd_score=0,
    macd_hist_score=0,
    adx_score=0,
    atr_score=0,
    candle_score=0,
    fib_score=0,
    atr=None,
    atr_average=None,
    atr_status=None,
):
    atr_average_score, atr_average_reason = score_atr_average(
        atr=atr,
        atr_average=atr_average,
        atr_status=atr_status,
    )

    total = (
        base_score
        + ema20_score
        + ema75_score
        + macd_score
        + macd_hist_score
        + adx_score
        + atr_score
        + candle_score
        + fib_score
        + atr_average_score
    )

    breakdown = {
        "BASE": base_score,
        "EMA20": ema20_score,
        "EMA75": ema75_score,
        "MACD": macd_score,
        "MACD_HIST": macd_hist_score,
        "ADX": adx_score,
        "ATR": atr_score + atr_average_score,
        "CANDLE": candle_score,
        "FIBO": fib_score,
        "ATR_REASON": atr_average_reason,
        "TOTAL": clamp_score(total),
    }

    return clamp_score(total), breakdown


def should_force_wait(
    score,
    adx_text=None,
    atr_text=None,
):
    score = clamp_score(score)

    if score < 50:
        return True

    if adx_text == "レンジ気味":
        return True

    if atr_text == "ボラ不足":
        return True

    return False