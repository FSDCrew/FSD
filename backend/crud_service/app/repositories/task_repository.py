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
    
    async def get_task(self, task_id: UUID) -> TaskRead | None:
        """Get a task from the database."""
        query = select(TaskDB).where(TaskDB.id == task_id)
        result = await self.session.execute(query)
        db_task = result.scalar_one_or_none()
        # TODO: Place validation in service layer
        if not db_task:
            return None
        return TaskRead(
            id=UUID(str(db_task.id)),
            key=str(db_task.key),
            description=str(db_task.description) if hasattr(db_task, 'description') else "",
            expected_output=str(db_task.expected_output) if hasattr(db_task, 'expected_output') else "",
            agent_key=str(db_task.agent_key),
            order=cast(int, db_task.order)
        )

    async def get_tasks_by_crew(self, crew_id: UUID) -> list[TaskRead]:
        """Get all tasks for a crew."""
        query = select(TaskDB).where(TaskDB.crew_id == crew_id)
        result = await self.session.execute(query)
        db_tasks = result.scalars().all()
        
        return [
            TaskRead(
                id=UUID(str(task.id)),
                key=str(task.key),
                description=str(task.description) if hasattr(task, 'description') else "",
                expected_output=str(task.expected_output) if hasattr(task, 'expected_output') else "",
                agent_key=str(task.agent_key),
                order=cast(int, task.order)
            )
            for task in db_tasks
        ]
    
    async def create_task(self, task: TaskCreate, crew_id: UUID) -> TaskRead:
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

        return TaskRead(
            id=UUID(str(db_task.id)),
            key=str(db_task.key),
            description=str(db_task.description) if hasattr(db_task, 'description') else "",
            expected_output=str(db_task.expected_output) if hasattr(db_task, 'expected_output') else "",
            agent_key=str(db_task.agent_key),
            order=cast(int, db_task.order)
        )
    
    async def update_task(self, task_patch: TaskUpdate) -> TaskRead | None:
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
        
        return TaskRead(
            id=UUID(str(db_task.id)),
            key=str(db_task.key),
            description=str(db_task.description) if hasattr(db_task, 'description') else "",
            expected_output=str(db_task.expected_output) if hasattr(db_task, 'expected_output') else "",
            agent_key=str(db_task.agent_key),
            order=cast(int, db_task.order)
        )
    
    async def replace_tasks_by_crew(self, crew_id: UUID, tasks: list[TaskCreate]) -> list[TaskRead]:
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
        
        return [
            TaskRead(
                id=UUID(str(db_task.id)),
                key=str(db_task.key),
                description=str(db_task.description) if hasattr(db_task, 'description') else "",
                expected_output=str(db_task.expected_output) if hasattr(db_task, 'expected_output') else "",
                agent_key=str(db_task.agent_key),
                order=cast(int, db_task.order)
            )
            for db_task in created_tasks
        ]