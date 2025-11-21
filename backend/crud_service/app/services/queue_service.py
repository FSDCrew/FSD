from uuid import UUID
from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND
from app.repositories.queue_repository import QueueRepository
from app.models.models import QueueStatus, ClaimJobResponse


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
            
            response_data = {
                "id": db_job.id,
                "crew_run_id": db_job.crew_run_id,
                "crew_id": crew_id,
                "status": db_job.status,
                "lease_token": db_job.lease_token,
                "visible_at": db_job.visible_at.isoformat(),
            }
            return ClaimJobResponse.model_validate(response_data)
        return None

    async def update_queue_status(
        self,
        queue_id: UUID,
        lease_token: str,
        status: QueueStatus
    ) -> None:
        """
        Update the status of a queue entry.
        Requires valid lease_token so that only the worker that claimed the job can update the status.
        Raises HTTPException if queue entry not found or lease token invalid.
        """
        db_job = await self.repository.update_status(queue_id, lease_token, status)
        
        if not db_job:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Queue entry not found or lease token invalid"
            )

    async def heartbeat(
        self,
        queue_id: UUID,
        lease_token: str,
        visibility_timeout_seconds: int = 300
    ) -> dict:
        """
        Extend the visibility timeout (lease renewal) for a claimed job.
        Returns dict with status and visible_at timestamp.
        Raises HTTPException if queue entry not found, lease token invalid, or job not in CLAIMED status.
        """
        db_job = await self.repository.heartbeat(queue_id, lease_token, visibility_timeout_seconds)
        
        if not db_job:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Queue entry not found, lease token invalid, or job not in CLAIMED status"
            )
        
        return {
            "status": "heartbeat_sent",
            "queue_id": str(queue_id),
            "visible_at": db_job.visible_at.isoformat()
        }

