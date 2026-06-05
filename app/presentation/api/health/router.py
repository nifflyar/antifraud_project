from fastapi import APIRouter

from .schemas import HealthCheckResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthCheckResponse)
async def health_check_handler() -> HealthCheckResponse:
    """Health check endpoint to verify that the application is running."""
    return HealthCheckResponse()


health_router = router
