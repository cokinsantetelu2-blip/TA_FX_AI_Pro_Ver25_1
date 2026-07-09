# settings.py
# TA FX AI Pro Ver13

MARKETS = {
    # FX
    "USDJPY": "JPY=X",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "AUDJPY": "AUDJPY=X",

    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",

    "USDCHF": "CHF=X",
    "USDCAD": "CAD=X",

    # Crypto
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "XRP": "XRP-USD",
}

TARGET_SYMBOLS = [
    "USDJPY",
    "EURJPY",
    "GBPJPY",
    "AUDJPY",
    "EURUSD",
    "GBPUSD",
    "AUDUSD",
    "USDCHF",
    "USDCAD",
    "BTC",
    "ETH",
    "XRP",
]

SYMBOL_NAME = "USDJPY"
SYMBOL = MARKETS[SYMBOL_NAME]

INTERVAL = "1h"
PERIOD = "10d"

ENABLE_TELEGRAM = True

CHART_FILE = "chart_pro.png"

APP_NAME = "TA FX AI Pro"
VERSION = "Ver13"


def set_symbol(symbol_name):
    global SYMBOL_NAME
    global SYMBOL

    if symbol_name not in MARKETS:
        raise ValueError(f"未対応の銘柄です: {symbol_name}")

    SYMBOL_NAME = symbol_name
    SYMBOL = MARKETS[symbol_name]


def print_settings():
    print("====================================")
    print(APP_NAME, VERSION)
    print("====================================")
    print("分析銘柄 :", SYMBOL_NAME)
    print("Yahooコード :", SYMBOL)
    print("時間足 :", INTERVAL)
    print("取得期間 :", PERIOD)
    print("====================================")