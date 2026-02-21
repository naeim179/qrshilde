import os, uuid, json, datetime
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyzbar.pyzbar import decode
from PIL import Image
from qrshilde.src.ai.analyzer import analyze_qr_payload

app = FastAPI()
REPORTS_DIR = "reports"
HISTORY_FILE = "history.json"

os.makedirs("static/uploads", exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="qrshilde/src/web/templates")

def create_markdown_report(result, report_id):
    report_path = os.path.join(REPORTS_DIR, f"Report_{report_id}.md")
    content = f"""# 🛡️ QrShilde Security Audit Report
**Date:** {result['timestamp']} | **ID:** {report_id}
## 📊 Verdict: {result['category']} ({result['risk_score']}/100)

### 🔍 Findings:
"""
    for f in result['findings']: content += f"- ⚠️ {f}\n"
    
    if result.get("evidence_img"):
        # إضافة الصورة للتقرير المكتوب
        content += f"\n### 📸 Site Evidence:\n![Screenshot](..{result['evidence_img']})\n"

    content += f"\n### 🤖 AI Analysis:\n{result['ai_analysis']}\n\n---\n**Payload:** `{result['payload']}`"
    
    with open(report_path, "w", encoding="utf-8") as f: f.write(content)
    return report_path

@app.post("/api/analyze")
async def analyze_api(file: UploadFile = File(...)):
    report_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"static/uploads/{report_id}.png"
    with open(file_path, "wb") as f: f.write(await file.read())

    decoded = decode(Image.open(file_path))
    payload = decoded[0].data.decode("utf-8") if decoded else "No QR Found"

    # تشغيل التحليل (لاحظ استخدام await هنا)
    result = await analyze_qr_payload(payload, report_id)
    result["image_url"] = f"/static/uploads/{report_id}.png"
    
    report_file = create_markdown_report(result, report_id)
    
    # حفظ في التاريخ
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: history = json.load(f)
    history.insert(0, result)
    with open(HISTORY_FILE, "w") as f: json.dump(history[:50], f, indent=4)

    return result

@app.get("/")
async def index(request: Request):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: history = json.load(f)
    return templates.TemplateResponse("dashboard.html", {"request": request, "history": history})