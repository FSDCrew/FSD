from fastapi import APIRouter, Depends, Path, Body
from uuid import UUID
from typing import Dict, Any
from app.models.models import CrewRunRead, CrewRunCreate, User
from app.services.crew_run_service import CrewRunService
from app.dependencies import get_crew_run_service, get_current_user

crew_run_router = APIRouter(
    prefix="/crew-run",
    tags=["crew-run"],
)

@crew_run_router.post(
    "/",
    status_code=201,
    response_model=CrewRunRead
)
async def create_crew_run(
    crew_run_data: CrewRunCreate,
    current_user: User = Depends(get_current_user), 
    service: CrewRunService = Depends(get_crew_run_service),
):
    """Create a new crew run record for a crew and enqueue it."""
    return await service.create_crew_run(crew_run_data, current_user.id)

@crew_run_router.get(
    "/{crew_run_id}",
    response_model=CrewRunRead
)
async def get_crew_run(
    crew_run_id: UUID = Path(..., description="Crew Run ID to retrieve"),
    current_user: User = Depends(get_current_user),
    service: CrewRunService = Depends(get_crew_run_service),
):
    """Retrieve a crew run and all associated artifacts."""
    return await service.get_crew_run_by_id_with_artifacts(crew_run_id, current_user.id)

@crew_run_router.put(
    "/{crew_run_id}/output",
    status_code=200,
    response_model=CrewRunRead
)
async def update_crew_run_output(
    crew_run_id: UUID = Path(..., description="Crew Run ID to update"),
    output: Dict[str, Any] = Body(..., description="Output data to update"),
    service: CrewRunService = Depends(get_crew_run_service),
):
    """Update the output of a crew run. Used by CrewService to post results."""
    return await service.update_crew_run_output(crew_run_id, output)