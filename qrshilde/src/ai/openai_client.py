import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from groq import Groq

# 📌 تحديد مسار الروت وتحميل المتغيرات
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

def ai_enabled() -> bool:
    """
    Returns True if AT LEAST one API key is available.
    """
    has_gemini = os.getenv("GEMINI_API_KEY") is not None
    has_groq = os.getenv("GROQ_API_KEY") is not None
    return has_gemini or has_groq

def ask_gemini(prompt: str) -> str | None:
    """
    محاولة الاتصال بموديل Gemini
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None  # المفتاح غير موجود، ننتقل للتالي

    try:
        genai.configure(api_key=api_key)
        
        # ✅ التعديل هنا: استخدام الموديل العام والمستقر للباقة المجانية
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # دمج تعليمات النظام مع البرومبت
        full_prompt = (
            "You are a cybersecurity expert analyzing a QR payload. "
            "Identify attacks, risks, and obfuscation. Be concise.\n"
            f"Payload to analyze: {prompt}"
        )
        
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"[⚠️] Gemini Error: {e}")
        return None # فشل الاتصال، نرجع None عشان نجرب Groq

def ask_groq(prompt: str) -> str | None:
    """
    محاولة الاتصال بموديل Groq (احتياطي)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        client = Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a cybersecurity expert. Analyze this QR payload concisely."
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[⚠️] Groq Error: {e}")
        return None

def ask_model(prompt: str) -> str | None:
    """
    الدالة الرئيسية الذكية:
    1. تحاول Gemini أولاً.
    2. إذا فشل، تحاول Groq.
    3. إذا فشل الاثنان، تعتذر.
    """
    # 1️⃣ المحاولة الأولى: Google Gemini
    print("   [..] Trying Google Gemini...")
    result = ask_gemini(prompt)
    if result:
        return result

    # 2️⃣ المحاولة الثانية: Groq (Fallback)
    print("   [..] Gemini unavailable, switching to Groq...")
    result = ask_groq(prompt)
    if result:
        return result

    # 3️⃣ الكل فشل
    print("[!] All AI models failed or keys are missing.")
    return None

def ask_model_safe(prompt: str):
    """
    Wrapper لضمان عدم توقف البرنامج عند الأخطاء
    """
    try:
        result = ask_model(prompt)
        if result:
            return True, result
        else:
            return False, "AI Analysis unavailable (Check API keys or Quota)."
    except Exception as e:
        return False, str(e)