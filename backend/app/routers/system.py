from fastapi import APIRouter

router = APIRouter(
    tags=["system"],
)

@router.get("/health", summary="Health check")
async def health_check():
    """
    Simple health check endpoint to verify the API is running.
    """
    return {"status": "healthy"} 