class AppError(Exception):
    """Base class for application-level errors that map to a specific HTTP response."""

    status_code = 500
    detail = "Internal server error"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = 404
    detail = "Resource not found"


class PDFExtractionError(AppError):
    status_code = 422
    detail = "Failed to extract text from PDF"


class AIExtractionError(AppError):
    status_code = 502
    detail = "Failed to extract structured invoice data"
