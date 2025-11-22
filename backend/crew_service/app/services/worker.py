import asyncio
import logging
import httpx
from uuid import UUID

from config import settings
from app.services.job_executor import JobExecutor
from app.api.crud_client import AuthenticatedClient
from app.api.crud_client.api.internal import (
    claim_next_job_internal_internal_queue_claim_post as claim_next_job_func,
    update_queue_status_internal_internal_queue_queue_id_status_put as update_queue_status_func,
)
from app.api.crud_client.models.update_status_request import UpdateStatusRequest
from app.api.crud_client.models.queue_status import QueueStatus
from app.api.crud_client.models.claim_job_response import ClaimJobResponse
from app.api.crud_client import errors

logger = logging.getLogger(__name__)


class Worker:
    """Worker that polls the db queue from CrudService and executes jobs."""
    
    def __init__(self):
        timeout = httpx.Timeout(30.0)
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token = settings.INTERNAL_CREW_API_KEY,
            timeout=timeout
        )
        self.job_executor = JobExecutor()
        self.running_jobs: dict[UUID, tuple[asyncio.Task, str]] = {}  # { queue_id: (task, lease_token) }
        self._running = False
    
    async def start(self):
        """Start the worker polling the db queue from CrudService and executing jobs."""
        self._running = True
        logger.info("Worker started")
        
        while self._running:
            try:
                await self._poll_and_process()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
            
            await asyncio.sleep(settings.QUEUE_POLL_INTERVAL_SECONDS)
    
    async def stop(self):
        """Stop the worker. Cancels all running tasks and marks them as failed."""
        self._running = False
        logger.info("Worker stopping...")
        
        if self.running_jobs:
            logger.info(f"Stopping {len(self.running_jobs)} running jobs and marking them as failed...")
            
            for job_id, (task, lease_token) in self.running_jobs.items():
                task.cancel()
                try:
                    body = UpdateStatusRequest(
                        lease_token=lease_token,
                        status=QueueStatus.FAILED
                    )
                    await update_queue_status_func.asyncio(
                        queue_id=job_id,
                        client=self.crud_client,
                        body=body
                    )
                    logger.info(f"Marked job {job_id} as FAILED due to shutdown")
                except Exception as e:
                    logger.error(f"Failed to mark job {job_id} as FAILED: {e}")
        
        logger.info("Worker stopped")
    
    async def _poll_and_process(self):
        """Poll the queue and process a job if available."""
        try:
            from app.api.crud_client.types import Unset
            
            timeout: int | Unset = settings.JOB_VISIBILITY_TIMEOUT_SECONDS
            result = await claim_next_job_func.asyncio(
                client=self.crud_client,
                visibility_timeout_seconds=timeout
            )
            
            if result is None:
                return
            
            if isinstance(result, ClaimJobResponse):
                job = result
                logger.info(f"Claimed job: {job.id} for crew_run: {job.crew_run_id}")
                
                task = asyncio.create_task(
                    self._execute_job(job)
                )
                self.running_jobs[job.id] = (task, job.lease_token)
                
                self._cleanup_completed_tasks()
        except errors.UnexpectedStatus as e:
            if e.status_code == 404:
                # No job available, this is normal
                return
            logger.error(f"Error claiming job: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error claiming job: {e}", exc_info=True)
    
    async def _execute_job(self, job: ClaimJobResponse):
        """Execute a claimed job."""
        try:
            logger.info(f"Starting execution of job {job.id} for crew_run {job.crew_run_id}")
            
            await self.job_executor.execute(
                crew_run_id=job.crew_run_id,
                crew_id=job.crew_id,
                queue_id=job.id,
                lease_token=job.lease_token
            )
            
            body = UpdateStatusRequest(
                lease_token=job.lease_token,
                status=QueueStatus.COMPLETED
            )
            await update_queue_status_func.asyncio(
                queue_id=job.id,
                client=self.crud_client,
                body=body
            )
            
            logger.info(f"Job {job.id} completed successfully")
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}", exc_info=True)
            
            try:
                body = UpdateStatusRequest(
                    lease_token=job.lease_token,
                    status=QueueStatus.FAILED
                )
                await update_queue_status_func.asyncio(
                    queue_id=job.id,
                    client=self.crud_client,
                    body=body
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status to FAILED: {update_error}")
        finally:
            if job.id in self.running_jobs:
                del self.running_jobs[job.id]
    
    def _cleanup_completed_tasks(self):
        """Remove completed tasks from running_jobs."""
        completed = [
            job_id for job_id, (task, _) in self.running_jobs.items()
            if task.done()
        ]
        for job_id in completed:
            del self.running_jobs[job_id]

