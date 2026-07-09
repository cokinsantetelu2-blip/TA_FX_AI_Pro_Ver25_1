def calculate_score(trend, structure, signal):

    score = 0
    reasons = []

    # ダウ理論
    if "上昇" in trend:
        score += 30
        reasons.append("📈 上昇トレンド")

    elif "下降" in trend:
        score += 30
        reasons.append("📉 下降トレンド")

    # 相場構造
    if "強い上昇" in structure:
        score += 30
        reasons.append("🚀 強い上昇")

    elif "強い下降" in structure:
        score += 30
        reasons.append("⬇ 強い下降")

    # シグナル
    if "押し目" in signal:
        score += 40
        reasons.append("✅ 押し目候補")

    elif "戻り売り" in signal:
        score += 40
        reasons.append("✅ 戻り売り候補")

    return score, reasons