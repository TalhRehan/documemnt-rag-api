from sqlalchemy.orm import Session
from app.db.models import Document
from app.agents.ingestion_agent import IngestionAgent

def ingest_document(document_id: int, db: Session) -> str:
    # Fetch document record
    doc = db.get(Document, document_id)
    if not doc:
        raise ValueError("Document not found")

    # Initialize ingestion agent
    agent = IngestionAgent()
    
    # Extract text from document
    extracted_text = agent.extract_text(doc.path, doc.file_type)

    # Handle extraction failure
    if not extracted_text:
        doc.status = "FAILED_TEXT_EXTRACTION"
        db.commit()
        raise ValueError("No text could be extracted from document")

    # Update document status
    doc.status = "TEXT_EXTRACTED"
    db.commit()

    # Return extracted content
    return extracted_text
