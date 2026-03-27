from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import os
import uuid

from qrshilde.analysis.analyzer import analyze_qr_payload
from qrshilde.analysis.fake_qr_detector import detect_fake_qr


app = FastAPI(
    title="QRShilde API",
    version="2.0.0",
    description="QR security analysis API with Fake QR detection.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ امتدادات مسموحة فقط
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


# -----------------------------
# Models
# -----------------------------
class AnalyzeRequest(BaseModel):
    payload: str = Field(..., min_length=1)
    image_path: str | None = None


# -----------------------------
# Health
# -----------------------------
@app.get("/")
async def root():
    return {"status": "ok", "service": "qrshilde-api"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# -----------------------------
# Upload API
# -----------------------------
@app.post("/upload")
async def upload_qr_image(file: UploadFile = File(...)):
    # ✅ تحقق من الامتداد
    ext = (file.filename or "").split(".")[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    filename = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as f:
        f.write(await file.read())

    return {"ok": True, "image_path": path}


# -----------------------------
# Analyze API
# -----------------------------
@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    payload = (request.payload or "").strip()

    if not payload:
        raise HTTPException(status_code=400, detail="Payload empty")

    result = await analyze_qr_payload(payload)

    # 🔥 Fake QR Detection
    if request.image_path:
        try:
            fake = detect_fake_qr(request.image_path)
            result["fake_qr"] = fake

            fake_score = fake.get("fake_qr_score", 0)

            if fake_score >= 60:
                # ✅ ادمج السكورين وحدّث كلاهما معاً
                combined = min(100, result.get("final_score", 0) + 30)
                result["final_score"] = combined
                result["risk_score"] = combined  # ✅ synchronized
                result["verdict"] = "HIGH" if combined >= 70 else "MEDIUM"

        except Exception as e:
            result["fake_qr_error"] = str(e)

    return {"ok": True, "result": result}