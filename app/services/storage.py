import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import UPLOAD_DIR

def ensure_storage_dirs():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def infer_file_type(ext: str) -> str:
    return "pdf" if ext == ".pdf" else "image"

def safe_filename(original_name: str) -> str:
    # Keep extension; replace name with uuid to avoid collisions / weird chars
    ext = Path(original_name).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"

async def save_upload(file: UploadFile) -> Path:
    ensure_storage_dirs()
    filename = safe_filename(file.filename)
    dest = UPLOAD_DIR / filename

    content = await file.read()
    dest.write_bytes(content)

    # reset pointer (good habit)
    file.file.seek(0)
    return dest
