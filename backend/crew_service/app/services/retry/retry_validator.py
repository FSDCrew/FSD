"""Validation logic for crew run retries."""

from app.api.crud_client.models import CrewRunRead, TaskStatus


class RetryValidator:
    """Validates retry requests for crew runs."""

    @staticmethod
    def validate_retry_request(crew_run: CrewRunRead, retry_from_task_key: str) -> None:
        """
        Validate:
            1. retry_from_task_key is in task_states
            2. retry_from_task_key is TaskStatus.COMPLETED
        """
        task_states = crew_run.output.task_states
        if not task_states.__contains__(retry_from_task_key):
            raise ValueError(f"Cannot retry from task '{retry_from_task_key}' as it is not found in the crew run task states {crew_run.id}")
        
        retry_task = task_states.__getitem__(retry_from_task_key)
        if retry_task.status != TaskStatus.COMPLETED:
            raise ValueError(f"Cannot retry from task '{retry_from_task_key}': task status is '{retry_task.status.value}', but only COMPLETED tasks can be retried from")


