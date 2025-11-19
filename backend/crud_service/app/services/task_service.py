from app.models.models import TaskRead, TaskCreate, TaskUpdate
from app.repositories.task_repository import TaskRepository
from fastapi import HTTPException
from uuid import UUID
from typing import cast

from app.schemas.schemas import Task as TaskDB

from app.services.crew_service import CrewService


class TaskService:
    def __init__(self, repository: TaskRepository, crew_service: CrewService):
        self.repository = repository
        self.crew_service = crew_service

    def _convert_to_task_read(self, db_task: TaskDB) -> TaskRead:
        """Helper to convert TaskDB object to TaskRead Pydantic model."""

        return TaskRead.model_validate(db_task)

    async def create_task(self, task: TaskCreate, crew_id: UUID, user_id: UUID) -> TaskRead:
        """Create a new task."""
        await self.crew_service.validate_crew(crew_id, user_id)
        db_task = await self.repository.create_task(task, crew_id)
        return self._convert_to_task_read(db_task)
    
    async def update_task(self, task: TaskUpdate, user_id: UUID, crew_id: UUID) -> TaskRead:
        """Update an existing task."""
        await self.crew_service.validate_crew(crew_id, user_id)
        updated_task = await self.repository.update_task(task)
        if updated_task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return self._convert_to_task_read(updated_task)
    
    async def replace_tasks_by_crew(self, crew_id: UUID, tasks: list[TaskCreate], user_id: UUID) -> list[TaskRead]:
        """Replace all tasks for a crew."""
        await self.crew_service.validate_crew(crew_id, user_id)
        created_tasks = await self.repository.replace_tasks_by_crew(crew_id, tasks)
        return [self._convert_to_task_read(task) for task in created_tasks]