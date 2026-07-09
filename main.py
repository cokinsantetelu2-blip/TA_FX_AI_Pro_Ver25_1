# main.py
# TA FX AI Pro Ver25.0
# TouchTracker 時刻ベースバー番号対応版
# AI採点監査対応版

import inspect
import pandas as pd
import settings

from price import get_current_price, get_price_history, get_ohlc_history
from indicator import get_indicators
from multi_timeframe import get_multi_timeframe
from fibonacci import calculate_auto_dual_fibonacci_from_candles
from fibo_signal import judge_dual_fibo_signal
from dow import judge_dow
from candlestick import judge_candlestick
from risk import calculate_trade_plan
import risk
print("読み込み中 risk.py =", risk.__file__)
from chart_pro import create_pro_chart_image
from reversal_engine import judge_reversal
from touch_tracker import TouchTracker

from chart_mobile import (
    create_mobile_chart_1h,
    create_mobile_chart_4h,
    create_mobile_chart_1d,
)

from ai_judge_v123 import (
    judge_ema_slope,
    judge_ema75_slope,
    judge_macd_cross,
    judge_macd_histogram,
    judge_adx,
    judge_candle_pattern,
    calculate_ai_score_v123,
)

from score_engine import (
    judge_buy_sell_score,
    calculate_win_rate,
)


TOUCH_TRACKER = TouchTracker()


def get_candle_time_value(candle):
    if not isinstance(candle, dict):
        return None

    for key in ["timestamp", "time", "datetime", "date"]:
        if key in candle and candle.get(key) is not None:
            return candle.get(key)

    return None


def get_bar_index_from_candle(candle, fallback_index):
    """
    ローソク足の時刻から絶対バー番号を作る。
    1時間足なので timestamp秒 // 3600。
    これで毎回 len(candles)-1 が固定でも、時間が進めば 1本ずつ増える。
    """

    try:
        time_value = get_candle_time_value(candle)

        if time_value is None:
            return fallback_index

        dt = pd.to_datetime(time_value, errors="coerce")

        if pd.isna(dt):
            return fallback_index

        timestamp = int(dt.timestamp())
        return int(timestamp // 3600)

    except Exception:
        return fallback_index


def calculate_ema_series(prices, span):
    if not prices or len(prices) < span:
        return []

    series = pd.Series(prices)
    ema = series.ewm(span=span, adjust=False).mean()
    return ema.tolist()


def calculate_macd_series(prices):
    if not prices or len(prices) < 35:
        return [], [], []

    series = pd.Series(prices)
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    return macd.tolist(), signal.tolist(), hist.tolist()


def get_latest_value(values):
    if not values:
        return None

    try:
        return values[-1]
    except Exception:
        return None


def calculate_adx_from_candles(candles, period=14):
    if not candles or len(candles) < period + 2:
        return None

    highs = []
    lows = []
    closes = []

    for c in candles:
        try:
            highs.append(float(c["high"]))
            lows.append(float(c["low"]))
            closes.append(float(c["close"]))
        except Exception:
            return None

    plus_dm = []
    minus_dm = []
    tr_list = []

    for i in range(1, len(candles)):
        high_diff = highs[i] - highs[i - 1]
        low_diff = lows[i - 1] - lows[i]

        plus_dm.append(high_diff if high_diff > low_diff and high_diff > 0 else 0)
        minus_dm.append(low_diff if low_diff > high_diff and low_diff > 0 else 0)

        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        tr_list.append(tr)

    tr_series = pd.Series(tr_list)
    plus_dm_series = pd.Series(plus_dm)
    minus_dm_series = pd.Series(minus_dm)

    atr = tr_series.rolling(window=period).mean()
    plus_di = 100 * (plus_dm_series.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm_series.rolling(window=period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    latest_adx = adx.iloc[-1]

    if pd.isna(latest_adx):
        return None

    return round(float(latest_adx), 2)


def calculate_atr_from_candles(candles, period=14):
    if not candles or len(candles) < period + 1:
        return None

    tr_list = []

    for i in range(1, len(candles)):
        try:
            high = float(candles[i]["high"])
            low = float(candles[i]["low"])
            prev_close = float(candles[i - 1]["close"])

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )

            tr_list.append(tr)

        except Exception:
            return None

    if len(tr_list) < period:
        return None

    atr = sum(tr_list[-period:]) / period

    return round(float(atr), 5)


def calculate_atr_average_from_candles(candles, period=14, average_days=30, candles_per_day=24):
    if not candles:
        return None

    need_bars = period + (average_days * candles_per_day)

    if len(candles) < period + candles_per_day:
        return None

    target_candles = candles[-need_bars:] if len(candles) >= need_bars else candles

    tr_list = []

    for i in range(1, len(target_candles)):
        try:
            high = float(target_candles[i]["high"])
            low = float(target_candles[i]["low"])
            prev_close = float(target_candles[i - 1]["close"])

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )

            tr_list.append(tr)

        except Exception:
            return None

    if len(tr_list) < period:
        return None

    atr_values = []

    for i in range(period, len(tr_list) + 1):
        atr = sum(tr_list[i - period:i]) / period
        atr_values.append(atr)

    if not atr_values:
        return None

    average_atr = sum(atr_values) / len(atr_values)

    return round(float(average_atr), 5)


def judge_atr_volatility_text(atr_current, atr_average):
    if atr_current is None or atr_average is None:
        return "ATR平均比較: データ不足"

    try:
        if float(atr_average) <= 0:
            return "ATR平均比較: データ不足"

        ratio = float(atr_current) / float(atr_average)

        if ratio < 0.8:
            return f"ATR平均比較: 低ボラ / {ratio:.2f}倍"
        elif ratio > 1.2:
            return f"ATR平均比較: 高ボラ / {ratio:.2f}倍"
        else:
            return f"ATR平均比較: 通常ボラ / {ratio:.2f}倍"

    except Exception:
        return "ATR平均比較: データ不足"


def format_price(value):
    if value is None:
        return "-"

    try:
        symbol_name = str(settings.SYMBOL_NAME).upper()

        if "JPY" in symbol_name:
            return f"{float(value):.3f}"

        if "XAU" in symbol_name or "GOLD" in symbol_name:
            return f"{float(value):.2f}"

        if symbol_name in ["BTC", "ETH"]:
            return f"{float(value):.2f}"

        if symbol_name == "XRP":
            return f"{float(value):.5f}"

        return f"{float(value):.5f}"

    except Exception:
        return str(value)


def get_timeframe_candles(period, interval):
    try:
        data = get_ohlc_history(period=period, interval=interval)
        if data and len(data) > 0:
            return data
        return []
    except TypeError:
        return []
    except Exception as e:
        print(f"時間足取得失敗 {period} {interval}:", e)
        return []


def call_chart_function_safely(func, kwargs):
    try:
        params = inspect.signature(func).parameters
        safe_kwargs = {}

        for key, value in kwargs.items():
            if key in params:
                safe_kwargs[key] = value

        return func(**safe_kwargs)

    except Exception as e:
        print("チャート関数実行失敗:", e)
        return None


def call_reversal_safely(
    direction,
    rsi14,
    macd,
    macd_signal,
    macd_hist,
    candles,
    touch_info
):
    if not touch_info or not touch_info.get("within_limit", False):
        elapsed = "-"

        if isinstance(touch_info, dict):
            elapsed = touch_info.get("elapsed_bars", "-")

        return {
            "ok": False,
            "score": 0,
            "text": f"フィボタッチ5本以内ではないため反転確認なし（{elapsed}本経過）",
            "reasons": [
                "フィボタッチ期限外",
                f"{elapsed}本経過",
                "5本以内のみ反転確認AIを実行",
            ],
            "elapsed_bars": elapsed,
            "within_limit": False,
        }

    kwargs = {
        "direction": direction,
        "rsi14": rsi14,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "candles": candles,
        "touch_info": touch_info,
    }

    try:
        params = inspect.signature(judge_reversal).parameters
        safe_kwargs = {}

        for key, value in kwargs.items():
            if key in params:
                safe_kwargs[key] = value

        result = judge_reversal(**safe_kwargs)

        if isinstance(result, dict):
            result["elapsed_bars"] = touch_info.get("elapsed_bars", "-")
            result["within_limit"] = touch_info.get("within_limit", False)
            return result

        return {
            "ok": False,
            "score": 0,
            "text": "反転確認AI結果不明",
            "reasons": ["反転確認AIの戻り値が不正"],
            "elapsed_bars": touch_info.get("elapsed_bars", "-"),
            "within_limit": touch_info.get("within_limit", False),
        }

    except Exception as e:
        return {
            "ok": False,
            "score": 0,
            "text": "反転確認AIエラー",
            "reasons": [str(e)],
            "elapsed_bars": touch_info.get("elapsed_bars", "-"),
            "within_limit": touch_info.get("within_limit", False),
        }


def make_touch_info_default(side):
    return {
        "side": side,
        "has_touch": False,
        "within_limit": False,
        "expired": False,
        "elapsed_bars": "-",
        "touch_bar_index": None,
        "current_bar_index": None,
        "level": "-",
        "price": None,
        "diff": None,
        "text": f"{side}: フィボタッチなし",
        "display_text": "フィボタッチなし",
    }


def normalize_touch_status(side, tracker_status, current_bar_index, fibo_touch=None):
    info = make_touch_info_default(side)
    info["current_bar_index"] = current_bar_index

    if isinstance(fibo_touch, dict):
        info["price"] = fibo_touch.get("price", None)
        info["diff"] = fibo_touch.get("diff", None)

    if not isinstance(tracker_status, dict):
        return info

    bars = tracker_status.get("bars", None)
    valid = tracker_status.get("valid", False)
    expired = tracker_status.get("expired", False)
    level = tracker_status.get("level", None)
    display_text = tracker_status.get("display_text", tracker_status.get("text", "フィボタッチなし"))

    if bars is None:
        info["text"] = f"{side}: フィボタッチなし"
        info["display_text"] = "フィボタッチなし"
        return info

    info["has_touch"] = True
    info["within_limit"] = bool(valid)
    info["expired"] = bool(expired)
    info["elapsed_bars"] = bars
    info["touch_bar_index"] = current_bar_index - bars
    info["level"] = level if level is not None else "-"
    info["display_text"] = display_text

    if valid:
        info["text"] = f"{side}: {bars}本経過 / 5本以内"
    else:
        info["text"] = f"{side}: {bars}本経過 / 期限切れ"

    return info


def update_touch_tracker(side, symbol_name, fibo_touch, current_bar_index):
    side = str(side).upper()
    symbol_name = str(symbol_name).upper()

    touched_now = False
    level = "-"
    price = None
    diff = None

    if isinstance(fibo_touch, dict):
        touched_now = bool(fibo_touch.get("touch", False))
        level = fibo_touch.get("level", "-")
        price = fibo_touch.get("price", None)
        diff = fibo_touch.get("diff", None)

    def get_tracker_snapshot():
        """
        TouchTracker内部状態の監査用。
        touch_tracker.py側の作りが変わっても落ちないように、
        よくある保存名を順番に見る。
        """

        snapshot = {
            "touch_index": None,
            "in_touch_area": None,
            "level": None,
            "raw": None,
        }

        try:
            for attr_name in [
                "state",
                "touch_state",
                "touch_states",
                "data",
                "tracker",
                "trackers",
            ]:
                raw_state = getattr(TOUCH_TRACKER, attr_name, None)

                if not isinstance(raw_state, dict):
                    continue

                snapshot["raw"] = raw_state

                target = None

                if symbol_name in raw_state and isinstance(raw_state.get(symbol_name), dict):
                    symbol_state = raw_state.get(symbol_name, {})
                    if side in symbol_state and isinstance(symbol_state.get(side), dict):
                        target = symbol_state.get(side)

                if target is None and side in raw_state and isinstance(raw_state.get(side), dict):
                    target = raw_state.get(side)

                if target is None:
                    continue

                snapshot["touch_index"] = target.get("touch_index", target.get("index", None))
                snapshot["in_touch_area"] = target.get("in_touch_area", target.get("is_touching", None))
                snapshot["level"] = target.get("touch_level", target.get("level", None))
                return snapshot

        except Exception as e:
            snapshot["raw"] = f"snapshot_error: {e}"

        return snapshot

    def get_status_safely():
        try:
            status = TOUCH_TRACKER.get_status(
                current_index=current_bar_index,
                side=side,
                symbol=symbol_name,
                max_bars=5,
            )

            if isinstance(status, dict):
                return status

            return {}

        except Exception as e:
            return {
                "error": str(e),
            }

    before_snapshot = get_tracker_snapshot()
    before_status = get_status_safely()

    before_touch_index = before_snapshot.get("touch_index", None)
    before_bars = before_status.get("bars", None)

    print(
        f"[TouchAudit BEFORE] {symbol_name} {side} "
        f"current_bar_index={current_bar_index} "
        f"touched_now={touched_now} "
        f"level={level} "
        f"before_touch_index={before_touch_index} "
        f"before_bars={before_bars} "
        f"in_touch_area={before_snapshot.get('in_touch_area')} "
        f"valid={before_status.get('valid')} "
        f"expired={before_status.get('expired')}"
    )

    TOUCH_TRACKER.update_touch_state(
        candle_index=current_bar_index,
        side=side,
        is_touching=touched_now,
        level=level,
        symbol=symbol_name,
        max_bars=5,
    )

    after_snapshot = get_tracker_snapshot()

    tracker_status = TOUCH_TRACKER.get_status(
        current_index=current_bar_index,
        side=side,
        symbol=symbol_name,
        max_bars=5,
    )

    after_touch_index = after_snapshot.get("touch_index", None)
    after_bars = None

    if isinstance(tracker_status, dict):
        after_bars = tracker_status.get("bars", None)

    print(
        f"[TouchAudit AFTER] {symbol_name} {side} "
        f"current_bar_index={current_bar_index} "
        f"touched_now={touched_now} "
        f"level={level} "
        f"before_touch_index={before_touch_index} "
        f"after_touch_index={after_touch_index} "
        f"before_bars={before_bars} "
        f"after_bars={after_bars} "
        f"in_touch_area={after_snapshot.get('in_touch_area')} "
        f"valid={tracker_status.get('valid') if isinstance(tracker_status, dict) else None} "
        f"expired={tracker_status.get('expired') if isinstance(tracker_status, dict) else None}"
    )

    touch_info = normalize_touch_status(
        side=side,
        tracker_status=tracker_status,
        current_bar_index=current_bar_index,
        fibo_touch=fibo_touch,
    )

    if price is not None:
        touch_info["price"] = price

    if diff is not None:
        touch_info["diff"] = diff

    if touched_now:
        touch_info["level"] = level
        touch_info["has_touch"] = True

    print(
        f"[TouchTracker] {symbol_name} {side} "
        f"current_bar_index={current_bar_index} "
        f"has_touch={touch_info.get('has_touch')} "
        f"elapsed={touch_info.get('elapsed_bars')} "
        f"within_limit={touch_info.get('within_limit')} "
        f"expired={touch_info.get('expired')} "
        f"level={touch_info.get('level')}"
    )

    return touch_info


def make_fibo_text(side, fib_touch):
    if not fib_touch:
        return f"{side}: 判定なし"

    touch = fib_touch.get("touch", False)
    level = fib_touch.get("level", "")
    price = fib_touch.get("price", None)
    diff = fib_touch.get("diff", None)

    if touch:
        return f"{side}: {level} タッチ / {price} / 差 {diff}"

    return f"{side}: タッチなし / 最寄 {level} / {price} / 差 {diff}"


def make_touch_text(side, touch_info):
    if not isinstance(touch_info, dict):
        return f"{side}: タッチ管理データなし"

    return touch_info.get("text", f"{side}: タッチ管理データなし")


def make_reversal_text(side, reversal):
    if not isinstance(reversal, dict):
        return f"{side}反転確認: データなし"

    text = reversal.get("text", "-")
    elapsed = reversal.get("elapsed_bars", "-")
    return f"{side}反転確認: {text} / {elapsed}本経過"


def create_chart_safely(
    candles,
    candles_4h,
    candles_1d,
    fib,
    buy_fib,
    sell_fib,
    current_price,
    signal,
    score,
    buy_score,
    sell_score,
    adopted_side,
    win_rate_text,
    rsi14,
    dow,
    mtf,
    entry_text,
    stop_text,
    tp1_text,
    tp2_text,
    rr_text,
    reason_text,
    chart_filename,
    buy_touch_info=None,
    sell_touch_info=None,
):
    chart_kwargs = {
        "candles": candles,
        "candles_4h": candles_4h,
        "candles_1d": candles_1d,
        "fib": fib,
        "buy_fib": buy_fib,
        "sell_fib": sell_fib,
        "current_price": current_price,
        "signal": signal,
        "ai_score": score,
        "score": score,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "adopted_side": adopted_side,
        "win_rate_text": win_rate_text,
        "rsi14": rsi14,
        "dow_text": f"Dow: {dow}",
        "mtf_text": f"MTF: 1H {mtf['1H']} / 4H {mtf['4H']} / 1D {mtf['1D']}",
        "entry_text": entry_text,
        "stop_text": stop_text,
        "tp1_text": tp1_text,
        "tp2_text": tp2_text,
        "rr_text": rr_text,
        "reason_text": reason_text,
        "buy_touch_info": buy_touch_info,
        "sell_touch_info": sell_touch_info,
        "filename": chart_filename,
    }

    return call_chart_function_safely(create_pro_chart_image, chart_kwargs)


def create_mobile_charts_safely(
    candles_1h,
    candles_4h,
    candles_1d,
    fib,
    buy_fib,
    sell_fib,
    current_price,
    signal,
    score,
    buy_score,
    sell_score,
    adopted_side,
    win_rate_text,
    rsi14,
    dow,
    mtf,
    entry_text,
    stop_text,
    tp1_text,
    tp2_text,
    symbol_name,
    buy_touch_info=None,
    sell_touch_info=None,
):
    common_kwargs = {
        "fib": fib,
        "buy_fib": buy_fib,
        "sell_fib": sell_fib,
        "current_price": current_price,
        "signal": signal,
        "ai_score": score,
        "score": score,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "adopted_side": adopted_side,
        "win_rate_text": win_rate_text,
        "rsi14": rsi14,
        "dow_text": f"Dow: {dow}",
        "mtf_text": f"MTF: 1H {mtf['1H']} / 4H {mtf['4H']} / 1D {mtf['1D']}",
        "entry_text": entry_text,
        "stop_text": stop_text,
        "tp1_text": tp1_text,
        "tp2_text": tp2_text,
        "buy_touch_info": buy_touch_info,
        "sell_touch_info": sell_touch_info,
    }

    chart_1h = None
    chart_4h = None
    chart_1d = None

    try:
        kwargs_1h = common_kwargs.copy()
        kwargs_1h["candles"] = candles_1h
        kwargs_1h["filename"] = f"chart_{symbol_name}_1h.png"
        chart_1h = call_chart_function_safely(create_mobile_chart_1h, kwargs_1h)
        print("1Hスマホチャート:", chart_1h)
    except Exception as e:
        print("1Hスマホチャート作成失敗:", e)

    try:
        kwargs_4h = common_kwargs.copy()
        kwargs_4h["candles"] = candles_4h
        kwargs_4h["filename"] = f"chart_{symbol_name}_4h.png"
        chart_4h = call_chart_function_safely(create_mobile_chart_4h, kwargs_4h)
        print("4Hスマホチャート:", chart_4h)
    except Exception as e:
        print("4Hスマホチャート作成失敗:", e)

    try:
        kwargs_1d = common_kwargs.copy()
        kwargs_1d["candles"] = candles_1d
        kwargs_1d["filename"] = f"chart_{symbol_name}_1d.png"
        chart_1d = call_chart_function_safely(create_mobile_chart_1d, kwargs_1d)
        print("1Dスマホチャート:", chart_1d)
    except Exception as e:
        print("1Dスマホチャート作成失敗:", e)

    return chart_1h, chart_4h, chart_1d


def make_error_result(symbol_name, error_text):
    return {
        "symbol": symbol_name,
        "status": "ERROR",
        "error": error_text,
        "score": 0,
        "buy_score": 0,
        "sell_score": 0,
        "adopted_side": "WAIT",
        "signal": "WAIT",
        "win_rate": "勝率目安：低め",
        "price": None,
        "current_price": None,
        "entry": "-",
        "sl": "-",
        "tp1": "-",
        "tp2": "-",
        "rr": "-",
        "trade": {},
        "chart": None,
        "chart_main": None,
        "chart_1h": None,
        "chart_4h": None,
        "chart_1d": None,
        "message": "",
        "buy_fib": None,
        "sell_fib": None,
        "fibo_side": "WAIT",
        "buy_fibo_touch": {},
        "sell_fibo_touch": {},
        "buy_touch_info": make_touch_info_default("BUY"),
        "sell_touch_info": make_touch_info_default("SELL"),
        "buy_reversal": {},
        "sell_reversal": {},
        "score_breakdown": {},
        "buy_score_breakdown": {},
        "sell_score_breakdown": {},
        "adx_value": None,
        "adx_text": "データ不足",
        "atr_value": None,
        "atr_current": None,
        "atr_average": None,
        "atr_volatility_text": "ATR平均比較: データ不足",
        "ema20_text": "データ不足",
        "ema75_text": "データ不足",
        "macd_cross_text": "データ不足",
        "macd_hist_text": "データ不足",
        "candle_text": "データ不足",
        "mtf": {
            "1H": "不明",
            "4H": "不明",
            "1D": "不明",
        },
        "rsi14": None,
        "dow": "データ不足",
    }


def main():

    symbol_name = settings.SYMBOL_NAME
    chart_filename = f"chart_{symbol_name}.png"

    print("===================================")
    print(f"{settings.APP_NAME} {settings.VERSION} 起動")
    print("分析銘柄:", symbol_name)
    print("Ver25.0 AI採点監査対応版")
    print("通貨別 + BUY/SELL別 + 5本以内反転確認AI")
    print("===================================")

    current_price = get_current_price()
    prices = get_price_history()

    candles = get_timeframe_candles(period="30d", interval="1h")

    if not candles:
        candles = get_ohlc_history()

    candles_4h = get_timeframe_candles(period="60d", interval="4h")
    candles_1d = get_timeframe_candles(period="1y", interval="1d")

    print("1Hローソク足本数:", len(candles) if candles else 0)
    print("4Hローソク足本数:", len(candles_4h) if candles_4h else 0)
    print("1Dローソク足本数:", len(candles_1d) if candles_1d else 0)

    if not prices or not candles:
        print("価格取得失敗:", symbol_name)
        return make_error_result(symbol_name, "価格取得失敗")

    if len(candles) < 20:
        print("1Hローソク足データ不足:", symbol_name)
        return make_error_result(symbol_name, "1Hローソク足データ不足")

    if not candles_4h:
        candles_4h = candles

    if not candles_1d:
        candles_1d = candles

    fallback_bar_index = len(candles) - 1
    current_bar_index = get_bar_index_from_candle(candles[-1], fallback_bar_index)

    print("最新ローソク足time:", candles[-1].get("time", "-"))
    print("current_bar_index:", current_bar_index)

    buy_fib, sell_fib, swing_high, swing_low = calculate_auto_dual_fibonacci_from_candles(candles)

    if buy_fib is None or sell_fib is None:
        print("フィボナッチ計算失敗:", symbol_name)
        return make_error_result(symbol_name, "フィボナッチ計算失敗")

    fib = buy_fib

    indicators = get_indicators(prices)

    ema20 = indicators["ema20"]
    ema75 = indicators["ema75"]
    rsi14 = indicators["rsi14"]

    mtf = get_multi_timeframe()
    dow = judge_dow(prices)

    dual_fibo = judge_dual_fibo_signal(current_price, buy_fib, sell_fib)
    fibo_side = dual_fibo.get("side", "WAIT")
    buy_fibo_touch = dual_fibo.get("buy", {})
    sell_fibo_touch = dual_fibo.get("sell", {})

    buy_touch_info = update_touch_tracker(
        side="BUY",
        symbol_name=symbol_name,
        fibo_touch=buy_fibo_touch,
        current_bar_index=current_bar_index,
    )

    sell_touch_info = update_touch_tracker(
        side="SELL",
        symbol_name=symbol_name,
        fibo_touch=sell_fibo_touch,
        current_bar_index=current_bar_index,
    )

    candle_ok, candle_name_old = judge_candlestick(prices)

    ema20_series = calculate_ema_series(prices, 20)
    ema75_series = calculate_ema_series(prices, 75)

    ema_slope_text, ema_slope_score = judge_ema_slope(ema20_series)
    ema75_slope_text, ema75_slope_score = judge_ema75_slope(ema75_series)

    macd_series, macd_signal_series, macd_hist_series = calculate_macd_series(prices)

    latest_macd = get_latest_value(macd_series)
    latest_macd_signal = get_latest_value(macd_signal_series)
    latest_macd_hist = get_latest_value(macd_hist_series)

    macd_cross_text, macd_cross_score = judge_macd_cross(
        macd_series,
        macd_signal_series
    )

    macd_hist_text, macd_hist_score = judge_macd_histogram(macd_hist_series)

    adx_value = calculate_adx_from_candles(candles)
    adx_text, adx_score = judge_adx(adx_value)

    atr_current = calculate_atr_from_candles(candles)
    atr_average = calculate_atr_average_from_candles(candles)
    atr_volatility_text = judge_atr_volatility_text(atr_current, atr_average)

    print("現在ATR:", atr_current)
    print("30日平均ATR:", atr_average)
    print(atr_volatility_text)

    candle_text, candle_score = judge_candle_pattern(candles)

    buy_reversal = call_reversal_safely(
        direction="BUY",
        rsi14=rsi14,
        macd=latest_macd,
        macd_signal=latest_macd_signal,
        macd_hist=latest_macd_hist,
        candles=candles,
        touch_info=buy_touch_info,
    )

    sell_reversal = call_reversal_safely(
        direction="SELL",
        rsi14=rsi14,
        macd=latest_macd,
        macd_signal=latest_macd_signal,
        macd_hist=latest_macd_hist,
        candles=candles,
        touch_info=sell_touch_info,
    )

    score_result = judge_buy_sell_score(
        buy_fibo_touch=buy_fibo_touch,
        sell_fibo_touch=sell_fibo_touch,
        rsi14=rsi14,
        macd_cross_text=macd_cross_text,
        macd_hist_text=macd_hist_text,
        dow_text=dow,
        mtf=mtf,
        candle_text=candle_text,
        buy_reversal=buy_reversal,
        sell_reversal=sell_reversal,
        buy_touch_info=buy_touch_info,
        sell_touch_info=sell_touch_info,
        atr=atr_current,
        atr_average=atr_average,
        atr_status=atr_volatility_text,
    )

    base_direction_score = score_result.get("score", 0)
    signal = score_result.get("signal", "WAIT")
    adopted_side = score_result.get("adopted_side", score_result.get("side", "WAIT"))
    buy_score = score_result.get("buy_score", 0)
    sell_score = score_result.get("sell_score", 0)
    buy_reasons = score_result.get("buy_reasons", [])
    sell_reasons = score_result.get("sell_reasons", [])
    reasons = score_result.get("reasons", [])

    score_breakdown = score_result.get("score_breakdown", {})
    buy_score_breakdown = score_result.get("buy_score_breakdown", {})
    sell_score_breakdown = score_result.get("sell_score_breakdown", {})

    score = base_direction_score

    if adopted_side == "WAIT" or signal == "WAIT":
        score = 0
        signal = "WAIT"
        adopted_side = "WAIT"

        if not reasons:
            reasons = [
                "BUYフィボ未タッチ、または5本以内反転未確認",
                "SELLフィボ未タッチ、または5本以内反転未確認",
                "フィボタッチなし、期限切れ、または反転未確認のため見送り",
            ]

    score = max(score, base_direction_score)

    if adopted_side == "WAIT":
        score = 0

    if isinstance(score_breakdown, dict):
        score_breakdown["TOTAL"] = score

    win_rate_text = calculate_win_rate(score)

    reasons.append(f"BUY SCORE: {buy_score}")
    reasons.append(f"SELL SCORE: {sell_score}")
    reasons.append(f"採用方向: {adopted_side}")
    reasons.append(make_fibo_text("BUYフィボ", buy_fibo_touch))
    reasons.append(make_fibo_text("SELLフィボ", sell_fibo_touch))
    reasons.append(make_touch_text("BUYタッチ管理", buy_touch_info))
    reasons.append(make_touch_text("SELLタッチ管理", sell_touch_info))
    reasons.append(make_reversal_text("BUY", buy_reversal))
    reasons.append(make_reversal_text("SELL", sell_reversal))
    reasons.append(f"EMA20傾き: {ema_slope_text}")
    reasons.append(f"EMA75傾き: {ema75_slope_text}")
    reasons.append(f"MACDクロス: {macd_cross_text}")
    reasons.append(f"MACD勢い: {macd_hist_text}")
    reasons.append(f"ADX: {adx_text}")
    reasons.append(f"ローソク足強化: {candle_text}")
    reasons.append(f"現在ATR: {atr_current}")
    reasons.append(f"30日平均ATR: {atr_average}")
    reasons.append(atr_volatility_text)

    if adopted_side == "BUY":
        trade_signal = "BUY候補"
    elif adopted_side == "SELL":
        trade_signal = "SELL候補"
    else:
        trade_signal = "WAIT"

    trade = calculate_trade_plan(
        current_price=current_price,
        signal=trade_signal,
        symbol=symbol_name,
        atr=atr_current,
        atr_average=atr_average,
    )

    reason_text = "AI理由: " + " / ".join(reasons)

    entry_text = f"Entry: {trade['entry']}"
    stop_text = f"SL: {trade['stop']}"
    tp1_text = f"TP1: {trade['tp1']}"
    tp2_text = f"TP2: {trade['tp2']}"
    rr_text = f"RR1: {trade['rr1']} / RR2: {trade['rr2']}"

    chart_file = create_chart_safely(
        candles=candles,
        candles_4h=candles_4h,
        candles_1d=candles_1d,
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
        current_price=current_price,
        signal=signal,
        score=score,
        buy_score=buy_score,
        sell_score=sell_score,
        adopted_side=adopted_side,
        win_rate_text=win_rate_text,
        rsi14=rsi14,
        dow=dow,
        mtf=mtf,
        entry_text=entry_text,
        stop_text=stop_text,
        tp1_text=tp1_text,
        tp2_text=tp2_text,
        rr_text=rr_text,
        reason_text=reason_text,
        chart_filename=chart_filename,
        buy_touch_info=buy_touch_info,
        sell_touch_info=sell_touch_info,
    )

    print("メインチャート:", chart_file)
    print("★★★ スマホチャート作成処理に入りました ★★★")

    chart_1h, chart_4h, chart_1d = create_mobile_charts_safely(
        candles_1h=candles,
        candles_4h=candles_4h,
        candles_1d=candles_1d,
        fib=fib,
        buy_fib=buy_fib,
        sell_fib=sell_fib,
        current_price=current_price,
        signal=signal,
        score=score,
        buy_score=buy_score,
        sell_score=sell_score,
        adopted_side=adopted_side,
        win_rate_text=win_rate_text,
        rsi14=rsi14,
        dow=dow,
        mtf=mtf,
        entry_text=entry_text,
        stop_text=stop_text,
        tp1_text=tp1_text,
        tp2_text=tp2_text,
        symbol_name=symbol_name,
        buy_touch_info=buy_touch_info,
        sell_touch_info=sell_touch_info,
    )

    message = f"""
🏆 {settings.APP_NAME} {settings.VERSION}
Today's Best Trade

銘柄
{symbol_name}

現在価格
{format_price(current_price)}

AIスコア
{score}点

BUY SCORE
{buy_score}点

SELL SCORE
{sell_score}点

採用方向
{adopted_side}

{win_rate_text}

判定
{signal}

フィボ判定
{fibo_side}

======== フィボ時間管理AI ========

BUYタッチ管理
{buy_touch_info.get("text", "-")}

BUY経過本数
{buy_touch_info.get("elapsed_bars", "-")}本

BUY有効判定
{"5本以内" if buy_touch_info.get("within_limit", False) else "期限外または未タッチ"}

SELLタッチ管理
{sell_touch_info.get("text", "-")}

SELL経過本数
{sell_touch_info.get("elapsed_bars", "-")}本

SELL有効判定
{"5本以内" if sell_touch_info.get("within_limit", False) else "期限外または未タッチ"}

======== 反転確認AI ========

BUY反転確認
{buy_reversal.get("text", "-")}

BUY反転理由
{chr(10).join(buy_reversal.get("reasons", []))}

SELL反転確認
{sell_reversal.get("text", "-")}

SELL反転理由
{chr(10).join(sell_reversal.get("reasons", []))}

理由
{chr(10).join(reasons)}

ローソク足
{candle_text}

ダウ理論
{dow}

マルチタイムフレーム
1H : {mtf['1H']}
4H : {mtf['4H']}
1D : {mtf['1D']}

RSI14
{rsi14}

ADX
{adx_value} / {adx_text}

======== ATR平均比較AI ========

現在ATR
{atr_current}

30日平均ATR
{atr_average}

ボラティリティ判定
{atr_volatility_text}

======== BUYフィボ 安値→高値 ========

スイング安値 : {format_price(swing_low)}
スイング高値 : {format_price(swing_high)}

BUY 38.2% : {format_price(buy_fib.get("38.2%"))}
BUY 50.0% : {format_price(buy_fib.get("50.0%"))}
BUY 61.8% : {format_price(buy_fib.get("61.8%"))}
BUY 78.6% : {format_price(buy_fib.get("78.6%"))}

======== SELLフィボ 高値→安値 ========

スイング高値 : {format_price(swing_high)}
スイング安値 : {format_price(swing_low)}

SELL 38.2% : {format_price(sell_fib.get("38.2%"))}
SELL 50.0% : {format_price(sell_fib.get("50.0%"))}
SELL 61.8% : {format_price(sell_fib.get("61.8%"))}
SELL 78.6% : {format_price(sell_fib.get("78.6%"))}

======== トレードプラン ========

方向 : {trade['direction']}
Entry : {trade['entry']}
SL : {trade['stop']}
TP1 : {trade['tp1']}
TP2 : {trade['tp2']}
RR1 : {trade['rr1']}
RR2 : {trade['rr2']}
"""

    print("分析完了:", symbol_name)

    return {
        "symbol": symbol_name,
        "status": "OK",
        "score": score,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "adopted_side": adopted_side,
        "signal": signal,
        "win_rate": win_rate_text,

        "score_breakdown": score_breakdown,
        "buy_score_breakdown": buy_score_breakdown,
        "sell_score_breakdown": sell_score_breakdown,

        "price": current_price,
        "current_price": current_price,

        "entry": trade["entry"],
        "entry_price": trade["entry"],
        "sl": trade["stop"],
        "stop": trade["stop"],
        "stop_loss": trade["stop"],
        "tp1": trade["tp1"],
        "tp2": trade["tp2"],
        "rr": f"{trade['rr1']} / {trade['rr2']}",
        "rr1": trade["rr1"],
        "rr2": trade["rr2"],
        "trade": trade,
        "trade_plan": trade,

        "chart": chart_file,
        "chart_main": chart_file,
        "chart_1h": chart_1h,
        "chart_4h": chart_4h,
        "chart_1d": chart_1d,

        "message": message,

        "fib": fib,
        "buy_fib": buy_fib,
        "sell_fib": sell_fib,
        "fibo_side": fibo_side,
        "buy_fibo_touch": buy_fibo_touch,
        "sell_fibo_touch": sell_fibo_touch,
        "swing_high": swing_high,
        "swing_low": swing_low,

        "buy_touch_info": buy_touch_info,
        "sell_touch_info": sell_touch_info,

        "buy_reversal": buy_reversal,
        "sell_reversal": sell_reversal,

        "adx_value": adx_value,
        "adx_text": adx_text,

        "atr_value": atr_current,
        "atr_current": atr_current,
        "atr_average": atr_average,
        "atr_volatility_text": atr_volatility_text,

        "ema20_text": ema_slope_text,
        "ema75_text": ema75_slope_text,
        "macd_cross_text": macd_cross_text,
        "macd_hist_text": macd_hist_text,
        "candle_text": candle_text,
        "mtf": mtf,
        "rsi14": rsi14,
        "dow": dow,

        "buy_reasons": buy_reasons,
        "sell_reasons": sell_reasons,
        "reasons": reasons,
    }


if __name__ == "__main__":
    main()