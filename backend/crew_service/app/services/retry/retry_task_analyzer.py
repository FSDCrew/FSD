from typing import Any, Dict, List, Set, Tuple

from app.api.crud_client.models import TaskInfo as CrudTaskInfo, TaskStateSnapshot
from app.models.models import FlowDependencyGraph


class RetryTaskAnalyzer:
    """Analyzes task dependencies and field relationships for retries."""

    @staticmethod
    def find_upstream_tasks(
        sorted_task_states: List[Tuple[str, TaskStateSnapshot]], 
        tasks_snapshot_dict: Dict[str, CrudTaskInfo], 
        retry_from_task_key: str
    ) -> List[Tuple[str, TaskStateSnapshot, CrudTaskInfo]]:
        """
        Find all tasks that come before retry_from_task_key in tasks_snapshot.
        
        Args:
            tasks_snapshot: List of tasks in execution order
            retry_from_task_key: The task key to retry from
            
        Returns:
            List of upstream (key, task_state, task_info) tuples
            
        Raises:
            ValueError: If retry_from_task_key is not found in tasks_snapshot
        """
        upstream_tasks = []
        for task_key, task_state in sorted_task_states:
            if task_key == retry_from_task_key:
                break
            upstream_tasks.append((task_key, task_state, tasks_snapshot_dict[task_key]))
        
        return upstream_tasks

    @staticmethod
    def find_retry_and_downstream_tasks(
        sorted_task_states: List[Tuple[str, TaskStateSnapshot]],
        tasks_snapshot_dict: Dict[str, CrudTaskInfo],
        retry_from_task_key: str
    ) -> List[Tuple[str, TaskStateSnapshot, CrudTaskInfo]]:
        """
        Find all tasks that are retry_from_task_key and downstream of it in tasks_snapshot, inclusive of retry_from_task_key.
        
        Args:
            tasks_snapshot: List of tasks in execution order
            retry_from_task_key: The task key to retry from
            
        Returns:
            List of retry and downstream (key, task_state, task_info) tuples
            
        Raises:
            ValueError: If retry_from_task_key is not found in tasks_snapshot
        """
        retry_index = None
        for index, (task_key, task_state) in enumerate(sorted_task_states):
            if task_key == retry_from_task_key:
                retry_index = index
                break
        
        if retry_index is None:
            raise ValueError(f"Task '{retry_from_task_key}' not found in sorted_task_states")
        
        retry_and_downstream_tasks = []
        for task_key, task_state in sorted_task_states[retry_index:]:
            retry_and_downstream_tasks.append((task_key, task_state, tasks_snapshot_dict[task_key]))
        
        return retry_and_downstream_tasks

    @staticmethod
    def get_fields_written_by_tasks(graph: FlowDependencyGraph, task_keys: Set[str]) -> Set[str]:
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

    @staticmethod
    def filter_inputs_for_retry(
        original_inputs: Dict[str, Any],
        graph: FlowDependencyGraph,
        tasks_to_retry_keys: Set[str]
    ) -> Dict[str, Any]:
        """
        Filter inputs by removing fields written by tasks that will be retried.
        
        Context fields are always kept as they are user-provided, not task-written.
        
        Args:
            original_inputs: Original inputs from the crew run
            graph: FlowDependencyGraph containing field specifications
            tasks_to_retry_keys: Set of task keys that will be retried
            
        Returns:
            Filtered inputs dictionary
        """
        fields_written_by_retry_tasks = RetryTaskAnalyzer.get_fields_written_by_tasks(graph, tasks_to_retry_keys)
        
        filtered_inputs = {}
        for field_name, field_value in original_inputs.items():
            # Keep context fields (they're user-provided, not task-written)
            field_spec = graph.state_field_specs.get(field_name)
            if field_spec and field_spec.get("field_kind") == "context":
                filtered_inputs[field_name] = field_value
            # Keep fields not written by tasks that will be retried
            elif field_name not in fields_written_by_retry_tasks:
                filtered_inputs[field_name] = field_value
        
        return filtered_inputs

