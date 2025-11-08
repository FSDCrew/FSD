from fastapi import APIRouter, Depends, Query
from uuid import UUID

from app.models.models import  TaskRead, TaskUpdate, TaskCreate
from app.services.task_service import TaskService
from app.dependencies import get_task_service

task_router = APIRouter(
    prefix="/task",
    tags=["task"],
)

@task_router.post(
    "/",
    status_code=201,
    response_model=TaskRead
)
async def create_task(
    task: TaskCreate,
    crew_id: UUID = Query(..., description="Crew ID to associate the task with"),
    task_service: TaskService = Depends(get_task_service),
):
    """Create a new task."""
    return await task_service.create_task(task, crew_id)

@task_router.patch(
    "/",
    response_model=list[TaskRead]
)
async def update_one_task(
    task: TaskUpdate,
    service: TaskService = Depends(get_task_service),
):
    """Update one task."""
    updated_task = await service.update_task(task)
    return [updated_task]

@task_router.put(
    "/crew/{crew_id}",
    response_model=list[TaskRead]
)
async def replace_all_tasks_for_crew(
    crew_id: UUID,
    tasks: list[TaskCreate],
    service: TaskService = Depends(get_task_service),
):
    """Replace all tasks for a crew."""
    return await service.replace_tasks_by_crew(crew_id, tasks)