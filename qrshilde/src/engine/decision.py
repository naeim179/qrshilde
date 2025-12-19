import os, json
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")

SYSTEM = """Return ONLY valid JSON:
{
  "risk_score": 0-100,
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "recommended_action": "ALLOW|SANDBOX_PREVIEW|BLOCK",
  "reasons": ["..."]
}
No extra text.
"""

def groq_decide(payload: str, inspection: dict, tool_signals: dict) -> dict:
    if not GROQ_API_KEY:
        return {
            "risk_score": 50,
            "risk_level": "MEDIUM",
            "recommended_action": "SANDBOX_PREVIEW",
            "reasons": ["Groq API key not configured; defaulting to safe preview."]
        }

    prompt = {
        "payload": payload,
        "inspection": inspection,
        "tool_signals": tool_signals,
    }

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(prompt)}
        ],
        "temperature": 0.1
    }

    r = requests.post(
        f"{GROQ_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json=body,
        timeout=20
    )
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    return json.loads(content)
