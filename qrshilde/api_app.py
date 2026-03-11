from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from qrshilde.analysis.analyzer import analyze_qr_payload


app = FastAPI(
    title="QRShilde API",
    version="1.0.0",
    description="QR security analysis API for Flutter/mobile integration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    payload: str = Field(..., min_length=1, description="Decoded QR payload text")


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/", response_model=HealthResponse)
async def root() -> HealthResponse:
    return HealthResponse(status="ok", service="qrshilde-api")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="qrshilde-api")


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    payload = (request.payload or "").strip()
    if not payload:
        raise HTTPException(status_code=400, detail="Payload must not be empty.")

    result = await analyze_qr_payload(payload)

    return {
        "ok": True,
        "result": result,
    }