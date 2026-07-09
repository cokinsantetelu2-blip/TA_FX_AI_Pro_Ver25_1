# chart.py

import pandas as pd
import mplfinance as mpf


def is_number(value):
    return isinstance(value, (int, float))


def create_chart_image(candles, fib=None, signal=None, trade=None, filename="usd_jpy_chart.png"):

    if not candles or len(candles) < 20:
        print("チャート作成失敗")
        return None

    df = pd.DataFrame(candles)

    df["time"] = pd.to_datetime(df["time"])
    df.set_index("time", inplace=True)

    df.rename(columns={
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close"
    }, inplace=True)

    df = df[["Open", "High", "Low", "Close"]].dropna()

    close = df["Close"]

    df["EMA20"] = close.ewm(span=20, adjust=False).mean()
    df["EMA75"] = close.ewm(span=75, adjust=False).mean()

    current_price = df["Close"].iloc[-1]

    addplots = [
        mpf.make_addplot(df["EMA20"], width=1.3),
        mpf.make_addplot(df["EMA75"], width=1.3),
    ]

    # BUY / SELL 矢印
    if signal:
        arrow_data = pd.Series(index=df.index, dtype="float64")
        last_time = df.index[-1]

        if "買い" in signal or "BUY" in signal:
            arrow_data.loc[last_time] = df["Low"].iloc[-1] - 0.15
            addplots.append(
                mpf.make_addplot(
                    arrow_data,
                    type="scatter",
                    marker="^",
                    markersize=500,
                    color="lime"
                )
            )

        elif "売り" in signal or "SELL" in signal:
            arrow_data.loc[last_time] = df["High"].iloc[-1] + 0.15
            addplots.append(
                mpf.make_addplot(
                    arrow_data,
                    type="scatter",
                    marker="v",
                    markersize=500,
                    color="red"
                )
            )

    hlines = []

    # フィボナッチライン
    if fib:
        for value in fib.values():
            if is_number(value):
                hlines.append(value)

    # 現在価格ライン
    hlines.append(current_price)

    # Entry / SL / TP ライン
    if trade:
        for key in ["entry", "stop", "tp1", "tp2"]:
            value = trade.get(key)
            if is_number(value):
                hlines.append(value)

    try:
        mpf.plot(
            df,
            type="candle",
            style="nightclouds",
            figratio=(16, 9),
            figscale=1.5,
            title="USDJPY_Fibo_AI Ver7.3.1 TradingView Style",
            ylabel="Price",
            addplot=addplots,
            hlines=dict(
                hlines=hlines,
                linestyle="--",
                linewidths=0.9
            ),
            tight_layout=True,
            savefig=dict(
                fname=filename,
                dpi=170,
                bbox_inches="tight"
            )
        )

        print("Ver7.3.1 チャート保存完了")
        return filename

    except Exception as e:
        print("チャートエラー:", e)
        return None