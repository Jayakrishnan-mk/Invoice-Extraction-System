from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
def health_check() -> HealthResponse:
    """Returns 200 with a static payload if the API process is up."""
    return HealthResponse(status="ok")
