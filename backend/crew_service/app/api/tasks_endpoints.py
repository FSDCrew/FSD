from fastapi import APIRouter
from typing import List
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
    """Get all pre-defined tasks with key, name, and task_description."""
    tasks = []
    
    for task_key, task_config in tasks_config.items():
        if isinstance(task_config, dict):
            task_info = TaskInfo(
                key=task_config.get("key", task_key),
                name=task_config.get("name", ""),
                task_description=task_config.get("task_description", ""),
            )
            tasks.append(task_info)
    
    return tasks

