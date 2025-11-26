import os
from openai import OpenAI

# نستخدم متغير بيئة عشان ما نفضح الـ API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    # نخلي الأداة تشتغل بدون كراش لو مافي مفتاح
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)


def ask_model(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    يرسل برومبت للموديل ويرجع النص.
    لو ما في API key أو في مشكلة، يرجع رسالة بسيطة بدل ما يوقع البرنامج.
    """
    if client is None:
        return "[AI disabled] No OPENAI_API_KEY set. Cannot analyze."

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a cybersecurity QR attack analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[AI error] {e}"
