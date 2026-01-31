from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import Document

from app.services.validators import validate_upload, validate_size
from app.services.storage import save_upload, infer_file_type

from app.services.ingestion_service import ingest_document
from app.services.indexing_service import index_document
from app.services.qa_service import ask_question
from app.services.orchestrator import Orchestrator

router = APIRouter()

# --------------------------------------------------
# Health Check
# --------------------------------------------------

@router.get("/health")
def health():
    return {"ok": True}

# --------------------------------------------------
# Document Upload
# --------------------------------------------------

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    ext = validate_upload(file)
    await validate_size(file)

    path = await save_upload(file)

    doc = Document(
        filename=file.filename,
        file_type=infer_file_type(ext),
        path=str(path),
        status="UPLOADED"
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "success": True,
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "status": doc.status
        }
    }

# --------------------------------------------------
# DEBUG: Text Extraction (Optional)
# --------------------------------------------------

@router.post("/documents/{document_id}/extract")
def extract_text(document_id: int, db: Session = Depends(get_db)):
    try:
        text = ingest_document(document_id, db)
        return {
            "success": True,
            "preview": text[:1000],
            "length": len(text)
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TEXT_EXTRACTION_FAILED",
                "message": str(e)
            }
        )

# --------------------------------------------------
# DEBUG: Indexing (Optional)
# --------------------------------------------------

@router.post("/documents/{document_id}/index")
def index_doc(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)

    if not doc or doc.status != "TEXT_EXTRACTED":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_STATE",
                "message": "Document must have extracted text before indexing"
            }
        )

    # NOTE: indexing assumes text already extracted
    text = ingest_document(document_id, db)
    count = index_document(document_id, text, db)

    return {
        "success": True,
        "chunks_indexed": count
    }

# --------------------------------------------------
# Orchestrated Processing (PRODUCTION FLOW)
# --------------------------------------------------

@router.post("/documents/{document_id}/process")
def process_document(document_id: int, db: Session = Depends(get_db)):
    try:
        orch = Orchestrator()
        result = orch.process_document(document_id, db)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "PROCESSING_FAILED",
                "message": str(e)
            }
        )

# --------------------------------------------------
# Question Answering
# --------------------------------------------------

class QuestionRequest(BaseModel):
    document_id: int
    question: str
    top_k: int = 5

@router.post("/questions/ask")
def ask(req: QuestionRequest, db: Session = Depends(get_db)):
    try:
        answer, sources = ask_question(
            document_id=req.document_id,
            question=req.question,
            db=db,
            top_k=req.top_k
        )
        return {
            "success": True,
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "QA_FAILED",
                "message": str(e)
            }
        )
