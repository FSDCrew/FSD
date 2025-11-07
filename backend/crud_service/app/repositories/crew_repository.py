import uuid
from uuid import UUID
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.schemas.schemas import Crew as CrewDB, Task as TaskDB
from app.models.models import CrewCreate, CrewUpdate, CrewRead, TaskRead


class CrewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_crew_with_tasks(self, crew_id: UUID) -> CrewRead | None:
        """Get a crew from the database with tasks and agents."""
        query = select(CrewDB).options(selectinload(CrewDB.tasks)).where(CrewDB.id == crew_id)
        result = await self.session.execute(query)
        db_crew = result.scalar_one_or_none()
        if not db_crew:
            return None
        
        return CrewRead(
            id=UUID(str(db_crew.id)),
            name=str(db_crew.name),
            tasks=[
                TaskRead(
                    id=UUID(str(task.id)),
                    key=str(task.key),
                    description=str(task.description) if hasattr(task, 'description') else "",
                    expected_output=str(task.expected_output) if hasattr(task, 'expected_output') else "",
                    agent_key=str(task.agent_key),
                    order=cast(int, task.order)
                )
                for task in db_crew.tasks
            ],
            agents=[]
        )

    async def get_crews_with_tasks(self, crew_id: UUID | None = None) -> list[CrewRead]:
        """Get crews from database with tasks."""
        query = select(CrewDB).options(selectinload(CrewDB.tasks))
        result = await self.session.execute(query)
        db_crews = result.scalars().all()
        
        return [
            CrewRead(
                id=UUID(str(db_crew.id)),
                name=str(db_crew.name),
                tasks=[
                    TaskRead(
                        id=UUID(str(task.id)),
                        key=str(task.key),
                        description=str(task.description) if hasattr(task, 'description') else "",
                        expected_output=str(task.expected_output) if hasattr(task, 'expected_output') else "",
                        agent_key=str(task.agent_key),
                        order=cast(int, task.order)
                    )
                    for task in (db_crew.tasks if db_crew.tasks else [])
                ],
                agents=[]
            )
            for db_crew in db_crews
        ]
    
    async def create_crew(self, crew: CrewCreate) -> CrewRead:
        """Create a new crew in the database."""
        db_crew = CrewDB(
            name=crew.name,
            user_id=crew.user_id
        )
        self.session.add(db_crew)
        await self.session.commit()
        await self.session.refresh(db_crew)

        return CrewRead(
            id=UUID(str(db_crew.id)),
            name=str(db_crew.name),
            tasks=[],
            agents=[]
        )
    
    async def update_crew(self, crew_patch: CrewUpdate) -> CrewRead | None:
        """Update an existing crew in the database."""
        query = select(CrewDB).options(selectinload(CrewDB.tasks)).where(CrewDB.id == crew_patch.id)
        result = await self.session.execute(query)
        db_crew = result.scalar_one_or_none()
        if not db_crew:
            return None
        
        update_data = crew_patch.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_crew, key, value)
        
        await self.session.commit()
        await self.session.refresh(db_crew, ["tasks"])
        
        tasks = [
            TaskRead(
                id=UUID(str(task.id)),
                key=str(task.key),
                description=str(task.description) if hasattr(task, 'description') else "",
                expected_output=str(task.expected_output) if hasattr(task, 'expected_output') else "",
                agent_key=str(task.agent_key),
                order=cast(int, task.order)
            )
            for task in db_crew.tasks
        ]
        return CrewRead(
            id=UUID(str(db_crew.id)),
            name=str(db_crew.name),
            tasks=tasks,
            agents=[]
        )