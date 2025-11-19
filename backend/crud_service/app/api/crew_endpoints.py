from uuid import UUID
from fastapi import APIRouter, Query, Depends

from app.models.models import CrewCreate, CrewRead, CrewUpdate, User
from app.services.crew_service import CrewService
from app.dependencies import get_crew_service, get_current_user

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
    current_user: User = Depends(get_current_user),
    service: CrewService = Depends(get_crew_service),
):
    """Get crews, optionally filtered by crew_id."""
    if crew_id:
        return await service.get_fully_loaded_crew_by_id(crew_id, current_user.id)
    return await service.get_all_fully_loaded_crews(current_user.id)

@crew_router.post(
    "/",
    status_code=201,
    response_model=CrewRead,
)
async def create_crew(
    crew: CrewCreate,
    current_user: User = Depends(get_current_user),
    service: CrewService = Depends(get_crew_service),
):
    """Create a new crew."""
    return await service.create_crew(crew, current_user.id)

@crew_router.put(
    "/",
    status_code=200,
    response_model=CrewRead,
)
async def update_crew(
    crew: CrewUpdate,
    current_user: User = Depends(get_current_user),
    service: CrewService = Depends(get_crew_service),
):
    """Update an existing crew."""
    return await service.update_crew(crew, current_user)

@crew_router.delete(
    "/{crew_id}",
    status_code=204,
    response_model=None,
)
async def delete_crew(
    crew_id: UUID,
    current_user: User = Depends(get_current_user),
    service: CrewService = Depends(get_crew_service),
):
    """Delete an existing crew."""
    await service.delete_crew(crew_id, current_user.id)
    return None