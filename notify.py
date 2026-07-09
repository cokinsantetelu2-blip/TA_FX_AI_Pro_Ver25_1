# notify.py

import requests

TOKEN = "8661344147:AAE-Fcae7xsUTZLWHMQGuxODZfWlUtePfA8"
CHAT_ID = "8950835084"


def send_notification(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        }
    )

    return response.status_code, response.text


def send_photo(image_path, caption=""):
    import os
    import time

    if not image_path:
        print("画像パスなし")
        return 0, "画像パスなし"

    if not os.path.exists(image_path):
        print("画像ファイルなし:", image_path)
        return 0, f"画像ファイルなし: {image_path}"

    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    try:
        with open(image_path, "rb") as image:
            response = requests.post(
                url,
                data={
                    "chat_id": CHAT_ID,
                    "caption": caption
                },
                files={
                    "photo": image
                },
                timeout=30
            )

        print("Telegram画像送信:", image_path, response.status_code, response.text[:200])

        time.sleep(1)

        return response.status_code, response.text

    except Exception as e:
        print("Telegram画像送信エラー:", image_path, e)
        return 0, str(e)

   