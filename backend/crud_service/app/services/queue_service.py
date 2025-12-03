from uuid import UUID
from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from app.repositories.queue_repository import QueueRepository
from app.models.models import QueueStatus, ClaimJobResponse, HeartbeatResponse
from datetime import datetime, timezone


class QueueService:
    def __init__(self, repository: QueueRepository):
        self.repository = repository

    async def claim_next_job(self, visibility_timeout_seconds: int = 300) -> ClaimJobResponse | None:
        """
        Claim the next available job from the queue.
        Returns None if no job is available.
        """
        db_job = await self.repository.claim_next_job(visibility_timeout_seconds)
        
        if db_job:
            crew_id = db_job.crew_run.crew_id if db_job.crew_run else None
            if crew_id is None:
                raise ValueError(f"Crew run {db_job.crew_run_id} not found or has no crew_id")
            
            return ClaimJobResponse.model_validate({
                "id": db_job.id,
                "crew_run_id": db_job.crew_run_id,
                "crew_id": crew_id,
                "status": db_job.status,
                "lease_token": db_job.lease_token,
                "visible_at": db_job.visible_at.isoformat(),
            })
        return None

    async def update_queue_status(
        self,
        queue_id: UUID,
        lease_token: str,
        status: QueueStatus
    ) -> ClaimJobResponse | None:
        """
        Update the status of a queue entry.
        Requires valid lease_token so that only the worker that claimed the job can update the status.
        Increments retry_count if status is FAILED.
        Sets visible_at to now if status is FAILED so it can be retried immediately.
        Raises HTTPException if queue entry not found or lease token invalid.
        Returns the updated queue entry as ClaimJobResponse.
        """
        db_job = await self.repository.get_queue_entry(queue_id, lease_token)
        
        if not db_job:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Queue entry not found or lease token invalid"
            )
        
        retry_count = None
        visible_at = None
        if status == QueueStatus.FAILED:
            current_retry_count = getattr(db_job, "retry_count", 0) or 0
            retry_count = current_retry_count + 1
            visible_at = datetime.now(timezone.utc)
        
        updated_job = await self.repository.update_status(queue_id, lease_token, status, retry_count, visible_at)
        assert updated_job is not None, "Job should exist after validation"
        
        crew_id = updated_job.crew_run.crew_id if updated_job.crew_run else None
        if crew_id is None:
            raise ValueError(f"Crew run {updated_job.crew_run_id} not found or has no crew_id")
        
        return ClaimJobResponse.model_validate({
            "id": updated_job.id,
            "crew_run_id": updated_job.crew_run_id,
            "crew_id": crew_id,
            "status": updated_job.status,
            "lease_token": updated_job.lease_token,
            "visible_at": updated_job.visible_at.isoformat(),
        })

    async def heartbeat(
        self,
        queue_id: UUID,
        lease_token: str,
        visibility_timeout_seconds: int = 300
    ) -> HeartbeatResponse:
        """
        Extend the visibility timeout (lease renewal) for a claimed job.
        Returns dict with cancel_requested flag, queue_id, visible_at timestamp, and status.
        Raises HTTPException if queue entry not found, lease token invalid, or job not in CLAIMED status.
        """
        db_job = await self.repository.heartbeat(queue_id, lease_token, visibility_timeout_seconds)
        
        if not db_job:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Queue entry not found, lease token invalid, or job not in CLAIMED status"
            )
        
        cancel_requested = db_job.cancel_requested
        
        return HeartbeatResponse.model_validate({
            "status": "heartbeat_sent",
            "queue_id": str(queue_id),
            "visible_at": db_job.visible_at.isoformat(),
            "cancel_requested": cancel_requested,
        })

