from sqlalchemy.orm import Session
from app.db.models import Document
from app.services.ingestion_service import ingest_document
from app.services.indexing_service import index_document

class Orchestrator:
    """
    Central controller coordinating agent-based workflow.
    Agents never call each other directly; APIs call the Orchestrator.
    """

    def process_document(self, document_id: int, db: Session) -> dict:
        doc = db.get(Document, document_id)
        if not doc:
            raise ValueError("Document not found")

        # Step 1: Extract text (IngestionAgent via service)
        doc.status = "PROCESSING_TEXT"
        db.commit()
        text = ingest_document(document_id, db)

        # Step 2: Index text (IndexingAgent via service)
        doc.status = "PROCESSING_INDEX"
        db.commit()
        chunks_count = index_document(document_id, text, db)

        return {
            "document_id": document_id,
            "status": "INDEXED",
            "chunks_indexed": chunks_count,
        }
