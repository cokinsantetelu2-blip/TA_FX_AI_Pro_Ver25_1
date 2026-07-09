# price.py
# TA FX AI Pro Ver13
# 12銘柄対応版

import yfinance as yf
import settings


def round_price(price):
    try:
        price = float(price)

        # 円絡みFX
        if "JPY" in settings.SYMBOL_NAME:
            return round(price, 3)

        # 仮想通貨
        if settings.SYMBOL_NAME in ["BTC", "ETH"]:
            return round(price, 2)

        if settings.SYMBOL_NAME == "XRP":
            return round(price, 4)

        # その他FX
        return round(price, 5)

    except Exception:
        return price


def get_ohlc_history(period=None, interval=None):
    if period is None:
        period = settings.PERIOD

    if interval is None:
        interval = settings.INTERVAL

    try:
        data = yf.download(
            settings.SYMBOL,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False
        )
    except Exception as e:
        print("価格取得エラー:", e)
        return []

    if data is None or data.empty:
        print("価格データが取得できません:", settings.SYMBOL_NAME, settings.SYMBOL)
        return []

    candles = []

    for index, row in data.iterrows():
        try:
            open_price = row["Open"]
            high_price = row["High"]
            low_price = row["Low"]
            close_price = row["Close"]

            if hasattr(open_price, "iloc"):
                open_price = open_price.iloc[0]
                high_price = high_price.iloc[0]
                low_price = low_price.iloc[0]
                close_price = close_price.iloc[0]

            candles.append({
                "time": str(index),
                "open": round_price(open_price),
                "high": round_price(high_price),
                "low": round_price(low_price),
                "close": round_price(close_price)
            })

        except Exception:
            continue

    return candles


def get_price_history(period=None, interval=None):
    candles = get_ohlc_history(period, interval)

    if not candles:
        return []

    return [candle["close"] for candle in candles]


def get_current_price():
    prices = get_price_history()

    if not prices:
        return None

    return prices[-1]


def find_swing_points(candles, window=3):

    swing_highs = []
    swing_lows = []

    if not candles or len(candles) < window * 2 + 1:
        return swing_highs, swing_lows

    for i in range(window, len(candles) - window):

        current_high = candles[i]["high"]
        current_low = candles[i]["low"]

        left = candles[i - window:i]
        right = candles[i + 1:i + window + 1]

        left_highs = [c["high"] for c in left]
        right_highs = [c["high"] for c in right]

        left_lows = [c["low"] for c in left]
        right_lows = [c["low"] for c in right]

        if current_high > max(left_highs) and current_high > max(right_highs):
            swing_highs.append({
                "index": i,
                "time": candles[i]["time"],
                "price": current_high
            })

        if current_low < min(left_lows) and current_low < min(right_lows):
            swing_lows.append({
                "index": i,
                "time": candles[i]["time"],
                "price": current_low
            })

    return swing_highs, swing_lows


def get_latest_swing_pair(candles):

    swing_highs, swing_lows = find_swing_points(candles)

    if not swing_highs or not swing_lows:
        return None, None

    latest_high = swing_highs[-1]
    latest_low = swing_lows[-1]

    return latest_high, latest_low