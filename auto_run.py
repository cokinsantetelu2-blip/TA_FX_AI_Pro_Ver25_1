# auto_run.py

import time
from main import main

print("===================================")
print("USDJPY_Fibo_AI 自動監視開始")
print("Ctrl + C で停止できます")
print("===================================")

while True:
    try:
        print("\nAI分析開始")
        main()
        print("分析完了")

    except Exception as e:
        print("エラー:", e)

    print("1時間待機します...")
    time.sleep(3600)   # テスト中は30秒。本番は3600に変更。