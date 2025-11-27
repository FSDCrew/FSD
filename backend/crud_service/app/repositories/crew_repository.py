from uuid import UUID
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.schemas.schemas import Crew as CrewDB, CrewRun as CrewRunDB
from app.models.models import CrewCreate, CrewUpdate


class CrewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_fully_loaded_crew_by_id(self, crew_id: UUID, user_id: UUID) -> CrewDB | None:
        """Retrieve a single Crew by its ID, eagerly loading all associated tasks and crew runs"""
        query = select(CrewDB).options(selectinload(CrewDB.tasks), selectinload(CrewDB.crew_runs).selectinload(CrewRunDB.artifacts)).where(CrewDB.id == crew_id).where(CrewDB.user_id == user_id)
        result = await self.session.execute(query)
        db_crew = result.scalar_one_or_none()
        if not db_crew:
            return None
        
        return db_crew
    
    async def get_fully_loaded_crew_by_id_internal(self, crew_id: UUID) -> CrewDB | None:
        """Retrieve a single Crew by its ID for internal services without user ownership constraint."""
        query = select(CrewDB).options(
            selectinload(CrewDB.tasks),
            selectinload(CrewDB.crew_runs).selectinload(CrewRunDB.artifacts)
        ).where(CrewDB.id == crew_id)
        result = await self.session.execute(query)
        db_crew = result.scalar_one_or_none()
        if not db_crew:
            return None
        
        return db_crew

    async def get_all_fully_loaded_crews(self, user_id: UUID) -> list[CrewDB]:
        """Retrieve all Crews belonging to a user, eagerly loading all associated tasks and crew runs"""
        query = select(CrewDB).options(selectinload(CrewDB.tasks), selectinload(CrewDB.crew_runs).selectinload(CrewRunDB.artifacts)).where(CrewDB.user_id == user_id) 
        result = await self.session.execute(query)
        db_crews = list(result.scalars().all())
        
        return db_crews
    
    async def create_crew(self, crew: CrewCreate, user_id: UUID) -> CrewDB:
        """Create a new crew in the database."""
        db_crew = CrewDB(
            name=crew.name,
            user_id=user_id
        )
        self.session.add(db_crew)
        await self.session.commit()
        await self.session.refresh(db_crew)

        return db_crew
    
    async def update_crew(self, crew_patch: CrewUpdate) -> CrewDB | None:
        """Update an existing crew in the database."""
        query = select(CrewDB).options(selectinload(CrewDB.tasks), selectinload(CrewDB.crew_runs).selectinload(CrewRunDB.artifacts)).where(CrewDB.id == crew_patch.id)
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
    
    async def delete_crew(self, crew_id: UUID) -> CrewDB | None:
        """Delete a crew from the database and return the deleted row, using a single DELETE ... RETURNING."""
        stmt = (
            delete(CrewDB)
            .where(CrewDB.id == crew_id)
            .returning(CrewDB)
        )
        result = await self.session.execute(stmt)
        deleted_crew = result.scalars().first()
        await self.session.commit()
        return None