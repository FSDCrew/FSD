import logging
import multiprocessing
import os
import threading
import time
from typing import Any, Optional, Union
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.api.crud_client import AuthenticatedClient
from app.api.crud_client.api.internal import (
    get_crew_run_by_id_internal_crew_run_crew_run_id_get as get_crew_run_func,
    heartbeat_internal_internal_queue_queue_id_heartbeat_post as heartbeat_func,
    update_queue_status_internal_internal_queue_queue_id_status_put as update_queue_status_func,
)
from app.api.crud_client.models import HeartbeatResponse, HTTPValidationError
from app.api.crud_client.models.heartbeat_request import HeartbeatRequest
from app.api.crud_client.models.queue_status import QueueStatus
from app.api.crud_client.models.update_status_request import UpdateStatusRequest
from app.api.crud_client.types import Unset
from app.dependencies import get_flow_service
from app.models.models import TaskInfo
from app.services.flow.flow_utils import TaskStatusService
from config import settings

logger = logging.getLogger(__name__)

_mp_context = multiprocessing.get_context('spawn')


class HeartbeatThread:
    """Manages synchronous heartbeat loop in a background thread."""
    
    MAX_HEARTBEAT_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1.0
    
    def __init__(
        self,
        crud_client: AuthenticatedClient,
        queue_id: UUID,
        lease_token: str,
        cancellation_event: threading.Event
    ):
        self.crud_client = crud_client
        self.queue_id = queue_id
        self.lease_token = lease_token
        self.cancellation_event = cancellation_event
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self):
        """Start the heartbeat thread."""
        self.thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.thread.start()
        logger.info(f"Started heartbeat thread for queue {self.queue_id}")
    
    def stop(self):
        """Stop the heartbeat thread."""
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning(f"Heartbeat thread for queue {self.queue_id} did not stop within timeout")
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to extend lease with retry logic."""
        try:
            while not self._stop_event.is_set():
                time.sleep(settings.HEARTBEAT_INTERVAL_SECONDS)
                
                if self._stop_event.is_set():
                    break
                
                # Attempt heartbeat with retry logic
                success, cancel_requested = self._send_heartbeat_with_retry()
                
                if cancel_requested:
                    logger.info(f"Cancellation requested for queue {self.queue_id}")
                    self.cancellation_event.set()
                    break
                
                if not success:
                    logger.error(
                        f"Failed to send heartbeat for queue {self.queue_id} after "
                        f"{self.MAX_HEARTBEAT_RETRIES} retries. Continuing heartbeat loop."
                    )
        except Exception as e:
            logger.error(f"Error in heartbeat loop for queue {self.queue_id}: {e}", exc_info=True)
    
    def _send_heartbeat_with_retry(self) -> tuple[bool, bool]:
        """
        Send heartbeat request with retry logic and exponential backoff.
        
        Returns:
            Tuple of (success: bool, cancel_requested: bool)
        """
        from app.api.crud_client.types import Unset
        
        timeout: Union[int, Unset] = settings.JOB_VISIBILITY_TIMEOUT_SECONDS
        body = HeartbeatRequest(lease_token=self.lease_token)
        
        backoff = self.INITIAL_BACKOFF_SECONDS
        
        for attempt in range(self.MAX_HEARTBEAT_RETRIES):
            try:
                response = heartbeat_func.sync(
                    queue_id=self.queue_id,
                    client=self.crud_client,
                    body=body,
                    visibility_timeout_seconds=timeout
                )
                
                # Check for cancellation request
                if isinstance(response, HeartbeatResponse) and response.cancel_requested:
                    return True, True
                
                # Success - reset backoff for next heartbeat interval
                if attempt > 0:
                    logger.info(
                        f"Heartbeat succeeded for queue {self.queue_id} on attempt {attempt + 1}"
                    )
                return True, False
                
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
                # Network timeout errors - retry with backoff
                if attempt < self.MAX_HEARTBEAT_RETRIES - 1:
                    logger.warning(
                        f"Heartbeat timeout for queue {self.queue_id} (attempt {attempt + 1}/"
                        f"{self.MAX_HEARTBEAT_RETRIES}): {e}. Retrying in {backoff}s..."
                    )
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Heartbeat timeout for queue {self.queue_id} after "
                        f"{self.MAX_HEARTBEAT_RETRIES} attempts: {e}",
                        exc_info=True
                    )
                    
            except Exception as e:
                # Other exceptions - retry with backoff
                if attempt < self.MAX_HEARTBEAT_RETRIES - 1:
                    logger.warning(
                        f"Heartbeat failed for queue {self.queue_id} (attempt {attempt + 1}/"
                        f"{self.MAX_HEARTBEAT_RETRIES}): {e}. Retrying in {backoff}s...",
                        exc_info=True
                    )
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Heartbeat failed for queue {self.queue_id} after "
                        f"{self.MAX_HEARTBEAT_RETRIES} attempts: {e}",
                        exc_info=True
                    )
        
        return False, False


def run_entire_job(job_metadata: dict):
    """
    Execute entire job lifecycle in a child process.
    
    This function runs in a separate process and handles:
    - Fetching crew_run data
    - Preparing execution data
    - Running heartbeat loop in background thread
    - Building and executing flow
    - Handling cancellation
    - Updating queue status
    
    Args:
        job_metadata: Dictionary containing:
            - crew_run_id: UUID
            - crew_id: UUID
            - queue_id: UUID
            - lease_token: str
    """
    crew_run_id = UUID(job_metadata['crew_run_id'])
    crew_id = UUID(job_metadata['crew_id'])
    queue_id = UUID(job_metadata['queue_id'])
    lease_token = job_metadata['lease_token']
    
    # Initialize synchronous HTTP client
    timeout = httpx.Timeout(30.0)
    crud_client = AuthenticatedClient(
        base_url=settings.CRUD_SERVICE_URL,
        token=settings.INTERNAL_CREW_API_KEY,
        timeout=timeout
    )
    
    # Cancellation event for heartbeat thread to signal cancellation
    cancellation_event = threading.Event()
    heartbeat_thread: Optional[HeartbeatThread] = None
    
    try:
        logger.info(f"Starting job execution for queue {queue_id}, crew_run {crew_run_id}")
        
        # Start heartbeat loop
        heartbeat_thread = HeartbeatThread(
            crud_client=crud_client,
            queue_id=queue_id,
            lease_token=lease_token,
            cancellation_event=cancellation_event
        )
        heartbeat_thread.start()
        
        # Fetch crew_run data
        crew_run_response = get_crew_run_func.sync(
            crew_run_id=crew_run_id,
            client=crud_client
        )
        
        if not crew_run_response or isinstance(crew_run_response, (Exception, HTTPValidationError)):
            raise ValueError(f"Failed to fetch crew_run {crew_run_id}")
        
        # Type narrowing: crew_run_response is now guaranteed to be CrewRunRead
        crew_run = crew_run_response
        
        # Prepare execution data
        stored_inputs = crew_run.run_metadata.inputs.to_dict()
        stored_inputs['crew_run_id'] = str(crew_run_id)
        
        tasks = [
            TaskInfo.model_validate(task.to_dict())
            for task in crew_run.run_metadata.tasks_snapshot
        ]
        
        # Check for cancellation before starting flow
        if cancellation_event.is_set():
            logger.info(f"Cancellation detected before flow execution for queue {queue_id}")
            body = UpdateStatusRequest(
                lease_token=lease_token,
                status=QueueStatus.CANCELLED
            )
            update_queue_status_func.sync(
                queue_id=queue_id,
                client=crud_client,
                body=body
            )
            return
        
        # Build and execute flow
        flow_service = get_flow_service()
        task_status_service = TaskStatusService()
        _, FlowClass, _ = flow_service.build_flow(tasks, task_status_service)
        flow = FlowClass()
        
        # Execute flow in a separate thread to allow cancellation monitoring
        # Note: CrewAI flow.kickoff() doesn't support cancellation signals directly,
        # so we run it in a thread and periodically check for cancellation
        flow_result: list[Any] = []  # Use list to store result (thread-safe mutable container)
        flow_exception: list[Optional[Exception]] = [None]  # Use list to store exception
        
        def run_flow():
            """Wrapper function to run flow.kickoff() and capture result/exception."""
            try:
                result = flow.kickoff(inputs=stored_inputs)
                flow_result.append(result)
            except Exception as e:
                flow_exception[0] = e
        
        # Start flow execution in a separate thread
        flow_thread = threading.Thread(target=run_flow, daemon=False)
        flow_thread.start()
        logger.info(f"Started flow execution thread for queue {queue_id}")
        
        # Monitor flow execution and check for cancellation periodically
        try:
            while flow_thread.is_alive():
                # Wait for thread with timeout to allow periodic cancellation checks
                flow_thread.join(timeout=1.0)
                
                # Check for cancellation request (only if thread is still running)
                if flow_thread.is_alive() and cancellation_event.is_set():
                    logger.info(f"Cancellation detected during flow execution for queue {queue_id}")
                    
                    # Update queue status to CANCELLED
                    try:
                        body = UpdateStatusRequest(
                            lease_token=lease_token,
                            status=QueueStatus.CANCELLED
                        )
                        update_queue_status_func.sync(
                            queue_id=queue_id,
                            client=crud_client,
                            body=body
                        )
                    except Exception as update_error:
                        logger.error(f"Failed to update queue {queue_id} status to CANCELLED: {update_error}")
                    
                    # Stop heartbeat thread before exiting
                    if heartbeat_thread:
                        heartbeat_thread.stop()
                    
                    # Close HTTP client before exiting
                    try:
                        sync_client = crud_client.get_httpx_client()
                        sync_client.close()
                    except Exception as e:
                        logger.warning(f"Error closing HTTP client: {e}")
                    
                    # Exit process immediately (terminates all threads including flow execution)
                    logger.info(f"Exiting process for queue {queue_id} due to cancellation")
                    os._exit(0)
            
            # Flow thread completed - check for exceptions
            if flow_exception[0]:
                raise flow_exception[0]
            
            # Flow completed successfully
            result = flow_result[0] if flow_result else None
            
            # Check for cancellation after flow execution (in case it was set right before completion)
            if cancellation_event.is_set():
                logger.info(f"Cancellation detected after flow execution for queue {queue_id}")
                body = UpdateStatusRequest(
                    lease_token=lease_token,
                    status=QueueStatus.CANCELLED
                )
                update_queue_status_func.sync(
                    queue_id=queue_id,
                    client=crud_client,
                    body=body
                )
                return
            
            # Flow completed successfully
            body = UpdateStatusRequest(
                lease_token=lease_token,
                status=QueueStatus.COMPLETED
            )
            update_queue_status_func.sync(
                queue_id=queue_id,
                client=crud_client,
                body=body
            )
            logger.info(f"Job {queue_id} completed successfully")
            
        except Exception as flow_error:
            logger.error(f"Flow execution failed for queue {queue_id}: {flow_error}", exc_info=True)
            
            # Check if cancellation was requested
            if cancellation_event.is_set():
                status = QueueStatus.CANCELLED
                logger.info(f"Updating queue {queue_id} status to CANCELLED due to cancellation")
            else:
                status = QueueStatus.FAILED
                logger.info(f"Updating queue {queue_id} status to FAILED due to error")
            
            body = UpdateStatusRequest(
                lease_token=lease_token,
                status=status
            )
            try:
                update_queue_status_func.sync(
                    queue_id=queue_id,
                    client=crud_client,
                    body=body
                )
            except Exception as update_error:
                logger.error(f"Failed to update queue {queue_id} status to {status}: {update_error}")
            raise
    
    except Exception as e:
        logger.error(f"Error executing job {queue_id}: {e}", exc_info=True)
        
        # Try to update status to FAILED if not already updated
        try:
            body = UpdateStatusRequest(
                lease_token=lease_token,
                status=QueueStatus.FAILED
            )
            update_queue_status_func.sync(
                queue_id=queue_id,
                client=crud_client,
                body=body
            )
        except Exception as update_error:
            logger.error(f"Failed to update queue {queue_id} status to FAILED: {update_error}")
    
    finally:
        # Stop heartbeat thread
        if heartbeat_thread:
            heartbeat_thread.stop()
        
        # Close HTTP client
        try:
            sync_client = crud_client.get_httpx_client()
            sync_client.close()
        except Exception as e:
            logger.warning(f"Error closing HTTP client: {e}")


class ResultBuilder:
    """Builds and serializes flow execution results for API submission."""
    
    @staticmethod
    def build_payload(
        result: Any, 
        flow: Any, 
        flow_state_model: type, 
        flow_state: Optional[dict] = None
    ) -> dict:
        """
        Build result payload combining execution result and flow state.
        
        Args:
            result: Flow execution result
            flow: Flow instance (for state extraction fallback)
            flow_state_model: Pydantic model class for flow state
            flow_state: Optional pre-extracted flow_state dict (preferred over extracting from flow)
            
        Returns:
            Dictionary containing result and/or flow_state
        """
        result_data = ResultBuilder._serialize_value(result)
        
        if flow_state is not None:
            state_dict = flow_state
        else:
            state_dict = ResultBuilder._extract_flow_state(flow, flow_state_model)
        
        if not state_dict:
            return result_data
        
        if result_data is None:
            return {"flow_state": state_dict}
        
        if isinstance(result_data, dict):
            result_data["flow_state"] = state_dict
            return result_data
        
        return {"result": result_data, "flow_state": state_dict}
    
    @staticmethod
    def _extract_flow_state(flow: Any, flow_state_model: type) -> Optional[dict]:
        """
        Extract flow state from flow instance using flow state model.
        
        Args:
            flow: Flow instance
            flow_state_model: Pydantic model class for flow state
            
        Returns:
            Dictionary of flow state fields, or None if no state available
        """
        if not flow_state_model or not hasattr(flow, 'state'):
            return None
        
        state_dict = {}
        for field_name in flow_state_model.model_fields.keys():
            value = getattr(flow.state, field_name, None)
            if value is None:
                continue
            serialized_value = ResultBuilder._serialize_value(value)
            if serialized_value is not None:
                state_dict[field_name] = serialized_value
        
        return state_dict or None
    
    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """
        Serialize a value to JSON-serializable format.
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized value (dict, list, primitive, or string representation)
        """
        if value is None:
            return None
        
        if isinstance(value, BaseModel):
            return value.model_dump(mode='json')
        
        if hasattr(value, '__dict__'):
            return str(value)
        
        if isinstance(value, (str, int, float, bool, dict, list)):
            return value
        
        return str(value)

