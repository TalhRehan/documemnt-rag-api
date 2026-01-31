from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # doc_ai_backend/
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
DB_PATH = BASE_DIR / "storage" / "app.db"

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB (adjust if you want)
