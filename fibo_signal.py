# fibo_signal.py
# TA FX AI Pro Ver25.1
# BUY / SELL フィボタッチ判定対応版
# Ver25 監査ログ追加版
#
# 目的:
# ・TOP5で経過本数が0本へ戻る原因調査
# ・judge_dual_fibo_signal() が touch=True を毎回返していないか監査
# ・フィボ価格が毎回変わっていないか監査
#
# 注意:
# ・Ver25は監査のみ
# ・判定ロジックは変更しない
# ・新機能追加なし


TARGET_LEVELS = [
    "38.2%",
    "50.0%",
    "61.8%",
    "78.6%",
]


def safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def get_fibo_tolerance(current_price):
    """
    通貨ペアごとの価格差をざっくり吸収する許容幅
    USDJPYなどは約0.050
    BTCやGOLDなど高価格商品は少し広め
    """
    price = safe_float(current_price)

    if price is None:
        return 0.050

    if price >= 10000:
        return price * 0.001
    if price >= 1000:
        return price * 0.0008
    if price >= 100:
        return 0.050
    if price >= 10:
        return 0.020

    return 0.005


def print_fibo_audit_log(title, current_price, fib, result):
    """
    Ver25監査用ログ
    判定ロジックには一切影響させない
    """

    price = safe_float(current_price)
    tolerance = get_fibo_tolerance(price)

    print("")
    print("========== FIBO SIGNAL AUDIT ==========")
    print("TITLE:", title)
    print("current_price:", price)
    print("tolerance:", round(tolerance, 6))
    print("touch:", result.get("touch"))
    print("判定level:", result.get("level"))
    print("level_price:", result.get("price"))
    print("diff:", result.get("diff"))
    print("---------- fib levels ----------")

    if not fib:
        print("fib: None / empty")
    else:
        for level in TARGET_LEVELS:
            fib_price = safe_float(fib.get(level))
            if fib_price is None:
                print(level, ": None")
            else:
                diff = abs(price - fib_price) if price is not None else None
                print(
                    level,
                    "price:",
                    round(fib_price, 6),
                    "diff:",
                    round(diff, 6) if diff is not None else None,
                    "within:",
                    diff <= tolerance if diff is not None else False
                )

    print("========================================")
    print("")


def judge_fibo_touch_detail(current_price, fib):
    """
    指定フィボに現在価格がタッチしているか判定
    戻り値:
    {
        "touch": True/False,
        "level": "61.8%",
        "price": 157.123,
        "diff": 0.012,
        "tolerance": 0.050
    }
    """
    price = safe_float(current_price)

    if price is None or not fib:
        return {
            "touch": False,
            "level": "",
            "price": None,
            "diff": None,
            "tolerance": get_fibo_tolerance(current_price),
        }

    tolerance = get_fibo_tolerance(price)

    best_level = ""
    best_price = None
    best_diff = None

    for level in TARGET_LEVELS:
        if level not in fib:
            continue

        fib_price = safe_float(fib[level])

        if fib_price is None:
            continue

        diff = abs(price - fib_price)

        if best_diff is None or diff < best_diff:
            best_level = level
            best_price = fib_price
            best_diff = diff

    if best_diff is not None and best_diff <= tolerance:
        return {
            "touch": True,
            "level": best_level,
            "price": round(best_price, 3),
            "diff": round(best_diff, 3),
            "tolerance": round(tolerance, 3),
        }

    return {
        "touch": False,
        "level": best_level,
        "price": round(best_price, 3) if best_price is not None else None,
        "diff": round(best_diff, 3) if best_diff is not None else None,
        "tolerance": round(tolerance, 3),
    }


def judge_buy_fibo_signal(current_price, buy_fib):
    """
    BUY用フィボタッチ判定
    """
    return judge_fibo_touch_detail(current_price, buy_fib)


def judge_sell_fibo_signal(current_price, sell_fib):
    """
    SELL用フィボタッチ判定
    """
    return judge_fibo_touch_detail(current_price, sell_fib)


def judge_dual_fibo_signal(current_price, buy_fib, sell_fib):
    """
    BUY / SELL 両方のフィボタッチを判定
    Ver25監査ログ追加
    """
    buy_result = judge_buy_fibo_signal(current_price, buy_fib)
    sell_result = judge_sell_fibo_signal(current_price, sell_fib)

    print_fibo_audit_log("BUY_FIB", current_price, buy_fib, buy_result)
    print_fibo_audit_log("SELL_FIB", current_price, sell_fib, sell_result)

    buy_touch = buy_result.get("touch", False)
    sell_touch = sell_result.get("touch", False)

    print("")
    print("========== DUAL FIBO RESULT AUDIT ==========")
    print("current_price:", current_price)
    print("buy_touch:", buy_touch)
    print("buy_level:", buy_result.get("level"))
    print("buy_price:", buy_result.get("price"))
    print("buy_diff:", buy_result.get("diff"))
    print("sell_touch:", sell_touch)
    print("sell_level:", sell_result.get("level"))
    print("sell_price:", sell_result.get("price"))
    print("sell_diff:", sell_result.get("diff"))
    print("============================================")
    print("")

    if buy_touch and sell_touch:
        buy_diff = buy_result.get("diff")
        sell_diff = sell_result.get("diff")

        if buy_diff is not None and sell_diff is not None:
            if buy_diff <= sell_diff:
                main_side = "BUY"
            else:
                main_side = "SELL"
        else:
            main_side = "BOTH"

    elif buy_touch:
        main_side = "BUY"

    elif sell_touch:
        main_side = "SELL"

    else:
        main_side = "WAIT"

    print("")
    print("========== MAIN FIBO SIDE AUDIT ==========")
    print("main_side:", main_side)
    print("==========================================")
    print("")

    return {
        "side": main_side,
        "buy": buy_result,
        "sell": sell_result,
        "buy_touch": buy_touch,
        "sell_touch": sell_touch,
    }


def judge_fibo_signal(current_price, fib):
    """
    旧仕様互換
    これまで通り True / False を返す
    """
    result = judge_fibo_touch_detail(current_price, fib)
    return result.get("touch", False)