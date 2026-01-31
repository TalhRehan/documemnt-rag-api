from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES

def validate_upload(file: UploadFile) -> str:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail={"code": "NO_FILE", "message": "No file provided."})

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail={
                "code": "UNSUPPORTED_FILE_TYPE",
                "message": f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
            }
        )
    return ext

async def validate_size(file: UploadFile) -> None:
    # Read file into memory once in Phase 1 for simplicity; later we can stream if needed.
    data = await file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail={"code": "EMPTY_FILE", "message": "Uploaded file is empty."})
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": f"File exceeds {MAX_FILE_SIZE_BYTES} bytes limit."}
        )
    # Put pointer back for subsequent reads
    file.file.seek(0)
