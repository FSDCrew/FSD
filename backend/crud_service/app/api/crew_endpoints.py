from uuid import UUID
from fastapi import APIRouter, Query, Depends, HTTPException

from app.models.models import CrewCreate, CrewRead, CrewUpdate
from app.services.crew_service import CrewService
from app.dependencies import get_crew_service

crew_router = APIRouter(
    prefix="/crew",
    tags=["crew"],
)

@crew_router.get(
    "/",
    status_code=200,
    response_model=CrewRead | list[CrewRead],
)
async def get_crews(
    crew_id: UUID | None = Query(None, description="Optional Crew ID to filter"),
    service: CrewService = Depends(get_crew_service),
):
    """Get crews, optionally filtered by crew_id."""
    if crew_id:
        return await service.get_crew_with_tasks(crew_id)
    return await service.get_crews_with_tasks()

@crew_router.post(
    "/",
    status_code=201,
    response_model=CrewRead,
)
async def create_crew(
    crew: CrewCreate,
    service: CrewService = Depends(get_crew_service),
):
    """Create a new crew."""
    return await service.create_crew(crew)

@crew_router.put(
    "/",
    status_code=200,
    response_model=CrewRead,
)
async def update_crew(
    crew: CrewUpdate,
    service: CrewService = Depends(get_crew_service),
):
    """Update an existing crew."""
    return await service.update_crew(crew)