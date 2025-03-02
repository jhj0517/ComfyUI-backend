from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal

router = APIRouter(
    tags=["system"],
)

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: Literal["healthy", "unhealthy"] = Field(..., description="Current health status of the API")

@router.get(
    "/health", 
    summary="Health check",
    response_model=HealthResponse,
    responses={
        200: {"description": "API is healthy and running normally"}
    }
)
async def health_check():
    """
    Simple health check endpoint to verify the API is running.
    Returns a status indicating the health of the API.
    """
    return HealthResponse(status="healthy") 