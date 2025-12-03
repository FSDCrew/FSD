from typing import List, Set
from uuid import UUID
import copy
import datetime
from config import logging

import httpx
from fastapi import HTTPException

from app.api.crud_client import AuthenticatedClient, errors
from app.api.crud_client.api.internal import (
    cancel_crew_run_internal_internal_crew_run_crew_run_id_cancel_post as cancel_crew_run_func,
    create_crew_run_internal_internal_crew_run_create_post as create_crew_run_func,
    get_crew_by_id_internal_crew_crew_id_get as get_crew_by_id_func,
    get_crew_run_by_id_internal_crew_run_crew_run_id_get as get_crew_run_func,
)
from app.api.crud_client.models import (
    BodyCreateCrewRunInternalInternalCrewRunCreatePost as CrewRunCreateBody,
    CrewRunCreate,
    CrewRunMetadataCreate,
    CrewRunMetadataCreateInputs,
    CrewRunOutputCreate,
    CrewRunOutputCreateTaskStates,
    RetryFeedback,
    HTTPValidationError,
    QueueStatus,
    TaskInfo as CrudTaskInfo,
    TaskRead as CrudTaskRead,
    TaskStateSnapshot,
    TaskStateSnapshotState,
    TaskStatus,
)
from app.api.crud_client.types import UNSET

from app.models.models import CrewRun, CrewRunCreateRequest, CrewRunRetryRequest, TaskInfo, FlowDependencyGraph
from app.services.flow.dependency_graph import build_flow_dependency_graph
from app.services.flow.flow_service import FlowService
from config import settings, tasks_config

logger = logging.getLogger(__name__)


class CrewService:
    """Application service for crew operations."""

    def __init__(
        self,
        flow_service: FlowService,
    ) -> None:
        self.crud_client = AuthenticatedClient(
            base_url=settings.CRUD_SERVICE_URL,
            token=settings.INTERNAL_CREW_API_KEY,
            timeout=httpx.Timeout(30.0),
        )
        self.flow_service = flow_service

    async def _get_crew_tasks(self, crew_id: UUID) -> List["CrudTaskRead"]:
        """
        Fetch crew by ID and return its tasks.
        
        Args:
            crew_id: UUID of the crew to fetch
            
        Returns:
            List of TaskRead objects from the crew
            
        Raises:
            ValueError: If crew is not found, has validation errors, or has no tasks
        """
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
        
        return tasks

    def _load_full_task_definitions(self, tasks: List[CrudTaskRead]) -> List[TaskInfo]:
        """Get full task definitions from tasks_config """
        full_tasks = []
        for task in tasks:
            task_config = tasks_config.get(task.key)
            
            if not task_config:
                raise ValueError(f"Task {task.key} not found in tasks_config")
            
            full_task = TaskInfo.model_validate(task_config)
            full_tasks.append(full_task)
        return full_tasks

    async def get_required_inputs(self, crew_id: UUID, user_token: str):
        """Get required inputs for a crew based on its tasks and flow dependencies."""
        tasks = await self._get_crew_tasks(crew_id)
        tasks_full = self._load_full_task_definitions(tasks)
        return self.flow_service.get_required_inputs(tasks_full)

    async def kickoff_crew_run(self, crew_run_data: CrewRunCreateRequest, user_token: str):
        """Queue a crew run in CRUD service."""
        # Validate input types before creating crew run
        # * 1. Create task_snapshots
        tasks = await self._get_crew_tasks(crew_run_data.crew_id)
        tasks_full = self._load_full_task_definitions(tasks)
        
        # * 2. Validate input types
        if crew_run_data.inputs:
            try:
                self.flow_service.validate_inputs(
                    inputs=crew_run_data.inputs,
                    tasks=tasks_full,
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                ) from e
        
        task_snapshots = [CrudTaskInfo.from_dict(task.model_dump()) for task in tasks_full]
        metadata = CrewRunMetadataCreate(
            inputs=CrewRunMetadataCreateInputs(),
            tasks_snapshot=task_snapshots,
        )
        if crew_run_data.inputs:
            metadata.inputs.additional_properties = crew_run_data.inputs

        task_states_dict: dict[str, TaskStateSnapshot] = {}
        for index, task in enumerate(tasks_full):
            task_states_dict[task.key] = TaskStateSnapshot(
                order=index,
                state=TaskStateSnapshotState(),
                status=TaskStatus.QUEUED,
            )
        task_states = CrewRunOutputCreateTaskStates()
        task_states.additional_properties = task_states_dict
        output = CrewRunOutputCreate(task_states=task_states)
        
        crew_run_create = CrewRunCreate(
            crew_id=crew_run_data.crew_id,
            run_metadata=metadata,
            output=output,
        )
        
        response = await create_crew_run_func.asyncio_detailed(
            body=CrewRunCreateBody(crew_run_data=crew_run_create, user_token=user_token),
            client=self.crud_client,
        )

        if response.status_code != 201:
            error_msg = f"Failed to create crew run: status {response.status_code}"
            try:
                error_content = response.content.decode() if response.content else "No error details"
                error_msg += f" - {error_content}"
            except:
                pass
            raise ValueError(error_msg)

        if isinstance(response.parsed, HTTPValidationError):
            raise ValueError(f"Validation error creating crew run: {response.parsed}")

        if response.parsed is None:
            raise ValueError("Failed to create crew run: received None response")

        return CrewRun.model_validate(response.parsed.to_dict())

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

    async def cancel_crew_run(self, crew_run_id: UUID, user_token: str):
        """Cancel a crew run."""
        await cancel_crew_run_func.asyncio(
            crew_run_id=crew_run_id,
            body=user_token,
            client=self.crud_client,
        )

    async def retry_crew_run(self, retry_request: CrewRunRetryRequest, crew_run_id: UUID, user_token: str):
        """Retry a crew run from a specific task."""
        crew_run = await self.get_crew_run(crew_run_id)
        if crew_run is None:
            raise ValueError(f"Crew run {crew_run_id} not found")
        
        retry_from_task_key = retry_request.retry_from_task_key
        
        try:
            self._validate_retry_task_completed(crew_run, retry_from_task_key)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            ) from e
        
        tasks_snapshot = crew_run.run_metadata.tasks_snapshot
        
        upstream_tasks = self._find_upstream_tasks(tasks_snapshot, retry_from_task_key)
        downstream_tasks = self._find_downstream_tasks(tasks_snapshot, retry_from_task_key)
        
        # Convert tasks_snapshot to TaskInfo objects for building dependency graph
        tasks_full = [TaskInfo.model_validate(task.to_dict()) for task in tasks_snapshot]
        graph = build_flow_dependency_graph(tasks_full)
        
        # Include retry_from_task_key and downstream tasks in the set of tasks whose written fields should be removed
        # since we're retrying FROM (including) retry_from_task_key
        tasks_to_retry_keys = {task.key for task in downstream_tasks}
        tasks_to_retry_keys.add(retry_from_task_key)
        fields_written_by_retry_tasks = self._get_fields_written_by_tasks(graph, tasks_to_retry_keys)
        
        # Filter inputs: remove fields written by tasks that will be retried (but keep context fields)
        original_inputs = crew_run.run_metadata.inputs.to_dict()
        filtered_inputs = {}
        
        for field_name, field_value in original_inputs.items():
            # Keep context fields (they're user-provided, not task-written)
            field_spec = graph.state_field_specs.get(field_name)
            if field_spec and field_spec.get("field_kind") == "context":
                filtered_inputs[field_name] = field_value
            # Keep fields not written by tasks that will be retried (retry_from_task_key and downstream)
            elif field_name not in fields_written_by_retry_tasks:
                filtered_inputs[field_name] = field_value
        
        # Get original task states if available (for order preservation)
        # output is always present in CrewRunRead, and task_states is required in CrewRunOutputRead
        original_task_states = crew_run.output.task_states.additional_properties if hasattr(crew_run.output.task_states, 'additional_properties') else None
        
        # Create task states for all tasks:
        # - Upstream tasks: COMPLETED
        # - retry_from_task_key and downstream tasks: QUEUED (will be retried)
        all_task_states = self._create_retry_task_states(
            upstream_tasks,
            retry_from_task_key,
            downstream_tasks,
            tasks_snapshot,
            original_task_states
        )
        
        new_metadata = CrewRunMetadataCreate(
            inputs=CrewRunMetadataCreateInputs(),
            tasks_snapshot=tasks_snapshot,  # Keep tasks_snapshot unchanged
        )
        new_metadata.inputs.additional_properties = filtered_inputs
        new_metadata.retry_feedback = RetryFeedback(
            retry_from_task_key=retry_request.retry_from_task_key,
            feedback=retry_request.feedback,
        )
        
        # Create crew run output with all task states
        output = CrewRunOutputCreate(task_states=all_task_states)
        
        # Create new crew run
        crew_run_create = CrewRunCreate(
            crew_id=crew_run.crew_id,
            run_metadata=new_metadata,
            output=output,
        )
        
        response = await create_crew_run_func.asyncio_detailed(
            body=CrewRunCreateBody(crew_run_data=crew_run_create, user_token=user_token),
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

        retry_crew_run_result = CrewRun.model_validate(response.parsed.to_dict())
        
        # Copy artifacts from the original crew run to the retry crew run
        # This is best-effort - failures should not prevent retry from succeeding
        try:
            copy_artifacts_url = f"{settings.CRUD_SERVICE_URL}/internal/crew-run/{crew_run_id}/copy-artifacts/{retry_crew_run_result.id}"
            copy_response = await self.crud_client.get_httpx_client().post(
                copy_artifacts_url,
                headers={
                    "X-Internal-API-Key": settings.INTERNAL_CREW_API_KEY,
                },
                timeout=httpx.Timeout(60.0),  # Artifact copying may take time
            )
            if copy_response.status_code == 200:
                logger.info(
                    f"Successfully copied artifacts from crew run {crew_run_id} to retry {retry_crew_run_result.id}"
                )
            else:
                logger.warning(
                    f"Failed to copy artifacts from crew run {crew_run_id} to retry {retry_crew_run_result.id}: "
                    f"status {copy_response.status_code}"
                )
        except Exception as e:
            # Log warning but don't fail the retry operation (artifact copying is best-effort)
            logger.warning(
                f"Failed to copy artifacts from crew run {crew_run_id} to retry {retry_crew_run_result.id}: {e}"
            )
        
        # Cancel the original crew run after successfully creating the retry
        # Skip cancellation if already in terminal state (CANCELLED or COMPLETED)
        queue_status = crew_run.queue_status
        if queue_status and queue_status not in (QueueStatus.CANCELLED, QueueStatus.COMPLETED):
            try:
                await self.cancel_crew_run(crew_run_id, user_token)
                logger.info(f"Cancelled original crew run {crew_run_id} after creating retry {retry_crew_run_result.id}")
            except Exception as e:
                # Log warning but don't fail the retry operation (cancellation is best-effort)
                logger.warning(
                    f"Failed to cancel original crew run {crew_run_id} after creating retry {retry_crew_run_result.id}: {e}"
                )
        else:
            logger.info(
                f"Skipping cancellation of crew run {crew_run_id}: already in terminal state "
                f"({queue_status if queue_status is not UNSET else 'UNSET'})"
            )
        
        return retry_crew_run_result

    def _validate_retry_task_completed(self, crew_run, retry_from_task_key: str):
        """
        Validate that retry_from_task_key has been completed.
        
        Args:
            crew_run: The crew run to validate
            retry_from_task_key: The task key to check
            
        Raises:
            ValueError: If the task is not found or not completed
        """
        # Get task states from crew run output
        if not hasattr(crew_run.output, 'task_states') or not hasattr(crew_run.output.task_states, 'additional_properties'):
            raise ValueError(f"Cannot retry: crew run {crew_run.id} does not have task states")
        
        task_states = crew_run.output.task_states.additional_properties
        
        # Check if retry_from_task_key exists in task states
        if retry_from_task_key not in task_states:
            raise ValueError(
                f"Cannot retry from task '{retry_from_task_key}': task not found in crew run {crew_run.id}"
            )
        
        # Check if the task is completed
        task_state = task_states[retry_from_task_key]
        if task_state.status != TaskStatus.COMPLETED:
            raise ValueError(
                f"Cannot retry from task '{retry_from_task_key}': task status is '{task_state.status.value}', "
                f"but only COMPLETED tasks can be retried from"
            )

    def _find_upstream_tasks(self, tasks_snapshot: List[CrudTaskInfo], retry_from_task_key: str) -> List[CrudTaskInfo]:
        """
        Find all tasks that come before retry_from_task_key in tasks_snapshot.
        
        Args:
            tasks_snapshot: List of tasks in execution order
            retry_from_task_key: The task key to retry from
            
        Returns:
            List of upstream tasks (tasks before retry_from_task_key)
            
        Raises:
            ValueError: If retry_from_task_key is not found in tasks_snapshot
        """
        retry_index = None
        for index, task in enumerate(tasks_snapshot):
            if task.key == retry_from_task_key:
                retry_index = index
                break
        
        if retry_index is None:
            raise ValueError(f"Task '{retry_from_task_key}' not found in tasks_snapshot")
        
        return tasks_snapshot[:retry_index]

    def _find_downstream_tasks(self, tasks_snapshot: List[CrudTaskInfo], retry_from_task_key: str) -> List[CrudTaskInfo]:
        """
        Find all tasks that come after retry_from_task_key in tasks_snapshot.
        
        Args:
            tasks_snapshot: List of tasks in execution order
            retry_from_task_key: The task key to retry from
            
        Returns:
            List of downstream tasks (tasks after retry_from_task_key)
            
        Raises:
            ValueError: If retry_from_task_key is not found in tasks_snapshot
        """
        retry_index = None
        for index, task in enumerate(tasks_snapshot):
            if task.key == retry_from_task_key:
                retry_index = index
                break
        
        if retry_index is None:
            raise ValueError(f"Task '{retry_from_task_key}' not found in tasks_snapshot")
        
        return tasks_snapshot[retry_index + 1:]

    def _get_fields_written_by_tasks(self, graph: FlowDependencyGraph, task_keys: Set[str]) -> Set[str]:
        """
        Get all fields written by the given set of tasks.
        
        Args:
            graph: FlowDependencyGraph containing task write information
            task_keys: Set of task keys to check
            
        Returns:
            Set of field names written by any of the given tasks
        """
        fields_written = set()
        for task_key in task_keys:
            write_specs = graph.task_write_specs.get(task_key, [])
            for write_spec in write_specs:
                fields_written.add(write_spec["field"])
        return fields_written

    def _create_completed_task_states(
        self, 
        upstream_tasks: List[CrudTaskInfo],
        tasks_snapshot: List[CrudTaskInfo],
        original_task_states: dict[str, TaskStateSnapshot] | None = None
    ) -> CrewRunOutputCreateTaskStates:
        """
        Create TaskStateSnapshot entries for upstream tasks marked as completed.
        
        Args:
            upstream_tasks: List of tasks to mark as completed
            tasks_snapshot: Full list of tasks in execution order (for fallback ordering)
            original_task_states: Optional dict of original task states keyed by task key (for order lookup)
            
        Returns:
            CrewRunOutputCreateTaskStates containing completed task states
        """
        task_states_dict: dict[str, TaskStateSnapshot] = {}
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Build a map of task key to index in tasks_snapshot for fallback ordering
        task_index_map = {task.key: index for index, task in enumerate(tasks_snapshot)}
        
        for task in upstream_tasks:
            # Try to get order from original task states, otherwise use index from tasks_snapshot
            if original_task_states and task.key in original_task_states:
                order = original_task_states[task.key].order
            else:
                # Fallback to index in tasks_snapshot
                order = task_index_map.get(task.key, 0)
            
            task_states_dict[task.key] = TaskStateSnapshot(
                order=order,
                state=TaskStateSnapshotState(),
                status=TaskStatus.COMPLETED,
                completed_at=current_time,
            )
        
        task_states = CrewRunOutputCreateTaskStates()
        task_states.additional_properties = task_states_dict
        return task_states

    def _create_retry_task_states(
        self,
        upstream_tasks: List[CrudTaskInfo],
        retry_from_task_key: str,
        downstream_tasks: List[CrudTaskInfo],
        tasks_snapshot: List[CrudTaskInfo],
        original_task_states: dict[str, TaskStateSnapshot] | None = None
    ) -> CrewRunOutputCreateTaskStates:
        """
        Create TaskStateSnapshot entries for all tasks in a retry scenario.
        
        Args:
            upstream_tasks: List of tasks before retry_from_task_key (copied from original with COMPLETED status)
            retry_from_task_key: The task key to retry from (marked as QUEUED)
            downstream_tasks: List of tasks after retry_from_task_key (marked as QUEUED)
            tasks_snapshot: Full list of tasks in execution order (for fallback ordering)
            original_task_states: Optional dict of original task states keyed by task key (for copying upstream states)
            
        Returns:
            CrewRunOutputCreateTaskStates containing all task states
            
        Note:
            Upstream task states are copied entirely from the original run, preserving state (task outputs),
            completed_at timestamps, and all other fields. Only the retry task and downstream tasks get
            new TaskStateSnapshot objects with QUEUED status.
        """
        task_states_dict: dict[str, TaskStateSnapshot] = {}
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Build a map of task key to index in tasks_snapshot for fallback ordering
        task_index_map = {task.key: index for index, task in enumerate(tasks_snapshot)}
        
        # Copy upstream tasks from original (preserving state, completed_at, etc.)
        for task in upstream_tasks:
            if original_task_states and task.key in original_task_states:
                # Copy the entire original TaskStateSnapshot to preserve all fields
                original_snapshot = original_task_states[task.key]
                task_states_dict[task.key] = copy.deepcopy(original_snapshot)
                # Ensure status is COMPLETED (should already be, but verify)
                if task_states_dict[task.key].status != TaskStatus.COMPLETED:
                    task_states_dict[task.key].status = TaskStatus.COMPLETED
            else:
                # Fallback: create new snapshot if original doesn't exist
                order = task_index_map.get(task.key, 0)
                task_states_dict[task.key] = TaskStateSnapshot(
                    order=order,
                    state=TaskStateSnapshotState(),
                    status=TaskStatus.COMPLETED,
                    completed_at=current_time,
                )
        
        # Mark retry_from_task_key as QUEUED (will be retried)
        # Reset status to QUEUED and clear completed_at to ensure clean retry state
        if original_task_states and retry_from_task_key in original_task_states:
            order = original_task_states[retry_from_task_key].order
        else:
            order = task_index_map.get(retry_from_task_key, len(upstream_tasks))
        
        task_states_dict[retry_from_task_key] = TaskStateSnapshot(
            order=order,
            state=TaskStateSnapshotState(),
            status=TaskStatus.QUEUED,
            completed_at=UNSET,  # Explicitly reset completed_at for retry
        )
        
        # Mark downstream tasks as QUEUED (will be retried)
        # Reset status to QUEUED and clear completed_at to ensure clean retry state
        for task in downstream_tasks:
            if original_task_states and task.key in original_task_states:
                order = original_task_states[task.key].order
            else:
                order = task_index_map.get(task.key, 0)
            
            task_states_dict[task.key] = TaskStateSnapshot(
                order=order,
                state=TaskStateSnapshotState(),
                status=TaskStatus.QUEUED,
                completed_at=UNSET,  # Explicitly reset completed_at for retry
            )
        
        task_states = CrewRunOutputCreateTaskStates()
        task_states.additional_properties = task_states_dict
        return task_states