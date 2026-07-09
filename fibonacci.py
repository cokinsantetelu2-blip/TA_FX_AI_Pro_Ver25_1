# fibonacci.py
# TA FX AI Pro Ver25.1
# BUY用スイング / SELL用スイング 別検出版
# Ver25 監査ログ追加版
#
# 目的:
# ・スイングが毎回変わっていないか確認
# ・フィボ価格が毎回変わっていないか確認
# ・TOP5で0本へ戻る原因が fibonacci.py 側にあるか監査
#
# 注意:
# ・Ver25は監査のみ
# ・判定ロジックは変更しない
# ・新機能追加なし

from collections import deque


TARGET_AUDIT_LEVELS = [
    "38.2%",
    "50.0%",
    "61.8%",
    "78.6%",
]


def print_pair_audit(title, pair):
    print("")
    print("========== FIBONACCI PAIR AUDIT ==========")
    print("TITLE:", title)

    if pair is None:
        print("pair: None")
        print("==========================================")
        print("")
        return

    start, end = pair

    print("START type:", start.get("type"))
    print("START index:", start.get("index"))
    print("START price:", start.get("price"))
    print("START strength:", start.get("strength"))

    print("END type:", end.get("type"))
    print("END index:", end.get("index"))
    print("END price:", end.get("price"))
    print("END strength:", end.get("strength"))

    print("pair_score:", round(_pair_score(start, end), 6))
    print("==========================================")
    print("")


def print_fibonacci_audit(title, fib):
    print("")
    print("========== FIBONACCI PRICE AUDIT ==========")
    print("TITLE:", title)

    if not fib:
        print("fib: None / empty")
        print("===========================================")
        print("")
        return

    for level in TARGET_AUDIT_LEVELS:
        print(level, ":", fib.get(level))

    print("===========================================")
    print("")


def calculate_fibonacci(high_price, low_price):
    """
    旧仕様互換用
    高値 → 安値の通常フィボ
    """
    diff = high_price - low_price

    if diff <= 0:
        return None

    return {
        "0.0%": round(high_price, 3),
        "23.6%": round(high_price - diff * 0.236, 3),
        "38.2%": round(high_price - diff * 0.382, 3),
        "50.0%": round(high_price - diff * 0.500, 3),
        "61.8%": round(high_price - diff * 0.618, 3),
        "78.6%": round(high_price - diff * 0.786, 3),
        "100.0%": round(low_price, 3),
    }


def calculate_buy_fibonacci(low_price, high_price):
    """
    BUY用フィボ
    LOW → HIGH
    押し目買い判定用
    """
    diff = high_price - low_price

    if diff <= 0:
        return None

    return {
        "0.0%": round(low_price, 3),
        "23.6%": round(high_price - diff * 0.236, 3),
        "38.2%": round(high_price - diff * 0.382, 3),
        "50.0%": round(high_price - diff * 0.500, 3),
        "61.8%": round(high_price - diff * 0.618, 3),
        "78.6%": round(high_price - diff * 0.786, 3),
        "100.0%": round(high_price, 3),
    }


def calculate_sell_fibonacci(high_price, low_price):
    """
    SELL用フィボ
    HIGH → LOW
    戻り売り判定用
    """
    diff = high_price - low_price

    if diff <= 0:
        return None

    return {
        "0.0%": round(high_price, 3),
        "23.6%": round(low_price + diff * 0.236, 3),
        "38.2%": round(low_price + diff * 0.382, 3),
        "50.0%": round(low_price + diff * 0.500, 3),
        "61.8%": round(low_price + diff * 0.618, 3),
        "78.6%": round(low_price + diff * 0.786, 3),
        "100.0%": round(low_price, 3),
    }


def calculate_dual_fibonacci(high_price, low_price):
    """
    旧互換用
    同じ高値安値からBUY/SELL両方作成
    """
    if high_price is None or low_price is None:
        return None, None

    if high_price <= low_price:
        return None, None

    buy_fib = calculate_buy_fibonacci(low_price, high_price)
    sell_fib = calculate_sell_fibonacci(high_price, low_price)

    return buy_fib, sell_fib


def _safe_float(value):
    try:
        if value is None:
            return None
        if hasattr(value, "iloc"):
            value = value.iloc[0]
        return float(value)
    except Exception:
        return None


def _normalize_candles(candles):
    clean = []

    if not candles:
        return clean

    for i, c in enumerate(candles):
        try:
            high = _safe_float(c.get("high", c.get("High")))
            low = _safe_float(c.get("low", c.get("Low")))

            if high is None or low is None:
                continue

            clean.append({
                "index": i,
                "high": high,
                "low": low,
            })
        except Exception:
            continue

    return clean


def _find_swings(candles, window=3):
    candles = _normalize_candles(candles)
    swings = []

    if len(candles) < window * 2 + 5:
        return swings

    for i in range(window, len(candles) - window):
        high = candles[i]["high"]
        low = candles[i]["low"]

        left = candles[i - window:i]
        right = candles[i + 1:i + window + 1]

        left_high = max(c["high"] for c in left)
        right_high = max(c["high"] for c in right)
        left_low = min(c["low"] for c in left)
        right_low = min(c["low"] for c in right)

        if high > left_high and high > right_high:
            strength = high - max(left_high, right_high)

            swings.append({
                "type": "HIGH",
                "index": candles[i]["index"],
                "price": high,
                "strength": strength,
            })

        if low < left_low and low < right_low:
            strength = min(left_low, right_low) - low

            swings.append({
                "type": "LOW",
                "index": candles[i]["index"],
                "price": low,
                "strength": strength,
            })

    swings.sort(key=lambda x: x["index"])
    return swings


def _remove_noise(swings):
    if not swings:
        return []

    cleaned = deque()

    for swing in swings:
        if not cleaned:
            cleaned.append(swing)
            continue

        last = cleaned[-1]

        if last["type"] == swing["type"]:
            if swing["type"] == "HIGH":
                if swing["price"] >= last["price"]:
                    cleaned[-1] = swing
            else:
                if swing["price"] <= last["price"]:
                    cleaned[-1] = swing
        else:
            cleaned.append(swing)

    return list(cleaned)


def _pair_score(start, end):
    distance = abs(end["index"] - start["index"])
    movement = abs(end["price"] - start["price"])
    recency = end["index"]

    return (
        movement * 100
        + distance * 0.5
        + recency * 0.05
        + start.get("strength", 0) * 50
        + end.get("strength", 0) * 50
    )


def _latest_direction_pair(swings, start_type, end_type):
    """
    BUY用 : LOW → HIGH
    SELL用: HIGH → LOW
    """
    if not swings or len(swings) < 2:
        return None

    candidates = []

    for i in range(len(swings) - 1):
        start = swings[i]

        if start["type"] != start_type:
            continue

        for j in range(i + 1, len(swings)):
            end = swings[j]

            if end["type"] != end_type:
                continue

            if start_type == "LOW" and end_type == "HIGH":
                if end["price"] <= start["price"]:
                    continue

            if start_type == "HIGH" and end_type == "LOW":
                if start["price"] <= end["price"]:
                    continue

            candidates.append((start, end, _pair_score(start, end)))

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: (
            x[1]["index"],
            x[2],
        ),
        reverse=True,
    )

    print("")
    print("========== FIBONACCI CANDIDATES AUDIT ==========")
    print("PAIR:", start_type, "→", end_type)
    print("candidate_count:", len(candidates))
    print("selected_start_index:", candidates[0][0].get("index"))
    print("selected_start_price:", candidates[0][0].get("price"))
    print("selected_end_index:", candidates[0][1].get("index"))
    print("selected_end_price:", candidates[0][1].get("price"))
    print("selected_score:", round(candidates[0][2], 6))

    print("---- top 5 candidates ----")
    for n, item in enumerate(candidates[:5], start=1):
        start, end, score = item
        print(
            n,
            "start:",
            start.get("type"),
            start.get("index"),
            start.get("price"),
            "end:",
            end.get("type"),
            end.get("index"),
            end.get("price"),
            "score:",
            round(score, 6),
        )

    print("================================================")
    print("")

    return candidates[0][0], candidates[0][1]


def _fallback_high_low(candles):
    candles = _normalize_candles(candles)

    if not candles:
        return None, None

    recent = candles[-80:]
    high_price = max(c["high"] for c in recent)
    low_price = min(c["low"] for c in recent)

    print("")
    print("========== FIBONACCI FALLBACK AUDIT ==========")
    print("fallback_recent_count:", len(recent))
    print("fallback_high_price:", high_price)
    print("fallback_low_price:", low_price)
    print("==============================================")
    print("")

    return high_price, low_price


def find_auto_high_low_from_candles(candles):
    """
    旧仕様互換
    直近80本の高値安値を返す
    """
    if not candles or len(candles) < 30:
        return None, None

    return _fallback_high_low(candles)


def find_buy_sell_swing_pairs_from_candles(candles):
    """
    Ver15.1用
    BUY用 LOW→HIGH
    SELL用 HIGH→LOW
    を別々に探す
    """
    if not candles or len(candles) < 30:
        return None, None

    swings = _find_swings(candles, window=3)
    swings = _remove_noise(swings)

    print("")
    print("========== FIBONACCI SWINGS AUDIT ==========")
    print("candles_count:", len(candles))
    print("swings_count:", len(swings))
    print("---- latest 10 swings ----")

    for swing in swings[-10:]:
        print(
            swing.get("type"),
            "index:",
            swing.get("index"),
            "price:",
            swing.get("price"),
            "strength:",
            round(swing.get("strength", 0), 6),
        )

    print("============================================")
    print("")

    buy_pair = _latest_direction_pair(swings, "LOW", "HIGH")
    sell_pair = _latest_direction_pair(swings, "HIGH", "LOW")

    clean = _normalize_candles(candles)
    recent = clean[-80:]

    if buy_pair is None and recent:
        low_index = min(range(len(recent)), key=lambda i: recent[i]["low"])
        after_low = recent[low_index:]
        if after_low:
            high_item = max(after_low, key=lambda c: c["high"])
            low_item = recent[low_index]

            if high_item["high"] > low_item["low"]:
                buy_pair = (
                    {"type": "LOW", "index": low_item["index"], "price": low_item["low"], "strength": 0},
                    {"type": "HIGH", "index": high_item["index"], "price": high_item["high"], "strength": 0},
                )

                print("")
                print("========== FIBONACCI BUY FALLBACK PAIR ==========")
                print("BUY fallback LOW index:", low_item["index"])
                print("BUY fallback LOW price:", low_item["low"])
                print("BUY fallback HIGH index:", high_item["index"])
                print("BUY fallback HIGH price:", high_item["high"])
                print("=================================================")
                print("")

    if sell_pair is None and recent:
        high_index = max(range(len(recent)), key=lambda i: recent[i]["high"])
        after_high = recent[high_index:]
        if after_high:
            low_item = min(after_high, key=lambda c: c["low"])
            high_item = recent[high_index]

            if high_item["high"] > low_item["low"]:
                sell_pair = (
                    {"type": "HIGH", "index": high_item["index"], "price": high_item["high"], "strength": 0},
                    {"type": "LOW", "index": low_item["index"], "price": low_item["low"], "strength": 0},
                )

                print("")
                print("========== FIBONACCI SELL FALLBACK PAIR ==========")
                print("SELL fallback HIGH index:", high_item["index"])
                print("SELL fallback HIGH price:", high_item["high"])
                print("SELL fallback LOW index:", low_item["index"])
                print("SELL fallback LOW price:", low_item["low"])
                print("==================================================")
                print("")

    print_pair_audit("BUY_PAIR LOW→HIGH", buy_pair)
    print_pair_audit("SELL_PAIR HIGH→LOW", sell_pair)

    return buy_pair, sell_pair


def calculate_auto_fibonacci_from_candles(candles):
    """
    旧仕様互換用
    戻り値：fib, high_price, low_price
    """
    if not candles or len(candles) < 30:
        return None, None, None

    high_price, low_price = find_auto_high_low_from_candles(candles)

    if high_price is None or low_price is None:
        return None, None, None

    fib = calculate_fibonacci(high_price, low_price)

    return fib, high_price, low_price


def calculate_auto_dual_fibonacci_from_candles(candles):
    """
    Ver15.1用
    BUY用スイングとSELL用スイングを別々に検出
    戻り値：
    buy_fib, sell_fib, swing_high, swing_low
    """
    if not candles or len(candles) < 30:
        return None, None, None, None

    print("")
    print("========== AUTO DUAL FIBONACCI AUDIT START ==========")
    print("candles_count:", len(candles))
    print("=====================================================")
    print("")

    buy_pair, sell_pair = find_buy_sell_swing_pairs_from_candles(candles)

    buy_fib = None
    sell_fib = None

    swing_high = None
    swing_low = None

    if buy_pair is not None:
        buy_low, buy_high = buy_pair
        buy_fib = calculate_buy_fibonacci(
            buy_low["price"],
            buy_high["price"],
        )
        swing_low = buy_low["price"]
        swing_high = buy_high["price"]

        print("")
        print("========== BUY FIBONACCI SOURCE AUDIT ==========")
        print("BUY low_index:", buy_low.get("index"))
        print("BUY low_price:", buy_low.get("price"))
        print("BUY high_index:", buy_high.get("index"))
        print("BUY high_price:", buy_high.get("price"))
        print("================================================")
        print("")

    if sell_pair is not None:
        sell_high, sell_low = sell_pair
        sell_fib = calculate_sell_fibonacci(
            sell_high["price"],
            sell_low["price"],
        )

        print("")
        print("========== SELL FIBONACCI SOURCE AUDIT ==========")
        print("SELL high_index:", sell_high.get("index"))
        print("SELL high_price:", sell_high.get("price"))
        print("SELL low_index:", sell_low.get("index"))
        print("SELL low_price:", sell_low.get("price"))
        print("=================================================")
        print("")

        if swing_high is None:
            swing_high = sell_high["price"]
        if swing_low is None:
            swing_low = sell_low["price"]

    if buy_fib is None or sell_fib is None:
        high_price, low_price = _fallback_high_low(candles)

        if high_price is None or low_price is None:
            return None, None, None, None

        if buy_fib is None:
            buy_fib = calculate_buy_fibonacci(low_price, high_price)
            print("")
            print("BUY fib used fallback high/low")
            print("fallback low_price:", low_price)
            print("fallback high_price:", high_price)
            print("")

        if sell_fib is None:
            sell_fib = calculate_sell_fibonacci(high_price, low_price)
            print("")
            print("SELL fib used fallback high/low")
            print("fallback high_price:", high_price)
            print("fallback low_price:", low_price)
            print("")

        if swing_high is None:
            swing_high = high_price
        if swing_low is None:
            swing_low = low_price

    print_fibonacci_audit("BUY_FIB_RESULT", buy_fib)
    print_fibonacci_audit("SELL_FIB_RESULT", sell_fib)

    print("")
    print("========== AUTO DUAL FIBONACCI AUDIT END ==========")
    print("return_swing_high:", swing_high)
    print("return_swing_low:", swing_low)
    print("===================================================")
    print("")

    return buy_fib, sell_fib, swing_high, swing_low


def calculate_auto_fibonacci(prices):
    """
    旧仕様互換用
    戻り値：fib, high_price, low_price
    """
    if not prices or len(prices) < 10:
        return None, None, None

    high_price = max(prices[-80:])
    low_price = min(prices[-80:])

    fib = calculate_fibonacci(high_price, low_price)

    return fib, high_price, low_price


def calculate_auto_dual_fibonacci(prices):
    """
    価格リスト用の簡易版
    """
    if not prices or len(prices) < 10:
        return None, None, None, None

    high_price = max(prices[-80:])
    low_price = min(prices[-80:])

    buy_fib = calculate_buy_fibonacci(low_price, high_price)
    sell_fib = calculate_sell_fibonacci(high_price, low_price)

    return buy_fib, sell_fib, high_price, low_price


def nearest_fibonacci(price, fib):
    if not fib:
        return "", None

    nearest_name = ""
    nearest_price = None
    nearest_diff = float("inf")

    for level, value in fib.items():
        diff = abs(price - value)

        if diff < nearest_diff:
            nearest_diff = diff
            nearest_name = level
            nearest_price = value

    return nearest_name, nearest_price