"""Execution preparation logic for retry crew runs."""

from typing import Any, Dict, List, Tuple

from app.api.crud_client.models import CrewRunRead, TaskInfo as CrudTaskInfo, TaskStatus
from app.api.crud_client.types import UNSET
from app.models.models import TaskInfo
from app.services.retry.retry_task_analyzer import RetryTaskAnalyzer
from config import logger, tasks_config


class RetryExecutor:
    """Prepares crew run execution for retry scenarios."""

    @staticmethod
    def prepare_retry_execution(
        crew_run: CrewRunRead,
    ) -> Tuple[List[TaskInfo], Dict[str, Any]]:
        """
        Prepare execution data for a retry crew run.
        
        Args:
            crew_run: The crew run with retry_feedback set
            
        Returns:
            Tuple of (filtered_tasks, combined_inputs) where:
            - filtered_tasks: List of tasks from retry_from_task_key onwards with retry prompt in description
            - combined_inputs: Dict combining run_metadata.inputs + upstream task outputs
        """
        retry_feedback = crew_run.run_metadata.retry_feedback
        if retry_feedback is None or retry_feedback is UNSET:
            raise ValueError("Cannot prepare retry execution: retry_feedback is not set")
        
        # Type narrowing: retry_feedback is now RetryFeedback
        from app.api.crud_client.models import RetryFeedback
        if not isinstance(retry_feedback, RetryFeedback):
            raise ValueError(f"Unexpected retry_feedback type: {type(retry_feedback)}")
        
        retry_from_task_key = retry_feedback.retry_from_task_key
        feedback = retry_feedback.feedback
        
        logger.info(
            f"Preparing retry execution for crew_run {crew_run.id} from task {retry_from_task_key}"
        )
        
        # Get task states sorted by order
        task_states = crew_run.output.task_states
        sorted_task_states = sorted(
            task_states.additional_properties.items(),
            key=lambda item: item[1].order
        )
        
        # Build tasks_snapshot dict for quick lookup
        tasks_snapshot = crew_run.run_metadata.tasks_snapshot
        tasks_snapshot_dict = {task.key: task for task in tasks_snapshot}
        
        # Find upstream and retry+downstream tasks
        upstream_tasks = RetryTaskAnalyzer.find_upstream_tasks(
            sorted_task_states, tasks_snapshot_dict, retry_from_task_key
        )
        retry_and_downstream_tasks = RetryTaskAnalyzer.find_retry_and_downstream_tasks(
            sorted_task_states, tasks_snapshot_dict, retry_from_task_key
        )
        
        # Extract upstream task outputs
        upstream_outputs = RetryExecutor._extract_upstream_outputs(upstream_tasks)
        
        # Combine run_metadata.inputs with upstream outputs
        original_inputs = crew_run.run_metadata.inputs.to_dict()
        combined_inputs = {**original_inputs, **upstream_outputs}
        combined_inputs['crew_run_id'] = str(crew_run.id)
        
        # Filter tasks to only include retry_from_task_key and downstream
        filtered_tasks = []
        retry_and_downstream_task_keys = {
            task_key for task_key, _, _ in retry_and_downstream_tasks
        }
        
        for task in tasks_snapshot:
            if task.key in retry_and_downstream_task_keys:
                # Convert CrudTaskInfo to TaskInfo
                task_dict = task.to_dict()
                task_info = TaskInfo.model_validate(task_dict)
                
                # If this is the retry task, prepend retry prompt to description
                if task.key == retry_from_task_key:
                    task_info.description = RetryExecutor._format_retry_prompt(
                        task_info.description, feedback
                    )
                
                filtered_tasks.append(task_info)
        
        logger.info(
            f"Prepared retry execution: {len(filtered_tasks)} tasks, "
            f"{len(upstream_outputs)} upstream outputs merged into inputs"
        )
        
        return filtered_tasks, combined_inputs

    @staticmethod
    def _extract_upstream_outputs(
        upstream_tasks: List[Tuple[str, Any, CrudTaskInfo]]
    ) -> Dict[str, Any]:
        """
        Extract outputs from upstream tasks that completed successfully.
        
        Args:
            upstream_tasks: List of (task_key, task_state, task_info) tuples
            
        Returns:
            Dictionary of field_name -> output_value from upstream tasks
        """
        upstream_outputs = {}
        
        for task_key, task_state, _ in upstream_tasks:
            # Only extract outputs from completed tasks
            if task_state.status != TaskStatus.COMPLETED:
                logger.warning(
                    f"Skipping upstream task {task_key}: status is {task_state.status}, not COMPLETED"
                )
                continue
            
            # Extract outputs from task_state.state.additional_properties
            task_outputs = task_state.state.additional_properties
            
            # Merge outputs into upstream_outputs dict
            # Field names are the keys in task_outputs
            for field_name, output_value in task_outputs.items():
                if field_name in upstream_outputs:
                    logger.warning(
                        f"Field {field_name} already exists in upstream_outputs from another task. "
                        f"Overwriting with value from task {task_key}"
                    )
                upstream_outputs[field_name] = output_value
        
        return upstream_outputs

    @staticmethod
    def _format_retry_prompt(original_description: str, feedback: str) -> str:
        """
        Format retry prompt by prepending it to the original task description.
        
        Args:
            original_description: Original task description from tasks.yaml
            feedback: Retry feedback string
            
        Returns:
            Formatted description with retry prompt prepended
        """
        retry_prompt = (
            "<IMPORTANT>\n"
            "- You MUST ground your work on the retry feedback exactly. Do not deviate from the retry feedback.\n"
            "- This task was previously executed and the outputs were not satisfactory. The retry feedback is provided to help you improve the output.\n"
            f"- The retry feedback is as follows: <RETRY FEEDBACK>\n{feedback}\n</RETRY FEEDBACK>\n"
            "</IMPORTANT>\n\n"
        )
        
        return f"{retry_prompt}{original_description}"

