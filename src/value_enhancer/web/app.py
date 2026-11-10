import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from ..orchestrator import ReconOrchestrator
from ..models import IntelligenceReport

app = FastAPI(
    title="Value-Enhancer OSINT Intelligence Suite",
    description="Unified Digital Reconnaissance and Security Audit API",
    version="0.1.0"
)

orchestrator = ReconOrchestrator()
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class UsernameRequest(BaseModel):
    username: str


class PhoneRequest(BaseModel):
    phone: str


class DomainRequest(BaseModel):
    domain: str


class SecretScanRequest(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h2>Value-Enhancer Dashboard: Static file not found</h2>")


@app.post("/api/scan/identity", response_model=IntelligenceReport)
async def scan_identity(req: UsernameRequest):
    if not req.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    return await orchestrator.scan_username(req.username.strip())


@app.post("/api/scan/phone", response_model=IntelligenceReport)
async def scan_phone(req: PhoneRequest):
    if not req.phone.strip():
        raise HTTPException(status_code=400, detail="Phone number cannot be empty")
    return orchestrator.scan_phone(req.phone.strip())


@app.post("/api/scan/domain", response_model=IntelligenceReport)
async def scan_domain(req: DomainRequest):
    if not req.domain.strip():
        raise HTTPException(status_code=400, detail="Domain cannot be empty")
    return await orchestrator.scan_domain(req.domain.strip())


@app.post("/api/scan/secrets", response_model=IntelligenceReport)
async def scan_secrets(req: SecretScanRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return orchestrator.scan_secrets(req.text, is_text=True)


@app.post("/api/scan/metadata", response_model=IntelligenceReport)
async def scan_metadata(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename or "")[1]) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        report = orchestrator.scan_metadata(tmp_path)
        report.target = file.filename or "uploaded_image"
        if report.metadata_results:
            report.metadata_results[0].filename = file.filename or "uploaded_image"
        return report
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
