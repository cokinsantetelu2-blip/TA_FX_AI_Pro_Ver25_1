# atr.py
# USDJPY_Fibo_AI Ver12.6

import pandas as pd


def calculate_atr(candles, period=14):
    """
    ATR(Average True Range)を計算
    戻り値:
        atr値(float) または None
    """

    if not candles or len(candles) < period + 1:
        return None

    try:
        df = pd.DataFrame(candles)

        rename = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
        }

        df.rename(columns=rename, inplace=True)

        high = df["high"].astype(float)
        low = df["low"].astype(float)
        close = df["close"].astype(float)

        prev_close = close.shift(1)

        tr = pd.concat(
            [
                high - low,
                (high - prev_close).abs(),
                (low - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        atr = tr.rolling(period).mean()

        value = atr.iloc[-1]

        if pd.isna(value):
            return None

        return round(float(value), 3)

    except Exception:
        return None


def judge_atr(atr):

    if atr is None:
        return "ATR取得失敗", 0

    # USDJPY 1H向け初期設定
    if atr >= 0.180:
        return "非常に活発", 15

    elif atr >= 0.120:
        return "十分な値動き", 10

    elif atr >= 0.080:
        return "普通", 5

    else:
        return "ボラ不足", -15