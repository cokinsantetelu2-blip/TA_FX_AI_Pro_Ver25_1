# telegram_bot.py
# TA FX AI Pro Ver14.0
# Telegram Remote Control
# スマホから /scan /status /help で操作

import time
import requests
import notify
from scanner import scan_all_symbols


BOT_TOKEN = notify.TOKEN
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

LAST_SCAN_TIME = "-"
IS_SCANNING = False


def send_message(chat_id, text):
    try:
        url = f"{BASE_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        requests.post(url, data=data, timeout=20)
    except Exception as e:
        print("Telegram返信エラー:", e)


def get_updates(offset=None):
    try:
        url = f"{BASE_URL}/getUpdates"
        params = {
            "timeout": 30
        }

        if offset is not None:
            params["offset"] = offset

        response = requests.get(url, params=params, timeout=40)
        data = response.json()

        if not data.get("ok"):
            print("getUpdatesエラー:", data)
            return []

        return data.get("result", [])

    except Exception as e:
        print("更新取得エラー:", e)
        return []


def get_now_text():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def handle_start(chat_id):
    send_message(
        chat_id,
        "TA FX AI Pro Ver14 起動中\n\n"
        "使えるコマンド\n"
        "/scan  全銘柄スキャン\n"
        "/status  Bot状態確認\n"
        "/help  使い方"
    )


def handle_help(chat_id):
    send_message(
        chat_id,
        "使い方\n\n"
        "/scan\n"
        "12銘柄を分析して、TOP5ランキングとTOP1チャートをTelegramへ送信します。\n\n"
        "/status\n"
        "Botが起動しているか確認します。\n\n"
        "/help\n"
        "使い方を表示します。"
    )


def handle_status(chat_id):
    global LAST_SCAN_TIME
    global IS_SCANNING

    if IS_SCANNING:
        status_text = "スキャン中"
    else:
        status_text = "待機中"

    send_message(
        chat_id,
        "TA FX AI Pro Ver14\n\n"
        f"状態：{status_text}\n"
        f"最終スキャン：{LAST_SCAN_TIME}\n"
        "監視銘柄：12銘柄\n"
        "コマンド：/scan"
    )


def handle_scan(chat_id):
    global LAST_SCAN_TIME
    global IS_SCANNING

    if IS_SCANNING:
        send_message(chat_id, "現在スキャン中です。完了まで少し待ってね。")
        return

    IS_SCANNING = True
    send_message(chat_id, "スキャン開始しました。少し待ってね。")

    try:
        scan_all_symbols()
        LAST_SCAN_TIME = get_now_text()
        send_message(chat_id, "スキャン完了しました。TOP5を送信済みです。")

    except Exception as e:
        send_message(chat_id, f"スキャン中にエラーが出ました。\n{e}")
        print("スキャンエラー:", e)

    IS_SCANNING = False


def handle_command(chat_id, text):
    text = str(text).strip().lower()

    if text == "/start":
        handle_start(chat_id)
        return

    if text == "/help":
        handle_help(chat_id)
        return

    if text == "/status":
        handle_status(chat_id)
        return

    if text == "/scan":
        handle_scan(chat_id)
        return

    send_message(
        chat_id,
        "未対応コマンドです。\n\n"
        "使えるコマンド\n"
        "/scan\n"
        "/status\n"
        "/help"
    )


def main():
    if not BOT_TOKEN:
        print("Telegram Bot Token が見つかりません")
        print("notify.py の TOKEN を確認してね")
        return

    print("====================================")
    print("TA FX AI Pro Ver14 Telegram Bot 起動")
    print("スマホから /scan でスキャンできます")
    print("Ctrl + C で停止")
    print("====================================")

    last_update_id = None

    while True:
        updates = get_updates(last_update_id)

        for update in updates:
            last_update_id = update["update_id"] + 1

            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")

            if chat_id is None:
                continue

            print("受信:", chat_id, text)
            handle_command(chat_id, text)

        time.sleep(1)


if __name__ == "__main__":
    main()