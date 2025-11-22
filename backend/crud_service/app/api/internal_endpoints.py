from fastapi import APIRouter, Depends, Path, Body
from uuid import UUID
from typing import Dict, Any
from app.models.models import (
    CrewRead,
    CrewRunRead,
    CrewRunCreate,
    ClaimJobResponse,
    UpdateStatusRequest,
    HeartbeatRequest,
)
from app.dependencies import (
    get_internal_service,
    require_internal_api_key,
    get_crew_run_service,
    get_queue_service,
    get_auth_service,
)
from app.services.internal_service import InternalService
from app.services.crew_run_service import CrewRunService
from app.services.queue_service import QueueService
from app.services.auth_service import AuthService

internal_router = APIRouter(
    prefix="/internal",
    tags=["internal"],
)

@internal_router.get(
    "/crew/{crew_id}",
    status_code=200,
    response_model=CrewRead,
    dependencies=[Depends(require_internal_api_key)],
)
async def get_crew_by_id(
    crew_id: UUID = Path(..., description="Crew ID to retrieve"),
    service: InternalService = Depends(get_internal_service),
):
    """Get a single crew by ID."""
    return await service.get_fully_loaded_crew_by_id(crew_id)


@internal_router.post(
    "/crew-run/create",
    status_code=201,
    response_model=CrewRunRead,
    dependencies=[Depends(require_internal_api_key)],
)
async def create_crew_run_internal(
    crew_run_data: CrewRunCreate = Body(..., description="Crew run data to create"),
    user_token: str = Body(..., description="User's JWT token for authentication"),
    service: CrewRunService = Depends(get_crew_run_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Create a crew run via internal API. Validates user token and checks ownership."""
    user = await auth_service.get_user(user_token)
    return await service.create_crew_run(crew_run_data, user.id)


@internal_router.put(
    "/crew-run/{crew_run_id}/output",
    status_code=200,
    response_model=CrewRunRead,
    dependencies=[Depends(require_internal_api_key)],
)
async def update_crew_run_output_internal(
    crew_run_id: UUID = Path(..., description="Crew Run ID to update"),
    output: Dict[str, Any] = Body(..., description="Output data to update"),
    service: CrewRunService = Depends(get_crew_run_service),
):
    """Update the output of a crew run via internal API."""
    return await service.update_crew_run_output(crew_run_id, output)


@internal_router.post(
    "/queue/claim",
    response_model=ClaimJobResponse | None,
    status_code=200,
    dependencies=[Depends(require_internal_api_key)],
)
async def claim_next_job_internal(
    visibility_timeout_seconds: int = 300,
    service: QueueService = Depends(get_queue_service),
):
    """Claim the next available job from the queue (internal use only)."""
    return await service.claim_next_job(visibility_timeout_seconds)


@internal_router.put(
    "/queue/{queue_id}/status",
    response_model=ClaimJobResponse | None,
    status_code=200,
    dependencies=[Depends(require_internal_api_key)],
)
async def update_queue_status_internal(
    queue_id: UUID,
    request: UpdateStatusRequest,
    service: QueueService = Depends(get_queue_service),
):
    """Update the status of a queue entry (internal use only)."""
    await service.update_queue_status(queue_id, request.lease_token, request.status)
    return {"status": "updated", "queue_id": str(queue_id)}


@internal_router.post(
    "/queue/{queue_id}/heartbeat",
    status_code=200,
    dependencies=[Depends(require_internal_api_key)],
)
async def heartbeat_internal(
    queue_id: UUID,
    request: HeartbeatRequest,
    visibility_timeout_seconds: int = 300,
    service: QueueService = Depends(get_queue_service),
):
    """Extend the visibility timeout (lease renewal) for a claimed job."""
    return await service.heartbeat(queue_id, request.lease_token, visibility_timeout_seconds)