import os
from dotenv import load_dotenv
from openai import OpenAI

# 🟢 حمّل المتغيرات من ملف .env
load_dotenv()

def ai_enabled() -> bool:
    """
    Check if OPENAI_API_KEY is available (after loading .env).
    """
    return os.getenv("OPENAI_API_KEY") is not None

def get_client() -> OpenAI | None:
    """
    Return an OpenAI client if the API key is set, otherwise None.
    """
    if not ai_enabled():
        return None
    # OpenAI SDK بيقرأ المفتاح من الـ env تلقائياً
    return OpenAI()

def ask_model(prompt: str) -> str | None:
    """
    Send the prompt to the model and return the response text.
    If AI is disabled or an error occurs, return None.
    """
    client = get_client()
    if client is None:
        print("[!] AI disabled: no OPENAI_API_KEY set.")
        return None

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": (
                    "You are a security assistant that analyzes QR code payloads. "
                    "Explain what the QR does, classify the attack type if any, "
                    "estimate risk, and suggest mitigations. Keep it concise."
                )},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[!] AI error: {e}")
        return None
