from app.models.models import TaskRead, TaskCreate, TaskUpdate
from app.repositories.task_repository import TaskRepository
from fastapi import HTTPException
from uuid import UUID

from app.services.crew_service import CrewService


class TaskService:
    def __init__(self, repository: TaskRepository, crew_service: CrewService):
        self.repository = repository
        self.crew_service = crew_service

    async def create_task(self, task: TaskCreate, crew_id: UUID, user_id: UUID) -> TaskRead:
        """Create a new task."""
        await self.crew_service.validate_crew(crew_id, user_id)
        db_task = await self.repository.create_task(task, crew_id)
        return TaskRead(
            id=UUID(str(db_task.id)),
            key=str(db_task.key),
            description=str(db_task.description) if hasattr(db_task, 'description') else "",
            expected_output=str(db_task.expected_output) if hasattr(db_task, 'expected_output') else "",
            agent_key=str(db_task.agent_key),
            order=int(db_task.order)
        )
    
    async def update_task(self, task: TaskUpdate, user_id: UUID, crew_id: UUID) -> TaskRead:
        """Update an existing task."""
        await self.crew_service.validate_crew(crew_id, user_id)
        updated_task = await self.repository.update_task(task)
        if updated_task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskRead(
            id=UUID(str(updated_task.id)),
            key=str(updated_task.key),
            description=str(updated_task.description) if hasattr(updated_task, 'description') else "",
            expected_output=str(updated_task.expected_output) if hasattr(updated_task, 'expected_output') else "",
            agent_key=str(updated_task.agent_key),
            order=int(updated_task.order)
        )
        # return updated_task
    
    async def replace_tasks_by_crew(self, crew_id: UUID, tasks: list[TaskCreate], user_id: UUID) -> list[TaskRead]:
        """Replace all tasks for a crew."""
        await self.crew_service.validate_crew(crew_id, user_id)
        created_tasks = await self.repository.replace_tasks_by_crew(crew_id, tasks)
        return [
            TaskRead(
                id=UUID(str(task.id)),
                key=str(task.key),
                description=str(task.description) if hasattr(task, 'description') else "",
                expected_output=str(task.expected_output) if hasattr(task, 'expected_output') else "",
                agent_key=str(task.agent_key),
                order=int(task.order)
            )
            for task in created_tasks
        ]