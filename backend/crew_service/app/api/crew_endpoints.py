from uuid import UUID
from fastapi import APIRouter, Depends
from app.dependencies import get_crew_service, get_user_token
from app.models.models import (
    CrewRun,
    CrewRunCreateRequest,
    CrewRunRetryRequest,
    RequiredInputsResponse,
)
from app.services.crew_service import CrewService

crew_router = APIRouter(
    prefix="/crew",
    tags=["crew"],
)

@crew_router.get(
    "/{crew_id}/required-inputs",
    response_model=RequiredInputsResponse,
)
async def get_required_inputs(
    crew_id: UUID,
    user_token: str = Depends(get_user_token),
    crew_service: CrewService = Depends(get_crew_service)
):
    """Get required inputs for a crew based on its tasks and flow dependencies."""
    return await crew_service.get_required_inputs(crew_id, user_token)

@crew_router.post(
    "/kickoff",
    response_model=CrewRun,
    status_code=201,
)
async def crew_kickoff(
    crew_run_data: CrewRunCreateRequest,
    user_token: str = Depends(get_user_token),
    crew_service: CrewService = Depends(get_crew_service)
):
    """Kick off a crew run. Only crew owners can kick off their crews."""
    return await crew_service.kickoff_crew_run(crew_run_data, user_token)

@crew_router.post(
    "/crew-run/{crew_run_id}/cancel",
    status_code=204,
)
async def crew_run_cancel(
    crew_run_id: UUID,
    user_token: str = Depends(get_user_token),
    crew_service: CrewService = Depends(get_crew_service)
):
    """Cancel a crew run."""
    return await crew_service.cancel_crew_run(crew_run_id, user_token)

@crew_router.post(
    "/crew-run/{crew_run_id}/retry",
    response_model=CrewRun,
    status_code=201,
)
async def crew_run_retry(
    retry_request: CrewRunRetryRequest,
    crew_run_id: UUID,
    user_token: str = Depends(get_user_token),
    crew_service: CrewService = Depends(get_crew_service)
):
    """Retry a crew run."""
    return await crew_service.retry_crew_run(retry_request, crew_run_id, user_token)
