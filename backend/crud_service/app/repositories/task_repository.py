import uuid
from uuid import UUID
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.schemas.schemas import Task as TaskDB, Crew as CrewDB
from app.models.models import TaskCreate, TaskUpdate, TaskRead


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_task(self, task_id: UUID) -> TaskDB | None:
        """Get a task from the database."""
        query = select(TaskDB).where(TaskDB.id == task_id)
        result = await self.session.execute(query)
        db_task = result.scalar_one_or_none()
        # TODO: Place validation in service layer
        if not db_task:
            return None
        
        return db_task

    async def get_tasks_by_crew(self, crew_id: UUID) -> list[TaskDB]:
        """Get all tasks for a crew."""
        query = select(TaskDB).where(TaskDB.crew_id == crew_id)
        result = await self.session.execute(query)
        db_tasks = result.scalars().all()
        
        return db_tasks
    
    async def create_task(self, task: TaskCreate, crew_id: UUID) -> TaskDB:
        """Create a new task in the database."""
        db_task = TaskDB(
            key=task.key,
            agent_key=task.agent_key or "",
            order=task.order or 0,
            crew_id=crew_id
        )
        
        self.session.add(db_task)
        await self.session.commit()
        await self.session.refresh(db_task)
        return db_task
    
    async def update_task(self, task_patch: TaskUpdate) -> TaskDB | None:
        """Update an existing task in the database."""
        query = select(TaskDB).where(TaskDB.id == task_patch.id)
        result = await self.session.execute(query)
        db_task = result.scalar_one_or_none()
        if not db_task:
            return None
        
        update_data = task_patch.model_dump(exclude_unset=True, exclude={'id'})
        for key, value in update_data.items():
            if hasattr(db_task, key):
                setattr(db_task, key, value)
        
        await self.session.commit()
        await self.session.refresh(db_task)

        return db_task
    
    async def replace_tasks_by_crew(self, crew_id: UUID, tasks: list[TaskCreate]) -> list[TaskDB]:
        """Replace all tasks for a crew."""
        query = select(TaskDB).where(TaskDB.crew_id == crew_id)
        result = await self.session.execute(query)
        existing_tasks = result.scalars().all()
        
        for task in existing_tasks:
            await self.session.delete(task)
        
        created_tasks = []
        for task in tasks:
            db_task = TaskDB(
                key=task.key,
                agent_key=task.agent_key or "",
                order=task.order or 0,
                crew_id=crew_id
            )
            self.session.add(db_task)
            created_tasks.append(db_task)
        
        await self.session.commit()
        
        return created_tasks