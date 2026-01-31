from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import Document, Chunk
from app.agents.indexing_agent import IndexingAgent

# Directory for FAISS indexes and metadata
INDEX_DIR = Path("storage/indexes")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def index_document(document_id: int, text: str, db: Session) -> int:
    # Fetch document record
    doc = db.get(Document, document_id)
    if not doc:
        raise ValueError("Document not found")

    # Initialize indexing agent
    agent = IndexingAgent()
    
    # Split document text into chunks
    chunks = agent.chunk_text(text)

    # Remove existing chunks for document
    db.query(Chunk).filter(Chunk.document_id == document_id).delete()
    
    # Persist new chunks
    for i, chunk in enumerate(chunks):
        db.add(Chunk(document_id=document_id, chunk_index=i, text=chunk))

    # Resolve index storage paths
    index_path = INDEX_DIR / f"{document_id}.faiss"
    map_path = INDEX_DIR / f"{document_id}_map.json"

    # Build and persist vector index
    count = agent.build_index(chunks, index_path, map_path)

    # Update document status
    doc.status = "INDEXED"
    db.commit()

    # Return indexed chunk count
    return count
