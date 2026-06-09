from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Returns a minimal health status for the Mindvox API.",
)
def health_check():
    return {
        "status": "ok",
        "service": "mindvox-api",
        "version": "v1.0.0",
    }
