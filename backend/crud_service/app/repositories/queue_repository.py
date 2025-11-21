from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, case
from sqlalchemy.orm import selectinload
from app.schemas.schemas import CrewRunQueue as CrewRunQueueDB
from app.models.models import QueueStatus


class QueueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def enqueue_crew_run(self, crew_run_id: UUID) -> CrewRunQueueDB:
        """Enqueue a crew run by creating a queue entry with QUEUED status."""
        queue_entry = CrewRunQueueDB(
            crew_run_id=crew_run_id,
            status=QueueStatus.QUEUED,
            visible_at=datetime.now(timezone.utc)
        )
        self.session.add(queue_entry)
        await self.session.flush()
        await self.session.refresh(queue_entry)
        return queue_entry

    async def claim_next_job(self, visibility_timeout_seconds: int = 300) -> CrewRunQueueDB | None:
        """
        Claim the next available job from the queue using SKIP LOCKED.
        Returns None if no job is available.
        
        Args:
            visibility_timeout_seconds: How long the job should remain invisible after claiming (default 5 minutes)
        """
        lease_token = str(uuid4())
        new_visible_at = datetime.now(timezone.utc) + timedelta(seconds=visibility_timeout_seconds)
        
        query = (
            select(CrewRunQueueDB)
            .options(selectinload(CrewRunQueueDB.crew_run))
            .where(
                and_(
                    CrewRunQueueDB.status.in_([QueueStatus.QUEUED, QueueStatus.FAILED]),
                    CrewRunQueueDB.visible_at <= datetime.now(timezone.utc)
                )
            )
            .order_by(
                case(
                    (CrewRunQueueDB.status == QueueStatus.QUEUED, 0),
                    (CrewRunQueueDB.status == QueueStatus.FAILED, 1),
                    else_=2
                ),
                CrewRunQueueDB.created_at
            )
            .limit(1)
            .with_for_update(skip_locked=True) # Use SKIP LOCKED to claim a job atomically
        )
        
        result = await self.session.execute(query)
        job = result.scalar_one_or_none()
        
        if job:
            setattr(job, "status", QueueStatus.CLAIMED.value)
            setattr(job, "lease_token", lease_token)
            setattr(job, "visible_at", new_visible_at)
            await self.session.commit()
            await self.session.refresh(job)
            return job
        
        return None

    async def update_status(
        self,
        queue_id: UUID,
        lease_token: str,
        status: QueueStatus
    ) -> CrewRunQueueDB | None:
        """
        Update the status of a queue entry, verifying the lease token.
        Returns None if the lease token doesn't match or job not found.
        """
        query = (
            select(CrewRunQueueDB)
            .where(
                and_(
                    CrewRunQueueDB.id == queue_id,
                    CrewRunQueueDB.lease_token == lease_token
                )
            )
        )
        result = await self.session.execute(query)
        job = result.scalar_one_or_none()
        
        if job:
            setattr(job, "status", status.value)
            await self.session.commit()
            await self.session.refresh(job)
            return job
        
        return None

    async def heartbeat(
        self,
        queue_id: UUID,
        lease_token: str,
        visibility_timeout_seconds: int = 300
    ) -> CrewRunQueueDB | None:
        """
        Extend the visibility timeout (lease renewal) for a claimed job.
        Returns None if the lease token doesn't match or job not found.
        """
        new_visible_at = datetime.now(timezone.utc) + timedelta(seconds=visibility_timeout_seconds)
        
        query = (
            select(CrewRunQueueDB)
            .where(
                and_(
                    CrewRunQueueDB.id == queue_id,
                    CrewRunQueueDB.lease_token == lease_token,
                    CrewRunQueueDB.status == QueueStatus.CLAIMED
                )
            )
        )
        result = await self.session.execute(query)
        job = result.scalar_one_or_none()
        
        if job:
            setattr(job, "visible_at", new_visible_at)
            await self.session.commit()
            await self.session.refresh(job)
            return job
        
        return None

    async def get_queue_entry_by_crew_run_id(self, crew_run_id: UUID) -> CrewRunQueueDB | None:
        """Retrieve a queue entry by crew_run_id."""
        query = (
            select(CrewRunQueueDB)
            .where(CrewRunQueueDB.crew_run_id == crew_run_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

