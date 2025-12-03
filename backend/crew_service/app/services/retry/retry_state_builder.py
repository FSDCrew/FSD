"""Task state creation logic for crew run retries."""

import copy
import datetime
from typing import Dict, List, Optional

from app.api.crud_client.models import (
    CrewRunOutputCreateTaskStates,
    TaskInfo as CrudTaskInfo,
    TaskStateSnapshot,
    TaskStateSnapshotState,
    TaskStatus,
)
from app.api.crud_client.types import UNSET


class RetryStateBuilder:
    """Builds task state snapshots for retry scenarios."""

    @staticmethod
    def create_retry_task_states(
        upstream_tasks: List[CrudTaskInfo],
        retry_from_task_key: str,
        downstream_tasks: List[CrudTaskInfo],
        tasks_snapshot: List[CrudTaskInfo],
        original_task_states: Optional[Dict[str, TaskStateSnapshot]] = None
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
        task_states_dict: Dict[str, TaskStateSnapshot] = {}
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

