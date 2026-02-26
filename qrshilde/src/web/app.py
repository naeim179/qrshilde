import os, json, datetime
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyzbar.pyzbar import decode
from PIL import Image
from pydantic import BaseModel

from qrshilde.src.ai.analyzer import analyze_qr_payload
from qrshilde.src.ml.status import get_ml_status  # ✅ ML status endpoint


app = FastAPI()

REPORTS_DIR = "reports"
HISTORY_FILE = "history.json"

os.makedirs("static/uploads", exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="qrshilde/src/web/templates")


# (اختياري) لو احتجت CORS لاحقاً لتطبيق خارجي:
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


def _safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default


def create_markdown_report(result, report_id):
    report_path = os.path.join(REPORTS_DIR, f"Report_{report_id}.md")

    content = f"""# 🛡️ QrShilde Security Audit Report
**Date:** {result.get('timestamp')} | **ID:** {report_id}
## 📊 Verdict: {result.get('category')} ({result.get('risk_score')}/100)

### 🔍 Findings:
"""
    for f in result.get("findings", []):
        content += f"- ⚠️ {f}\n"

    if result.get("evidence_img"):
        content += f"\n### 📸 Site Evidence:\n![Screenshot](..{result['evidence_img']})\n"

    # ✅ Include ML details if present
    if result.get("ml_result"):
        mlr = result["ml_result"]
        prob = _safe_float(mlr.get("phishing_probability"))
        thr = _safe_float(mlr.get("threshold"))
        label = mlr.get("label", "unknown")

        content += "\n### 🧠 ML Result:\n"
        content += f"- Label: **{label}**\n"
        if prob is not None:
            content += f"- Phishing Probability: **{prob:.4f}**\n"
        if thr is not None:
            content += f"- Threshold: **{thr:.2f}**\n"

        if mlr.get("reasons"):
            content += "\n**Top ML signals:**\n"
            for r in mlr["reasons"]:
                imp = _safe_float(r.get("impact"))
                if imp is None:
                    content += f"- {r.get('feature')}: {r.get('impact')}\n"
                else:
                    content += f"- {r.get('feature')}: {imp:.4f}\n"

    content += f"\n### 🤖 AI Analysis:\n{result.get('ai_analysis')}\n\n---\n**Payload:** `{result.get('payload')}`"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path


@app.get("/api/ml/status")
async def ml_status():
    """Quick health/status for local ML model & key libraries."""
    return get_ml_status()


class AnalyzeTextRequest(BaseModel):
    payload: str


@app.post("/api/analyze_text")
async def analyze_text_api(body: AnalyzeTextRequest):
    """Analyze raw payload (for testing/demo without QR image)."""
    report_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result = await analyze_qr_payload(body.payload, report_id)
    _ = create_markdown_report(result, report_id)

    # history
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    history.insert(0, result)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:50], f, indent=4)

    return result


@app.post("/api/analyze")
async def analyze_api(file: UploadFile = File(...)):
    report_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"static/uploads/{report_id}.png"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    decoded = decode(Image.open(file_path))
    payload = decoded[0].data.decode("utf-8") if decoded else "No QR Found"

    result = await analyze_qr_payload(payload, report_id)
    result["image_url"] = f"/static/uploads/{report_id}.png"

    _ = create_markdown_report(result, report_id)

    # history
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    history.insert(0, result)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:50], f, indent=4)

    return result


@app.get("/")
async def index(request: Request):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    return templates.TemplateResponse("dashboard.html", {"request": request, "history": history})