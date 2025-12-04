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
from app.api.crud_client.types import Unset
from app.services.job_executor import run_entire_job  # type: ignore
from config import settings

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
        # Process registry maps queue_id -> Process
        self.running_processes: dict[UUID, Any] = {}
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
        """Stop the worker. Terminates all running processes."""
        self._running = False
        
        if self.running_processes:
            logger.info(f"Terminating {len(self.running_processes)} running process(es)...")
            processes_to_stop = list(self.running_processes.items())
            for queue_id, process in processes_to_stop:
                if process.is_alive():
                    try:
                        logger.info(f"Terminating process {process.pid} for queue {queue_id}")
                        process.terminate()
                        process.join(timeout=5.0)
                        if process.is_alive():
                            logger.warning(f"Process {process.pid} did not terminate, killing...")
                            process.kill()
                            process.join()
                    except Exception as e:
                        logger.error(f"Error terminating process {process.pid}: {e}")
            self.running_processes.clear()
        
        try:
            async_client = self.crud_client.get_async_httpx_client()
            await async_client.aclose()
        except Exception as e:
            logger.error(f"Error closing HTTP client: {e}")
    
    async def _poll_and_process(self):
        """Poll the queue and process a job if available."""
        self._cleanup_completed_processes()
        
        try:          
            timeout: int | Unset = settings.JOB_VISIBILITY_TIMEOUT_SECONDS
            result = await claim_next_job_func.asyncio(
                client=self.crud_client,
                visibility_timeout_seconds=timeout
            )
            
            if result is None:
                return
            
            if isinstance(result, ClaimJobResponse):
                job = result
                
                # Prepare job metadata for child process
                job_metadata = {
                    'crew_run_id': str(job.crew_run_id),
                    'crew_id': str(job.crew_id),
                    'queue_id': str(job.id),
                    'lease_token': job.lease_token
                }
                
                # Spawn child process to handle entire job lifecycle
                process = multiprocessing.Process(
                    target=run_entire_job,
                    args=(job_metadata,)
                )
                process.start()
                self.running_processes[job.id] = process
                logger.info(f"Started process {process.pid} for queue {job.id}")
                
        except errors.UnexpectedStatus as e:
            if e.status_code == 404:
                return
            logger.error(f"Error claiming job: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error claiming job: {e}", exc_info=True)
    
    def _cleanup_completed_processes(self):
        """Remove completed processes from running_processes registry."""
        completed = [
            queue_id for queue_id, process in self.running_processes.items()
            if not process.is_alive()
        ]
        for queue_id in completed:
            process = self.running_processes.pop(queue_id, None)
            if process:
                try:
                    process.join(timeout=0.1)
                except Exception as e:
                    logger.warning(f"Error joining completed process for queue {queue_id}: {e}")
                logger.debug(f"Cleaned up completed process for queue {queue_id}")

