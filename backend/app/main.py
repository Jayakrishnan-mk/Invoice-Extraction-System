from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health
from app.config import settings
from app.core.exceptions import AppError
from app.core.exception_handlers import app_error_handler, unhandled_exception_handler
from app.logging_config import configure_logging


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="Invoice Extraction API", version="0.1.0")

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

    return app


app = create_app()
