import asyncio
import logging
import multiprocessing
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.api.crud_client import AuthenticatedClient, errors
from app.api.crud_client.api.internal import (
    get_crew_by_id_internal_crew_crew_id_get as get_crew_by_id_func,
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
from config import settings

logger = logging.getLogger(__name__)

# Use 'spawn' context for cross-platform compatibility (especially macOS/Windows)
_mp_context = multiprocessing.get_context('spawn')


def run_flow_worker(tasks_dict: list[dict], inputs: dict, result_queue: multiprocessing.Queue):
    """
    Worker function that runs in a separate process to execute flow.kickoff().
    
    This function must be at module level for multiprocessing to work correctly.
    
    Args:
        tasks_dict: List of task dictionaries (serialized TaskInfo objects)
        inputs: Dictionary of input values for the flow
        result_queue: Queue to put the result or error
    """
    try:
        # Import here to avoid issues with multiprocessing
        from app.dependencies import get_flow_service
        from app.models.models import TaskInfo
        
        flow_service = get_flow_service()
        tasks = [TaskInfo.model_validate(task_dict) for task_dict in tasks_dict]
        
        FlowStateModel, FlowClass, _ = flow_service.build_flow(tasks)
        flow = FlowClass()
        result = flow.kickoff(inputs=inputs)
        result_queue.put(("ok", result))
    except Exception as e:
        logger.error(f"Error in flow worker process: {e}", exc_info=True)
        result_queue.put(("error", str(e)))


class JobExecutor:
    """Executes crew runs by building flows and running them."""
    
    def __init__(self, crew_service: CrewService, process_registry: dict[UUID, Any] | None = None):
        timeout = httpx.Timeout(30.0)
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token=settings.INTERNAL_CREW_API_KEY,
            timeout=timeout
        )
        self.flow_service = get_flow_service()
        self.crew_service = crew_service
        self.process_registry = process_registry or {}
    
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
        2. Build flow from tasks snapshot
        3. Run flow with inputs
        4. Send output to CrudService
        5. Handle heartbeat
        """
        heartbeat_task = None
        execute_task = asyncio.current_task()
        try:
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(queue_id, lease_token, execute_task)
            )
            
            crew_run = await self.crew_service.get_crew_run(crew_run_id)
            
            stored_inputs = crew_run.run_metadata.inputs.to_dict()           
            stored_inputs['crew_run_id'] = str(crew_run_id)

            tasks = [TaskInfo.model_validate(task.to_dict()) for task in crew_run.run_metadata.tasks_snapshot]
            
            # Build Flow from tasks snapshot
            FlowStateModel, FlowClass, _ = self.flow_service.build_flow(tasks)
            
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
                
                try:
                    # Use asyncio.to_thread to await queue.get() without blocking the event loop
                    # Worker function has try/except to ensure it always puts something in queue
                    try:
                        queue_result = await asyncio.to_thread(result_queue.get, timeout=None)
                    except Exception as queue_error:
                        # Check if process crashed unexpectedly
                        if not flow_process.is_alive() and flow_process.exitcode != 0:
                            raise RuntimeError(
                                f"Flow process {flow_process.pid} exited with code {flow_process.exitcode}"
                            ) from queue_error
                        raise
                    
                    status, result_or_error = queue_result
                    
                    if status == "error":
                        raise RuntimeError(f"Flow execution failed: {result_or_error}")
                    
                    result = result_or_error
                    
                    flow_process.join(timeout=5.0)
                    if flow_process.is_alive():
                        logger.warning(f"Flow process {flow_process.pid} did not terminate within timeout")
                        flow_process.terminate()
                        flow_process.join(timeout=2.0)
                        if flow_process.is_alive():
                            logger.warning(f"Force killing flow process {flow_process.pid}")
                            flow_process.kill()
                            flow_process.join()
                    
                except asyncio.CancelledError:
                    logger.info(f"Flow execution cancelled for crew_run {crew_run_id}, terminating process...")
                    if flow_process.is_alive():
                        logger.info(f"Terminating flow process {flow_process.pid}")
                        flow_process.terminate()
                        try:
                            flow_process.join(timeout=5.0)
                            if flow_process.is_alive():
                                logger.warning(f"Process {flow_process.pid} did not terminate, killing...")
                                flow_process.kill()
                                flow_process.join()
                        except Exception as term_error:
                            logger.error(f"Error terminating process: {term_error}")
                    raise
                finally:
                    self.process_registry.pop(crew_run_id, None)
                    try:
                        result_queue.close()
                        result_queue.join_thread()
                    except Exception as cleanup_error:
                        logger.warning(f"Error cleaning up queue: {cleanup_error}")

            except Exception as e:
                if flow_process.is_alive():
                    try:
                        flow_process.terminate()
                        flow_process.join(timeout=2.0)
                        if flow_process.is_alive():
                            flow_process.kill()
                            flow_process.join()
                    except Exception:
                        pass
                self.process_registry.pop(crew_run_id, None)
                raise

            # Rebuild flow for state extraction (can't access flow instance from process)
            flow = FlowClass()
            result_data = self._build_result_payload(result, flow, FlowStateModel)
            
            output_body = CrewRunOutputUpdate()
            output_body.additional_properties = {"result": result_data}
            
            await update_crew_run_output_func.asyncio(
                crew_run_id=crew_run_id,
                client=self.crud_client,
                body=output_body,
            )
        except asyncio.CancelledError:
            logger.info(f"Crew run {crew_run_id} execution cancelled")
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
            raise
        except Exception as e:
            logger.error(f"Error executing crew run {crew_run_id}: {e}", exc_info=True)
            raise
        finally:
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
    
    async def _heartbeat_loop(
        self,
        queue_id: UUID,
        lease_token: str,
        execute_task: asyncio.Task | None = None
    ):
        """Send periodic heartbeats to extend lease."""
        try:
            while True:
                await asyncio.sleep(settings.HEARTBEAT_INTERVAL_SECONDS)
                try:
                    from app.api.crud_client.types import Unset
                    
                    timeout: int | Unset = settings.JOB_VISIBILITY_TIMEOUT_SECONDS
                    body = HeartbeatRequest(lease_token=lease_token)
                    response = await heartbeat_func.asyncio(
                        queue_id=queue_id,
                        client=self.crud_client,
                        body=body,
                        visibility_timeout_seconds=timeout
                    )
                    if isinstance(response, HeartbeatResponse) and response.cancel_requested:
                        logger.info(f"Cancellation requested for queue {queue_id}")
                        if execute_task and not execute_task.done():
                            logger.info(f"Cancelling execute task for queue {queue_id}")
                            execute_task.cancel()
                        raise asyncio.CancelledError()
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}", exc_info=True)
        except asyncio.CancelledError:
            logger.info(f"Heartbeat loop for queue {queue_id} cancelled")
            raise

    def _build_result_payload(self, result, flow, flow_state_model):
        result_data = self._serialize_value(result)
        state_dict = self._extract_flow_state(flow, flow_state_model)
        
        if not state_dict:
            return result_data
        
        if result_data is None:
            return {"flow_state": state_dict}
        
        if isinstance(result_data, dict):
            result_data["flow_state"] = state_dict
            return result_data
        
        return {"result": result_data, "flow_state": state_dict}
    
    def _extract_flow_state(self, flow, flow_state_model):
        if not flow_state_model or not hasattr(flow, 'state'):
            return None
        
        state_dict = {}
        for field_name in flow_state_model.model_fields.keys():
            value = getattr(flow.state, field_name, None)
            if value is None:
                continue
            serialized_value = self._serialize_value(value)
            if serialized_value is not None:
                state_dict[field_name] = serialized_value
        
        return state_dict or None
    
    @staticmethod
    def _serialize_value(value):
        if value is None:
            return None
        
        if isinstance(value, BaseModel):
            return value.model_dump(mode='json')
        
        if hasattr(value, '__dict__'):
            return str(value)
        
        if isinstance(value, (str, int, float, bool, dict, list)):
            return value
        
        return str(value)