from app.models.models import TaskRead, TaskCreate, TaskUpdate
from app.repositories.task_repository import TaskRepository
from fastapi import HTTPException
from uuid import UUID
from typing import Any
from collections.abc import Sequence
import httpx

from app.schemas.schemas import Task as TaskDB

from app.services.crew_service import CrewService
from app.api.crew_client.client import Client
from app.api.crew_client.api.tasks import get_pre_defined_tasks_tasks_pre_defined_get as get_pre_defined_tasks
from config import settings


class TaskService:
    def __init__(self, repository: TaskRepository, crew_service: CrewService):
        self.repository = repository
        self.crew_service = crew_service
        self.crew_client = Client(
            base_url=settings.CREW_SERVICE_URL,
            timeout=httpx.Timeout(30.0),
        )

    def _convert_to_task_read(self, db_task: TaskDB) -> TaskRead:
        """Helper to convert TaskDB object to TaskRead Pydantic model."""

        return TaskRead.model_validate(db_task)

    async def _get_valid_task_dict(self) -> dict[str, dict[str, Any]]:
        """Get the dictionary of valid pre-defined tasks from crew service, keyed by task key."""
        try:
            pre_defined_tasks = await get_pre_defined_tasks.asyncio(client=self.crew_client)
            if not pre_defined_tasks:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get pre-defined tasks from crew service"
                )
            return {task.key: task.to_dict() for task in pre_defined_tasks}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get pre-defined tasks: {str(e)}"
            )

    async def _validate_task_key(self, key: str, pre_defined_task_dict: dict[str, dict[str, Any]]) -> None:
        """Validate that the task key exists in pre-defined tasks."""
        if key not in pre_defined_task_dict:
            raise HTTPException(
                status_code=400,
                detail=f"Task key '{key}' is not a valid pre-defined task key"
            )

    def _check_duplicate_keys(self, tasks: Sequence[TaskCreate | TaskUpdate], exclude_task_id: UUID | None = None) -> None:
        """Check for duplicate task keys in a list of tasks."""
        seen_keys = set()
        for task in tasks:
            if isinstance(task, TaskUpdate) and exclude_task_id and task.id == exclude_task_id:
                continue
            if task.key in seen_keys:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate task key '{task.key}' found in the provided tasks"
                )
            seen_keys.add(task.key)
    
    async def replace_tasks_by_crew(self, crew_id: UUID, tasks: list[TaskCreate], user_id: UUID) -> list[TaskRead]:
        """Replace all tasks for a crew."""
        await self.crew_service.validate_crew(crew_id, user_id)
        
        valid_task_dict = await self._get_valid_task_dict()
        seen_keys = set()
        for task in tasks:
            # Check for duplicates
            if task.key in seen_keys:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate task key '{task.key}' found in the provided tasks"
                )
            seen_keys.add(task.key)
            
            # Validate task key is a valid pre-defined task
            if task.key not in valid_task_dict:
                raise HTTPException(
                    status_code=400,
                    detail=f"Task key '{task.key}' is not a valid pre-defined task key"
                )
        
        created_tasks = await self.repository.replace_tasks_by_crew(crew_id, tasks)
        return [self._convert_to_task_read(task) for task in created_tasks]