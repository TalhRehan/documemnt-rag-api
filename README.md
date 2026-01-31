# Document AI Backend
### Multi-Agent RAG System with Production-Grade Architecture

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![AWS](https://img.shields.io/badge/Deployed-AWS%20EC2-orange.svg)](https://aws.amazon.com/ec2/)

**Live API** 'http://13.51.194.236:8080/docs' : | [API Docs](http://13.51.194.236:8080/docs)

---

## 🎯 System Overview

A production-ready document intelligence platform utilizing a **multi-agent architecture** for automated document processing and question answering. Built with FastAPI, SQLAlchemy, and FAISS for high-performance vector search.

### Architecture Highlights

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI REST API Layer                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator (Controller)                   │
│          Coordinates agent workflow & state management       │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Ingestion   │    │  Indexing   │    │     Q&A     │
│   Agent     │───▶│    Agent    │───▶│    Agent    │
│             │    │             │    │             │
│ • PyMuPDF   │    │ • Chunking  │    │ • FAISS     │
│ • Tesseract │    │ • Embedding │    │ • Retrieval │
│ • OCR       │    │ • FAISS     │    │ • Context   │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│         SQLite (Metadata) + FAISS (Vector Store)             │
└─────────────────────────────────────────────────────────────┘
```

### Key Technical Decisions

- **Agent Isolation**: Agents never call each other directly; orchestrator manages all inter-agent communication
- **State Machine**: Documents transition through defined states (UPLOADED → TEXT_EXTRACTED → INDEXED)
- **Dual Storage**: Relational DB for metadata + FAISS for vector similarity search
- **Embedding Model**: `all-MiniLM-L6-v2` (384-dim, optimized for semantic search)
- **Chunking Strategy**: 800-char chunks with 150-char overlap for context preservation

---

## 🤖 Agent Responsibilities

### 1. **Ingestion Agent** (`app/agents/ingestion_agent.py`)
**Purpose**: Multimodal text extraction with intelligent preprocessing

**Capabilities**:
- PDF text extraction (PyMuPDF) with layout preservation
- Image OCR (Tesseract) for scanned documents
- Text normalization and cleaning pipeline
- Handles corrupted PDFs and low-quality scans

**Technology**: PyMuPDF, Pillow, Pytesseract

---

### 2. **Indexing Agent** (`app/agents/indexing_agent.py`)
**Purpose**: Semantic chunking and vector index generation

**Workflow**:
1. **Chunking**: Splits text into 800-char segments with 150-char overlap
2. **Embedding**: Generates 384-dim dense vectors using Sentence-BERT
3. **Indexing**: Builds FAISS L2 index for fast similarity search
4. **Persistence**: Stores index + metadata mapping on disk

**Optimizations**:
- Batch embedding for efficiency
- Overlap strategy prevents context loss at chunk boundaries
- FAISS IndexFlatL2 for exact nearest neighbor search

**Technology**: Sentence-Transformers, FAISS, NumPy

---

### 3. **Q&A Agent** (`app/agents/qa_agent.py`)
**Purpose**: Semantic retrieval and grounded answer generation

**Workflow**:
1. **Query Encoding**: Embeds user question using same model
2. **Retrieval**: FAISS returns top-k most relevant chunks (default k=5)
3. **Context Assembly**: Fetches full chunk text from database
4. **Answer Generation**: Returns extractive summary from source material

**Design Philosophy**: 
- **Grounded responses only** - no hallucination risk
- Returns ranked source excerpts with chunk IDs
- Ready for LLM integration (Phase 5 upgrade path)

**Technology**: FAISS, Sentence-Transformers

---

### 4. **Orchestrator** (`app/services/orchestrator.py`)
**Purpose**: Workflow coordination and error handling

**Responsibilities**:
- Enforces agent execution order
- Manages document state transitions
- Handles rollback on failures
- Provides single entry point for complex workflows

**Pattern**: Mediator pattern for loose coupling

---

## 📡 API Endpoints

### Health Check
```http
GET /health
```
Returns service status

---

### Document Upload
```http
POST /documents/upload
Content-Type: multipart/form-data

{
  "file": <binary>
}
```

**Supported Formats**: PDF, PNG, JPG, JPEG, TIFF  
**Max Size**: 25 MB  
**Response**:
```json
{
  "success": true,
  "document": {
    "id": 1,
    "filename": "report.pdf",
    "file_type": "pdf",
    "status": "UPLOADED"
  }
}
```

---

### Orchestrated Processing (Production)
```http
POST /documents/{document_id}/process
```

**Workflow**: Upload → Extract → Chunk → Index (fully automated)

**Response**:
```json
{
  "success": true,
  "result": {
    "document_id": 1,
    "status": "INDEXED",
    "chunks_indexed": 42
  }
}
```

---

### Question Answering
```http
POST /questions/ask
Content-Type: application/json

{
  "document_id": 1,
  "question": "What are the key findings?",
  "top_k": 5
}
```

**Response**:
```json
{
  "success": true,
  "answer": "Based on the uploaded document, the most relevant excerpts are:\n\n[Context 1]\n\n---\n\n[Context 2]...",
  "sources": [
    {
      "chunk_id": 12,
      "chunk_index": 5,
      "preview": "The study revealed..."
    }
  ]
}
```

---

### Debug Endpoints (Optional)

```http
POST /documents/{document_id}/extract  # Test extraction only
POST /documents/{document_id}/index    # Test indexing only
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- Tesseract OCR installed on system
- 2GB+ RAM (for FAISS indexing)

### Local Development

```bash
# 1. Clone repository
git clone <repo-url>
cd doc_ai_backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Tesseract OCR
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# 5. Create storage directories
mkdir -p storage/uploads storage/indexes

# 6. Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API Documentation: `http://localhost:8000/docs`

---

### AWS EC2 Deployment

```bash
# 1. Launch EC2 instance (Ubuntu 22.04, t3.medium recommended)

# 2. SSH into instance
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# 3. Install system dependencies
sudo apt update
sudo apt install -y python3.11 python3-pip tesseract-ocr

# 4. Clone and setup
git clone <repo-url>
cd doc_ai_backend
pip install -r requirements.txt

# 5. Run with systemd (production) or tmux/screen
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 6. Configure security group: Allow inbound TCP 8000
```

**Production Considerations**:
- Use Nginx reverse proxy for HTTPS
- Implement rate limiting
- Add authentication middleware
- Set up CloudWatch logging
- Use RDS instead of SQLite for multi-instance deployments

---

## 🛠️ Technology Stack

| Component | Technology | Justification |
|-----------|-----------|---------------|
| **API Framework** | FastAPI | Async support, auto-docs, type safety |
| **ORM** | SQLAlchemy 2.0 | Type-safe database interactions |
| **Vector Store** | FAISS | Industry-standard, 10M+ vectors/sec |
| **Embeddings** | all-MiniLM-L6-v2 | 384-dim, 120M params, fast inference |
| **PDF Parsing** | PyMuPDF | 3x faster than PyPDF2 |
| **OCR** | Tesseract | Open-source, multi-language support |
| **Database** | SQLite | Zero-config, perfect for MVP |

---

## 📊 Performance Benchmarks

- **Upload**: 1-5 seconds (25MB PDF)
- **Text Extraction**: 2-10 seconds (depends on OCR needs)
- **Indexing**: 1-3 seconds (10,000 words)
- **Query Latency**: <200ms (top-5 retrieval)

---

## 🔐 Error Handling

All endpoints return structured error responses:

```json
{
  "detail": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Unsupported file type '.docx'. Allowed: ['.jpg', '.jpeg', '.pdf', '.png', '.tiff']"
  }
}
```

**Error Codes**:
- `NO_FILE`, `EMPTY_FILE`, `FILE_TOO_LARGE`
- `UNSUPPORTED_FILE_TYPE`
- `TEXT_EXTRACTION_FAILED`, `PROCESSING_FAILED`, `QA_FAILED`
- `INVALID_STATE`

---

## 🎯 Future Enhancements (Roadmap)

- [ ] LLM integration for generative answers (OpenAI/Anthropic)
- [ ] Multi-document cross-referencing
- [ ] Hybrid search (keyword + semantic)
- [ ] PostgreSQL + pgvector for production scale
- [ ] Async task queue (Celery/Redis) for large files
- [ ] Streaming responses for real-time feedback
- [ ] Document version control
- [ ] Multi-user support with authentication

---

## 📝 File Structure

```
doc_ai_backend/
├── app/
│   ├── main.py                    # FastAPI application factory
│   ├── agents/                    # Core AI agents (isolated)
│   │   ├── ingestion_agent.py    # PDF/Image → Text
│   │   ├── indexing_agent.py     # Text → Vectors
│   │   └── qa_agent.py           # Query → Answer
│   ├── api/
│   │   └── routes.py             # REST endpoints
│   ├── services/                  # Business logic layer
│   │   ├── orchestrator.py       # Workflow coordinator
│   │   ├── ingestion_service.py  # Ingestion wrapper
│   │   ├── indexing_service.py   # Indexing wrapper
│   │   ├── qa_service.py         # Q&A wrapper
│   │   ├── storage.py            # File I/O utilities
│   │   └── validators.py         # Input validation
│   ├── db/
│   │   ├── base.py               # SQLAlchemy base
│   │   ├── session.py            # DB connection pool
│   │   └── models.py             # Document & Chunk models
│   └── core/
│       └── config.py             # Application configuration
├── storage/
│   ├── uploads/                  # User uploaded files
│   └── indexes/                  # FAISS indices + mappings
├── requirements.txt
└── README.md
```

**Built with attention to production-ready patterns, scalability, and maintainability.**
