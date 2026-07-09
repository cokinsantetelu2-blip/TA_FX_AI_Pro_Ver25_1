# ai_score.py

def calculate_ai_score(mtf, ema20, ema75, rsi, dow):

    score = 0
    reasons = []

    # ===== ダウ理論（最重要）=====
    if "上昇" in dow:
        score += 30
        reasons.append("ダウ理論 上昇")
    elif "下降" in dow:
        score += 0
        reasons.append("ダウ理論 下降")
    else:
        score += 10
        reasons.append("ダウ理論 レンジ")

    # ===== マルチタイムフレーム =====
    if "上昇" in mtf["1H"]:
        score += 10
        reasons.append("1時間足 上昇")

    if "上昇" in mtf["4H"]:
        score += 15
        reasons.append("4時間足 上昇")

    if "上昇" in mtf["1D"]:
        score += 20
        reasons.append("日足 上昇")

    # ===== EMA =====
    if ema20 > ema75:
        score += 15
        reasons.append("EMA ゴールデンクロス")

    # ===== RSI =====
    if 45 <= rsi <= 60:
        score += 10
        reasons.append("RSI 適正")
    elif rsi < 30:
        score += 10
        reasons.append("RSI 売られすぎ")
    elif rsi > 70:
        reasons.append("RSI 買われすぎ")

    # ===== AI判定 =====
    if score >= 80:
        signal = "🟢 強い買い"
    elif score >= 60:
        signal = "🟡 買い候補"
    elif score >= 40:
        signal = "⚪ 様子見"
    else:
        signal = "🔴 見送り"

    return score, signal, reasons