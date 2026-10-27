from fastapi import FastAPI, File, HTTPException, UploadFile
from .documents import extract_text
from .engine import analyze_text
from .schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(title="Contract Risk Analyzer Pro API", version="0.1.0",
              description="Frontend-agnostic contract screening API. Not legal advice.")

@app.get("/health")
def health():
    return {"status": "ok", "mode": "rules_baseline"}

@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    try:
        return analyze_text(request.text, request.contract_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/v1/analyze/file", response_model=AnalyzeResponse)
async def analyze_file(file: UploadFile = File(...), contract_type: str = "general"):
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 15 MB limit.")
    try:
        return analyze_text(extract_text(file.filename or "upload.txt", content), contract_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to parse uploaded document.") from exc
