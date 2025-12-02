from copy import deepcopy
from typing import List

from fastapi import APIRouter

from app.models.models import TaskInfo
from config import tasks_config

tasks_router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@tasks_router.get(
    "/pre-defined",
    response_model=List[TaskInfo],
)
async def get_pre_defined_tasks() -> List[TaskInfo]:
    """Return the full pre-defined task definitions sourced from tasks.yaml."""
    tasks: List[TaskInfo] = []

    for task_config in tasks_config.values():
        tasks.append(TaskInfo.model_validate(task_config))

    return tasks
