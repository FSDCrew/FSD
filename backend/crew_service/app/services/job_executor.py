import asyncio
import logging
from uuid import UUID

import httpx
from pydantic import BaseModel

from app.api.crud_client import AuthenticatedClient, errors
from app.api.crud_client.api.internal import (
    get_crew_by_id_internal_crew_crew_id_get as get_crew_by_id_func,
    get_crew_run_by_id_internal_crew_run_crew_run_id_get as get_crew_run_func,
    heartbeat_internal_internal_queue_queue_id_heartbeat_post as heartbeat_func,
    update_crew_run_output_internal_internal_crew_run_crew_run_id_output_put as update_crew_run_output_func,
)
from app.api.crud_client.models.heartbeat_request import HeartbeatRequest
from app.api.crud_client.models.http_validation_error import HTTPValidationError
from app.api.crud_client.models.update_crew_run_output_internal_internal_crew_run_crew_run_id_output_put_output import (
    UpdateCrewRunOutputInternalInternalCrewRunCrewRunIdOutputPutOutput as CrewRunOutputUpdate,
)
from app.dependencies import get_flow_service
from app.models.models import TaskInfo
from config import settings

logger = logging.getLogger(__name__)


class JobExecutor:
    """Executes crew runs by building flows and running them."""
    
    def __init__(self):
        timeout = httpx.Timeout(30.0)
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token=settings.INTERNAL_CREW_API_KEY,
            timeout=timeout
        )
        self.flow_service = get_flow_service()
    
    async def execute(
        self,
        crew_run_id: UUID,
        crew_id: UUID,
        queue_id: UUID,
        lease_token: str
    ):
        """
        Execute a crew run:
        1. Fetch crew_run to get stored inputs
        2. Fetch crew configuration
        3. Load agents and tasks from YAML
        4. Build Flow
        5. Run flow with inputs
        6. Send output to CrudService
        7. Handle heartbeat
        """
        heartbeat_task = None
        try:
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(queue_id, lease_token)
            )
            
            crew_run = await self._get_crew_run(crew_run_id)
            
            stored_inputs = crew_run.run_metadata.inputs.to_dict()           
            stored_inputs['crew_run_id'] = str(crew_run_id)

            tasks = [TaskInfo.model_validate(task.to_dict()) for task in crew_run.run_metadata.tasks_snapshot]
            
            # Build Flow from tasks
            FlowStateModel, FlowClass, _ = self.flow_service.build_flow(tasks)
            flow = FlowClass()
            
            # Create a task from the thread execution so we can track and wait for it
            flow_task = asyncio.create_task(asyncio.to_thread(flow.kickoff, inputs=stored_inputs))
            try:
                result = await asyncio.shield(flow_task)
            except asyncio.CancelledError:
                logger.info("Flow execution cancelled, waiting for thread to finish...")
                try:
                    if not flow_task.done():
                        await asyncio.wait_for(flow_task, timeout=5.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.warning("Thread did not finish within timeout, proceeding with shutdown")
                raise

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
        lease_token: str
    ):
        """Send periodic heartbeats to extend lease."""
        try:
            while True:
                await asyncio.sleep(settings.HEARTBEAT_INTERVAL_SECONDS)
                try:
                    from app.api.crud_client.types import Unset
                    
                    timeout: int | Unset = settings.JOB_VISIBILITY_TIMEOUT_SECONDS
                    body = HeartbeatRequest(lease_token=lease_token)
                    await heartbeat_func.asyncio(
                        queue_id=queue_id,
                        client=self.crud_client,
                        body=body,
                        visibility_timeout_seconds=timeout
                    )
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}", exc_info=True)
        except asyncio.CancelledError:
            raise

    async def _get_crew_run(self, crew_run_id: UUID):
        try:
            response = await get_crew_run_func.asyncio(
                crew_run_id=crew_run_id,
                client=self.crud_client,
            )
            if not response:
                raise ValueError(f"Crew run {crew_run_id} not found")
            
            if isinstance(response, HTTPValidationError):
                raise ValueError(f"Validation error retrieving crew run {crew_run_id}: {response}")
            
            return response
        except errors.UnexpectedStatus as e:
            if e.status_code == 404:
                raise ValueError(f"Crew run {crew_run_id} not found") from e
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