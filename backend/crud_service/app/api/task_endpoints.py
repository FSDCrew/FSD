from fastapi import APIRouter, Depends, Path
from uuid import UUID

from app.models.models import  TaskRead, TaskUpdate, TaskCreate, User
from app.services.task_service import TaskService
from app.dependencies import get_task_service, get_current_user

task_router = APIRouter(
    prefix="/task",
    tags=["task"],
)

@task_router.post(
    "/{crew_id}",
    status_code=201,
    response_model=TaskRead
)
async def create_task(
    task: TaskCreate,
    crew_id: UUID = Path(..., description="Crew ID to associate the task with", example="123e4567-e89b-12d3-a456-426614174000"),
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    """Create a new task."""
    return await task_service.create_task(task, crew_id, current_user.id)

@task_router.patch(
    "/{crew_id}",
    response_model=list[TaskRead]
)
async def update_one_task(
    task: TaskUpdate,
    crew_id: UUID = Path(..., description="Crew ID to associate the task with", example="123e4567-e89b-12d3-a456-426614174000"),
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
):
    """Update one task."""
    updated_task = await service.update_task(task, current_user.id, crew_id)
    return [updated_task]

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