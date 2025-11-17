import uuid
from uuid import UUID
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.schemas.schemas import Crew as CrewDB, Task as TaskDB
from app.models.models import CrewCreate, CrewUpdate, CrewRead, TaskRead, CrewRunRead


class CrewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_crew_with_tasks(self, crew_id: UUID, user_id: UUID) -> CrewRead | None:
        """Get a crew from the database with tasks and agents."""
        query = select(CrewDB).options(selectinload(CrewDB.tasks), selectinload(CrewDB.crew_runs)).where(CrewDB.id == crew_id).where(CrewDB.user_id == user_id)
        result = await self.session.execute(query)
        db_crew = result.scalar_one_or_none()
        if not db_crew:
            return None
        
        return db_crew

    async def get_crews_with_tasks(self, user_id: UUID) -> list[CrewRead]:
        """Get crews from database with tasks."""
        query = select(CrewDB).options(selectinload(CrewDB.tasks)).where(CrewDB.user_id == user_id) 
        result = await self.session.execute(query)
        db_crews = result.scalars().all()
        
        return db_crews
    
    async def create_crew(self, crew: CrewCreate) -> CrewDB:
        """Create a new crew in the database."""
        db_crew = CrewDB(
            name=crew.name,
            user_id=crew.user_id
        )
        self.session.add(db_crew)
        await self.session.commit()
        await self.session.refresh(db_crew)

        return db_crew
    
    async def update_crew(self, crew_patch: CrewUpdate) -> CrewDB | None:
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
        
        return db_crew
    
    async def delete_crew(self, crew_id: UUID) -> None:
        """Delete a crew from the database."""
        query = select(CrewDB).where(CrewDB.id == crew_id)
        result = await self.session.execute(query)
        db_crew = result.scalar_one_or_none()
        if db_crew:
            await self.session.delete(db_crew)
            await self.session.commit()
        return None