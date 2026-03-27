from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import os
import uuid

from qrshilde.analysis.analyzer import analyze_qr_payload
from qrshilde.analysis.fake_qr_detector import detect_fake_qr


# =============================
# APP INIT
# =============================
app = FastAPI(
    title="QRShilde API",
    version="3.0.0",
    description="QR Security Analysis API (Production Ready)",
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

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


# =============================
# MODELS
# =============================
class AnalyzeRequest(BaseModel):
    payload: str = Field(..., min_length=1)
    image_path: str | None = None  # optional


# =============================
# HEALTH
# =============================
@app.get("/")
async def root():
    return {"status": "ok", "service": "qrshilde-api"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# =============================
# UPLOAD API
# =============================
@app.post("/upload")
async def upload_qr_image(file: UploadFile = File(...)):
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

    return {
        "ok": True,
        "image_path": path
    }


# =============================
# ANALYZE API (🔥 CLEAN RESPONSE)
# =============================
@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    payload = (request.payload or "").strip()

    if not payload:
        raise HTTPException(status_code=400, detail="Payload empty")

    result = await analyze_qr_payload(payload)

    # =============================
    # 🔥 Fake QR Detection (optional)
    # =============================
    if request.image_path:
        try:
            fake = detect_fake_qr(request.image_path)
            result["fake_qr"] = fake

            fake_score = fake.get("fake_qr_score", 0)

            if fake_score >= 60:
                combined = min(100, result.get("risk_score", 0) + 30)

                result["risk_score"] = combined
                result["final_score"] = combined
                result["verdict"] = "HIGH" if combined >= 70 else "MEDIUM"

        except Exception as e:
            result["fake_qr_error"] = str(e)

    # =============================
    # 🔥 FINAL CLEAN RESPONSE
    # =============================
    return {
        "ok": True,
        "payload": result.get("payload"),
        "risk_score": result.get("risk_score"),
        "verdict": result.get("verdict"),
        "findings": result.get("findings"),
        "confidence": result.get("confidence"),
        "fake_qr": result.get("fake_qr", None)
    }