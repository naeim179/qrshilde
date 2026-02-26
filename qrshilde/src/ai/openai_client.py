import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

# ✅ New SDK
from google import genai

ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def ai_enabled() -> bool:
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    return has_gemini or has_groq


def _build_json_prompt(payload: str) -> str:
    """
    Force the LLM to return STRICT JSON and NOT override the app verdict.
    """
    return f"""
You are assisting a QR security scanner.
STRICT RULES:
- Do NOT output a final verdict label like SAFE/MALICIOUS/HIGH RISK.
- Do NOT exaggerate. Be evidence-based.
- If domain is a reserved placeholder like example.com, mention it is a documentation domain and reduce alarm.
- Output MUST be valid JSON only (no markdown, no extra text).

Return JSON with exactly these keys:
summary: string
suspicious_signals: array of strings
benign_signals: array of strings
recommendation: string

Payload:
{payload}
""".strip()


def _safe_parse_json(text: str):
    """
    Tries to parse JSON from model output. If fails, wraps raw text.
    """
    if not text:
        return None

    t = text.strip()

    # First try: direct JSON
    try:
        return json.loads(t)
    except Exception:
        pass

    # Second try: extract JSON block if model added text
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = t[start : end + 1].strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Fallback: wrap raw output
    return {
        "summary": t[:500],
        "suspicious_signals": [],
        "benign_signals": [],
        "recommendation": "Review manually (AI output was not valid JSON)."
    }


def ask_gemini(payload: str) -> dict | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        client = genai.Client(api_key=api_key)
        full_prompt = _build_json_prompt(payload)

        resp = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=full_prompt,
        )

        data = _safe_parse_json(getattr(resp, "text", None))
        return data
    except Exception as e:
        print(f"[⚠️] Gemini Error: {e}")
        return None


def ask_groq(payload: str) -> dict | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        client = Groq(api_key=api_key)

        system_msg = (
            "You are assisting a QR security scanner. "
            "Return STRICT JSON only with keys: summary, suspicious_signals, benign_signals, recommendation. "
            "Do NOT output final verdict labels SAFE/MALICIOUS. Evidence-based only."
        )

        user_msg = _build_json_prompt(payload)

        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.2,
        )

        text = resp.choices[0].message.content
        return _safe_parse_json(text)

    except Exception as e:
        print(f"[⚠️] Groq Error: {e}")
        return None


def ask_model(payload: str) -> dict | None:
    """
    Returns a dict JSON:
    {summary, suspicious_signals, benign_signals, recommendation}
    """
    print("   [..] Trying Google Gemini...")
    result = ask_gemini(payload)
    if result:
        return result

    print("   [..] Gemini unavailable, switching to Groq...")
    result = ask_groq(payload)
    if result:
        return result

    print("[!] All AI models failed or keys are missing.")
    return None


def format_ai_analysis(ai_json: dict | None) -> str:
    """
    Convert AI JSON into a readable markdown-ish text for your report/dashboard.
    """
    if not ai_json:
        return "AI Analysis unavailable."

    summary = ai_json.get("summary", "")
    sus = ai_json.get("suspicious_signals", []) or []
    ben = ai_json.get("benign_signals", []) or []
    rec = ai_json.get("recommendation", "")

    out = []
    if summary:
        out.append(f"**Summary:** {summary}")

    if sus:
        out.append("\n**Suspicious signals:**")
        out.extend([f"- {x}" for x in sus[:10]])

    if ben:
        out.append("\n**Benign signals:**")
        out.extend([f"- {x}" for x in ben[:10]])

    if rec:
        out.append(f"\n**Recommendation:** {rec}")

    return "\n".join(out)


def ask_model_safe(prompt):
    """
    Keeps compatibility: returns (ok, text)
    """
    data = ask_model(str(prompt))
    if not data:
        return False, "AI Analysis unavailable."
    return True, format_ai_analysis(data)