def judge_trend(swing_highs, swing_lows):
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "判定できません"

    high1 = swing_highs[-2][1]
    high2 = swing_highs[-1][1]

    low1 = swing_lows[-2][1]
    low2 = swing_lows[-1][1]

    if high2 > high1 and low2 > low1:
        return "📈 上昇トレンド"
    elif high2 < high1 and low2 < low1:
        return "📉 下降トレンド"
    else:
        return "➡ レンジ"