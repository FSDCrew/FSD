from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.schemas.schemas import CrewRun as CrewRunDB
from app.models.models import CrewRunCreate

class CrewRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_crew_run(self, crew_run_data: CrewRunCreate) -> CrewRunDB:
        """Creates a new crew run record."""
        db_crew_run = CrewRunDB(
            crew_id=crew_run_data.crew_id,
            output=crew_run_data.output
        )
        self.session.add(db_crew_run)
        await self.session.flush()
        await self.session.refresh(db_crew_run)
        return db_crew_run

    async def get_crew_run_by_id_with_artifacts(self, crew_run_id: UUID) -> CrewRunDB | None:
        """Retrieves a crew run by ID, loading all associated artifacts in one query."""
        query = (
            select(CrewRunDB)
            .where(CrewRunDB.id == crew_run_id)
            .options(selectinload(CrewRunDB.artifacts))
        )
        result = await self.session.execute(query)

        return result.scalar_one_or_none()
    
    async def update_crew_run_output(self, crew_run_id: UUID, output: dict) -> CrewRunDB | None:
        """Updates the output of a crew run."""
        query = select(CrewRunDB).where(CrewRunDB.id == crew_run_id)
        result = await self.session.execute(query)
        db_crew_run = result.scalar_one_or_none()
        
        if db_crew_run:
            setattr(db_crew_run, "output", output)
            await self.session.commit()
            await self.session.refresh(db_crew_run)
        
        return db_crew_run