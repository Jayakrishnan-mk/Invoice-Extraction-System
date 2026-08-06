import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import InvalidFileError

_ALLOWED_EXTENSION = ".pdf"


def validate_pdf_upload(file: UploadFile, max_size_bytes: int) -> bytes:
    """Reads and validates an uploaded file, returning its bytes on success."""
    if not (file.filename or "").lower().endswith(_ALLOWED_EXTENSION):
        raise InvalidFileError(f"'{file.filename}' is not a PDF file")

    content = file.file.read()
    if not content:
        raise InvalidFileError(f"'{file.filename}' is empty")
    if len(content) > max_size_bytes:
        raise InvalidFileError(
            f"'{file.filename}' exceeds the {max_size_bytes // (1024 * 1024)}MB upload limit"
        )

    return content


def save_pdf(content: bytes, original_filename: str, upload_dir: str | Path) -> Path:
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    destination = upload_path / f"{uuid.uuid4()}_{Path(original_filename).name}"
    destination.write_bytes(content)
    return destination
