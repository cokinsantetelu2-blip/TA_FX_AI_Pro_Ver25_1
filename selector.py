def select_best_fibo(swing_highs, swing_lows):
    """
    たーちゃんルール Ver3
    """

    if not swing_highs or not swing_lows:
        return None, None, "山・谷が見つかりません"

    best_high = None
    best_low = None
    best_score = 0
    best_reason = "条件に合う波が見つかりません"

    for high_time, high_price in swing_highs:
        previous_lows = [
            (low_time, low_price)
            for low_time, low_price in swing_lows
            if low_time < high_time
        ]

        if not previous_lows:
            continue

        low_time, low_price = previous_lows[-1]
        move = high_price - low_price

        if move < 0.050:
            continue

        minutes = (high_time - low_time).total_seconds() / 60

        if minutes < 3:
            continue

        score = move * 100

        if minutes >= 5:
            score += 5
        if minutes >= 10:
            score += 10

        if score > best_score:
            best_score = score
            best_high = high_price
            best_low = low_price
            best_reason = f"値幅 {move:.3f}円 / 時間 {minutes:.1f}分 / スコア {score:.1f}"

    if best_high is None or best_low is None:
        return None, None, best_reason

    return best_high, best_low, best_reason