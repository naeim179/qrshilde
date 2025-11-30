import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq  # نستخدم Groq بدل OpenAI

# 📌 حدد مسار الروت تبع المشروع (اللي فيه ملف .env)
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT_DIR / ".env"

# 🟢 حمّل المتغيرات من ملف .env من مسار ثابت
load_dotenv(dotenv_path=ENV_PATH)


def ai_enabled() -> bool:
    """
    Check if GROQ_API_KEY is available (after loading .env).
    """
    return os.getenv("GROQ_API_KEY") is not None


def get_client() -> Groq | None:
    """
    Return a Groq client if the API key is set, otherwise None.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[!] GROQ_API_KEY not set.")
        return None

    return Groq(api_key=api_key)


def ask_model(prompt: str) -> str | None:
    """
    Send the prompt to the Groq model and return the response text.
    If AI is disabled or an error occurs, return None.
    """
    client = get_client()
    if client is None:
        print("[!] AI disabled: no GROQ_API_KEY set.")
        return None

    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # موديل Groq (تقدر تغيّره لاحقاً)
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a security assistant that analyzes QR code payloads. "
                        "Explain what the QR does, classify the attack type if any, "
                        "estimate risk, and suggest mitigations. Keep it concise."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[!] AI error: {e}")
        return None


def ask_model_safe(prompt: str):
    """
    Wrapper يرجّع (ok, result_or_error_string)
    """
    try:
        result = ask_model(prompt)
        return True, result
    except Exception as e:
        print(f"[!] AI error (safe): {e}")
        return False, str(e)
