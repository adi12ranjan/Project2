import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from . import database
from .pipeline import run_pipeline
from .models import RawEmailRequest, DemoRequest

app = FastAPI(title="TraceMail AI — Email Threat & Forensic Intelligence Platform", version="1.0.0")

# Initialize the DB at import time (module load = cold start), not only on
# the ASGI startup event — serverless wrappers don't always reliably fire
# lifespan events, so this guarantees the schema exists either way.
database.init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hackathon MVP — tighten before any real deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEMO_DATA_DIR = os.path.join(os.path.dirname(__file__), 'demo_data')
DEMO_FILES = {
    'demo1': ('demo1_bec.eml', 'Fake CEO Wire Transfer (BEC)'),
    'demo2': ('demo2_phishing.eml', 'Credential Phishing'),
    'demo3': ('demo3_legit.eml', 'Safe Legitimate Email'),
    'demo4': ('demo4_lookalike.eml', 'Lookalike-Domain Impersonation'),
}

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2MB — plenty for headers + body, blocks abuse


@app.on_event("startup")
def on_startup():
    database.init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/demo-emails")
def list_demo_emails():
    return [{"demo_id": k, "filename": v[0], "label": v[1]} for k, v in DEMO_FILES.items()]


@app.post("/api/analyze/demo")
def analyze_demo(req: DemoRequest):
    if req.demo_id not in DEMO_FILES:
        raise HTTPException(status_code=404, detail="Unknown demo_id")
    filename, _label = DEMO_FILES[req.demo_id]
    path = os.path.join(DEMO_DATA_DIR, filename)
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    return run_pipeline(raw, filename=filename)


@app.post("/api/analyze/raw")
def analyze_raw(req: RawEmailRequest):
    # Treat all uploaded content as untrusted input: size-limit, never execute
    # attachments, never auto-follow URLs. Parsing is read-only text analysis.
    if len(req.raw_email.encode('utf-8', errors='ignore')) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Email content too large")
    if not req.raw_email.strip():
        raise HTTPException(status_code=400, detail="Empty email content")
    return run_pipeline(req.raw_email, filename=req.filename or 'pasted-email.eml')


@app.post("/api/analyze/upload")
async def analyze_upload(file: UploadFile = File(...)):
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 2MB)")
    try:
        raw = contents.decode('utf-8', errors='replace')
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode file as text")
    return run_pipeline(raw, filename=file.filename or 'uploaded.eml')


@app.get("/api/dashboard/stats")
def dashboard_stats():
    return database.dashboard_stats()


@app.get("/api/investigations")
def get_investigations():
    return database.list_investigations()


@app.get("/api/investigations/{investigation_id}")
def get_investigation(investigation_id: str):
    inv = database.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@app.get("/api/investigations/{investigation_id}/report", response_class=PlainTextResponse)
def get_report(investigation_id: str):
    inv = database.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv['analysis'].get('report_markdown', '# Report unavailable')


@app.get("/api/iocs")
def get_iocs():
    return database.list_iocs()
