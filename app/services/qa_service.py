from sqlalchemy.orm import Session
from app.db.models import Document, Chunk
from app.agents.qa_agent import QAAgent

def ask_question(document_id: int, question: str, db: Session, top_k: int = 5):
    doc = db.get(Document, document_id)
    if not doc:
        raise ValueError("Document not found")

    if doc.status != "INDEXED":
        raise ValueError("Document must be indexed before asking questions")

    agent = QAAgent()
    retrieved = agent.retrieve(document_id, question, top_k=top_k)

    # Resolve retrieved vector_ids -> chunk_index -> chunk text
    contexts = []
    sources = []

    for r in retrieved:
        # vector_id == chunk_index by our design
        chunk_index = r["vector_id"]

        chunk = (
            db.query(Chunk)
            .filter(Chunk.document_id == document_id, Chunk.chunk_index == chunk_index)
            .first()
        )
        if not chunk:
            continue

        contexts.append(chunk.text)
        sources.append({
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "preview": chunk.text[:200]
        })

    answer = agent.answer_from_context(question, contexts)

    return answer, sources
