from sqlalchemy import String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.base import Base


class Document(Base):
    # Document metadata table
    __tablename__ = "documents"

    # Primary document identifier
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Original uploaded filename
    filename: Mapped[str] = mapped_column(String, nullable=False)
    
    # File type (e.g., pdf, image)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    
    # Storage path on disk
    path: Mapped[str] = mapped_column(String, nullable=False)
    
    # Processing status
    status: Mapped[str] = mapped_column(String, nullable=False, default="UPLOADED")
    
    # Creation timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Chunk(Base):
    # Text chunk table
    __tablename__ = "chunks"

    # Primary chunk identifier
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Parent document reference
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    
    # Chunk sequence index
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Chunk text content
    text: Mapped[str] = mapped_column(Text, nullable=False)
