# multi_timeframe.py

import yfinance as yf

SYMBOL = "JPY=X"


def get_trend(interval, period):

    data = yf.download(
        SYMBOL,
        interval=interval,
        period=period,
        progress=False,
        auto_adjust=False
    )

    if data.empty:
        return "取得失敗"

    close = data["Close"]

    if hasattr(close, "columns"):
        close = close.iloc[:, 0]

    close = close.dropna().tolist()

    if len(close) < 75:
        return "データ不足"

    ema20 = sum(close[-20:]) / 20
    ema75 = sum(close[-75:]) / 75

    if ema20 > ema75:
        return "📈 上昇"

    elif ema20 < ema75:
        return "📉 下降"

    else:
        return "➡ 横ばい"


def get_multi_timeframe():

    return {
        "1H": get_trend("1h", "5d"),
        "4H": get_trend("4h", "30d"),
        "1D": get_trend("1d", "6mo")
    }