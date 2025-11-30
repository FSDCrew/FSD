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

    for task_key, task_config in tasks_config.items():
        if not isinstance(task_config, dict):
            continue

        task_definition = deepcopy(task_config)
        task_definition.setdefault("key", task_key)
        task_definition.setdefault("name", "")
        task_definition.setdefault("task_description", "")
        tasks.append(TaskInfo(**task_definition))

    return tasks
