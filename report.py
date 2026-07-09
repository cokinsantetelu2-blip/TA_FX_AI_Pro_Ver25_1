def create_report(
    current_price,
    trend,
    structure,
    signal,
    selected_high,
    selected_low,
    fib,
    score,
    reasons
):
    stars = "★" * (score // 20)
    if stars == "":
        stars = "☆"

    reason_text = "\n".join(reasons)

    report = f"""
🤖 USDJPY Fibo AI

💰 現在価格
{current_price:.3f}

📈 ダウ理論
{trend}

📊 相場構造
{structure}

🔥 シグナル
{signal}

⭐ AIスコア
{score}点
{stars}

🧠 理由
{reason_text}

📍 採用高値
{selected_high:.3f}

📍 採用安値
{selected_low:.3f}

🎯 フィボ
38.2% : {fib['38.2']:.3f}
50.0% : {fib['50.0']:.3f}
61.8% : {fib['61.8']:.3f}
"""

    return report