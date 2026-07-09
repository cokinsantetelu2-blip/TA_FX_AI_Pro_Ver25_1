# scanner.py
# TA FX AI Pro Ver25.1
# Telegram表示数値一致版
# AI採点監査ログ補正版
# 修正対象：scanner.py のみ
# 目的：補正前AI・補正後AI・Telegram表示AIスコアのズレを正しく監査する

import settings
from main import main
from notify import send_notification, send_photo
from ranking_engine import apply_ranking_scores


def safe_text(value, default="-"):
    if value is None or value == "":
        return default
    return str(value)


def safe_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def safe_bool(value):
    try:
        return bool(value)
    except Exception:
        return False


def get_price_digits(symbol):
    symbol_text = str(symbol).upper()

    if "XAU" in symbol_text or "GOLD" in symbol_text:
        return 2

    if "BTC" in symbol_text or "ETH" in symbol_text:
        return 2

    if "XRP" in symbol_text:
        return 5

    if "JPY" in symbol_text:
        return 3

    return 5


def safe_number_text(value, symbol=None, default="-"):
    if value is None or value == "":
        return default

    if value == "-":
        return default

    try:
        digits = get_price_digits(symbol)
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def format_trade_fields(result):
    symbol = result.get("symbol", settings.SYMBOL if hasattr(settings, "SYMBOL") else "")

    result["current_price"] = safe_number_text(result.get("current_price"), symbol)
    result["entry"] = safe_number_text(result.get("entry"), symbol)
    result["sl"] = safe_number_text(result.get("sl"), symbol)
    result["tp1"] = safe_number_text(result.get("tp1"), symbol)
    result["tp2"] = safe_number_text(result.get("tp2"), symbol)

    return result


def get_signal_rank(signal):
    signal_text = str(signal).upper()
    signal_raw = str(signal)

    if "BUY" in signal_text or "SELL" in signal_text or "買" in signal_raw or "売" in signal_raw:
        return 3
    if "候補" in signal_raw:
        return 2
    if "WAIT" in signal_text or "見送り" in signal_raw:
        return 0
    return 1


def cap_score_by_signal(score, signal):
    signal_text = str(signal).upper()
    signal_raw = str(signal)

    if "WAIT" in signal_text or "見送り" in signal_raw:
        return min(score, 69)
    if "候補" in signal_raw:
        return min(score, 84)
    return score


def get_rank_text(score, signal):
    signal_text = str(signal).upper()
    signal_raw = str(signal)

    if "WAIT" in signal_text or "見送り" in signal_raw:
        if score >= 65:
            return "見送り強め"
        if score >= 55:
            return "見送り"
        return "弱い"

    if score >= 90:
        return "最強"
    if score >= 80:
        return "強い"
    if score >= 70:
        return "候補"
    if score >= 60:
        return "弱い"
    return "見送り"


def get_rank_power(rank_text):
    rank_map = {
        "最強": 5,
        "強い": 4,
        "候補": 3,
        "見送り強め": 2,
        "弱い": 1,
        "見送り": 0,
        "エラー": -1,
    }
    return rank_map.get(str(rank_text), 0)


def get_win_rate_number(score, signal):
    signal_text = str(signal).upper()
    signal_raw = str(signal)

    if "WAIT" in signal_text or "見送り" in signal_raw:
        if score >= 65:
            return 62
        if score >= 55:
            return 58
        return 50

    if score >= 90:
        return 82
    if score >= 80:
        return 75
    if score >= 70:
        return 68
    if score >= 60:
        return 62
    return 50


def get_wait_penalty(signal):
    signal_text = str(signal).upper()
    signal_raw = str(signal)

    if "WAIT" in signal_text or "見送り" in signal_raw:
        return -1
    return 0


def get_rank_icon(index):
    icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    if index < len(icons):
        return icons[index]
    return f"{index + 1}."


def extract_trade_value(result, *keys):
    for key in keys:
        value = result.get(key)
        if value is not None and value != "":
            return value

    trade = result.get("trade")
    if isinstance(trade, dict):
        for key in keys:
            value = trade.get(key)
            if value is not None and value != "":
                return value

    trade_plan = result.get("trade_plan")
    if isinstance(trade_plan, dict):
        for key in keys:
            value = trade_plan.get(key)
            if value is not None and value != "":
                return value

    return "-"


def normalize_trade_fields(result):
    current_price = extract_trade_value(
        result,
        "current_price",
        "price",
        "now_price",
        "last_price",
    )

    entry = extract_trade_value(
        result,
        "entry",
        "entry_price",
    )

    stop = extract_trade_value(
        result,
        "stop",
        "sl",
        "stop_loss",
    )

    tp1 = extract_trade_value(
        result,
        "tp1",
        "take_profit1",
    )

    tp2 = extract_trade_value(
        result,
        "tp2",
        "take_profit2",
    )

    rr = extract_trade_value(
        result,
        "rr",
        "rr1",
        "risk_reward",
    )

    result["current_price"] = current_price
    result["entry"] = entry
    result["sl"] = stop
    result["tp1"] = tp1
    result["tp2"] = tp2
    result["rr"] = rr

    return result


def normalize_touch_fields(result):
    buy_touch_info = result.get("buy_touch_info")
    sell_touch_info = result.get("sell_touch_info")

    if not isinstance(buy_touch_info, dict):
        buy_touch_info = {
            "side": "BUY",
            "has_touch": False,
            "within_limit": False,
            "elapsed_bars": "-",
            "text": "BUY: フィボタッチなし",
        }

    if not isinstance(sell_touch_info, dict):
        sell_touch_info = {
            "side": "SELL",
            "has_touch": False,
            "within_limit": False,
            "elapsed_bars": "-",
            "text": "SELL: フィボタッチなし",
        }

    result["buy_touch_info"] = buy_touch_info
    result["sell_touch_info"] = sell_touch_info

    return result


def normalize_breakdown_fields(result):
    if not isinstance(result.get("score_breakdown"), dict):
        result["score_breakdown"] = {}

    if not isinstance(result.get("buy_score_breakdown"), dict):
        result["buy_score_breakdown"] = {}

    if not isinstance(result.get("sell_score_breakdown"), dict):
        result["sell_score_breakdown"] = {}

    return result


def get_chart_path(result):
    keys = [
        "chart",
        "chart_main",
        "chart_file",
        "chart_path",
        "image_path",
        "main_chart",
        "main_chart_file",
        "mobile_chart_file",
        "pro_chart_file",
    ]

    for key in keys:
        value = result.get(key)
        if value is not None and value != "":
            return value

    return None


def get_touch_info(result, side):
    key = "buy_touch_info" if side == "BUY" else "sell_touch_info"
    touch_info = result.get(key)

    if isinstance(touch_info, dict):
        return touch_info

    return {
        "side": side,
        "has_touch": False,
        "within_limit": False,
        "elapsed_bars": "-",
        "text": f"{side}: フィボタッチなし",
    }


def get_touch_text(result, side):
    touch_info = get_touch_info(result, side)

    elapsed = touch_info.get("elapsed_bars", "-")
    within_limit = safe_bool(touch_info.get("within_limit", False))
    has_touch = safe_bool(touch_info.get("has_touch", False))

    if not has_touch:
        return f"{side}: フィボタッチなし"

    if within_limit:
        return f"{side}: {elapsed}本経過 / 5本以内"

    return f"{side}: {elapsed}本経過 / 期限切れ"


def get_reversal_text(result, side):
    key = "buy_reversal" if side == "BUY" else "sell_reversal"
    reversal = result.get(key)

    if not isinstance(reversal, dict):
        return f"{side}: 反転確認データなし"

    text = safe_text(reversal.get("text"), "反転確認データなし")
    elapsed = reversal.get("elapsed_bars", None)
    reasons = reversal.get("reasons", [])

    if elapsed is not None and elapsed != "":
        text = f"{text} / {elapsed}本経過"

    if not isinstance(reasons, list):
        reasons = [str(reasons)]

    short_reasons = []
    for reason in reasons[:3]:
        short_reasons.append(f"・{safe_text(reason)}")

    reason_text = "\n".join(short_reasons)

    if reason_text:
        return f"{side}: {text}\n{reason_text}"

    return f"{side}: {text}"


def get_adopted_breakdown(result):
    adopted_side = safe_text(result.get("adopted_side", "WAIT"))

    if adopted_side == "BUY":
        breakdown = result.get("buy_score_breakdown")
        if isinstance(breakdown, dict):
            return breakdown

    if adopted_side == "SELL":
        breakdown = result.get("sell_score_breakdown")
        if isinstance(breakdown, dict):
            return breakdown

    breakdown = result.get("score_breakdown")
    if isinstance(breakdown, dict):
        return breakdown

    return {}


def get_breakdown_value(breakdown, key):
    if not isinstance(breakdown, dict):
        return 0

    return safe_int(breakdown.get(key, 0))


def print_score_audit(result):
    symbol = safe_text(result.get("symbol"))
    adopted_side = safe_text(result.get("adopted_side", "WAIT"))
    signal = safe_text(result.get("signal", "WAIT"))

    raw_score = safe_int(result.get("raw_score", result.get("score", 0)))
    telegram_score = safe_int(result.get("score", 0))
    buy_score = safe_int(result.get("buy_score", 0))
    sell_score = safe_int(result.get("sell_score", 0))

    breakdown = get_adopted_breakdown(result)

    fibo = get_breakdown_value(breakdown, "FIBO")
    reversal = get_breakdown_value(breakdown, "REVERSAL")
    rsi = get_breakdown_value(breakdown, "RSI")
    macd = get_breakdown_value(breakdown, "MACD")
    dow = get_breakdown_value(breakdown, "DOW")
    mtf = get_breakdown_value(breakdown, "MTF")
    candle = get_breakdown_value(breakdown, "CANDLE")
    atr = get_breakdown_value(breakdown, "ATR")
    cap = get_breakdown_value(breakdown, "CAP")
    score_engine_total = get_breakdown_value(breakdown, "TOTAL")

    if adopted_side == "BUY":
        side_total = buy_score
    elif adopted_side == "SELL":
        side_total = sell_score
    else:
        side_total = 0

    final_internal_total = telegram_score
    result_text = "OK" if final_internal_total == telegram_score else "NG"

    print("")
    print(f"========== {symbol} AI SCORE AUDIT ==========")
    print("Signal     :", signal)
    print("Adopted    :", adopted_side)
    print("")
    print(f"FIBO       {fibo:+}")
    print(f"REVERSAL   {reversal:+}")
    print(f"RSI        {rsi:+}")
    print(f"MACD       {macd:+}")
    print(f"DOW        {dow:+}")
    print(f"MTF        {mtf:+}")
    print(f"CANDLE     {candle:+}")
    print(f"ATR        {atr:+}")

    if cap != 0:
        print(f"CAP        {cap:+}")

    print("")
    print("BUY SCORE        :", buy_score)
    print("SELL SCORE       :", sell_score)
    print("採用側SCORE      :", side_total)
    print("score_engine合計 :", score_engine_total)
    print("補正前AI         :", raw_score)
    print("補正後AI         :", telegram_score)
    print("Telegram表示     :", telegram_score)
    print("RESULT           :", result_text)
    print("=============================================")
    print("")

    result["audit_total"] = final_internal_total
    result["audit_side_total"] = side_total
    result["audit_score_engine_total"] = score_engine_total
    result["audit_raw_score"] = raw_score
    result["audit_adjusted_score"] = telegram_score
    result["audit_telegram_score"] = telegram_score
    result["audit_result"] = result_text

    return result


def make_top5_message(top_results):
    message = f"""
🏆 {settings.APP_NAME} {settings.VERSION}
TOP5 Ranking
"""

    for i, result in enumerate(top_results):
        icon = get_rank_icon(i)

        symbol = safe_text(result.get("symbol"))
        score = safe_int(result.get("score", 0))
        raw_score = safe_int(result.get("raw_score", score))
        ranking_score = safe_int(result.get("ranking_score", 0))
        signal = safe_text(result.get("signal"))
        rank_text = safe_text(result.get("rank_text"))
        win_rate = safe_int(result.get("win_rate_number", 0))

        buy_score = safe_int(result.get("buy_score", 0))
        sell_score = safe_int(result.get("sell_score", 0))
        adopted_side = safe_text(result.get("adopted_side", "WAIT"))

        current_price = safe_text(result.get("current_price"))
        entry = safe_text(result.get("entry"))
        sl = safe_text(result.get("sl"))
        tp1 = safe_text(result.get("tp1"))
        tp2 = safe_text(result.get("tp2"))
        rr = safe_text(result.get("rr"))

        buy_touch_text = get_touch_text(result, "BUY")
        sell_touch_text = get_touch_text(result, "SELL")

        buy_reversal_text = get_reversal_text(result, "BUY")
        sell_reversal_text = get_reversal_text(result, "SELL")

        audit_result = safe_text(result.get("audit_result", "-"))
        audit_total = safe_int(result.get("audit_total", score))
        audit_raw_score = safe_int(result.get("audit_raw_score", raw_score))
        audit_adjusted_score = safe_int(result.get("audit_adjusted_score", score))

        message += f"""
{icon} {symbol}
AIスコア：{score}点
AI監査：{audit_result}
内部TOTAL：{audit_total}点
補正前AI：{audit_raw_score}点
補正後AI：{audit_adjusted_score}点
BUY SCORE：{buy_score}点
SELL SCORE：{sell_score}点
採用方向：{adopted_side}
Ranking Score：{ranking_score}
判定：{signal}
強度：{rank_text}
勝率目安：{win_rate}%
現在価格：{current_price}
Entry：{entry}
SL：{sl}
TP1：{tp1}
TP2：{tp2}
RR：{rr}

フィボ時間管理AI
{buy_touch_text}
{sell_touch_text}

反転確認AI
{buy_reversal_text}
{sell_reversal_text}
"""

        if raw_score != score:
            message += f"AI補正：{raw_score}点 → {score}点\n"

    return message


def make_top1_caption(top1):
    symbol = safe_text(top1.get("symbol"))
    score = safe_int(top1.get("score", 0))
    buy_score = safe_int(top1.get("buy_score", 0))
    sell_score = safe_int(top1.get("sell_score", 0))
    adopted_side = safe_text(top1.get("adopted_side", "WAIT"))
    signal = safe_text(top1.get("signal", "WAIT"))

    current_price = safe_text(top1.get("current_price"))
    entry = safe_text(top1.get("entry"))
    sl = safe_text(top1.get("sl"))
    tp1 = safe_text(top1.get("tp1"))
    tp2 = safe_text(top1.get("tp2"))
    rr = safe_text(top1.get("rr"))

    ranking_score = safe_int(top1.get("ranking_score", 0))

    buy_touch_text = get_touch_text(top1, "BUY")
    sell_touch_text = get_touch_text(top1, "SELL")

    buy_reversal_text = get_reversal_text(top1, "BUY")
    sell_reversal_text = get_reversal_text(top1, "SELL")

    audit_result = safe_text(top1.get("audit_result", "-"))
    audit_total = safe_int(top1.get("audit_total", score))
    audit_raw_score = safe_int(top1.get("audit_raw_score", score))
    audit_adjusted_score = safe_int(top1.get("audit_adjusted_score", score))

    caption = f"""
🥇 TOP1 メインチャート
{symbol}

AI SCORE : {score}
AI AUDIT : {audit_result}
INTERNAL TOTAL : {audit_total}
RAW AI : {audit_raw_score}
ADJUSTED AI : {audit_adjusted_score}
BUY SCORE : {buy_score}
SELL SCORE : {sell_score}
Ranking Score : {ranking_score}
採用方向 : {adopted_side}
判定 : {signal}

現在価格 : {current_price}
Entry : {entry}
SL : {sl}
TP1 : {tp1}
TP2 : {tp2}
RR : {rr}

フィボ時間管理AI
{buy_touch_text}
{sell_touch_text}

反転確認AI
{buy_reversal_text}
{sell_reversal_text}
"""

    return caption


def scan_all_symbols():

    print("====================================")
    print(f"{settings.APP_NAME} {settings.VERSION} Scanner 起動")
    print("Ver25.1 AI採点監査ログ補正版")
    print("送信内容：TOP5ランキング + TOP1メインチャートのみ")
    print("内部計算値・ターミナル表示・Telegram表示の一致確認対応")
    print("====================================")

    results = []

    for symbol_name in settings.TARGET_SYMBOLS:

        print("")
        print("------------------------------------")
        print("分析開始:", symbol_name)
        print("------------------------------------")

        try:
            settings.set_symbol(symbol_name)

            result = main()

            if result is not None:
                result["symbol"] = symbol_name

                raw_score = safe_int(result.get("score", 0))
                signal = result.get("signal", "WAIT")

                adjusted_score = cap_score_by_signal(raw_score, signal)

                rank_text = result.get("rank_text")
                win_rate_number = result.get("win_rate_number")

                if not rank_text:
                    rank_text = get_rank_text(adjusted_score, signal)

                if win_rate_number is None or win_rate_number == "":
                    win_rate_number = get_win_rate_number(adjusted_score, signal)
                else:
                    win_rate_number = safe_int(win_rate_number)

                result["raw_score"] = raw_score
                result["score"] = adjusted_score
                result["signal_rank"] = get_signal_rank(signal)
                result["rank_text"] = rank_text
                result["rank_power"] = get_rank_power(rank_text)
                result["win_rate_number"] = win_rate_number
                result["wait_penalty"] = get_wait_penalty(signal)

                result["buy_score"] = safe_int(result.get("buy_score", 0))
                result["sell_score"] = safe_int(result.get("sell_score", 0))
                result["adopted_side"] = safe_text(result.get("adopted_side", "WAIT"))

                if not isinstance(result.get("buy_reversal"), dict):
                    result["buy_reversal"] = {}
                if not isinstance(result.get("sell_reversal"), dict):
                    result["sell_reversal"] = {}

                result = normalize_trade_fields(result)
                result = normalize_touch_fields(result)
                result = normalize_breakdown_fields(result)
                result = format_trade_fields(result)
                result = print_score_audit(result)

                results.append(result)

            print("分析完了:", symbol_name)

        except Exception as e:
            print("分析エラー:", symbol_name, e)

            results.append({
                "symbol": symbol_name,
                "status": "ERROR",
                "raw_score": 0,
                "score": 0,
                "buy_score": 0,
                "sell_score": 0,
                "adopted_side": "WAIT",
                "signal_rank": 0,
                "signal": "ERROR",
                "rank_text": "エラー",
                "rank_power": -1,
                "win_rate_number": 0,
                "wait_penalty": -1,
                "ranking_score": 0,
                "audit_total": 0,
                "audit_side_total": 0,
                "audit_score_engine_total": 0,
                "audit_raw_score": 0,
                "audit_adjusted_score": 0,
                "audit_telegram_score": 0,
                "audit_result": "ERROR",
                "score_breakdown": {},
                "buy_score_breakdown": {},
                "sell_score_breakdown": {},
                "current_price": "-",
                "entry": "-",
                "sl": "-",
                "tp1": "-",
                "tp2": "-",
                "rr": "-",
                "buy_touch_info": {
                    "side": "BUY",
                    "has_touch": False,
                    "within_limit": False,
                    "elapsed_bars": "-",
                    "text": "BUY: フィボタッチなし",
                },
                "sell_touch_info": {
                    "side": "SELL",
                    "has_touch": False,
                    "within_limit": False,
                    "elapsed_bars": "-",
                    "text": "SELL: フィボタッチなし",
                },
                "buy_reversal": {},
                "sell_reversal": {},
                "message": "",
                "error": str(e),
            })

    print("")
    print("====================================")
    print("スキャン完了")
    print("====================================")

    results = apply_ranking_scores(results)

    if results:
        top5 = results[:5]
        top1 = top5[0]

        print("")
        print("====================================")
        print("TOP5 Ranking")
        print("====================================")

        for i, r in enumerate(top5):
            icon = get_rank_icon(i)

            print(icon, r.get("symbol"))
            print("AI :", r.get("score"))
            print("AI監査 :", r.get("audit_result"))
            print("内部TOTAL :", r.get("audit_total"))
            print("補正前AI :", r.get("audit_raw_score"))
            print("補正後AI :", r.get("audit_adjusted_score"))
            print("BUY SCORE :", r.get("buy_score"))
            print("SELL SCORE :", r.get("sell_score"))
            print("採用方向 :", r.get("adopted_side"))
            print("Ranking Score :", r.get("ranking_score"))
            print("Signal :", r.get("signal"))
            print("強度 :", r.get("rank_text"))
            print("勝率目安 :", f"{r.get('win_rate_number')}%")
            print("現在価格 :", r.get("current_price"))
            print("Entry :", r.get("entry"))
            print("SL :", r.get("sl"))
            print("TP1 :", r.get("tp1"))
            print("TP2 :", r.get("tp2"))
            print("RR :", r.get("rr"))
            print("フィボ時間管理AI")
            print(get_touch_text(r, "BUY"))
            print(get_touch_text(r, "SELL"))
            print("反転確認AI")
            print(get_reversal_text(r, "BUY"))
            print(get_reversal_text(r, "SELL"))
            print("------------------------------------")

        top5_message = make_top5_message(top5)
        send_notification(top5_message)

        print("Telegram送信完了: TOP5ランキング")

        chart_path = get_chart_path(top1)

        if chart_path:
            caption = make_top1_caption(top1)
            send_photo(chart_path, caption)
            print("Telegram送信完了: TOP1メインチャート", chart_path)
        else:
            print("TOP1メインチャートなし: 画像送信スキップ")

    return results


if __name__ == "__main__":
    scan_all_symbols()