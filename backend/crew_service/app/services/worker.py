import asyncio
import logging
import multiprocessing
from typing import Any
from uuid import UUID

import httpx

from app.api.crud_client import AuthenticatedClient
from app.api.crud_client import errors
from app.api.crud_client.api.internal import (
    claim_next_job_internal_internal_queue_claim_post as claim_next_job_func,
    update_queue_status_internal_internal_queue_queue_id_status_put as update_queue_status_func,
)
from app.api.crud_client.models.claim_job_response import ClaimJobResponse
from app.api.crud_client.models.queue_status import QueueStatus
from app.api.crud_client.models.update_status_request import UpdateStatusRequest
from app.services.crew_service import CrewService
from app.services.job_executor import JobExecutor
from config import settings

logger = logging.getLogger(__name__)


class Worker:
    """Worker that polls the db queue from CrudService and executes jobs."""
    
    MAX_CONCURRENT_JOBS = 3
    
    def __init__(self, crew_service: CrewService):
        timeout = httpx.Timeout(30.0)
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token = settings.INTERNAL_CREW_API_KEY,
            timeout=timeout
        )
        # Process registry maps crew_run_id -> Process
        self.running_processes: dict[UUID, Any] = {}
        self.job_executor = JobExecutor(crew_service=crew_service, process_registry=self.running_processes)
        self.running_jobs: dict[UUID, tuple[asyncio.Task, str]] = {}  # { queue_id: (task, lease_token) }
        self._running = False
    
    async def start(self):
        """Start the worker polling the db queue from CrudService and executing jobs."""
        self._running = True
        
        while self._running:
            try:
                await self._poll_and_process()
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
            
            await asyncio.sleep(settings.QUEUE_POLL_INTERVAL_SECONDS)
    
    async def stop(self):
        """Stop the worker. Cancels all running tasks and terminates all processes."""
        self._running = False
        
        if self.running_processes:
            logger.info(f"Terminating {len(self.running_processes)} running process(es)...")
            processes_to_stop = list(self.running_processes.items())
            for crew_run_id, process in processes_to_stop:
                if process.is_alive():
                    try:
                        logger.info(f"Terminating process {process.pid} for crew_run {crew_run_id}")
                        process.terminate()
                        process.join(timeout=5.0)
                        if process.is_alive():
                            logger.warning(f"Process {process.pid} did not terminate, killing...")
                            process.kill()
                            process.join()
                    except Exception as e:
                        logger.error(f"Error terminating process {process.pid}: {e}")
            self.running_processes.clear()
        
        if self.running_jobs:
            # Create a copy to avoid RuntimeError if dictionary changes during iteration
            jobs_to_stop = list(self.running_jobs.items())
            for job_id, (task, lease_token) in jobs_to_stop:
                task.cancel()
            
            logger.info(f"Waiting for {len(jobs_to_stop)} job(s) to finish...")
            for job_id, (task, lease_token) in jobs_to_stop:
                try:
                    await asyncio.wait_for(task, timeout=10.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.warning(f"Job {job_id} did not finish within timeout")
                except Exception as e:
                    logger.error(f"Error waiting for job {job_id}: {e}")
                
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
                except Exception as e:
                    logger.error(f"Failed to mark job {job_id} as FAILED: {e}")
        
        try:
            async_client = self.crud_client.get_async_httpx_client()
            await async_client.aclose()
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")
    
    async def _poll_and_process(self):
        """Poll the queue and process a job if available."""
        self._cleanup_completed_tasks()
        self._cleanup_completed_processes()
        
        if len(self.running_jobs) >= self.MAX_CONCURRENT_JOBS:
            return
        
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
                
                task = asyncio.create_task(
                    self._execute_job(job)
                )
                self.running_jobs[job.id] = (task, job.lease_token)
        except errors.UnexpectedStatus as e:
            if e.status_code == 404:
                return
            logger.error(f"Error claiming job: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error claiming job: {e}", exc_info=True)
    
    async def _execute_job(self, job: ClaimJobResponse):
        """Execute a claimed job."""
        try:
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
        except asyncio.CancelledError:
            logger.info(f"Job {job.id} was cancelled")
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
    
    def _cleanup_completed_processes(self):
        """Remove completed processes from running_processes registry."""
        completed = [
            crew_run_id for crew_run_id, process in self.running_processes.items()
            if not process.is_alive()
        ]
        for crew_run_id in completed:
            process = self.running_processes.pop(crew_run_id, None)
            if process:
                try:
                    process.join(timeout=0.1)
                except Exception as e:
                    logger.warning(f"Error joining completed process for crew_run {crew_run_id}: {e}")
                logger.debug(f"Cleaned up completed process for crew_run {crew_run_id}")

