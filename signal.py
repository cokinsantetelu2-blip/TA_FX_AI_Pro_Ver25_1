def judge_signal(trend, selected_high, selected_low, best_reason):
    if selected_high is None or selected_low is None:
        return "見送り", "フィボに使える山と谷がありません"

    move = selected_high - selected_low

    if move < 0.050:
        return "見送り", "値幅が小さすぎます"

    if "レンジ" in trend:
        return "注意", "レンジ内の先読みフィボです"

    if "上昇" in trend:
        return "押し目候補", "上昇トレンド中のフィボです"

    if "下降" in trend:
        return "戻り売り候補", "下降トレンド中のフィボです"

    return "注意", "トレンド判定が弱い状態です"