from fastapi import APIRouter, Depends
from uuid import UUID
from app.services.queue_service import QueueService
from app.models.models import ClaimJobResponse, UpdateStatusRequest, HeartbeatRequest
from app.dependencies import get_queue_service


queue_router = APIRouter(
    prefix="/queue",
    tags=["queue"],
)


@queue_router.post(
    "/claim",
    response_model=ClaimJobResponse | None,
    status_code=200
)
async def claim_next_job(
    visibility_timeout_seconds: int = 300,
    service: QueueService = Depends(get_queue_service),
):
    """
    Claim the next available job from the queue.
    Returns None if no job is available.
    """
    return await service.claim_next_job(visibility_timeout_seconds)


@queue_router.put(
    "/{queue_id}/status",
    response_model=ClaimJobResponse | None,
    status_code=200
)
async def update_queue_status(
    queue_id: UUID,
    request: UpdateStatusRequest,
    service: QueueService = Depends(get_queue_service),
):
    """
    Update the status of a queue entry.
    Requires valid lease_token so that only the worker that claimed the job can update the status.
    This prevents zombie workers from updating the status after they've lost the lease.
    """
    await service.update_queue_status(queue_id, request.lease_token, request.status)
    return {"status": "updated", "queue_id": str(queue_id)}


@queue_router.post(
    "/{queue_id}/heartbeat",
    status_code=200,
)
async def heartbeat(
    queue_id: UUID,
    request: HeartbeatRequest,
    visibility_timeout_seconds: int = 300,
    service: QueueService = Depends(get_queue_service),
):
    """
    Extend the visibility timeout (lease renewal) for a claimed job.
    """
    return await service.heartbeat(queue_id, request.lease_token, visibility_timeout_seconds)

