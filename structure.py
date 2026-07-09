def analyze_structure(swing_highs, swing_lows):
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "判定不足", "山・谷が足りません"

    prev_high = swing_highs[-2][1]
    last_high = swing_highs[-1][1]

    prev_low = swing_lows[-2][1]
    last_low = swing_lows[-1][1]

    high_status = "高値切り上げ" if last_high > prev_high else "高値切り下げ"
    low_status = "安値切り上げ" if last_low > prev_low else "安値切り下げ"

    if last_high > prev_high and last_low > prev_low:
        structure = "強い上昇"
        reason = "高値も安値も切り上げています"
    elif last_high < prev_high and last_low < prev_low:
        structure = "強い下降"
        reason = "高値も安値も切り下げています"
    elif last_high > prev_high and last_low < prev_low:
        structure = "拡大型レンジ"
        reason = "高値は更新、安値は切り下げています"
    elif last_high < prev_high and last_low > prev_low:
        structure = "収縮レンジ"
        reason = "高値は切り下げ、安値は切り上げています"
    else:
        structure = "レンジ"
        reason = "方向感が弱いです"

    return structure, f"{high_status} / {low_status} / {reason}"