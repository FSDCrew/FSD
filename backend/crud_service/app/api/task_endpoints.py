from fastapi import APIRouter, Depends, Path
from uuid import UUID

from app.models.models import  TaskRead, TaskUpdate, TaskCreate, User
from app.services.task_service import TaskService
from app.dependencies import get_task_service, get_current_user

task_router = APIRouter(
    prefix="/task",
    tags=["task"],
)

@task_router.put(
    "/{crew_id}/save",
    response_model=list[TaskRead]
)
async def replace_all_tasks_for_crew(
    tasks: list[TaskCreate],
    crew_id: UUID = Path(..., description="Crew ID to associate the task with", example="123e4567-e89b-12d3-a456-426614174000"),
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    """Replace all tasks for a crew."""
    return await service.replace_tasks_by_crew(crew_id, tasks, current_user.id)