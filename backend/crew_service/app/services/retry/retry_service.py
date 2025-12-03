from uuid import UUID

from fastapi import HTTPException

from config import logging

from app.api.crud_client import AuthenticatedClient, errors
from app.api.crud_client.api.internal import (
    cancel_crew_run_internal_internal_crew_run_crew_run_id_cancel_post as cancel_crew_run_func,
    copy_artifacts_internal_internal_crew_run_original_crew_run_id_copy_artifacts_new_crew_run_id_post as copy_artifacts_func,
    create_crew_run_internal_internal_crew_run_create_post as create_crew_run_func,
    get_crew_run_by_id_internal_crew_run_crew_run_id_get as get_crew_run_func,
)
from app.api.crud_client.models import (
    BodyCreateCrewRunInternalInternalCrewRunCreatePost as CrewRunCreateBody,
    CrewRunRead,
    HTTPValidationError,
    CrewRunCreate,
    CrewRunMetadataCreate,
    CrewRunMetadataCreateInputs,
    CrewRunOutputCreate,
    CrewRunOutputCreateTaskStates,
    QueueStatus,
    TaskStateSnapshot,
    TaskStateSnapshotState,
    TaskStatus,
)

from app.models.models import CrewRunRetryRequest
from app.services.retry.retry_state_builder import RetryStateBuilder
from app.services.retry.retry_task_analyzer import RetryTaskAnalyzer
from app.services.retry.retry_validator import RetryValidator

logger = logging.getLogger(__name__)


class RetryService:
    """Orchestrates crew run retry operations."""

    def __init__(self, crud_client: AuthenticatedClient):
        """
        Initialize RetryService.
        
        Args:
            crud_client: Authenticated CRUD client for API calls
        """
        self.crud_client = crud_client
        self.validator = RetryValidator()
        self.task_analyzer = RetryTaskAnalyzer()

    async def get_crew_run(self, crew_run_id: UUID):
        """
        Fetch a crew run by ID from the CRUD service.
        
        Args:
            crew_run_id: UUID of the crew run to fetch
            
        Returns:
            Crew run response object
            
        Raises:
            ValueError: If crew run is not found or has validation errors
        """
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

    async def retry_crew_run(
        self,
        retry_request: CrewRunRetryRequest,
        crew_run_id: UUID,
        user_token: str
    ):
        """
        Retry a crew run from a specific task.
        
        Args:
            retry_request: Retry request containing task key and feedback
            crew_run_id: UUID of the crew run to retry
            user_token: User authentication token
            
        Returns:
            The newly created retry crew run
            
        Raises:
            HTTPException: If validation fails
            ValueError: If retry creation fails
        """
        crew_run = await self.get_crew_run(crew_run_id)
        if crew_run is None:
            raise ValueError(f"Crew run {crew_run_id} not found")
        
        retry_from_task_key = retry_request.retry_from_task_key
        
        # * 1. Validate retry request
        try:
            self.validator.validate_retry_request(crew_run, retry_from_task_key)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            ) from e

        # * 2. Find Upstream and Downstream (inclusive of retry_from_task) tasks using tasks_snaphsot
        task_states = crew_run.output.task_states
        sorted_task_states = sorted(
            task_states.additional_properties.items(),
            key=lambda item: item[1].order
        )
        
        tasks_snapshot = crew_run.run_metadata.tasks_snapshot
        tasks_snapshot_dict = {task.key: task for task in tasks_snapshot}
        
        upstream_tasks = self.task_analyzer.find_upstream_tasks(sorted_task_states, tasks_snapshot_dict, retry_from_task_key)
        retry_and_downstream_tasks = self.task_analyzer.find_retry_and_downstream_tasks(sorted_task_states, tasks_snapshot_dict, retry_from_task_key)

        # * 3. Create CrewRunCreate body
        # - Reset retry and downstream tasks
        # - Create run_metadata for new crew_run
        new_task_states = CrewRunOutputCreateTaskStates()
        for task_key, task_state, _ in upstream_tasks:
            new_task_states[task_key] = TaskStateSnapshot(
                state=task_state.state,
                status=TaskStatus.COMPLETED,
                order=task_state.order,
            )
        
        for task_key, task_state, _ in retry_and_downstream_tasks:
            new_task_states[task_key] = TaskStateSnapshot(
                state=TaskStateSnapshotState(),
                status=TaskStatus.QUEUED,
                completed_at=None,
                order=task_state.order,
            )
            
        new_crew_run_output = CrewRunOutputCreate(task_states=new_task_states)
        
        inputs_dict = crew_run.run_metadata.inputs.to_dict()
        create_inputs = CrewRunMetadataCreateInputs()
        create_inputs.additional_properties = inputs_dict
        
        new_run_metadata = CrewRunMetadataCreate(
            inputs=create_inputs,
            tasks_snapshot=tasks_snapshot
        )
        
        # * 4. Create new Crew Run
        new_crew_run = await self._create_retry_crew_run(
            crew_run_create_body=CrewRunCreate(
                crew_id=crew_run.crew_id,
                run_metadata=new_run_metadata,
                output=new_crew_run_output,
            ),
            user_token=user_token
        )
        
        # * 5. Copy Artifacts to new Crew Run
        await self._copy_artifacts(crew_run_id, new_crew_run.id)
        
        # * 6. Cancel Original Crew Run
        await self._cancel_original_crew_run(crew_run, crew_run_id, user_token)
        
        return new_crew_run

    async def _create_retry_crew_run(
        self,
        crew_run_create_body: CrewRunCreate,
        user_token: str
    ) -> CrewRunRead:
        """
        Create a new crew run for retry.
        
        Args:
            crew_run_create_body: CrewRunCreate body
            user_token: User authentication token
        """

        try:
            response = await create_crew_run_func.asyncio_detailed(
                body=CrewRunCreateBody(crew_run_data=crew_run_create_body, user_token=user_token),
                client=self.crud_client,
            )
            
            if response.status_code != 201:
                error_msg = f"Failed to create retry crew run: status {response.status_code}"
                try:
                    error_content = response.content.decode() if response.content else "No error details"
                    error_msg += f" - {error_content}"
                except:
                    pass
                raise ValueError(error_msg)
            
            if isinstance(response.parsed, HTTPValidationError):
                raise ValueError(f"Validation error creating retry crew run: {response.parsed}")
            
            if response.parsed is None:
                raise ValueError("Failed to create retry crew run: received None response")
            
            return response.parsed
        except Exception as e:
            logger.error(f"Failed to create retry crew run: {e}", exc_info=True)
            raise e


    async def _copy_artifacts(self, original_crew_run_id: UUID, new_crew_run_id: UUID) -> None:
        """
        Copy artifacts from the original crew run to the retry crew run.
        
        Args:
            original_crew_run_id: UUID of the original crew run
            new_crew_run_id: UUID of the new retry crew run
            
        Raises:
            ValueError: If artifact copying fails
        """
        try:
            copy_response = await copy_artifacts_func.asyncio_detailed(
                original_crew_run_id=original_crew_run_id,
                new_crew_run_id=new_crew_run_id,
                client=self.crud_client
            )
            if copy_response.status_code != 200:
                raise ValueError(
                    f"Failed to copy artifacts from crew run {original_crew_run_id} to retry {new_crew_run_id}: "
                    f"{copy_response.content}"
                )
        except Exception as e:
            logger.error(f"Failed to copy artifacts from crew run {original_crew_run_id} to retry {new_crew_run_id}: {e}", exc_info=True)
            raise e

    async def _cancel_original_crew_run(
        self,
        crew_run: CrewRunRead,
        crew_run_id: UUID,
        user_token: str
    ) -> None:
        """
        Cancel the original crew run after successfully creating the retry.
        
        This is best-effort - failures should not prevent retry from succeeding.
        
        Args:
            crew_run: Original crew run object
            crew_run_id: UUID of the original crew run
            user_token: User authentication token
        """
        queue_status = crew_run.queue_status
        if queue_status and queue_status in [QueueStatus.CANCELLED, QueueStatus.COMPLETED]:
            return
        
        try:
            await cancel_crew_run_func.asyncio(
                crew_run_id=crew_run_id,
                body=user_token,
                client=self.crud_client,
            )
            return
        except Exception as e:
            logger.error(
                f"Failed to cancel original crew run {crew_run_id}: {e}"
            )
            raise e

