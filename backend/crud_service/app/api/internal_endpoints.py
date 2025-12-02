import base64
import io
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from app.models.models import (
    ArtifactRead,
    ArtifactServerCreate,
    ClaimJobResponse,
    CrewRead,
    CrewRunCreate,
    CrewRunRead,
    HeartbeatRequest,
    HeartbeatResponse,
    UpdateStatusRequest,
)
from app.dependencies import (
    get_artifact_service,
    get_auth_service,
    get_crew_run_owner_id,
    get_crew_run_service,
    get_internal_service,
    get_queue_service,
    require_internal_api_key,
)
from app.services.artifact_service import ArtifactService
from app.services.auth_service import AuthService
from app.services.crew_run_service import CrewRunService
from app.services.internal_service import InternalService
from app.services.queue_service import QueueService

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


@internal_router.get(
    "/crew-run/{crew_run_id}",
    status_code=200,
    response_model=CrewRunRead,
    dependencies=[Depends(require_internal_api_key)],
)
async def get_crew_run_by_id(
    crew_run_id: UUID = Path(..., description="Crew Run ID to retrieve"),
    service: InternalService = Depends(get_internal_service),
):
    """Get a single crew run by ID (internal use only)."""
    return await service.get_crew_run_by_id(crew_run_id)


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


@internal_router.post(
    "/crew-run/{crew_run_id}/cancel",
    status_code=200,
    dependencies=[Depends(require_internal_api_key)],
)
async def cancel_crew_run_internal(
    crew_run_id: UUID = Path(..., description="Crew Run ID to cancel"),
    user_token: str = Body(..., description="User's JWT token for authentication"),
    service: CrewRunService = Depends(get_crew_run_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Cancel a crew run via internal API."""
    user = await auth_service.get_user(user_token)
    return await service.cancel_crew_run(crew_run_id, user.id)


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
    return await service.update_queue_status(queue_id, request.lease_token, request.status)


@internal_router.post(
    "/queue/{queue_id}/heartbeat",
    status_code=200,
    response_model=HeartbeatResponse,
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


@internal_router.post(
    "/artifact/{crew_run_id}",
    status_code=201,
    response_model=ArtifactRead,
    dependencies=[Depends(require_internal_api_key)],
)
async def create_artifact_internal(
    artifact_upload: ArtifactServerCreate,
    crew_run_id: UUID = Path(
        ...,
        description="Crew Run ID to associate the artifact with",
        example="123e4567-e89b-12d3-a456-426614174000",
    ),
    crew_run_owner_id: UUID = Depends(get_crew_run_owner_id),
    artifact_service: ArtifactService = Depends(get_artifact_service),
):
    """Internal-only endpoint for Base64 artifact uploads."""

    try:
        file_bytes = base64.b64decode(artifact_upload.file_content_base64)
        file_stream = io.BytesIO(file_bytes)

        uploaded_file = {
            "file": file_stream,
            "filename": artifact_upload.file_name,
            "content_type": "application/octet-stream",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Base64 content: {e}",
        )

    return await artifact_service.create_artifact(
        uploaded_file=uploaded_file,
        artifact_type=artifact_upload.type,
        crew_run_id=crew_run_id,
        user_id=crew_run_owner_id,
    )
