# trend_engine.py
# USDJPY_Fibo_AI Ver13

def judge_trend(
    ema20_text=None,
    ema75_text=None,
    dow_text=None,
    mtf=None,
):
    """
    トレンド判定
    戻り値:
        trend_text
        trend_score
        reasons
    """

    score = 0
    reasons = []

    # EMA20
    if ema20_text in ["強い上向き", "上向き"]:
        score += 10
        reasons.append("EMA20上昇")

    elif ema20_text in ["強い下向き", "下向き"]:
        score += 10
        reasons.append("EMA20下降")

    # EMA75
    if ema75_text == "EMA75上向き":
        score += 10
        reasons.append("EMA75上昇")

    elif ema75_text == "EMA75下向き":
        score += 10
        reasons.append("EMA75下降")

    # ダウ理論
    if dow_text == "上昇":
        score += 10
        reasons.append("ダウ上昇")

    elif dow_text == "下降":
        score += 10
        reasons.append("ダウ下降")

    # MTF一致
    if isinstance(mtf, dict):

        values = [
            mtf.get("1H"),
            mtf.get("4H"),
            mtf.get("1D"),
        ]

        if values.count("上昇") >= 2:
            score += 15
            reasons.append("MTF上昇一致")

        elif values.count("下降") >= 2:
            score += 15
            reasons.append("MTF下降一致")

    # 判定
    if score >= 40:
        trend = "強いトレンド"

    elif score >= 25:
        trend = "トレンドあり"

    else:
        trend = "レンジ"

    return trend, score, reasons