import asyncio
import logging
import multiprocessing
from typing import Any, Optional, Union
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.api.crud_client import AuthenticatedClient
from app.api.crud_client.api.internal import (
    heartbeat_internal_internal_queue_queue_id_heartbeat_post as heartbeat_func,
    update_crew_run_output_internal_internal_crew_run_crew_run_id_output_put as update_crew_run_output_func,
    update_queue_status_internal_internal_queue_queue_id_status_put as update_queue_status_func,
)
from app.api.crud_client.models import HeartbeatResponse
from app.api.crud_client.models.heartbeat_request import HeartbeatRequest
from app.api.crud_client.models.queue_status import QueueStatus
from app.api.crud_client.models.update_status_request import UpdateStatusRequest
from app.api.crud_client.models.update_crew_run_output_internal_internal_crew_run_crew_run_id_output_put_output import (
    UpdateCrewRunOutputInternalInternalCrewRunCrewRunIdOutputPutOutput as CrewRunOutputUpdate,
)
from app.dependencies import get_flow_service
from app.models.models import TaskInfo
from app.services.crew_service import CrewService
from app.services.flow.flow_utils import TaskStatusService
from config import settings

logger = logging.getLogger(__name__)

_mp_context = multiprocessing.get_context('spawn')


def run_flow_worker(tasks_dict: list[dict], inputs: dict, result_queue: multiprocessing.Queue):
    """
    Worker function that runs in a separate process to execute flow.kickoff().
    
    This function must be at module level for multiprocessing to work correctly.
    
    Args:
        tasks_dict: List of task dictionaries (serialized TaskInfo objects)
        inputs: Dictionary of input values for the flow
        result_queue: Queue to put the result or error, along with flow_state
    """
    flow = None
    FlowStateModel = None
    try:
        flow_service = get_flow_service()
        tasks = [TaskInfo.model_validate(task_dict) for task_dict in tasks_dict]
        
        task_status_service = TaskStatusService()
        FlowStateModel, FlowClass, _ = flow_service.build_flow(tasks, task_status_service)
        flow = FlowClass()
        result = flow.kickoff(inputs=inputs)
        
        # Extract flow_state from executed flow instance
        flow_state = ResultBuilder._extract_flow_state(flow, FlowStateModel)
        result_queue.put(("ok", result, flow_state))
    except Exception as e:
        logger.error(f"Error in flow worker process: {e}", exc_info=True)
        # Extract flow_state even on error to capture partial state
        flow_state = None
        if flow is not None and FlowStateModel is not None:
            try:
                flow_state = ResultBuilder._extract_flow_state(flow, FlowStateModel)
            except Exception as state_error:
                logger.warning(f"Failed to extract flow_state on error: {state_error}", exc_info=True)
        result_queue.put(("error", str(e), flow_state))


class FlowProcessManager:
    """Manages the lifecycle of flow execution processes."""
    
    def __init__(self, process_registry: dict[UUID, Any]):
        self.process_registry = process_registry
    
    async def run_flow(
        self,
        crew_run_id: UUID,
        tasks: list[TaskInfo],
        stored_inputs: dict
    ) -> tuple[Any, Optional[dict]]:
        """
        Execute flow in a separate process and return the result and flow_state.
        
        Args:
            crew_run_id: UUID of the crew run
            tasks: List of task definitions
            stored_inputs: Input dictionary for the flow
            
        Returns:
            Tuple of (flow execution result, flow_state dict or None)
            
        Raises:
            RuntimeError: If flow execution fails or process crashes
            asyncio.CancelledError: If execution is cancelled
        """
        tasks_dict = [task.model_dump() for task in tasks]
        result_queue = _mp_context.Queue()
        flow_process = _mp_context.Process(
            target=run_flow_worker,
            args=(tasks_dict, stored_inputs, result_queue)
        )
        self.process_registry[crew_run_id] = flow_process
        
        try:
            flow_process.start()
            logger.info(f"Started flow process {flow_process.pid} for crew_run {crew_run_id}")
            
            # Wait for result from worker process
            queue_result = await self._wait_for_result(flow_process, result_queue)
            
            status, result_or_error, flow_state = queue_result
            if status == "error":
                # Store flow_state before raising error so caller can access it
                error_with_state = RuntimeError(f"Flow execution failed: {result_or_error}")
                error_with_state.flow_state = flow_state  # type: ignore
                raise error_with_state
            
            # Gracefully terminate process
            self._terminate_process(flow_process, timeout=5.0)
            return result_or_error, flow_state
            
        except asyncio.CancelledError:
            logger.info(f"Flow execution cancelled for crew_run {crew_run_id}")
            self._terminate_process(flow_process, timeout=5.0, force=True)
            raise
        finally:
            self._cleanup(crew_run_id, result_queue)
    
    async def _wait_for_result(
        self,
        flow_process: Any,
        result_queue: multiprocessing.Queue
    ) -> tuple[str, Any, Optional[dict]]:
        """Wait for result from worker process, handling process crashes."""
        try:
            return await asyncio.to_thread(result_queue.get, timeout=None)
        except Exception as queue_error:
            if not flow_process.is_alive() and flow_process.exitcode != 0:
                raise RuntimeError(
                    f"Flow process {flow_process.pid} exited with code {flow_process.exitcode}"
                ) from queue_error
            raise
    
    def _terminate_process(self, process: Any, timeout: float = 5.0, force: bool = False):
        """Terminate a process gracefully, with fallback to kill if needed."""
        if not process or not process.is_alive():
            return
        
        if force:
            logger.info(f"Terminating flow process {process.pid}")
        else:
            logger.debug(f"Waiting for flow process {process.pid} to terminate")
        
        process.terminate()
        process.join(timeout=2.0)
        
        if process.is_alive():
            logger.warning(f"Process {process.pid} did not terminate, killing...")
            process.kill()
            process.join()
    
    def _cleanup(self, crew_run_id: UUID, result_queue: multiprocessing.Queue):
        """Clean up process registry and result queue."""
        self.process_registry.pop(crew_run_id, None)
        try:
            result_queue.close()
            result_queue.join_thread()
        except Exception as cleanup_error:
            logger.warning(f"Error cleaning up queue: {cleanup_error}")


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
        
        # Use provided flow_state if available, otherwise extract from flow instance
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


class HeartbeatManager:
    """Manages heartbeat loop for queue lease extension."""
    
    MAX_HEARTBEAT_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1.0
    
    def __init__(self, crud_client: AuthenticatedClient):
        self.crud_client = crud_client
    
    async def start_heartbeat_loop(
        self,
        queue_id: UUID,
        lease_token: str,
        execute_task: Optional[asyncio.Task] = None
    ) -> asyncio.Task:
        """
        Start heartbeat loop to extend queue lease.
        
        Args:
            queue_id: UUID of the queue
            lease_token: Token for the queue lease
            execute_task: Task to cancel if cancellation is requested
            
        Returns:
            asyncio.Task for the heartbeat loop
        """
        return asyncio.create_task(
            self._heartbeat_loop(queue_id, lease_token, execute_task)
        )
    
    async def _heartbeat_loop(
        self,
        queue_id: UUID,
        lease_token: str,
        execute_task: Optional[asyncio.Task] = None
    ):
        """Send periodic heartbeats to extend lease with retry logic."""
        try:
            while True:
                await asyncio.sleep(settings.HEARTBEAT_INTERVAL_SECONDS)
                
                # Attempt heartbeat with retry logic
                success = await self._send_heartbeat_with_retry(
                    queue_id, lease_token, execute_task
                )
                
                if not success:
                    logger.error(
                        f"Failed to send heartbeat for queue {queue_id} after "
                        f"{self.MAX_HEARTBEAT_RETRIES} retries. Continuing heartbeat loop."
                    )
        except asyncio.CancelledError:
            logger.info(f"Heartbeat loop for queue {queue_id} cancelled")
            raise
    
    async def _send_heartbeat_with_retry(
        self,
        queue_id: UUID,
        lease_token: str,
        execute_task: Optional[asyncio.Task] = None
    ) -> bool:
        """
        Send heartbeat request with retry logic and exponential backoff.
        
        Args:
            queue_id: UUID of the queue
            lease_token: Token for the queue lease
            execute_task: Task to cancel if cancellation is requested
            
        Returns:
            True if heartbeat succeeded, False if all retries failed
        """
        from app.api.crud_client.types import Unset
        
        timeout: Union[int, Unset] = settings.JOB_VISIBILITY_TIMEOUT_SECONDS
        body = HeartbeatRequest(lease_token=lease_token)
        
        backoff = self.INITIAL_BACKOFF_SECONDS
        
        for attempt in range(self.MAX_HEARTBEAT_RETRIES):
            try:
                response = await heartbeat_func.asyncio(
                    queue_id=queue_id,
                    client=self.crud_client,
                    body=body,
                    visibility_timeout_seconds=timeout
                )
                
                # Check for cancellation request
                if isinstance(response, HeartbeatResponse) and response.cancel_requested:
                    logger.info(f"Cancellation requested for queue {queue_id}")
                    if execute_task and not execute_task.done():
                        logger.info(f"Cancelling execute task for queue {queue_id}")
                        execute_task.cancel()
                    raise asyncio.CancelledError()
                
                # Success - reset backoff for next heartbeat interval
                if attempt > 0:
                    logger.info(
                        f"Heartbeat succeeded for queue {queue_id} on attempt {attempt + 1}"
                    )
                return True
                
            except asyncio.CancelledError:
                # Re-raise cancellation immediately
                raise
                
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
                # Network timeout errors - retry with backoff
                if attempt < self.MAX_HEARTBEAT_RETRIES - 1:
                    logger.warning(
                        f"Heartbeat timeout for queue {queue_id} (attempt {attempt + 1}/"
                        f"{self.MAX_HEARTBEAT_RETRIES}): {e}. Retrying in {backoff}s..."
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Heartbeat timeout for queue {queue_id} after "
                        f"{self.MAX_HEARTBEAT_RETRIES} attempts: {e}",
                        exc_info=True
                    )
                    
            except Exception as e:
                # Other exceptions - retry with backoff
                if attempt < self.MAX_HEARTBEAT_RETRIES - 1:
                    logger.warning(
                        f"Heartbeat failed for queue {queue_id} (attempt {attempt + 1}/"
                        f"{self.MAX_HEARTBEAT_RETRIES}): {e}. Retrying in {backoff}s...",
                        exc_info=True
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Heartbeat failed for queue {queue_id} after "
                        f"{self.MAX_HEARTBEAT_RETRIES} attempts: {e}",
                        exc_info=True
                    )
        
        return False


class JobExecutor:
    """Executes crew runs by building flows and running them."""
    
    def __init__(self, crew_service: CrewService, process_registry: Optional[dict[UUID, Any]] = None):
        timeout = httpx.Timeout(30.0)
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token=settings.INTERNAL_CREW_API_KEY,
            timeout=timeout
        )
        self.flow_service = get_flow_service()
        self.crew_service = crew_service
        self.process_registry = process_registry or {}
        
        # Initialize helper components
        self.process_manager = FlowProcessManager(self.process_registry)
        self.heartbeat_manager = HeartbeatManager(self.crud_client)
    
    async def execute(
        self,
        crew_run_id: UUID,
        crew_id: UUID,
        queue_id: UUID,
        lease_token: str
    ):
        """
        Execute a crew run:
        1. Fetch crew_run to get stored inputs and tasks snapshot
        2. Run flow with inputs in separate process
        3. Build result payload and send to CrudService
        4. Handle heartbeat and cancellation
        
        Args:
            crew_run_id: UUID of the crew run to execute
            crew_id: UUID of the crew
            queue_id: UUID of the queue job
            lease_token: Token for the queue lease
        """
        heartbeat_task = None
        execute_task = asyncio.current_task()
        flow_state = None
        tasks = None
        
        try:
            # Start heartbeat loop
            heartbeat_task = await self.heartbeat_manager.start_heartbeat_loop(
                queue_id, lease_token, execute_task
            )
            
            # Prepare execution data
            tasks, stored_inputs = await self._prepare_execution_data(crew_run_id)
            
            # Execute flow in separate process
            result, flow_state = await self.process_manager.run_flow(crew_run_id, tasks, stored_inputs)
            
            # Build and submit result with flow_state
            await self._submit_result(crew_run_id, tasks, result, flow_state=flow_state)
            
        except asyncio.CancelledError:
            logger.info(f"Crew run {crew_run_id} execution cancelled")
            await self._handle_cancellation(queue_id, lease_token)
            raise
        except RuntimeError as e:
            # RuntimeError from run_flow may contain flow_state attribute
            flow_state = getattr(e, 'flow_state', None)
            logger.error(f"Error executing crew run {crew_run_id}: {e}", exc_info=True)
            # Try to save flow_state even on error if we have it
            if flow_state is not None and tasks is not None:
                try:
                    await self._submit_result(crew_run_id, tasks, None, flow_state=flow_state)
                except Exception as submit_error:
                    logger.warning(f"Failed to submit flow_state on error: {submit_error}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error executing crew run {crew_run_id}: {e}", exc_info=True)
            # Try to save flow_state even on error if we have it
            if flow_state is not None and tasks is not None:
                try:
                    await self._submit_result(crew_run_id, tasks, None, flow_state=flow_state)
                except Exception as submit_error:
                    logger.warning(f"Failed to submit flow_state on error: {submit_error}", exc_info=True)
            raise
        finally:
            await self._cleanup_heartbeat(heartbeat_task)
    
    async def _prepare_execution_data(
        self,
        crew_run_id: UUID
    ) -> tuple[list[TaskInfo], dict]:
        """
        Fetch crew run and prepare tasks and inputs for execution.
        
        Args:
            crew_run_id: UUID of the crew run
            
        Returns:
            Tuple of (tasks list, inputs dictionary)
        """
        crew_run = await self.crew_service.get_crew_run(crew_run_id)
        stored_inputs = crew_run.run_metadata.inputs.to_dict()
        stored_inputs['crew_run_id'] = str(crew_run_id)
        
        tasks = [
            TaskInfo.model_validate(task.to_dict())
            for task in crew_run.run_metadata.tasks_snapshot
        ]
        
        return tasks, stored_inputs
    
    async def _submit_result(
        self,
        crew_run_id: UUID,
        tasks: list[TaskInfo],
        result: Any,
        flow_state: Optional[dict] = None
    ):
        """
        Build result payload and submit to CRUD service.
        
        Args:
            crew_run_id: UUID of the crew run
            tasks: List of task definitions
            result: Flow execution result
            flow_state: Optional flow_state dict from executed flow
        """
        task_status_service = TaskStatusService()
        FlowStateModel, FlowClass, _ = self.flow_service.build_flow(tasks, task_status_service)
        flow = FlowClass()
        
        # Build result payload using provided flow_state
        result_data = ResultBuilder.build_payload(result, flow, FlowStateModel, flow_state=flow_state)
        
        output_body = CrewRunOutputUpdate()
        if isinstance(result_data, dict):
            output_body.additional_properties = result_data
        else:
            # If result_data is not a dict (e.g., a primitive), wrap it in result key
            output_body.additional_properties = {"result": result_data}
        
        await update_crew_run_output_func.asyncio(
            crew_run_id=crew_run_id,
            client=self.crud_client,
            body=output_body,
        )
    
    async def _handle_cancellation(self, queue_id: UUID, lease_token: str):
        """Handle cancellation by updating queue status."""
        try:
            body = UpdateStatusRequest(
                lease_token=lease_token,
                status=QueueStatus.CANCELLED
            )
            await update_queue_status_func.asyncio(
                queue_id=queue_id,
                client=self.crud_client,
                body=body
            )
            logger.info(f"Updated queue {queue_id} status to CANCELLED")
        except Exception as update_error:
            logger.error(f"Failed to update queue {queue_id} status to CANCELLED: {update_error}")
    
    async def _cleanup_heartbeat(self, heartbeat_task: Optional[asyncio.Task]):
        """Cancel and await heartbeat task cleanup."""
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
