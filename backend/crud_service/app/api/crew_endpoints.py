from uuid import UUID
from fastapi import APIRouter, Query, Depends, Path

from app.models.models import CrewCreate, CrewRead, CrewUpdate, User
from app.services.crew_service import CrewService
from app.dependencies import get_crew_service, get_current_user

crew_router = APIRouter(
    prefix="/crew",
    tags=["crew"],
)

@crew_router.get(
    "/{crew_id}",
    status_code=200,
    response_model=CrewRead,
)
async def get_crew_by_id(
    crew_id: UUID = Path(..., description="Crew ID to retrieve"),
    current_user: User = Depends(get_current_user),
    service: CrewService = Depends(get_crew_service),
):
    """Get a single crew by ID."""
    return await service.get_fully_loaded_crew_by_id(crew_id, current_user.id)

@crew_router.get(
    "/",
    status_code=200,
    response_model=list[CrewRead],
)
async def get_all_crews(
    current_user: User = Depends(get_current_user),
    service: CrewService = Depends(get_crew_service),
):
    """Get all crews for the current user."""
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