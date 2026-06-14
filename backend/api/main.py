import os
import shutil
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from core.pipeline import NyayAIPipeline
from database.connection import get_db, init_db
from database.models import Case, InputType, StatusType
import uuid

app = FastAPI(
    title="NyayAI",
    description="Autonomous Legal Research Agent for Indian Judiciary",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    try:
        app.state.pipeline = NyayAIPipeline()
        print("Pipeline initialized successfully")
    except Exception as e:
        print(f"Pipeline init failed: {e}")
        app.state.pipeline = None


def get_pipeline():
    pipeline = getattr(app.state, "pipeline", None)
    if not pipeline:
        raise HTTPException(status_code=500, detail="Pipeline not initialized. Check your GEMINI_API_KEY in .env")
    return pipeline


# ── Request models ────────────────────────────────────────────────────────────
class TextRequest(BaseModel):
    description: str
    court_type: Optional[str] = None

# Frontend sends this shape
class AnalyseRequest(BaseModel):
    case_description: str
    judge_name: Optional[str] = ""


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "NyayAI API is running", "version": "1.0.0"}


@app.get("/health")
def health():
    pipeline = getattr(app.state, "pipeline", None)
    return {"status": "ok", "pipeline_ready": pipeline is not None}


# ── /analyse — called by the React frontend ───────────────────────────────────
@app.post("/analyse")
def analyse(request: AnalyseRequest, db: Session = Depends(get_db)):
    """
    Main endpoint consumed by the React frontend.
    Accepts { case_description, judge_name }
    Returns { precedents, argument, outcome, judge_profile }
    """
    pipeline = get_pipeline()
    case_id = str(uuid.uuid4())

    case = Case(
        id=case_id,
        input_type=InputType.text,
        case_description=request.case_description,
        status=StatusType.processing,
    )
    db.add(case)
    db.commit()

    try:
        state = pipeline.run_from_text_full_state(
            case_description=request.case_description
        )

        # Map judgements → precedents (frontend shape)
        precedents = []
        for j in state.judgements:
            year = j.date[:4] if j.date and len(j.date) >= 4 else "N/A"
            precedents.append({
                "id": j.docid,
                "title": j.title,
                "court": j.court,
                "year": year,
                "principle": j.snippet,
                "citations": 0,
                "url": f"https://indiankanoon.org/doc/{j.docid}/",
            })

        # Build judge profile
        judge_name = (request.judge_name or "").strip()
        if judge_name:
            judge_profile = {
                "name": judge_name,
                "court": "Indian High Court / Supreme Court",
                "favour_rate": 55,
                "temperament": "Evidence-focused and procedurally rigorous",
                "tips": [
                    "File a well-indexed brief at least three days before the hearing date.",
                    "Lead with constitutional provisions before moving to statutory arguments.",
                    "Keep oral submissions concise — identify the two strongest arguments.",
                ],
                "landmark": "Profile based on available judicial records.",
            }
        else:
            judge_profile = {
                "name": "Presiding Judge",
                "court": "Indian Judiciary",
                "favour_rate": 50,
                "temperament": "Methodical and evidence-driven",
                "tips": [
                    "Present all documentary evidence in an organised brief before the hearing.",
                    "Keep oral submissions structured and precedent-backed.",
                    "Anticipate jurisdictional and limitation issues at the outset.",
                ],
                "landmark": "No specific judge name provided.",
            }

        # Save report
        case.final_report = state.final_report
        case.status = StatusType.completed
        db.commit()

        return {
            "case_description": request.case_description,
            "judge_name": judge_name,
            "precedents": precedents,
            "argument": state.final_report,
            "outcome": state.structured_outcome,
            "judge_profile": judge_profile,
        }

    except Exception as e:
        case.status = StatusType.failed
        case.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


# ── /analyze/text — legacy endpoint (kept for compatibility) ──────────────────
@app.post("/analyze/text")
def analyze_text(request: TextRequest, db: Session = Depends(get_db)):
    pipeline = get_pipeline()
    case_id = str(uuid.uuid4())
    case = Case(
        id=case_id,
        input_type=InputType.text,
        case_description=request.description,
        status=StatusType.processing,
    )
    db.add(case)
    db.commit()
    try:
        report = pipeline.run_from_text(
            case_description=request.description, court_type=request.court_type
        )

        db.query(Case).filter(Case.id == case_id).update({
            "final_report": report,
            "status": StatusType.completed
        })
        case.final_report = report
        case.status = StatusType.completed
        db.commit()
        return {"case_id": case_id, "report": report, "status": "completed"}
    except Exception as e:
        case.status = StatusType.failed
        case.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


# ── /analyze/pdf ──────────────────────────────────────────────────────────────
@app.post("/analyze/pdf")
async def analyze_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    pipeline = get_pipeline()
    case_id = str(uuid.uuid4())
    temp_path = f"temp_{case_id}_{file.filename}"
    case = Case(
        id=case_id,
        input_type=InputType.pdf,
        case_description=f"PDF: {file.filename}",
        status=StatusType.processing,
    )
    db.add(case)
    db.commit()
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        report = pipeline.run_from_pdf(pdf_path=temp_path)
        case.final_report = report
        case.status = StatusType.completed
        db.commit()
        return {"case_id": case_id, "report": report, "status": "completed"}
    except Exception as e:
        case.status = StatusType.failed
        case.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.get("/case/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"case_id": case.id, "report": case.final_report or "", "status": case.status.value}


@app.get("/cases")
def get_all_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return [
        {
            "case_id": c.id,
            "input_type": c.input_type.value,
            "status": c.status.value,
            "created_at": str(c.created_at),
            "case_description": c.case_description[:100] + "..." if len(c.case_description) > 100 else c.case_description,
        }
        for c in cases
    ]