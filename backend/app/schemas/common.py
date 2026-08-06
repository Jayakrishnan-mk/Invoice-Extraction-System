from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    """Shape of every error response raised by ``AppError`` and its subclasses."""

    model_config = ConfigDict(json_schema_extra={"example": {"detail": "Invoice not found"}})

    detail: str


class HealthResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok"}})

    status: str
