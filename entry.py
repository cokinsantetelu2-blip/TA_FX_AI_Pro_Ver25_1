# entry.py

def judge_entry(mtf, dow, ema20, ema75, rsi, fib_ok):

    score = 0
    reasons = []

    # =========================
    # ダウ理論
    # =========================
    if dow == "上昇":
        score += 25
        reasons.append("ダウ理論：上昇トレンド")
    elif dow == "下降":
        score -= 10
        reasons.append("ダウ理論：下降トレンド")
    else:
        reasons.append("ダウ理論：方向感なし")

    # =========================
    # マルチタイムフレーム
    # =========================
    if "上昇" in mtf["1D"]:
        score += 25
        reasons.append("日足：上昇")
    elif "下降" in mtf["1D"]:
        score -= 10
        reasons.append("日足：下降")

    if "上昇" in mtf["4H"]:
        score += 20
        reasons.append("4時間足：上昇")
    elif "下降" in mtf["4H"]:
        score -= 8
        reasons.append("4時間足：下降")

    if "上昇" in mtf["1H"]:
        score += 10
        reasons.append("1時間足：上昇")
    elif "下降" in mtf["1H"]:
        score -= 5
        reasons.append("1時間足：下降")

    # =========================
    # EMA
    # =========================
    if ema20 is not None and ema75 is not None:
        if ema20 > ema75:
            score += 10
            reasons.append("EMA：短期線が長期線より上")
        elif ema20 < ema75:
            score -= 5
            reasons.append("EMA：短期線が長期線より下")
        else:
            reasons.append("EMA：横ばい")

    # =========================
    # RSI
    # =========================
    if rsi is not None:
        if 45 <= rsi <= 60:
            score += 10
            reasons.append("RSI：買いに適した範囲")
        elif 35 <= rsi < 45:
            score += 7
            reasons.append("RSI：押し目候補")
        elif rsi < 30:
            score += 5
            reasons.append("RSI：売られすぎ注意")
        elif rsi > 70:
            score -= 10
            reasons.append("RSI：買われすぎ注意")
        else:
            reasons.append("RSI：中立")

    # =========================
    # フィボナッチ
    # =========================
    if fib_ok:
        score += 15
        reasons.append("フィボ：反発候補")

    # =========================
    # スコア調整
    # =========================
    if score > 100:
        score = 100

    if score < 0:
        score = 0

    # =========================
    # ランク
    # =========================
    if score >= 90:
        rank = "★★★★★"
        strength = "最強"
    elif score >= 80:
        rank = "★★★★☆"
        strength = "強い"
    elif score >= 70:
        rank = "★★★☆☆"
        strength = "普通"
    elif score >= 60:
        rank = "★★☆☆☆"
        strength = "弱い"
    else:
        rank = "★☆☆☆☆"
        strength = "見送り"

    # =========================
    # 勝率目安
    # =========================
    win_rate = int(score * 0.8 + 10)

    if win_rate > 90:
        win_rate = 90

    if win_rate < 30:
        win_rate = 30

    # =========================
    # 判定
    # =========================
    if score >= 80:
        signal = f"🟢 BUY候補\nランク：{rank}\n強度：{strength}\n勝率目安：{win_rate}%"
    elif score >= 60:
        signal = f"🟡 WAIT\nランク：{rank}\n強度：{strength}\n勝率目安：{win_rate}%"
    else:
        signal = f"🔴 WAIT\nランク：{rank}\n強度：{strength}\n勝率目安：{win_rate}%"

    return score, signal, reasons