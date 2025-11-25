import asyncio
import logging
from uuid import UUID

import httpx

from app.api.crud_client import AuthenticatedClient, errors
from app.api.crud_client.api.internal import (
    get_crew_by_id_internal_crew_crew_id_get as get_crew_by_id_func,
    heartbeat_internal_internal_queue_queue_id_heartbeat_post as heartbeat_func,
    update_crew_run_output_internal_internal_crew_run_crew_run_id_output_put as update_crew_run_output_func,
)
from app.api.crud_client.models.heartbeat_request import HeartbeatRequest
from app.api.crud_client.models.http_validation_error import HTTPValidationError
from app.api.crud_client.models.update_crew_run_output_internal_internal_crew_run_crew_run_id_output_put_output import (
    UpdateCrewRunOutputInternalInternalCrewRunCrewRunIdOutputPutOutput as CrewRunOutputUpdate,
)
from app.services.crewai_service import CrewAIService
from config import settings

logger = logging.getLogger(__name__)


class JobExecutor:
    """Executes crew runs by rebuilding crews and running them."""
    
    def __init__(self):
        timeout = httpx.Timeout(30.0)
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token=settings.INTERNAL_CREW_API_KEY,
            timeout=timeout
        )
        self.crewai_service = CrewAIService()
    
    async def execute(
        self,
        crew_run_id: UUID,
        crew_id: UUID,
        queue_id: UUID,
        lease_token: str
    ):
        """
        Execute a crew run:
        1. Fetch crew configuration
        2. Load agents and tasks from YAML
        3. Build crew
        4. Run crew asynchronously
        5. Send output to CrudService
        6. Handle heartbeat
        """
        heartbeat_task = None
        try:
            heartbeat_task = asyncio.create_task(
                self._heartbeat_loop(queue_id, lease_token)
            )
                        
            try:
                crew_result = await get_crew_by_id_func.asyncio(
                    crew_id=crew_id,
                    client=self.crud_client,
                )
                if not crew_result:
                    raise ValueError(f"Crew {crew_id} not found")
                
                if isinstance(crew_result, HTTPValidationError):
                    raise ValueError(f"Validation error retrieving crew {crew_id}: {crew_result}")
            except errors.UnexpectedStatus as e:
                if e.status_code == 404:
                    raise ValueError(f"Crew {crew_id} not found") from e
                raise
            
            tasks = crew_result.tasks
            if len(tasks) == 0:
                raise ValueError(f"Crew {crew_id} has no tasks")
            crew = self.crewai_service.build_crew(tasks)
            
            logger.info(f"Running crew for crew_run {crew_run_id}")
            result = await crew.kickoff_async()
            
            # TODO: Instead of only final output, we should store step-by-step agent/task outputs in addition to final output
            # Convert result to serializable format
            result_data = None
            if result:
                if hasattr(result, '__dict__'):
                    result_data = str(result)
                elif isinstance(result, (str, int, float, bool, dict, list)):
                    result_data = result
                else:
                    result_data = str(result)
            
            # Update crew run output
            output_body = CrewRunOutputUpdate()
            output_body.additional_properties = {"result": result_data}
            
            await update_crew_run_output_func.asyncio(
                crew_run_id=crew_run_id,
                client=self.crud_client,
                body=output_body,
            )
            
            logger.info(f"Crew run {crew_run_id} completed successfully")
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
                    logger.debug(f"Heartbeat sent for queue_id {queue_id}")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat: {e}", exc_info=True)
        except asyncio.CancelledError:
            logger.debug(f"Heartbeat loop cancelled for queue_id {queue_id}")
            raise

