from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health, invoices
from app.config import settings
from app.core.exceptions import AppError
from app.core.exception_handlers import app_error_handler, unhandled_exception_handler
from app.logging_config import configure_logging

API_DESCRIPTION = """
AI-powered invoice extraction for a construction company. Vendors send PDF invoices;
this API extracts structured data from them with Gemini, stores it in PostgreSQL, and
exposes it for search, filtering, and review.

**Workflow**: upload a PDF (or trigger mock-inbox ingestion) → text is pulled from the
PDF → Gemini returns structured JSON → the result is validated and persisted → the
invoice is queryable via the list/detail endpoints.

Extraction is synchronous and fail-fast per file: a failure at any step for one file
persists nothing and does not affect the other files in the same batch. Per-file
success/failure is reported in the response body of the upload endpoints, not via HTTP
error status codes.
"""

OPENAPI_TAGS = [
    {"name": "health", "description": "Service liveness check."},
    {
        "name": "invoices",
        "description": "Upload invoice PDFs for AI extraction, and search, filter, and "
        "retrieve the resulting structured invoice data.",
    },
]


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Invoice Extraction API",
        summary="AI-powered invoice extraction and search for construction vendor invoices.",
        description=API_DESCRIPTION,
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(invoices.router, prefix="/api/v1")

    return app


app = create_app()
